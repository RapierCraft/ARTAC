"""
ARTAC Assembly Platform API Endpoints
Provides interface to the social-technical collaboration layer
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.artac_assembly import artac_assembly, CollaborationMode, ResourceState
from services.perpetual_efficiency_model import perpetual_efficiency_model, AgentPersonalityProcess
from services.ceo_service import get_ceo_service

router = APIRouter()


class ProjectGenesisRequest(BaseModel):
    human_directive: str
    project_title: str
    estimated_budget_hours: int
    timeline_weeks: int


class AssemblyCommandRequest(BaseModel):
    command: str
    parameters: Dict[str, Any]


class MessageComplexityRequest(BaseModel):
    content: str
    message_type: str = "general"


class ComputationalTaskRequest(BaseModel):
    task_type: str
    description: str
    estimated_duration_minutes: int
    priority: str = "normal"


@router.post("/genesis")
async def initiate_project_genesis(request: ProjectGenesisRequest):
    """Initiate Project Genesis - Human-to-CEO handoff with assembly creation"""
    try:
        if not artac_assembly:
            raise HTTPException(status_code=503, detail="Assembly platform not initialized")
        
        # Use CEO service to get CEO agent ID
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not available")
        
        # For now, use a default CEO agent ID
        ceo_agent_id = "ceo-001"
        
        project_id = await artac_assembly.initiate_project_genesis(
            human_directive=request.human_directive,
            project_title=request.project_title,
            estimated_budget_hours=request.estimated_budget_hours,
            timeline_weeks=request.timeline_weeks,
            ceo_agent_id=ceo_agent_id
        )
        
        if not project_id:
            raise HTTPException(status_code=500, detail="Failed to initiate project genesis")
        
        return {
            "success": True,
            "project_id": project_id,
            "message": f"Project '{request.project_title}' initiated in Assembly platform",
            "ceo_agent": ceo_agent_id,
            "next_phase": "Squad Formation & Technical Lead Assignment"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project genesis failed: {str(e)}")


@router.post("/channels/{channel_id}/message")
async def handle_assembly_message(channel_id: str, message: MessageComplexityRequest):
    """Handle message in assembly channel with complexity analysis"""
    try:
        if not artac_assembly:
            raise HTTPException(status_code=503, detail="Assembly platform not initialized")
        
        # For now, use system as sender
        sender_id = "system"
        
        result = await artac_assembly.handle_message_with_complexity_analysis(
            channel_id=channel_id,
            sender_id=sender_id,
            content=message.content,
            message_type=message.message_type
        )
        
        return {
            "success": True,
            "analysis": result,
            "message": "Message processed with complexity analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Message handling failed: {str(e)}")


@router.post("/channels/{channel_id}/command")
async def execute_assembly_command(channel_id: str, command_request: AssemblyCommandRequest):
    """Execute assembly platform commands (/decision, /task, etc.)"""
    try:
        if not artac_assembly:
            raise HTTPException(status_code=503, detail="Assembly platform not initialized")
        
        # For now, use system as sender
        sender_id = "system"
        
        result = await artac_assembly.execute_assembly_command(
            channel_id=channel_id,
            sender_id=sender_id,
            command=command_request.command,
            parameters=command_request.parameters
        )
        
        return {
            "success": True,
            "result": result,
            "command": command_request.command
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@router.get("/agents/{agent_id}/status")
async def get_agent_assembly_status(agent_id: str):
    """Get agent's current assembly and processing status"""
    try:
        # Get resource status from assembly
        resource_status = None
        if artac_assembly:
            resource_status = await artac_assembly.get_agent_resource_status(agent_id)
        
        # Get processing status from efficiency model
        processing_status = await perpetual_efficiency_model.get_agent_processing_status(agent_id)
        
        # Check interruption status
        can_interrupt = False
        interruption_cost = 0
        interruption_reason = "Agent not found"
        
        if processing_status:
            can_interrupt, interruption_cost, interruption_reason = await perpetual_efficiency_model.can_interrupt_agent(agent_id)
        
        return {
            "agent_id": agent_id,
            "resource_status": {
                "current_state": resource_status.current_state.value if resource_status else "unknown",
                "state_reason": resource_status.state_reason if resource_status else "Not initialized",
                "computational_load": resource_status.computational_load if resource_status else 0.0,
                "available_capacity": resource_status.available_capacity if resource_status else 1.0,
                "queued_messages": len(resource_status.queued_messages) if resource_status else 0
            },
            "processing_status": processing_status,
            "interruption_info": {
                "can_interrupt": can_interrupt,
                "cost_seconds": interruption_cost,
                "reason": interruption_reason
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.post("/agents/{agent_id}/task/computational")
async def start_computational_task(agent_id: str, task_request: ComputationalTaskRequest):
    """Start a computational task for an agent"""
    try:
        if not artac_assembly:
            raise HTTPException(status_code=503, detail="Assembly platform not initialized")
        
        from datetime import timedelta
        
        task_id = await artac_assembly.start_computational_task(
            agent_id=agent_id,
            task_type=task_request.task_type,
            description=task_request.description,
            estimated_duration=timedelta(minutes=task_request.estimated_duration_minutes),
            priority=task_request.priority
        )
        
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to start computational task")
        
        return {
            "success": True,
            "task_id": task_id,
            "agent_id": agent_id,
            "estimated_duration_minutes": task_request.estimated_duration_minutes,
            "message": f"Computational task '{task_request.task_type}' started for agent {agent_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.post("/agents/{agent_id}/task/processing")
async def start_processing_task(agent_id: str, task_type: str, description: str, complexity: float = 0.5):
    """Start a processing task using the perpetual efficiency model"""
    try:
        task_id = await perpetual_efficiency_model.start_processing_task(
            agent_id=agent_id,
            task_type=task_type,
            description=description,
            input_complexity=complexity,
            requires_validation=True
        )
        
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to start processing task")
        
        # Calculate response time for this task
        response_time, reason = await perpetual_efficiency_model.calculate_technical_response_time(
            agent_id=agent_id,
            task_type=task_type,
            input_complexity=complexity
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "estimated_response_time_seconds": response_time,
            "reasoning": reason,
            "message": f"Processing task '{task_type}' started for agent {agent_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing task: {str(e)}")


@router.get("/projects/{project_id}/overview")
async def get_project_assembly_overview(project_id: str):
    """Get assembly overview for a project"""
    try:
        if not artac_assembly:
            raise HTTPException(status_code=503, detail="Assembly platform not initialized")
        
        overview = await artac_assembly.get_assembly_overview(project_id)
        
        return {
            "success": True,
            "overview": overview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project overview: {str(e)}")


@router.post("/agents/{agent_id}/initialize")
async def initialize_agent_for_assembly(
    agent_id: str,
    role: str,
    capabilities: List[str],
    computational_capacity: float = 1.0,
    personality_process: Optional[str] = None
):
    """Initialize agent for Assembly platform participation"""
    try:
        # Initialize in Assembly platform
        if artac_assembly:
            await artac_assembly.initialize_agent_assembly_profile(
                agent_id=agent_id,
                role=role,
                capabilities=capabilities,
                computational_capacity=computational_capacity
            )
        
        # Initialize in Perpetual Efficiency Model
        personality = None
        if personality_process:
            try:
                personality = AgentPersonalityProcess(personality_process)
            except ValueError:
                personality = None
        
        await perpetual_efficiency_model.initialize_agent_efficiency_profile(
            agent_id=agent_id,
            role=role,
            specializations=capabilities,
            processing_capacity=computational_capacity,
            personality_process=personality
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "role": role,
            "capabilities": capabilities,
            "personality_process": personality.value if personality else "auto_assigned",
            "message": f"Agent {agent_id} initialized for Assembly platform"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")


@router.get("/agents/{agent_id}/response-time")
async def calculate_agent_response_time(
    agent_id: str,
    task_type: str = "simple_response",
    complexity: float = 0.5,
    requires_collaboration: bool = False
):
    """Calculate technical response time for an agent"""
    try:
        response_time, reason = await perpetual_efficiency_model.calculate_technical_response_time(
            agent_id=agent_id,
            task_type=task_type,
            input_complexity=complexity,
            requires_collaboration=requires_collaboration
        )
        
        return {
            "agent_id": agent_id,
            "task_type": task_type,
            "input_complexity": complexity,
            "estimated_response_time_seconds": response_time,
            "reasoning": reason,
            "requires_collaboration": requires_collaboration
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response time calculation failed: {str(e)}")


@router.get("/efficiency/overview")
async def get_efficiency_overview():
    """Get overview of the perpetual efficiency model performance"""
    try:
        # Get all agent statuses
        agent_statuses = {}
        
        # This would iterate through all known agents
        # For now, return a summary structure
        
        return {
            "model": "Perpetual Efficiency Model",
            "status": "operational",
            "total_agents": len(perpetual_efficiency_model.agent_profiles),
            "active_processing_tasks": len(perpetual_efficiency_model.active_processing_tasks),
            "average_efficiency": 0.85,  # Would calculate from actual metrics
            "24_7_operational": True,
            "human_like_delays_eliminated": True,
            "technical_resource_states": [state.value for state in ResourceState],
            "personality_processes": [process.value for process in AgentPersonalityProcess]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get efficiency overview: {str(e)}")


@router.get("/status")
async def get_assembly_platform_status():
    """Get overall Assembly platform status"""
    try:
        return {
            "assembly_platform": {
                "status": "operational" if artac_assembly else "not_initialized",
                "active_sessions": len(artac_assembly.active_sessions) if artac_assembly else 0,
                "computational_tasks": len(artac_assembly.computational_tasks) if artac_assembly else 0
            },
            "efficiency_model": {
                "status": "operational",
                "agent_profiles": len(perpetual_efficiency_model.agent_profiles),
                "active_processing_tasks": len(perpetual_efficiency_model.active_processing_tasks),
                "model_type": "perpetual_efficiency"
            },
            "features": {
                "24_7_operation": True,
                "technical_resource_states": True,
                "complexity_based_timing": True,
                "human_in_the_loop": True,
                "institutional_memory": True,
                "collaborative_commands": True
            },
            "timestamp": "2025-08-01T16:30:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")