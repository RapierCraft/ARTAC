"""
ARTAC Collaborative Decision-Making System
Enables realistic multi-agent consensus building, voting, and collaborative project planning
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
from services.organizational_hierarchy import organizational_hierarchy
from services.agent_behavior import agent_behavior_service
from models.organizational_hierarchy import Agent, AuthorityLevel

logger = get_logger(__name__)


class DecisionType(str, Enum):
    PROJECT_APPROACH = "project_approach"
    ARCHITECTURE_DECISION = "architecture_decision"
    TECHNOLOGY_STACK = "technology_stack"
    TIMELINE_ESTIMATION = "timeline_estimation"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_ASSESSMENT = "risk_assessment"
    FEATURE_PRIORITIZATION = "feature_prioritization"
    CODE_REVIEW_POLICY = "code_review_policy"
    DEPLOYMENT_STRATEGY = "deployment_strategy"
    BUDGET_APPROVAL = "budget_approval"


class DecisionStatus(str, Enum):
    PROPOSED = "proposed"
    DISCUSSING = "discussing"
    VOTING = "voting"
    CONSENSUS_REACHED = "consensus_reached"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTATION = "implementation"
    COMPLETED = "completed"


class VoteType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    CONDITIONAL = "conditional"  # Approve with conditions


@dataclass
class DecisionOption:
    """Represents an option in a decision"""
    id: str
    title: str
    description: str
    proposed_by: str
    pros: List[str]
    cons: List[str]
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    cost_estimate: Optional[float]
    timeline_impact: Optional[str]
    votes: Dict[str, VoteType]  # agent_id -> vote
    vote_reasoning: Dict[str, str]  # agent_id -> reasoning


@dataclass
class CollaborativeDecision:
    """Represents a collaborative decision process"""
    id: str
    project_id: str
    decision_type: DecisionType
    title: str
    description: str
    context: Dict[str, Any]
    options: List[DecisionOption]
    required_participants: List[str]  # agent_ids who must participate
    optional_participants: List[str]  # agent_ids who can participate
    minimum_consensus: float  # 0.0 to 1.0 - percentage needed for consensus
    authority_required: AuthorityLevel  # minimum authority level to approve
    initiated_by: str
    facilitator: Optional[str]  # agent leading the discussion
    status: DecisionStatus
    discussion_messages: List[str]  # message_ids in the discussion
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    decision_made_at: Optional[datetime]
    selected_option: Optional[str]  # option_id
    final_reasoning: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class PlanningSession:
    """Represents a collaborative planning session"""
    id: str
    project_id: str
    session_type: str  # sprint_planning, architecture_review, estimation, retrospective
    title: str
    agenda: List[str]
    participants: List[str]  # agent_ids
    facilitator: str
    status: str  # scheduled, in_progress, completed, cancelled
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    discussion_points: List[Dict[str, Any]]
    decisions_made: List[str]  # decision_ids
    action_items: List[Dict[str, Any]]
    meeting_notes: str
    follow_up_sessions: List[str]  # session_ids


class CollaborativeDecisionSystem:
    """Manages collaborative decision-making and planning processes"""
    
    def __init__(
        self, 
        inter_agent_comm: InterAgentCommunicationService,
        project_channel_manager: ProjectChannelManager
    ):
        self.inter_agent_comm = inter_agent_comm
        self.project_channel_manager = project_channel_manager
        self.active_decisions: Dict[str, CollaborativeDecision] = {}
        self.planning_sessions: Dict[str, PlanningSession] = {}
        self.decision_templates: Dict[DecisionType, Dict[str, Any]] = {}
        
        # Initialize decision templates
        self._initialize_decision_templates()
    
    def _initialize_decision_templates(self):
        """Initialize templates for different types of decisions"""
        self.decision_templates = {
            DecisionType.PROJECT_APPROACH: {
                "minimum_consensus": 0.75,
                "authority_required": AuthorityLevel.MIDDLE_MANAGEMENT,
                "typical_participants": ["cto", "senior_developer", "architect"],
                "discussion_duration": timedelta(hours=2),
                "common_options": [
                    "Agile/Scrum approach with 2-week sprints",
                    "Kanban continuous flow approach", 
                    "Waterfall with defined phases",
                    "Hybrid approach combining methodologies"
                ]
            },
            DecisionType.ARCHITECTURE_DECISION: {
                "minimum_consensus": 0.8,
                "authority_required": AuthorityLevel.SENIOR_MANAGEMENT,
                "typical_participants": ["cto", "architect", "senior_developer"],
                "discussion_duration": timedelta(hours=3),
                "common_options": [
                    "Microservices architecture",
                    "Monolithic architecture",
                    "Serverless architecture",
                    "Hybrid architecture"
                ]
            },
            DecisionType.TECHNOLOGY_STACK: {
                "minimum_consensus": 0.7,
                "authority_required": AuthorityLevel.MIDDLE_MANAGEMENT,
                "typical_participants": ["cto", "senior_developer", "developer", "devops"],
                "discussion_duration": timedelta(hours=1.5),
                "common_options": []  # Will be generated based on project context
            },
            DecisionType.TIMELINE_ESTIMATION: {
                "minimum_consensus": 0.6,
                "authority_required": AuthorityLevel.MIDDLE_MANAGEMENT,
                "typical_participants": ["project_manager", "senior_developer", "developer", "qa"],
                "discussion_duration": timedelta(hours=1),
                "common_options": []  # Will be generated based on project scope
            }
        }
    
    async def initiate_collaborative_decision(
        self,
        project_id: str,
        decision_type: DecisionType,
        title: str,
        description: str,
        initiated_by: str,
        context: Dict[str, Any] = None,
        custom_options: List[Dict[str, Any]] = None,
        deadline: Optional[datetime] = None
    ) -> str:
        """Initiate a collaborative decision-making process"""
        try:
            decision_id = f"decision_{uuid.uuid4().hex[:8]}"
            template = self.decision_templates.get(decision_type, {})
            
            # Determine participants based on decision type and project context
            participants = await self._determine_participants(
                project_id, decision_type, initiated_by
            )
            
            # Generate or use provided options
            if custom_options:
                options = [
                    DecisionOption(
                        id=f"opt_{uuid.uuid4().hex[:6]}",
                        title=opt["title"],
                        description=opt["description"],
                        proposed_by=opt.get("proposed_by", initiated_by),
                        pros=opt.get("pros", []),
                        cons=opt.get("cons", []),
                        implementation_effort=opt.get("implementation_effort", "medium"),
                        risk_level=opt.get("risk_level", "medium"),
                        cost_estimate=opt.get("cost_estimate"),
                        timeline_impact=opt.get("timeline_impact"),
                        votes={},
                        vote_reasoning={}
                    )
                    for opt in custom_options
                ]
            else:
                options = await self._generate_default_options(decision_type, context or {})
            
            # Create decision
            decision = CollaborativeDecision(
                id=decision_id,
                project_id=project_id,
                decision_type=decision_type,
                title=title,
                description=description,
                context=context or {},
                options=options,
                required_participants=participants["required"],
                optional_participants=participants["optional"],
                minimum_consensus=template.get("minimum_consensus", 0.7),
                authority_required=template.get("authority_required", AuthorityLevel.MIDDLE_MANAGEMENT),
                initiated_by=initiated_by,
                facilitator=await self._select_facilitator(participants["required"], decision_type),
                status=DecisionStatus.PROPOSED,
                discussion_messages=[],
                deadline=deadline or (datetime.utcnow() + template.get("discussion_duration", timedelta(hours=2))),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                decision_made_at=None,
                selected_option=None,
                final_reasoning=None,
                metadata={}
            )
            
            self.active_decisions[decision_id] = decision
            
            # Create discussion in appropriate channel
            await self._initiate_decision_discussion(decision)
            
            # Schedule automated follow-ups
            asyncio.create_task(self._manage_decision_lifecycle(decision_id))
            
            logger.log_system_event("collaborative_decision_initiated", {
                "decision_id": decision_id,
                "project_id": project_id,
                "decision_type": decision_type.value,
                "participants": len(participants["required"] + participants["optional"]),
                "options": len(options)
            })
            
            return decision_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initiate_collaborative_decision",
                "project_id": project_id,
                "decision_type": decision_type.value
            })
            raise
    
    async def _determine_participants(
        self, 
        project_id: str, 
        decision_type: DecisionType, 
        initiated_by: str
    ) -> Dict[str, List[str]]:
        """Determine who should participate in the decision"""
        try:
            # Get project team members
            project_agents = await self._get_project_agents(project_id)
            template = self.decision_templates.get(decision_type, {})
            
            required_participants = []
            optional_participants = []
            
            # Add typical participants based on decision type
            typical_roles = template.get("typical_participants", [])
            for role in typical_roles:
                agents_with_role = [
                    agent_id for agent_id, agent_info in project_agents.items()
                    if agent_info.get("role", "").lower() == role.lower()
                ]
                required_participants.extend(agents_with_role)
            
            # Always include the initiator
            if initiated_by not in required_participants:
                required_participants.append(initiated_by)
            
            # Add authority figures if needed
            authority_required = template.get("authority_required", AuthorityLevel.MIDDLE_MANAGEMENT)
            authority_agents = await organizational_hierarchy.get_agents_with_authority(authority_required)
            for agent in authority_agents:
                if agent.id not in required_participants:
                    optional_participants.append(agent.id)
            
            # Add other project team members as optional
            for agent_id in project_agents:
                if agent_id not in required_participants and agent_id not in optional_participants:
                    optional_participants.append(agent_id)
            
            return {
                "required": list(set(required_participants)),
                "optional": list(set(optional_participants))
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "determine_participants",
                "project_id": project_id,
                "decision_type": decision_type.value
            })
            return {"required": [initiated_by], "optional": []}
    
    async def _generate_default_options(
        self, 
        decision_type: DecisionType, 
        context: Dict[str, Any]
    ) -> List[DecisionOption]:
        """Generate default options for a decision type"""
        options = []
        
        if decision_type == DecisionType.PROJECT_APPROACH:
            base_options = [
                {
                    "title": "Agile/Scrum with 2-week Sprints",
                    "description": "Iterative development with regular sprint cycles, daily standups, and sprint reviews",
                    "pros": ["Flexible to changes", "Regular feedback cycles", "Team collaboration"],
                    "cons": ["Requires experienced team", "Can be overhead for small projects"],
                    "implementation_effort": "medium",
                    "risk_level": "low"
                },
                {
                    "title": "Kanban Continuous Flow",
                    "description": "Continuous delivery with work-in-progress limits and visual workflow management",
                    "pros": ["Continuous delivery", "Visual workflow", "Flexible priorities"],
                    "cons": ["Less structured", "Requires mature team"],
                    "implementation_effort": "low",
                    "risk_level": "medium"
                },
                {
                    "title": "Hybrid Agile-Waterfall",
                    "description": "Combine planning phases with iterative development cycles",
                    "pros": ["Structured planning", "Iterative delivery", "Risk mitigation"],
                    "cons": ["More complex", "Potential overhead"],
                    "implementation_effort": "high",
                    "risk_level": "medium"
                }
            ]
        elif decision_type == DecisionType.TECHNOLOGY_STACK:
            # Generate options based on project context
            project_type = context.get("project_type", "web_application")
            if project_type == "web_application":
                base_options = [
                    {
                        "title": "React + Node.js + PostgreSQL",
                        "description": "Modern JavaScript stack with React frontend, Node.js backend, and PostgreSQL database",
                        "pros": ["Unified language", "Large ecosystem", "Good performance"],
                        "cons": ["JavaScript complexity", "Rapid ecosystem changes"],
                        "implementation_effort": "medium",
                        "risk_level": "low"
                    },
                    {
                        "title": "Python + Django + PostgreSQL",
                        "description": "Python web framework with batteries included and robust database",
                        "pros": ["Rapid development", "Mature framework", "Great libraries"],
                        "cons": ["Performance limitations", "GIL constraints"],
                        "implementation_effort": "low",
                        "risk_level": "low"
                    },
                    {
                        "title": "Java + Spring Boot + MySQL",
                        "description": "Enterprise-grade Java framework with proven scalability",
                        "pros": ["Enterprise proven", "Strong typing", "Great tooling"],
                        "cons": ["Verbose code", "Slower development"],
                        "implementation_effort": "high",
                        "risk_level": "low"
                    }
                ]
            else:
                base_options = [{"title": "Custom Analysis Required", "description": "Project type requires specific technology analysis", "pros": [], "cons": [], "implementation_effort": "medium", "risk_level": "medium"}]
        else:
            # Default generic options
            base_options = [
                {
                    "title": "Option A - Conservative Approach",
                    "description": "Lower risk option with proven methods",
                    "pros": ["Lower risk", "Proven approach"],
                    "cons": ["May be slower", "Less innovative"],
                    "implementation_effort": "low",
                    "risk_level": "low"
                },
                {
                    "title": "Option B - Balanced Approach", 
                    "description": "Moderate risk with good potential upside",
                    "pros": ["Good balance", "Reasonable timeline"],
                    "cons": ["Some uncertainty", "Moderate complexity"],
                    "implementation_effort": "medium",
                    "risk_level": "medium"
                },
                {
                    "title": "Option C - Innovative Approach",
                    "description": "Higher risk but potentially higher reward option",
                    "pros": ["Cutting edge", "High potential value"],
                    "cons": ["Higher risk", "Unknown challenges"],
                    "implementation_effort": "high", 
                    "risk_level": "high"
                }
            ]
        
        # Convert to DecisionOption objects
        for i, opt in enumerate(base_options):
            options.append(DecisionOption(
                id=f"opt_{uuid.uuid4().hex[:6]}",
                title=opt["title"],
                description=opt["description"],
                proposed_by="system",
                pros=opt.get("pros", []),
                cons=opt.get("cons", []),
                implementation_effort=opt.get("implementation_effort", "medium"),
                risk_level=opt.get("risk_level", "medium"),
                cost_estimate=opt.get("cost_estimate"),
                timeline_impact=opt.get("timeline_impact"),
                votes={},
                vote_reasoning={}
            ))
        
        return options
    
    async def _select_facilitator(
        self, 
        required_participants: List[str], 
        decision_type: DecisionType
    ) -> Optional[str]:
        """Select the best facilitator for the decision"""
        try:
            # Preference order for facilitators by decision type
            facilitator_preferences = {
                DecisionType.PROJECT_APPROACH: ["project_manager", "cto", "senior_developer"],
                DecisionType.ARCHITECTURE_DECISION: ["architect", "cto", "senior_developer"],
                DecisionType.TECHNOLOGY_STACK: ["cto", "architect", "senior_developer"],
                DecisionType.TIMELINE_ESTIMATION: ["project_manager", "senior_developer"],
                DecisionType.RESOURCE_ALLOCATION: ["cto", "project_manager"],
                DecisionType.BUDGET_APPROVAL: ["ceo", "cto"]
            }
            
            preferred_roles = facilitator_preferences.get(decision_type, ["senior_developer", "cto"])
            
            # Get agent roles
            for participant_id in required_participants:
                agent_info = await self._get_agent_info(participant_id)
                if agent_info and agent_info.get("role", "").lower() in [r.lower() for r in preferred_roles]:
                    return participant_id
            
            # Fallback to first required participant
            return required_participants[0] if required_participants else None
            
        except Exception as e:
            logger.log_error(e, {"action": "select_facilitator"})
            return required_participants[0] if required_participants else None
    
    async def _initiate_decision_discussion(self, decision: CollaborativeDecision):
        """Start the discussion for a decision in the appropriate channel"""
        try:
            # Get or create decision-making channel
            channel = await self.project_channel_manager.get_channel_by_type(
                decision.project_id, ChannelType.GENERAL
            )
            
            if not channel:
                logger.log_error("No suitable channel found for decision discussion", {
                    "project_id": decision.project_id,
                    "decision_id": decision.id
                })
                return
            
            # Create comprehensive discussion initiation message
            facilitator_info = await self._get_agent_info(decision.facilitator)
            facilitator_name = facilitator_info.get("name", "Project Facilitator") if facilitator_info else "Project Facilitator"
            
            # Build participant list
            all_participants = decision.required_participants + decision.optional_participants
            participant_mentions = []
            for participant_id in all_participants:
                agent_info = await self._get_agent_info(participant_id)
                if agent_info:
                    participant_mentions.append(f"@{agent_info.get('name', participant_id)}")
            
            # Build options summary
            options_summary = []
            for i, option in enumerate(decision.options, 1):
                options_summary.append(
                    f"**Option {i}: {option.title}**\n"
                    f"   • {option.description}\n"
                    f"   • Effort: {option.implementation_effort.title()}, Risk: {option.risk_level.title()}\n"
                    f"   • Pros: {', '.join(option.pros[:2])}{'...' if len(option.pros) > 2 else ''}\n"
                )
            
            discussion_content = f"""🎯 **COLLABORATIVE DECISION REQUIRED**

**Decision:** {decision.title}
**Type:** {decision.decision_type.value.replace('_', ' ').title()}
**Facilitator:** {facilitator_name}
**Deadline:** {decision.deadline.strftime('%Y-%m-%d %H:%M')}

**Context:**
{decision.description}

**Options to Consider:**
{chr(10).join(options_summary)}

**Participants:**
{', '.join(participant_mentions)}

**Next Steps:**
1. 💭 **Discussion Phase**: Share your thoughts, concerns, and suggestions
2. 🗳️ **Voting Phase**: Cast your votes with reasoning
3. ✅ **Consensus Building**: Work toward agreement
4. 📋 **Implementation**: Execute the decided approach

**Discussion Guidelines:**
• Consider all technical, business, and timeline implications
• Share your expertise and concerns openly
• Ask clarifying questions
• Propose alternative solutions if needed

Let's start the discussion! What are your initial thoughts on these options?"""

            # Send the discussion initiation message
            message_id = await self.project_channel_manager.send_channel_message(
                channel_id=channel.id,
                sender_id=decision.facilitator,
                sender_name=facilitator_name,
                sender_type="agent",
                content=discussion_content,
                message_type="decision_discussion",
                metadata={
                    "decision_id": decision.id,
                    "decision_type": decision.decision_type.value,
                    "phase": "discussion_initiated",
                    "options_count": len(decision.options),
                    "required_participants": decision.required_participants
                }
            )
            
            if message_id:
                decision.discussion_messages.append(message_id)
                decision.status = DecisionStatus.DISCUSSING
                decision.updated_at = datetime.utcnow()
            
            # Notify all participants
            for participant_id in all_participants:
                await self._notify_participant_of_decision(participant_id, decision)
            
            logger.log_system_event("decision_discussion_initiated", {
                "decision_id": decision.id,
                "channel_id": channel.id,
                "participants": len(all_participants),
                "message_id": message_id
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initiate_decision_discussion",
                "decision_id": decision.id
            })
    
    async def _notify_participant_of_decision(self, participant_id: str, decision: CollaborativeDecision):
        """Notify a participant about a new decision requiring their input"""
        try:
            participant_info = await self._get_agent_info(participant_id)
            if not participant_info:
                return
            
            # Send direct notification
            notification_content = f"""📋 **Decision Input Needed**

You've been invited to participate in a collaborative decision for **{decision.title}**.

**Decision Type:** {decision.decision_type.value.replace('_', ' ').title()}
**Deadline:** {decision.deadline.strftime('%Y-%m-%d %H:%M')}
**Your Role:** {'Required Participant' if participant_id in decision.required_participants else 'Optional Participant'}

Please join the discussion in the project channel and share your expertise and perspective.

**Quick Summary:** {decision.description[:200]}{'...' if len(decision.description) > 200 else ''}"""

            # Send via inter-agent communication
            await self.inter_agent_comm.send_message(
                from_agent_id="system",
                to_agent_id=participant_id,
                content=notification_content,
                message_type="collaboration_request",
                priority="high" if participant_id in decision.required_participants else "normal",
                metadata={
                    "decision_id": decision.id,
                    "decision_type": decision.decision_type.value,
                    "role": "required" if participant_id in decision.required_participants else "optional"
                }
            )
            
        except Exception as e:
            logger.log_error(e, {
                "action": "notify_participant_of_decision",
                "participant_id": participant_id,
                "decision_id": decision.id
            })
    
    async def _manage_decision_lifecycle(self, decision_id: str):
        """Manage the automated lifecycle of a decision"""
        try:
            await asyncio.sleep(300)  # Wait 5 minutes before first check
            
            while decision_id in self.active_decisions:
                decision = self.active_decisions[decision_id]
                
                if decision.status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.COMPLETED]:
                    break
                
                current_time = datetime.utcnow()
                
                # Check if we need to move to voting phase
                if (decision.status == DecisionStatus.DISCUSSING and 
                    current_time >= decision.deadline - timedelta(minutes=30)):
                    await self._transition_to_voting(decision)
                
                # Check if voting deadline has passed
                elif (decision.status == DecisionStatus.VOTING and 
                      current_time >= decision.deadline):
                    await self._evaluate_consensus(decision)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            logger.log_error(e, {
                "action": "manage_decision_lifecycle",
                "decision_id": decision_id
            })
    
    async def _transition_to_voting(self, decision: CollaborativeDecision):
        """Transition decision from discussion to voting phase"""
        try:
            decision.status = DecisionStatus.VOTING
            decision.updated_at = datetime.utcnow()
            
            # Get discussion channel
            channel = await self.project_channel_manager.get_channel_by_type(
                decision.project_id, ChannelType.GENERAL
            )
            
            if channel:
                facilitator_info = await self._get_agent_info(decision.facilitator)
                facilitator_name = facilitator_info.get("name", "Project Facilitator") if facilitator_info else "Project Facilitator"
                
                voting_content = f"""🗳️ **VOTING PHASE INITIATED**

The discussion period for **{decision.title}** has concluded. It's time to cast your votes!

**Voting Instructions:**
• Vote for your preferred option with reasoning
• You can vote: Approve ✅, Reject ❌, Abstain ⚪, or Conditional ⚠️
• **Required consensus:** {decision.minimum_consensus * 100:.0f}%
• **Voting deadline:** {decision.deadline.strftime('%Y-%m-%d %H:%M')}

**Options Available:**
{chr(10).join([f"**{i+1}. {opt.title}** - {opt.description}" for i, opt in enumerate(decision.options)])}

Please respond with your vote and reasoning. Format: "I vote for Option X because..."

Required participants who haven't voted will receive reminders."""

                await self.project_channel_manager.send_channel_message(
                    channel_id=channel.id,
                    sender_id=decision.facilitator,
                    sender_name=facilitator_name,
                    sender_type="agent",
                    content=voting_content,
                    message_type="voting_phase",
                    metadata={
                        "decision_id": decision.id,
                        "phase": "voting",
                        "deadline": decision.deadline.isoformat()
                    }
                )
            
            logger.log_system_event("decision_voting_initiated", {
                "decision_id": decision.id,
                "options": len(decision.options),
                "required_participants": len(decision.required_participants)
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "transition_to_voting",
                "decision_id": decision.id
            })
    
    async def _evaluate_consensus(self, decision: CollaborativeDecision):
        """Evaluate if consensus has been reached and finalize decision"""
        try:
            total_votes = 0
            approve_votes = 0
            option_votes = {}
            
            # Count votes across all options
            for option in decision.options:
                for agent_id, vote in option.votes.items():
                    total_votes += 1
                    if vote == VoteType.APPROVE:
                        approve_votes += 1
                        option_votes[option.id] = option_votes.get(option.id, 0) + 1
            
            # Check if minimum participation is met
            required_participation = len(decision.required_participants)
            if total_votes < required_participation * 0.8:  # At least 80% of required participants
                await self._extend_deadline_or_escalate(decision, "insufficient_participation")
                return
            
            # Find winning option
            if option_votes:
                winning_option_id = max(option_votes, key=option_votes.get)
                winning_option = next(opt for opt in decision.options if opt.id == winning_option_id)
                
                consensus_ratio = option_votes[winning_option_id] / total_votes
                
                if consensus_ratio >= decision.minimum_consensus:
                    # Consensus reached
                    decision.status = DecisionStatus.CONSENSUS_REACHED
                    decision.selected_option = winning_option_id
                    decision.decision_made_at = datetime.utcnow()
                    
                    # Generate final reasoning
                    decision.final_reasoning = await self._generate_decision_reasoning(
                        decision, winning_option, consensus_ratio
                    )
                    
                    await self._announce_decision_result(decision, True)
                    
                    # Check if authority approval is needed
                    if decision.authority_required != AuthorityLevel.INDIVIDUAL_CONTRIBUTOR:
                        await self._request_authority_approval(decision)
                    else:
                        decision.status = DecisionStatus.APPROVED
                        await self._initiate_implementation(decision)
                else:
                    # No consensus, try conflict resolution
                    await self._initiate_conflict_resolution(decision)
            else:
                # No votes, escalate
                await self._extend_deadline_or_escalate(decision, "no_votes")
            
            decision.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.log_error(e, {
                "action": "evaluate_consensus",
                "decision_id": decision.id
            })
    
    async def _generate_decision_reasoning(
        self, 
        decision: CollaborativeDecision, 
        winning_option: DecisionOption, 
        consensus_ratio: float
    ) -> str:
        """Generate comprehensive reasoning for the decision"""
        try:
            reasoning_parts = [
                f"**Decision:** {winning_option.title}",
                f"**Consensus Level:** {consensus_ratio * 100:.1f}% ({consensus_ratio:.2f} ratio)",
                f"**Primary Reasons:**"
            ]
            
            # Collect reasoning from votes
            unique_reasons = set()
            for agent_id, reason in winning_option.vote_reasoning.items():
                if reason and reason not in unique_reasons:
                    unique_reasons.add(reason)
                    reasoning_parts.append(f"• {reason}")
            
            # Add implementation details
            reasoning_parts.extend([
                f"**Implementation Effort:** {winning_option.implementation_effort.title()}",
                f"**Risk Level:** {winning_option.risk_level.title()}",
                f"**Key Benefits:** {', '.join(winning_option.pros[:3])}"
            ])
            
            if winning_option.timeline_impact:
                reasoning_parts.append(f"**Timeline Impact:** {winning_option.timeline_impact}")
            
            return "\n".join(reasoning_parts)
            
        except Exception as e:
            logger.log_error(e, {"action": "generate_decision_reasoning"})
            return f"Decision made for {winning_option.title} with {consensus_ratio * 100:.1f}% consensus."
    
    # Helper methods
    async def _get_project_agents(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Get agents assigned to a project"""
        # This would integrate with your project management system
        # For now, return a mock structure
        return {
            "cto-001": {"role": "CTO", "name": "Technical Director"},
            "dev-001": {"role": "Senior Developer", "name": "Lead Developer"},
            "dev-002": {"role": "Developer", "name": "Backend Developer"},
            "qa-001": {"role": "QA Engineer", "name": "Quality Assurance"}
        }
    
    async def _get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent"""
        # This would integrate with your agent management system
        agent_mapping = {
            "cto-001": {"name": "Technical Director", "role": "CTO"},
            "dev-001": {"name": "Lead Developer", "role": "Senior Developer"},
            "dev-002": {"name": "Backend Developer", "role": "Developer"},
            "qa-001": {"name": "Quality Assurance", "role": "QA Engineer"},
            "system": {"name": "System", "role": "System"}
        }
        return agent_mapping.get(agent_id)
    
    async def _announce_decision_result(self, decision: CollaborativeDecision, consensus_reached: bool):
        """Announce the result of a decision"""
        # Implementation for announcing results
        pass
    
    async def _request_authority_approval(self, decision: CollaborativeDecision):
        """Request approval from higher authority"""
        # Implementation for authority approval
        pass
    
    async def _initiate_implementation(self, decision: CollaborativeDecision):
        """Start implementing the decided approach"""
        # Implementation for starting implementation
        pass
    
    async def _initiate_conflict_resolution(self, decision: CollaborativeDecision):
        """Start conflict resolution process when consensus isn't reached"""
        # Implementation for conflict resolution
        pass
    
    async def _extend_deadline_or_escalate(self, decision: CollaborativeDecision, reason: str):
        """Extend deadline or escalate decision to higher authority"""
        # Implementation for deadline extension or escalation
        pass


# Global instance will be created when dependencies are available
collaborative_decision_system = None