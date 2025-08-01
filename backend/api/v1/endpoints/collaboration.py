"""
ARTAC Collaboration API Endpoints
Advanced multi-agent collaboration endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
from core.logging import get_logger

logger = get_logger(__name__)

try:
    from services.project_workspace_manager import project_workspace_manager
    from services.task_hierarchy_manager import task_hierarchy_manager, TaskType, TaskPriority, AgentSkill, TaskStatus
    from services.advanced_context_manager import advanced_context_manager, ContextRequest as AdvancedContextRequest
    from services.monitoring_dashboard import monitoring_dashboard
    from services.performance_analytics import performance_analytics, AnalyticsPeriod
    from services.file_lock_manager import get_lock_manager, LockType
    from services.stateless_rag_manager import stateless_rag_manager
    COLLABORATION_ENABLED = True
except ImportError as e:
    logger.log_error(e, {"action": "import_collaboration_services"})
    COLLABORATION_ENABLED = False
router = APIRouter()


def check_collaboration_enabled():
    """Check if collaboration services are available"""
    if not COLLABORATION_ENABLED:
        raise HTTPException(
            status_code=503, 
            detail="Collaboration services not available. Please install required dependencies: aiosqlite, faiss-cpu, sentence-transformers"
        )


# Pydantic models
class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    git_repo_url: Optional[str] = None


class AssignAgentRequest(BaseModel):
    agent_id: str
    agent_name: str
    agent_role: str
    skills: List[str] = []
    max_workload: float = 40.0


class CreateTaskRequest(BaseModel):
    title: str
    description: str
    task_type: str
    priority: str = "medium"
    parent_task_id: Optional[str] = None
    required_skills: List[str] = []
    estimated_hours: Optional[float] = None
    due_date: Optional[str] = None
    file_paths: List[str] = []
    acceptance_criteria: List[str] = []
    tags: List[str] = []


class AssignTaskRequest(BaseModel):
    task_id: str
    agent_id: Optional[str] = None
    assignment_algorithm: str = "hierarchy_aware"


class UpdateTaskProgressRequest(BaseModel):
    task_id: str
    progress_percentage: int
    status: Optional[str] = None
    actual_hours: Optional[float] = None


class AcquireLockRequest(BaseModel):
    agent_id: str
    file_path: str
    lock_type: str = "write"
    timeout: int = 1800


class ContextRequest(BaseModel):
    agent_id: str
    query: str
    max_tokens: int = 180000
    strategy: str = "comprehensive"
    include_history: bool = True
    time_range: str = "all"
    content_types: Optional[List[str]] = None
    file_filter: Optional[str] = None


class UnlimitedContextRequest(BaseModel):
    agent_id: str
    query: str
    max_tokens: int = 180000
    strategy: str = "hybrid"  # hierarchical, semantic_clustering, temporal_priority, hybrid
    include_history: bool = True
    time_filter: Optional[str] = None  # ISO datetime string or relative like "1 day ago"


class AddContentRequest(BaseModel):
    agent_id: str
    content: str
    content_type: str  # code_function, code_class, code_file, documentation, conversation, task_description, error_log, etc.
    metadata: Dict[str, Any] = {}


# Status Endpoint
@router.get("/status")
async def get_collaboration_status():
    """Get collaboration system status"""
    return {
        "collaboration_enabled": COLLABORATION_ENABLED,
        "features": {
            "project_management": COLLABORATION_ENABLED,
            "task_hierarchy": COLLABORATION_ENABLED,
            "file_locking": COLLABORATION_ENABLED,
            "context_management": COLLABORATION_ENABLED,
            "performance_analytics": COLLABORATION_ENABLED,
            "real_time_monitoring": COLLABORATION_ENABLED
        },
        "dependencies": {
            "aiosqlite": COLLABORATION_ENABLED,
            "faiss": COLLABORATION_ENABLED,
            "sentence_transformers": COLLABORATION_ENABLED
        }
    }


# Project Management Endpoints
@router.post("/projects")
async def create_project(request: CreateProjectRequest):
    """Create a new collaborative project"""
    check_collaboration_enabled()
    
    try:
        project_id = await project_workspace_manager.create_project(
            project_name=request.name,
            git_repo_url=request.git_repo_url
        )
        
        if project_id:
            return {
                "success": True,
                "project_id": project_id,
                "message": "Project created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create project")
            
    except Exception as e:
        logger.log_error(e, {"action": "create_project"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_projects():
    """List all collaborative projects"""
    try:
        projects = await project_workspace_manager.list_projects()
        return {"projects": projects}
        
    except Exception as e:
        logger.log_error(e, {"action": "list_projects"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}")
async def get_project_status(project_id: str):
    """Get detailed project status"""
    try:
        workspace = await project_workspace_manager.get_project(project_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Project not found")
        
        status = await workspace.get_workspace_status()
        return status
        
    except Exception as e:
        logger.log_error(e, {"action": "get_project_status"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/agents")
async def assign_agent_to_project(project_id: str, request: AssignAgentRequest):
    """Assign an agent to a project"""
    try:
        # Register agent in task manager
        skills = [AgentSkill(skill) for skill in request.skills if skill in [s.value for s in AgentSkill]]
        
        await task_hierarchy_manager.register_agent(
            agent_id=request.agent_id,
            name=request.agent_name,
            role=request.agent_role,
            skills=skills,
            max_workload=request.max_workload
        )
        
        # Assign to project workspace
        success = await project_workspace_manager.assign_agent_to_project(
            project_id=project_id,
            agent_id=request.agent_id,
            agent_role=request.agent_role,
            agent_name=request.agent_name
        )
        
        if success:
            return {"success": True, "message": "Agent assigned to project successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to assign agent to project")
            
    except Exception as e:
        logger.log_error(e, {"action": "assign_agent_to_project"})
        raise HTTPException(status_code=500, detail=str(e))


# Task Management Endpoints
@router.post("/projects/{project_id}/tasks")
async def create_task(project_id: str, request: CreateTaskRequest):
    """Create a new task"""
    try:
        task_type = TaskType(request.task_type)
        priority = TaskPriority(request.priority)
        required_skills = [AgentSkill(skill) for skill in request.required_skills if skill in [s.value for s in AgentSkill]]
        
        due_date = None
        if request.due_date:
            due_date = datetime.fromisoformat(request.due_date.replace('Z', '+00:00'))
        
        task_id = await task_hierarchy_manager.create_task(
            project_id=project_id,
            title=request.title,
            description=request.description,
            task_type=task_type,
            created_by="system",  # TODO: Get from authentication
            priority=priority,
            parent_task_id=request.parent_task_id,
            required_skills=required_skills,
            estimated_hours=request.estimated_hours,
            due_date=due_date,
            file_paths=request.file_paths,
            acceptance_criteria=request.acceptance_criteria,
            tags=request.tags
        )
        
        if task_id:
            return {"success": True, "task_id": task_id, "message": "Task created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create task")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task type or priority: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "create_task"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/tasks/assign")
async def assign_task(project_id: str, request: AssignTaskRequest):
    """Assign a task to an agent"""
    try:
        if request.agent_id:
            # Manual assignment
            success = await task_hierarchy_manager.assign_task(
                task_id=request.task_id,
                agent_id=request.agent_id,
                assigned_by="system"
            )
            assigned_agent = request.agent_id
        else:
            # Auto assignment
            assigned_agent = await task_hierarchy_manager.auto_assign_task(
                task_id=request.task_id,
                assigned_by="system",
                algorithm=request.assignment_algorithm
            )
            success = bool(assigned_agent)
        
        if success:
            return {
                "success": True,
                "assigned_agent": assigned_agent,
                "message": "Task assigned successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to assign task")
            
    except Exception as e:
        logger.log_error(e, {"action": "assign_task"})
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_id}/tasks/progress")
async def update_task_progress(project_id: str, request: UpdateTaskProgressRequest):
    """Update task progress"""
    try:
        status = TaskStatus(request.status) if request.status else None
        
        success = await task_hierarchy_manager.update_task_progress(
            task_id=request.task_id,
            progress_percentage=request.progress_percentage,
            status=status,
            actual_hours=request.actual_hours
        )
        
        if success:
            return {"success": True, "message": "Task progress updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update task progress")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "update_task_progress"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str, task_type: Optional[str] = None, status: Optional[str] = None):
    """Get all tasks for a project"""
    try:
        task_type_filter = TaskType(task_type) if task_type else None
        status_filter = [TaskStatus(status)] if status else None
        
        tasks = await task_hierarchy_manager.get_project_tasks(
            project_id=project_id,
            task_type=task_type_filter,
            status_filter=status_filter
        )
        
        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task type or status: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "get_project_tasks"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/agents/{agent_id}/tasks")
async def get_agent_tasks(project_id: str, agent_id: str, status: Optional[str] = None):
    """Get tasks assigned to an agent"""
    try:
        status_filter = [TaskStatus(status)] if status else None
        
        tasks = await task_hierarchy_manager.get_agent_tasks(
            agent_id=agent_id,
            project_id=project_id,
            status_filter=status_filter
        )
        
        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "get_agent_tasks"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/tasks/{task_id}/hierarchy")
async def get_task_hierarchy(project_id: str, task_id: str):
    """Get task hierarchy (parent and children)"""
    try:
        hierarchy = await task_hierarchy_manager.get_task_hierarchy(task_id)
        
        if not hierarchy:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return hierarchy
        
    except Exception as e:
        logger.log_error(e, {"action": "get_task_hierarchy"})
        raise HTTPException(status_code=500, detail=str(e))


# File Lock Management Endpoints
@router.post("/projects/{project_id}/locks/acquire")
async def acquire_file_lock(project_id: str, request: AcquireLockRequest):
    """Acquire a file lock"""
    try:
        lock_manager = get_lock_manager(project_id)
        lock_type = LockType(request.lock_type)
        
        lock_id = await lock_manager.acquire_lock(
            agent_id=request.agent_id,
            file_path=request.file_path,
            lock_type=lock_type,
            timeout=request.timeout
        )
        
        if lock_id:
            return {"success": True, "lock_id": lock_id, "message": "File lock acquired"}
        else:
            raise HTTPException(status_code=409, detail="Unable to acquire file lock")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid lock type: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "acquire_file_lock"})
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/locks/{lock_id}")
async def release_file_lock(project_id: str, lock_id: str, agent_id: Optional[str] = None):
    """Release a file lock"""
    try:
        lock_manager = get_lock_manager(project_id)
        
        success = await lock_manager.release_lock(lock_id, agent_id)
        
        if success:
            return {"success": True, "message": "File lock released"}
        else:
            raise HTTPException(status_code=400, detail="Failed to release file lock")
            
    except Exception as e:
        logger.log_error(e, {"action": "release_file_lock"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/locks")
async def get_active_locks(project_id: str):
    """Get all active file locks"""
    try:
        lock_manager = get_lock_manager(project_id)
        active_locks = await lock_manager.get_active_locks()
        
        return {
            "locks": [lock.to_dict() for lock in active_locks],
            "total": len(active_locks)
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "get_active_locks"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/agents/{agent_id}/locks")
async def get_agent_locks(project_id: str, agent_id: str):
    """Get all locks held by an agent"""
    try:
        lock_manager = get_lock_manager(project_id)
        agent_locks = await lock_manager.get_agent_locks(agent_id)
        
        return {
            "locks": [lock.to_dict() for lock in agent_locks],
            "total": len(agent_locks)
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "get_agent_locks"})
        raise HTTPException(status_code=500, detail=str(e))


# Context Management Endpoints
@router.post("/projects/{project_id}/context")
async def get_agent_context(project_id: str, request: ContextRequest):
    """Get comprehensive context for an agent"""
    try:
        context_req = ContextRequest(
            project_id=project_id,
            agent_id=request.agent_id,
            query=request.query,
            max_tokens=request.max_tokens,
            include_history=request.include_history,
            time_range=request.time_range,
            content_types=request.content_types,
            file_filter=request.file_filter
        )
        
        context = await advanced_context_manager.get_agent_context(
            context_req, request.strategy
        )
        
        return context
        
    except Exception as e:
        logger.log_error(e, {"action": "get_agent_context"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/context/unlimited")
async def get_unlimited_context(project_id: str, request: UnlimitedContextRequest):
    """Get unlimited context using stateless RAG optimization"""
    check_collaboration_enabled()
    
    try:
        # Parse time filter
        time_filter = None
        if request.time_filter:
            if request.time_filter.lower() == "1 day ago":
                time_filter = datetime.now() - timedelta(days=1)
            elif request.time_filter.lower() == "1 week ago":
                time_filter = datetime.now() - timedelta(days=7)
            elif request.time_filter.lower() == "1 month ago":
                time_filter = datetime.now() - timedelta(days=30)
            else:
                try:
                    time_filter = datetime.fromisoformat(request.time_filter.replace('Z', '+00:00'))
                except:
                    pass  # Invalid format, use None
        
        context_response = await stateless_rag_manager.get_unlimited_context(
            project_id=project_id,
            agent_id=request.agent_id,
            query=request.query,
            max_tokens=request.max_tokens,
            strategy=request.strategy,
            include_history=request.include_history,
            time_filter=time_filter
        )
        
        return context_response
        
    except Exception as e:
        logger.log_error(e, {"action": "get_unlimited_context"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/context/add")
async def add_content_to_context(project_id: str, request: AddContentRequest):
    """Add content to the stateless RAG system"""
    check_collaboration_enabled()
    
    try:
        chunk_ids = await stateless_rag_manager.add_optimized_content(
            project_id=project_id,
            agent_id=request.agent_id,
            content=request.content,
            content_type=request.content_type,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "chunk_ids": chunk_ids,
            "chunks_created": len(chunk_ids),
            "message": f"Content added and optimized into {len(chunk_ids)} chunks"
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "add_content_to_context"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/context/summary")
async def get_context_summary(project_id: str):
    """Get context availability summary for a project"""
    try:
        summary = await advanced_context_manager.get_context_summary(project_id)
        return summary
        
    except Exception as e:
        logger.log_error(e, {"action": "get_context_summary"})
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring and Analytics Endpoints
@router.get("/projects/{project_id}/dashboard")
async def get_project_dashboard(project_id: str):
    """Get comprehensive project dashboard data"""
    try:
        dashboard_data = await monitoring_dashboard.get_dashboard_data(project_id)
        return dashboard_data
        
    except Exception as e:
        logger.log_error(e, {"action": "get_project_dashboard"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/agents/{agent_id}/dashboard")
async def get_agent_dashboard(project_id: str, agent_id: str):
    """Get agent-specific dashboard data"""
    try:
        dashboard_data = await monitoring_dashboard.get_agent_dashboard(project_id, agent_id)
        return dashboard_data
        
    except Exception as e:
        logger.log_error(e, {"action": "get_agent_dashboard"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/performance")
async def get_team_performance(project_id: str, period: str = "week"):
    """Get team performance analytics"""
    try:
        analytics_period = AnalyticsPeriod(period)
        performance_data = await performance_analytics.generate_performance_report(
            project_id=project_id,
            period=analytics_period
        )
        
        return performance_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid period: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "get_team_performance"})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/agents/{agent_id}/performance")
async def get_agent_performance(project_id: str, agent_id: str, period: str = "week"):
    """Get individual agent performance analytics"""
    try:
        analytics_period = AnalyticsPeriod(period)
        performance_data = await performance_analytics.generate_performance_report(
            project_id=project_id,
            agent_id=agent_id,
            period=analytics_period
        )
        
        return performance_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid period: {str(e)}")
    except Exception as e:
        logger.log_error(e, {"action": "get_agent_performance"})
        raise HTTPException(status_code=500, detail=str(e))


# Real-time WebSocket endpoint
@router.websocket("/projects/{project_id}/ws")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        # Extract agent_id from query params or headers
        agent_id = websocket.query_params.get('agent_id')
        
        # Register WebSocket connection
        monitoring_dashboard.websocket_manager.add_connection(websocket, project_id, agent_id)
        
        # Send initial dashboard data
        dashboard_data = await monitoring_dashboard.get_dashboard_data(project_id)
        await websocket.send_text(json.dumps({
            "type": "dashboard_data",
            "data": dashboard_data
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "get_dashboard":
                    dashboard_data = await monitoring_dashboard.get_dashboard_data(project_id)
                    await websocket.send_text(json.dumps({
                        "type": "dashboard_data", 
                        "data": dashboard_data
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.log_error(e, {"action": "websocket_message_handler"})
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.log_error(e, {"action": "websocket_connection"})
    finally:
        # Clean up connection
        monitoring_dashboard.websocket_manager.remove_connection(websocket)