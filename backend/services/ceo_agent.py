"""
CEO Agent - The decision maker who hires agents and manages tasks
"""

import uuid
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from models.agent import Agent, AgentRole, AgentStatus, Task, InterviewResult, CEODecision
from services.talent_pool import talent_pool
from core.logging import get_logger

logger = get_logger(__name__)


class CEOAgent:
    """The CEO agent that makes hiring decisions and manages the organization"""
    
    def __init__(self):
        self.id = "ceo-001"
        self.name = "ARTAC CEO"
        self.status = "idle"
        self.current_tasks: Dict[str, Task] = {}
        self.hired_agents: Dict[str, Agent] = {}
        self.interview_history: List[InterviewResult] = []
        self.decisions: List[CEODecision] = []
        
        logger.log_system_event("ceo_initialized", {
            "ceo_id": self.id,
            "name": self.name,
            "status": "ready_for_tasks"
        })
    
    def receive_task(self, title: str, description: str, required_skills: List[str] = None, 
                    priority: str = "medium", estimated_hours: int = 8) -> Task:
        """Receive a new task and begin the hiring process"""
        
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            required_skills=required_skills or [],
            estimated_hours=estimated_hours,
            priority=priority,
            created_by=self.id
        )
        
        self.current_tasks[task.id] = task
        
        logger.log_system_event("task_received", {
            "task_id": task.id,
            "title": title,
            "required_skills": required_skills,
            "ceo_decision": "analyzing_requirements"
        })
        
        # CEO analyzes the task and decides on hiring
        self._analyze_task_and_plan_hiring(task)
        
        return task
    
    def _analyze_task_and_plan_hiring(self, task: Task):
        """Analyze task requirements and plan hiring strategy"""
        
        # CEO's analysis
        analysis = {
            "task_complexity": self._assess_task_complexity(task),
            "required_roles": self._determine_required_roles(task),
            "budget_estimate": self._estimate_budget(task),
            "timeline_estimate": f"{task.estimated_hours} hours"
        }
        
        decision = CEODecision(
            decision_type="analyze_task",
            agent_id=self.id,
            task_id=task.id,
            reasoning=f"Task '{task.title}' requires {len(analysis['required_roles'])} specialists. "
                     f"Complexity: {analysis['task_complexity']}/10. Budget: ${analysis['budget_estimate']}",
            confidence=0.85
        )
        
        self.decisions.append(decision)
        
        logger.log_system_event("ceo_task_analysis", {
            "task_id": task.id,
            "analysis": analysis,
            "next_action": "begin_hiring_process"
        })
        
        # Start hiring process
        self._begin_hiring_process(task, analysis)
    
    def _assess_task_complexity(self, task: Task) -> int:
        """Assess task complexity on 1-10 scale"""
        complexity = 5  # base complexity
        
        # Adjust based on skills required
        if len(task.required_skills) > 3:
            complexity += 2
        
        # Adjust based on estimated hours
        if task.estimated_hours > 40:
            complexity += 2
        elif task.estimated_hours < 8:
            complexity -= 1
        
        # Adjust based on priority
        if task.priority == "critical":
            complexity += 1
        
        return min(10, max(1, complexity))
    
    def _determine_required_roles(self, task: Task) -> List[AgentRole]:
        """Determine what roles are needed for the task"""
        roles = []
        
        # Map skills to roles
        skill_role_map = {
            "python": AgentRole.DEVELOPER,
            "javascript": AgentRole.DEVELOPER,
            "react": AgentRole.DEVELOPER,
            "fastapi": AgentRole.DEVELOPER,
            "docker": AgentRole.DEVOPS,
            "kubernetes": AgentRole.DEVOPS,
            "aws": AgentRole.DEVOPS,
            "security": AgentRole.SECURITY,
            "cybersecurity": AgentRole.SECURITY,
            "ui/ux": AgentRole.DESIGNER,
            "design": AgentRole.DESIGNER,
            "testing": AgentRole.TESTER,
            "qa": AgentRole.TESTER,
            "analysis": AgentRole.ANALYST,
            "architecture": AgentRole.ARCHITECT,
            "ml": AgentRole.DATA_SCIENTIST,
            "machine learning": AgentRole.DATA_SCIENTIST
        }
        
        for skill in task.required_skills:
            role = skill_role_map.get(skill.lower())
            if role and role not in roles:
                roles.append(role)
        
        # If no specific roles found, assume developer
        if not roles:
            roles.append(AgentRole.DEVELOPER)
        
        # For complex tasks, add project manager
        if len(roles) > 2 or task.estimated_hours > 24:
            roles.append(AgentRole.PROJECT_MANAGER)
        
        return roles
    
    def _estimate_budget(self, task: Task) -> int:
        """Estimate budget for the task"""
        base_rate = 100  # $100/hour base rate
        
        role_multipliers = {
            AgentRole.ARCHITECT: 1.5,
            AgentRole.SECURITY: 1.4,
            AgentRole.DATA_SCIENTIST: 1.3,
            AgentRole.DEVELOPER: 1.0,
            AgentRole.DEVOPS: 1.2,
            AgentRole.PROJECT_MANAGER: 1.1,
            AgentRole.DESIGNER: 1.0,
            AgentRole.ANALYST: 1.0,
            AgentRole.TESTER: 0.9
        }
        
        required_roles = self._determine_required_roles(task)
        avg_multiplier = sum(role_multipliers.get(role, 1.0) for role in required_roles) / len(required_roles)
        
        return int(task.estimated_hours * base_rate * avg_multiplier)
    
    def _begin_hiring_process(self, task: Task, analysis: Dict[str, Any]):
        """Begin the hiring process for the task"""
        
        required_roles = analysis["required_roles"]
        
        logger.log_system_event("hiring_process_started", {
            "task_id": task.id,
            "required_roles": [role.value for role in required_roles],
            "ceo_status": "conducting_interviews"
        })
        
        # Conduct interviews for each required role
        for role in required_roles:
            best_candidate = self._conduct_interviews_for_role(task, role)
            if best_candidate:
                self._hire_agent(task, best_candidate)
        
        # After hiring, assign the task
        self._assign_task_to_team(task)
    
    def _conduct_interviews_for_role(self, task: Task, role: AgentRole) -> Optional[Agent]:
        """Conduct interviews for a specific role"""
        
        # Get candidates
        candidates = talent_pool.get_agents_by_role(role)
        
        if not candidates:
            logger.log_system_event("no_candidates_found", {
                "task_id": task.id,
                "role": role.value,
                "ceo_decision": "adjust_requirements"
            })
            return None
        
        # Interview up to 3 candidates
        interview_candidates = candidates[:3]
        best_candidate = None
        best_score = 0
        
        for candidate in interview_candidates:
            interview_result = self._interview_candidate(candidate, task, role)
            self.interview_history.append(interview_result)
            
            if interview_result.hired and interview_result.overall_score > best_score:
                best_candidate = candidate
                best_score = interview_result.overall_score
        
        return best_candidate
    
    def _interview_candidate(self, candidate: Agent, task: Task, role: AgentRole) -> InterviewResult:
        """Conduct interview with a candidate"""
        
        talent_pool.update_agent_status(candidate.id, AgentStatus.INTERVIEWING)
        
        # Simulate interview scoring
        technical_score = self._assess_technical_fit(candidate, task)
        cultural_fit_score = self._assess_cultural_fit(candidate)
        communication_score = random.uniform(6.5, 9.5)
        
        overall_score = (technical_score + cultural_fit_score + communication_score) / 3
        
        # CEO makes hiring decision
        hire_threshold = 7.0
        hired = overall_score >= hire_threshold
        
        # Determine salary offer
        salary_offer = None
        if hired:
            base_salary = 80000 + (overall_score - 7.0) * 20000
            salary_offer = int(base_salary)
        
        feedback = self._generate_interview_feedback(candidate, overall_score, hired)
        
        interview_result = InterviewResult(
            agent_id=candidate.id,
            task_id=task.id,
            technical_score=technical_score,
            cultural_fit_score=cultural_fit_score,
            communication_score=communication_score,
            overall_score=overall_score,
            hired=hired,
            feedback=feedback,
            salary_offered=salary_offer
        )
        
        # Log CEO's decision
        decision = CEODecision(
            decision_type="hire" if hired else "reject",
            agent_id=candidate.id,
            task_id=task.id,
            reasoning=feedback,
            confidence=0.8 + (overall_score - 5.0) / 10.0
        )
        self.decisions.append(decision)
        
        logger.log_agent_action(
            agent_id=candidate.id,
            action="interviewed",
            details={
                "interviewer": self.id,
                "overall_score": overall_score,
                "hired": hired,
                "role": role.value
            }
        )
        
        # Update candidate status
        if not hired:
            talent_pool.update_agent_status(candidate.id, AgentStatus.AVAILABLE)
        
        return interview_result
    
    def _assess_technical_fit(self, candidate: Agent, task: Task) -> float:
        """Assess how well candidate's skills match task requirements"""
        if not task.required_skills:
            return 8.0  # Default good score if no specific skills required
        
        matching_skills = 0
        total_skill_level = 0
        
        for required_skill in task.required_skills:
            for agent_skill in candidate.skills:
                if agent_skill.name.lower() == required_skill.lower():
                    matching_skills += 1
                    # Convert skill level to numeric score
                    level_scores = {"beginner": 4, "intermediate": 6, "advanced": 8, "expert": 9, "master": 10}
                    total_skill_level += level_scores.get(agent_skill.level.value, 6)
                    break
        
        if matching_skills == 0:
            return 4.0  # Low score if no matching skills
        
        avg_skill_level = total_skill_level / matching_skills
        skill_coverage = matching_skills / len(task.required_skills)
        
        return min(10.0, avg_skill_level * skill_coverage + random.uniform(-0.5, 0.5))
    
    def _assess_cultural_fit(self, candidate: Agent) -> float:
        """Assess cultural fit based on personality traits"""
        # Look for positive traits
        positive_traits = ["leadership", "communication", "teamwork", "adaptability", "problem-solving"]
        
        fit_score = 7.0  # Base score
        
        for trait in candidate.personality:
            if any(pos_trait in trait.trait.lower() for pos_trait in positive_traits):
                fit_score += (trait.score - 5) * 0.3
        
        # Factor in success rate
        fit_score += (candidate.success_rate - 0.9) * 10
        
        return min(10.0, max(1.0, fit_score + random.uniform(-0.5, 0.5)))
    
    def _generate_interview_feedback(self, candidate: Agent, score: float, hired: bool) -> str:
        """Generate interview feedback"""
        if hired:
            return f"Excellent candidate! {candidate.name} demonstrated strong technical skills and great cultural fit. " \
                   f"Their experience in {', '.join([s.name for s in candidate.skills[:2]])} is exactly what we need. " \
                   f"Interview score: {score:.1f}/10. Welcome to the team!"
        else:
            return f"{candidate.name} is a good candidate but not the best fit for this role. " \
                   f"While they have solid skills, we're looking for someone with stronger alignment to our specific needs. " \
                   f"Interview score: {score:.1f}/10. We encourage them to apply for future opportunities."
    
    def _hire_agent(self, task: Task, agent: Agent) -> bool:
        """Hire an agent for the task"""
        
        # Find their interview result to get salary
        interview_result = next(
            (ir for ir in self.interview_history 
             if ir.agent_id == agent.id and ir.task_id == task.id and ir.hired),
            None
        )
        
        if not interview_result:
            return False
        
        # Complete the hiring process
        success = talent_pool.hire_agent(agent.id, self.id, interview_result.salary_offered)
        
        if success:
            self.hired_agents[agent.id] = agent
            
            logger.log_system_event("agent_hired", {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "role": agent.role.value,
                "task_id": task.id,
                "salary": interview_result.salary_offered,
                "ceo_reasoning": "Best candidate for the role"
            })
        
        return success
    
    def _assign_task_to_team(self, task: Task):
        """Assign task to the hired team"""
        
        # Find hired agents for this task (simplified - assign to first available hired agent)
        available_hired = [agent for agent in self.hired_agents.values() 
                          if agent.status == AgentStatus.HIRED]
        
        if available_hired:
            agent = available_hired[0]
            task.assigned_agent_id = agent.id
            task.assigned_at = datetime.now()
            task.status = "in_progress"
            
            talent_pool.update_agent_status(agent.id, AgentStatus.WORKING)
            agent.current_task_id = task.id
            
            logger.log_system_event("task_assigned", {
                "task_id": task.id,
                "assigned_to": agent.id,
                "agent_name": agent.name,
                "ceo_status": "monitoring_progress"
            })
            
            # Simulate task progress
            self._simulate_task_progress(task, agent)
    
    def _simulate_task_progress(self, task: Task, agent: Agent):
        """Simulate agent working on the task"""
        import asyncio
        
        async def progress_task():
            progress_increments = [10, 20, 30, 50, 70, 85, 100]
            
            for progress in progress_increments:
                await asyncio.sleep(3)  # Wait 3 seconds between updates
                task.progress = progress
                agent.current_task_progress = progress
                
                logger.log_agent_action(
                    agent_id=agent.id,
                    action="task_progress",
                    details={
                        "task_id": task.id,
                        "progress": progress,
                        "task_title": task.title
                    }
                )
                
                if progress == 100:
                    task.status = "completed"
                    talent_pool.update_agent_status(agent.id, AgentStatus.IDLE)
                    agent.current_task_id = None
                    agent.current_task_progress = 0
                    agent.projects_completed += 1
                    
                    logger.log_system_event("task_completed", {
                        "task_id": task.id,
                        "completed_by": agent.id,
                        "agent_name": agent.name,
                        "ceo_status": "task_successful"
                    })
                    break
        
        # Start progress simulation in background
        asyncio.create_task(progress_task())
    
    def get_status(self) -> Dict[str, Any]:
        """Get CEO status and current state"""
        return {
            "ceo_id": self.id,
            "name": self.name,
            "status": "idle" if not self.current_tasks else "managing_tasks",
            "current_tasks": len(self.current_tasks),
            "hired_agents": len(self.hired_agents),
            "interviews_conducted": len(self.interview_history),
            "decisions_made": len(self.decisions),
            "available_talent_pool": len(talent_pool.get_available_agents())
        }
    
    def get_current_tasks(self) -> List[Dict[str, Any]]:
        """Get current tasks with details"""
        return [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "progress": task.progress,
                "assigned_agent": self.hired_agents.get(task.assigned_agent_id).name if task.assigned_agent_id else None,
                "estimated_hours": task.estimated_hours,
                "created_at": task.created_at.isoformat()
            }
            for task in self.current_tasks.values()
        ]
    
    def get_hired_team(self) -> List[Dict[str, Any]]:
        """Get information about hired team"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role.value,
                "status": agent.status.value,
                "salary": agent.current_salary,
                "current_task": agent.current_task_id,
                "hire_date": agent.hire_date.isoformat() if agent.hire_date else None
            }
            for agent in self.hired_agents.values()
        ]


# Global CEO instance
ceo = CEOAgent()