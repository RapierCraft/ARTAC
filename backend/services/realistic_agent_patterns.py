"""
ARTAC Realistic Agent Patterns
Extends agent behavior with asynchronous work patterns, availability, and human-like responses
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from core.logging import get_logger
from services.inter_agent_communication import InterAgentCommunicationService
from services.project_channel_manager import ProjectChannelManager
from services.agent_behavior import agent_behavior_service

logger = get_logger(__name__)


class WorkStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    IN_MEETING = "in_meeting"
    FOCUSED_WORK = "focused_work"
    BREAK = "break"
    OFFLINE = "offline"
    

class ResponsePattern(str, Enum):
    IMMEDIATE = "immediate"        # 0-2 minutes
    QUICK = "quick"               # 2-10 minutes
    NORMAL = "normal"             # 10-30 minutes
    DELAYED = "delayed"           # 30-120 minutes
    SLOW = "slow"                 # 2-6 hours
    NEXT_WORKDAY = "next_workday" # Next working period


class PersonalityType(str, Enum):
    PERFECTIONIST = "perfectionist"    # Takes time for quality
    RAPID_RESPONDER = "rapid_responder" # Quick responses
    DEEP_THINKER = "deep_thinker"      # Thoughtful, slower responses
    COLLABORATOR = "collaborator"       # Frequent communication
    FOCUSED_WORKER = "focused_worker"   # Long focused periods


@dataclass
class WorkSchedule:
    """Represents an agent's work schedule and patterns"""
    agent_id: str
    timezone: str
    work_start_hour: int  # 24-hour format
    work_end_hour: int
    break_times: List[Tuple[int, int]]  # (start_hour, duration_minutes)
    lunch_start: int  # hour
    lunch_duration: int  # minutes
    meeting_blocks: List[Tuple[datetime, datetime]]  # Scheduled meetings
    focus_blocks: List[Tuple[datetime, datetime]]    # Deep work periods
    preferred_response_times: Dict[str, ResponsePattern]  # message_type -> pattern
    productivity_curve: Dict[int, float]  # hour -> productivity (0.0-1.0)


@dataclass
class AgentAvailability:
    """Current availability status of an agent"""
    agent_id: str
    current_status: WorkStatus
    status_until: Optional[datetime]
    response_delay_minutes: int
    current_workload: float  # 0.0 to 1.0
    interruption_tolerance: float  # 0.0 to 1.0 - how easily interrupted
    last_activity: datetime
    estimated_free_time: Optional[datetime]
    current_focus_task: Optional[str]
    communication_preferences: Dict[str, Any]


@dataclass
class ResponseBehavior:
    """Defines how an agent responds to different types of communication"""
    agent_id: str
    personality_type: PersonalityType
    base_response_delay: ResponsePattern
    priority_modifiers: Dict[str, float]  # priority -> delay multiplier
    relationship_modifiers: Dict[str, float]  # agent_id -> delay multiplier
    message_type_modifiers: Dict[str, float]  # message_type -> delay multiplier
    workload_sensitivity: float  # How much workload affects response time
    meeting_participation_style: str  # active, moderate, observer
    communication_frequency: float  # How often they initiate communication


@dataclass
class WorkActivity:
    """Represents a work activity or task an agent is engaged in"""
    id: str
    agent_id: str
    activity_type: str  # coding, reviewing, meeting, planning, research
    title: str
    description: str
    estimated_duration: timedelta
    actual_start: datetime
    estimated_end: datetime
    actual_end: Optional[datetime]
    interruption_cost: int  # Minutes lost when interrupted
    focus_required: float  # 0.0 to 1.0 - how much focus is needed
    collaboration_level: str  # solo, pair, team
    status: str  # scheduled, in_progress, paused, completed, cancelled


class RealisticAgentPatterns:
    """Manages realistic agent behavior patterns and availability"""
    
    def __init__(
        self,
        inter_agent_comm: InterAgentCommunicationService,
        project_channel_manager: ProjectChannelManager
    ):
        self.inter_agent_comm = inter_agent_comm
        self.project_channel_manager = project_channel_manager
        
        # Core data structures
        self.agent_schedules: Dict[str, WorkSchedule] = {}
        self.agent_availability: Dict[str, AgentAvailability] = {}
        self.response_behaviors: Dict[str, ResponseBehavior] = {}
        self.active_activities: Dict[str, List[WorkActivity]] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        
        # Behavioral patterns
        self.personality_templates: Dict[PersonalityType, Dict[str, Any]] = {}
        self.role_behavior_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Initialize behavior patterns
        self._initialize_personality_templates()
        self._initialize_role_patterns()
        
        # Start background processes
        asyncio.create_task(self._manage_agent_availability())
        asyncio.create_task(self._process_delayed_messages())
        asyncio.create_task(self._simulate_work_activities())
    
    def _initialize_personality_templates(self):
        """Initialize personality-based behavior templates"""
        self.personality_templates = {
            PersonalityType.PERFECTIONIST: {
                "base_response_delay": ResponsePattern.NORMAL,
                "workload_sensitivity": 0.8,
                "interruption_tolerance": 0.3,
                "meeting_participation": "active",
                "communication_frequency": 0.6,
                "priority_modifiers": {
                    "urgent": 0.7,
                    "high": 0.8,
                    "normal": 1.0,
                    "low": 1.5
                },
                "message_type_modifiers": {
                    "code_review": 0.6,  # Faster for quality-related tasks
                    "bug_report": 0.5,
                    "general": 1.0,
                    "social": 1.3
                }
            },
            PersonalityType.RAPID_RESPONDER: {
                "base_response_delay": ResponsePattern.QUICK,
                "workload_sensitivity": 0.4,
                "interruption_tolerance": 0.8,
                "meeting_participation": "active",
                "communication_frequency": 0.9,
                "priority_modifiers": {
                    "urgent": 0.3,
                    "high": 0.5,
                    "normal": 1.0,
                    "low": 1.2
                },
                "message_type_modifiers": {
                    "urgent": 0.2,
                    "meeting_invitation": 0.4,
                    "general": 1.0,
                    "deep_technical": 1.4
                }
            },
            PersonalityType.DEEP_THINKER: {
                "base_response_delay": ResponsePattern.DELAYED,
                "workload_sensitivity": 0.9,
                "interruption_tolerance": 0.2,
                "meeting_participation": "moderate",
                "communication_frequency": 0.4,
                "priority_modifiers": {
                    "urgent": 0.6,
                    "high": 0.8,
                    "normal": 1.0,
                    "low": 1.0  # Takes same time regardless
                },
                "message_type_modifiers": {
                    "architecture_decision": 0.8,
                    "technical_discussion": 0.7,
                    "quick_question": 1.5,
                    "social": 2.0
                }
            },
            PersonalityType.COLLABORATOR: {
                "base_response_delay": ResponsePattern.NORMAL,
                "workload_sensitivity": 0.5,
                "interruption_tolerance": 0.7,
                "meeting_participation": "very_active",
                "communication_frequency": 1.0,
                "priority_modifiers": {
                    "urgent": 0.4,
                    "high": 0.7,
                    "normal": 1.0,
                    "low": 1.1
                },
                "message_type_modifiers": {
                    "collaboration_request": 0.3,
                    "team_discussion": 0.5,
                    "brainstorming": 0.4,
                    "solo_work": 1.3
                }
            },
            PersonalityType.FOCUSED_WORKER: {
                "base_response_delay": ResponsePattern.NORMAL,
                "workload_sensitivity": 0.7,
                "interruption_tolerance": 0.1,
                "meeting_participation": "moderate",
                "communication_frequency": 0.3,
                "priority_modifiers": {
                    "urgent": 0.8,  # Still slow to respond even to urgent
                    "high": 1.0,
                    "normal": 1.0,
                    "low": 1.0
                },
                "message_type_modifiers": {
                    "interruption": 2.0,
                    "quick_question": 1.8,
                    "end_of_day": 0.6,
                    "project_update": 0.8
                }
            }
        }
    
    def _initialize_role_patterns(self):
        """Initialize role-based behavior patterns"""
        self.role_behavior_patterns = {
            "ceo": {
                "work_hours": (8, 18),
                "typical_personality": PersonalityType.COLLABORATOR,
                "meeting_heavy": True,
                "response_priorities": ["urgent", "high", "strategic"],
                "focus_blocks": [(9, 11), (14, 16)],  # Morning and afternoon focus
                "communication_style": "strategic"
            },
            "cto": {
                "work_hours": (9, 19),
                "typical_personality": PersonalityType.DEEP_THINKER,
                "meeting_heavy": True,
                "response_priorities": ["technical", "architecture", "urgent"],
                "focus_blocks": [(10, 12), (15, 17)],
                "communication_style": "technical"
            },
            "senior_developer": {
                "work_hours": (9, 18),
                "typical_personality": PersonalityType.PERFECTIONIST,
                "meeting_heavy": False,
                "response_priorities": ["code_review", "technical", "mentoring"],
                "focus_blocks": [(9, 12), (14, 17)],  # Long morning and afternoon focus
                "communication_style": "detailed"
            },
            "developer": {
                "work_hours": (9, 17),
                "typical_personality": PersonalityType.FOCUSED_WORKER,
                "meeting_heavy": False,
                "response_priorities": ["task_assignment", "clarification", "help"],
                "focus_blocks": [(10, 12), (14, 16)],
                "communication_style": "direct"
            },
            "qa_engineer": {
                "work_hours": (9, 17),
                "typical_personality": PersonalityType.PERFECTIONIST,
                "meeting_heavy": False,
                "response_priorities": ["bug_report", "test_results", "quality"],
                "focus_blocks": [(9, 11), (14, 16)],
                "communication_style": "precise"
            },
            "project_manager": {
                "work_hours": (8, 17),
                "typical_personality": PersonalityType.RAPID_RESPONDER,
                "meeting_heavy": True,
                "response_priorities": ["urgent", "timeline", "coordination"],
                "focus_blocks": [(7, 9), (16, 17)],  # Early morning and end of day
                "communication_style": "coordinating"
            },
            "devops": {
                "work_hours": (8, 20),  # Longer hours for system monitoring
                "typical_personality": PersonalityType.RAPID_RESPONDER,
                "meeting_heavy": False,
                "response_priorities": ["system_alert", "deployment", "infrastructure"],
                "focus_blocks": [(9, 11), (14, 16)],
                "communication_style": "operational"
            },
            "architect": {
                "work_hours": (9, 18),
                "typical_personality": PersonalityType.DEEP_THINKER,
                "meeting_heavy": True,
                "response_priorities": ["architecture", "design", "technical_review"],
                "focus_blocks": [(10, 12), (15, 17)],
                "communication_style": "architectural"
            }
        }
    
    async def initialize_agent_realistic_patterns(
        self,
        agent_id: str,
        role: str,
        personality_override: Optional[PersonalityType] = None,
        custom_schedule: Optional[Dict[str, Any]] = None
    ):
        """Initialize realistic behavior patterns for a new agent"""
        try:
            role_pattern = self.role_behavior_patterns.get(role.lower(), self.role_behavior_patterns["developer"])
            personality = personality_override or role_pattern["typical_personality"]
            personality_template = self.personality_templates[personality]
            
            # Create work schedule
            work_start, work_end = role_pattern["work_hours"]
            schedule = WorkSchedule(
                agent_id=agent_id,
                timezone="UTC",  # Simplified for now
                work_start_hour=work_start,
                work_end_hour=work_end,
                break_times=[(10, 15), (15, 15)],  # Standard breaks
                lunch_start=12,
                lunch_duration=60,
                meeting_blocks=[],
                focus_blocks=[
                    (
                        datetime.now().replace(hour=block[0], minute=0, second=0, microsecond=0),
                        datetime.now().replace(hour=block[1], minute=0, second=0, microsecond=0)
                    )
                    for block in role_pattern["focus_blocks"]
                ],
                preferred_response_times={},
                productivity_curve=self._generate_productivity_curve(work_start, work_end)
            )
            
            # Create availability status
            availability = AgentAvailability(
                agent_id=agent_id,
                current_status=self._determine_current_status(schedule),
                status_until=None,
                response_delay_minutes=self._calculate_response_delay(personality_template["base_response_delay"]),
                current_workload=random.uniform(0.3, 0.7),
                interruption_tolerance=personality_template["interruption_tolerance"],
                last_activity=datetime.utcnow(),
                estimated_free_time=None,
                current_focus_task=None,
                communication_preferences={}
            )
            
            # Create response behavior
            response_behavior = ResponseBehavior(
                agent_id=agent_id,
                personality_type=personality,
                base_response_delay=personality_template["base_response_delay"],
                priority_modifiers=personality_template["priority_modifiers"],
                relationship_modifiers={},  # Will be learned over time
                message_type_modifiers=personality_template["message_type_modifiers"],
                workload_sensitivity=personality_template["workload_sensitivity"],
                meeting_participation_style=personality_template["meeting_participation"],
                communication_frequency=personality_template["communication_frequency"]
            )
            
            # Store all patterns
            self.agent_schedules[agent_id] = schedule
            self.agent_availability[agent_id] = availability
            self.response_behaviors[agent_id] = response_behavior
            self.active_activities[agent_id] = []
            self.message_queue[agent_id] = []
            
            logger.log_system_event("realistic_agent_patterns_initialized", {
                "agent_id": agent_id,
                "role": role,
                "personality": personality.value,
                "work_hours": f"{work_start}-{work_end}",
                "base_response_delay": personality_template["base_response_delay"].value
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initialize_agent_realistic_patterns",
                "agent_id": agent_id,
                "role": role
            })
    
    def _generate_productivity_curve(self, work_start: int, work_end: int) -> Dict[int, float]:
        """Generate a realistic productivity curve for work hours"""
        curve = {}
        work_hours = work_end - work_start
        
        for hour in range(24):
            if hour < work_start or hour > work_end:
                curve[hour] = 0.0  # Outside work hours
            else:
                # Relative hour within work day
                rel_hour = hour - work_start
                
                # Typical productivity curve: ramp up, peak, lunch dip, afternoon peak, decline
                if rel_hour <= 1:  # First hour - ramping up
                    curve[hour] = 0.6 + (rel_hour * 0.3)
                elif rel_hour <= 3:  # Morning peak
                    curve[hour] = 0.9 + random.uniform(-0.1, 0.1)
                elif rel_hour == 4:  # Pre-lunch
                    curve[hour] = 0.7
                elif rel_hour == 5:  # Lunch hour
                    curve[hour] = 0.3
                elif rel_hour <= 7:  # Post-lunch recovery and afternoon peak
                    curve[hour] = 0.8 + random.uniform(-0.1, 0.1)
                else:  # End of day decline
                    remaining_hours = work_hours - rel_hour
                    curve[hour] = max(0.4, 0.8 - ((rel_hour - 7) * 0.1))
        
        return curve
    
    def _determine_current_status(self, schedule: WorkSchedule) -> WorkStatus:
        """Determine current work status based on schedule and time"""
        current_hour = datetime.utcnow().hour
        
        # Check if within work hours
        if current_hour < schedule.work_start_hour or current_hour > schedule.work_end_hour:
            return WorkStatus.OFFLINE
        
        # Check for lunch
        if (current_hour >= schedule.lunch_start and 
            current_hour < schedule.lunch_start + (schedule.lunch_duration / 60)):
            return WorkStatus.BREAK
        
        # Check for breaks
        for break_start, break_duration in schedule.break_times:
            break_end = break_start + (break_duration / 60)
            if break_start <= current_hour < break_end:
                return WorkStatus.BREAK
        
        # Check for focus blocks
        current_time = datetime.utcnow()
        for focus_start, focus_end in schedule.focus_blocks:
            if focus_start <= current_time <= focus_end:
                return WorkStatus.FOCUSED_WORK
        
        # Default to available during work hours
        return WorkStatus.AVAILABLE
    
    def _calculate_response_delay(self, pattern: ResponsePattern) -> int:
        """Calculate actual response delay in minutes based on pattern"""
        base_delays = {
            ResponsePattern.IMMEDIATE: (0, 2),
            ResponsePattern.QUICK: (2, 10),
            ResponsePattern.NORMAL: (10, 30),
            ResponsePattern.DELAYED: (30, 120),
            ResponsePattern.SLOW: (120, 360),
            ResponsePattern.NEXT_WORKDAY: (480, 1440)  # 8-24 hours
        }
        
        min_delay, max_delay = base_delays[pattern]
        return random.randint(min_delay, max_delay)
    
    async def calculate_realistic_response_delay(
        self,
        agent_id: str,
        message_type: str = "general",
        priority: str = "normal",
        from_agent_id: Optional[str] = None
    ) -> int:
        """Calculate realistic response delay for a message"""
        try:
            if agent_id not in self.response_behaviors:
                return 15  # Default 15 minutes
            
            behavior = self.response_behaviors[agent_id]
            availability = self.agent_availability.get(agent_id)
            
            # Base delay from personality
            base_delay = self._calculate_response_delay(behavior.base_response_delay)
            
            # Apply priority modifier
            priority_modifier = behavior.priority_modifiers.get(priority, 1.0)
            base_delay = int(base_delay * priority_modifier)
            
            # Apply message type modifier
            message_type_modifier = behavior.message_type_modifiers.get(message_type, 1.0)
            base_delay = int(base_delay * message_type_modifier)
            
            # Apply relationship modifier if exists
            if from_agent_id and from_agent_id in behavior.relationship_modifiers:
                relationship_modifier = behavior.relationship_modifiers[from_agent_id]
                base_delay = int(base_delay * relationship_modifier)
            
            # Apply workload sensitivity
            if availability:
                workload_impact = availability.current_workload * behavior.workload_sensitivity
                base_delay = int(base_delay * (1 + workload_impact))
                
                # Apply current status impact
                status_multipliers = {
                    WorkStatus.AVAILABLE: 1.0,
                    WorkStatus.BUSY: 1.5,
                    WorkStatus.IN_MEETING: 3.0,
                    WorkStatus.FOCUSED_WORK: 4.0,
                    WorkStatus.BREAK: 0.8,
                    WorkStatus.OFFLINE: 8.0
                }
                status_multiplier = status_multipliers.get(availability.current_status, 1.0)
                base_delay = int(base_delay * status_multiplier)
            
            # Add some randomness to make it more natural
            randomness = random.uniform(0.8, 1.2)
            final_delay = max(1, int(base_delay * randomness))
            
            return final_delay
            
        except Exception as e:
            logger.log_error(e, {
                "action": "calculate_realistic_response_delay",
                "agent_id": agent_id,
                "message_type": message_type
            })
            return 15  # Safe default
    
    async def queue_delayed_message(
        self,
        agent_id: str,
        message_content: str,
        message_type: str,
        delay_minutes: int,
        metadata: Dict[str, Any] = None
    ):
        """Queue a message for delayed delivery"""
        try:
            if agent_id not in self.message_queue:
                self.message_queue[agent_id] = []
            
            send_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
            
            message_item = {
                "content": message_content,
                "message_type": message_type,
                "send_time": send_time,
                "metadata": metadata or {},
                "queued_at": datetime.utcnow()
            }
            
            self.message_queue[agent_id].append(message_item)
            
            logger.log_system_event("message_queued_for_delay", {
                "agent_id": agent_id,
                "delay_minutes": delay_minutes,
                "send_time": send_time.isoformat(),
                "message_type": message_type
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "queue_delayed_message",
                "agent_id": agent_id
            })
    
    async def simulate_work_activity(
        self,
        agent_id: str,
        activity_type: str,
        title: str,
        estimated_duration: timedelta,
        focus_required: float = 0.5
    ) -> str:
        """Simulate a work activity for an agent"""
        try:
            activity_id = f"activity_{uuid.uuid4().hex[:8]}"
            
            activity = WorkActivity(
                id=activity_id,
                agent_id=agent_id,
                activity_type=activity_type,
                title=title,
                description=f"Agent working on {title}",
                estimated_duration=estimated_duration,
                actual_start=datetime.utcnow(),
                estimated_end=datetime.utcnow() + estimated_duration,
                actual_end=None,
                interruption_cost=int(5 + (focus_required * 15)),  # 5-20 minutes
                focus_required=focus_required,
                collaboration_level="solo",
                status="in_progress"
            )
            
            # Add to active activities
            if agent_id not in self.active_activities:
                self.active_activities[agent_id] = []
            self.active_activities[agent_id].append(activity)
            
            # Update agent availability
            if agent_id in self.agent_availability:
                availability = self.agent_availability[agent_id]
                if focus_required > 0.7:
                    availability.current_status = WorkStatus.FOCUSED_WORK
                else:
                    availability.current_status = WorkStatus.BUSY
                availability.current_focus_task = title
                availability.estimated_free_time = activity.estimated_end
                availability.current_workload = min(1.0, availability.current_workload + 0.3)
            
            logger.log_system_event("work_activity_started", {
                "activity_id": activity_id,
                "agent_id": agent_id,
                "activity_type": activity_type,
                "duration_minutes": estimated_duration.total_seconds() / 60,
                "focus_required": focus_required
            })
            
            return activity_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "simulate_work_activity",
                "agent_id": agent_id
            })
            return ""
    
    # Background processes
    async def _manage_agent_availability(self):
        """Background process to update agent availability status"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for agent_id, availability in self.agent_availability.items():
                    schedule = self.agent_schedules.get(agent_id)
                    if not schedule:
                        continue
                    
                    # Update status based on schedule
                    new_status = self._determine_current_status(schedule)
                    
                    # Check if status should change due to time-based events
                    if availability.status_until and current_time >= availability.status_until:
                        availability.current_status = new_status
                        availability.status_until = None
                    
                    # Gradually reduce workload over time
                    if availability.current_workload > 0.1:
                        availability.current_workload = max(0.1, availability.current_workload - 0.05)
                    
                    # Update response delay based on current state
                    behavior = self.response_behaviors.get(agent_id)
                    if behavior:
                        availability.response_delay_minutes = await self.calculate_realistic_response_delay(
                            agent_id, "general", "normal"
                        )
                
                # Sleep for 5 minutes before next update
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.log_error(e, {"action": "manage_agent_availability"})
                await asyncio.sleep(300)
    
    async def _process_delayed_messages(self):
        """Background process to send delayed messages"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for agent_id, message_queue in self.message_queue.items():
                    # Process messages that are ready to send
                    ready_messages = [msg for msg in message_queue if msg["send_time"] <= current_time]
                    
                    for message in ready_messages:
                        # Send the message through existing behavior service
                        await self._send_delayed_message(agent_id, message)
                        message_queue.remove(message)
                
                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.log_error(e, {"action": "process_delayed_messages"})
                await asyncio.sleep(60)
    
    async def _simulate_work_activities(self):
        """Background process to simulate realistic work activities"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Check for completed activities
                for agent_id, activities in self.active_activities.items():
                    completed_activities = []
                    
                    for activity in activities:
                        if activity.status == "in_progress" and current_time >= activity.estimated_end:
                            # Complete the activity
                            activity.actual_end = current_time
                            activity.status = "completed"
                            completed_activities.append(activity)
                            
                            # Update agent availability
                            if agent_id in self.agent_availability:
                                availability = self.agent_availability[agent_id]
                                availability.current_status = WorkStatus.AVAILABLE
                                availability.current_focus_task = None
                                availability.current_workload = max(0.2, availability.current_workload - 0.2)
                                availability.estimated_free_time = None
                    
                    # Remove completed activities
                    for completed in completed_activities:
                        activities.remove(completed)
                        
                        logger.log_system_event("work_activity_completed", {
                            "activity_id": completed.id,
                            "agent_id": agent_id,
                            "activity_type": completed.activity_type,
                            "actual_duration": (completed.actual_end - completed.actual_start).total_seconds() / 60
                        })
                
                # Randomly start new activities for agents who are available
                for agent_id, availability in self.agent_availability.items():
                    if (availability.current_status == WorkStatus.AVAILABLE and 
                        availability.current_workload < 0.7 and
                        random.random() < 0.1):  # 10% chance every cycle
                        
                        # Start a random work activity
                        activity_types = ["coding", "reviewing", "research", "documentation", "planning"]
                        activity_type = random.choice(activity_types)
                        duration = timedelta(minutes=random.randint(30, 180))
                        focus_level = random.uniform(0.3, 0.9)
                        
                        await self.simulate_work_activity(
                            agent_id=agent_id,
                            activity_type=activity_type,
                            title=f"{activity_type.title()} Task",
                            estimated_duration=duration,
                            focus_required=focus_level
                        )
                
                # Sleep for 10 minutes before next simulation cycle
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.log_error(e, {"action": "simulate_work_activities"})
                await asyncio.sleep(600)
    
    async def _send_delayed_message(self, agent_id: str, message_data: Dict[str, Any]):
        """Send a delayed message through existing behavior service"""
        try:
            # Use the existing agent behavior service to send messages
            if hasattr(agent_behavior_service, 'send_proactive_message'):
                await agent_behavior_service.send_proactive_message(
                    agent_id=agent_id,
                    content=message_data["content"],
                    message_type=message_data["message_type"],
                    metadata=message_data["metadata"]
                )
            
            logger.log_system_event("delayed_message_sent", {
                "agent_id": agent_id,
                "message_type": message_data["message_type"],
                "delay_was": (datetime.utcnow() - message_data["queued_at"]).total_seconds() / 60
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "send_delayed_message",
                "agent_id": agent_id
            })
    
    # Public interface methods
    async def get_agent_availability(self, agent_id: str) -> Optional[AgentAvailability]:
        """Get current availability status for an agent"""
        return self.agent_availability.get(agent_id)
    
    async def get_estimated_response_time(self, agent_id: str, message_type: str = "general") -> int:
        """Get estimated response time in minutes"""
        return await self.calculate_realistic_response_delay(agent_id, message_type)
    
    async def is_agent_interruptible(self, agent_id: str) -> bool:
        """Check if an agent can be interrupted"""
        availability = self.agent_availability.get(agent_id)
        if not availability:
            return True
        
        if availability.current_status == WorkStatus.OFFLINE:
            return False
        
        if availability.current_status == WorkStatus.FOCUSED_WORK:
            return availability.interruption_tolerance > 0.5
        
        return True
    
    async def schedule_focus_time(self, agent_id: str, duration_minutes: int, task_description: str):
        """Schedule focused work time for an agent"""
        await self.simulate_work_activity(
            agent_id=agent_id,
            activity_type="focused_work",
            title=task_description,
            estimated_duration=timedelta(minutes=duration_minutes),
            focus_required=0.9
        )
    
    async def get_agent_work_schedule(self, agent_id: str) -> Optional[WorkSchedule]:
        """Get work schedule for an agent"""
        return self.agent_schedules.get(agent_id)
    
    async def update_agent_workload(self, agent_id: str, workload_delta: float):
        """Update an agent's current workload"""
        if agent_id in self.agent_availability:
            availability = self.agent_availability[agent_id]
            availability.current_workload = max(0.0, min(1.0, availability.current_workload + workload_delta))
            availability.last_activity = datetime.utcnow()


# Global instance
realistic_agent_patterns = None