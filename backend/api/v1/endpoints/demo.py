"""
CEO and Organization Management Endpoints
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ceo_agent import ceo
from services.talent_pool import talent_pool
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class TaskRequest(BaseModel):
    title: str
    description: str
    required_skills: Optional[List[str]] = None
    priority: str = "medium"
    estimated_hours: int = 8


@router.get("/organization/status")
async def get_organization_status() -> Dict[str, Any]:
    """Get the overall organization status"""
    
    ceo_status = ceo.get_status()
    talent_stats = talent_pool.get_pool_stats()
    
    return {
        "ceo": ceo_status,
        "talent_pool": talent_stats,
        "organization_state": "idle" if ceo_status["current_tasks"] == 0 else "active",
        "message": "Organization ready for tasks" if ceo_status["current_tasks"] == 0 else "CEO managing active tasks"
    }


@router.get("/organization/talent-pool")
async def get_talent_pool() -> Dict[str, Any]:
    """Get information about available talent"""
    
    available_agents = talent_pool.get_available_agents()
    
    agents_info = []
    for agent in available_agents:
        agents_info.append({
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "skills": [{"name": s.name, "level": s.level.value, "years": s.years_experience} for s in agent.skills],
            "personality_highlights": [f"{t.trait}: {t.score}/10" for t in agent.personality[:3]],
            "success_rate": f"{agent.success_rate:.1%}",
            "projects_completed": agent.projects_completed,
            "bio": agent.bio
        })
    
    return {
        "available_agents": len(available_agents),
        "agents": agents_info,
        "total_pool_size": talent_pool.get_pool_stats()["total_agents"]
    }


@router.post("/organization/assign-task")
async def assign_task(task_request: TaskRequest) -> Dict[str, Any]:
    """Give the CEO a new task - this will trigger the hiring process"""
    
    logger.log_system_event("new_task_received", {
        "title": task_request.title,
        "required_skills": task_request.required_skills,
        "priority": task_request.priority
    })
    
    # CEO receives the task and begins hiring process
    task = ceo.receive_task(
        title=task_request.title,
        description=task_request.description,
        required_skills=task_request.required_skills,
        priority=task_request.priority,
        estimated_hours=task_request.estimated_hours
    )
    
    return {
        "status": "task_received",
        "task_id": task.id,
        "message": f"CEO received task '{task.title}' and is analyzing requirements",
        "ceo_status": "analyzing_and_hiring",
        "next_steps": [
            "CEO will analyze task requirements",
            "Identify needed roles and skills", 
            "Interview candidates from talent pool",
            "Hire best candidates",
            "Assign task to hired team"
        ]
    }


@router.get("/organization/current-tasks")
async def get_current_tasks() -> Dict[str, Any]:
    """Get all current tasks being managed by the CEO"""
    
    tasks = ceo.get_current_tasks()
    
    return {
        "total_tasks": len(tasks),
        "tasks": tasks,
        "ceo_workload": "light" if len(tasks) < 3 else "heavy" if len(tasks) > 5 else "moderate"
    }


@router.get("/organization/hired-team")
async def get_hired_team() -> Dict[str, Any]:
    """Get information about currently hired team members"""
    
    team = ceo.get_hired_team()
    
    return {
        "team_size": len(team),
        "team_members": team,
        "total_payroll": sum(member.get("salary", 0) for member in team)
    }


@router.get("/organization/interview-history")
async def get_interview_history() -> Dict[str, Any]:
    """Get CEO's interview and hiring history"""
    
    interviews = []
    for interview in ceo.interview_history[-10:]:  # Last 10 interviews
        interviews.append({
            "agent_id": interview.agent_id,
            "task_id": interview.task_id,
            "technical_score": round(interview.technical_score, 1),
            "cultural_fit_score": round(interview.cultural_fit_score, 1),
            "communication_score": round(interview.communication_score, 1),
            "overall_score": round(interview.overall_score, 1),
            "hired": interview.hired,
            "feedback": interview.feedback,
            "salary_offered": interview.salary_offered,
            "interview_date": interview.interview_date.isoformat()
        })
    
    return {
        "recent_interviews": len(interviews),
        "interviews": interviews,
        "hire_rate": f"{sum(1 for i in ceo.interview_history if i.hired) / len(ceo.interview_history) * 100:.1f}%" if ceo.interview_history else "0%"
    }


@router.get("/organization/ceo-decisions")
async def get_ceo_decisions() -> Dict[str, Any]:
    """Get recent CEO decisions and reasoning"""
    
    recent_decisions = []
    for decision in ceo.decisions[-10:]:  # Last 10 decisions
        recent_decisions.append({
            "decision_type": decision.decision_type,
            "agent_id": decision.agent_id,
            "task_id": decision.task_id,
            "reasoning": decision.reasoning,
            "confidence": f"{decision.confidence:.1%}",
            "timestamp": decision.timestamp.isoformat()
        })
    
    return {
        "recent_decisions": len(recent_decisions),
        "decisions": recent_decisions,
        "total_decisions_made": len(ceo.decisions)
    }


@router.post("/organization/expand-talent-pool")
async def expand_talent_pool(target_size: int = 50) -> Dict[str, Any]:
    """Use Ollama to generate more diverse agents for the talent pool"""
    
    current_size = len(talent_pool.get_available_agents())
    
    if current_size >= target_size:
        return {
            "status": "no_expansion_needed",
            "current_size": current_size,
            "target_size": target_size,
            "message": "Talent pool already meets target size"
        }
    
    logger.log_system_event("talent_pool_expansion_requested", {
        "current_size": current_size,
        "target_size": target_size,
        "using": "ollama_generation"
    })
    
    try:
        # Trigger expansion using Ollama
        await talent_pool.expand_talent_pool_with_ollama(target_size)
        
        new_size = len(talent_pool.get_available_agents())
        agents_added = new_size - current_size
        
        return {
            "status": "expansion_completed",
            "agents_added": agents_added,  
            "previous_size": current_size,
            "new_size": new_size,
            "target_size": target_size,
            "message": f"Successfully generated {agents_added} new agents using Ollama",
            "cost_savings": "Used local Ollama instead of Claude CLI tokens"
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "expand_talent_pool_endpoint"})
        return {
            "status": "expansion_failed",
            "error": str(e),
            "current_size": current_size,
            "message": "Failed to expand talent pool. Check Ollama service."
        }