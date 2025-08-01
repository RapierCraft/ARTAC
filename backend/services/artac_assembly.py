"""
ARTAC Assembly Platform
Social-technical collaboration layer implementing the Perpetual Efficiency Model
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from core.logging import get_logger
from services.inter_agent_communication import InterAgentCommunicationService
from services.project_channel_manager import ProjectChannelManager, ChannelType
from services.collaborative_decision_system import CollaborativeDecisionSystem
from services.planning_meeting_system import PlanningMeetingSystem
from services.agent_behavior import agent_behavior_service

logger = get_logger(__name__)


class ResourceState(str, Enum):
    """Technical resource-based states for AI agents"""
    AVAILABLE = "available"                    # Ready for new tasks, low computational load
    EXCLUSIVE_COMPUTATION = "exclusive_computation"  # Resource-intensive task, can interrupt with cost
    AWAITING_DEPENDENCY = "awaiting_dependency"      # Paused waiting for dependency completion
    CONTEXT_SWITCHING = "context_switching"          # Brief period during task transitions


class TaskComplexity(str, Enum):
    """Task complexity levels determining response timing"""
    TRIVIAL = "trivial"        # 0-5 seconds (simple acknowledgments, status checks)
    SIMPLE = "simple"          # 5-15 seconds (basic questions, quick clarifications)
    MODERATE = "moderate"      # 15-45 seconds (technical discussions, code reviews)
    COMPLEX = "complex"        # 45-120 seconds (architectural decisions, analysis)
    INTENSIVE = "intensive"    # 2-10 minutes (deep research, comprehensive reports)


class CollaborationMode(str, Enum):
    """Different modes of agent collaboration"""
    BRAINSTORMING = "brainstorming"        # Open ideation, all voices welcome
    TECHNICAL_REVIEW = "technical_review"  # Structured code/design review
    DECISION_MAKING = "decision_making"    # Focused consensus building
    PROBLEM_SOLVING = "problem_solving"    # Collaborative debugging/analysis
    HANDOFF = "handoff"                   # Task completion and transfer


@dataclass
class ComputationalTask:
    """Represents a computational task an agent is performing"""
    id: str
    agent_id: str
    task_type: str  # compile, analyze, test, research, generate
    description: str
    estimated_duration: timedelta
    actual_start: datetime
    estimated_completion: datetime
    interruption_cost: int  # Minutes lost if interrupted
    progress_percentage: float  # 0.0 to 1.0
    can_pause: bool
    priority: str  # low, normal, high, urgent
    resource_usage: float  # 0.0 to 1.0 - computational intensity


@dataclass
class AgentResourceStatus:
    """Current resource status of an agent"""
    agent_id: str
    current_state: ResourceState
    state_reason: str
    state_until: Optional[datetime]
    current_task: Optional[ComputationalTask]
    queued_messages: List[str]
    computational_load: float  # 0.0 to 1.0
    available_capacity: float  # 0.0 to 1.0
    last_state_change: datetime


@dataclass
class AssemblySession:
    """Represents an active collaboration session"""
    id: str
    project_id: str
    channel_id: str
    mode: CollaborationMode
    participants: List[str]  # agent_ids
    facilitator: Optional[str]
    topic: str
    objective: str
    started_at: datetime
    estimated_duration: Optional[timedelta]
    current_phase: str
    decisions_made: List[str]  # decision_ids
    tasks_created: List[str]  # task_ids
    artifacts_generated: List[str]  # Links to generated content
    human_participants: List[str]  # Human observer/participant IDs
    session_state: str  # active, paused, completed, archived


@dataclass
class TaskComplexityAnalysis:
    """Analysis of message/task complexity for response timing"""
    message_id: str
    content: str
    complexity_level: TaskComplexity
    estimated_processing_time: int  # seconds
    requires_context_lookup: bool
    requires_analysis: bool
    requires_creativity: bool
    technical_depth: float  # 0.0 to 1.0
    analysis_confidence: float  # 0.0 to 1.0


class ARTACAssembly:
    """The ARTAC Assembly Platform - Social-technical collaboration layer"""
    
    def __init__(
        self,
        inter_agent_comm: InterAgentCommunicationService,
        project_channel_manager: ProjectChannelManager,
        collaborative_decisions: CollaborativeDecisionSystem,
        planning_meetings: PlanningMeetingSystem
    ):
        self.inter_agent_comm = inter_agent_comm
        self.project_channel_manager = project_channel_manager
        self.collaborative_decisions = collaborative_decisions
        self.planning_meetings = planning_meetings
        
        # Core data structures
        self.agent_resource_status: Dict[str, AgentResourceStatus] = {}
        self.active_sessions: Dict[str, AssemblySession] = {}
        self.computational_tasks: Dict[str, ComputationalTask] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        
        # Assembly intelligence
        self.complexity_analyzer = TaskComplexityAnalyzer()
        self.session_orchestrator = SessionOrchestrator(self)
        self.institutional_memory = InstitutionalMemory()
        
        # Background processes
        asyncio.create_task(self._manage_resource_states())
        asyncio.create_task(self._process_message_queue())
        asyncio.create_task(self._orchestrate_sessions())
    
    async def initialize_agent_assembly_profile(
        self,
        agent_id: str,
        role: str,
        capabilities: List[str],
        computational_capacity: float = 1.0
    ):
        """Initialize agent for Assembly participation"""
        try:
            status = AgentResourceStatus(
                agent_id=agent_id,
                current_state=ResourceState.AVAILABLE,
                state_reason="Initialized and ready",
                state_until=None,
                current_task=None,
                queued_messages=[],
                computational_load=0.0,
                available_capacity=computational_capacity,
                last_state_change=datetime.utcnow()
            )
            
            self.agent_resource_status[agent_id] = status
            self.message_queue[agent_id] = []
            
            logger.log_system_event("agent_assembly_profile_initialized", {
                "agent_id": agent_id,
                "role": role,
                "capabilities": capabilities,
                "computational_capacity": computational_capacity
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initialize_agent_assembly_profile",
                "agent_id": agent_id
            })
    
    async def initiate_project_genesis(
        self,
        human_directive: str,
        project_title: str,
        estimated_budget_hours: int,
        timeline_weeks: int,
        ceo_agent_id: str
    ) -> str:
        """Phase 1: Project Genesis - Human-to-CEO handoff"""
        try:
            project_id = f"project_{uuid.uuid4().hex[:8]}"
            
            # Create project channel
            channel = await self.project_channel_manager.create_channel(
                project_id=project_id,
                name=f"project-{project_title.lower().replace(' ', '-')}",
                channel_type=ChannelType.PROJECT,
                description=f"Assembly workspace for {project_title}",
                created_by="system"
            )
            
            # CEO processes directive and creates initial briefing
            briefing_content = f"""🎯 **PROJECT INITIATED: {project_title}**

**Human Directive:**
{human_directive}

**Resource Allocation:**
• Budget: {estimated_budget_hours} compute-hours
• Timeline: {timeline_weeks}-week sprint
• Priority: High

**Mission Parameters:**
I am assembling leadership to execute this directive. Technical lead will be appointed based on project requirements analysis.

**Next Actions:**
1. Technical requirements analysis
2. Squad formation and role assignment  
3. Architecture and approach definition
4. Execution roadmap creation

Leadership candidates, please review the directive and indicate your assessment of technical approach and resource requirements.

Execution begins immediately upon squad formation."""

            # Send CEO briefing to project channel
            message_id = await self.project_channel_manager.send_channel_message(
                channel_id=channel.id,
                sender_id=ceo_agent_id,
                sender_name="ARTAC CEO",
                sender_type="agent",
                content=briefing_content,
                message_type="project_genesis",
                metadata={
                    "project_id": project_id,
                    "human_directive": human_directive,
                    "budget_hours": estimated_budget_hours,
                    "timeline_weeks": timeline_weeks
                }
            )
            
            # Create assembly session for project kickoff
            session_id = await self.session_orchestrator.create_session(
                project_id=project_id,
                channel_id=channel.id,
                mode=CollaborationMode.BRAINSTORMING,
                topic="Project Genesis & Squad Formation",
                objective="Analyze requirements, form technical team, define approach",
                facilitator=ceo_agent_id,
                estimated_duration=timedelta(hours=2)
            )
            
            logger.log_system_event("project_genesis_initiated", {
                "project_id": project_id,
                "channel_id": channel.id,
                "session_id": session_id,
                "ceo_agent": ceo_agent_id,
                "budget_hours": estimated_budget_hours
            })
            
            return project_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initiate_project_genesis",
                "project_title": project_title
            })
            raise
    
    async def handle_message_with_complexity_analysis(
        self,
        channel_id: str,
        sender_id: str,
        content: str,
        message_type: str = "general"
    ) -> Dict[str, Any]:
        """Process message with complexity-based response timing"""
        try:
            # Analyze message complexity
            complexity_analysis = await self.complexity_analyzer.analyze_message_complexity(
                content=content,
                message_type=message_type,
                channel_context=await self._get_channel_context(channel_id)
            )
            
            # Determine which agents should respond
            responding_agents = await self._determine_responding_agents(
                channel_id=channel_id,
                sender_id=sender_id,
                complexity_analysis=complexity_analysis
            )
            
            responses = []
            
            for agent_id in responding_agents:
                agent_status = self.agent_resource_status.get(agent_id)
                if not agent_status:
                    continue
                
                # Calculate response timing based on complexity and agent state
                response_delay = await self._calculate_response_timing(
                    agent_id=agent_id,
                    complexity_analysis=complexity_analysis,
                    agent_status=agent_status
                )
                
                if response_delay > 0:
                    # Queue delayed response
                    await self._queue_delayed_response(
                        agent_id=agent_id,
                        channel_id=channel_id,
                        original_message=content,
                        complexity_analysis=complexity_analysis,
                        delay_seconds=response_delay
                    )
                    
                    # Send notification about agent state if delayed
                    if response_delay > 30:  # More than 30 seconds
                        await self._send_agent_state_notification(
                            channel_id=channel_id,
                            agent_id=agent_id,
                            agent_status=agent_status,
                            estimated_response_time=response_delay
                        )
                
                responses.append({
                    "agent_id": agent_id,
                    "estimated_response_seconds": response_delay,
                    "complexity_level": complexity_analysis.complexity_level.value
                })
            
            return {
                "complexity_analysis": asdict(complexity_analysis),
                "responding_agents": responses,
                "total_agents": len(responding_agents)
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "handle_message_with_complexity_analysis",
                "channel_id": channel_id,
                "sender_id": sender_id
            })
            return {"error": str(e)}
    
    async def execute_assembly_command(
        self,
        channel_id: str,
        sender_id: str,
        command: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Assembly platform commands (/decision, /task, etc.)"""
        try:
            if command == "decision":
                return await self._execute_decision_command(channel_id, sender_id, parameters)
            elif command == "task":
                return await self._execute_task_command(channel_id, sender_id, parameters)
            elif command == "session":
                return await self._execute_session_command(channel_id, sender_id, parameters)
            elif command == "analysis":
                return await self._execute_analysis_command(channel_id, sender_id, parameters)
            elif command == "handoff":
                return await self._execute_handoff_command(channel_id, sender_id, parameters)
            else:
                return {"error": f"Unknown command: {command}"}
                
        except Exception as e:
            logger.log_error(e, {
                "action": "execute_assembly_command",
                "command": command,
                "channel_id": channel_id
            })
            return {"error": str(e)}
    
    async def start_computational_task(
        self,
        agent_id: str,
        task_type: str,
        description: str,
        estimated_duration: timedelta,
        priority: str = "normal",
        can_pause: bool = True
    ) -> str:
        """Start a computational task that affects agent availability"""
        try:
            task_id = f"comp_task_{uuid.uuid4().hex[:8]}"
            
            task = ComputationalTask(
                id=task_id,
                agent_id=agent_id,
                task_type=task_type,
                description=description,
                estimated_duration=estimated_duration,
                actual_start=datetime.utcnow(),
                estimated_completion=datetime.utcnow() + estimated_duration,
                interruption_cost=self._calculate_interruption_cost(task_type, estimated_duration),
                progress_percentage=0.0,
                can_pause=can_pause,
                priority=priority,
                resource_usage=self._calculate_resource_usage(task_type)
            )
            
            self.computational_tasks[task_id] = task
            
            # Update agent status
            agent_status = self.agent_resource_status.get(agent_id)
            if agent_status:
                agent_status.current_state = ResourceState.EXCLUSIVE_COMPUTATION
                agent_status.state_reason = f"Executing {task_type}: {description}"
                agent_status.state_until = task.estimated_completion
                agent_status.current_task = task
                agent_status.computational_load = task.resource_usage
                agent_status.available_capacity = 1.0 - task.resource_usage
                agent_status.last_state_change = datetime.utcnow()
            
            logger.log_system_event("computational_task_started", {
                "task_id": task_id,
                "agent_id": agent_id,
                "task_type": task_type,
                "estimated_duration_minutes": estimated_duration.total_seconds() / 60,
                "resource_usage": task.resource_usage
            })
            
            return task_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "start_computational_task",
                "agent_id": agent_id,
                "task_type": task_type
            })
            return ""
    
    # Background process methods
    async def _manage_resource_states(self):
        """Background process to manage agent resource states"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for agent_id, status in self.agent_resource_status.items():
                    # Check if computational tasks are complete
                    if status.current_task:
                        task = status.current_task
                        if current_time >= task.estimated_completion:
                            await self._complete_computational_task(task)
                    
                    # Update state based on conditions
                    if (status.current_state == ResourceState.EXCLUSIVE_COMPUTATION and 
                        not status.current_task):
                        status.current_state = ResourceState.AVAILABLE
                        status.state_reason = "Computational task completed"
                        status.computational_load = 0.0
                        status.available_capacity = 1.0
                        status.last_state_change = current_time
                    
                    # Process queued messages if agent becomes available
                    if (status.current_state == ResourceState.AVAILABLE and 
                        status.queued_messages):
                        await self._process_agent_message_queue(agent_id)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.log_error(e, {"action": "manage_resource_states"})
                await asyncio.sleep(30)
    
    async def _process_message_queue(self):
        """Background process to handle delayed message delivery"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for agent_id, queue in self.message_queue.items():
                    ready_messages = [
                        msg for msg in queue 
                        if msg.get("send_time", current_time) <= current_time
                    ]
                    
                    for message in ready_messages:
                        await self._deliver_queued_message(agent_id, message)
                        queue.remove(message)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.log_error(e, {"action": "process_message_queue"})
                await asyncio.sleep(30)
    
    async def _orchestrate_sessions(self):
        """Background process to manage assembly sessions"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for session_id, session in self.active_sessions.items():
                    if session.session_state == "active":
                        # Check if session should transition phases or complete
                        await self.session_orchestrator.update_session_state(session)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.log_error(e, {"action": "orchestrate_sessions"})
                await asyncio.sleep(300)
    
    # Helper methods continue in next section...
    def _calculate_interruption_cost(self, task_type: str, duration: timedelta) -> int:
        """Calculate cost of interrupting a computational task"""
        base_costs = {
            "compile": 5,      # 5 minutes lost
            "analyze": 3,      # 3 minutes lost
            "test": 2,         # 2 minutes lost
            "research": 8,     # 8 minutes lost
            "generate": 4      # 4 minutes lost
        }
        
        base_cost = base_costs.get(task_type, 3)
        
        # Longer tasks have higher interruption costs
        duration_factor = min(2.0, duration.total_seconds() / 3600)  # Cap at 2x
        
        return int(base_cost * duration_factor)
    
    def _calculate_resource_usage(self, task_type: str) -> float:
        """Calculate computational resource usage for task type"""
        resource_usage = {
            "compile": 0.8,    # High CPU usage
            "analyze": 0.6,    # Moderate usage
            "test": 0.4,       # Low-moderate usage
            "research": 0.3,   # Low usage (mostly I/O)
            "generate": 0.7    # High usage for content generation
        }
        
        return resource_usage.get(task_type, 0.5)
    
    async def get_agent_resource_status(self, agent_id: str) -> Optional[AgentResourceStatus]:
        """Get current resource status for an agent"""
        return self.agent_resource_status.get(agent_id)
    
    async def get_assembly_overview(self, project_id: str) -> Dict[str, Any]:
        """Get overview of assembly activity for a project"""
        project_sessions = [
            session for session in self.active_sessions.values()
            if session.project_id == project_id
        ]
        
        return {
            "project_id": project_id,
            "active_sessions": len([s for s in project_sessions if s.session_state == "active"]),
            "total_sessions": len(project_sessions),
            "participating_agents": len(set(
                agent_id for session in project_sessions 
                for agent_id in session.participants
            )),
            "decisions_made": sum(len(s.decisions_made) for s in project_sessions),
            "tasks_created": sum(len(s.tasks_created) for s in project_sessions),
            "last_activity": max(
                (s.started_at for s in project_sessions), 
                default=datetime.utcnow()
            ).isoformat()
        }


class TaskComplexityAnalyzer:
    """Analyzes message/task complexity for response timing"""
    
    def __init__(self):
        self.complexity_indicators = {
            TaskComplexity.TRIVIAL: {
                "keywords": ["yes", "no", "ok", "thanks", "got it", "acknowledged"],
                "max_words": 10,
                "technical_terms": 0
            },
            TaskComplexity.SIMPLE: {
                "keywords": ["status", "update", "quick", "simple", "when"],
                "max_words": 50,
                "technical_terms": 2
            },
            TaskComplexity.MODERATE: {
                "keywords": ["review", "analyze", "implement", "design", "test"],
                "max_words": 200,
                "technical_terms": 10
            },
            TaskComplexity.COMPLEX: {
                "keywords": ["architecture", "strategy", "algorithm", "optimize", "refactor"],
                "max_words": 500,
                "technical_terms": 20
            },
            TaskComplexity.INTENSIVE: {
                "keywords": ["research", "investigate", "comprehensive", "detailed analysis"],
                "max_words": float('inf'),
                "technical_terms": float('inf')
            }
        }
    
    async def analyze_message_complexity(
        self,
        content: str,
        message_type: str,
        channel_context: Dict[str, Any]
    ) -> TaskComplexityAnalysis:
        """Analyze message complexity to determine processing time"""
        try:
            word_count = len(content.split())
            technical_terms = self._count_technical_terms(content)
            
            # Determine complexity level
            complexity_level = TaskComplexity.SIMPLE  # Default
            
            for level, indicators in self.complexity_indicators.items():
                if any(keyword in content.lower() for keyword in indicators["keywords"]):
                    if word_count <= indicators["max_words"] and technical_terms <= indicators["technical_terms"]:
                        complexity_level = level
                        break
            
            # Calculate processing time
            base_times = {
                TaskComplexity.TRIVIAL: (0, 5),
                TaskComplexity.SIMPLE: (5, 15),
                TaskComplexity.MODERATE: (15, 45),
                TaskComplexity.COMPLEX: (45, 120),
                TaskComplexity.INTENSIVE: (120, 600)
            }
            
            min_time, max_time = base_times[complexity_level]
            estimated_time = min_time + (max_time - min_time) * min(1.0, word_count / 100)
            
            return TaskComplexityAnalysis(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                content=content[:200],  # First 200 chars for reference
                complexity_level=complexity_level,
                estimated_processing_time=int(estimated_time),
                requires_context_lookup="context" in content.lower() or "previous" in content.lower(),
                requires_analysis="analyze" in content.lower() or "review" in content.lower(),
                requires_creativity="design" in content.lower() or "creative" in content.lower(),
                technical_depth=min(1.0, technical_terms / 10),
                analysis_confidence=0.8  # Fixed confidence for now
            )
            
        except Exception as e:
            logger.log_error(e, {"action": "analyze_message_complexity"})
            # Return default analysis
            return TaskComplexityAnalysis(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                content=content[:200],
                complexity_level=TaskComplexity.SIMPLE,
                estimated_processing_time=15,
                requires_context_lookup=False,
                requires_analysis=False,
                requires_creativity=False,
                technical_depth=0.3,
                analysis_confidence=0.5
            )
    
    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content"""
        technical_terms = [
            "api", "database", "frontend", "backend", "microservice", "docker", "kubernetes",
            "algorithm", "optimization", "performance", "scalability", "architecture",
            "authentication", "authorization", "encryption", "security", "vulnerability",
            "deployment", "ci/cd", "testing", "unit test", "integration", "framework",
            "library", "dependency", "version", "git", "branch", "merge", "commit"
        ]
        
        content_lower = content.lower()
        return sum(1 for term in technical_terms if term in content_lower)


class SessionOrchestrator:
    """Orchestrates assembly sessions and collaboration"""
    
    def __init__(self, assembly: 'ARTACAssembly'):
        self.assembly = assembly
    
    async def create_session(
        self,
        project_id: str,
        channel_id: str,
        mode: CollaborationMode,
        topic: str,
        objective: str,
        facilitator: Optional[str] = None,
        estimated_duration: Optional[timedelta] = None
    ) -> str:
        """Create a new assembly session"""
        try:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            session = AssemblySession(
                id=session_id,
                project_id=project_id,
                channel_id=channel_id,
                mode=mode,
                participants=[],
                facilitator=facilitator,
                topic=topic,
                objective=objective,
                started_at=datetime.utcnow(),
                estimated_duration=estimated_duration,
                current_phase="initialization",
                decisions_made=[],
                tasks_created=[],
                artifacts_generated=[],
                human_participants=[],
                session_state="active"
            )
            
            self.assembly.active_sessions[session_id] = session
            
            return session_id
            
        except Exception as e:
            logger.log_error(e, {"action": "create_session"})
            return ""
    
    async def update_session_state(self, session: AssemblySession):
        """Update session state and manage transitions"""
        try:
            current_time = datetime.utcnow()
            
            # Check if session should complete
            if (session.estimated_duration and 
                current_time >= session.started_at + session.estimated_duration):
                await self._complete_session(session)
                return
            
            # Update session phase based on activity
            # This is where we'd implement phase transitions
            # For now, keep sessions active
            
        except Exception as e:
            logger.log_error(e, {
                "action": "update_session_state",
                "session_id": session.id
            })
    
    async def _complete_session(self, session: AssemblySession):
        """Complete and archive a session"""
        session.session_state = "completed"
        
        # Archive session data to institutional memory
        await self.assembly.institutional_memory.archive_session(session)


class InstitutionalMemory:
    """Manages ARTAC's institutional memory and learning"""
    
    async def archive_session(self, session: AssemblySession):
        """Archive session data for future reference"""
        try:
            # This would integrate with the RAG system
            # For now, just log the session completion
            logger.log_system_event("session_archived", {
                "session_id": session.id,
                "project_id": session.project_id,
                "mode": session.mode.value,
                "duration_minutes": (datetime.utcnow() - session.started_at).total_seconds() / 60,
                "decisions_made": len(session.decisions_made),
                "tasks_created": len(session.tasks_created),
                "participants": len(session.participants)
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "archive_session",
                "session_id": session.id
            })


# Global instance
artac_assembly = None