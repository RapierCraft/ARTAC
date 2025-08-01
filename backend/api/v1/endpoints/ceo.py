"""
ARTAC CEO API Endpoints
Real CEO agent endpoints for project management and hiring decisions
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.ceo_service import get_ceo_service
from services.agent_manager import get_agent_manager
from services.inter_agent_communication import inter_agent_comm

router = APIRouter()


class ProjectRequest(BaseModel):
    title: str
    description: str
    user_id: Optional[str] = "client"


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "user"


@router.post("/project")
async def submit_project_to_ceo(project_data: ProjectRequest, request: Request):
    """Submit a new project to the CEO for analysis and team assembly"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        # CEO processes the project request
        response = await ceo_service.receive_project_request(
            title=project_data.title,
            description=project_data.description,
            user_id=project_data.user_id
        )
        
        return {
            "message": "Project received and analyzed by CEO",
            "ceo_response": response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CEO processing failed: {str(e)}")


@router.post("/chat")
async def chat_with_ceo(chat_data: ChatRequest, request: Request):
    """Chat with the CEO agent"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        # Check if this is a project request
        message_lower = chat_data.message.lower()
        if any(keyword in message_lower for keyword in ['project', 'client', 'order', 'build', 'create', 'develop']):
            # Extract a better project name from the message
            title = "Client Project"  # Default
            message = chat_data.message.lower()
            
            # Try to extract a more specific name
            if 'calculator' in message:
                title = "Calculator App"
            elif 'dashboard' in message:
                title = "System Dashboard"
            elif 'e-commerce' in message or 'ecommerce' in message:
                title = "E-commerce Platform"
            elif 'mobile app' in message:
                title = "Mobile Application"
            elif 'web' in message and 'app' in message:
                title = "Web Application"
            elif 'website' in message:
                title = "Website"
            elif 'api' in message:
                title = "API Service"
            elif 'database' in message:
                title = "Database System"
            elif 'monitoring' in message or 'metrics' in message:
                title = "Monitoring System"
            
            description = chat_data.message
            
            # Process as project request
            response = await ceo_service.receive_project_request(
                title=title,
                description=description,
                user_id=chat_data.user_id
            )
            
            # Create project channel
            project_channel_id = f"project-{response['project_id']}"
            await inter_agent_comm.create_channel(
                channel_id=project_channel_id,
                name=f"Project: {title}",
                description=f"Communication channel for {title}",
                channel_type="project"
            )
            
            # Send welcome messages to project channel
            await inter_agent_comm.send_message(
                channel_id=project_channel_id,
                sender_id="ceo-001",
                sender_name="ARTAC CEO",
                content=f"🎯 **PROJECT INITIATED: {title}**\n\n"
                       f"I've analyzed the requirements and assembled our team:\n\n"
                       f"**Team Members:**\n" +
                       "\n".join([f"• {agent['name']} - {agent['role'].title()}" for agent in response['hired_agents']]) +
                       f"\n\n**Project Scope:** {description}\n"
                       f"**Estimated Timeline:** {response['ceo_analysis']['estimated_hours']} hours\n"
                       f"**Budget Allocated:** ${response['ceo_analysis']['estimated_budget']}\n\n"
                       f"Team, let's deliver excellence for our client! 🚀",
                message_type="announcement"
            )
            
            # Send individual welcome messages to each hired agent
            for agent in response['hired_agents']:
                await inter_agent_comm.send_direct_message(
                    from_agent="ceo-001",
                    to_agent=agent['id'],
                    content=f"Welcome to ARTAC, {agent['name']}! 👋\n\n"
                           f"I've just hired you for the '{title}' project. Your expertise in {agent['role']} "
                           f"will be crucial for our success.\n\n"
                           f"Please join the project channel: #{project_channel_id}\n\n"
                           f"Looking forward to working with you!\n\n"
                           f"Best regards,\nARTAC CEO",
                    priority="high"
                )
            
            # Send announcement to general channel about new project
            await inter_agent_comm.send_message(
                channel_id="general",
                sender_id="ceo-001", 
                sender_name="ARTAC CEO",
                content=f"📢 **NEW PROJECT ANNOUNCEMENT**\n\n"
                       f"We've just secured a new project: '{title}'\n\n"
                       f"I've hired {len(response['hired_agents'])} specialized agents:\n" +
                       "\n".join([f"• {agent['name']} ({agent['role']})" for agent in response['hired_agents']]) +
                       f"\n\nThis demonstrates ARTAC's rapid response capability and our commitment to client success! 💪",
                message_type="company_announcement"
            )
            
            return {
                "message": f"✅ **PROJECT LAUNCHED SUCCESSFULLY!**\n\n" +
                          f"**Project ID:** {response['project_id']}\n" +
                          f"**Team Assembled:** {len(response['hired_agents'])} agents hired\n" +
                          f"**Project Channel:** #{project_channel_id}\n\n" +
                          f"I've created the project channel and welcomed all team members. "
                          f"You can monitor progress in the #{project_channel_id} channel.\n\n" +
                          f"**Next Steps:**\n"
                          f"• Team members are being onboarded\n"
                          f"• Initial tasks are being assigned\n"
                          f"• Project timeline: {response['ceo_analysis']['estimated_hours']} hours\n\n"
                          f"Work has begun immediately! 🚀",
                "type": "project_response",
                "project_data": response,
                "project_channel": project_channel_id,
                "actions_taken": [
                    "Project channel created",
                    "Team members hired and welcomed",
                    "Company announcement sent",
                    "Individual onboarding messages sent"
                ]
            }
        else:
            # General CEO conversation
            return {
                "message": "Hello! As ARTAC's CEO, I'm here to help with project analysis, team assembly, and strategic decisions. " +
                          "Tell me about any project you need completed and I'll immediately hire the right agents to get it done!",
                "type": "general_response"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CEO chat failed: {str(e)}")


@router.get("/project/{project_id}/status")
async def get_project_status(project_id: str, request: Request):
    """Get current status of a project managed by CEO"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        status = await ceo_service.get_project_status(project_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project status: {str(e)}")


@router.get("/context/{user_id}")
async def get_conversation_context(user_id: str, request: Request):
    """Get conversation context for user continuity"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        context = ceo_service.get_conversation_context(user_id)
        return {"context": context}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.get("/projects")
async def get_all_projects(request: Request):
    """Get all active projects managed by CEO"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        projects = []
        for project_id, project in ceo_service.active_projects.items():
            projects.append({
                "id": project.id,
                "title": project.title,
                "status": project.status,
                "complexity": project.complexity.value,
                "estimated_hours": project.estimated_hours,
                "team_size": len(project.assigned_agents),
                "created_at": project.created_at.isoformat()
            })
        
        return {"projects": projects}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")


@router.get("/hiring-history")
async def get_hiring_history(request: Request):
    """Get CEO's hiring decision history"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            raise HTTPException(status_code=503, detail="CEO service not initialized")
        
        history = []
        for decision in ceo_service.hiring_decisions:
            history.append({
                "project_id": decision.project_id,
                "roles_hired": [role.value for role in decision.required_roles],
                "reasoning": decision.reasoning,
                "estimated_budget": decision.estimated_budget,
                "timeline_days": decision.timeline_days,
                "created_at": decision.created_at.isoformat()
            })
        
        return {"hiring_history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hiring history: {str(e)}")


@router.get("/status")
async def get_ceo_status(request: Request):
    """Get CEO service status"""
    try:
        ceo_service = get_ceo_service()
        if not ceo_service:
            return {"status": "not_initialized", "message": "CEO service not available"}
        
        return {
            "status": "operational",
            "active_projects": len(ceo_service.active_projects),
            "total_hiring_decisions": len(ceo_service.hiring_decisions),
            "active_conversations": len(ceo_service.conversation_context)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CEO status: {str(e)}")