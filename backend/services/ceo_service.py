"""
ARTAC CEO Service
Real CEO agent that makes decisions and hires agents
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger
from services.agent_manager import AgentRole, AgentSkill
from services.task_hierarchy_manager import TaskType, TaskPriority, task_hierarchy_manager
from services.interaction_logger import interaction_logger, InteractionType
from services.project_workspace_manager import project_workspace_manager
from services.project_channel_manager import ProjectChannelManager
from services.inter_agent_communication import InterAgentCommunicationService

# Assembly platform integration
try:
    from services.artac_assembly import artac_assembly
    from services.perpetual_efficiency_model import perpetual_efficiency_model
except ImportError:
    artac_assembly = None
    perpetual_efficiency_model = None

logger = get_logger(__name__)


class ProjectComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class Project:
    id: str
    title: str
    description: str
    complexity: ProjectComplexity
    estimated_hours: int
    required_skills: List[AgentSkill]
    assigned_agents: List[str]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class HiringDecision:
    project_id: str
    required_roles: List[AgentRole]
    reasoning: str
    estimated_budget: float
    timeline_days: int
    created_at: datetime


class CEOService:
    """Real CEO service that makes hiring decisions and manages projects"""
    
    def __init__(self, agent_manager, inter_agent_comm: InterAgentCommunicationService):
        self.agent_manager = agent_manager
        self.inter_agent_comm = inter_agent_comm
        self.project_channel_manager = ProjectChannelManager(inter_agent_comm)
        self.active_projects: Dict[str, Project] = {}
        self.hiring_decisions: List[HiringDecision] = []
        self.conversation_context: Dict[str, Any] = {}
        
        # CEO decision-making parameters
        self.max_budget_per_project = 50000
        self.preferred_team_sizes = {
            ProjectComplexity.SIMPLE: 2,
            ProjectComplexity.MODERATE: 3,
            ProjectComplexity.COMPLEX: 5,
            ProjectComplexity.ENTERPRISE: 8
        }
        
    async def receive_project_request(
        self,
        title: str,
        description: str,
        user_id: str = "client"
    ) -> Dict[str, Any]:
        """Receive and analyze a new project request"""
        
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        # CEO analyzes the project
        analysis = await self._analyze_project_requirements(title, description)
        
        # Create project record
        project = Project(
            id=project_id,
            title=title,
            description=description,
            complexity=analysis["complexity"],
            estimated_hours=analysis["estimated_hours"],
            required_skills=analysis["required_skills"],
            assigned_agents=[],
            status="analyzing",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.active_projects[project_id] = project
        
        # Create project workspace
        workspace_created = await self._create_project_workspace(project_id, title)
        
        # Create project communication channels
        channels_created = await self._create_project_channels(project_id, title, "ceo-001")
        
        # Initialize Assembly platform for collaborative work
        if artac_assembly:
            try:
                # This integrates with the human directive workflow
                await artac_assembly.initiate_project_genesis(
                    human_directive=description,
                    project_title=title,
                    estimated_budget_hours=analysis["estimated_hours"],
                    timeline_weeks=max(1, analysis["estimated_hours"] // 40),  # Rough weeks estimate
                    ceo_agent_id="ceo-001"
                )
                logger.log_system_event("assembly_platform_integrated", {
                    "project_id": project_id,
                    "assembly_initiated": True
                })
            except Exception as e:
                logger.log_error(e, {
                    "action": "assembly_platform_integration",
                    "project_id": project_id
                })
        
        # Log CEO decision-making process
        await interaction_logger.log_interaction(
            project_id=project_id,
            agent_id="ceo-001",
            interaction_type=InteractionType.SYSTEM_EVENT,
            action="project_received",
            content=f"CEO analyzing project: {title}",
            context={
                "user_id": user_id,
                "complexity": analysis["complexity"].value,
                "estimated_hours": analysis["estimated_hours"],
                "required_skills": [skill.value for skill in analysis["required_skills"]]
            }
        )
        
        # Make hiring decision
        hiring_decision = await self._make_hiring_decision(project, analysis)
        self.hiring_decisions.append(hiring_decision)
        
        # Execute hiring
        hired_agents = await self._execute_hiring_plan(project, hiring_decision)
        
        # Assign tasks to hired agents
        await self._assign_initial_tasks(project, hired_agents)
        
        # Update project status
        project.status = "in_progress"
        project.assigned_agents = [agent.id for agent in hired_agents]
        project.updated_at = datetime.utcnow()
        
        # Notify project channels about progress
        await self._notify_project_progress(project, hired_agents)
        
        # Return CEO response
        response = {
            "project_id": project_id,
            "ceo_analysis": {
                "complexity": analysis["complexity"].value,
                "estimated_hours": analysis["estimated_hours"],
                "required_skills": [skill.value for skill in analysis["required_skills"]],
                "estimated_budget": hiring_decision.estimated_budget,
                "timeline_days": hiring_decision.timeline_days
            },
            "hiring_decision": {
                "roles_hired": [role.value for role in hiring_decision.required_roles],
                "reasoning": hiring_decision.reasoning,
                "team_size": len(hiring_decision.required_roles)
            },
            "hired_agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "status": agent.status.value
                }
                for agent in hired_agents
            ],
            "next_steps": self._generate_next_steps(project, hired_agents),
            "status": "team_assembled"
        }
        
        # Update conversation context for continuity
        self.conversation_context[user_id] = {
            "last_project_id": project_id,
            "last_interaction": "project_started",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
    
    async def _create_project_workspace(self, project_id: str, project_name: str) -> bool:
        """Create a project workspace for the new project"""
        try:
            # Use the project workspace manager to create workspace
            workspace_project_id = await project_workspace_manager.create_project(
                project_name=project_name,
                git_repo_url=None  # Will initialize empty repo
            )
            
            logger.log_system_event("ceo_created_project_workspace", {
                "project_id": project_id,
                "workspace_project_id": workspace_project_id,
                "project_name": project_name
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_project_workspace",
                "project_id": project_id,
                "project_name": project_name
            })
            return False
    
    async def _create_project_channels(self, project_id: str, project_name: str, created_by: str) -> List[str]:
        """Create all project communication channels"""
        try:
            # Create structured channels for the project
            channels = await self.project_channel_manager.create_project_channels(
                project_id=project_id,
                project_name=project_name,
                created_by=created_by,
                initial_participants=[created_by]  # CEO is initial participant
            )
            
            # Send announcement to general channel about project creation
            general_channel = await self.project_channel_manager.get_channel_by_type(
                project_id, 
                self.project_channel_manager.ChannelType.GENERAL
            )
            
            if general_channel:
                await self.project_channel_manager.send_channel_message(
                    channel_id=general_channel.id,
                    sender_id="ceo-001",
                    sender_name="ARTAC CEO",
                    sender_type="agent",
                    content=f"🎯 **Project '{project_name}' has been initiated!**\n\nI'll be assembling the perfect team for this project. Stay tuned for updates as we bring the best agents on board.",
                    message_type="announcement"
                )
            
            logger.log_system_event("ceo_created_project_channels", {
                "project_id": project_id,
                "project_name": project_name,
                "channels_created": len(channels),
                "channel_types": [ch.split("_")[-2] for ch in channels]  # Extract channel types
            })
            
            return channels
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_project_channels",
                "project_id": project_id,
                "project_name": project_name
            })
            return []
    
    async def _notify_project_progress(self, project: Project, hired_agents: List[Any]):
        """Send updates to project channels about progress"""
        try:
            # Get announcements channel
            announcements_channel = await self.project_channel_manager.get_channel_by_type(
                project.id,
                self.project_channel_manager.ChannelType.ANNOUNCEMENTS
            )
            
            if announcements_channel:
                # Create hiring announcement
                agent_list = "\n".join([f"• **{agent.name}** ({agent.role.value})" for agent in hired_agents])
                
                await self.project_channel_manager.send_channel_message(
                    channel_id=announcements_channel.id,
                    sender_id="ceo-001",
                    sender_name="ARTAC CEO",
                    sender_type="agent",
                    content=f"📋 **Team Assembly Complete for '{project.title}'**\n\n**Hired Agents:**\n{agent_list}\n\n**Project Complexity:** {project.complexity.value.title()}\n**Estimated Timeline:** {len(hired_agents)} agents × {project.estimated_hours // len(hired_agents)} hours each\n\nLet's build something amazing! 🚀",
                    message_type="announcement"
                )
            
            # Get agent updates channel for detailed assignments
            agent_updates_channel = await self.project_channel_manager.get_channel_by_type(
                project.id,
                self.project_channel_manager.ChannelType.AGENT_UPDATES
            )
            
            if agent_updates_channel:
                for agent in hired_agents:
                    await self.project_channel_manager.send_channel_message(
                        channel_id=agent_updates_channel.id,
                        sender_id="ceo-001",
                        sender_name="ARTAC CEO",
                        sender_type="agent",
                        content=f"🤖 **Agent {agent.name} assigned to project**\n\n**Role:** {agent.role.value}\n**Status:** {agent.status.value}\n**Assignment:** Initial project analysis and task breakdown",
                        message_type="agent_assignment",
                        metadata={
                            "agent_id": agent.id,
                            "agent_role": agent.role.value,
                            "assignment_type": "project_initialization"
                        }
                    )
            
        except Exception as e:
            logger.log_error(e, {
                "action": "notify_project_progress",
                "project_id": project.id
            })
    
    async def _analyze_project_requirements(self, title: str, description: str) -> Dict[str, Any]:
        """Analyze project to determine complexity and requirements"""
        
        # Simple keyword-based analysis (could be enhanced with LLM)
        text = (title + " " + description).lower()
        
        # Determine complexity
        complexity_indicators = {
            ProjectComplexity.SIMPLE: ["simple", "basic", "calculator", "todo", "small"],
            ProjectComplexity.MODERATE: ["website", "api", "database", "user", "auth"],
            ProjectComplexity.COMPLEX: ["enterprise", "microservices", "cloud", "scale", "system"],
            ProjectComplexity.ENTERPRISE: ["distributed", "architecture", "scalable", "high-availability"]
        }
        
        complexity = ProjectComplexity.SIMPLE
        max_score = 0
        
        for comp, keywords in complexity_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > max_score:
                max_score = score
                complexity = comp
        
        # Determine required skills
        skill_keywords = {
            AgentSkill.BACKEND: ["api", "server", "database", "backend"],
            AgentSkill.FRONTEND: ["ui", "frontend", "react", "html", "css"],
            AgentSkill.FULLSTACK: ["fullstack", "full-stack", "web app", "website"],
            AgentSkill.TESTING: ["test", "quality", "qa", "testing"],
            AgentSkill.DEVOPS: ["deploy", "cloud", "docker", "infrastructure"],
            AgentSkill.DOCUMENTATION: ["docs", "documentation", "manual"]
        }
        
        required_skills = []
        for skill, keywords in skill_keywords.items():
            if any(keyword in text for keyword in keywords):
                required_skills.append(skill)
        
        # Default skills for common projects
        if not required_skills:
            if "calculator" in text or "simple" in text:
                required_skills = [AgentSkill.BACKEND, AgentSkill.TESTING]
            else:
                required_skills = [AgentSkill.FULLSTACK, AgentSkill.TESTING]
        
        # Estimate hours based on complexity
        hour_estimates = {
            ProjectComplexity.SIMPLE: 16,
            ProjectComplexity.MODERATE: 40,
            ProjectComplexity.COMPLEX: 120,
            ProjectComplexity.ENTERPRISE: 320
        }
        
        return {
            "complexity": complexity,
            "required_skills": required_skills,
            "estimated_hours": hour_estimates[complexity]
        }
    
    async def _make_hiring_decision(self, project: Project, analysis: Dict[str, Any]) -> HiringDecision:
        """Make strategic hiring decision based on project analysis"""
        
        # Determine required roles based on skills and complexity
        role_mapping = {
            AgentSkill.BACKEND: AgentRole.DEVELOPER,
            AgentSkill.FRONTEND: AgentRole.DEVELOPER,
            AgentSkill.FULLSTACK: AgentRole.DEVELOPER,
            AgentSkill.TESTING: AgentRole.QA_ENGINEER,
            AgentSkill.DEVOPS: AgentRole.DEVOPS,
            AgentSkill.DOCUMENTATION: AgentRole.DEVELOPER
        }
        
        required_roles = []
        for skill in project.required_skills:
            role = role_mapping.get(skill, AgentRole.DEVELOPER)
            if role not in required_roles:
                required_roles.append(role)
        
        # Add senior oversight for complex projects
        if project.complexity in [ProjectComplexity.COMPLEX, ProjectComplexity.ENTERPRISE]:
            if AgentRole.SENIOR_DEVELOPER not in required_roles:
                required_roles.append(AgentRole.SENIOR_DEVELOPER)
        
        # Ensure minimum team size
        min_size = self.preferred_team_sizes[project.complexity]
        while len(required_roles) < min_size:
            if AgentRole.DEVELOPER not in required_roles:
                required_roles.append(AgentRole.DEVELOPER)
            elif AgentRole.QA_ENGINEER not in required_roles:
                required_roles.append(AgentRole.QA_ENGINEER)
            else:
                break
        
        # Calculate budget and timeline
        role_costs = {
            AgentRole.SENIOR_DEVELOPER: 120,  # per hour
            AgentRole.DEVELOPER: 80,
            AgentRole.QA_ENGINEER: 70,
            AgentRole.DEVOPS: 100,
            AgentRole.ARCHITECT: 150
        }
        
        estimated_budget = sum(
            role_costs.get(role, 80) * (project.estimated_hours / len(required_roles))
            for role in required_roles
        )
        
        timeline_days = max(5, project.estimated_hours // (len(required_roles) * 8))
        
        # CEO reasoning
        reasoning = f"""
        Project Analysis: {project.complexity.value.title()} project requiring {project.estimated_hours} hours.
        
        Team Strategy: Assembling {len(required_roles)} specialists with complementary skills.
        
        Roles: {', '.join(role.value.replace('_', ' ').title() for role in required_roles)}
        
        This team composition ensures quality delivery while maintaining cost efficiency.
        Timeline allows for proper development, testing, and deployment phases.
        """.strip()
        
        return HiringDecision(
            project_id=project.id,
            required_roles=required_roles,
            reasoning=reasoning,
            estimated_budget=estimated_budget,
            timeline_days=timeline_days,
            created_at=datetime.utcnow()
        )
    
    async def _execute_hiring_plan(self, project: Project, hiring_decision: HiringDecision) -> List:
        """Execute the hiring plan by creating real agents"""
        
        hired_agents = []
        
        for role in hiring_decision.required_roles:
            try:
                # Map skills based on role
                role_skills = {
                    AgentRole.DEVELOPER: [AgentSkill.BACKEND, AgentSkill.FRONTEND],
                    AgentRole.SENIOR_DEVELOPER: [AgentSkill.BACKEND, AgentSkill.ARCHITECTURE],
                    AgentRole.QA_ENGINEER: [AgentSkill.TESTING],
                    AgentRole.DEVOPS: [AgentSkill.DEVOPS],
                    AgentRole.ARCHITECT: [AgentSkill.ARCHITECTURE]
                }
                
                skills = role_skills.get(role, [AgentSkill.BACKEND])
                
                # Create agent with specific specializations for this project
                specialization = [
                    f"{project.complexity.value}_projects",
                    project.title.lower().replace(" ", "_")
                ]
                
                agent = await self.agent_manager.create_agent(
                    role=role,
                    skills=skills,
                    specialization=specialization,
                    auto_start=True
                )
                
                hired_agents.append(agent)
                
                # Log successful hire
                await interaction_logger.log_interaction(
                    project_id=project.id,
                    agent_id="ceo-001",
                    interaction_type=InteractionType.SYSTEM_EVENT,
                    action="agent_hired",
                    content=f"Successfully hired {agent.name} for project {project.title}",
                    context={
                        "hired_agent_id": agent.id,
                        "role": role.value,
                        "skills": [skill.value for skill in skills],
                        "specialization": specialization
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to hire {role.value} for project {project.id}: {e}")
                
                # Log hiring failure
                await interaction_logger.log_interaction(
                    project_id=project.id,
                    agent_id="ceo-001",
                    interaction_type=InteractionType.SYSTEM_EVENT,
                    action="hiring_failed",
                    content=f"Failed to hire {role.value}: {str(e)}",
                    context={"role": role.value, "error": str(e)}
                )
        
        return hired_agents
    
    async def _assign_initial_tasks(self, project: Project, hired_agents: List) -> None:
        """Create and assign initial tasks to hired agents"""
        
        # Create main project tasks based on complexity
        task_templates = {
            ProjectComplexity.SIMPLE: [
                "Setup project structure and dependencies",
                "Implement core functionality",
                "Add error handling and validation",
                "Create tests and documentation",
                "Final review and deployment preparation"
            ],
            ProjectComplexity.MODERATE: [
                "Project setup and architecture planning",
                "Backend API development",
                "Frontend implementation",
                "Database design and integration",
                "Testing and quality assurance",
                "Documentation and deployment"
            ]
        }
        
        tasks = task_templates.get(project.complexity, task_templates[ProjectComplexity.SIMPLE])
        
        for i, task_title in enumerate(tasks):
            try:
                # Create task using task hierarchy manager
                task_id = await task_hierarchy_manager.create_task(
                    project_id=project.id,
                    title=task_title,
                    description=f"Task for project: {project.title}",
                    task_type=TaskType.TASK,
                    created_by="ceo-001",
                    priority=TaskPriority.HIGH if i == 0 else TaskPriority.MEDIUM,
                    estimated_hours=project.estimated_hours // len(tasks)
                )
                
                # Auto-assign to appropriate agent
                assigned_agent_id = await task_hierarchy_manager.auto_assign_task(
                    task_id=task_id,
                    assigned_by="ceo-001",
                    algorithm="hierarchy_aware"
                )
                
                if assigned_agent_id:
                    logger.info(f"Assigned task '{task_title}' to agent {assigned_agent_id}")
                
            except Exception as e:
                logger.error(f"Failed to create/assign task '{task_title}': {e}")
    
    def _generate_next_steps(self, project: Project, hired_agents: List) -> List[str]:
        """Generate next steps for the project"""
        
        steps = [
            f"✅ Assembled team of {len(hired_agents)} specialists",
            f"🎯 Project scope: {project.complexity.value} complexity",
            f"⏱️ Estimated timeline: {project.estimated_hours} hours",
            "📋 Initial tasks assigned to team members",
            "🚀 Development phase initiated"
        ]
        
        if project.complexity in [ProjectComplexity.COMPLEX, ProjectComplexity.ENTERPRISE]:
            steps.append("👥 Senior oversight assigned for quality assurance")
        
        steps.extend([
            "📊 Progress monitoring activated",
            "🔄 Regular status updates will be provided",
            "📧 Client will be notified of major milestones"
        ])
        
        return steps
    
    async def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a project"""
        
        project = self.active_projects.get(project_id)
        if not project:
            return None
        
        # Get agent statuses
        agent_statuses = []
        for agent_id in project.assigned_agents:
            agent = await self.agent_manager.get_agent(agent_id)
            if agent:
                agent_statuses.append({
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "status": agent.status.value,
                    "active_tasks": len(agent.active_tasks)
                })
        
        return {
            "project": {
                "id": project.id,
                "title": project.title,
                "status": project.status,
                "complexity": project.complexity.value,
                "estimated_hours": project.estimated_hours
            },
            "team": agent_statuses,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    
    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Get conversation context for continuity"""
        return self.conversation_context.get(user_id, {})


# Global CEO service instance (will be initialized with agent_manager)
ceo_service: Optional[CEOService] = None


def initialize_ceo_service(agent_manager):
    """Initialize CEO service with agent manager"""
    global ceo_service
    ceo_service = CEOService(agent_manager)
    return ceo_service


def get_ceo_service() -> Optional[CEOService]:
    """Get the global CEO service instance"""
    return ceo_service