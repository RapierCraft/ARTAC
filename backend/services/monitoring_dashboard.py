"""
ARTAC Real-Time Monitoring Dashboard
Comprehensive monitoring and observability for multi-agent collaboration
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import weakref

from core.config import settings
from core.logging import get_logger
from services.interaction_logger import interaction_logger, InteractionType
from services.task_hierarchy_manager import task_hierarchy_manager, TaskStatus
from services.project_workspace_manager import project_workspace_manager
from services.file_lock_manager import get_lock_manager
from services.advanced_context_manager import advanced_context_manager

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Alert:
    """Alert definition"""
    id: str
    level: AlertLevel
    title: str
    message: str
    project_id: str
    agent_id: Optional[str]
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        return data


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.connection_metadata: Dict[websockets.WebSocketServerProtocol, Dict[str, Any]] = {}
    
    def add_connection(self, websocket: websockets.WebSocketServerProtocol, project_id: str, agent_id: str = None):
        """Add a WebSocket connection"""
        if project_id not in self.connections:
            self.connections[project_id] = set()
        
        self.connections[project_id].add(websocket)
        self.connection_metadata[websocket] = {
            "project_id": project_id,
            "agent_id": agent_id,
            "connected_at": datetime.now()
        }
    
    def remove_connection(self, websocket: websockets.WebSocketServerProtocol):
        """Remove a WebSocket connection"""
        if websocket in self.connection_metadata:
            project_id = self.connection_metadata[websocket]["project_id"]
            if project_id in self.connections:
                self.connections[project_id].discard(websocket)
                if not self.connections[project_id]:
                    del self.connections[project_id]
            del self.connection_metadata[websocket]
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a project"""
        if project_id not in self.connections:
            return
        
        disconnected = set()
        message_json = json.dumps(message)
        
        for websocket in self.connections[project_id]:
            try:
                await websocket.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.log_error(e, {"action": "websocket_broadcast"})
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.remove_connection(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        for project_id in list(self.connections.keys()):
            await self.broadcast_to_project(project_id, message)


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.alerts: Dict[str, Alert] = {}
        self.websocket_manager = websocket_manager
        self.alert_rules = self._initialize_alert_rules()
    
    def _initialize_alert_rules(self) -> List[Dict[str, Any]]:
        """Initialize default alert rules"""
        return [
            {
                "name": "high_error_rate",
                "condition": "error_count_1h > 10",
                "level": AlertLevel.ERROR,
                "message": "High error rate detected"
            },
            {
                "name": "agent_unresponsive",
                "condition": "agent_inactive > 30min",
                "level": AlertLevel.WARNING,
                "message": "Agent appears unresponsive"
            },
            {
                "name": "task_overdue",
                "condition": "task_past_due",
                "level": AlertLevel.WARNING,
                "message": "Task is overdue"
            },
            {
                "name": "file_lock_timeout",
                "condition": "lock_duration > 2h",
                "level": AlertLevel.WARNING,
                "message": "File lock held for too long"
            },
            {
                "name": "system_error",
                "condition": "system_error",
                "level": AlertLevel.CRITICAL,
                "message": "System error occurred"
            }
        ]
    
    async def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        project_id: str,
        agent_id: str = None,
        source: str = "system",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new alert"""
        try:
            alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts)}"
            
            alert = Alert(
                id=alert_id,
                level=level,
                title=title,
                message=message,
                project_id=project_id,
                agent_id=agent_id,
                source=source,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            self.alerts[alert_id] = alert
            
            # Broadcast alert to connected clients
            await self.websocket_manager.broadcast_to_project(project_id, {
                "type": "alert",
                "data": alert.to_dict()
            })
            
            # Log alert
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=agent_id or "system",
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="alert_created",
                content=f"{level.value.upper()}: {title}",
                context={
                    "alert_id": alert_id,
                    "level": level.value,
                    "source": source
                },
                metadata=metadata or {}
            )
            
            return alert_id
            
        except Exception as e:
            logger.log_error(e, {"action": "create_alert"})
            return ""
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Broadcast resolution
            await self.websocket_manager.broadcast_to_project(alert.project_id, {
                "type": "alert_resolved",
                "data": alert.to_dict()
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {"action": "resolve_alert"})
            return False
    
    def get_active_alerts(self, project_id: str = None, level: AlertLevel = None) -> List[Alert]:
        """Get active alerts"""
        active_alerts = [alert for alert in self.alerts.values() if not alert.resolved]
        
        if project_id:
            active_alerts = [alert for alert in active_alerts if alert.project_id == project_id]
        
        if level:
            active_alerts = [alert for alert in active_alerts if alert.level == level]
        
        return sorted(active_alerts, key=lambda a: a.timestamp, reverse=True)


class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.metrics: Dict[str, List[Metric]] = {}
        self.websocket_manager = websocket_manager
        self.metric_retention = timedelta(hours=24)  # Keep metrics for 24 hours
        
        # Start metric collection tasks
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._cleanup_old_metrics())
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Dict[str, str] = None
    ):
        """Record a metric"""
        try:
            metric = Metric(
                name=name,
                value=value,
                metric_type=metric_type,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append(metric)
            
            # Broadcast metric update
            project_id = tags.get("project_id") if tags else None
            if project_id:
                await self.websocket_manager.broadcast_to_project(project_id, {
                    "type": "metric",
                    "data": metric.to_dict()
                })
            
        except Exception as e:
            logger.log_error(e, {"action": "record_metric"})
    
    async def _collect_system_metrics(self):
        """Collect system-wide metrics periodically"""
        while True:
            try:
                # Collect project metrics
                projects = await project_workspace_manager.list_projects()
                
                await self.record_metric("artac.projects.total", len(projects))
                
                for project in projects:
                    project_id = project["project_id"]
                    tags = {"project_id": project_id}
                    
                    # Agent metrics
                    await self.record_metric(
                        "artac.agents.active",
                        project.get("agents_count", 0),
                        tags=tags
                    )
                    
                    # Task metrics
                    await self.record_metric(
                        "artac.tasks.active",
                        project.get("active_tasks", 0),
                        tags=tags
                    )
                    
                    await self.record_metric(
                        "artac.tasks.completed",
                        project.get("completed_tasks", 0),
                        tags=tags
                    )
                    
                    # Lock metrics
                    await self.record_metric(
                        "artac.locks.active",
                        project.get("active_locks", 0),
                        tags=tags
                    )
                
                # Interaction metrics
                recent_interactions = await interaction_logger.get_project_timeline(
                    project_id="",  # All projects
                    start_time=datetime.now() - timedelta(hours=1)
                )
                
                await self.record_metric(
                    "artac.interactions.hourly",
                    len(recent_interactions)
                )
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.log_error(e, {"action": "collect_system_metrics"})
                await asyncio.sleep(60)
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics periodically"""
        while True:
            try:
                cutoff_time = datetime.now() - self.metric_retention
                
                for metric_name in list(self.metrics.keys()):
                    self.metrics[metric_name] = [
                        metric for metric in self.metrics[metric_name]
                        if metric.timestamp > cutoff_time
                    ]
                    
                    if not self.metrics[metric_name]:
                        del self.metrics[metric_name]
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.log_error(e, {"action": "cleanup_old_metrics"})
                await asyncio.sleep(3600)
    
    def get_metrics(
        self,
        name: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        tags: Dict[str, str] = None
    ) -> List[Metric]:
        """Get metrics with optional filtering"""
        if name and name not in self.metrics:
            return []
        
        metrics_to_search = [self.metrics[name]] if name else self.metrics.values()
        
        filtered_metrics = []
        for metric_list in metrics_to_search:
            for metric in metric_list:
                # Time filtering
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                
                # Tag filtering
                if tags:
                    if not all(metric.tags.get(k) == v for k, v in tags.items()):
                        continue
                
                filtered_metrics.append(metric)
        
        return sorted(filtered_metrics, key=lambda m: m.timestamp)


class MonitoringDashboard:
    """Real-time monitoring dashboard for ARTAC"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.alert_manager = AlertManager(self.websocket_manager)
        self.metrics_collector = MetricsCollector(self.websocket_manager)
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_system_health())
        asyncio.create_task(self._monitor_agent_activity())
        asyncio.create_task(self._monitor_task_deadlines())
    
    async def get_dashboard_data(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a project"""
        try:
            # Get project status
            workspace = await project_workspace_manager.get_project(project_id)
            project_status = await workspace.get_workspace_status() if workspace else {}
            
            # Get active tasks
            project_tasks = await task_hierarchy_manager.get_project_tasks(project_id)
            
            # Get recent interactions
            recent_interactions = await interaction_logger.get_project_timeline(
                project_id=project_id,
                start_time=datetime.now() - timedelta(hours=24)
            )
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts(project_id)
            
            # Get file locks
            lock_manager = get_lock_manager(project_id)
            active_locks = await lock_manager.get_active_locks()
            
            # Get metrics
            recent_metrics = self.metrics_collector.get_metrics(
                start_time=datetime.now() - timedelta(hours=24),
                tags={"project_id": project_id}
            )
            
            # Calculate statistics
            task_stats = self._calculate_task_stats(project_tasks)
            interaction_stats = self._calculate_interaction_stats(recent_interactions)
            performance_stats = self._calculate_performance_stats(recent_metrics)
            
            return {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "project_status": project_status,
                "task_statistics": task_stats,
                "interaction_statistics": interaction_stats,
                "performance_statistics": performance_stats,
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "active_locks": [lock.to_dict() for lock in active_locks],
                "agent_activity": await self._get_agent_activity(project_id)
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_dashboard_data",
                "project_id": project_id
            })
            return {"error": str(e)}
    
    async def get_agent_dashboard(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Get agent-specific dashboard data"""
        try:
            # Get agent tasks
            agent_tasks = await task_hierarchy_manager.get_agent_tasks(agent_id, project_id)
            
            # Get agent interactions
            agent_interactions = await interaction_logger.get_agent_interactions(
                agent_id=agent_id,
                project_id=project_id,
                start_time=datetime.now() - timedelta(hours=24)
            )
            
            # Get agent locks
            lock_manager = get_lock_manager(project_id)
            agent_locks = await lock_manager.get_agent_locks(agent_id)
            
            # Get context summary
            context_summary = await advanced_context_manager.get_context_summary(project_id)
            
            return {
                "agent_id": agent_id,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "tasks": {
                    "total": len(agent_tasks),
                    "active": len([t for t in agent_tasks if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]]),
                    "completed": len([t for t in agent_tasks if t.status == TaskStatus.COMPLETED]),
                    "overdue": len([t for t in agent_tasks if t.due_date and t.due_date < datetime.now() and t.status != TaskStatus.COMPLETED])
                },
                "activity": {
                    "interactions_24h": len(agent_interactions),
                    "last_activity": max([i.timestamp for i in agent_interactions]).isoformat() if agent_interactions else None
                },
                "file_locks": len(agent_locks),
                "context_availability": context_summary.get("context_availability", {})
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_agent_dashboard",
                "project_id": project_id,
                "agent_id": agent_id
            })
            return {"error": str(e)}
    
    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while True:
            try:
                # Check for system errors
                recent_errors = await interaction_logger.get_project_timeline(
                    project_id="",  # All projects
                    start_time=datetime.now() - timedelta(hours=1),
                    interaction_types=[InteractionType.SYSTEM_EVENT]
                )
                
                error_count = len([i for i in recent_errors if "error" in i.action.lower()])
                
                if error_count > 10:
                    await self.alert_manager.create_alert(
                        level=AlertLevel.ERROR,
                        title="High System Error Rate",
                        message=f"Detected {error_count} system errors in the last hour",
                        project_id="system",
                        source="health_monitor"
                    )
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.log_error(e, {"action": "monitor_system_health"})
                await asyncio.sleep(300)
    
    async def _monitor_agent_activity(self):
        """Monitor agent activity and responsiveness"""
        while True:
            try:
                projects = await project_workspace_manager.list_projects()
                
                for project in projects:
                    project_id = project["project_id"]
                    
                    # Get recent agent interactions
                    recent_interactions = await interaction_logger.get_project_timeline(
                        project_id=project_id,
                        start_time=datetime.now() - timedelta(minutes=30)
                    )
                    
                    # Track agent activity
                    active_agents = set(i.agent_id for i in recent_interactions)
                    
                    # Check for inactive agents with assigned tasks
                    project_tasks = await task_hierarchy_manager.get_project_tasks(
                        project_id,
                        status_filter=[TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
                    )
                    
                    assigned_agents = set(t.assigned_to for t in project_tasks if t.assigned_to)
                    inactive_agents = assigned_agents - active_agents
                    
                    for agent_id in inactive_agents:
                        await self.alert_manager.create_alert(
                            level=AlertLevel.WARNING,
                            title="Agent Inactive",
                            message=f"Agent {agent_id} has been inactive for 30+ minutes with assigned tasks",
                            project_id=project_id,
                            agent_id=agent_id,
                            source="activity_monitor"
                        )
                
                # Sleep for 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.log_error(e, {"action": "monitor_agent_activity"})
                await asyncio.sleep(600)
    
    async def _monitor_task_deadlines(self):
        """Monitor task deadlines and overdue tasks"""
        while True:
            try:
                projects = await project_workspace_manager.list_projects()
                
                for project in projects:
                    project_id = project["project_id"]
                    
                    # Get all active tasks
                    active_tasks = await task_hierarchy_manager.get_project_tasks(
                        project_id,
                        status_filter=[TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
                    )
                    
                    now = datetime.now()
                    
                    for task in active_tasks:
                        if task.due_date and task.due_date < now:
                            await self.alert_manager.create_alert(
                                level=AlertLevel.WARNING,
                                title="Task Overdue",
                                message=f"Task '{task.title}' is overdue (due: {task.due_date.strftime('%Y-%m-%d')})",
                                project_id=project_id,
                                agent_id=task.assigned_to,
                                source="deadline_monitor",
                                metadata={"task_id": task.id}
                            )
                
                # Sleep for 30 minutes
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.log_error(e, {"action": "monitor_task_deadlines"})
                await asyncio.sleep(1800)
    
    def _calculate_task_stats(self, tasks: List) -> Dict[str, Any]:
        """Calculate task statistics"""
        if not tasks:
            return {"total": 0}
        
        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "completion_rate": 0,
            "overdue_count": 0
        }
        
        completed_count = 0
        now = datetime.now()
        
        for task in tasks:
            # Status stats
            status = task.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Priority stats
            priority = task.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Type stats
            task_type = task.task_type.value
            stats["by_type"][task_type] = stats["by_type"].get(task_type, 0) + 1
            
            # Completion tracking
            if task.status.value == "completed":
                completed_count += 1
            
            # Overdue tracking
            if task.due_date and task.due_date < now and task.status.value != "completed":
                stats["overdue_count"] += 1
        
        stats["completion_rate"] = (completed_count / len(tasks)) * 100 if tasks else 0
        
        return stats
    
    def _calculate_interaction_stats(self, interactions: List) -> Dict[str, Any]:
        """Calculate interaction statistics"""
        if not interactions:
            return {"total": 0}
        
        stats = {
            "total": len(interactions),
            "by_type": {},
            "by_agent": {},
            "by_hour": {}
        }
        
        for interaction in interactions:
            # Type stats
            interaction_type = interaction.interaction_type.value
            stats["by_type"][interaction_type] = stats["by_type"].get(interaction_type, 0) + 1
            
            # Agent stats
            agent_id = interaction.agent_id
            stats["by_agent"][agent_id] = stats["by_agent"].get(agent_id, 0) + 1
            
            # Hourly stats
            hour = interaction.timestamp.strftime("%H:00")
            stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1
        
        return stats
    
    def _calculate_performance_stats(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Calculate performance statistics from metrics"""
        if not metrics:
            return {}
        
        stats = {}
        
        # Group metrics by name
        grouped_metrics = {}
        for metric in metrics:
            if metric.name not in grouped_metrics:
                grouped_metrics[metric.name] = []
            grouped_metrics[metric.name].append(metric.value)
        
        # Calculate stats for each metric
        for metric_name, values in grouped_metrics.items():
            stats[metric_name] = {
                "current": values[-1] if values else 0,
                "average": sum(values) / len(values) if values else 0,
                "max": max(values) if values else 0,
                "min": min(values) if values else 0
            }
        
        return stats
    
    async def _get_agent_activity(self, project_id: str) -> Dict[str, Any]:
        """Get agent activity summary"""
        try:
            # Get recent interactions
            recent_interactions = await interaction_logger.get_project_timeline(
                project_id=project_id,
                start_time=datetime.now() - timedelta(hours=8)
            )
            
            agent_activity = {}
            
            for interaction in recent_interactions:
                agent_id = interaction.agent_id
                
                if agent_id not in agent_activity:
                    agent_activity[agent_id] = {
                        "interactions": 0,
                        "last_activity": None,
                        "types": {}
                    }
                
                agent_activity[agent_id]["interactions"] += 1
                
                if not agent_activity[agent_id]["last_activity"] or interaction.timestamp > agent_activity[agent_id]["last_activity"]:
                    agent_activity[agent_id]["last_activity"] = interaction.timestamp.isoformat()
                
                interaction_type = interaction.interaction_type.value
                agent_activity[agent_id]["types"][interaction_type] = agent_activity[agent_id]["types"].get(interaction_type, 0) + 1
            
            return agent_activity
            
        except Exception as e:
            logger.log_error(e, {"action": "get_agent_activity"})
            return {}


# Global instance
monitoring_dashboard = MonitoringDashboard()