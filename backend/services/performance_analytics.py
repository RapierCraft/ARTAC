"""
ARTAC Performance Analytics System
Advanced analytics for agent performance, team productivity, and system optimization
"""

import asyncio
import json
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import sqlite3
import aiosqlite

from core.config import settings
from core.logging import get_logger
from services.interaction_logger import interaction_logger, InteractionType
from services.task_hierarchy_manager import task_hierarchy_manager, TaskStatus, TaskType
from services.project_workspace_manager import project_workspace_manager
from services.rag_context_manager import rag_context_manager

logger = get_logger(__name__)


class AnalyticsPeriod(Enum):
    """Time periods for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class PerformanceMetric(Enum):
    """Types of performance metrics"""
    TASK_COMPLETION_RATE = "task_completion_rate"
    TASK_VELOCITY = "task_velocity"
    CODE_QUALITY = "code_quality"
    COLLABORATION_SCORE = "collaboration_score"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    PRODUCTIVITY_INDEX = "productivity_index"
    LEARNING_RATE = "learning_rate"


@dataclass
class PerformanceReport:
    """Performance report data structure"""
    agent_id: str
    project_id: str
    period: AnalyticsPeriod
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, float]
    recommendations: List[str]
    trends: Dict[str, str]  # improving, declining, stable
    raw_data: Dict[str, Any]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['period'] = self.period.value
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        data['generated_at'] = self.generated_at.isoformat()
        return data


class AgentAnalyzer:
    """Analyzes individual agent performance"""
    
    def __init__(self):
        self.db_path = os.path.join(settings.DATA_ROOT, "analytics", "performance.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self):
        """Initialize analytics database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Performance metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        period_type TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance reports table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS performance_reports (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        report_data TEXT NOT NULL,
                        period_type TEXT NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Agent rankings table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_rankings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        ranking_type TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        rank_position INTEGER NOT NULL,
                        score REAL NOT NULL,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                await db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_agent ON performance_metrics(agent_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_project ON performance_metrics(project_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_agent ON performance_reports(agent_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_rankings_project ON agent_rankings(project_id)")
                
                await db.commit()
                
        except Exception as e:
            logger.log_error(e, {"action": "initialize_performance_database"})
    
    async def analyze_agent_performance(
        self,
        agent_id: str,
        project_id: str,
        period: AnalyticsPeriod,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> PerformanceReport:
        """Analyze comprehensive agent performance"""
        try:
            # Calculate date range
            if not end_date:
                end_date = datetime.now()
            
            if not start_date:
                period_deltas = {
                    AnalyticsPeriod.HOUR: timedelta(hours=1),
                    AnalyticsPeriod.DAY: timedelta(days=1),
                    AnalyticsPeriod.WEEK: timedelta(weeks=1),
                    AnalyticsPeriod.MONTH: timedelta(days=30),
                    AnalyticsPeriod.QUARTER: timedelta(days=90)
                }
                start_date = end_date - period_deltas[period]
            
            # Calculate various performance metrics
            metrics = {}
            raw_data = {}
            
            # Task completion metrics
            task_metrics = await self._calculate_task_metrics(agent_id, project_id, start_date, end_date)
            metrics.update(task_metrics["metrics"])
            raw_data["tasks"] = task_metrics["raw_data"]
            
            # Code quality metrics
            code_metrics = await self._calculate_code_metrics(agent_id, project_id, start_date, end_date)
            metrics.update(code_metrics["metrics"])
            raw_data["code"] = code_metrics["raw_data"]
            
            # Collaboration metrics
            collab_metrics = await self._calculate_collaboration_metrics(agent_id, project_id, start_date, end_date)
            metrics.update(collab_metrics["metrics"])
            raw_data["collaboration"] = collab_metrics["raw_data"]
            
            # Error and quality metrics
            error_metrics = await self._calculate_error_metrics(agent_id, project_id, start_date, end_date)
            metrics.update(error_metrics["metrics"])
            raw_data["errors"] = error_metrics["raw_data"]
            
            # Calculate overall productivity index
            metrics["productivity_index"] = self._calculate_productivity_index(metrics)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(agent_id, metrics, raw_data)
            
            # Calculate trends
            trends = await self._calculate_trends(agent_id, project_id, metrics, period)
            
            # Create performance report
            report = PerformanceReport(
                agent_id=agent_id,
                project_id=project_id,
                period=period,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                recommendations=recommendations,
                trends=trends,
                raw_data=raw_data,
                generated_at=datetime.now()
            )
            
            # Store metrics in database
            await self._store_performance_metrics(report)
            
            # Log performance analysis
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="performance_analyzed",
                content=f"Performance analysis completed for {period.value}",
                context={
                    "period": period.value,
                    "productivity_index": metrics.get("productivity_index", 0),
                    "metrics_count": len(metrics)
                }
            )
            
            return report
            
        except Exception as e:
            logger.log_error(e, {
                "action": "analyze_agent_performance",
                "agent_id": agent_id,
                "project_id": project_id
            })
            return None
    
    async def _calculate_task_metrics(self, agent_id: str, project_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate task-related performance metrics"""
        try:
            # Get agent tasks in the period
            agent_tasks = await task_hierarchy_manager.get_agent_tasks(agent_id, project_id)
            
            # Filter tasks by date
            period_tasks = [
                task for task in agent_tasks
                if start_date <= task.created_at <= end_date or
                   (task.completed_at and start_date <= task.completed_at <= end_date)
            ]
            
            if not period_tasks:
                return {
                    "metrics": {
                        "task_completion_rate": 0,
                        "task_velocity": 0,
                        "average_task_time": 0,
                        "on_time_delivery_rate": 0
                    },
                    "raw_data": {"total_tasks": 0, "completed_tasks": 0}
                }
            
            # Calculate metrics
            completed_tasks = [task for task in period_tasks if task.status == TaskStatus.COMPLETED]
            overdue_tasks = [
                task for task in period_tasks
                if task.due_date and task.due_date < datetime.now() and task.status != TaskStatus.COMPLETED
            ]
            
            # Task completion rate
            completion_rate = len(completed_tasks) / len(period_tasks) * 100 if period_tasks else 0
            
            # Task velocity (tasks completed per day)
            period_days = (end_date - start_date).days or 1
            velocity = len(completed_tasks) / period_days
            
            # Average task completion time
            task_times = []
            for task in completed_tasks:
                if task.completed_at and task.created_at:
                    time_taken = (task.completed_at - task.created_at).total_seconds() / 3600  # hours
                    task_times.append(time_taken)
            
            avg_task_time = statistics.mean(task_times) if task_times else 0
            
            # On-time delivery rate
            on_time_tasks = [
                task for task in completed_tasks
                if not task.due_date or (task.completed_at and task.completed_at <= task.due_date)
            ]
            on_time_rate = len(on_time_tasks) / len(completed_tasks) * 100 if completed_tasks else 100
            
            # Task complexity handling
            complexity_scores = {
                TaskType.EPIC: 10,
                TaskType.STORY: 7,
                TaskType.TASK: 5,
                TaskType.SUBTASK: 3,
                TaskType.BUG: 4,
                TaskType.RESEARCH: 6
            }
            
            avg_complexity = statistics.mean([
                complexity_scores.get(task.task_type, 5) for task in completed_tasks
            ]) if completed_tasks else 0
            
            return {
                "metrics": {
                    "task_completion_rate": completion_rate,
                    "task_velocity": velocity,
                    "average_task_time": avg_task_time,
                    "on_time_delivery_rate": on_time_rate,
                    "average_task_complexity": avg_complexity
                },
                "raw_data": {
                    "total_tasks": len(period_tasks),
                    "completed_tasks": len(completed_tasks),
                    "overdue_tasks": len(overdue_tasks),
                    "task_types": {task_type.value: len([t for t in period_tasks if t.task_type == task_type]) 
                                 for task_type in TaskType}
                }
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_task_metrics"})
            return {"metrics": {}, "raw_data": {}}
    
    async def _calculate_code_metrics(self, agent_id: str, project_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate code quality and productivity metrics"""
        try:
            # Get code-related interactions
            code_interactions = await interaction_logger.get_agent_interactions(
                agent_id=agent_id,
                project_id=project_id,
                interaction_type=InteractionType.CODE_EDIT,
                start_time=start_date,
                end_time=end_date
            )
            
            if not code_interactions:
                return {
                    "metrics": {
                        "code_commits": 0,
                        "files_modified": 0,
                        "lines_changed": 0,
                        "code_quality_score": 0
                    },
                    "raw_data": {"interactions": 0}
                }
            
            # Calculate code metrics
            files_modified = set()
            total_lines_changed = 0
            
            for interaction in code_interactions:
                file_path = interaction.context.get('file_path')
                if file_path:
                    files_modified.add(file_path)
                
                # Estimate lines changed from content length
                content_length = len(interaction.content)
                estimated_lines = max(1, content_length // 50)  # Rough estimate
                total_lines_changed += estimated_lines
            
            # Code quality score (based on various factors)
            quality_factors = []
            
            # Frequency of commits (not too many, not too few)
            commits_per_day = len(code_interactions) / ((end_date - start_date).days or 1)
            if 1 <= commits_per_day <= 5:
                quality_factors.append(1.0)
            elif commits_per_day < 1:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.8)
            
            # File organization (variety of files)
            file_variety = len(files_modified)
            if file_variety > 0:
                quality_factors.append(min(1.0, file_variety / 10))
            
            code_quality_score = statistics.mean(quality_factors) * 100 if quality_factors else 0
            
            return {
                "metrics": {
                    "code_commits": len(code_interactions),
                    "files_modified": len(files_modified),
                    "lines_changed_estimate": total_lines_changed,
                    "commits_per_day": commits_per_day,
                    "code_quality_score": code_quality_score
                },
                "raw_data": {
                    "interactions": len(code_interactions),
                    "modified_files": list(files_modified)
                }
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_code_metrics"})
            return {"metrics": {}, "raw_data": {}}
    
    async def _calculate_collaboration_metrics(self, agent_id: str, project_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate collaboration and communication metrics"""
        try:
            # Get communication interactions
            comm_interactions = await interaction_logger.get_agent_interactions(
                agent_id=agent_id,
                project_id=project_id,
                interaction_type=InteractionType.COMMUNICATION,
                start_time=start_date,
                end_time=end_date
            )
            
            # Get collaboration interactions
            collab_interactions = await interaction_logger.get_agent_interactions(
                agent_id=agent_id,
                project_id=project_id,
                interaction_type=InteractionType.COLLABORATION,
                start_time=start_date,
                end_time=end_date
            )
            
            all_interactions = comm_interactions + collab_interactions
            
            if not all_interactions:
                return {
                    "metrics": {
                        "collaboration_score": 0,
                        "communication_frequency": 0,
                        "team_interactions": 0,
                        "response_time_avg": 0
                    },
                    "raw_data": {"interactions": 0}
                }
            
            # Calculate collaboration metrics
            unique_collaborators = set()
            response_times = []
            
            for interaction in all_interactions:
                # Track collaborators
                if interaction.context.get('to_agent'):
                    unique_collaborators.add(interaction.context['to_agent'])
                if interaction.context.get('from_agent'):
                    unique_collaborators.add(interaction.context['from_agent'])
                
                # Estimate response time (simplified)
                if 'response_time' in interaction.metadata:
                    response_times.append(interaction.metadata['response_time'])
            
            # Collaboration score based on various factors
            collab_factors = []
            
            # Communication frequency
            period_days = (end_date - start_date).days or 1
            comm_per_day = len(all_interactions) / period_days
            collab_factors.append(min(1.0, comm_per_day / 5))  # Normalize to max 5 per day
            
            # Team interaction diversity
            if unique_collaborators:
                collab_factors.append(min(1.0, len(unique_collaborators) / 5))  # Up to 5 collaborators
            else:
                collab_factors.append(0.0)
            
            collaboration_score = statistics.mean(collab_factors) * 100 if collab_factors else 0
            
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            return {
                "metrics": {
                    "collaboration_score": collaboration_score,
                    "communication_frequency": comm_per_day,
                    "team_interactions": len(all_interactions),
                    "unique_collaborators": len(unique_collaborators),
                    "response_time_avg": avg_response_time
                },
                "raw_data": {
                    "interactions": len(all_interactions),
                    "collaborators": list(unique_collaborators)
                }
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_collaboration_metrics"})
            return {"metrics": {}, "raw_data": {}}
    
    async def _calculate_error_metrics(self, agent_id: str, project_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate error and debugging metrics"""
        try:
            # Get debugging interactions
            debug_interactions = await interaction_logger.get_agent_interactions(
                agent_id=agent_id,
                project_id=project_id,
                interaction_type=InteractionType.DEBUGGING,
                start_time=start_date,
                end_time=end_date
            )
            
            if not debug_interactions:
                return {
                    "metrics": {
                        "error_rate": 0,
                        "resolution_time_avg": 0,
                        "debugging_efficiency": 100
                    },
                    "raw_data": {"errors": 0}
                }
            
            # Calculate error metrics
            resolution_times = []
            error_types = {}
            
            for interaction in debug_interactions:
                # Track error types
                error_type = interaction.metadata.get('error_type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Track resolution time
                if 'resolution_time' in interaction.metadata:
                    resolution_times.append(interaction.metadata['resolution_time'])
            
            # Error rate (errors per day)
            period_days = (end_date - start_date).days or 1
            error_rate = len(debug_interactions) / period_days
            
            # Average resolution time
            avg_resolution_time = statistics.mean(resolution_times) if resolution_times else 0
            
            # Debugging efficiency (inverse of error rate, normalized)
            debugging_efficiency = max(0, 100 - (error_rate * 10))  # Scale down error rate
            
            return {
                "metrics": {
                    "error_rate": error_rate,
                    "resolution_time_avg": avg_resolution_time,
                    "debugging_efficiency": debugging_efficiency,
                    "total_errors": len(debug_interactions)
                },
                "raw_data": {
                    "errors": len(debug_interactions),
                    "error_types": error_types
                }
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_error_metrics"})
            return {"metrics": {}, "raw_data": {}}
    
    def _calculate_productivity_index(self, metrics: Dict[str, float]) -> float:
        """Calculate overall productivity index from various metrics"""
        try:
            # Weight factors for different metrics
            weights = {
                "task_completion_rate": 0.25,
                "task_velocity": 0.20,
                "on_time_delivery_rate": 0.20,
                "code_quality_score": 0.15,
                "collaboration_score": 0.10,
                "debugging_efficiency": 0.10
            }
            
            weighted_score = 0
            total_weight = 0
            
            for metric, weight in weights.items():
                if metric in metrics:
                    # Normalize metrics to 0-100 scale
                    normalized_value = min(100, max(0, metrics[metric]))
                    weighted_score += normalized_value * weight
                    total_weight += weight
            
            if total_weight > 0:
                return weighted_score / total_weight
            else:
                return 0
                
        except Exception as e:
            logger.log_error(e, {"action": "calculate_productivity_index"})
            return 0
    
    async def _generate_recommendations(self, agent_id: str, metrics: Dict[str, float], raw_data: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        try:
            # Task completion recommendations
            if metrics.get("task_completion_rate", 0) < 70:
                recommendations.append("Focus on completing assigned tasks. Consider breaking down complex tasks into smaller, manageable pieces.")
            
            # Time management recommendations
            if metrics.get("on_time_delivery_rate", 100) < 80:
                recommendations.append("Improve time estimation and planning. Consider using time-blocking techniques for better deadline management.")
            
            # Code quality recommendations
            if metrics.get("code_quality_score", 0) < 70:
                recommendations.append("Focus on code quality. Consider implementing code reviews and following coding standards more consistently.")
            
            # Collaboration recommendations
            if metrics.get("collaboration_score", 0) < 60:
                recommendations.append("Increase team collaboration. Participate more in team discussions and code reviews.")
            
            # Velocity recommendations
            if metrics.get("task_velocity", 0) < 0.5:  # Less than 0.5 tasks per day
                recommendations.append("Consider optimizing your workflow and eliminating distractions to improve task completion velocity.")
            
            # Error rate recommendations
            if metrics.get("error_rate", 0) > 2:  # More than 2 errors per day
                recommendations.append("Focus on reducing errors through better testing and code review practices.")
            
            # General productivity recommendations
            productivity_index = metrics.get("productivity_index", 0)
            if productivity_index < 60:
                recommendations.append("Overall productivity could be improved. Consider identifying bottlenecks in your workflow and addressing them.")
            elif productivity_index > 90:
                recommendations.append("Excellent performance! Consider mentoring other team members and sharing your best practices.")
            
            # Specific recommendations based on raw data
            if raw_data.get("tasks", {}).get("overdue_tasks", 0) > 0:
                recommendations.append(f"You have {raw_data['tasks']['overdue_tasks']} overdue tasks. Prioritize completing them first.")
            
            if not recommendations:
                recommendations.append("Great work! Keep maintaining your current performance level.")
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.log_error(e, {"action": "generate_recommendations"})
            return ["Continue focusing on your assigned tasks and maintain good collaboration with the team."]
    
    async def _calculate_trends(self, agent_id: str, project_id: str, current_metrics: Dict[str, float], period: AnalyticsPeriod) -> Dict[str, str]:
        """Calculate performance trends compared to previous period"""
        try:
            trends = {}
            
            # Get previous period metrics from database
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT metric_type, metric_value FROM performance_metrics
                    WHERE agent_id = ? AND project_id = ? AND period_type = ?
                    ORDER BY created_at DESC LIMIT 20
                """, (agent_id, project_id, period.value))
                
                previous_metrics = {}
                async for row in cursor:
                    metric_type, metric_value = row
                    if metric_type not in previous_metrics:
                        previous_metrics[metric_type] = metric_value
            
            # Compare current metrics with previous
            for metric_name, current_value in current_metrics.items():
                if metric_name in previous_metrics:
                    previous_value = previous_metrics[metric_name]
                    
                    if current_value > previous_value * 1.05:  # 5% improvement threshold
                        trends[metric_name] = "improving"
                    elif current_value < previous_value * 0.95:  # 5% decline threshold
                        trends[metric_name] = "declining"
                    else:
                        trends[metric_name] = "stable"
                else:
                    trends[metric_name] = "new"
            
            return trends
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_trends"})
            return {}
    
    async def _store_performance_metrics(self, report: PerformanceReport):
        """Store performance metrics and report in database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Store individual metrics
                for metric_name, metric_value in report.metrics.items():
                    await db.execute("""
                        INSERT INTO performance_metrics 
                        (agent_id, project_id, metric_type, metric_value, period_start, period_end, period_type, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        report.agent_id,
                        report.project_id,
                        metric_name,
                        metric_value,
                        report.start_date.isoformat(),
                        report.end_date.isoformat(),
                        report.period.value,
                        json.dumps(report.raw_data)
                    ))
                
                # Store complete report
                report_id = f"report_{report.agent_id}_{report.project_id}_{int(report.generated_at.timestamp())}"
                await db.execute("""
                    INSERT INTO performance_reports 
                    (id, agent_id, project_id, report_data, period_type, period_start, period_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id,
                    report.agent_id,
                    report.project_id,
                    json.dumps(report.to_dict()),
                    report.period.value,
                    report.start_date.isoformat(),
                    report.end_date.isoformat()
                ))
                
                await db.commit()
                
        except Exception as e:
            logger.log_error(e, {"action": "store_performance_metrics"})


class TeamAnalyzer:
    """Analyzes team-wide performance and dynamics"""
    
    def __init__(self, agent_analyzer: AgentAnalyzer):
        self.agent_analyzer = agent_analyzer
    
    async def analyze_team_performance(self, project_id: str, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Analyze overall team performance"""
        try:
            # Get all project agents
            workspace = await project_workspace_manager.get_project(project_id)
            if not workspace:
                return {"error": "Project not found"}
            
            # Get all agents with tasks in the project
            project_tasks = await task_hierarchy_manager.get_project_tasks(project_id)
            agent_ids = set(task.assigned_to for task in project_tasks if task.assigned_to)
            
            if not agent_ids:
                return {"error": "No agents found for project"}
            
            # Generate individual performance reports
            agent_reports = {}
            for agent_id in agent_ids:
                report = await self.agent_analyzer.analyze_agent_performance(
                    agent_id, project_id, period
                )
                if report:
                    agent_reports[agent_id] = report
            
            # Calculate team metrics
            team_metrics = self._calculate_team_metrics(agent_reports)
            
            # Generate team insights
            insights = self._generate_team_insights(agent_reports, team_metrics)
            
            # Calculate collaboration matrix
            collaboration_matrix = await self._calculate_collaboration_matrix(project_id, period)
            
            return {
                "project_id": project_id,
                "period": period.value,
                "team_metrics": team_metrics,
                "agent_reports": {aid: report.to_dict() for aid, report in agent_reports.items()},
                "insights": insights,
                "collaboration_matrix": collaboration_matrix,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "analyze_team_performance",
                "project_id": project_id
            })
            return {"error": str(e)}
    
    def _calculate_team_metrics(self, agent_reports: Dict[str, PerformanceReport]) -> Dict[str, Any]:
        """Calculate team-wide performance metrics"""
        if not agent_reports:
            return {}
        
        team_metrics = {}
        
        # Aggregate metrics across all agents
        all_metrics = {}
        for report in agent_reports.values():
            for metric_name, value in report.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)
        
        # Calculate team statistics
        for metric_name, values in all_metrics.items():
            team_metrics[metric_name] = {
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Team-specific metrics
        team_metrics["team_size"] = len(agent_reports)
        team_metrics["performance_variance"] = statistics.stdev([
            report.metrics.get("productivity_index", 0) for report in agent_reports.values()
        ]) if len(agent_reports) > 1 else 0
        
        return team_metrics
    
    def _generate_team_insights(self, agent_reports: Dict[str, PerformanceReport], team_metrics: Dict[str, Any]) -> List[str]:
        """Generate team performance insights"""
        insights = []
        
        try:
            # Performance distribution insights
            productivity_scores = [report.metrics.get("productivity_index", 0) for report in agent_reports.values()]
            avg_productivity = statistics.mean(productivity_scores) if productivity_scores else 0
            
            if avg_productivity > 80:
                insights.append("Team is performing excellently with high overall productivity.")
            elif avg_productivity > 60:
                insights.append("Team performance is good but has room for improvement.")
            else:
                insights.append("Team performance needs attention. Consider additional support and training.")
            
            # Performance variance insights
            performance_variance = team_metrics.get("performance_variance", 0)
            if performance_variance > 20:
                insights.append("High performance variance detected. Consider balancing workloads and providing support to lower-performing team members.")
            elif performance_variance < 10:
                insights.append("Team performance is well-balanced across members.")
            
            # Collaboration insights
            collab_scores = [report.metrics.get("collaboration_score", 0) for report in agent_reports.values()]
            avg_collaboration = statistics.mean(collab_scores) if collab_scores else 0
            
            if avg_collaboration < 50:
                insights.append("Team collaboration could be improved. Consider implementing more team activities and communication channels.")
            
            # Task completion insights
            completion_rates = [report.metrics.get("task_completion_rate", 0) for report in agent_reports.values()]
            avg_completion = statistics.mean(completion_rates) if completion_rates else 0
            
            if avg_completion < 70:
                insights.append("Task completion rates are below optimal. Review task assignment and support processes.")
            
            # Top performers identification
            if len(agent_reports) > 1:
                top_performer = max(agent_reports.items(), key=lambda x: x[1].metrics.get("productivity_index", 0))
                insights.append(f"Top performer: {top_performer[0]} with productivity index of {top_performer[1].metrics.get('productivity_index', 0):.1f}")
            
            return insights[:5]  # Limit to top 5 insights
            
        except Exception as e:
            logger.log_error(e, {"action": "generate_team_insights"})
            return ["Team analysis completed. Review individual agent reports for detailed insights."]
    
    async def _calculate_collaboration_matrix(self, project_id: str, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Calculate collaboration matrix between team members"""
        try:
            # Get collaboration interactions
            end_date = datetime.now()
            period_deltas = {
                AnalyticsPeriod.HOUR: timedelta(hours=1),
                AnalyticsPeriod.DAY: timedelta(days=1),
                AnalyticsPeriod.WEEK: timedelta(weeks=1),
                AnalyticsPeriod.MONTH: timedelta(days=30),
                AnalyticsPeriod.QUARTER: timedelta(days=90)
            }
            start_date = end_date - period_deltas[period]
            
            interactions = await interaction_logger.get_project_timeline(
                project_id=project_id,
                start_time=start_date,
                end_time=end_date,
                interaction_types=[InteractionType.COMMUNICATION, InteractionType.COLLABORATION]
            )
            
            # Build collaboration matrix
            collaboration_matrix = {}
            
            for interaction in interactions:
                from_agent = interaction.agent_id
                to_agent = interaction.context.get('to_agent')
                
                if to_agent:
                    if from_agent not in collaboration_matrix:
                        collaboration_matrix[from_agent] = {}
                    
                    if to_agent not in collaboration_matrix[from_agent]:
                        collaboration_matrix[from_agent][to_agent] = 0
                    
                    collaboration_matrix[from_agent][to_agent] += 1
            
            return collaboration_matrix
            
        except Exception as e:
            logger.log_error(e, {"action": "calculate_collaboration_matrix"})
            return {}


class PerformanceAnalytics:
    """Main performance analytics system"""
    
    def __init__(self):
        self.agent_analyzer = AgentAnalyzer()
        self.team_analyzer = TeamAnalyzer(self.agent_analyzer)
        
        # Start periodic analysis tasks
        asyncio.create_task(self._periodic_analysis())
    
    async def generate_performance_report(
        self,
        project_id: str,
        agent_id: str = None,
        period: AnalyticsPeriod = AnalyticsPeriod.WEEK
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            if agent_id:
                # Generate individual agent report
                report = await self.agent_analyzer.analyze_agent_performance(
                    agent_id, project_id, period
                )
                return report.to_dict() if report else {"error": "Failed to generate report"}
            else:
                # Generate team report
                return await self.team_analyzer.analyze_team_performance(project_id, period)
                
        except Exception as e:
            logger.log_error(e, {"action": "generate_performance_report"})
            return {"error": str(e)}
    
    async def get_performance_trends(self, project_id: str, agent_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            # Query historical performance data
            async with aiosqlite.connect(self.agent_analyzer.db_path) as db:
                if agent_id:
                    cursor = await db.execute("""
                        SELECT metric_type, metric_value, period_start, created_at
                        FROM performance_metrics
                        WHERE agent_id = ? AND project_id = ? AND created_at >= datetime('now', '-{} days')
                        ORDER BY created_at ASC
                    """.format(days), (agent_id, project_id))
                else:
                    cursor = await db.execute("""
                        SELECT metric_type, AVG(metric_value) as metric_value, period_start, created_at
                        FROM performance_metrics
                        WHERE project_id = ? AND created_at >= datetime('now', '-{} days')
                        GROUP BY metric_type, DATE(created_at)
                        ORDER BY created_at ASC
                    """.format(days), (project_id,))
                
                trends_data = {}
                async for row in cursor:
                    metric_type, metric_value, period_start, created_at = row
                    
                    if metric_type not in trends_data:
                        trends_data[metric_type] = []
                    
                    trends_data[metric_type].append({
                        "value": metric_value,
                        "date": created_at,
                        "period_start": period_start
                    })
                
                return {
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "trends": trends_data,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.log_error(e, {"action": "get_performance_trends"})
            return {"error": str(e)}
    
    async def _periodic_analysis(self):
        """Run periodic performance analysis"""
        while True:
            try:
                # Get all projects
                projects = await project_workspace_manager.list_projects()
                
                for project in projects:
                    project_id = project["project_id"]
                    
                    # Generate daily team reports
                    await self.team_analyzer.analyze_team_performance(
                        project_id, AnalyticsPeriod.DAY
                    )
                
                # Sleep for 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.log_error(e, {"action": "periodic_analysis"})
                await asyncio.sleep(3600)  # Retry in 1 hour


# Global instance
performance_analytics = PerformanceAnalytics()