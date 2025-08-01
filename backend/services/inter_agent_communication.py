"""
Inter-Agent Communication Service
Enables agents to communicate with each other directly, form teams, and collaborate
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pydantic import BaseModel

from models.agent import Agent, AgentRole, AgentStatus
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class MessageType(str, Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    TEAM_CHAT = "team_chat"
    TASK_UPDATE = "task_update"
    MEETING_INVITE = "meeting_invite"
    COLLABORATION_REQUEST = "collaboration_request"
    STATUS_UPDATE = "status_update"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentMessage(BaseModel):
    id: str
    from_agent_id: str
    to_agent_id: Optional[str] = None  # None for broadcast messages
    team_id: Optional[str] = None
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    subject: str
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    read: bool = False
    replied: bool = False
    archived: bool = False


class TeamConversation(BaseModel):
    id: str
    name: str
    description: str
    team_members: List[str]  # agent IDs
    created_by: str
    created_at: datetime = datetime.now()
    last_activity: datetime = datetime.now()
    active: bool = True


class CollaborationRequest(BaseModel):
    id: str
    from_agent_id: str
    to_agent_ids: List[str]
    task_id: str
    description: str
    required_skills: List[str] = []
    urgency: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = datetime.now()
    responses: Dict[str, str] = {}  # agent_id -> response (accept/decline/counter)


class InterAgentCommunicationService:
    """Service for handling all inter-agent communication"""
    
    def __init__(self):
        self.messages: Dict[str, AgentMessage] = {}
        self.team_conversations: Dict[str, TeamConversation] = {}
        self.collaboration_requests: Dict[str, CollaborationRequest] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = {}  # agent_id -> set of topic subscriptions
        self.active_meetings: Dict[str, Dict[str, Any]] = {}
        self.message_listeners: Dict[str, List[callable]] = {}  # agent_id -> list of callback functions
        
    async def initialize(self):
        """Initialize the communication service"""
        logger.log_system_event("inter_agent_communication_initializing", {})
        
        # Create default team channels
        await self._create_default_teams()
        
        logger.log_system_event("inter_agent_communication_initialized", {
            "default_teams_created": len(self.team_conversations)
        })
    
    async def _create_default_teams(self):
        """Create default team conversation channels"""
        default_teams = [
            {
                "id": "general",
                "name": "General",
                "description": "Company-wide announcements and discussions",
                "members": []  # Will be populated as agents join
            },
            {
                "id": "ceo", 
                "name": "CEO Channel",
                "description": "Direct communication with the CEO",
                "members": []
            },
            {
                "id": "development",
                "name": "Development Team",
                "description": "Development and engineering discussions",
                "members": []
            },
            {
                "id": "leadership",
                "name": "Leadership Team", 
                "description": "Executive and management discussions",
                "members": []
            }
        ]
        
        for team_info in default_teams:
            team_id = team_info["id"]
            team = TeamConversation(
                id=team_id,
                name=team_info["name"],
                description=team_info["description"],
                team_members=team_info["members"],
                created_by="system"
            )
            self.team_conversations[team_id] = team
    
    async def send_direct_message(self, from_agent_id: str = None, to_agent_id: str = None, 
                                content: str = None,
                                subject: str = "Direct Message", 
                                priority = MessagePriority.NORMAL,
                                metadata: Dict[str, Any] = None,
                                # Alternative parameter names for compatibility
                                from_agent: str = None, to_agent: str = None) -> str:
        """Send a direct message between two agents"""
        # Handle both parameter styles for compatibility
        sender_id = from_agent_id or from_agent
        recipient_id = to_agent_id or to_agent
        
        if not sender_id or not recipient_id or not content:
            raise ValueError("from_agent_id/from_agent, to_agent_id/to_agent, and content are required")
        
        # Handle priority parameter that might be string or enum
        if isinstance(priority, str):
            priority_map = {
                "low": MessagePriority.LOW,
                "normal": MessagePriority.NORMAL, 
                "high": MessagePriority.HIGH,
                "urgent": MessagePriority.URGENT
            }
            priority = priority_map.get(priority.lower(), MessagePriority.NORMAL)
        
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            from_agent_id=sender_id,
            to_agent_id=recipient_id,
            message_type=MessageType.DIRECT,
            priority=priority,
            subject=subject,
            content=content,
            metadata=metadata or {}
        )
        
        self.messages[message_id] = message
        
        # Trigger message received event for recipient
        await self._notify_agent_message_received(recipient_id, message)
        
        logger.log_system_event("direct_message_sent", {
            "message_id": message_id,
            "from_agent": sender_id,
            "to_agent": recipient_id,
            "priority": priority.value
        })
        
        return message_id
    
    async def send_team_message(self, from_agent_id: str, team_id: str,
                              subject: str, content: str,
                              priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a message to a team conversation"""
        if team_id not in self.team_conversations:
            raise ValueError(f"Team {team_id} not found")
        
        team = self.team_conversations[team_id]
        # Auto-add sender to team if not already a member (for system agents like CEO)
        if from_agent_id not in team.team_members:
            team.team_members.append(from_agent_id)
        
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            from_agent_id=from_agent_id,
            team_id=team_id,
            message_type=MessageType.TEAM_CHAT,
            priority=priority,
            subject=subject,
            content=content
        )
        
        self.messages[message_id] = message
        team.last_activity = datetime.now()
        
        # Notify all team members except sender
        for member_id in team.team_members:
            if member_id != from_agent_id:
                await self._notify_agent_message_received(member_id, message)
        
        logger.log_system_event("team_message_sent", {
            "message_id": message_id,
            "from_agent": from_agent_id,
            "team_id": team_id,
            "team_size": len(team.team_members)
        })
        
        return message_id
    
    async def broadcast_message(self, from_agent_id: str, subject: str, content: str,
                              target_roles: List[AgentRole] = None,
                              priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Broadcast a message to all agents or specific roles"""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            from_agent_id=from_agent_id,
            message_type=MessageType.BROADCAST,
            priority=priority,
            subject=subject,
            content=content,
            metadata={"target_roles": [role.value for role in target_roles] if target_roles else []}
        )
        
        self.messages[message_id] = message
        
        # Get all agents that should receive this broadcast
        # This would integrate with the talent pool service
        recipient_count = await self._broadcast_to_agents(message, target_roles)
        
        logger.log_system_event("broadcast_message_sent", {
            "message_id": message_id,
            "from_agent": from_agent_id,
            "recipients": recipient_count,
            "target_roles": [role.value for role in target_roles] if target_roles else "all"
        })
        
        return message_id
    
    async def request_collaboration(self, from_agent_id: str, to_agent_ids: List[str],
                                  task_id: str, description: str,
                                  required_skills: List[str] = None,
                                  urgency: MessagePriority = MessagePriority.NORMAL) -> str:
        """Request collaboration from other agents"""
        request_id = str(uuid.uuid4())
        
        collab_request = CollaborationRequest(
            id=request_id,
            from_agent_id=from_agent_id,
            to_agent_ids=to_agent_ids,
            task_id=task_id,
            description=description,
            required_skills=required_skills or [],
            urgency=urgency
        )
        
        self.collaboration_requests[request_id] = collab_request
        
        # Send collaboration request messages to each target agent
        for to_agent_id in to_agent_ids:
            message_id = await self.send_direct_message(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                subject=f"Collaboration Request: {description}",
                content=f"I need help with task {task_id}. Required skills: {', '.join(required_skills)}. Please respond with accept/decline.",
                priority=urgency,
                metadata={"collaboration_request_id": request_id, "task_id": task_id}
            )
        
        logger.log_system_event("collaboration_requested", {
            "request_id": request_id,
            "from_agent": from_agent_id,
            "to_agents": to_agent_ids,
            "task_id": task_id
        })
        
        return request_id
    
    async def respond_to_collaboration(self, agent_id: str, request_id: str, 
                                     response: str, message: str = "") -> bool:
        """Respond to a collaboration request"""
        if request_id not in self.collaboration_requests:
            raise ValueError(f"Collaboration request {request_id} not found")
        
        collab_request = self.collaboration_requests[request_id]
        if agent_id not in collab_request.to_agent_ids:
            raise ValueError(f"Agent {agent_id} was not invited to this collaboration")
        
        collab_request.responses[agent_id] = response
        
        # Send response back to requesting agent
        response_content = f"Response to collaboration request: {response}"
        if message:
            response_content += f"\nMessage: {message}"
        
        await self.send_direct_message(
            from_agent_id=agent_id,
            to_agent_id=collab_request.from_agent_id,
            subject=f"Re: Collaboration Request - {response.upper()}",
            content=response_content,
            metadata={"collaboration_request_id": request_id, "response": response}
        )
        
        logger.log_system_event("collaboration_response", {
            "request_id": request_id,
            "responding_agent": agent_id,
            "response": response
        })
        
        return True
    
    async def create_team_conversation(self, creator_id: str, name: str, 
                                     description: str, member_ids: List[str]) -> str:
        """Create a new team conversation channel"""
        team_id = str(uuid.uuid4())
        
        # Add creator to members if not already included
        if creator_id not in member_ids:
            member_ids.append(creator_id)
        
        team = TeamConversation(
            id=team_id,
            name=name,
            description=description,
            team_members=member_ids,
            created_by=creator_id
        )
        
        self.team_conversations[team_id] = team
        
        # Notify all members they've been added to the team
        for member_id in member_ids:
            if member_id != creator_id:
                await self.send_direct_message(
                    from_agent_id="system",
                    to_agent_id=member_id,
                    subject=f"Added to team: {name}",
                    content=f"You've been added to the '{name}' team by {creator_id}. {description}",
                    metadata={"team_id": team_id}
                )
        
        logger.log_system_event("team_created", {
            "team_id": team_id,
            "name": name,
            "creator": creator_id,
            "members": len(member_ids)
        })
        
        return team_id
    
    async def schedule_meeting(self, organizer_id: str, attendee_ids: List[str],
                             subject: str, description: str, 
                             scheduled_time: datetime) -> str:
        """Schedule a meeting between agents"""
        meeting_id = str(uuid.uuid4())
        
        meeting_info = {
            "id": meeting_id,
            "organizer": organizer_id,
            "attendees": attendee_ids,
            "subject": subject,
            "description": description,
            "scheduled_time": scheduled_time,
            "status": "scheduled",
            "responses": {}  # agent_id -> accept/decline
        }
        
        self.active_meetings[meeting_id] = meeting_info
        
        # Send meeting invites to all attendees
        for attendee_id in attendee_ids:
            await self.send_direct_message(
                from_agent_id=organizer_id,
                to_agent_id=attendee_id,
                subject=f"Meeting Invitation: {subject}",
                content=f"You're invited to a meeting:\n\nSubject: {subject}\nTime: {scheduled_time}\nDescription: {description}\n\nPlease respond with accept/decline.",
                priority=MessagePriority.HIGH,
                metadata={"meeting_id": meeting_id, "meeting_invite": True}
            )
        
        logger.log_system_event("meeting_scheduled", {
            "meeting_id": meeting_id,
            "organizer": organizer_id,
            "attendees": len(attendee_ids),
            "scheduled_time": scheduled_time.isoformat()
        })
        
        return meeting_id
    
    async def get_agent_messages(self, agent_id: str, unread_only: bool = False,
                               limit: int = 50) -> List[AgentMessage]:
        """Get messages for a specific agent"""
        agent_messages = []
        
        for message in self.messages.values():
            # Check if message is for this agent
            if (message.to_agent_id == agent_id or 
                (message.team_id and self._is_agent_in_team(agent_id, message.team_id)) or
                message.message_type == MessageType.BROADCAST):
                
                if unread_only and message.read:
                    continue
                    
                agent_messages.append(message)
        
        # Sort by timestamp (newest first) and limit
        agent_messages.sort(key=lambda m: m.timestamp, reverse=True)
        return agent_messages[:limit]
    
    async def mark_message_read(self, agent_id: str, message_id: str) -> bool:
        """Mark a message as read by an agent"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Verify agent has permission to read this message
        if (message.to_agent_id == agent_id or 
            (message.team_id and self._is_agent_in_team(agent_id, message.team_id)) or
            message.message_type == MessageType.BROADCAST):
            
            message.read = True
            return True
        
        return False
    
    async def get_team_conversations(self, agent_id: str) -> List[TeamConversation]:
        """Get all team conversations an agent is part of"""
        agent_teams = []
        
        for team in self.team_conversations.values():
            if agent_id in team.team_members:
                agent_teams.append(team)
        
        return agent_teams
    
    async def add_agent_to_team(self, team_id: str, agent_id: str, added_by: str) -> bool:
        """Add an agent to a team conversation"""
        if team_id not in self.team_conversations:
            return False
        
        team = self.team_conversations[team_id]
        
        if agent_id not in team.team_members:
            team.team_members.append(agent_id)
            
            # Notify the agent they've been added
            await self.send_direct_message(
                from_agent_id=added_by,
                to_agent_id=agent_id,
                subject=f"Added to team: {team.name}",
                content=f"You've been added to the '{team.name}' team. {team.description}",
                metadata={"team_id": team_id}
            )
            
            logger.log_system_event("agent_added_to_team", {
                "team_id": team_id,
                "agent_id": agent_id,
                "added_by": added_by
            })
            
            return True
        
        return False
    
    async def _notify_agent_message_received(self, agent_id: str, message: AgentMessage):
        """Notify an agent that they received a message"""
        # This would integrate with the agent's active Claude CLI session
        # For now, we'll just log it
        logger.log_system_event("agent_message_received", {
            "agent_id": agent_id,
            "message_id": message.id,
            "from_agent": message.from_agent_id,
            "message_type": message.message_type.value,
            "priority": message.priority.value
        })
        
        # In a full implementation, this would trigger the agent's Claude CLI
        # to process the message and potentially respond
    
    async def _broadcast_to_agents(self, message: AgentMessage, target_roles: List[AgentRole] = None) -> int:
        """Broadcast message to agents (placeholder - would integrate with talent pool)"""
        # This would integrate with the talent pool service to get actual agents
        # For now, just return a simulated count
        return 5 if target_roles else 10
    
    def _is_agent_in_team(self, agent_id: str, team_id: str) -> bool:
        """Check if an agent is in a specific team"""
        if team_id not in self.team_conversations:
            return False
        
        return agent_id in self.team_conversations[team_id].team_members

    # Additional methods for communication API compatibility
    async def create_channel(self, channel_id: str, name: str, description: str, channel_type: str = "public") -> str:
        """Create a new communication channel"""
        # Create team conversation with the specified channel_id
        from datetime import datetime
        team = TeamConversation(
            id=channel_id,
            name=name,
            description=description,
            team_members=[],
            created_by="system",
            created_at=datetime.now(),
            last_activity=datetime.now(),
            active=True
        )
        
        self.team_conversations[channel_id] = team
        
        logger.log_system_event("channel_created", {
            "channel_id": channel_id,
            "name": name,
            "type": channel_type
        })
        
        return channel_id

    async def get_all_channels(self) -> List[Dict[str, Any]]:
        """Get all available channels"""
        channels = []
        for team_id, team in self.team_conversations.items():
            channels.append({
                "id": team_id,
                "name": team.name,
                "description": team.description,
                "type": "public",
                "created_at": team.created_at,
                "last_activity": team.last_activity
            })
        return channels

    async def get_channel_messages(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get messages for a specific channel"""
        messages = []
        for message_id, message in self.messages.items():
            if (message.message_type == MessageType.TEAM_CHAT and 
                hasattr(message, 'team_id') and message.team_id == channel_id):
                messages.append({
                    "id": message.id,
                    "channel_id": channel_id,
                    "sender_id": message.from_agent_id,
                    "sender_name": f"Agent {message.from_agent_id}",
                    "content": message.content,
                    "timestamp": message.timestamp,
                    "mentions": getattr(message, 'mentions', [])
                })
        return sorted(messages, key=lambda x: x['timestamp'])

    async def send_message(self, channel_id: str, sender_id: str, sender_name: str, 
                          content: str, mentions: List[str] = None, reply_to: str = None,
                          message_type: str = "team_chat") -> str:
        """Send a message to a channel"""
        # Use team message for channel communication
        message_id = await self.send_team_message(
            from_agent_id=sender_id,
            team_id=channel_id,
            subject="Message",
            content=content,
            priority=MessagePriority.NORMAL
        )
        return message_id

    async def get_unread_count(self, channel_id: str) -> int:
        """Get unread message count for a channel"""
        # Simplified - return 0 for now
        return 0

    # Compatibility method for different method signatures
    async def send_direct_message_alt(self, from_agent: str, to_agent: str, content: str, priority: str = "high") -> str:
        """Alternative signature for send_direct_message"""
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL, 
            "high": MessagePriority.HIGH,
            "urgent": MessagePriority.URGENT
        }
        
        return await self.send_direct_message(
            from_agent_id=from_agent,
            to_agent_id=to_agent,
            content=content,
            priority=priority_map.get(priority, MessagePriority.NORMAL)
        )


# Global service instance
inter_agent_comm = InterAgentCommunicationService()