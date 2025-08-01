"""
ARTAC Agents API Endpoints
Real agent management and monitoring endpoints
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from services.agent_manager import AgentRole, AgentSkill

router = APIRouter()


class AgentCreate(BaseModel):
    role: str
    skills: List[str] = []
    specialization: List[str] = []
    auto_start: bool = True


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    performance_score: float
    specialization: List[str]
    skills: List[str]
    created_at: str
    updated_at: str


class AgentStatusResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    performance_score: float
    specialization: List[str]
    active_tasks: int
    claude_session: dict
    created_at: str
    updated_at: str


@router.get("/", response_model=List[AgentResponse])
async def get_agents(request: Request):
    """Get all agents"""
    try:
        agent_manager = request.app.state.agent_manager
        agents = await agent_manager.get_all_agents()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role.value,
                "status": agent.status.value,
                "performance_score": agent.performance_score,
                "specialization": agent.specialization,
                "skills": [skill.value for skill in agent.skills],
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat()
            }
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")


@router.get("/status", response_model=List[AgentStatusResponse])
async def get_agents_status(request: Request):
    """Get detailed status of all agents"""
    try:
        agent_manager = request.app.state.agent_manager
        agents = await agent_manager.get_all_agents()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role.value,
                "status": agent.status.value,
                "performance_score": agent.performance_score,
                "specialization": agent.specialization,
                "active_tasks": len(agent.active_tasks),
                "claude_session": {
                    "active": agent.claude_session.is_active if agent.claude_session else False,
                    "session_id": agent.claude_session.session_id if agent.claude_session else None,
                    "working_directory": agent.working_directory,
                    "process_id": agent.claude_session.process.pid if agent.claude_session and agent.claude_session.process else None
                },
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat()
            }
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.get("/{agent_id}", response_model=AgentStatusResponse)
async def get_agent(agent_id: str, request: Request):
    """Get specific agent details"""
    try:
        agent_manager = request.app.state.agent_manager
        agent = await agent_manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "status": agent.status.value,
            "performance_score": agent.performance_score,
            "specialization": agent.specialization,
            "active_tasks": len(agent.active_tasks),
            "claude_session": {
                "active": agent.claude_session.is_active if agent.claude_session else False,
                "session_id": agent.claude_session.session_id if agent.claude_session else None,
                "working_directory": agent.working_directory,
                "process_id": agent.claude_session.process.pid if agent.claude_session and agent.claude_session.process else None
            },
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.post("/", response_model=AgentResponse)
async def create_agent(agent_data: AgentCreate, request: Request):
    """Create a new agent with real Claude Code session"""
    try:
        agent_manager = request.app.state.agent_manager
        
        # Validate role
        try:
            role = AgentRole(agent_data.role.lower())
        except ValueError:
            valid_roles = [role.value for role in AgentRole]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid role '{agent_data.role}'. Valid roles: {valid_roles}"
            )
        
        # Validate skills
        skills = []
        for skill_str in agent_data.skills:
            try:
                skill = AgentSkill(skill_str.lower())
                skills.append(skill)
            except ValueError:
                valid_skills = [skill.value for skill in AgentSkill]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid skill '{skill_str}'. Valid skills: {valid_skills}"
                )
        
        # Create the agent
        agent = await agent_manager.create_agent(
            role=role,
            skills=skills,
            specialization=agent_data.specialization,
            auto_start=agent_data.auto_start
        )
        
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "status": agent.status.value,
            "performance_score": agent.performance_score,
            "specialization": agent.specialization,
            "skills": [skill.value for skill in agent.skills],
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.delete("/{agent_id}")
async def terminate_agent(agent_id: str, request: Request):
    """Terminate an agent"""
    try:
        agent_manager = request.app.state.agent_manager
        success = await agent_manager.terminate_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found or already terminated")
        
        return {"message": f"Agent {agent_id} terminated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate agent: {str(e)}")


@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, status_data: dict, request: Request):
    """Update agent status"""
    try:
        agent_manager = request.app.state.agent_manager
        agent = await agent_manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update status if provided
        if "status" in status_data:
            try:
                from services.agent_manager import AgentStatus
                new_status = AgentStatus(status_data["status"])
                agent.status = new_status
                agent.updated_at = datetime.utcnow()
                
                # Update in database
                await agent_manager._store_agent(agent)
                
            except ValueError:
                from services.agent_manager import AgentStatus
                valid_statuses = [status.value for status in AgentStatus]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Valid options: {valid_statuses}"
                )
        
        return {"message": f"Agent {agent_id} status updated to {agent.status.value}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent status: {str(e)}")


@router.get("/manager/status")
async def get_manager_status(request: Request):
    """Get agent manager status"""
    try:
        agent_manager = request.app.state.agent_manager
        return agent_manager.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get manager status: {str(e)}")


@router.post("/{agent_id}/tasks")
async def assign_task_to_agent(agent_id: str, task_data: dict, request: Request):
    """Assign a task to an agent"""
    try:
        agent_manager = request.app.state.agent_manager
        agent = await agent_manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Add task to agent's active tasks
        task_id = task_data.get("task_id", f"task-{len(agent.active_tasks) + 1}")
        agent.active_tasks.append(task_id)
        
        # Update agent in database
        await agent_manager._store_agent(agent)
        
        return {
            "message": f"Task assigned to agent {agent_id}",
            "task_id": task_id,
            "agent_name": agent.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")