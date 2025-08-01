"""
ARTAC Perpetual Efficiency Model
Replaces human-like work patterns with technical resource-based states for 24/7 AI operation
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger
from services.artac_assembly import ResourceState, ComputationalTask, TaskComplexity

logger = get_logger(__name__)


class AgentPersonalityProcess(str, Enum):
    """Process-based personality traits (not timing-based delays)"""
    PERFECTIONIST = "perfectionist"     # More validation checks, extensive documentation
    RAPID_EXECUTOR = "rapid_executor"   # Minimal overhead, fast execution
    THOROUGH_ANALYST = "thorough_analyst"  # Deep analysis, comprehensive reports
    COLLABORATIVE_OPTIMIZER = "collaborative_optimizer"  # Seeks input, builds consensus
    EFFICIENT_SPECIALIST = "efficient_specialist"  # Focused, streamlined approach


class ProcessingIntensity(str, Enum):
    """Computational intensity levels"""
    MINIMAL = "minimal"      # Simple text processing, acknowledgments
    LIGHT = "light"         # Basic analysis, simple queries
    MODERATE = "moderate"   # Code review, technical discussion
    HEAVY = "heavy"         # Complex analysis, architecture decisions
    INTENSIVE = "intensive" # Research, comprehensive reports, code generation


@dataclass
class AgentProcessProfile:
    """Process-based agent profile (not human-like delays)"""
    agent_id: str
    role: str
    personality_process: AgentPersonalityProcess
    base_processing_capacity: float  # 0.0 to 1.0 - agent's computational capacity
    specialization_areas: List[str]
    quality_standards: Dict[str, float]  # area -> quality threshold (0.0-1.0)
    validation_steps: Dict[str, List[str]]  # task_type -> validation checklist
    documentation_level: str  # minimal, standard, comprehensive
    collaboration_preference: float  # 0.0 to 1.0 - seeks input vs works independently


@dataclass
class ProcessingTask:
    """Technical processing task with measurable parameters"""
    id: str
    agent_id: str
    task_type: str
    description: str
    processing_intensity: ProcessingIntensity
    input_complexity: float  # 0.0 to 1.0
    output_requirements: Dict[str, Any]
    validation_required: bool
    collaboration_needed: bool
    started_at: datetime
    estimated_completion: datetime
    actual_completion: Optional[datetime]
    processing_steps: List[str]
    current_step: int
    step_progress: float  # 0.0 to 1.0 for current step
    can_be_interrupted: bool
    interruption_recovery_cost: int  # seconds to resume after interruption
    dependencies: List[str]  # Other task IDs this depends on


@dataclass
class AgentResourceMetrics:
    """Real-time resource metrics for agents"""
    agent_id: str
    current_state: ResourceState
    computational_load: float  # 0.0 to 1.0
    memory_usage: float  # 0.0 to 1.0 (simulated)
    context_size: int  # tokens in current context
    active_tasks: List[str]  # task IDs
    queued_tasks: List[str]  # task IDs waiting for resources
    processing_efficiency: float  # 0.0 to 1.0 - current efficiency level
    last_context_switch: datetime
    total_tasks_completed: int
    average_task_duration: float  # seconds
    specialization_bonus: Dict[str, float]  # area -> efficiency multiplier


class PerpetualEfficiencyModel:
    """Technical resource management replacing human-like work patterns"""
    
    def __init__(self):
        self.agent_profiles: Dict[str, AgentProcessProfile] = {}
        self.agent_metrics: Dict[str, AgentResourceMetrics] = {}
        self.active_processing_tasks: Dict[str, ProcessingTask] = {}
        self.task_queue: Dict[str, List[str]] = {}  # agent_id -> task_ids
        self.dependency_graph: Dict[str, List[str]] = {}  # task_id -> dependent_task_ids
        
        # Processing templates by task type
        self.processing_templates = self._initialize_processing_templates()
        
        # Background processes for continuous operation
        asyncio.create_task(self._manage_processing_resources())
        asyncio.create_task(self._optimize_task_scheduling())
        asyncio.create_task(self._update_efficiency_metrics())
    
    def _initialize_processing_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize processing templates for different task types"""
        return {
            "code_review": {
                "base_intensity": ProcessingIntensity.MODERATE,
                "steps": [
                    "Parse code structure",
                    "Analyze logic patterns", 
                    "Check style compliance",
                    "Identify potential issues",
                    "Generate recommendations",
                    "Create review summary"
                ],
                "validation_required": True,
                "estimated_duration": lambda complexity: 30 + (complexity * 120),  # 30s to 2.5min
                "quality_gates": ["syntax_check", "logic_validation", "security_scan"]
            },
            "architecture_analysis": {
                "base_intensity": ProcessingIntensity.HEAVY,
                "steps": [
                    "Analyze current architecture",
                    "Identify requirements",
                    "Evaluate constraints",
                    "Design alternatives",
                    "Compare trade-offs",
                    "Generate recommendations",
                    "Create documentation"
                ],
                "validation_required": True,
                "estimated_duration": lambda complexity: 180 + (complexity * 600),  # 3-13 minutes
                "quality_gates": ["feasibility_check", "scalability_validation", "cost_analysis"]
            },
            "bug_analysis": {
                "base_intensity": ProcessingIntensity.MODERATE,
                "steps": [
                    "Parse error information",
                    "Trace execution path",
                    "Identify root cause",
                    "Assess impact",
                    "Generate solution options",
                    "Recommend fix approach"
                ],
                "validation_required": True,
                "estimated_duration": lambda complexity: 45 + (complexity * 180),  # 45s to 3.5min
                "quality_gates": ["root_cause_validation", "solution_verification"]
            },
            "feature_implementation": {
                "base_intensity": ProcessingIntensity.HEAVY,
                "steps": [
                    "Analyze requirements",
                    "Design implementation approach",
                    "Generate code structure",
                    "Implement core logic",
                    "Add error handling",
                    "Create tests",
                    "Generate documentation"
                ],
                "validation_required": True,
                "estimated_duration": lambda complexity: 300 + (complexity * 1200),  # 5-25 minutes
                "quality_gates": ["requirements_validation", "code_quality_check", "test_coverage"]
            },
            "research_analysis": {
                "base_intensity": ProcessingIntensity.INTENSIVE,
                "steps": [
                    "Define research scope",
                    "Gather information sources",
                    "Analyze data patterns",
                    "Synthesize findings",
                    "Identify insights",
                    "Generate conclusions",
                    "Create comprehensive report"
                ],
                "validation_required": True,
                "estimated_duration": lambda complexity: 600 + (complexity * 1800),  # 10-40 minutes
                "quality_gates": ["source_validation", "analysis_verification", "conclusion_review"]
            },
            "simple_response": {
                "base_intensity": ProcessingIntensity.LIGHT,
                "steps": [
                    "Parse input",
                    "Generate response",
                    "Validate output"
                ],
                "validation_required": False,
                "estimated_duration": lambda complexity: 2 + (complexity * 15),  # 2-17 seconds
                "quality_gates": ["response_relevance"]
            }
        }
    
    async def initialize_agent_efficiency_profile(
        self,
        agent_id: str,
        role: str,
        specializations: List[str],
        processing_capacity: float = 1.0,
        personality_process: Optional[AgentPersonalityProcess] = None
    ):
        """Initialize efficiency-based agent profile"""
        try:
            # Determine personality process based on role if not specified
            if not personality_process:
                role_personalities = {
                    "ceo": AgentPersonalityProcess.COLLABORATIVE_OPTIMIZER,
                    "cto": AgentPersonalityProcess.THOROUGH_ANALYST,
                    "senior_developer": AgentPersonalityProcess.PERFECTIONIST,
                    "developer": AgentPersonalityProcess.EFFICIENT_SPECIALIST,
                    "qa_engineer": AgentPersonalityProcess.PERFECTIONIST,
                    "architect": AgentPersonalityProcess.THOROUGH_ANALYST,
                    "devops": AgentPersonalityProcess.RAPID_EXECUTOR,
                    "project_manager": AgentPersonalityProcess.COLLABORATIVE_OPTIMIZER
                }
                personality_process = role_personalities.get(role.lower(), AgentPersonalityProcess.EFFICIENT_SPECIALIST)
            
            # Create process profile
            profile = AgentProcessProfile(
                agent_id=agent_id,
                role=role,
                personality_process=personality_process,
                base_processing_capacity=processing_capacity,
                specialization_areas=specializations,
                quality_standards=self._generate_quality_standards(personality_process, role),
                validation_steps=self._generate_validation_steps(personality_process),
                documentation_level=self._determine_documentation_level(personality_process),
                collaboration_preference=self._calculate_collaboration_preference(personality_process)
            )
            
            # Create resource metrics
            metrics = AgentResourceMetrics(
                agent_id=agent_id,
                current_state=ResourceState.AVAILABLE,
                computational_load=0.0,
                memory_usage=0.0,
                context_size=0,
                active_tasks=[],
                queued_tasks=[],
                processing_efficiency=1.0,
                last_context_switch=datetime.utcnow(),
                total_tasks_completed=0,
                average_task_duration=0.0,
                specialization_bonus={spec: 1.2 for spec in specializations}  # 20% efficiency bonus
            )
            
            self.agent_profiles[agent_id] = profile
            self.agent_metrics[agent_id] = metrics
            self.task_queue[agent_id] = []
            
            logger.log_system_event("agent_efficiency_profile_initialized", {
                "agent_id": agent_id,
                "role": role,
                "personality_process": personality_process.value,
                "processing_capacity": processing_capacity,
                "specializations": specializations
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initialize_agent_efficiency_profile",
                "agent_id": agent_id
            })
    
    async def calculate_technical_response_time(
        self,
        agent_id: str,
        task_type: str,
        input_complexity: float,
        requires_collaboration: bool = False
    ) -> Tuple[int, str]:
        """Calculate response time based on technical processing requirements"""
        try:
            profile = self.agent_profiles.get(agent_id)
            metrics = self.agent_metrics.get(agent_id)
            
            if not profile or not metrics:
                return 15, "Agent profile not found"
            
            # Get processing template
            template = self.processing_templates.get(task_type, self.processing_templates["simple_response"])
            
            # Calculate base processing time
            base_duration = template["estimated_duration"](input_complexity)
            
            # Apply personality process modifiers
            personality_modifiers = {
                AgentPersonalityProcess.PERFECTIONIST: {
                    "time_multiplier": 1.4,  # More thorough processing
                    "reason": "additional validation and quality checks"
                },
                AgentPersonalityProcess.RAPID_EXECUTOR: {
                    "time_multiplier": 0.7,  # Streamlined processing
                    "reason": "optimized execution path"
                },
                AgentPersonalityProcess.THOROUGH_ANALYST: {
                    "time_multiplier": 1.6,  # Deep analysis
                    "reason": "comprehensive analysis and verification"
                },
                AgentPersonalityProcess.COLLABORATIVE_OPTIMIZER: {
                    "time_multiplier": 1.2,  # Additional consensus building
                    "reason": "collaboration and consensus building"
                },
                AgentPersonalityProcess.EFFICIENT_SPECIALIST: {
                    "time_multiplier": 0.9,  # Focused efficiency
                    "reason": "specialized expertise application"
                }
            }
            
            modifier = personality_modifiers.get(profile.personality_process, {"time_multiplier": 1.0, "reason": "standard processing"})
            adjusted_duration = base_duration * modifier["time_multiplier"]
            
            # Apply specialization bonus
            if any(spec in task_type for spec in profile.specialization_areas):
                specialization_bonus = max(metrics.specialization_bonus.values())
                adjusted_duration = adjusted_duration / specialization_bonus
                modifier["reason"] += " with specialization efficiency"
            
            # Apply current load factor
            load_factor = 1.0 + (metrics.computational_load * 0.5)  # Up to 50% slower when fully loaded
            final_duration = adjusted_duration * load_factor
            
            # Apply current state multiplier
            state_multipliers = {
                ResourceState.AVAILABLE: 1.0,
                ResourceState.EXCLUSIVE_COMPUTATION: 3.0,  # Can interrupt but with cost
                ResourceState.AWAITING_DEPENDENCY: 0.1,    # Very quick to respond when waiting
                ResourceState.CONTEXT_SWITCHING: 1.5       # Brief overhead
            }
            
            state_multiplier = state_multipliers.get(metrics.current_state, 1.0)
            final_duration = final_duration * state_multiplier
            
            # Add collaboration time if needed
            if requires_collaboration and profile.collaboration_preference > 0.7:
                final_duration += 30  # 30 seconds for coordination
                modifier["reason"] += " including collaboration coordination"
            
            # Round to reasonable precision
            response_time_seconds = max(1, int(final_duration))
            
            return response_time_seconds, modifier["reason"]
            
        except Exception as e:
            logger.log_error(e, {
                "action": "calculate_technical_response_time",
                "agent_id": agent_id,
                "task_type": task_type
            })
            return 30, "Error calculating response time"
    
    async def start_processing_task(
        self,
        agent_id: str,
        task_type: str,
        description: str,
        input_complexity: float,
        requires_validation: bool = True
    ) -> str:
        """Start a technical processing task"""
        try:
            task_id = f"proc_task_{uuid.uuid4().hex[:8]}"
            
            profile = self.agent_profiles.get(agent_id)
            metrics = self.agent_metrics.get(agent_id)
            
            if not profile or not metrics:
                return ""
            
            template = self.processing_templates.get(task_type, self.processing_templates["simple_response"])
            
            # Calculate processing parameters
            estimated_duration = template["estimated_duration"](input_complexity)
            estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_duration)
            
            # Create processing task
            task = ProcessingTask(
                id=task_id,
                agent_id=agent_id,
                task_type=task_type,
                description=description,
                processing_intensity=template["base_intensity"],
                input_complexity=input_complexity,
                output_requirements={"quality_level": profile.quality_standards.get(task_type, 0.8)},
                validation_required=requires_validation and template["validation_required"],
                collaboration_needed=profile.collaboration_preference > 0.7,
                started_at=datetime.utcnow(),
                estimated_completion=estimated_completion,
                actual_completion=None,
                processing_steps=template["steps"].copy(),
                current_step=0,
                step_progress=0.0,
                can_be_interrupted=template["base_intensity"] != ProcessingIntensity.INTENSIVE,
                interruption_recovery_cost=self._calculate_interruption_cost(template["base_intensity"]),
                dependencies=[]
            )
            
            self.active_processing_tasks[task_id] = task
            
            # Update agent metrics
            metrics.active_tasks.append(task_id)
            metrics.computational_load = min(1.0, metrics.computational_load + self._get_intensity_load(template["base_intensity"]))
            
            # Update state if necessary
            if metrics.computational_load > 0.8:
                metrics.current_state = ResourceState.EXCLUSIVE_COMPUTATION
            
            logger.log_system_event("processing_task_started", {
                "task_id": task_id,
                "agent_id": agent_id,
                "task_type": task_type,
                "intensity": template["base_intensity"].value,
                "estimated_duration_seconds": estimated_duration,
                "validation_required": task.validation_required
            })
            
            return task_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "start_processing_task",
                "agent_id": agent_id,
                "task_type": task_type
            })
            return ""
    
    def _generate_quality_standards(self, personality: AgentPersonalityProcess, role: str) -> Dict[str, float]:
        """Generate quality standards based on personality and role"""
        base_standards = {
            "code_review": 0.8,
            "architecture_analysis": 0.9,
            "bug_analysis": 0.85,
            "feature_implementation": 0.8,
            "research_analysis": 0.9,
            "documentation": 0.7
        }
        
        # Personality adjustments
        if personality == AgentPersonalityProcess.PERFECTIONIST:
            return {k: min(1.0, v + 0.1) for k, v in base_standards.items()}  # Higher standards
        elif personality == AgentPersonalityProcess.RAPID_EXECUTOR:
            return {k: max(0.6, v - 0.1) for k, v in base_standards.items()}  # Balanced with speed
        elif personality == AgentPersonalityProcess.THOROUGH_ANALYST:
            base_standards["research_analysis"] = min(1.0, base_standards["research_analysis"] + 0.1)
            base_standards["architecture_analysis"] = min(1.0, base_standards["architecture_analysis"] + 0.1)
        
        return base_standards
    
    def _generate_validation_steps(self, personality: AgentPersonalityProcess) -> Dict[str, List[str]]:
        """Generate validation steps based on personality"""
        base_steps = {
            "code_review": ["syntax_check", "logic_validation"],
            "architecture_analysis": ["feasibility_check", "scalability_validation"],
            "bug_analysis": ["root_cause_validation"],
            "feature_implementation": ["requirements_validation", "test_coverage"],
            "research_analysis": ["source_validation", "conclusion_review"]
        }
        
        if personality == AgentPersonalityProcess.PERFECTIONIST:
            # Add extra validation steps
            for task_type in base_steps:
                base_steps[task_type].append("quality_assurance_review")
        
        return base_steps
    
    def _determine_documentation_level(self, personality: AgentPersonalityProcess) -> str:
        """Determine documentation level based on personality"""
        doc_levels = {
            AgentPersonalityProcess.PERFECTIONIST: "comprehensive",
            AgentPersonalityProcess.RAPID_EXECUTOR: "minimal",
            AgentPersonalityProcess.THOROUGH_ANALYST: "comprehensive",
            AgentPersonalityProcess.COLLABORATIVE_OPTIMIZER: "standard",
            AgentPersonalityProcess.EFFICIENT_SPECIALIST: "standard"
        }
        return doc_levels.get(personality, "standard")
    
    def _calculate_collaboration_preference(self, personality: AgentPersonalityProcess) -> float:
        """Calculate collaboration preference score"""
        preferences = {
            AgentPersonalityProcess.PERFECTIONIST: 0.6,
            AgentPersonalityProcess.RAPID_EXECUTOR: 0.3,
            AgentPersonalityProcess.THOROUGH_ANALYST: 0.5,
            AgentPersonalityProcess.COLLABORATIVE_OPTIMIZER: 0.9,
            AgentPersonalityProcess.EFFICIENT_SPECIALIST: 0.4
        }
        return preferences.get(personality, 0.5)
    
    def _get_intensity_load(self, intensity: ProcessingIntensity) -> float:
        """Get computational load for processing intensity"""
        loads = {
            ProcessingIntensity.MINIMAL: 0.1,
            ProcessingIntensity.LIGHT: 0.2,
            ProcessingIntensity.MODERATE: 0.4,
            ProcessingIntensity.HEAVY: 0.7,
            ProcessingIntensity.INTENSIVE: 0.9
        }
        return loads.get(intensity, 0.3)
    
    def _calculate_interruption_cost(self, intensity: ProcessingIntensity) -> int:
        """Calculate cost of interrupting a processing task"""
        costs = {
            ProcessingIntensity.MINIMAL: 1,    # 1 second
            ProcessingIntensity.LIGHT: 3,     # 3 seconds
            ProcessingIntensity.MODERATE: 8,  # 8 seconds
            ProcessingIntensity.HEAVY: 20,    # 20 seconds
            ProcessingIntensity.INTENSIVE: 45 # 45 seconds
        }
        return costs.get(intensity, 10)
    
    # Background processes
    async def _manage_processing_resources(self):
        """Background process to manage processing resources"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Update task progress and complete finished tasks
                for task_id, task in list(self.active_processing_tasks.items()):
                    if current_time >= task.estimated_completion:
                        await self._complete_processing_task(task)
                    else:
                        # Update progress
                        elapsed = (current_time - task.started_at).total_seconds()
                        total_duration = (task.estimated_completion - task.started_at).total_seconds()
                        progress = min(1.0, elapsed / total_duration)
                        
                        # Update current step
                        steps_total = len(task.processing_steps)
                        current_step = min(steps_total - 1, int(progress * steps_total))
                        task.current_step = current_step
                        task.step_progress = (progress * steps_total) - current_step
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.log_error(e, {"action": "manage_processing_resources"})
                await asyncio.sleep(30)
    
    async def _optimize_task_scheduling(self):
        """Background process to optimize task scheduling"""
        while True:
            try:
                # Schedule queued tasks when agents become available
                for agent_id, queued_task_ids in self.task_queue.items():
                    metrics = self.agent_metrics.get(agent_id)
                    if metrics and metrics.current_state == ResourceState.AVAILABLE and queued_task_ids:
                        # Start next queued task
                        next_task_id = queued_task_ids.pop(0)
                        # Implementation would start the queued task
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.log_error(e, {"action": "optimize_task_scheduling"})
                await asyncio.sleep(60)
    
    async def _update_efficiency_metrics(self):
        """Background process to update efficiency metrics"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for agent_id, metrics in self.agent_metrics.items():
                    # Update processing efficiency based on recent performance
                    # This would analyze completed tasks and adjust efficiency
                    pass
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.log_error(e, {"action": "update_efficiency_metrics"})
                await asyncio.sleep(300)
    
    async def _complete_processing_task(self, task: ProcessingTask):
        """Complete a processing task and update metrics"""
        try:
            task.actual_completion = datetime.utcnow()
            task.step_progress = 1.0
            task.current_step = len(task.processing_steps) - 1
            
            # Update agent metrics
            metrics = self.agent_metrics.get(task.agent_id)
            if metrics:
                metrics.active_tasks.remove(task.id)
                metrics.computational_load = max(0.0, metrics.computational_load - self._get_intensity_load(task.processing_intensity))
                metrics.total_tasks_completed += 1
                
                # Update average task duration
                task_duration = (task.actual_completion - task.started_at).total_seconds()
                if metrics.average_task_duration == 0.0:
                    metrics.average_task_duration = task_duration
                else:
                    metrics.average_task_duration = (metrics.average_task_duration * 0.8) + (task_duration * 0.2)
                
                # Update state if no more intensive tasks
                if metrics.computational_load < 0.8:
                    metrics.current_state = ResourceState.AVAILABLE
            
            # Remove from active tasks
            del self.active_processing_tasks[task.id]
            
            logger.log_system_event("processing_task_completed", {
                "task_id": task.id,
                "agent_id": task.agent_id,
                "task_type": task.task_type,
                "actual_duration_seconds": task_duration,
                "steps_completed": len(task.processing_steps)
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "complete_processing_task",
                "task_id": task.id
            })
    
    # Public interface methods
    async def get_agent_processing_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current processing status for an agent"""
        metrics = self.agent_metrics.get(agent_id)
        profile = self.agent_profiles.get(agent_id)
        
        if not metrics or not profile:
            return None
        
        # Get current task details
        current_task_info = None
        if metrics.active_tasks:
            task_id = metrics.active_tasks[0]  # Primary active task
            task = self.active_processing_tasks.get(task_id)
            if task:
                current_task_info = {
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "current_step": task.processing_steps[task.current_step],
                    "progress": (task.current_step + task.step_progress) / len(task.processing_steps),
                    "estimated_completion": task.estimated_completion.isoformat(),
                    "can_be_interrupted": task.can_be_interrupted,
                    "interruption_cost_seconds": task.interruption_recovery_cost
                }
        
        return {
            "agent_id": agent_id,
            "current_state": metrics.current_state.value,
            "computational_load": metrics.computational_load,
            "processing_efficiency": metrics.processing_efficiency,
            "active_tasks_count": len(metrics.active_tasks),
            "queued_tasks_count": len(metrics.queued_tasks),
            "current_task": current_task_info,
            "specialization_areas": profile.specialization_areas,
            "personality_process": profile.personality_process.value,
            "tasks_completed": metrics.total_tasks_completed,
            "average_task_duration_seconds": metrics.average_task_duration
        }
    
    async def can_interrupt_agent(self, agent_id: str) -> Tuple[bool, int, str]:
        """Check if agent can be interrupted and at what cost"""
        metrics = self.agent_metrics.get(agent_id)
        
        if not metrics:
            return True, 0, "Agent not found"
        
        if metrics.current_state == ResourceState.AVAILABLE:
            return True, 0, "Agent is available"
        
        if metrics.current_state == ResourceState.AWAITING_DEPENDENCY:
            return True, 2, "Agent is waiting for dependency"
        
        if metrics.active_tasks:
            task_id = metrics.active_tasks[0]
            task = self.active_processing_tasks.get(task_id)
            if task:
                if not task.can_be_interrupted:
                    return False, 0, f"Cannot interrupt {task.task_type} in progress"
                else:
                    return True, task.interruption_recovery_cost, f"Can interrupt {task.task_type} with {task.interruption_recovery_cost}s recovery time"
        
        return True, 5, "Can interrupt with minimal cost"


# Global instance
perpetual_efficiency_model = PerpetualEfficiencyModel()