"""
ARTAC Real-time Notifications System
WebSocket-based real-time notifications for code changes, deployments, and project updates
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol

from core.logging import get_logger
from services.embed_system import embed_system, RichEmbed
from services.code_artifact_manager import CodeArtifact
from services.project_channel_manager import ProjectChannelManager

logger = get_logger(__name__)


class NotificationType(str, Enum):
    CODE_CHANGE = "code_change"
    GIT_COMMIT = "git_commit"
    DEPLOYMENT = "deployment"
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    PROJECT_UPDATE = "project_update"
    CHANNEL_MESSAGE = "channel_message"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_ALERT = "performance_alert"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Real-time notification structure"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    project_id: Optional[str]
    agent_id: Optional[str]
    channel_id: Optional[str]
    embed: Optional[Dict[str, Any]]  # Serialized embed
    actions: List[Dict[str, str]]  # Available actions
    metadata: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    read: bool = False


@dataclass
class SubscriptionFilter:
    """Subscription filter for selective notifications"""
    user_id: str
    notification_types: Set[NotificationType]
    project_ids: Set[str]
    agent_ids: Set[str]
    channel_ids: Set[str]
    priority_threshold: NotificationPriority


class NotificationSubscription:
    """Manages a single WebSocket subscription"""
    
    def __init__(self, websocket: WebSocketServerProtocol, user_id: str, filters: SubscriptionFilter):
        self.websocket = websocket
        self.user_id = user_id
        self.filters = filters
        self.subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.notification_count = 0
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send notification to this subscription"""
        try:
            if not self._should_receive_notification(notification):
                return True  # Not an error, just filtered out
            
            message = {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "notification_type": notification.type.value,
                    "priority": notification.priority.value,
                    "title": notification.title,
                    "message": notification.message,
                    "project_id": notification.project_id,
                    "agent_id": notification.agent_id,
                    "channel_id": notification.channel_id,
                    "embed": notification.embed,
                    "actions": notification.actions,
                    "metadata": notification.metadata,
                    "timestamp": notification.timestamp.isoformat(),
                    "expires_at": notification.expires_at.isoformat() if notification.expires_at else None
                }
            }
            
            await self.websocket.send(json.dumps(message))
            self.notification_count += 1
            return True
            
        except websockets.exceptions.ConnectionClosed:
            return False
        except Exception as e:
            logger.log_error(e, {
                "action": "send_notification",
                "subscription_id": self.subscription_id,
                "user_id": self.user_id
            })
            return False
    
    def _should_receive_notification(self, notification: Notification) -> bool:
        """Check if this subscription should receive the notification"""
        # Check notification type filter
        if notification.type not in self.filters.notification_types:
            return False
        
        # Check priority threshold
        priority_order = {
            NotificationPriority.LOW: 0,
            NotificationPriority.MEDIUM: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.URGENT: 3
        }
        
        if priority_order[notification.priority] < priority_order[self.filters.priority_threshold]:
            return False
        
        # Check project filter
        if self.filters.project_ids and notification.project_id:
            if notification.project_id not in self.filters.project_ids:
                return False
        
        # Check agent filter
        if self.filters.agent_ids and notification.agent_id:
            if notification.agent_id not in self.filters.agent_ids:
                return False
        
        # Check channel filter
        if self.filters.channel_ids and notification.channel_id:
            if notification.channel_id not in self.filters.channel_ids:
                return False
        
        return True
    
    async def ping(self) -> bool:
        """Send ping to check connection"""
        try:
            await self.websocket.send(json.dumps({"type": "ping", "timestamp": datetime.utcnow().isoformat()}))
            self.last_ping = datetime.utcnow()
            return True
        except:
            return False


class RealTimeNotificationService:
    """Real-time notification service with WebSocket support"""
    
    def __init__(self):
        self.subscriptions: Dict[str, NotificationSubscription] = {}
        self.user_subscriptions: Dict[str, List[str]] = {}  # user_id -> subscription_ids
        self.notification_history: Dict[str, Notification] = {}
        self.notification_handlers: Dict[NotificationType, List[Callable]] = {}
        self.server: Optional[websockets.server.WebSocketServer] = None
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default notification handlers"""
        self.notification_handlers = {
            NotificationType.CODE_CHANGE: [],
            NotificationType.GIT_COMMIT: [],
            NotificationType.DEPLOYMENT: [],
            NotificationType.TASK_UPDATE: [],
            NotificationType.AGENT_STATUS: [],
            NotificationType.PROJECT_UPDATE: [],
            NotificationType.CHANNEL_MESSAGE: [],
            NotificationType.SYSTEM_ALERT: [],
            NotificationType.PERFORMANCE_ALERT: []
        }
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_websocket_connection,
                host,
                port,
                ping_interval=30,
                ping_timeout=10
            )
            
            logger.log_system_event("notification_server_started", {
                "host": host,
                "port": port
            })
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            
        except Exception as e:
            logger.log_error(e, {
                "action": "start_notification_server",
                "host": host,
                "port": port
            })
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.log_system_event("notification_server_stopped", {})
    
    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        subscription_id = None
        user_id = None
        
        try:
            # Wait for authentication message
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)
            
            if auth_data.get("type") != "auth":
                await websocket.close(code=4001, reason="Authentication required")
                return
            
            user_id = auth_data.get("user_id")
            if not user_id:
                await websocket.close(code=4001, reason="User ID required")
                return
            
            # Create subscription filter
            filter_data = auth_data.get("filters", {})
            filters = SubscriptionFilter(
                user_id=user_id,
                notification_types=set(filter_data.get("types", [t.value for t in NotificationType])),
                project_ids=set(filter_data.get("project_ids", [])),
                agent_ids=set(filter_data.get("agent_ids", [])),
                channel_ids=set(filter_data.get("channel_ids", [])),
                priority_threshold=NotificationPriority(filter_data.get("priority_threshold", "low"))
            )
            
            # Create subscription
            subscription = NotificationSubscription(websocket, user_id, filters)
            subscription_id = subscription.subscription_id
            
            # Store subscription
            self.subscriptions[subscription_id] = subscription
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = []
            self.user_subscriptions[user_id].append(subscription_id)
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "connected",
                "subscription_id": subscription_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            logger.log_system_event("notification_subscription_created", {
                "subscription_id": subscription_id,
                "user_id": user_id,
                "filters": asdict(filters)
            })
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(subscription, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                except Exception as e:
                    logger.log_error(e, {
                        "action": "handle_client_message",
                        "subscription_id": subscription_id
                    })
        
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.log_error(e, {
                "action": "handle_websocket_connection",
                "user_id": user_id
            })
        finally:
            # Cleanup subscription
            if subscription_id and subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                if user_id and user_id in self.user_subscriptions:
                    if subscription_id in self.user_subscriptions[user_id]:
                        self.user_subscriptions[user_id].remove(subscription_id)
                    if not self.user_subscriptions[user_id]:
                        del self.user_subscriptions[user_id]
                
                logger.log_system_event("notification_subscription_closed", {
                    "subscription_id": subscription_id,
                    "user_id": user_id
                })
    
    async def _handle_client_message(self, subscription: NotificationSubscription, data: Dict[str, Any]):
        """Handle message from client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await subscription.websocket.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        elif message_type == "mark_read":
            notification_id = data.get("notification_id")
            if notification_id and notification_id in self.notification_history:
                self.notification_history[notification_id].read = True
        
        elif message_type == "update_filters":
            # Update subscription filters
            filter_data = data.get("filters", {})
            subscription.filters.notification_types = set(filter_data.get("types", []))
            subscription.filters.project_ids = set(filter_data.get("project_ids", []))
            subscription.filters.agent_ids = set(filter_data.get("agent_ids", []))
            subscription.filters.channel_ids = set(filter_data.get("channel_ids", []))
            subscription.filters.priority_threshold = NotificationPriority(
                filter_data.get("priority_threshold", "low")
            )
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        embed: Optional[RichEmbed] = None,
        actions: List[Dict[str, str]] = None,
        metadata: Dict[str, Any] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Send notification to all relevant subscriptions"""
        try:
            notification_id = f"notif_{uuid.uuid4().hex[:8]}"
            
            notification = Notification(
                id=notification_id,
                type=notification_type,
                priority=priority,
                title=title,
                message=message,
                project_id=project_id,
                agent_id=agent_id,
                channel_id=channel_id,
                embed=embed_system.to_dict(embed) if embed else None,
                actions=actions or [],
                metadata=metadata or {},
                timestamp=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # Store notification
            self.notification_history[notification_id] = notification
            
            # Send to all relevant subscriptions
            disconnected_subscriptions = []
            for subscription_id, subscription in self.subscriptions.items():
                success = await subscription.send_notification(notification)
                if not success:
                    disconnected_subscriptions.append(subscription_id)
            
            # Cleanup disconnected subscriptions
            for sub_id in disconnected_subscriptions:
                if sub_id in self.subscriptions:
                    del self.subscriptions[sub_id]
            
            # Call registered handlers
            handlers = self.notification_handlers.get(notification_type, [])
            for handler in handlers:
                try:
                    await handler(notification)
                except Exception as e:
                    logger.log_error(e, {
                        "action": "notification_handler",
                        "handler": str(handler),
                        "notification_id": notification_id
                    })
            
            logger.log_system_event("notification_sent", {
                "notification_id": notification_id,
                "type": notification_type.value,
                "priority": priority.value,
                "subscriptions_notified": len(self.subscriptions) - len(disconnected_subscriptions)
            })
            
            return notification_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "send_notification",
                "type": notification_type.value
            })
            raise
    
    async def notify_code_change(self, artifact: CodeArtifact, changes_summary: str = ""):
        """Send notification for code changes"""
        embed = await embed_system.create_code_artifact_embed(artifact, changes_summary)
        
        actions = [
            {"type": "view_code", "label": "View Code", "url": f"/codebase/{artifact.project_id}/file/{artifact.id}"},
            {"type": "review", "label": "Review", "url": f"/review/{artifact.id}"}
        ]
        
        await self.send_notification(
            notification_type=NotificationType.CODE_CHANGE,
            title=f"Code Updated: {artifact.file_name}",
            message=f"{artifact.agent_name} updated {artifact.file_name}" + (f" - {changes_summary}" if changes_summary else ""),
            priority=NotificationPriority.MEDIUM if artifact.status.value == "review_pending" else NotificationPriority.LOW,
            project_id=artifact.project_id,
            agent_id=artifact.agent_id,
            embed=embed,
            actions=actions,
            metadata={
                "artifact_id": artifact.id,
                "file_path": artifact.file_path,
                "version": artifact.version
            }
        )
    
    async def notify_deployment(
        self,
        project_id: str,
        environment: str,
        status: str,
        deployed_by: str,
        deployment_url: Optional[str] = None
    ):
        """Send notification for deployments"""
        priority_map = {
            "success": NotificationPriority.MEDIUM,
            "failure": NotificationPriority.HIGH,
            "in_progress": NotificationPriority.LOW
        }
        
        emoji_map = {
            "success": "🚀",
            "failure": "❌",
            "in_progress": "⏳"
        }
        
        actions = []
        if deployment_url:
            actions.append({"type": "view_deployment", "label": "View Deployment", "url": deployment_url})
        actions.append({"type": "view_logs", "label": "View Logs", "url": f"/deployments/{project_id}/logs"})
        
        await self.send_notification(
            notification_type=NotificationType.DEPLOYMENT,
            title=f"{emoji_map.get(status, '📦')} Deployment {status.title()}",
            message=f"Deployment to {environment} {status} by {deployed_by}",
            priority=priority_map.get(status, NotificationPriority.MEDIUM),
            project_id=project_id,
            actions=actions,
            metadata={
                "environment": environment,
                "status": status,
                "deployed_by": deployed_by,
                "deployment_url": deployment_url
            }
        )
    
    async def notify_task_update(
        self,
        task_id: str,
        project_id: str,
        agent_id: str,
        agent_name: str,
        task_title: str,
        old_status: str,
        new_status: str
    ):
        """Send notification for task updates"""
        status_emoji = {
            "assigned": "📋",
            "in_progress": "⏳",
            "review_pending": "👀",
            "completed": "✅",
            "cancelled": "❌"
        }
        
        priority = NotificationPriority.HIGH if new_status == "completed" else NotificationPriority.MEDIUM
        
        await self.send_notification(
            notification_type=NotificationType.TASK_UPDATE,
            title=f"{status_emoji.get(new_status, '📋')} Task {new_status.replace('_', ' ').title()}",
            message=f"{agent_name}: {task_title}",
            priority=priority,
            project_id=project_id,
            agent_id=agent_id,
            metadata={
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status
            }
        )
    
    def register_handler(self, notification_type: NotificationType, handler: Callable):
        """Register a handler for specific notification types"""
        if notification_type not in self.notification_handlers:
            self.notification_handlers[notification_type] = []
        self.notification_handlers[notification_type].append(handler)
    
    async def _cleanup_task(self):
        """Periodic cleanup of expired notifications and dead connections"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                current_time = datetime.utcnow()
                
                # Remove expired notifications
                expired_notifications = [
                    notif_id for notif_id, notif in self.notification_history.items()
                    if notif.expires_at and notif.expires_at < current_time
                ]
                
                for notif_id in expired_notifications:
                    del self.notification_history[notif_id]
                
                # Ping connections and remove dead ones
                dead_subscriptions = []
                for sub_id, subscription in self.subscriptions.items():
                    if not await subscription.ping():
                        dead_subscriptions.append(sub_id)
                
                for sub_id in dead_subscriptions:
                    del self.subscriptions[sub_id]
                
                if expired_notifications or dead_subscriptions:
                    logger.log_system_event("notification_cleanup", {
                        "expired_notifications": len(expired_notifications),
                        "dead_subscriptions": len(dead_subscriptions)
                    })
                
            except Exception as e:
                logger.log_error(e, {"action": "notification_cleanup"})


# Global instance
real_time_notifications = RealTimeNotificationService()