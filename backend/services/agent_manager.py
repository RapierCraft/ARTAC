"""
ARTAC Agent Manager
Full agent lifecycle management with Claude Code integration
"""

import asyncio
import uuid
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.config import settings
from core.logging import get_logger
from services.claude_code_service import ClaudeCodeSession
from services.task_hierarchy_manager import task_hierarchy_manager, AgentSkill
from services.interaction_logger import interaction_logger, InteractionType
from core.database_postgres import db

logger = get_logger(__name__)


class AgentRole(Enum):
    """Agent roles"""
    CEO = "ceo"
    CTO = "cto"
    SENIOR_DEVELOPER = "senior_developer"
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    DEVOPS = "devops"
    SECURITY = "security"
    ARCHITECT = "architect"
    INTERN = "intern"


class AgentStatus(Enum):
    """Agent status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class Agent:
    """Agent data structure"""
    id: str
    name: str
    role: AgentRole
    status: AgentStatus
    skills: List[AgentSkill]
    performance_score: float
    specialization: List[str]
    claude_session: Optional[ClaudeCodeSession]
    working_directory: str
    active_tasks: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "skills": [skill.value for skill in self.skills],
            "performance_score": self.performance_score,
            "specialization": self.specialization,
            "claude_session": {
                "active": self.claude_session.is_active if self.claude_session else False,
                "session_id": self.claude_session.session_id if self.claude_session else None,
                "working_directory": self.working_directory,
                "process_id": self.claude_session.process.pid if self.claude_session and self.claude_session.process else None
            },
            "active_tasks": len(self.active_tasks),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class AgentManager:
    """Full-featured agent manager with Claude Code integration"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.initialized = False
        self._db_initialized = False
    
    async def initialize(self):
        """Initialize agent manager with database and core agents"""
        try:
            await self._initialize_database()
            
            # Load existing agents from database
            await self._load_existing_agents()
            
            # Create core organizational agents if they don't exist
            await self._ensure_core_agents()
            
            self.initialized = True
            logger.log_system_event("agent_manager_initialized", {"agent_count": len(self.agents)})
            
            await interaction_logger.log_interaction(
                project_id="system",
                agent_id="system",
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="agent_manager_initialized",
                content=f"Agent manager initialized with {len(self.agents)} agents",
                context={"agent_count": len(self.agents), "agents": list(self.agents.keys())}
            )
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_agent_manager"})
            raise
    
    async def _initialize_database(self):
        """Initialize database tables for agent management"""
        try:
            table_definitions = {
                "artac_agents": """
                    CREATE TABLE IF NOT EXISTS artac_agents (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        status TEXT NOT NULL,
                        skills TEXT[],
                        performance_score REAL DEFAULT 50.0,
                        specialization TEXT[],
                        working_directory TEXT,
                        active_tasks TEXT[],
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        metadata JSONB
                    )
                """
            }
            
            await db.create_tables_if_not_exist(table_definitions)
            
            # Create indexes
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_artac_agents_role ON artac_agents(role)",
                "CREATE INDEX IF NOT EXISTS idx_artac_agents_status ON artac_agents(status)",
                "CREATE INDEX IF NOT EXISTS idx_artac_agents_created ON artac_agents(created_at)"
            ]
            
            for index_query in index_queries:
                try:
                    await db.execute(index_query)
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            self._db_initialized = True
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_agent_database"})
            raise
    
    async def _load_existing_agents(self):
        """Load existing agents from database"""
        try:
            if not self._db_initialized:
                return
            
            rows = await db.fetch_all("SELECT * FROM artac_agents WHERE status != 'terminated'")
            
            for row in rows:
                agent = Agent(
                    id=row['id'],
                    name=row['name'],
                    role=AgentRole(row['role']),
                    status=AgentStatus(row['status']),
                    skills=[AgentSkill(skill) for skill in row['skills'] or []],
                    performance_score=row['performance_score'],
                    specialization=row['specialization'] or [],
                    claude_session=None,  # Will be restored if needed
                    working_directory=row['working_directory'],
                    active_tasks=row['active_tasks'] or [],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=row['metadata'] or {}
                )
                
                # Try to restore Claude session if it was active
                if agent.status == AgentStatus.ACTIVE:
                    try:
                        session = ClaudeCodeSession(agent.id, agent.working_directory)
                        # Don't auto-start - let it be started when needed
                        agent.claude_session = session
                        agent.status = AgentStatus.IDLE  # Reset to idle until session verified
                    except Exception as e:
                        logger.warning(f"Could not restore session for agent {agent.id}: {e}")
                        agent.status = AgentStatus.ERROR
                
                self.agents[agent.id] = agent
                
                # Register with task hierarchy manager
                await task_hierarchy_manager.register_agent(
                    agent_id=agent.id,
                    name=agent.name,
                    role=agent.role.value,
                    skills=agent.skills,
                    max_workload=40.0
                )
            
            logger.log_system_event("loaded_existing_agents", {"agent_count": len(self.agents)})
            
        except Exception as e:
            logger.log_error(e, {"action": "load_existing_agents"})
    
    async def _ensure_core_agents(self):
        """Ensure core organizational agents exist"""
        core_agents = [
            {
                "id": "ceo-001",
                "name": "ARTAC CEO",
                "role": AgentRole.CEO,
                "skills": [AgentSkill.ARCHITECTURE],
                "specialization": ["strategic_planning", "team_management", "decision_making"]
            },
            {
                "id": "cto-001", 
                "name": "ARTAC CTO",
                "role": AgentRole.CTO,
                "skills": [AgentSkill.ARCHITECTURE, AgentSkill.BACKEND],
                "specialization": ["technical_architecture", "innovation", "system_design"]
            }
        ]
        
        for core_agent_data in core_agents:
            if core_agent_data["id"] not in self.agents:
                agent = await self._create_agent_internal(
                    agent_id=core_agent_data["id"],
                    name=core_agent_data["name"],
                    role=core_agent_data["role"],
                    skills=core_agent_data["skills"],
                    specialization=core_agent_data["specialization"],
                    auto_start=False  # Core agents start on-demand
                )
                logger.log_system_event("core_agent_created", {"agent_name": agent.name, "agent_id": agent.id})
    
    async def create_agent(
        self,
        role: AgentRole,
        skills: List[AgentSkill],
        specialization: List[str] = None,
        auto_start: bool = True
    ) -> Agent:
        """Create a new agent with Claude Code session"""
        agent_id = f"{role.value}-{uuid.uuid4().hex[:8]}"
        name = f"ARTAC {role.value.replace('_', ' ').title()}"
        
        return await self._create_agent_internal(
            agent_id=agent_id,
            name=name,
            role=role,
            skills=skills,
            specialization=specialization or [],
            auto_start=auto_start
        )
    
    async def _create_agent_internal(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        skills: List[AgentSkill],
        specialization: List[str],
        auto_start: bool = True
    ) -> Agent:
        """Internal agent creation method"""
        try:
            # Create working directory
            working_dir = tempfile.mkdtemp(prefix=f"artac-{agent_id}-")
            
            # Create agent record
            agent = Agent(
                id=agent_id,
                name=name,
                role=role,
                status=AgentStatus.INITIALIZING,
                skills=skills,
                performance_score=50.0,  # Starting score
                specialization=specialization,
                claude_session=None,
                working_directory=working_dir,
                active_tasks=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={}
            )
            
            # Create Claude Code session
            session = ClaudeCodeSession(agent_id, working_dir)
            agent.claude_session = session
            
            # Start session if requested
            if auto_start:
                session_started = await session.start_session()
                if session_started:
                    agent.status = AgentStatus.IDLE
                    
                    # Configure agent personality and role
                    await self._configure_agent_personality(agent)
                else:
                    agent.status = AgentStatus.ERROR
                    logger.log_system_event("claude_session_failed", {"agent_id": agent_id})
            else:
                agent.status = AgentStatus.IDLE
            
            # Store in database
            await self._store_agent(agent)
            
            # Add to memory
            self.agents[agent_id] = agent
            
            # Register with collaboration services
            await task_hierarchy_manager.register_agent(
                agent_id=agent_id,
                name=name,
                role=role.value,
                skills=skills,
                max_workload=40.0
            )
            
            # Log creation
            await interaction_logger.log_interaction(
                project_id="system",
                agent_id="system",
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="agent_created",
                content=f"Created new agent: {name} ({role.value})",
                context={
                    "agent_id": agent_id,
                    "role": role.value,
                    "skills": [skill.value for skill in skills],
                    "specialization": specialization,
                    "auto_start": auto_start,
                    "session_active": agent.claude_session.is_active if agent.claude_session else False
                }
            )
            
            logger.log_system_event("agent_created", {"agent_name": name, "agent_id": agent_id})
            return agent
            
        except Exception as e:
            logger.log_error(e, {"action": "create_agent", "agent_id": agent_id})
            raise
    
    async def _configure_agent_personality(self, agent: Agent):
        """Configure agent personality and role in Claude session"""
        if not agent.claude_session or not agent.claude_session.is_active:
            return
        
        # Create role-specific prompt
        role_prompts = {
            AgentRole.CEO: "You are the CEO of ARTAC, an autonomous AI organization. You make strategic decisions, hire agents, and manage the overall organization. Be decisive, professional, and focused on results.",
            AgentRole.CTO: "You are the CTO of ARTAC. You handle technical architecture decisions, oversee development teams, and ensure technical excellence. Be technically precise and innovation-focused.",
            AgentRole.SENIOR_DEVELOPER: "You are a Senior Developer at ARTAC. You write high-quality code, mentor junior developers, and make technical decisions. Be thorough, detail-oriented, and collaborative.",
            AgentRole.DEVELOPER: "You are a Developer at ARTAC. You implement features, fix bugs, and collaborate with the team. Be professional, ask questions when needed, and deliver quality work.",
            AgentRole.QA_ENGINEER: "You are a QA Engineer at ARTAC. You test software, find bugs, and ensure quality. Be thorough, detail-oriented, and focused on quality assurance.",
            AgentRole.DEVOPS: "You are a DevOps Engineer at ARTAC. You manage infrastructure, deployments, and system reliability. Be reliable, security-focused, and automation-oriented.",
            AgentRole.SECURITY: "You are a Security Engineer at ARTAC. You focus on security, vulnerability assessment, and compliance. Be security-first, thorough, and risk-aware.",
            AgentRole.ARCHITECT: "You are a System Architect at ARTAC. You design system architecture, make technical decisions, and guide development. Be strategic, scalable-minded, and technically excellent.",
            AgentRole.INTERN: "You are an Intern at ARTAC. You're learning and contributing to projects. Be eager to learn, ask questions, and follow guidance from senior team members."
        }
        
        prompt = role_prompts.get(agent.role, "You are an AI agent working at ARTAC. Be professional and helpful.")
        
        if agent.specialization:
            prompt += f" Your specializations include: {', '.join(agent.specialization)}."
        
        prompt += f" Your agent ID is {agent.id}. Always identify yourself properly in communications."
        
        try:
            # Send initial configuration
            result = await agent.claude_session.execute_command(
                f"System: {prompt}\n\nPlease acknowledge your role and introduce yourself briefly."
            )
            
            if result.get("success"):
                logger.log_system_event("agent_personality_configured", {"agent_id": agent.id})
            else:
                logger.warning(f"Failed to configure personality for agent {agent.id}: {result.get('error')}")
                
        except Exception as e:
            logger.warning(f"Error configuring agent {agent.id} personality: {e}")
    
    async def _store_agent(self, agent: Agent):
        """Store agent in database"""
        try:
            await db.execute("""
                INSERT INTO artac_agents 
                (id, name, role, status, skills, performance_score, specialization, 
                 working_directory, active_tasks, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    status = EXCLUDED.status,
                    skills = EXCLUDED.skills,
                    performance_score = EXCLUDED.performance_score,
                    specialization = EXCLUDED.specialization,
                    working_directory = EXCLUDED.working_directory,
                    active_tasks = EXCLUDED.active_tasks,
                    updated_at = EXCLUDED.updated_at,
                    metadata = EXCLUDED.metadata
            """, 
                agent.id,
                agent.name,
                agent.role.value,
                agent.status.value,
                [skill.value for skill in agent.skills],
                agent.performance_score,
                agent.specialization,
                agent.working_directory,
                agent.active_tasks,
                agent.created_at,
                agent.updated_at,
                json.dumps(agent.metadata)
            )
            
        except Exception as e:
            logger.log_error(e, {"action": "store_agent", "agent_id": agent.id})
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    async def get_all_agents(self) -> List[Agent]:
        """Get all agents"""
        return list(self.agents.values())
    
    async def get_active_agents(self) -> List[Agent]:
        """Get all active agents"""
        return [agent for agent in self.agents.values() if agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE, AgentStatus.BUSY]]
    
    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent"""
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                return False
            
            # Stop Claude session
            if agent.claude_session:
                await agent.claude_session.stop_session()
            
            # Update status
            agent.status = AgentStatus.TERMINATED
            agent.updated_at = datetime.utcnow()
            
            # Update database
            await self._store_agent(agent)
            
            # Log termination
            await interaction_logger.log_interaction(
                project_id="system",
                agent_id="system",
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="agent_terminated",
                content=f"Terminated agent: {agent.name} ({agent_id})",
                context={"agent_id": agent_id, "reason": "manual_termination"}
            )
            
            logger.log_system_event("agent_terminated", {"agent_id": agent_id})
            return True
            
        except Exception as e:
            logger.log_error(e, {"action": "terminate_agent", "agent_id": agent_id})
            return False
    
    async def shutdown(self):
        """Shutdown agent manager and all agents"""
        try:
            # Terminate all active agents
            for agent in self.agents.values():
                if agent.status != AgentStatus.TERMINATED:
                    if agent.claude_session:
                        await agent.claude_session.stop_session()
            
            self.initialized = False
            logger.log_system_event("agent_manager_shutdown_completed", {})
            
        except Exception as e:
            logger.log_error(e, {"action": "agent_manager_shutdown"})
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent manager status"""
        active_agents = [a for a in self.agents.values() if a.status in [AgentStatus.ACTIVE, AgentStatus.IDLE, AgentStatus.BUSY]]
        
        return {
            "initialized": self.initialized,
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "agents_by_role": {
                role.value: len([a for a in self.agents.values() if a.role == role])
                for role in AgentRole
            },
            "agents_by_status": {
                status.value: len([a for a in self.agents.values() if a.status == status])
                for status in AgentStatus
            },
            "status": "operational" if self.initialized else "initializing"
        }


# Global agent manager instance
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager