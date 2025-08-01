"""
Enhanced Agent Assignment System
Manages agent task assignments with integrated workspace and codebase allocation
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger
from services.project_workspace_manager import project_workspace_manager
from services.code_artifact_manager import code_artifact_manager, ArtifactType
from services.project_channel_manager import ProjectChannelManager, ChannelType
from services.embed_system import embed_system
from services.task_hierarchy_manager import task_hierarchy_manager, TaskType, TaskPriority

logger = get_logger(__name__)


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW_PENDING = "review_pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class WorkspaceAllocation:
    """Represents a workspace allocation for an agent"""
    allocation_id: str
    project_id: str
    agent_id: str
    workspace_path: str
    git_branch: str
    allocated_files: List[str]
    permissions: Dict[str, bool]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class TaskAssignment:
    """Enhanced task assignment with workspace integration"""
    assignment_id: str
    task_id: str
    project_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    task_title: str
    task_description: str
    task_type: TaskType
    priority: TaskPriority
    estimated_hours: int
    allocated_files: List[str]
    workspace_allocation: Optional[WorkspaceAllocation]
    status: AssignmentStatus
    assigned_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    deliverables: List[str]
    metadata: Dict[str, Any]


class EnhancedAgentAssignmentService:
    """Enhanced agent assignment with workspace and codebase integration"""
    
    def __init__(self, project_channel_manager: ProjectChannelManager):
        self.project_channel_manager = project_channel_manager
        self.assignments: Dict[str, TaskAssignment] = {}
        self.workspace_allocations: Dict[str, WorkspaceAllocation] = {}
        self.agent_workloads: Dict[str, List[str]] = {}  # agent_id -> assignment_ids
        
    async def assign_task_with_workspace(
        self,
        project_id: str,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        task_title: str,
        task_description: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        estimated_hours: int = 4,
        required_files: List[str] = None,
        deliverable_types: List[ArtifactType] = None,
        due_date: Optional[datetime] = None
    ) -> str:
        """Assign a task to an agent with automatic workspace allocation"""
        try:
            assignment_id = f"assign_{uuid.uuid4().hex[:8]}"
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # Create task in task hierarchy
            await task_hierarchy_manager.create_task(
                task_id=task_id,
                title=task_title,
                description=task_description,
                task_type=task_type,
                priority=priority,
                assigned_to=agent_id,
                project_id=project_id,
                estimated_hours=estimated_hours,
                due_date=due_date
            )
            
            # Allocate workspace for the agent
            workspace_allocation = await self._allocate_agent_workspace(
                project_id=project_id,
                agent_id=agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
                required_files=required_files or []
            )
            
            # Create assignment
            assignment = TaskAssignment(
                assignment_id=assignment_id,
                task_id=task_id,
                project_id=project_id,
                agent_id=agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
                task_title=task_title,
                task_description=task_description,
                task_type=task_type,
                priority=priority,
                estimated_hours=estimated_hours,
                allocated_files=required_files or [],
                workspace_allocation=workspace_allocation,
                status=AssignmentStatus.ASSIGNED,
                assigned_at=datetime.utcnow(),
                due_date=due_date,
                completed_at=None,
                deliverables=self._generate_expected_deliverables(deliverable_types or []),
                metadata={
                    "deliverable_types": [dt.value for dt in deliverable_types or []],
                    "auto_allocated": True
                }
            )
            
            # Store assignment
            self.assignments[assignment_id] = assignment
            
            # Update agent workload tracking
            if agent_id not in self.agent_workloads:
                self.agent_workloads[agent_id] = []
            self.agent_workloads[agent_id].append(assignment_id)
            
            # Notify project channels
            await self._notify_task_assignment(assignment)
            
            # Create agent status embed
            await self._create_assignment_embed(assignment)
            
            logger.log_system_event("enhanced_task_assigned", {
                "assignment_id": assignment_id,
                "task_id": task_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "workspace_allocated": workspace_allocation is not None
            })
            
            return assignment_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "assign_task_with_workspace",
                "project_id": project_id,
                "agent_id": agent_id
            })
            raise
    
    async def _allocate_agent_workspace(
        self,
        project_id: str,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        required_files: List[str]
    ) -> Optional[WorkspaceAllocation]:
        """Allocate a workspace for an agent"""
        try:
            allocation_id = f"alloc_{uuid.uuid4().hex[:8]}"
            
            # Get project workspace
            workspace = await project_workspace_manager.get_project(project_id)
            if not workspace:
                logger.log_error("Project workspace not found", {
                    "project_id": project_id,
                    "agent_id": agent_id
                })
                return None
            
            # Add agent to project workspace
            success = await workspace.add_agent(agent_id, agent_role, agent_name)
            if not success:
                logger.log_error("Failed to add agent to workspace", {
                    "project_id": project_id,
                    "agent_id": agent_id
                })
                return None
            
            # Create workspace allocation record
            allocation = WorkspaceAllocation(
                allocation_id=allocation_id,
                project_id=project_id,
                agent_id=agent_id,
                workspace_path=workspace.agents_path + f"/{agent_id}",
                git_branch=f"agent/{agent_id}",
                allocated_files=required_files,
                permissions={
                    "read": True,
                    "write": True,
                    "create": True,
                    "delete": workspace.check_permissions(agent_id, "write")
                },
                created_at=datetime.utcnow()
            )
            
            self.workspace_allocations[allocation_id] = allocation
            
            logger.log_system_event("workspace_allocated", {
                "allocation_id": allocation_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "workspace_path": allocation.workspace_path
            })
            
            return allocation
            
        except Exception as e:
            logger.log_error(e, {
                "action": "allocate_agent_workspace",
                "project_id": project_id,
                "agent_id": agent_id
            })
            return None
    
    async def _notify_task_assignment(self, assignment: TaskAssignment):
        """Notify project channels about task assignment"""
        try:
            # Get agent updates channel
            agent_updates_channel = await self.project_channel_manager.get_channel_by_type(
                assignment.project_id,
                ChannelType.AGENT_UPDATES
            )
            
            if agent_updates_channel:
                content = f"📋 **New Task Assignment**\n\n"
                content += f"**Agent:** {assignment.agent_name} ({assignment.agent_role})\n"
                content += f"**Task:** {assignment.task_title}\n"
                content += f"**Priority:** {assignment.priority.value.title()}\n"
                content += f"**Estimated Hours:** {assignment.estimated_hours}h\n"
                
                if assignment.workspace_allocation:
                    content += f"**Workspace:** `{assignment.workspace_allocation.git_branch}`\n"
                
                if assignment.due_date:
                    content += f"**Due Date:** {assignment.due_date.strftime('%Y-%m-%d')}\n"
                
                content += f"\n**Description:**\n{assignment.task_description}"
                
                await self.project_channel_manager.send_channel_message(
                    channel_id=agent_updates_channel.id,
                    sender_id="system",
                    sender_name="Task Manager",
                    sender_type="system",
                    content=content,
                    message_type="task_assignment",
                    metadata={
                        "assignment_id": assignment.assignment_id,
                        "task_id": assignment.task_id,
                        "agent_id": assignment.agent_id
                    }
                )
            
        except Exception as e:
            logger.log_error(e, {
                "action": "notify_task_assignment",
                "assignment_id": assignment.assignment_id
            })
    
    async def _create_assignment_embed(self, assignment: TaskAssignment):
        """Create an embed for the task assignment"""
        try:
            embed = await embed_system.create_agent_status_embed(
                agent_id=assignment.agent_id,
                agent_name=assignment.agent_name,
                agent_role=assignment.agent_role,
                status="busy",
                current_task=assignment.task_title,
                tasks_completed=0,  # Would track this from agent history
                performance_metrics={
                    "estimated_hours": assignment.estimated_hours,
                    "priority": assignment.priority.value,
                    "workspace_allocated": "Yes" if assignment.workspace_allocation else "No"
                }
            )
            
            logger.log_system_event("assignment_embed_created", {
                "embed_id": embed.id,
                "assignment_id": assignment.assignment_id,
                "agent_id": assignment.agent_id
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_assignment_embed",
                "assignment_id": assignment.assignment_id
            })
    
    def _generate_expected_deliverables(self, deliverable_types: List[ArtifactType]) -> List[str]:
        """Generate expected deliverable descriptions"""
        deliverables = []
        
        for artifact_type in deliverable_types:
            if artifact_type == ArtifactType.SOURCE_CODE:
                deliverables.append("Implemented code files")
            elif artifact_type == ArtifactType.TEST_FILE:
                deliverables.append("Unit tests and test cases")
            elif artifact_type == ArtifactType.DOCUMENTATION:
                deliverables.append("Technical documentation")
            elif artifact_type == ArtifactType.CONFIGURATION:
                deliverables.append("Configuration files")
            elif artifact_type == ArtifactType.SCHEMA:
                deliverables.append("Database schema or API definitions")
            else:
                deliverables.append(f"{artifact_type.value.replace('_', ' ').title()} files")
        
        return deliverables
    
    async def update_assignment_status(
        self,
        assignment_id: str,
        new_status: AssignmentStatus,
        completion_notes: Optional[str] = None
    ) -> bool:
        """Update assignment status"""
        try:
            if assignment_id not in self.assignments:
                return False
            
            assignment = self.assignments[assignment_id]
            old_status = assignment.status
            assignment.status = new_status
            
            if new_status == AssignmentStatus.COMPLETED:
                assignment.completed_at = datetime.utcnow()
            
            # Update task in hierarchy
            await task_hierarchy_manager.update_task_status(
                task_id=assignment.task_id,
                status=new_status.value,
                completion_notes=completion_notes
            )
            
            # Notify channels about status change
            await self._notify_status_change(assignment, old_status, completion_notes)
            
            logger.log_system_event("assignment_status_updated", {
                "assignment_id": assignment_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "agent_id": assignment.agent_id
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "update_assignment_status",
                "assignment_id": assignment_id
            })
            return False
    
    async def _notify_status_change(
        self,
        assignment: TaskAssignment,
        old_status: AssignmentStatus,
        completion_notes: Optional[str]
    ):
        """Notify about assignment status changes"""
        try:
            # Get agent updates channel
            agent_updates_channel = await self.project_channel_manager.get_channel_by_type(
                assignment.project_id,
                ChannelType.AGENT_UPDATES
            )
            
            if agent_updates_channel:
                status_emoji = {
                    AssignmentStatus.IN_PROGRESS: "⏳",
                    AssignmentStatus.REVIEW_PENDING: "👀",
                    AssignmentStatus.COMPLETED: "✅",
                    AssignmentStatus.CANCELLED: "❌"
                }
                
                content = f"{status_emoji.get(assignment.status, '📋')} **Task Status Update**\n\n"
                content += f"**Agent:** {assignment.agent_name}\n"
                content += f"**Task:** {assignment.task_title}\n"
                content += f"**Status:** {old_status.value.replace('_', ' ').title()} → **{assignment.status.value.replace('_', ' ').title()}**\n"
                
                if completion_notes:
                    content += f"\n**Notes:** {completion_notes}"
                
                await self.project_channel_manager.send_channel_message(
                    channel_id=agent_updates_channel.id,
                    sender_id=assignment.agent_id,
                    sender_name=assignment.agent_name,
                    sender_type="agent",
                    content=content,
                    message_type="status_update",
                    metadata={
                        "assignment_id": assignment.assignment_id,
                        "old_status": old_status.value,
                        "new_status": assignment.status.value
                    }
                )
            
        except Exception as e:
            logger.log_error(e, {
                "action": "notify_status_change",
                "assignment_id": assignment.assignment_id
            })
    
    async def submit_deliverable(
        self,
        assignment_id: str,
        file_path: str,
        content: str,
        artifact_type: ArtifactType,
        description: str = ""
    ) -> Optional[str]:
        """Submit a deliverable for an assignment"""
        try:
            if assignment_id not in self.assignments:
                return None
            
            assignment = self.assignments[assignment_id]
            
            # Create code artifact
            artifact_id = await code_artifact_manager.create_artifact(
                project_id=assignment.project_id,
                agent_id=assignment.agent_id,
                agent_name=assignment.agent_name,
                file_path=file_path,
                content=content,
                artifact_type=artifact_type,
                task_id=assignment.task_id,
                description=description or f"Deliverable for task: {assignment.task_title}",
                metadata={
                    "assignment_id": assignment_id,
                    "deliverable": True,
                    "submitted_at": datetime.utcnow().isoformat()
                }
            )
            
            # Create artifact embed
            artifact = await code_artifact_manager.get_artifact(artifact_id)
            if artifact:
                embed = await embed_system.create_code_artifact_embed(
                    artifact=artifact,
                    changes_summary=f"Submitted as deliverable for {assignment.task_title}"
                )
                
                # Send to code review channel
                code_review_channel = await self.project_channel_manager.get_channel_by_type(
                    assignment.project_id,
                    ChannelType.CODE_REVIEW
                )
                
                if code_review_channel:
                    await self.project_channel_manager.send_channel_message(
                        channel_id=code_review_channel.id,
                        sender_id=assignment.agent_id,
                        sender_name=assignment.agent_name,
                        sender_type="agent",
                        content=f"📄 **Code Review Request**\n\nI've completed `{file_path}` for the task **{assignment.task_title}**. Please review when you have a chance!",
                        message_type="code_review",
                        embeds=[embed_system.to_dict(embed)],
                        metadata={
                            "artifact_id": artifact_id,
                            "assignment_id": assignment_id,
                            "review_requested": True
                        }
                    )
            
            # Update assignment to review pending if this completes all deliverables
            await self.update_assignment_status(assignment_id, AssignmentStatus.REVIEW_PENDING)
            
            logger.log_system_event("deliverable_submitted", {
                "assignment_id": assignment_id,
                "artifact_id": artifact_id,
                "agent_id": assignment.agent_id,
                "file_path": file_path
            })
            
            return artifact_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "submit_deliverable",
                "assignment_id": assignment_id,
                "file_path": file_path
            })
            return None
    
    async def get_agent_assignments(self, agent_id: str) -> List[TaskAssignment]:
        """Get all assignments for an agent"""
        agent_assignment_ids = self.agent_workloads.get(agent_id, [])
        return [self.assignments[aid] for aid in agent_assignment_ids if aid in self.assignments]
    
    async def get_project_assignments(self, project_id: str) -> List[TaskAssignment]:
        """Get all assignments for a project"""
        return [
            assignment for assignment in self.assignments.values()
            if assignment.project_id == project_id
        ]
    
    async def get_assignment(self, assignment_id: str) -> Optional[TaskAssignment]:
        """Get a specific assignment"""
        return self.assignments.get(assignment_id)


# Global instance will be created when project_channel_manager is available