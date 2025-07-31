"""
Auto-scaling HR API Endpoints
Provides REST API for intelligent organizational scaling and HR automation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.auto_scaling_hr import auto_scaling_hr
from models.auto_scaling_hr import (
    ScalingRecommendation, ScalingDashboard, SkillGapAnalysis,
    WorkloadMetrics, HiringCriteria, ScalingTrigger, ScalingAction
)
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class ApproveRecommendationRequest(BaseModel):
    approver_id: str
    notes: Optional[str] = None


class RejectRecommendationRequest(BaseModel):
    approver_id: str
    reason: str
    notes: Optional[str] = None


class ManualScalingRequest(BaseModel):
    trigger: ScalingTrigger
    action: ScalingAction
    title: str
    description: str
    justification: str
    target_department: Optional[str] = None
    target_agent_id: Optional[str] = None
    urgency: str = "normal"
    cost_impact: Optional[float] = None


class WorkloadUpdateRequest(BaseModel):
    department: str
    capacity_utilization: float
    active_tasks: int
    overdue_tasks: int = 0
    error_rate: float = 0.0
    burnout_risk_score: float = 0.0


# Dashboard and Overview Endpoints
@router.get("/dashboard", response_model=ScalingDashboard)
async def get_scaling_dashboard():
    """Get the auto-scaling HR dashboard with current metrics"""
    try:
        dashboard = auto_scaling_hr.get_scaling_dashboard()
        return dashboard
    except Exception as e:
        logger.log_error(e, {"action": "get_scaling_dashboard"})
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")


@router.get("/status")
async def get_ahr_system_status():
    """Get AHR system status and configuration"""
    return {
        "status": "operational",
        "max_org_size": auto_scaling_hr.max_org_size,
        "min_org_size": auto_scaling_hr.min_org_size,
        "daily_scaling_limit": auto_scaling_hr.daily_scaling_limit,
        "scaling_actions_today": auto_scaling_hr.scaling_actions_today,
        "cooldown_hours": auto_scaling_hr.scaling_cooldown_hours,
        "total_recommendations": len(auto_scaling_hr.scaling_recommendations),
        "total_scaling_rules": len(auto_scaling_hr.auto_scaling_rules),
        "skill_gap_analyses": len(auto_scaling_hr.skill_gap_analyses),
        "lifecycle_events": len(auto_scaling_hr.agent_lifecycle_events)
    }


# Scaling Recommendations Endpoints
@router.get("/recommendations")
async def get_scaling_recommendations(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, implemented"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: low, normal, high, critical"),
    trigger: Optional[str] = Query(None, description="Filter by trigger type"),
    limit: int = Query(50, le=200)
):
    """Get scaling recommendations with optional filters"""
    try:
        recommendations = auto_scaling_hr.get_recommendations(status)
        
        # Apply additional filters
        if urgency:
            recommendations = [r for r in recommendations if r.urgency_level == urgency]
        
        if trigger:
            recommendations = [r for r in recommendations if r.trigger.value == trigger]
        
        # Limit results
        limited_recommendations = recommendations[:limit]
        
        return {
            "recommendations": [
                {
                    "id": rec.id,
                    "trigger": rec.trigger.value,
                    "recommended_action": rec.recommended_action.value,
                    "title": rec.title,
                    "description": rec.description,
                    "justification": rec.justification,
                    "urgency_level": rec.urgency_level,
                    "cost_impact": rec.cost_impact,
                    "status": rec.status,
                    "target_department": rec.target_department,
                    "target_agent_id": rec.target_agent_id,
                    "created_at": rec.created_at,
                    "approved_by": rec.approved_by,
                    "supporting_metrics": rec.supporting_metrics
                }
                for rec in limited_recommendations
            ],
            "total_count": len(recommendations),
            "filtered_count": len(limited_recommendations)
        }
    except Exception as e:
        logger.log_error(e, {"action": "get_scaling_recommendations"})
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/recommendations/{recommendation_id}")
async def get_recommendation_details(recommendation_id: str):
    """Get detailed information about a specific recommendation"""
    recommendation = auto_scaling_hr.scaling_recommendations.get(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {
        "id": recommendation.id,
        "trigger": recommendation.trigger.value,
        "recommended_action": recommendation.recommended_action.value,
        "title": recommendation.title,
        "description": recommendation.description,
        "justification": recommendation.justification,
        "expected_outcome": recommendation.expected_outcome,
        "risk_assessment": recommendation.risk_assessment,
        "cost_impact": recommendation.cost_impact,
        "roi_projection": recommendation.roi_projection,
        "payback_period_months": recommendation.payback_period_months,
        "urgency_level": recommendation.urgency_level,
        "implementation_timeline": recommendation.implementation_timeline,
        "expected_resolution_time": recommendation.expected_resolution_time,
        "status": recommendation.status,
        "target_department": recommendation.target_department,
        "target_agent_id": recommendation.target_agent_id,
        "supporting_metrics": recommendation.supporting_metrics,
        "affected_agents": recommendation.affected_agents,
        "dependencies": recommendation.dependencies,
        "created_by": recommendation.created_by,
        "created_at": recommendation.created_at,
        "approved_by": recommendation.approved_by,
        "approved_at": recommendation.approved_at,
        "implemented_at": recommendation.implemented_at
    }


@router.post("/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: str, request: ApproveRecommendationRequest):
    """Approve a scaling recommendation"""
    try:
        success = await auto_scaling_hr.approve_recommendation(
            recommendation_id, 
            request.approver_id
        )
        
        if success:
            return {"success": True, "message": "Recommendation approved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Recommendation not found")
            
    except Exception as e:
        logger.log_error(e, {"action": "approve_recommendation"})
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(recommendation_id: str, request: RejectRecommendationRequest):
    """Reject a scaling recommendation"""
    try:
        success = await auto_scaling_hr.reject_recommendation(
            recommendation_id,
            request.approver_id,
            request.reason
        )
        
        if success:
            return {"success": True, "message": "Recommendation rejected successfully"}
        else:
            raise HTTPException(status_code=404, detail="Recommendation not found")
            
    except Exception as e:
        logger.log_error(e, {"action": "reject_recommendation"})
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommendations/manual")
async def create_manual_recommendation(request: ManualScalingRequest):
    """Create a manual scaling recommendation"""
    try:
        # This would create a manual recommendation
        # For now, we'll add it directly to the system
        recommendation_id = str(__import__('uuid').uuid4())
        
        from models.auto_scaling_hr import ScalingRecommendation
        recommendation = ScalingRecommendation(
            id=recommendation_id,
            trigger=request.trigger,
            recommended_action=request.action,
            title=request.title,
            description=request.description,
            justification=request.justification,
            target_department=request.target_department,
            target_agent_id=request.target_agent_id,
            urgency_level=request.urgency,
            cost_impact=request.cost_impact or 0.0,
            created_by="manual_request",
            expected_outcome="Manual scaling request outcome",
            risk_assessment="Manual request - review required"
        )
        
        auto_scaling_hr.scaling_recommendations[recommendation_id] = recommendation
        
        return {"success": True, "recommendation_id": recommendation_id}
        
    except Exception as e:
        logger.log_error(e, {"action": "create_manual_recommendation"})
        raise HTTPException(status_code=400, detail=str(e))


# Skill Gap Analysis Endpoints
@router.get("/skill-gaps/latest")
async def get_latest_skill_gap_analysis():
    """Get the latest skill gap analysis"""
    analysis = auto_scaling_hr.get_skill_gap_analysis()
    if not analysis:
        return {"message": "No skill gap analysis available yet"}
    
    return {
        "id": analysis.id,
        "analysis_date": analysis.analysis_date,
        "current_skills": analysis.current_skills,
        "required_skills": analysis.required_skills,
        "skill_shortages": analysis.skill_shortages,
        "skill_surpluses": analysis.skill_surpluses,
        "role_shortages": {role.value: count for role, count in analysis.role_shortages.items()},
        "critical_gaps": analysis.critical_gaps,
        "impact_score": analysis.impact_score,
        "hiring_recommendations": [
            {
                "role": rec.required_role.value,
                "skills": rec.required_skills,
                "department": rec.department,
                "urgency": rec.urgency,
                "budget": rec.budget_allocated
            }
            for rec in analysis.hiring_recommendations
        ],
        "next_analysis_date": analysis.next_analysis_date
    }


@router.post("/skill-gaps/trigger-analysis")
async def trigger_skill_gap_analysis():
    """Manually trigger a skill gap analysis"""
    try:
        # This would trigger the skill gap analysis
        await auto_scaling_hr._analyze_skill_gaps()
        return {"success": True, "message": "Skill gap analysis triggered"}
    except Exception as e:
        logger.log_error(e, {"action": "trigger_skill_gap_analysis"})
        raise HTTPException(status_code=500, detail="Failed to trigger analysis")


# Workload Monitoring Endpoints
@router.get("/workload/metrics")
async def get_workload_metrics(
    department: Optional[str] = Query(None),
    days: int = Query(7, le=30, description="Number of days of history")
):
    """Get workload metrics history"""
    try:
        cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)
        
        # Filter metrics
        filtered_metrics = [
            m for m in auto_scaling_hr.workload_metrics_history
            if m.measurement_date >= cutoff_date
        ]
        
        if department:
            filtered_metrics = [m for m in filtered_metrics if m.department == department]
        
        return {
            "metrics": [
                {
                    "department": m.department,
                    "active_tasks": m.active_tasks,
                    "overdue_tasks": m.overdue_tasks,
                    "capacity_utilization": m.capacity_utilization,
                    "burnout_risk_score": m.burnout_risk_score,
                    "error_rate": m.error_rate,
                    "productivity_trend": m.productivity_trend,
                    "collaboration_score": m.collaboration_score,
                    "measurement_date": m.measurement_date
                }
                for m in filtered_metrics
            ],
            "total_records": len(filtered_metrics)
        }
    except Exception as e:
        logger.log_error(e, {"action": "get_workload_metrics"})
        raise HTTPException(status_code=500, detail="Failed to get workload metrics")


@router.post("/workload/update")
async def update_workload_metrics(request: WorkloadUpdateRequest):
    """Manually update workload metrics for a department"""
    try:
        # Create workload metrics from request
        metrics = WorkloadMetrics(
            department=request.department,
            capacity_utilization=request.capacity_utilization,
            active_tasks=request.active_tasks,
            overdue_tasks=request.overdue_tasks,
            error_rate=request.error_rate,
            burnout_risk_score=request.burnout_risk_score
        )
        
        # Check for triggers
        await auto_scaling_hr._check_workload_triggers(metrics)
        
        # Add to history
        auto_scaling_hr.workload_metrics_history.append(metrics)
        
        return {"success": True, "message": "Workload metrics updated"}
        
    except Exception as e:
        logger.log_error(e, {"action": "update_workload_metrics"})
        raise HTTPException(status_code=400, detail=str(e))


# Scaling Rules Management
@router.get("/scaling-rules")
async def get_scaling_rules():
    """Get all auto-scaling rules"""
    rules = list(auto_scaling_hr.auto_scaling_rules.values())
    
    return {
        "scaling_rules": [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "trigger_type": rule.trigger_type.value,
                "scaling_action": rule.scaling_action.value,
                "active": rule.active,
                "requires_approval": rule.requires_approval,
                "approval_authority": rule.approval_authority.value,
                "max_daily_actions": rule.max_daily_actions,
                "last_triggered": rule.last_triggered,
                "trigger_count": rule.trigger_count,
                "success_rate": rule.success_rate,
                "created_at": rule.created_at
            }
            for rule in rules
        ]
    }


@router.patch("/scaling-rules/{rule_id}/toggle")
async def toggle_scaling_rule(rule_id: str):
    """Enable or disable a scaling rule"""
    rule = auto_scaling_hr.auto_scaling_rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Scaling rule not found")
    
    rule.active = not rule.active
    
    return {
        "success": True,
        "rule_id": rule_id,
        "active": rule.active,
        "message": f"Rule {'enabled' if rule.active else 'disabled'}"
    }


# Agent Lifecycle Events
@router.get("/lifecycle-events")
async def get_lifecycle_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    agent_id: Optional[str] = Query(None),
    days: int = Query(30, le=90, description="Number of days of history")
):
    """Get agent lifecycle events"""
    try:
        cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)
        
        # Filter events
        filtered_events = [
            event for event in auto_scaling_hr.agent_lifecycle_events.values()
            if event.event_date >= cutoff_date
        ]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if agent_id:
            filtered_events = [e for e in filtered_events if e.agent_id == agent_id]
        
        # Sort by date (newest first)
        filtered_events.sort(key=lambda e: e.event_date, reverse=True)
        
        return {
            "lifecycle_events": [
                {
                    "id": event.id,
                    "agent_id": event.agent_id,
                    "event_type": event.event_type,
                    "event_date": event.event_date,
                    "triggered_by": event.triggered_by,
                    "reason": event.reason,
                    "previous_role": event.previous_role.value if event.previous_role else None,
                    "new_role": event.new_role.value if event.new_role else None,
                    "previous_department": event.previous_department,
                    "new_department": event.new_department,
                    "cost_impact": event.cost_impact,
                    "productivity_impact": event.productivity_impact,
                    "performance_rating": event.performance_rating.value if event.performance_rating else None
                }
                for event in filtered_events
            ],
            "total_events": len(filtered_events)
        }
    except Exception as e:
        logger.log_error(e, {"action": "get_lifecycle_events"})
        raise HTTPException(status_code=500, detail="Failed to get lifecycle events")


# Analytics Endpoints
@router.get("/analytics/scaling-trends")
async def get_scaling_trends(days: int = Query(30, le=90)):
    """Get scaling trends and analytics"""
    try:
        cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)
        
        # Get recent events
        recent_events = [
            event for event in auto_scaling_hr.agent_lifecycle_events.values()
            if event.event_date >= cutoff_date
        ]
        
        # Calculate trends
        hires = len([e for e in recent_events if e.event_type == "hired"])
        terminations = len([e for e in recent_events if e.event_type == "terminated"])
        promotions = len([e for e in recent_events if e.event_type == "promoted"])
        
        # Get recent recommendations
        recent_recommendations = [
            rec for rec in auto_scaling_hr.scaling_recommendations.values()
            if rec.created_at >= cutoff_date
        ]
        
        # Calculate recommendation stats
        total_recommendations = len(recent_recommendations)
        approved_recommendations = len([r for r in recent_recommendations if r.status == "approved"])
        rejected_recommendations = len([r for r in recent_recommendations if r.status == "rejected"])
        pending_recommendations = len([r for r in recent_recommendations if r.status == "pending"])
        
        # Calculate cost impact
        total_cost_impact = sum(rec.cost_impact for rec in recent_recommendations)
        
        return {
            "period_days": days,
            "scaling_activity": {
                "hires": hires,
                "terminations": terminations,
                "promotions": promotions,
                "net_growth": hires - terminations
            },
            "recommendations": {
                "total": total_recommendations,
                "approved": approved_recommendations,
                "rejected": rejected_recommendations,
                "pending": pending_recommendations,
                "approval_rate": approved_recommendations / max(total_recommendations, 1)
            },
            "financial_impact": {
                "total_cost_impact": total_cost_impact,
                "avg_cost_per_recommendation": total_cost_impact / max(total_recommendations, 1)
            },
            "trigger_distribution": {
                trigger.value: len([r for r in recent_recommendations if r.trigger == trigger])
                for trigger in ScalingTrigger
            }
        }
    except Exception as e:
        logger.log_error(e, {"action": "get_scaling_trends"})
        raise HTTPException(status_code=500, detail="Failed to get scaling trends")


@router.get("/analytics/performance-impact")
async def get_performance_impact():
    """Get performance impact of scaling decisions"""
    try:
        # This would calculate the performance impact of recent scaling decisions
        # For now, return simulated data
        return {
            "overall_performance_change": 0.15,  # 15% improvement
            "productivity_improvement": 0.22,     # 22% improvement
            "cost_efficiency_change": -0.08,     # 8% cost reduction
            "employee_satisfaction": 0.85,       # 85% satisfaction
            "retention_rate": 0.92,              # 92% retention
            "time_to_productivity": 14,          # 14 days average
            "scaling_success_rate": 0.78         # 78% of scaling actions successful
        }
    except Exception as e:
        logger.log_error(e, {"action": "get_performance_impact"})
        raise HTTPException(status_code=500, detail="Failed to get performance impact")