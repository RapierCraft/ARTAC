"""
Inter-Agent Communication API Endpoints
Provides REST API for agents to communicate with each other
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.inter_agent_communication import (
    inter_agent_comm, 
    MessageType, 
    MessagePriority, 
    AgentMessage,
    TeamConversation,
    CollaborationRequest
)
from models.agent import AgentRole
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class DirectMessageRequest(BaseModel):
    to_agent_id: str
    subject: str
    content: str
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None


class TeamMessageRequest(BaseModel):
    team_id: str
    subject: str
    content: str
    priority: MessagePriority = MessagePriority.NORMAL


class BroadcastMessageRequest(BaseModel):
    subject: str
    content: str
    target_roles: Optional[List[AgentRole]] = None
    priority: MessagePriority = MessagePriority.NORMAL


class CollaborationRequestModel(BaseModel):
    to_agent_ids: List[str]
    task_id: str
    description: str
    required_skills: Optional[List[str]] = None
    urgency: MessagePriority = MessagePriority.NORMAL


class CollaborationResponseModel(BaseModel):
    request_id: str
    response: str  # "accept", "decline", "counter"
    message: Optional[str] = ""


class CreateTeamRequest(BaseModel):
    name: str
    description: str
    member_ids: List[str]


class MeetingRequest(BaseModel):
    attendee_ids: List[str]
    subject: str
    description: str
    scheduled_time: datetime


class MessageResponse(BaseModel):
    id: str
    from_agent_id: str
    to_agent_id: Optional[str]
    team_id: Optional[str]
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    read: bool
    replied: bool
    archived: bool


# Direct Messaging Endpoints
@router.post("/agents/{agent_id}/messages/send-direct")
async def send_direct_message(agent_id: str, request: DirectMessageRequest):
    """Send a direct message from one agent to another"""
    try:
        message_id = await inter_agent_comm.send_direct_message(
            from_agent_id=agent_id,
            to_agent_id=request.to_agent_id,
            subject=request.subject,
            content=request.content,
            priority=request.priority,
            metadata=request.metadata
        )
        
        return {"success": True, "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Error sending direct message: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/messages/send-team")
async def send_team_message(agent_id: str, request: TeamMessageRequest):
    """Send a message to a team conversation"""
    try:
        message_id = await inter_agent_comm.send_team_message(
            from_agent_id=agent_id,
            team_id=request.team_id,
            subject=request.subject,
            content=request.content,
            priority=request.priority
        )
        
        return {"success": True, "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Error sending team message: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/messages/broadcast")
async def broadcast_message(agent_id: str, request: BroadcastMessageRequest, 
                          background_tasks: BackgroundTasks):
    """Broadcast a message to all agents or specific roles"""
    try:
        message_id = await inter_agent_comm.broadcast_message(
            from_agent_id=agent_id,
            subject=request.subject,
            content=request.content,
            target_roles=request.target_roles,
            priority=request.priority
        )
        
        return {"success": True, "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/messages", response_model=List[MessageResponse])
async def get_agent_messages(agent_id: str, unread_only: bool = False, limit: int = 50):
    """Get messages for a specific agent"""
    try:
        messages = await inter_agent_comm.get_agent_messages(
            agent_id=agent_id,
            unread_only=unread_only,
            limit=limit
        )
        
        return [MessageResponse(**message.dict()) for message in messages]
        
    except Exception as e:
        logger.error(f"Error getting agent messages: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/agents/{agent_id}/messages/{message_id}/read")
async def mark_message_read(agent_id: str, message_id: str):
    """Mark a message as read"""
    try:
        success = await inter_agent_comm.mark_message_read(agent_id, message_id)
        
        if success:
            return {"success": True, "message": "Message marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Message not found or access denied")
            
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Collaboration Endpoints
@router.post("/agents/{agent_id}/collaboration/request")
async def request_collaboration(agent_id: str, request: CollaborationRequestModel):
    """Request collaboration from other agents"""
    try:
        request_id = await inter_agent_comm.request_collaboration(
            from_agent_id=agent_id,
            to_agent_ids=request.to_agent_ids,
            task_id=request.task_id,
            description=request.description,
            required_skills=request.required_skills,
            urgency=request.urgency
        )
        
        return {"success": True, "request_id": request_id}
        
    except Exception as e:
        logger.error(f"Error requesting collaboration: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/collaboration/respond")
async def respond_to_collaboration(agent_id: str, response: CollaborationResponseModel):
    """Respond to a collaboration request"""
    try:
        success = await inter_agent_comm.respond_to_collaboration(
            agent_id=agent_id,
            request_id=response.request_id,
            response=response.response,
            message=response.message
        )
        
        if success:
            return {"success": True, "message": "Response sent"}
        else:
            raise HTTPException(status_code=404, detail="Collaboration request not found")
            
    except Exception as e:
        logger.error(f"Error responding to collaboration: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/collaboration/requests")
async def get_collaboration_requests(agent_id: str):
    """Get collaboration requests for an agent"""
    try:
        # Get requests where this agent is a target
        requests = []
        for request in inter_agent_comm.collaboration_requests.values():
            if agent_id in request.to_agent_ids or request.from_agent_id == agent_id:
                requests.append(request.dict())
        
        return requests
        
    except Exception as e:
        logger.error(f"Error getting collaboration requests: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Team Management Endpoints
@router.post("/agents/{agent_id}/teams/create")
async def create_team(agent_id: str, request: CreateTeamRequest):
    """Create a new team conversation"""
    try:
        team_id = await inter_agent_comm.create_team_conversation(
            creator_id=agent_id,
            name=request.name,
            description=request.description,
            member_ids=request.member_ids
        )
        
        return {"success": True, "team_id": team_id}
        
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/teams", response_model=List[TeamConversation])
async def get_agent_teams(agent_id: str):
    """Get all teams an agent is part of"""
    try:
        teams = await inter_agent_comm.get_team_conversations(agent_id)
        return teams
        
    except Exception as e:
        logger.error(f"Error getting agent teams: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/teams/{team_id}/add-member")
async def add_member_to_team(agent_id: str, team_id: str, member_id: str):
    """Add a member to a team"""
    try:
        success = await inter_agent_comm.add_agent_to_team(
            team_id=team_id,
            agent_id=member_id,
            added_by=agent_id
        )
        
        if success:
            return {"success": True, "message": "Member added to team"}
        else:
            raise HTTPException(status_code=404, detail="Team not found or member already exists")
            
    except Exception as e:
        logger.error(f"Error adding member to team: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Meeting Endpoints
@router.post("/agents/{agent_id}/meetings/schedule")
async def schedule_meeting(agent_id: str, request: MeetingRequest):
    """Schedule a meeting between agents"""
    try:
        meeting_id = await inter_agent_comm.schedule_meeting(
            organizer_id=agent_id,
            attendee_ids=request.attendee_ids,
            subject=request.subject,
            description=request.description,
            scheduled_time=request.scheduled_time
        )
        
        return {"success": True, "meeting_id": meeting_id}
        
    except Exception as e:
        logger.error(f"Error scheduling meeting: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/meetings")
async def get_agent_meetings(agent_id: str):
    """Get meetings for an agent"""
    try:
        agent_meetings = []
        
        for meeting in inter_agent_comm.active_meetings.values():
            if agent_id == meeting["organizer"] or agent_id in meeting["attendees"]:
                agent_meetings.append(meeting)
        
        return agent_meetings
        
    except Exception as e:
        logger.error(f"Error getting agent meetings: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# System Endpoints
@router.get("/communication/stats")
async def get_communication_stats():
    """Get overall communication statistics"""
    try:
        stats = {
            "total_messages": len(inter_agent_comm.messages),
            "active_teams": len(inter_agent_comm.team_conversations),
            "pending_collaborations": len([
                req for req in inter_agent_comm.collaboration_requests.values()
                if len(req.responses) < len(req.to_agent_ids)
            ]),
            "active_meetings": len([
                meeting for meeting in inter_agent_comm.active_meetings.values()
                if meeting["status"] == "scheduled"
            ])
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting communication stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/teams", response_model=List[TeamConversation])
async def get_all_teams():
    """Get all team conversations"""
    try:
        return list(inter_agent_comm.team_conversations.values())
        
    except Exception as e:
        logger.error(f"Error getting all teams: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Initialize the communication service on startup
@router.on_event("startup")
async def startup_communication_service():
    """Initialize the inter-agent communication service"""
    await inter_agent_comm.initialize()