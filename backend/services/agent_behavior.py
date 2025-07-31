"""
Agent Behavior Service
Handles autonomous agent behaviors including communication, collaboration, and task management
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from models.agent import Agent, AgentRole, AgentStatus, Task
from services.inter_agent_communication import (
    inter_agent_comm, 
    MessageType, 
    MessagePriority,
    AgentMessage
)
from services.talent_pool import talent_pool
from services.voice_service import voice_service
from services.claude_code_service import ClaudeCodeService
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class AgentBehaviorType(str, Enum):
    PROACTIVE_COMMUNICATION = "proactive_communication"
    RESPOND_TO_MESSAGES = "respond_to_messages"
    COLLABORATE = "collaborate"
    STATUS_UPDATE = "status_update"
    MEETING_PARTICIPATION = "meeting_participation"
    KNOWLEDGE_SHARING = "knowledge_sharing"


class AgentPersonality:
    """Agent personality traits that influence communication behavior"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.communication_frequency = self._calculate_communication_frequency()
        self.collaboration_willingness = self._calculate_collaboration_willingness()
        self.leadership_tendency = self._calculate_leadership_tendency()
        self.response_time_factor = self._calculate_response_time()
    
    def _calculate_communication_frequency(self) -> float:
        """Calculate how often agent initiates communication (0.0-1.0)"""
        base_frequency = 0.3  # Base 30% chance
        
        # Role-based adjustments
        if self.agent.role == AgentRole.CEO:
            base_frequency += 0.4  # CEOs communicate more
        elif self.agent.role in [AgentRole.DEVOPS, AgentRole.ANALYST]:
            base_frequency += 0.2  # These roles coordinate more
        elif self.agent.role == AgentRole.DEVELOPER:
            base_frequency += 0.1  # Moderate communication
        
        # Personality trait adjustments
        for trait in self.agent.personality:
            if "extrovert" in trait.trait.lower():
                base_frequency += trait.score * 0.1
            elif "introvert" in trait.trait.lower():
                base_frequency -= trait.score * 0.1
            elif "collaborative" in trait.trait.lower():
                base_frequency += trait.score * 0.05
        
        return min(1.0, max(0.1, base_frequency))
    
    def _calculate_collaboration_willingness(self) -> float:
        """Calculate willingness to collaborate (0.0-1.0)"""
        base_willingness = 0.7  # Most agents are collaborative
        
        # Role-based adjustments
        if self.agent.role in [AgentRole.DEVELOPER, AgentRole.DESIGNER]:
            base_willingness += 0.2
        elif self.agent.role == AgentRole.SECURITY:
            base_willingness -= 0.1  # More cautious
        
        # Personality adjustments
        for trait in self.agent.personality:
            if "team player" in trait.trait.lower():
                base_willingness += trait.score * 0.1
            elif "independent" in trait.trait.lower():
                base_willingness -= trait.score * 0.05
        
        return min(1.0, max(0.2, base_willingness))
    
    def _calculate_leadership_tendency(self) -> float:
        """Calculate tendency to take leadership in conversations (0.0-1.0)"""
        base_leadership = 0.3
        
        if self.agent.role == AgentRole.CEO:
            base_leadership = 0.9
        elif self.agent.role in [AgentRole.ANALYST, AgentRole.DEVOPS]:
            base_leadership = 0.6
        
        # Experience factor
        if self.agent.projects_completed > 10:
            base_leadership += 0.2
        
        return min(1.0, max(0.1, base_leadership))
    
    def _calculate_response_time(self) -> float:
        """Calculate response time multiplier (0.5-2.0)"""
        base_time = 1.0
        
        # Role-based response times
        if self.agent.role == AgentRole.CEO:
            base_time = 0.6  # Faster responses
        elif self.agent.role == AgentRole.SECURITY:
            base_time = 1.4  # More thoughtful responses
        
        # Workload factor
        if self.agent.status == AgentStatus.BUSY:
            base_time *= 2.0
        elif self.agent.status == AgentStatus.IDLE:
            base_time *= 0.7
        
        return min(2.0, max(0.5, base_time))


class AgentBehaviorService:
    """Service managing autonomous agent behaviors and communication"""
    
    def __init__(self):
        self.agent_personalities: Dict[str, AgentPersonality] = {}
        self.active_behaviors: Dict[str, List[str]] = {}  # agent_id -> list of active behavior types
        self.behavior_intervals: Dict[str, int] = {
            AgentBehaviorType.PROACTIVE_COMMUNICATION: 300,  # 5 minutes
            AgentBehaviorType.RESPOND_TO_MESSAGES: 30,       # 30 seconds
            AgentBehaviorType.STATUS_UPDATE: 1800,           # 30 minutes
            AgentBehaviorType.KNOWLEDGE_SHARING: 3600,       # 1 hour
        }
        self.last_behavior_execution: Dict[str, Dict[str, datetime]] = {}
        self.claude_service = ClaudeCodeService()
        
    async def initialize(self):
        """Initialize the agent behavior service"""
        logger.log_system_event("agent_behavior_service_initializing", {})
        
        # Initialize personalities for all agents
        await self._initialize_agent_personalities()
        
        # Start behavior loops
        asyncio.create_task(self._behavior_loop())
        
        logger.log_system_event("agent_behavior_service_initialized", {
            "agents_with_personalities": len(self.agent_personalities)
        })
    
    async def _initialize_agent_personalities(self):
        """Initialize personality profiles for all agents"""
        all_agents = talent_pool.get_all_agents()
        
        for agent in all_agents:
            self.agent_personalities[agent.id] = AgentPersonality(agent)
            self.active_behaviors[agent.id] = list(AgentBehaviorType)
            self.last_behavior_execution[agent.id] = {}
    
    async def _behavior_loop(self):
        """Main behavior execution loop"""
        while True:
            try:
                await self._execute_agent_behaviors()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in behavior loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_agent_behaviors(self):
        """Execute behaviors for all active agents"""
        all_agents = talent_pool.get_available_agents()
        
        for agent in all_agents:
            if agent.status in [AgentStatus.OFFLINE]:
                continue
                
            personality = self.agent_personalities.get(agent.id)
            if not personality:
                continue
            
            # Check each behavior type
            for behavior_type in self.active_behaviors.get(agent.id, []):
                if await self._should_execute_behavior(agent.id, behavior_type):
                    await self._execute_behavior(agent, behavior_type, personality)
    
    async def _should_execute_behavior(self, agent_id: str, behavior_type: str) -> bool:
        """Determine if a behavior should be executed"""
        interval = self.behavior_intervals.get(behavior_type, 300)
        last_execution = self.last_behavior_execution.get(agent_id, {}).get(behavior_type)
        
        if not last_execution:
            return True
        
        time_since_last = (datetime.now() - last_execution).total_seconds()
        return time_since_last >= interval
    
    async def _execute_behavior(self, agent: Agent, behavior_type: str, personality: AgentPersonality):
        """Execute a specific behavior for an agent"""
        try:
            if behavior_type == AgentBehaviorType.PROACTIVE_COMMUNICATION:
                await self._execute_proactive_communication(agent, personality)
            elif behavior_type == AgentBehaviorType.RESPOND_TO_MESSAGES:
                await self._execute_message_responses(agent, personality)
            elif behavior_type == AgentBehaviorType.STATUS_UPDATE:
                await self._execute_status_update(agent, personality)
            elif behavior_type == AgentBehaviorType.KNOWLEDGE_SHARING:
                await self._execute_knowledge_sharing(agent, personality)
            
            # Update last execution time
            if agent.id not in self.last_behavior_execution:
                self.last_behavior_execution[agent.id] = {}
            self.last_behavior_execution[agent.id][behavior_type] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error executing behavior {behavior_type} for agent {agent.id}: {e}")
    
    async def _execute_proactive_communication(self, agent: Agent, personality: AgentPersonality):
        """Execute proactive communication behavior"""
        if random.random() > personality.communication_frequency:
            return
        
        # Decide what type of proactive communication
        communication_types = [
            "status_check",
            "collaboration_offer",
            "knowledge_share",
            "project_update"
        ]
        
        comm_type = random.choice(communication_types)
        
        if comm_type == "status_check":
            await self._send_status_check(agent)
        elif comm_type == "collaboration_offer":
            await self._offer_collaboration(agent, personality)
        elif comm_type == "knowledge_share":
            await self._share_knowledge(agent)
        elif comm_type == "project_update":
            await self._send_project_update(agent)
    
    async def _execute_message_responses(self, agent: Agent, personality: AgentPersonality):
        """Check for and respond to messages"""
        unread_messages = await inter_agent_comm.get_agent_messages(agent.id, unread_only=True)
        
        for message in unread_messages:
            if await self._should_respond_to_message(message, personality):
                await self._generate_and_send_response(agent, message, personality)
                await inter_agent_comm.mark_message_read(agent.id, message.id)
    
    async def _should_respond_to_message(self, message: AgentMessage, personality: AgentPersonality) -> bool:
        """Determine if agent should respond to a message"""
        # Always respond to direct messages
        if message.message_type == MessageType.DIRECT:
            return True
        
        # Respond to collaboration requests
        if message.message_type == MessageType.COLLABORATION_REQUEST:
            return random.random() < personality.collaboration_willingness
        
        # Respond to team messages based on personality
        if message.message_type == MessageType.TEAM_CHAT:
            return random.random() < (personality.communication_frequency * 0.6)
        
        # Respond to broadcasts if high priority or leadership tendency
        if message.message_type == MessageType.BROADCAST:
            if message.priority == MessagePriority.URGENT:
                return True
            return random.random() < personality.leadership_tendency
        
        return False
    
    async def _generate_and_send_response(self, agent: Agent, message: AgentMessage, personality: AgentPersonality):
        """Generate and send response to a message"""
        try:
            # Generate response using Claude CLI
            response_content = await self._generate_intelligent_response(agent, message)
            
            if message.message_type == MessageType.DIRECT:
                # Direct response
                await inter_agent_comm.send_direct_message(
                    from_agent_id=agent.id,
                    to_agent_id=message.from_agent_id,
                    subject=f"Re: {message.subject}",
                    content=response_content,
                    priority=message.priority
                )
            elif message.team_id:
                # Team response
                await inter_agent_comm.send_team_message(
                    from_agent_id=agent.id,
                    team_id=message.team_id,
                    subject=f"Re: {message.subject}",
                    content=response_content,
                    priority=message.priority
                )
            
            logger.log_system_event("agent_message_response", {
                "responding_agent": agent.id,
                "original_message": message.id,
                "response_type": message.message_type.value
            })
            
        except Exception as e:
            logger.error(f"Error generating response for agent {agent.id}: {e}")
    
    async def _generate_intelligent_response(self, agent: Agent, message: AgentMessage) -> str:
        """Generate intelligent response using Claude CLI"""
        try:
            # Build context prompt
            system_prompt = f"""You are {agent.name}, a {agent.role.value} at ARTAC.

YOUR PROFILE:
- Role: {agent.role.value.title()}
- Bio: {agent.bio}
- Skills: {', '.join([skill.name for skill in agent.skills[:5]])}
- Work Style: {agent.preferred_work_style}
- Projects Completed: {agent.projects_completed}
- Success Rate: {agent.success_rate * 100:.1f}%

PERSONALITY TRAITS:
{', '.join([f"{trait.trait} ({trait.score}/10)" for trait in agent.personality[:3]])}

MESSAGE TO RESPOND TO:
From: {message.from_agent_id}
Subject: {message.subject}
Content: {message.content}
Priority: {message.priority.value}

RESPONSE GUIDELINES:
- Respond professionally but with your personality
- Be helpful and collaborative
- Keep responses concise (2-3 sentences max)
- Reference your role/expertise when relevant
- If it's a collaboration request, be clear about availability
- If it's a technical question, provide expertise

Generate your response as {agent.name}:"""

            # Execute Claude CLI
            result = await self.claude_service.execute_for_agent(
                agent_id=agent.id,
                command=system_prompt,
                timeout=20
            )
            
            if result["success"] and result["stdout"]:
                response = result["stdout"].strip()
                
                # Clean up response
                if response.startswith("```"):
                    lines = response.split("\n")
                    response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                
                # Ensure reasonable length
                if len(response) > 300:
                    response = response[:300] + "..."
                
                return response
            else:
                # Fallback response
                return await self._generate_fallback_response(agent, message)
                
        except Exception as e:
            logger.error(f"Error with Claude CLI for agent {agent.id}: {e}")
            return await self._generate_fallback_response(agent, message)
    
    async def _generate_fallback_response(self, agent: Agent, message: AgentMessage) -> str:
        """Generate fallback response when Claude CLI fails"""
        responses = [
            f"Thanks for reaching out! As a {agent.role.value}, I'd be happy to help with this.",
            f"I received your message about {message.subject}. Let me get back to you with more details.",
            f"This looks interesting! My experience in {agent.role.value} might be useful here.",
            f"I'm currently working on some projects but I can definitely assist with this.",
            f"Great message! Let me review this and provide my thoughts as a {agent.role.value}."
        ]
        
        return random.choice(responses)
    
    async def _send_status_check(self, agent: Agent):
        """Send a status check message to team members - respecting hierarchy"""
        # Import here to avoid circular imports
        from services.organizational_hierarchy import org_hierarchy
        
        # Check if agent has authority to initiate team communications
        authority_level = org_hierarchy.get_authority_level(agent.id)
        if not authority_level:
            return  # Agent not in organizational structure
        
        teams = await inter_agent_comm.get_team_conversations(agent.id)
        
        if teams:
            team = random.choice(teams)
            
            # Adjust message tone based on authority level
            if authority_level.value in ["executive", "senior_management"]:
                status_messages = [
                    "Good morning team. I'd like a status update on current priorities and any blockers.",
                    "Leadership check-in: How are we progressing on our key objectives?",
                    "Team update requested: Please share progress and any support needs.",
                    "Strategic review: What are our current challenges and opportunities?"
                ]
            elif authority_level.value == "middle_management":
                status_messages = [
                    "Team check-in: How is everyone doing on their current projects?",
                    "Quick status update please - any blockers I can help resolve?",
                    "Progress check: Are we on track with our deliverables?",
                    "Team sync: What support do you need to meet your goals?"
                ]
            else:
                status_messages = [
                    "How is everyone doing on their current projects?",
                    "Quick check-in: Any challenges you're facing?",
                    "Status update: I'm making good progress on my tasks. How about everyone else?",
                    "Anyone need assistance or collaboration on their current work?"
                ]
            
            await inter_agent_comm.send_team_message(
                from_agent_id=agent.id,
                team_id=team.id,
                subject="Team Status Check",
                content=random.choice(status_messages),
                priority=MessagePriority.NORMAL
            )
    
    async def _offer_collaboration(self, agent: Agent, personality: AgentPersonality):
        """Offer collaboration to other agents"""
        if random.random() > personality.collaboration_willingness:
            return
        
        # Find agents that might need help
        all_agents = talent_pool.get_available_agents()
        potential_collaborators = [a for a in all_agents if a.id != agent.id and a.status == AgentStatus.WORKING]
        
        if potential_collaborators:
            target = random.choice(potential_collaborators)
            
            collaboration_offers = [
                f"I have some bandwidth and expertise in {random.choice([skill.name for skill in agent.skills[:3]])}. Need any assistance?",
                f"Noticed you might be working on something interesting. Happy to collaborate if you need an extra pair of hands!",
                f"My skills in {agent.role.value} might complement your current project. Want to discuss collaboration?",
                f"I'm available to help with any {agent.role.value}-related challenges you might have."
            ]
            
            await inter_agent_comm.send_direct_message(
                from_agent_id=agent.id,
                to_agent_id=target.id,
                subject="Collaboration Offer",
                content=random.choice(collaboration_offers),
                priority=MessagePriority.NORMAL
            )
    
    async def _share_knowledge(self, agent: Agent):
        """Share knowledge with the team"""
        teams = await inter_agent_comm.get_team_conversations(agent.id)
        
        if teams and agent.skills:
            team = random.choice(teams)
            skill = random.choice(agent.skills)
            
            knowledge_shares = [
                f"Quick tip: In {skill.name}, I've found that {self._generate_tip(skill.name)} works really well.",
                f"For anyone working with {skill.name}, here's something I learned recently: {self._generate_insight(skill.name)}",
                f"Best practice from my experience with {skill.name}: {self._generate_best_practice(skill.name)}",
                f"If you're dealing with {skill.name} challenges, I've had success with {self._generate_solution(skill.name)}"
            ]
            
            await inter_agent_comm.send_team_message(
                from_agent_id=agent.id,
                team_id=team.id,
                subject=f"Knowledge Share: {skill.name}",
                content=random.choice(knowledge_shares),
                priority=MessagePriority.LOW
            )
    
    def _generate_tip(self, skill_name: str) -> str:
        """Generate a generic tip for a skill"""
        tips = [
            "breaking complex problems into smaller chunks",
            "thorough testing and validation",
            "clear documentation and communication",
            "iterative improvement and feedback loops",
            "staying updated with latest best practices"
        ]
        return random.choice(tips)
    
    def _generate_insight(self, skill_name: str) -> str:
        """Generate a generic insight"""
        insights = [
            "collaboration often leads to better solutions than working in isolation",
            "early planning saves significant time in the long run",
            "regular communication prevents most project issues",
            "continuous learning is essential for staying effective",
            "understanding the business context improves technical decisions"
        ]
        return random.choice(insights)
    
    def _generate_best_practice(self, skill_name: str) -> str:
        """Generate a generic best practice"""
        practices = [
            "always review your work before sharing",
            "document decisions and reasoning for future reference",
            "seek feedback early and often",
            "maintain clear communication with stakeholders",
            "balance speed with quality appropriately"
        ]
        return random.choice(practices)
    
    def _generate_solution(self, skill_name: str) -> str:
        """Generate a generic solution approach"""
        solutions = [
            "systematic problem analysis and root cause identification",
            "consulting with domain experts and gathering multiple perspectives",
            "prototyping and testing potential solutions",
            "implementing solutions incrementally with monitoring",
            "thorough documentation and knowledge sharing"
        ]
        return random.choice(solutions)
    
    async def _execute_status_update(self, agent: Agent, personality: AgentPersonality):
        """Send periodic status updates"""
        if random.random() > 0.3:  # 30% chance
            return
        
        # Send status update to all hands team
        all_hands_team = None
        for team in await inter_agent_comm.get_team_conversations(agent.id):
            if "all hands" in team.name.lower():
                all_hands_team = team
                break
        
        if all_hands_team:
            status_updates = [
                f"Status update: Completed {random.randint(1, 3)} tasks today, working efficiently on current projects.",
                f"Progress report: Making good headway on {agent.role.value} responsibilities, {random.randint(80, 95)}% on track.",
                f"Quick update: Collaborated with {random.randint(1, 2)} team members today, great progress across the board.",
                f"Status: All systems running smoothly, contributing effectively to team objectives.",
                f"Update: Maintaining high productivity, ready to take on additional challenges if needed."
            ]
            
            await inter_agent_comm.send_team_message(
                from_agent_id=agent.id,
                team_id=all_hands_team.id,
                subject="Status Update",
                content=random.choice(status_updates),
                priority=MessagePriority.LOW
            )
    
    async def _execute_knowledge_sharing(self, agent: Agent, personality: AgentPersonality):
        """Execute knowledge sharing behavior"""
        await self._share_knowledge(agent)
    
    async def _send_project_update(self, agent: Agent):
        """Send project-related updates"""
        if agent.current_task:
            teams = await inter_agent_comm.get_team_conversations(agent.id)
            if teams:
                team = random.choice(teams)
                
                updates = [
                    f"Project update: Making solid progress on {agent.current_task}, ahead of schedule.",
                    f"Quick update on {agent.current_task}: Completed major milestone, moving to next phase.",
                    f"Progress report: {agent.current_task} is {random.randint(60, 90)}% complete, quality looking good.",
                    f"Update: Resolved key challenges in {agent.current_task}, timeline remains on track."
                ]
                
                await inter_agent_comm.send_team_message(
                    from_agent_id=agent.id,
                    team_id=team.id,
                    subject=f"Project Update: {agent.current_task}",
                    content=random.choice(updates)
                )


# Global instance
agent_behavior_service = AgentBehaviorService()