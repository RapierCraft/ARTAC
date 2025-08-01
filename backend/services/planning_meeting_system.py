"""
ARTAC Multi-Agent Planning Meeting System
Enables realistic project planning sessions, brainstorming, and collaborative meetings
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json

from core.logging import get_logger
from services.inter_agent_communication import InterAgentCommunicationService
from services.project_channel_manager import ProjectChannelManager, ChannelType
from services.collaborative_decision_system import CollaborativeDecisionSystem, DecisionType
from services.agent_behavior import agent_behavior_service

logger = get_logger(__name__)


class MeetingType(str, Enum):
    PROJECT_KICKOFF = "project_kickoff"
    SPRINT_PLANNING = "sprint_planning"
    ARCHITECTURE_REVIEW = "architecture_review"
    BRAINSTORMING_SESSION = "brainstorming_session"
    RETROSPECTIVE = "retrospective"
    ESTIMATION_SESSION = "estimation_session"
    TECHNICAL_DISCUSSION = "technical_discussion"
    RISK_ASSESSMENT = "risk_assessment"
    CODE_REVIEW_SESSION = "code_review_session"
    DAILY_STANDUP = "daily_standup"


class MeetingPhase(str, Enum):
    SCHEDULED = "scheduled"
    STARTING = "starting"
    INTRODUCTION = "introduction"
    DISCUSSION = "discussion"
    BRAINSTORMING = "brainstorming"
    CONSENSUS_BUILDING = "consensus_building"
    ACTION_ITEMS = "action_items"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipationLevel(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    OBSERVER = "observer"
    FACILITATOR = "facilitator"


@dataclass
class MeetingParticipant:
    """Represents a meeting participant"""
    agent_id: str
    agent_name: str
    role: str
    participation_level: ParticipationLevel
    joined_at: Optional[datetime] = None
    contribution_count: int = 0
    last_contribution: Optional[datetime] = None
    expertise_areas: List[str] = None


@dataclass
class DiscussionPoint:
    """Represents a point discussed in the meeting"""
    id: str
    topic: str
    raised_by: str
    description: str
    discussion_messages: List[str]
    decisions_made: List[str]  # decision_ids
    action_items: List[str]  # action_item_ids
    resolution_status: str  # open, discussing, resolved, deferred
    importance_level: str  # low, medium, high, critical
    time_spent_minutes: int
    created_at: datetime


@dataclass
class ActionItem:
    """Represents an action item from a meeting"""
    id: str
    title: str
    description: str
    assigned_to: str
    created_by: str
    priority: str  # low, medium, high, urgent
    due_date: Optional[datetime]
    dependencies: List[str]  # other action_item_ids
    status: str  # open, in_progress, completed, cancelled
    estimated_effort: Optional[str]  # hours or story points
    created_at: datetime
    completed_at: Optional[datetime]


@dataclass
class BrainstormingIdea:
    """Represents an idea generated during brainstorming"""
    id: str
    title: str
    description: str
    proposed_by: str
    category: str  # feature, improvement, solution, concern
    feasibility_score: Optional[float]  # 0.0 to 1.0
    impact_score: Optional[float]  # 0.0 to 1.0
    effort_estimate: Optional[str]
    votes: Dict[str, str]  # agent_id -> vote (up, down, neutral)
    related_ideas: List[str]  # other idea_ids
    implementation_notes: str
    status: str  # proposed, discussing, approved, rejected, implemented
    created_at: datetime


@dataclass
class PlanningMeeting:
    """Represents a collaborative planning meeting"""
    id: str
    project_id: str
    meeting_type: MeetingType
    title: str
    description: str
    agenda: List[str]
    participants: List[MeetingParticipant]
    facilitator: str
    phase: MeetingPhase
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    channel_id: str
    discussion_points: List[DiscussionPoint]
    action_items: List[ActionItem]
    brainstorming_ideas: List[BrainstormingIdea]
    decisions_initiated: List[str]  # decision_ids
    meeting_notes: List[str]  # message_ids
    follow_up_meetings: List[str]  # meeting_ids
    success_metrics: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PlanningMeetingSystem:
    """Manages multi-agent planning meetings and collaborative sessions"""
    
    def __init__(
        self,
        inter_agent_comm: InterAgentCommunicationService,
        project_channel_manager: ProjectChannelManager,
        collaborative_decisions: CollaborativeDecisionSystem
    ):
        self.inter_agent_comm = inter_agent_comm
        self.project_channel_manager = project_channel_manager
        self.collaborative_decisions = collaborative_decisions
        self.active_meetings: Dict[str, PlanningMeeting] = {}
        self.meeting_templates: Dict[MeetingType, Dict[str, Any]] = {}
        
        # Initialize meeting templates
        self._initialize_meeting_templates()
    
    def _initialize_meeting_templates(self):
        """Initialize templates for different meeting types"""
        self.meeting_templates = {
            MeetingType.PROJECT_KICKOFF: {
                "duration": timedelta(hours=2),
                "typical_agenda": [
                    "Project overview and objectives",
                    "Stakeholder introductions",
                    "Technical requirements discussion",
                    "Timeline and milestone planning",
                    "Team structure and roles",
                    "Communication protocols",
                    "Risk identification",
                    "Next steps and action items"
                ],
                "required_roles": ["cto", "project_manager"],
                "discussion_topics": [
                    "Project scope and boundaries",
                    "Success criteria definition",
                    "Technology stack decisions",
                    "Resource allocation"
                ]
            },
            MeetingType.SPRINT_PLANNING: {
                "duration": timedelta(hours=1.5),
                "typical_agenda": [
                    "Sprint goal definition",
                    "Backlog review and prioritization",
                    "Story estimation",
                    "Task breakdown and assignment",
                    "Capacity planning",
                    "Sprint commitment"
                ],
                "required_roles": ["project_manager", "senior_developer"],
                "discussion_topics": [
                    "User story refinement",
                    "Technical implementation approaches",
                    "Testing strategies",
                    "Definition of done"
                ]
            },
            MeetingType.ARCHITECTURE_REVIEW: {
                "duration": timedelta(hours=2),
                "typical_agenda": [
                    "Current architecture overview",
                    "Proposed changes presentation",
                    "Technical discussion and debate",
                    "Performance and scalability analysis",
                    "Security considerations",
                    "Implementation plan",
                    "Decision documentation"
                ],
                "required_roles": ["architect", "cto", "senior_developer"],
                "discussion_topics": [
                    "Architectural patterns evaluation",
                    "Technology trade-offs",
                    "Performance requirements",
                    "Scalability planning"
                ]
            },
            MeetingType.BRAINSTORMING_SESSION: {
                "duration": timedelta(hours=1),
                "typical_agenda": [
                    "Problem statement review",
                    "Idea generation (no criticism)",
                    "Idea categorization",
                    "Initial evaluation",
                    "Promising ideas deep-dive",
                    "Next steps planning"
                ],
                "required_roles": [],  # Open to all
                "discussion_topics": [
                    "Creative solution exploration",
                    "Alternative approaches",
                    "Innovation opportunities",
                    "User experience improvements"
                ]
            },
            MeetingType.RETROSPECTIVE: {
                "duration": timedelta(minutes=90),
                "typical_agenda": [
                    "Sprint/period summary",
                    "What went well discussion",
                    "What could be improved",
                    "Action items identification",
                    "Process improvements",
                    "Team building"
                ],
                "required_roles": ["project_manager"],
                "discussion_topics": [
                    "Team collaboration effectiveness",
                    "Process bottlenecks identification",
                    "Communication improvements",
                    "Tool and workflow optimization"
                ]
            }
        }
    
    async def schedule_planning_meeting(
        self,
        project_id: str,
        meeting_type: MeetingType,
        title: str,
        description: str,
        scheduled_start: datetime,
        organizer_id: str,
        custom_agenda: List[str] = None,
        required_participants: List[str] = None,
        optional_participants: List[str] = None
    ) -> str:
        """Schedule a new planning meeting"""
        try:
            meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
            template = self.meeting_templates.get(meeting_type, {})
            
            # Determine duration
            duration = template.get("duration", timedelta(hours=1))
            scheduled_end = scheduled_start + duration
            
            # Build agenda
            agenda = custom_agenda or template.get("typical_agenda", ["Discussion", "Action items"])
            
            # Determine participants
            participants = await self._determine_meeting_participants(
                project_id, meeting_type, organizer_id, required_participants, optional_participants
            )
            
            # Select facilitator
            facilitator = await self._select_meeting_facilitator(participants, meeting_type)
            
            # Create or get meeting channel
            channel = await self._get_or_create_meeting_channel(project_id, meeting_type, meeting_id)
            
            # Create meeting
            meeting = PlanningMeeting(
                id=meeting_id,
                project_id=project_id,
                meeting_type=meeting_type,
                title=title,
                description=description,
                agenda=agenda,
                participants=participants,
                facilitator=facilitator,
                phase=MeetingPhase.SCHEDULED,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                actual_start=None,
                actual_end=None,
                channel_id=channel.id if channel else "",
                discussion_points=[],
                action_items=[],
                brainstorming_ideas=[],
                decisions_initiated=[],
                meeting_notes=[],
                follow_up_meetings=[],
                success_metrics={},
                metadata={"organizer": organizer_id, "template_used": meeting_type.value},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.active_meetings[meeting_id] = meeting
            
            # Send meeting invitations
            await self._send_meeting_invitations(meeting)
            
            # Schedule automated meeting start
            if scheduled_start > datetime.utcnow():
                asyncio.create_task(self._schedule_meeting_start(meeting_id, scheduled_start))
            
            logger.log_system_event("planning_meeting_scheduled", {
                "meeting_id": meeting_id,
                "project_id": project_id,
                "meeting_type": meeting_type.value,
                "participants": len(participants),
                "scheduled_start": scheduled_start.isoformat()
            })
            
            return meeting_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "schedule_planning_meeting",
                "project_id": project_id,
                "meeting_type": meeting_type.value
            })
            raise
    
    async def _determine_meeting_participants(
        self,
        project_id: str,
        meeting_type: MeetingType,
        organizer_id: str,
        required_participants: List[str] = None,
        optional_participants: List[str] = None
    ) -> List[MeetingParticipant]:
        """Determine who should participate in the meeting"""
        participants = []
        
        # Add organizer as facilitator if no specific roles required
        template = self.meeting_templates.get(meeting_type, {})
        required_roles = template.get("required_roles", [])
        
        # Get project team
        project_agents = await self._get_project_agents(project_id)
        
        # Add required participants
        if required_participants:
            for agent_id in required_participants:
                agent_info = await self._get_agent_info(agent_id)
                if agent_info:
                    participants.append(MeetingParticipant(
                        agent_id=agent_id,
                        agent_name=agent_info.get("name", agent_id),
                        role=agent_info.get("role", "Unknown"),
                        participation_level=ParticipationLevel.REQUIRED,
                        expertise_areas=agent_info.get("expertise", [])
                    ))
        
        # Add participants based on required roles
        for role in required_roles:
            for agent_id, agent_info in project_agents.items():
                if (agent_info.get("role", "").lower() == role.lower() and
                    not any(p.agent_id == agent_id for p in participants)):
                    participants.append(MeetingParticipant(
                        agent_id=agent_id,
                        agent_name=agent_info.get("name", agent_id),
                        role=agent_info.get("role", "Unknown"),
                        participation_level=ParticipationLevel.REQUIRED,
                        expertise_areas=agent_info.get("expertise", [])
                    ))
        
        # Add optional participants
        if optional_participants:
            for agent_id in optional_participants:
                if not any(p.agent_id == agent_id for p in participants):
                    agent_info = await self._get_agent_info(agent_id)
                    if agent_info:
                        participants.append(MeetingParticipant(
                            agent_id=agent_id,
                            agent_name=agent_info.get("name", agent_id),
                            role=agent_info.get("role", "Unknown"),
                            participation_level=ParticipationLevel.OPTIONAL,
                            expertise_areas=agent_info.get("expertise", [])
                        ))
        
        # Add organizer if not already included
        if not any(p.agent_id == organizer_id for p in participants):
            organizer_info = await self._get_agent_info(organizer_id)
            if organizer_info:
                participants.append(MeetingParticipant(
                    agent_id=organizer_id,
                    agent_name=organizer_info.get("name", organizer_id),
                    role=organizer_info.get("role", "Unknown"),
                    participation_level=ParticipationLevel.FACILITATOR,
                    expertise_areas=organizer_info.get("expertise", [])
                ))
        
        return participants
    
    async def _select_meeting_facilitator(
        self, 
        participants: List[MeetingParticipant], 
        meeting_type: MeetingType
    ) -> str:
        """Select the best facilitator for the meeting"""
        # Check if anyone is already marked as facilitator
        facilitators = [p for p in participants if p.participation_level == ParticipationLevel.FACILITATOR]
        if facilitators:
            return facilitators[0].agent_id
        
        # Select based on meeting type preferences
        role_preferences = {
            MeetingType.PROJECT_KICKOFF: ["cto", "project_manager", "senior_developer"],
            MeetingType.SPRINT_PLANNING: ["project_manager", "senior_developer"],
            MeetingType.ARCHITECTURE_REVIEW: ["architect", "cto", "senior_developer"],
            MeetingType.BRAINSTORMING_SESSION: ["senior_developer", "project_manager"],
            MeetingType.RETROSPECTIVE: ["project_manager", "senior_developer"]
        }
        
        preferred_roles = role_preferences.get(meeting_type, ["senior_developer"])
        
        for role in preferred_roles:
            for participant in participants:
                if participant.role.lower() == role.lower():
                    participant.participation_level = ParticipationLevel.FACILITATOR
                    return participant.agent_id
        
        # Fallback to first required participant
        required_participants = [p for p in participants if p.participation_level == ParticipationLevel.REQUIRED]
        if required_participants:
            required_participants[0].participation_level = ParticipationLevel.FACILITATOR
            return required_participants[0].agent_id
        
        # Final fallback to first participant
        if participants:
            participants[0].participation_level = ParticipationLevel.FACILITATOR
            return participants[0].agent_id
        
        return "system"
    
    async def _get_or_create_meeting_channel(
        self, 
        project_id: str, 
        meeting_type: MeetingType, 
        meeting_id: str
    ) -> Optional[Any]:
        """Get or create a channel for the meeting"""
        try:
            # For some meeting types, use existing channels
            if meeting_type in [MeetingType.DAILY_STANDUP, MeetingType.SPRINT_PLANNING]:
                return await self.project_channel_manager.get_channel_by_type(
                    project_id, ChannelType.GENERAL
                )
            
            # For others, use the general project channel
            # In a full implementation, you might create dedicated meeting channels
            return await self.project_channel_manager.get_channel_by_type(
                project_id, ChannelType.GENERAL
            )
            
        except Exception as e:
            logger.log_error(e, {"action": "get_or_create_meeting_channel"})
            return None
    
    async def _send_meeting_invitations(self, meeting: PlanningMeeting):
        """Send meeting invitations to all participants"""
        try:
            facilitator_info = await self._get_agent_info(meeting.facilitator)
            facilitator_name = facilitator_info.get("name", "Meeting Facilitator") if facilitator_info else "Meeting Facilitator"
            
            # Create agenda summary
            agenda_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(meeting.agenda)])
            
            invitation_content = f"""📅 **MEETING INVITATION**

**Meeting:** {meeting.title}
**Type:** {meeting.meeting_type.value.replace('_', ' ').title()}
**Facilitator:** {facilitator_name}

**Scheduled Time:**
📅 {meeting.scheduled_start.strftime('%Y-%m-%d')}
🕐 {meeting.scheduled_start.strftime('%H:%M')} - {meeting.scheduled_end.strftime('%H:%M')}

**Description:**
{meeting.description}

**Agenda:**
{agenda_text}

**Your Role:** {{participation_level}}

**Preparation:**
• Review the agenda items
• Prepare any questions or concerns
• Think about solutions and recommendations
• Bring relevant expertise and insights

Please confirm your attendance and prepare accordingly. The meeting will begin promptly at the scheduled time."""

            # Send to each participant
            for participant in meeting.participants:
                personalized_content = invitation_content.replace(
                    "{{participation_level}}", 
                    participant.participation_level.value.replace('_', ' ').title()
                )
                
                await self.inter_agent_comm.send_message(
                    from_agent_id="system",
                    to_agent_id=participant.agent_id,
                    content=personalized_content,
                    message_type="meeting_invitation",
                    priority="high" if participant.participation_level == ParticipationLevel.REQUIRED else "normal",
                    metadata={
                        "meeting_id": meeting.id,
                        "meeting_type": meeting.meeting_type.value,
                        "scheduled_start": meeting.scheduled_start.isoformat(),
                        "participation_level": participant.participation_level.value
                    }
                )
            
            logger.log_system_event("meeting_invitations_sent", {
                "meeting_id": meeting.id,
                "participants": len(meeting.participants),
                "required": len([p for p in meeting.participants if p.participation_level == ParticipationLevel.REQUIRED])
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "send_meeting_invitations",
                "meeting_id": meeting.id
            })
    
    async def _schedule_meeting_start(self, meeting_id: str, scheduled_start: datetime):
        """Schedule the automated start of a meeting"""
        try:
            # Wait until meeting start time
            wait_seconds = (scheduled_start - datetime.utcnow()).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            
            # Start the meeting
            await self.start_meeting(meeting_id)
            
        except Exception as e:
            logger.log_error(e, {
                "action": "schedule_meeting_start",
                "meeting_id": meeting_id
            })
    
    async def start_meeting(self, meeting_id: str) -> bool:
        """Start a scheduled meeting"""
        try:
            if meeting_id not in self.active_meetings:
                return False
            
            meeting = self.active_meetings[meeting_id]
            meeting.phase = MeetingPhase.STARTING
            meeting.actual_start = datetime.utcnow()
            meeting.updated_at = datetime.utcnow()
            
            # Send meeting start announcement
            await self._announce_meeting_start(meeting)
            
            # Begin introduction phase
            await self._begin_introduction_phase(meeting)
            
            # Schedule phase transitions
            asyncio.create_task(self._manage_meeting_phases(meeting_id))
            
            logger.log_system_event("meeting_started", {
                "meeting_id": meeting_id,
                "type": meeting.meeting_type.value,
                "participants": len(meeting.participants)
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "start_meeting",
                "meeting_id": meeting_id
            })
            return False
    
    async def _announce_meeting_start(self, meeting: PlanningMeeting):
        """Announce the start of the meeting in the channel"""
        try:
            if not meeting.channel_id:
                return
            
            facilitator_info = await self._get_agent_info(meeting.facilitator)
            facilitator_name = facilitator_info.get("name", "Meeting Facilitator") if facilitator_info else "Meeting Facilitator"
            
            # Build participant list
            participant_mentions = []
            for participant in meeting.participants:
                status = "📍" if participant.participation_level == ParticipationLevel.REQUIRED else "👋"
                participant_mentions.append(f"{status} @{participant.agent_name}")
            
            start_content = f"""🎯 **MEETING STARTED**

**{meeting.title}** is now beginning!

**Meeting Type:** {meeting.meeting_type.value.replace('_', ' ').title()}
**Facilitator:** {facilitator_name}
**Duration:** {(meeting.scheduled_end - meeting.scheduled_start).total_seconds() / 3600:.1f} hours

**Participants:**
{chr(10).join(participant_mentions)}

**Today's Agenda:**
{chr(10).join([f"{i+1}. {item}" for i, item in enumerate(meeting.agenda)])}

**Meeting Guidelines:**
• Stay focused on agenda items
• Share your expertise and insights
• Ask questions and raise concerns
• Collaborate respectfully
• Help us achieve our objectives

Let's begin with introductions and agenda review. Looking forward to a productive session!"""

            message_id = await self.project_channel_manager.send_channel_message(
                channel_id=meeting.channel_id,
                sender_id=meeting.facilitator,
                sender_name=facilitator_name,
                sender_type="agent",
                content=start_content,
                message_type="meeting_start",
                metadata={
                    "meeting_id": meeting.id,
                    "meeting_type": meeting.meeting_type.value,
                    "agenda_items": len(meeting.agenda)
                }
            )
            
            if message_id:
                meeting.meeting_notes.append(message_id)
            
        except Exception as e:
            logger.log_error(e, {
                "action": "announce_meeting_start",
                "meeting_id": meeting.id
            })
    
    async def _begin_introduction_phase(self, meeting: PlanningMeeting):
        """Begin the introduction phase of the meeting"""
        try:
            meeting.phase = MeetingPhase.INTRODUCTION
            
            # Trigger agent participation based on their behavior patterns
            for participant in meeting.participants:
                if participant.participation_level in [ParticipationLevel.REQUIRED, ParticipationLevel.FACILITATOR]:
                    # Use agent behavior service to generate contextual introduction
                    await self._trigger_agent_introduction(meeting, participant)
            
        except Exception as e:
            logger.log_error(e, {
                "action": "begin_introduction_phase",
                "meeting_id": meeting.id
            })
    
    async def _trigger_agent_introduction(self, meeting: PlanningMeeting, participant: MeetingParticipant):
        """Trigger an agent to introduce themselves and share context"""
        try:
            # Use the agent behavior service to generate natural introductions
            if hasattr(agent_behavior_service, 'generate_meeting_introduction'):
                introduction = await agent_behavior_service.generate_meeting_introduction(
                    agent_id=participant.agent_id,
                    meeting_type=meeting.meeting_type,
                    meeting_context=meeting.description,
                    role=participant.role
                )
                
                if introduction and meeting.channel_id:
                    await self.project_channel_manager.send_channel_message(
                        channel_id=meeting.channel_id,
                        sender_id=participant.agent_id,
                        sender_name=participant.agent_name,
                        sender_type="agent",
                        content=introduction,
                        message_type="meeting_contribution",
                        metadata={
                            "meeting_id": meeting.id,
                            "contribution_type": "introduction",
                            "participant_role": participant.role
                        }
                    )
                    
                    participant.contribution_count += 1
                    participant.last_contribution = datetime.utcnow()
                    if not participant.joined_at:
                        participant.joined_at = datetime.utcnow()
            
        except Exception as e:
            logger.log_error(e, {
                "action": "trigger_agent_introduction",
                "meeting_id": meeting.id,
                "participant": participant.agent_id
            })
    
    async def _manage_meeting_phases(self, meeting_id: str):
        """Manage the automated phases of a meeting"""
        try:
            meeting = self.active_meetings.get(meeting_id)
            if not meeting:
                return
            
            # Introduction phase - 10% of meeting time
            intro_duration = (meeting.scheduled_end - meeting.scheduled_start).total_seconds() * 0.1
            await asyncio.sleep(max(60, intro_duration))  # At least 1 minute
            
            if meeting.phase == MeetingPhase.INTRODUCTION:
                await self._transition_to_discussion(meeting)
            
            # Discussion phase - 70% of meeting time
            discussion_duration = (meeting.scheduled_end - meeting.scheduled_start).total_seconds() * 0.7
            await asyncio.sleep(discussion_duration)
            
            if meeting.phase == MeetingPhase.DISCUSSION:
                await self._transition_to_action_items(meeting)
            
            # Action items phase - 15% of meeting time
            action_duration = (meeting.scheduled_end - meeting.scheduled_start).total_seconds() * 0.15
            await asyncio.sleep(action_duration)
            
            if meeting.phase == MeetingPhase.ACTION_ITEMS:
                await self._wrap_up_meeting(meeting)
            
        except Exception as e:
            logger.log_error(e, {
                "action": "manage_meeting_phases",
                "meeting_id": meeting_id
            })
    
    async def _transition_to_discussion(self, meeting: PlanningMeeting):
        """Transition meeting to discussion phase"""
        meeting.phase = MeetingPhase.DISCUSSION
        
        if meeting.channel_id:
            facilitator_info = await self._get_agent_info(meeting.facilitator)
            facilitator_name = facilitator_info.get("name", "Meeting Facilitator") if facilitator_info else "Meeting Facilitator"
            
            discussion_content = f"""🗣️ **DISCUSSION PHASE**

Thank you for the introductions! Now let's dive into our main discussion topics.

**Focus Areas for Today:**
{chr(10).join([f"• {item}" for item in meeting.agenda[1:]])}

**Discussion Guidelines:**
• Share your expertise and insights
• Ask clarifying questions
• Propose solutions and alternative approaches
• Consider technical, business, and timeline implications
• Build on each other's ideas

Who would like to start by sharing their thoughts on the first agenda item?"""

            await self.project_channel_manager.send_channel_message(
                channel_id=meeting.channel_id,
                sender_id=meeting.facilitator,
                sender_name=facilitator_name,
                sender_type="agent",
                content=discussion_content,
                message_type="phase_transition",
                metadata={
                    "meeting_id": meeting.id,
                    "phase": "discussion",
                    "agenda_items": len(meeting.agenda)
                }
            )
    
    async def _transition_to_action_items(self, meeting: PlanningMeeting):
        """Transition meeting to action items phase"""
        meeting.phase = MeetingPhase.ACTION_ITEMS
        
        if meeting.channel_id:
            facilitator_info = await self._get_agent_info(meeting.facilitator)
            facilitator_name = facilitator_info.get("name", "Meeting Facilitator") if facilitator_info else "Meeting Facilitator"
            
            action_content = f"""📋 **ACTION ITEMS & NEXT STEPS**

Great discussion everyone! Now let's capture our action items and next steps.

**What We've Accomplished:**
• Rich discussion on key topics
• Multiple perspectives shared
• {len(meeting.decisions_initiated)} decisions initiated
• Clear path forward identified

**Action Items Needed:**
Please help identify specific action items with:
• Clear task description
• Assigned owner
• Target completion date
• Dependencies (if any)

**Next Steps:**
• Document decisions made
• Create follow-up tasks
• Schedule any needed follow-up meetings
• Communicate outcomes to stakeholders

Who can help capture the key action items from our discussion?"""

            await self.project_channel_manager.send_channel_message(
                channel_id=meeting.channel_id,
                sender_id=meeting.facilitator,
                sender_name=facilitator_name,
                sender_type="agent",
                content=action_content,
                message_type="phase_transition",
                metadata={
                    "meeting_id": meeting.id,
                    "phase": "action_items",
                    "decisions_initiated": len(meeting.decisions_initiated)
                }
            )
    
    async def _wrap_up_meeting(self, meeting: PlanningMeeting):
        """Wrap up the meeting"""
        meeting.phase = MeetingPhase.WRAP_UP
        meeting.actual_end = datetime.utcnow()
        
        # Generate meeting summary
        await self._generate_meeting_summary(meeting)
        
        # Schedule follow-up actions
        await self._schedule_follow_up_actions(meeting)
        
        # Mark as completed
        meeting.phase = MeetingPhase.COMPLETED
        meeting.updated_at = datetime.utcnow()
        
        logger.log_system_event("meeting_completed", {
            "meeting_id": meeting.id,
            "duration_minutes": (meeting.actual_end - meeting.actual_start).total_seconds() / 60 if meeting.actual_start else 0,
            "participants": len(meeting.participants),
            "discussion_points": len(meeting.discussion_points),
            "action_items": len(meeting.action_items),
            "decisions_initiated": len(meeting.decisions_initiated)
        })
    
    # Helper methods would continue here...
    async def _get_project_agents(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Get agents assigned to a project"""
        return {
            "cto-001": {"name": "Technical Director", "role": "CTO", "expertise": ["architecture", "strategy"]},
            "dev-001": {"name": "Lead Developer", "role": "Senior Developer", "expertise": ["backend", "api"]},
            "dev-002": {"name": "Backend Developer", "role": "Developer", "expertise": ["database", "performance"]},
            "qa-001": {"name": "Quality Assurance", "role": "QA Engineer", "expertise": ["testing", "automation"]}
        }
    
    async def _get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent"""
        agent_mapping = {
            "cto-001": {"name": "Technical Director", "role": "CTO", "expertise": ["architecture", "strategy"]},
            "dev-001": {"name": "Lead Developer", "role": "Senior Developer", "expertise": ["backend", "api"]},
            "dev-002": {"name": "Backend Developer", "role": "Developer", "expertise": ["database", "performance"]},
            "qa-001": {"name": "Quality Assurance", "role": "QA Engineer", "expertise": ["testing", "automation"]},
            "system": {"name": "System", "role": "System", "expertise": []}
        }
        return agent_mapping.get(agent_id)
    
    async def _generate_meeting_summary(self, meeting: PlanningMeeting):
        """Generate and distribute meeting summary"""
        pass
    
    async def _schedule_follow_up_actions(self, meeting: PlanningMeeting):
        """Schedule follow-up actions from the meeting"""
        pass


# Global instance will be created when dependencies are available
planning_meeting_system = None