"""
Talent Pool Service - Manages available agents with skills and traits
"""

import random
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.agent import Agent, AgentRole, AgentStatus, Skill, SkillLevel, PersonalityTrait
from services.ollama_service import ollama_service
from core.logging import get_logger

logger = get_logger(__name__)


class TalentPool:
    """Manages a pool of available agents with diverse skills and personalities"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.initialize_talent_pool()
    
    def initialize_talent_pool(self):
        """Create initial talent pool with diverse agents"""
        logger.log_system_event("talent_pool_initializing", {"message": "Creating initial talent pool"})
        
        # Start with a few seed agents, then expand using Ollama
        self._create_seed_agents()
        
        logger.log_system_event("talent_pool_initialized", {
            "total_agents": len(self.agents),
            "roles": list(set(agent.role for agent in self.agents.values())),
            "source": "seed_agents"
        })
    
    def _create_seed_agents(self):
        """Create a few seed agents manually, then use Ollama for expansion"""
        seed_templates = [
            {
                "name": "Alex Chen", "role": AgentRole.DEVELOPER,
                "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
                "personality": [("Analytical", 9), ("Creative", 7), ("Leadership", 6)],
                "bio": "Full-stack developer with 8 years experience in web applications"
            },
            {
                "name": "Sarah Johnson", "role": AgentRole.DEVOPS,
                "skills": ["Docker", "Kubernetes", "AWS", "Terraform"],
                "personality": [("Reliability", 10), ("Problem-solving", 9), ("Patience", 8)],
                "bio": "DevOps engineer specializing in cloud infrastructure and automation"
            },
            {
                "name": "Marcus Rodriguez", "role": AgentRole.SECURITY,
                "skills": ["Cybersecurity", "Penetration Testing", "OWASP", "Compliance"],
                "personality": [("Attention to Detail", 10), ("Skepticism", 9), ("Thoroughness", 9)],
                "bio": "Security expert with focus on application security and threat analysis"
            }
        ]
        
        for template in seed_templates:
            agent = self._create_agent_from_template(template)
            self.agents[agent.id] = agent
    
    async def expand_talent_pool_with_ollama(self, target_size: int = 50):
        """Use Ollama to generate additional diverse agents"""
        
        if not ollama_service:
            logger.log_error(Exception("Ollama service not available"), {"action": "expand_talent_pool"})
            return
        
        current_size = len(self.agents)
        if current_size >= target_size:
            logger.log_system_event("talent_pool_already_full", {
                "current_size": current_size,
                "target_size": target_size
            })
            return
        
        agents_needed = target_size - current_size
        
        # Define how many agents per role
        roles_to_generate = {
            "developer": max(1, agents_needed // 8),
            "devops": max(1, agents_needed // 10),
            "security": max(1, agents_needed // 12),
            "designer": max(1, agents_needed // 10),
            "architect": max(1, agents_needed // 15),
            "analyst": max(1, agents_needed // 10),
            "tester": max(1, agents_needed // 12),
            "project_manager": max(1, agents_needed // 15),
            "data_scientist": max(1, agents_needed // 12)
        }
        
        logger.log_system_event("expanding_talent_pool", {
            "current_size": current_size,
            "target_size": target_size,
            "agents_to_generate": sum(roles_to_generate.values()),
            "roles": roles_to_generate
        })
        
        try:
            # Generate agents using Ollama
            generated_profiles = await ollama_service.generate_multiple_agents(roles_to_generate)
            
            # Convert profiles to Agent objects
            new_agents = 0
            for profile in generated_profiles:
                try:
                    agent = self._create_agent_from_ollama_profile(profile)
                    if agent:
                        self.agents[agent.id] = agent
                        new_agents += 1
                except Exception as e:
                    logger.log_error(e, {"action": "create_agent_from_profile", "profile": profile.get("name", "unknown")})
            
            logger.log_system_event("talent_pool_expanded", {
                "new_agents": new_agents,
                "total_agents": len(self.agents),
                "source": "ollama_generated"
            })
            
        except Exception as e:
            logger.log_error(e, {"action": "expand_talent_pool_with_ollama"})
    
    def _create_agent_from_ollama_profile(self, profile: Dict[str, Any]) -> Optional[Agent]:
        """Create Agent from Ollama-generated profile"""
        try:
            agent_id = str(uuid.uuid4())
            
            # Convert skills
            skills = []
            for skill_data in profile.get("skills", []):
                level_str = skill_data.get("level", "intermediate")
                level = SkillLevel.INTERMEDIATE
                try:
                    level = SkillLevel(level_str.lower())
                except ValueError:
                    level = SkillLevel.INTERMEDIATE
                
                skills.append(Skill(
                    name=skill_data.get("name", ""),
                    level=level,
                    years_experience=skill_data.get("years_experience", 3),
                    certifications=[]
                ))
            
            # Convert personality
            personality = []
            for trait_data in profile.get("personality", []):
                personality.append(PersonalityTrait(
                    trait=trait_data.get("trait", ""),
                    score=trait_data.get("score", 5),
                    description=trait_data.get("description", "")
                ))
            
            # Convert role
            role_str = profile.get("role", "developer")
            try:
                role = AgentRole(role_str.lower())
            except ValueError:
                role = AgentRole.DEVELOPER
            
            return Agent(
                id=agent_id,
                name=profile.get("name", "Unknown Agent"),
                role=role,
                status=AgentStatus.AVAILABLE,
                skills=skills,
                personality=personality,
                projects_completed=profile.get("projects_completed", 15),
                success_rate=profile.get("success_rate", 0.90),
                avg_task_completion_time=random.uniform(12.0, 36.0),
                bio=profile.get("bio", ""),
                preferred_work_style=profile.get("preferred_work_style", "Collaborative")
            )
            
        except Exception as e:
            logger.log_error(e, {"action": "_create_agent_from_ollama_profile"})
            return None
    
    def _create_agent_from_template(self, template: dict) -> Agent:
        """Create agent from template with randomized attributes"""
        agent_id = str(uuid.uuid4())
        
        # Create skills
        skills = []
        for skill_name in template["skills"]:
            level = random.choice([SkillLevel.ADVANCED, SkillLevel.EXPERT])
            years = random.randint(3, 10)
            skills.append(Skill(
                name=skill_name,
                level=level,
                years_experience=years,
                certifications=self._generate_certifications(skill_name)
            ))
        
        # Create personality traits
        personality = []
        for trait_name, base_score in template["personality"]:
            # Add some randomness to scores
            score = max(1, min(10, base_score + random.randint(-1, 1)))
            personality.append(PersonalityTrait(
                trait=trait_name,
                score=score,
                description=f"Strong in {trait_name.lower()}"
            ))
        
        return Agent(
            id=agent_id,
            name=template["name"],
            role=template["role"],
            status=AgentStatus.AVAILABLE,
            skills=skills,
            personality=personality,
            projects_completed=random.randint(5, 50),
            success_rate=random.uniform(0.85, 0.98),
            avg_task_completion_time=random.uniform(12.0, 36.0),
            bio=template["bio"],
            preferred_work_style=random.choice([
                "Independent", "Collaborative", "Structured", "Flexible", "Detail-oriented"
            ])
        )
    
    def _generate_certifications(self, skill: str) -> List[str]:
        """Generate relevant certifications for a skill"""
        cert_map = {
            "AWS": ["AWS Solutions Architect", "AWS DevOps Engineer"],
            "Docker": ["Docker Certified Associate"],
            "Kubernetes": ["Certified Kubernetes Administrator"],
            "Cybersecurity": ["CISSP", "CEH", "Security+"],
            "Python": ["Python Professional Certification"],
            "UI/UX": ["Google UX Design Certificate", "Adobe Certified Expert"],
            "Agile": ["Certified Scrum Master", "PMI-ACP"],
            "Machine Learning": ["Google ML Engineer", "AWS ML Specialty"]
        }
        
        base_certs = cert_map.get(skill, [])
        # Randomly assign 0-2 certifications
        return random.sample(base_certs, min(len(base_certs), random.randint(0, 2)))
    
    def get_available_agents(self) -> List[Agent]:
        """Get all available agents"""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.AVAILABLE]
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents regardless of status"""
        return list(self.agents.values())
    
    def get_agents_by_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.INTERMEDIATE) -> List[Agent]:
        """Find agents with specific skill at minimum level"""
        matching_agents = []
        skill_levels = [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED, SkillLevel.EXPERT, SkillLevel.MASTER]
        min_level_index = skill_levels.index(min_level)
        
        for agent in self.get_available_agents():
            for skill in agent.skills:
                if skill.name.lower() == skill_name.lower():
                    if skill_levels.index(skill.level) >= min_level_index:
                        matching_agents.append(agent)
                        break
        
        return matching_agents
    
    def get_agents_by_role(self, role: AgentRole) -> List[Agent]:
        """Find available agents by role"""
        return [agent for agent in self.get_available_agents() if agent.role == role]
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        if agent_id in self.agents:
            old_status = self.agents[agent_id].status
            self.agents[agent_id].status = status
            
            logger.log_agent_action(
                agent_id=agent_id,
                action="status_change",
                details={"old_status": old_status, "new_status": status}
            )
            return True
        return False
    
    def hire_agent(self, agent_id: str, hired_by: str, salary: int) -> bool:
        """Mark agent as hired"""
        if agent_id in self.agents and self.agents[agent_id].status == AgentStatus.AVAILABLE:
            agent = self.agents[agent_id]
            agent.status = AgentStatus.HIRED
            agent.hired_by = hired_by
            agent.hire_date = datetime.now()
            agent.current_salary = salary
            
            logger.log_agent_action(
                agent_id=agent_id,
                action="hired",
                details={"hired_by": hired_by, "salary": salary}
            )
            return True
        return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get talent pool statistics"""
        agents = list(self.agents.values())
        
        return {
            "total_agents": len(agents),
            "available_agents": len(self.get_available_agents()),
            "roles_distribution": {
                role.value: len([a for a in agents if a.role == role])
                for role in AgentRole if role != AgentRole.CEO
            },
            "avg_success_rate": sum(a.success_rate for a in agents) / len(agents),
            "total_skills": len(set(skill.name for agent in agents for skill in agent.skills))
        }


# Global talent pool instance
talent_pool = TalentPool()