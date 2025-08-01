"""
Communication API endpoints
Real-time communication system with agents and project management
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from services.inter_agent_communication import inter_agent_comm
from services.agent_manager import get_agent_manager
from services.ceo_service import get_ceo_service
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models for request/response
class SendMessageRequest(BaseModel):
    channel_id: str
    content: str
    mentions: Optional[List[str]] = []
    reply_to: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    channel_id: str
    user_id: str
    user_name: str
    content: str
    timestamp: datetime
    mentions: List[str]
    is_ceo_response: bool = False

class ChannelResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    unread_count: int = 0

@router.get("/channels", response_model=List[ChannelResponse])
async def get_channels():
    """Get all available channels from real system"""
    try:
        # Get real channels from inter-agent communication system
        channels = await inter_agent_comm.get_all_channels()
        
        # Convert to response format
        channel_responses = []
        for channel in channels:
            unread_count = await inter_agent_comm.get_unread_count(channel['id'])
            channel_responses.append(ChannelResponse(
                id=channel['id'],
                name=channel['name'],
                description=channel['description'],
                type=channel['type'],
                unread_count=unread_count
            ))
        
        return channel_responses
    except Exception as e:
        logger.log_error(e, {"action": "get_channels"})
        raise HTTPException(status_code=500, detail="Failed to fetch channels")

@router.get("/channels/{channel_id}/messages", response_model=List[MessageResponse])
async def get_channel_messages(channel_id: str):
    """Get messages for a specific channel from real system"""
    try:
        # Get real messages from inter-agent communication system
        messages = await inter_agent_comm.get_channel_messages(channel_id)
        
        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append(MessageResponse(
                id=msg['id'],
                channel_id=msg['channel_id'],
                user_id=msg['sender_id'],
                user_name=msg['sender_name'],
                content=msg['content'],
                timestamp=msg['timestamp'],
                mentions=msg.get('mentions', []),
                is_ceo_response=msg['sender_id'] == 'ceo-001'
            ))
        
        return message_responses
    except Exception as e:
        logger.log_error(e, {"action": "get_channel_messages", "channel_id": channel_id})
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.post("/channels/{channel_id}/messages", response_model=MessageResponse)
async def send_message(channel_id: str, request: SendMessageRequest):
    """Send a message to a channel using real system"""
    try:
        # Send message through inter-agent communication system
        message_id = await inter_agent_comm.send_message(
            channel_id=channel_id,
            sender_id="user-001",  # User sending message
            sender_name="User",
            content=request.content,
            mentions=request.mentions,
            reply_to=request.reply_to
        )
        
        # Create response
        message_response = MessageResponse(
            id=message_id,
            channel_id=channel_id,
            user_id="user-001",
            user_name="User",
            content=request.content,
            timestamp=datetime.now(),
            mentions=request.mentions,
            is_ceo_response=False
        ) 
        
        logger.log_system_event("message_sent", {
            "channel_id": channel_id,
            "message_id": message_id,
            "content_preview": request.content[:50],
            "mentions": request.mentions
        })
        
        # Check if CEO should respond
        ceo_mentioned = (
            channel_id == "ceo" or 
            "ceo" in [m.lower() for m in request.mentions] or
            "@ceo" in request.content.lower()
        )
        
        if ceo_mentioned:
            # Use the CEO chat endpoint we created
            import httpx
            async with httpx.AsyncClient() as client:
                ceo_response = await client.post(
                    "http://localhost:8000/api/v1/ceo/chat",
                    json={"message": request.content, "user_id": "user-001"}
                )
                if ceo_response.status_code == 200:
                    ceo_data = ceo_response.json()
                    # CEO has already sent messages through the project creation process
                    logger.log_system_event("ceo_response_triggered", {
                        "channel_id": channel_id,
                        "project_created": ceo_data.get("project_channel") is not None
                    })
        
        return message_response
    except Exception as e:
        logger.log_error(e, {"action": "send_message", "channel_id": channel_id})
        raise HTTPException(status_code=500, detail="Failed to send message")

# Additional endpoints for system status
@router.get("/agents")
async def get_active_agents():
    """Get all active agents"""
    try:
        agent_manager = get_agent_manager()
        if agent_manager:
            agents = await agent_manager.get_all_agents()
            return [agent.to_dict() for agent in agents]
        return []
    except Exception as e:
        logger.log_error(e, {"action": "get_active_agents"})
        return []

@router.post("/channels")
async def create_channel(name: str, description: str, channel_type: str = "public"):
    """Create a new channel"""
    try:
        channel_id = await inter_agent_comm.create_channel(
            channel_id=f"channel-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            channel_type=channel_type
        )
        return {"channel_id": channel_id, "name": name, "description": description, "type": channel_type}
    except Exception as e:
        logger.log_error(e, {"action": "create_channel"})
        raise HTTPException(status_code=500, detail="Failed to create channel")