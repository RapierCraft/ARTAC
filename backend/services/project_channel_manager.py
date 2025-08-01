"""
ARTAC Project Channel Manager
Automatically creates and manages project-specific communication channels
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from core.logging import get_logger
from services.inter_agent_communication import InterAgentCommunicationService

logger = get_logger(__name__)


class ChannelType(str, Enum):
    GENERAL = "general"
    GIT_COMMITS = "git-commits"
    DEPLOYMENTS = "deployments"
    CODE_REVIEW = "code-review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANNOUNCEMENTS = "announcements"
    AGENT_UPDATES = "agent-updates"
    USER_FEEDBACK = "user-feedback"
    SYSTEM_LOGS = "system-logs"


@dataclass
class ProjectChannel:
    """Represents a project-specific communication channel"""
    id: str
    project_id: str
    channel_type: ChannelType
    name: str
    description: str
    auto_notifications: bool
    participants: List[str]  # agent IDs and user IDs
    created_at: datetime
    created_by: str
    settings: Dict[str, Any]


@dataclass 
class ChannelMessage:
    """Enhanced message with project context and embeds"""
    id: str
    channel_id: str
    project_id: str
    sender_id: str
    sender_name: str
    sender_type: str  # "agent", "user", "system"
    content: str
    message_type: str  # "text", "embed", "notification"
    embeds: List[Dict[str, Any]]  # Rich embeds for git commits, deployments, etc.
    metadata: Dict[str, Any]
    timestamp: datetime
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None


class ProjectChannelManager:
    """Manages project-specific communication channels"""
    
    def __init__(self, inter_agent_comm: InterAgentCommunicationService):
        self.inter_agent_comm = inter_agent_comm
        self.project_channels: Dict[str, List[ProjectChannel]] = {}  # project_id -> channels
        self.channel_messages: Dict[str, List[ChannelMessage]] = {}  # channel_id -> messages
        self.channel_index: Dict[str, ProjectChannel] = {}  # channel_id -> channel
        
        # Default channel configurations
        self.default_channels = {
            ChannelType.GENERAL: {
                "name": "general",
                "description": "General project discussion",
                "auto_notifications": True,
                "settings": {"allow_user_posts": True, "allow_agent_posts": True}
            },
            ChannelType.GIT_COMMITS: {
                "name": "git-commits",
                "description": "Git commit notifications and discussions",
                "auto_notifications": True,
                "settings": {"embed_commits": True, "show_diffs": True}
            },
            ChannelType.DEPLOYMENTS: {
                "name": "deployments",
                "description": "Deployment status and notifications",
                "auto_notifications": True,
                "settings": {"embed_deployments": True, "show_logs": True}
            },
            ChannelType.CODE_REVIEW: {
                "name": "code-review",
                "description": "Code review requests and discussions",
                "auto_notifications": True,
                "settings": {"embed_code_snippets": True, "require_approval": True}
            },
            ChannelType.TESTING: {
                "name": "testing",
                "description": "Test results and quality assurance",
                "auto_notifications": True,
                "settings": {"embed_test_results": True, "show_coverage": True}
            },
            ChannelType.DOCUMENTATION: {
                "name": "documentation",
                "description": "Documentation updates and discussions",
                "auto_notifications": False,
                "settings": {"embed_docs": True, "version_tracking": True}
            },
            ChannelType.ANNOUNCEMENTS: {
                "name": "announcements",
                "description": "Project announcements and milestones",
                "auto_notifications": True,
                "settings": {"admin_only_posts": True, "priority_notifications": True}
            },
            ChannelType.AGENT_UPDATES: {
                "name": "agent-updates",
                "description": "Agent status and task updates",
                "auto_notifications": True,
                "settings": {"embed_task_progress": True, "agent_only_posts": True}
            },
            ChannelType.USER_FEEDBACK: {
                "name": "user-feedback",
                "description": "User feedback and feature requests",
                "auto_notifications": False,
                "settings": {"user_posts_only": True, "feedback_tracking": True}
            },
            ChannelType.SYSTEM_LOGS: {
                "name": "system-logs",
                "description": "System logs and monitoring",
                "auto_notifications": False,
                "settings": {"system_only_posts": True, "log_retention": "7d"}
            }
        }
    
    async def create_project_channels(
        self,
        project_id: str,
        project_name: str,
        created_by: str,
        initial_participants: List[str] = None
    ) -> List[str]:
        """Create all default channels for a new project"""
        try:
            created_channels = []
            participants = initial_participants or []
            
            for channel_type, config in self.default_channels.items():
                channel_id = await self.create_channel(
                    project_id=project_id,
                    channel_type=channel_type,
                    name=f"{project_name}-{config['name']}",
                    description=config['description'],
                    created_by=created_by,
                    participants=participants,
                    auto_notifications=config['auto_notifications'],
                    settings=config['settings']
                )
                
                if channel_id:
                    created_channels.append(channel_id)
            
            logger.log_system_event("project_channels_created", {
                "project_id": project_id,
                "project_name": project_name,
                "channels_created": len(created_channels),
                "channel_ids": created_channels
            })
            
            return created_channels
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_project_channels",
                "project_id": project_id
            })
            return []
    
    async def create_channel(
        self,
        project_id: str,
        channel_type: ChannelType,
        name: str,
        description: str,
        created_by: str,
        participants: List[str] = None,
        auto_notifications: bool = True,
        settings: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create a single project channel"""
        try:
            channel_id = f"ch_{project_id}_{channel_type.value}_{uuid.uuid4().hex[:8]}"
            
            channel = ProjectChannel(
                id=channel_id,
                project_id=project_id,
                channel_type=channel_type,
                name=name,
                description=description,
                auto_notifications=auto_notifications,
                participants=participants or [],
                created_at=datetime.utcnow(),
                created_by=created_by,
                settings=settings or {}
            )
            
            # Store channel
            if project_id not in self.project_channels:
                self.project_channels[project_id] = []
            self.project_channels[project_id].append(channel)
            self.channel_index[channel_id] = channel
            self.channel_messages[channel_id] = []
            
            # Create channel in inter-agent communication system
            await self.inter_agent_comm.create_channel(
                channel_id=channel_id,
                name=name,
                description=description,
                channel_type="project",
                metadata={
                    "project_id": project_id,
                    "channel_type": channel_type.value,
                    "auto_notifications": auto_notifications
                }
            )
            
            logger.log_system_event("project_channel_created", {
                "channel_id": channel_id,
                "project_id": project_id,
                "channel_type": channel_type.value,
                "name": name
            })
            
            return channel_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_channel",
                "project_id": project_id,
                "channel_type": channel_type.value
            })
            return None
    
    async def send_channel_message(
        self,
        channel_id: str,
        sender_id: str,
        sender_name: str,
        sender_type: str,
        content: str,
        message_type: str = "text",
        embeds: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """Send a message to a project channel"""
        try:
            if channel_id not in self.channel_index:
                logger.log_error(f"Channel {channel_id} not found", {})
                return None
            
            channel = self.channel_index[channel_id]
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            
            message = ChannelMessage(
                id=message_id,
                channel_id=channel_id,
                project_id=channel.project_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type=sender_type,
                content=content,
                message_type=message_type,
                embeds=embeds or [],
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            # Store message
            self.channel_messages[channel_id].append(message)
            
            # Send through inter-agent communication
            await self.inter_agent_comm.send_message(
                from_agent_id=sender_id,
                channel_id=channel_id,
                content=content,
                message_type="project_update",
                metadata={
                    **metadata,
                    "embeds": embeds,
                    "sender_type": sender_type,
                    "project_id": channel.project_id
                }
            )
            
            # Handle notifications if enabled
            if channel.auto_notifications:
                await self._send_notifications(channel, message)
            
            logger.log_system_event("channel_message_sent", {
                "message_id": message_id,
                "channel_id": channel_id,
                "project_id": channel.project_id,
                "sender_type": sender_type,
                "message_type": message_type
            })
            
            return message_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "send_channel_message",
                "channel_id": channel_id,
                "sender_id": sender_id
            })
            return None
    
    async def _send_notifications(self, channel: ProjectChannel, message: ChannelMessage):
        """Send notifications to channel participants"""
        for participant_id in channel.participants:
            if participant_id != message.sender_id:
                await self.inter_agent_comm.send_notification(
                    to_agent_id=participant_id,
                    title=f"New message in #{channel.name}",
                    content=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                    metadata={
                        "channel_id": channel.id,
                        "project_id": channel.project_id,
                        "message_id": message.id,
                        "sender_name": message.sender_name
                    }
                )
    
    async def get_project_channels(self, project_id: str) -> List[ProjectChannel]:
        """Get all channels for a project"""
        return self.project_channels.get(project_id, [])
    
    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChannelMessage]:
        """Get messages from a channel"""
        messages = self.channel_messages.get(channel_id, [])
        return messages[offset:offset + limit]
    
    async def add_participant_to_channel(self, channel_id: str, participant_id: str) -> bool:
        """Add a participant to a channel"""
        try:
            if channel_id in self.channel_index:
                channel = self.channel_index[channel_id]
                if participant_id not in channel.participants:
                    channel.participants.append(participant_id)
                    
                    logger.log_system_event("participant_added_to_channel", {
                        "channel_id": channel_id,
                        "participant_id": participant_id,
                        "project_id": channel.project_id
                    })
                    
                    return True
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "add_participant_to_channel",
                "channel_id": channel_id,
                "participant_id": participant_id
            })
            return False
    
    async def remove_participant_from_channel(self, channel_id: str, participant_id: str) -> bool:
        """Remove a participant from a channel"""
        try:
            if channel_id in self.channel_index:
                channel = self.channel_index[channel_id]
                if participant_id in channel.participants:
                    channel.participants.remove(participant_id)
                    
                    logger.log_system_event("participant_removed_from_channel", {
                        "channel_id": channel_id,
                        "participant_id": participant_id,
                        "project_id": channel.project_id
                    })
                    
                    return True
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "remove_participant_from_channel",
                "channel_id": channel_id,
                "participant_id": participant_id
            })
            return False
    
    async def get_channel_by_type(self, project_id: str, channel_type: ChannelType) -> Optional[ProjectChannel]:
        """Get a specific channel type for a project"""
        project_channels = self.project_channels.get(project_id, [])
        for channel in project_channels:
            if channel.channel_type == channel_type:
                return channel
        return None
    
    async def update_channel_settings(
        self,
        channel_id: str,
        settings: Dict[str, Any]
    ) -> bool:
        """Update channel settings"""
        try:
            if channel_id in self.channel_index:
                channel = self.channel_index[channel_id]
                channel.settings.update(settings)
                
                logger.log_system_event("channel_settings_updated", {
                    "channel_id": channel_id,
                    "project_id": channel.project_id,
                    "updated_settings": list(settings.keys())
                })
                
                return True
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "update_channel_settings",
                "channel_id": channel_id
            })
            return False
    
    async def archive_channel(self, channel_id: str) -> bool:
        """Archive a channel (make it read-only)"""
        try:
            if channel_id in self.channel_index:
                channel = self.channel_index[channel_id]
                channel.settings["archived"] = True
                channel.settings["read_only"] = True
                
                logger.log_system_event("channel_archived", {
                    "channel_id": channel_id,
                    "project_id": channel.project_id
                })
                
                return True
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "archive_channel",
                "channel_id": channel_id
            })
            return False


# Global instance will be created when inter_agent_communication is available