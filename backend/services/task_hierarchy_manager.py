"""
ARTAC Task Hierarchy Manager
Intelligent task assignment and management system with agent hierarchy support
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from core.config import settings
from core.logging import get_logger
from core.database_postgres import db
from services.interaction_logger import interaction_logger, InteractionType, LogLevel
from services.rag_context_manager import rag_context_manager

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task status types"""
    DRAFT = "draft"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(Enum):
    """Task types"""
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    SUBTASK = "subtask"
    BUG = "bug"
    RESEARCH = "research"


class AgentSkill(Enum):
    """Agent skill categories"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"


@dataclass
class Task:
    """Task definition with hierarchy support"""
    id: str
    project_id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_by: str
    assigned_to: Optional[str]
    parent_task_id: Optional[str]
    subtask_ids: List[str]
    dependencies: List[str]  # Task IDs this task depends on
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    tags: List[str]
    required_skills: List[AgentSkill]
    file_paths: List[str]  # Files related to this task
    acceptance_criteria: List[str]
    progress_percentage: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['due_date'] = self.due_date.isoformat() if self.due_date else None
        data['required_skills'] = [skill.value for skill in self.required_skills]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary"""
        data['task_type'] = TaskType(data['task_type'])
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        data['due_date'] = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
        data['required_skills'] = [AgentSkill(skill) for skill in data['required_skills']]
        return cls(**data)


@dataclass
class Agent:
    """Agent profile with skills and hierarchy"""
    id: str
    name: str
    role: str  # ceo, senior, developer, intern
    skills: List[AgentSkill]
    skill_levels: Dict[str, int]  # skill -> level (1-10)
    hierarchy_level: int  # 1-100, higher = more senior
    current_workload: float  # hours of assigned work
    max_workload: float  # maximum hours per week
    availability: Dict[str, Any]  # schedule and availability info
    performance_metrics: Dict[str, float]
    preferences: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['skills'] = [skill.value for skill in self.skills]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create from dictionary"""
        data['skills'] = [AgentSkill(skill) for skill in data['skills']]
        return cls(**data)


class TaskMatcher:
    """AI-powered task-to-agent matching"""
    
    def __init__(self):
        self.matching_algorithms = {
            "skill_based": self._skill_based_matching,
            "workload_balanced": self._workload_balanced_matching,
            "hierarchy_aware": self._hierarchy_aware_matching,
            "experience_weighted": self._experience_weighted_matching
        }
    
    async def find_best_agent(
        self,
        task: Task,
        available_agents: List[Agent],
        algorithm: str = "hierarchy_aware"
    ) -> Optional[str]:
        """Find the best agent for a task"""
        try:
            if not available_agents:
                return None
            
            matcher = self.matching_algorithms.get(algorithm, self._hierarchy_aware_matching)
            return await matcher(task, available_agents)
            
        except Exception as e:
            logger.log_error(e, {
                "action": "find_best_agent",
                "task_id": task.id,
                "algorithm": algorithm
            })
            return None
    
    async def _skill_based_matching(self, task: Task, agents: List[Agent]) -> Optional[str]:
        """Match based on required skills"""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            score = 0
            
            # Calculate skill match score
            for required_skill in task.required_skills:
                if required_skill in agent.skills:
                    skill_level = agent.skill_levels.get(required_skill.value, 1)
                    score += skill_level
            
            # Normalize by number of required skills
            if task.required_skills:
                score = score / len(task.required_skills)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.id if best_agent else None
    
    async def _workload_balanced_matching(self, task: Task, agents: List[Agent]) -> Optional[str]:
        """Match based on current workload"""
        best_agent = None
        lowest_utilization = float('inf')
        
        for agent in agents:
            # Check if agent has required skills
            has_skills = any(skill in agent.skills for skill in task.required_skills)
            if task.required_skills and not has_skills:
                continue
            
            # Calculate workload utilization
            utilization = agent.current_workload / agent.max_workload if agent.max_workload > 0 else 1.0
            
            if utilization < lowest_utilization:
                lowest_utilization = utilization
                best_agent = agent
        
        return best_agent.id if best_agent else None
    
    async def _hierarchy_aware_matching(self, task: Task, agents: List[Agent]) -> Optional[str]:
        """Match based on task complexity and agent hierarchy"""
        # Define task complexity scores
        complexity_scores = {
            TaskType.EPIC: 10,
            TaskType.STORY: 7,
            TaskType.TASK: 5,
            TaskType.SUBTASK: 3,
            TaskType.BUG: 4,
            TaskType.RESEARCH: 6
        }
        
        task_complexity = complexity_scores.get(task.task_type, 5)
        
        best_agent = None
        best_score = -1
        
        for agent in agents:
            # Check skill requirements
            skill_match = 0
            if task.required_skills:
                matching_skills = sum(1 for skill in task.required_skills if skill in agent.skills)
                skill_match = matching_skills / len(task.required_skills)
            else:
                skill_match = 1.0  # No specific skills required
            
            # Check hierarchy appropriateness
            hierarchy_match = min(agent.hierarchy_level / (task_complexity * 10), 1.0)
            
            # Check workload
            workload_factor = max(0, 1.0 - (agent.current_workload / agent.max_workload)) if agent.max_workload > 0 else 0.5
            
            # Priority factor
            priority_factors = {
                TaskPriority.CRITICAL: 1.2,
                TaskPriority.HIGH: 1.1,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.LOW: 0.9
            }
            priority_factor = priority_factors.get(task.priority, 1.0)
            
            # Calculate combined score
            score = (skill_match * 0.4 + hierarchy_match * 0.3 + workload_factor * 0.3) * priority_factor
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.id if best_agent else None
    
    async def _experience_weighted_matching(self, task: Task, agents: List[Agent]) -> Optional[str]:
        """Match based on agent experience and performance"""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            # Base skill score
            skill_score = 0
            for required_skill in task.required_skills:
                if required_skill in agent.skills:
                    skill_level = agent.skill_levels.get(required_skill.value, 1)
                    skill_score += skill_level
            
            # Performance metrics
            completion_rate = agent.performance_metrics.get("completion_rate", 0.8)
            quality_score = agent.performance_metrics.get("quality_score", 0.7)
            speed_factor = agent.performance_metrics.get("speed_factor", 1.0)
            
            # Experience factor (based on hierarchy level)
            experience_factor = agent.hierarchy_level / 100.0
            
            # Combined score
            score = (skill_score * 0.3 + completion_rate * 0.25 + 
                    quality_score * 0.25 + experience_factor * 0.2) * speed_factor
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.id if best_agent else None


class TaskHierarchyManager:
    """Advanced task hierarchy and assignment manager"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.agents: Dict[str, Agent] = {}
        self.task_matcher = TaskMatcher()
        
        # Initialize database tables after startup
        self._db_initialized = False
    
    async def _initialize_database(self):
        """Initialize PostgreSQL database for task management"""
        try:
            table_definitions = {
                "tasks": """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        task_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        assigned_to TEXT,
                        parent_task_id TEXT,
                        subtask_ids TEXT[],
                        dependencies TEXT[],
                        estimated_hours REAL,
                        actual_hours REAL,
                        due_date TIMESTAMPTZ,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMPTZ,
                        tags TEXT[],
                        required_skills TEXT[],
                        file_paths TEXT[],
                        acceptance_criteria TEXT[],
                        progress_percentage INTEGER DEFAULT 0,
                        metadata JSONB,
                        FOREIGN KEY (parent_task_id) REFERENCES tasks (id)
                    )
                """,
                "agents": """
                    CREATE TABLE IF NOT EXISTS agents (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        skills TEXT[],
                        skill_levels JSONB,
                        hierarchy_level INTEGER NOT NULL,
                        current_workload REAL DEFAULT 0,
                        max_workload REAL DEFAULT 40,
                        availability TEXT,
                        performance_metrics JSONB,
                        preferences JSONB,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "task_assignments": """
                    CREATE TABLE IF NOT EXISTS task_assignments (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        assigned_by TEXT NOT NULL,
                        assigned_at TIMESTAMPTZ NOT NULL,
                        unassigned_at TIMESTAMPTZ,
                        assignment_reason TEXT,
                        metadata JSONB,
                        FOREIGN KEY (task_id) REFERENCES tasks (id),
                        FOREIGN KEY (agent_id) REFERENCES agents (id)
                    )
                """
            }
            
            # Create tables
            await db.create_tables_if_not_exist(table_definitions)
            
            # Create indexes for performance
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)",
                "CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role)",
                "CREATE INDEX IF NOT EXISTS idx_agents_hierarchy ON agents(hierarchy_level)",
                "CREATE INDEX IF NOT EXISTS idx_assignments_task ON task_assignments(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_assignments_agent ON task_assignments(agent_id)"
            ]
            
            for index_query in index_queries:
                try:
                    await db.execute(index_query)
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            logger.log_system_event("task_hierarchy_manager_initialized", {
                "database": "PostgreSQL"
            })
            
            self._db_initialized = True
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_task_database"})
    
    async def _ensure_database_initialized(self):
        """Ensure database is initialized before use"""
        if not self._db_initialized and db.is_connected:
            await self._initialize_database()
    
    async def create_task(
        self,
        project_id: str,
        title: str,
        description: str,
        task_type: TaskType,
        created_by: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: str = None,
        required_skills: List[AgentSkill] = None,
        estimated_hours: float = None,
        due_date: datetime = None,
        file_paths: List[str] = None,
        acceptance_criteria: List[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new task"""
        try:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            task = Task(
                id=task_id,
                project_id=project_id,
                title=title,
                description=description,
                task_type=task_type,
                status=TaskStatus.DRAFT,
                priority=priority,
                created_by=created_by,
                assigned_to=None,
                parent_task_id=parent_task_id,
                subtask_ids=[],
                dependencies=[],
                estimated_hours=estimated_hours,
                actual_hours=None,
                due_date=due_date,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=None,
                tags=tags or [],
                required_skills=required_skills or [],
                file_paths=file_paths or [],
                acceptance_criteria=acceptance_criteria or [],
                progress_percentage=0,
                metadata=metadata or {}
            )
            
            # Store task
            await self._store_task(task)
            self.tasks[task_id] = task
            
            # Update parent task if applicable
            if parent_task_id and parent_task_id in self.tasks:
                parent_task = self.tasks[parent_task_id]
                parent_task.subtask_ids.append(task_id)
                await self._update_task(parent_task)
            
            # Add to RAG context
            await rag_context_manager.add_context(
                project_id=project_id,
                agent_id=created_by,
                content=f"Task: {title}\nDescription: {description}\nType: {task_type.value}",
                content_type="task",
                metadata={
                    "task_id": task_id,
                    "task_type": task_type.value,
                    "priority": priority.value,
                    "required_skills": [skill.value for skill in required_skills or []]
                }
            )
            
            # Log task creation
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=created_by,
                interaction_type=InteractionType.TASK_ASSIGNMENT,
                action="task_created",
                content=f"Created {task_type.value}: {title}",
                context={
                    "task_id": task_id,
                    "task_type": task_type.value,
                    "priority": priority.value,
                    "parent_task_id": parent_task_id
                },
                metadata=metadata or {}
            )
            
            return task_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_task",
                "project_id": project_id,
                "title": title
            })
            return ""
    
    async def assign_task(
        self,
        task_id: str,
        agent_id: str,
        assigned_by: str,
        assignment_reason: str = "manual"
    ) -> bool:
        """Assign a task to an agent"""
        try:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            old_assignee = task.assigned_to
            
            # Update task
            task.assigned_to = agent_id
            task.status = TaskStatus.ASSIGNED
            task.updated_at = datetime.utcnow()
            
            try:
                await self._update_task(task)
                
                # Record assignment history only if task update succeeded
                assignment_id = f"assign_{uuid.uuid4().hex[:8]}"
                
                await db.execute("""
                    INSERT INTO task_assignments 
                    (id, task_id, agent_id, assigned_by, assigned_at, assignment_reason)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    assignment_id,
                    task_id,
                    agent_id,
                    assigned_by,
                    datetime.utcnow(),
                    assignment_reason
                )
            except Exception as task_error:
                # Rollback assignment if task update failed
                task.assigned_to = old_assignee
                task.status = TaskStatus.PENDING if old_assignee is None else TaskStatus.ASSIGNED
                logger.log_error(task_error, {"action": "assign_task", "task_id": task_id, "agent_id": agent_id})
                return False
            
            # Update agent workload
            if agent_id in self.agents and task.estimated_hours:
                self.agents[agent_id].current_workload += task.estimated_hours
            
            # Log assignment
            await interaction_logger.log_interaction(
                project_id=task.project_id,
                agent_id=assigned_by,
                interaction_type=InteractionType.TASK_ASSIGNMENT,
                action="task_assigned",
                content=f"Assigned task '{task.title}' to {agent_id}",
                context={
                    "task_id": task_id,
                    "assigned_to": agent_id,
                    "previous_assignee": old_assignee,
                    "assignment_reason": assignment_reason
                }
            )
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "assign_task",
                "task_id": task_id,
                "agent_id": agent_id
            })
            return False
    
    async def auto_assign_task(
        self,
        task_id: str,
        assigned_by: str,
        algorithm: str = "hierarchy_aware"
    ) -> Optional[str]:
        """Automatically assign a task to the best available agent"""
        try:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            
            # Get available agents
            available_agents = [
                agent for agent in self.agents.values()
                if agent.current_workload < agent.max_workload
            ]
            
            if not available_agents:
                return None
            
            # Find best agent
            best_agent_id = await self.task_matcher.find_best_agent(
                task, available_agents, algorithm
            )
            
            if best_agent_id:
                success = await self.assign_task(
                    task_id, best_agent_id, assigned_by, f"auto_{algorithm}"
                )
                return best_agent_id if success else None
            
            return None
            
        except Exception as e:
            logger.log_error(e, {
                "action": "auto_assign_task",
                "task_id": task_id,
                "algorithm": algorithm
            })
            return None
    
    async def update_task_progress(
        self,
        task_id: str,
        progress_percentage: int,
        status: TaskStatus = None,
        actual_hours: float = None,
        agent_id: str = None
    ) -> bool:
        """Update task progress"""
        try:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            old_progress = task.progress_percentage
            
            # Update task
            task.progress_percentage = min(max(progress_percentage, 0), 100)
            task.updated_at = datetime.utcnow()
            
            if status:
                task.status = status
            
            if actual_hours:
                task.actual_hours = actual_hours
            
            if progress_percentage >= 100:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            
            await self._update_task(task)
            
            # Update parent task progress
            if task.parent_task_id:
                await self._update_parent_progress(task.parent_task_id)
            
            # Log progress update
            await interaction_logger.log_interaction(
                project_id=task.project_id,
                agent_id=agent_id or task.assigned_to or "system",
                interaction_type=InteractionType.TASK_ASSIGNMENT,
                action="task_progress_updated",
                content=f"Updated progress for '{task.title}': {old_progress}% -> {progress_percentage}%",
                context={
                    "task_id": task_id,
                    "old_progress": old_progress,
                    "new_progress": progress_percentage,
                    "status": status.value if status else task.status.value
                }
            )
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "update_task_progress",
                "task_id": task_id
            })
            return False
    
    async def get_agent_tasks(
        self,
        agent_id: str,
        project_id: str = None,
        status_filter: List[TaskStatus] = None
    ) -> List[Task]:
        """Get tasks assigned to an agent"""
        try:
            agent_tasks = []
            
            for task in self.tasks.values():
                if task.assigned_to != agent_id:
                    continue
                
                if project_id and task.project_id != project_id:
                    continue
                
                if status_filter and task.status not in status_filter:
                    continue
                
                agent_tasks.append(task)
            
            # Sort by priority and due date
            agent_tasks.sort(key=lambda t: (
                t.priority.value,
                t.due_date or datetime.max,
                t.created_at
            ))
            
            return agent_tasks
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_agent_tasks",
                "agent_id": agent_id
            })
            return []
    
    async def get_project_tasks(
        self,
        project_id: str,
        task_type: TaskType = None,
        status_filter: List[TaskStatus] = None
    ) -> List[Task]:
        """Get all tasks for a project"""
        try:
            project_tasks = []
            
            for task in self.tasks.values():
                if task.project_id != project_id:
                    continue
                
                if task_type and task.task_type != task_type:
                    continue
                
                if status_filter and task.status not in status_filter:
                    continue
                
                project_tasks.append(task)
            
            return project_tasks
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_project_tasks",
                "project_id": project_id
            })
            return []
    
    async def get_task_hierarchy(self, task_id: str) -> Dict[str, Any]:
        """Get task hierarchy (parent and children)"""
        try:
            if task_id not in self.tasks:
                return {}
            
            task = self.tasks[task_id]
            
            # Get parent chain
            parent_chain = []
            current_parent_id = task.parent_task_id
            while current_parent_id and current_parent_id in self.tasks:
                parent_task = self.tasks[current_parent_id]
                parent_chain.append(parent_task.to_dict())
                current_parent_id = parent_task.parent_task_id
            
            # Get children
            children = []
            for subtask_id in task.subtask_ids:
                if subtask_id in self.tasks:
                    children.append(self.tasks[subtask_id].to_dict())
            
            return {
                "task": task.to_dict(),
                "parent_chain": list(reversed(parent_chain)),
                "children": children,
                "total_subtasks": len(task.subtask_ids),
                "completed_subtasks": len([
                    sid for sid in task.subtask_ids
                    if sid in self.tasks and self.tasks[sid].status == TaskStatus.COMPLETED
                ])
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_task_hierarchy",
                "task_id": task_id
            })
            return {}
    
    async def register_agent(
        self,
        agent_id: str,
        name: str,
        role: str,
        skills: List[AgentSkill],
        skill_levels: Dict[str, int] = None,
        max_workload: float = 40.0
    ) -> bool:
        """Register an agent in the system"""
        try:
            # Define hierarchy levels
            hierarchy_levels = {
                "ceo": 100,
                "senior": 80,
                "developer": 60,
                "intern": 20
            }
            
            agent = Agent(
                id=agent_id,
                name=name,
                role=role,
                skills=skills,
                skill_levels=skill_levels or {},
                hierarchy_level=hierarchy_levels.get(role, 50),
                current_workload=0.0,
                max_workload=max_workload,
                availability={},
                performance_metrics={
                    "completion_rate": 0.8,
                    "quality_score": 0.7,
                    "speed_factor": 1.0
                },
                preferences={},
                metadata={}
            )
            
            await self._store_agent(agent)
            self.agents[agent_id] = agent
            
            logger.log_system_event("agent_registered", {
                "agent_id": agent_id,
                "name": name,
                "role": role,
                "hierarchy_level": agent.hierarchy_level
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "register_agent",
                "agent_id": agent_id
            })
            return False
    
    async def suggest_task_breakdown(self, task_id: str) -> List[Dict[str, Any]]:
        """Suggest how to break down a complex task"""
        try:
            if task_id not in self.tasks:
                return []
            
            task = self.tasks[task_id]
            
            # Use RAG context to get similar tasks and breakdown patterns
            context = await rag_context_manager.get_context(
                project_id=task.project_id,
                agent_id="system",
                query=f"break down task similar to: {task.title} {task.description}",
                content_types=["task"],
                max_tokens=10000
            )
            
            # Basic breakdown suggestions based on task type
            suggestions = []
            
            if task.task_type == TaskType.EPIC:
                suggestions = [
                    {
                        "title": f"Research and Planning for {task.title}",
                        "description": "Research requirements and create detailed plan",
                        "task_type": TaskType.STORY.value,
                        "estimated_hours": (task.estimated_hours or 40) * 0.2
                    },
                    {
                        "title": f"Core Implementation of {task.title}",
                        "description": "Main implementation work",
                        "task_type": TaskType.STORY.value,
                        "estimated_hours": (task.estimated_hours or 40) * 0.6
                    },
                    {
                        "title": f"Testing and Documentation for {task.title}",
                        "description": "Testing, documentation, and cleanup",
                        "task_type": TaskType.STORY.value,
                        "estimated_hours": (task.estimated_hours or 40) * 0.2
                    }
                ]
            elif task.task_type == TaskType.STORY:
                # Break story into tasks
                suggestions = [
                    {
                        "title": f"Setup for {task.title}",
                        "description": "Initial setup and scaffolding",
                        "task_type": TaskType.TASK.value,
                        "estimated_hours": (task.estimated_hours or 8) * 0.3
                    },
                    {
                        "title": f"Implementation of {task.title}",
                        "description": "Core implementation",
                        "task_type": TaskType.TASK.value,
                        "estimated_hours": (task.estimated_hours or 8) * 0.5
                    },
                    {
                        "title": f"Testing {task.title}",
                        "description": "Unit tests and integration tests",
                        "task_type": TaskType.TASK.value,
                        "estimated_hours": (task.estimated_hours or 8) * 0.2
                    }
                ]
            
            return suggestions
            
        except Exception as e:
            logger.log_error(e, {
                "action": "suggest_task_breakdown",
                "task_id": task_id
            })
            return []
    
    async def _store_task(self, task: Task):
        """Store task in database"""
        try:
# PostgreSQL connection handled by global db instance
                await db.execute("""
                    INSERT INTO tasks 
                    (id, project_id, title, description, task_type, status, priority, created_by,
                     assigned_to, parent_task_id, subtask_ids, dependencies, estimated_hours,
                     actual_hours, due_date, created_at, updated_at, completed_at, tags,
                     required_skills, file_paths, acceptance_criteria, progress_percentage, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
                """, 
                    task.id, task.project_id, task.title, task.description,
                    task.task_type.value, task.status.value, task.priority.value,
                    task.created_by, task.assigned_to, task.parent_task_id,
                    task.subtask_ids, task.dependencies,  # PostgreSQL arrays
                    task.estimated_hours, task.actual_hours,
                    task.due_date, task.created_at, task.updated_at, task.completed_at,
                    task.tags,  # PostgreSQL array
                    [skill.value for skill in task.required_skills],  # PostgreSQL array
                    task.file_paths,  # PostgreSQL array
                    task.acceptance_criteria,  # PostgreSQL array - not JSON
                    task.progress_percentage, json.dumps(task.metadata)
                )
                
        except Exception as e:
            logger.log_error(e, {"action": "store_task"})
            raise  # Re-raise to prevent further operations on failed task
    
    async def _update_task(self, task: Task):
        """Update task in database"""
        try:
# PostgreSQL connection handled by global db instance
                await db.execute("""
                    UPDATE tasks SET
                        title = $1, description = $2, task_type = $3, status = $4, priority = $5,
                        assigned_to = $6, parent_task_id = $7, subtask_ids = $8, dependencies = $9,
                        estimated_hours = $10, actual_hours = $11, due_date = $12, updated_at = $13,
                        completed_at = $14, tags = $15, required_skills = $16, file_paths = $17,
                        acceptance_criteria = $18, progress_percentage = $19, metadata = $20
                    WHERE id = $21
                """, 
                    task.title, task.description, task.task_type.value,
                    task.status.value, task.priority.value, task.assigned_to,
                    task.parent_task_id, task.subtask_ids, task.dependencies,  # PostgreSQL arrays
                    task.estimated_hours, task.actual_hours,
                    task.due_date, task.updated_at, task.completed_at,  # PostgreSQL datetime objects
                    task.tags, [skill.value for skill in task.required_skills], task.file_paths,  # PostgreSQL arrays
                    json.dumps(task.acceptance_criteria),
                    task.progress_percentage, json.dumps(task.metadata), task.id
                )
                
        except Exception as e:
            logger.log_error(e, {"action": "update_task"})
            raise  # Re-raise to prevent further operations on failed task
    
    async def _store_agent(self, agent: Agent):
        """Store agent in database"""
        try:
# PostgreSQL connection handled by global db instance
                await db.execute("""
                    INSERT INTO agents 
                    (id, name, role, skills, skill_levels, hierarchy_level, current_workload,
                     max_workload, availability, performance_metrics, preferences, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        role = EXCLUDED.role,
                        skills = EXCLUDED.skills,
                        skill_levels = EXCLUDED.skill_levels,
                        hierarchy_level = EXCLUDED.hierarchy_level,
                        current_workload = EXCLUDED.current_workload,
                        max_workload = EXCLUDED.max_workload,
                        availability = EXCLUDED.availability,
                        performance_metrics = EXCLUDED.performance_metrics,
                        preferences = EXCLUDED.preferences,
                        metadata = EXCLUDED.metadata
                """, 
                    agent.id, agent.name, agent.role,
                    [skill.value for skill in agent.skills],  # PostgreSQL array
                    json.dumps(agent.skill_levels), agent.hierarchy_level,
                    agent.current_workload, agent.max_workload,
                    json.dumps(agent.availability), json.dumps(agent.performance_metrics),
                    json.dumps(agent.preferences), json.dumps(agent.metadata)
                )
                
        except Exception as e:
            logger.log_error(e, {"action": "store_agent"})
    
    async def _update_parent_progress(self, parent_task_id: str):
        """Update parent task progress based on subtasks"""
        try:
            if parent_task_id not in self.tasks:
                return
            
            parent_task = self.tasks[parent_task_id]
            
            if not parent_task.subtask_ids:
                return
            
            # Calculate average progress of subtasks
            total_progress = 0
            completed_subtasks = 0
            
            for subtask_id in parent_task.subtask_ids:
                if subtask_id in self.tasks:
                    subtask = self.tasks[subtask_id]
                    total_progress += subtask.progress_percentage
                    if subtask.status == TaskStatus.COMPLETED:
                        completed_subtasks += 1
            
            # Update parent progress
            if parent_task.subtask_ids:
                new_progress = total_progress // len(parent_task.subtask_ids)
                parent_task.progress_percentage = new_progress
                parent_task.updated_at = datetime.utcnow()
                
                # If all subtasks are completed, mark parent as completed
                if completed_subtasks == len(parent_task.subtask_ids):
                    parent_task.status = TaskStatus.COMPLETED
                    parent_task.completed_at = datetime.utcnow()
                
                await self._update_task(parent_task)
                
                # Recursively update grandparent
                if parent_task.parent_task_id:
                    await self._update_parent_progress(parent_task.parent_task_id)
                    
        except Exception as e:
            logger.log_error(e, {"action": "update_parent_progress"})


# Global instance
task_hierarchy_manager = TaskHierarchyManager()