"""
Organizational Hierarchy API Endpoints
Provides REST API for organizational structure, approvals, delegation, and accountability
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.organizational_hierarchy import org_hierarchy
from models.organizational_hierarchy import (
    DecisionType, AuthorityLevel, ApprovalStatus, PerformanceRating,
    OrganizationalPosition, ApprovalRequest, DelegatedTask, 
    OrganizationalMetrics, AuditTrail
)
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class ApprovalRequestModel(BaseModel):
    decision_type: DecisionType
    title: str
    description: str
    justification: str
    requested_amount: Optional[int] = None
    priority: str = "normal"


class ApprovalResponseModel(BaseModel):
    request_id: str
    action: str  # "approve" or "reject"
    reasoning: str


class DelegationRequestModel(BaseModel):
    delegate_to_id: str
    task_id: str
    title: str
    description: str
    deadline: Optional[datetime] = None
    authority_granted: Optional[List[str]] = None


class PerformanceReviewModel(BaseModel):
    agent_id: str
    review_period_start: datetime
    review_period_end: datetime
    overall_rating: PerformanceRating
    tasks_completed: int = 0
    tasks_on_time: int = 0
    quality_score: float = 0.0
    collaboration_score: float = 0.0
    leadership_score: float = 0.0
    goals_achieved: List[str] = []
    strengths: List[str] = []
    development_areas: List[str] = []
    improvement_plan: List[str] = []


# Organizational Structure Endpoints
@router.get("/org-chart")
async def get_organizational_chart():
    """Get the complete organizational chart"""
    if not org_hierarchy.org_chart:
        raise HTTPException(status_code=404, detail="Organizational chart not initialized")
    
    return {
        "id": org_hierarchy.org_chart.id,
        "name": org_hierarchy.org_chart.name,
        "version": org_hierarchy.org_chart.version,
        "positions": len(org_hierarchy.org_chart.positions),
        "departments": list(org_hierarchy.org_chart.departments.keys()),
        "pending_approvals": len(org_hierarchy.org_chart.pending_approvals),
        "active_delegations": len(org_hierarchy.org_chart.active_delegations),
        "last_updated": org_hierarchy.org_chart.last_updated
    }


@router.get("/positions/{agent_id}", response_model=OrganizationalPosition)
async def get_agent_position(agent_id: str):
    """Get organizational position for a specific agent"""
    if not org_hierarchy.org_chart:
        raise HTTPException(status_code=404, detail="Organizational chart not initialized")
    
    position = org_hierarchy.org_chart.positions.get(agent_id)
    if not position:
        raise HTTPException(status_code=404, detail="Agent position not found")
    
    return position


@router.get("/reporting-chain/{agent_id}")
async def get_reporting_chain(agent_id: str):
    """Get the reporting chain for an agent"""
    chain = org_hierarchy.get_reporting_chain(agent_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Agent not found in organization")
    
    # Get position details for each agent in chain
    chain_details = []
    for agent_id_in_chain in chain:
        position = org_hierarchy.org_chart.positions.get(agent_id_in_chain)
        if position:
            chain_details.append({
                "agent_id": agent_id_in_chain,
                "title": position.title,
                "authority_level": position.authority_level.value,
                "department": position.department
            })
    
    return {"reporting_chain": chain_details}


@router.get("/direct-reports/{agent_id}")
async def get_direct_reports(agent_id: str):
    """Get direct reports for an agent"""
    reports = org_hierarchy.get_direct_reports(agent_id)
    
    # Get position details for each direct report
    report_details = []
    for report_id in reports:
        position = org_hierarchy.org_chart.positions.get(report_id)
        if position:
            report_details.append({
                "agent_id": report_id,
                "title": position.title,
                "authority_level": position.authority_level.value,
                "department": position.department
            })
    
    return {"direct_reports": report_details}


@router.get("/departments")
async def get_departments():
    """Get all departments and their members"""
    if not org_hierarchy.org_chart:
        raise HTTPException(status_code=404, detail="Organizational chart not initialized")
    
    departments = {}
    for dept_name, agent_ids in org_hierarchy.org_chart.departments.items():
        departments[dept_name] = []
        for agent_id in agent_ids:
            position = org_hierarchy.org_chart.positions.get(agent_id)
            if position:
                departments[dept_name].append({
                    "agent_id": agent_id,
                    "title": position.title,
                    "authority_level": position.authority_level.value
                })
    
    return {"departments": departments}


# Approval Workflow Endpoints
@router.post("/approvals/request")
async def request_approval(agent_id: str, request: ApprovalRequestModel):
    """Request approval for a decision"""
    try:
        request_id = await org_hierarchy.request_approval(
            requesting_agent_id=agent_id,
            decision_type=request.decision_type,
            title=request.title,
            description=request.description,
            justification=request.justification,
            requested_amount=request.requested_amount,
            priority=request.priority
        )
        
        return {"success": True, "request_id": request_id}
        
    except Exception as e:
        logger.log_error(e, {"action": "request_approval"})
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/respond")
async def respond_to_approval(agent_id: str, response: ApprovalResponseModel):
    """Respond to an approval request (approve or reject)"""
    try:
        if response.action.lower() == "approve":
            success = await org_hierarchy.approve_request(
                approver_id=agent_id,
                request_id=response.request_id,
                reasoning=response.reasoning
            )
        elif response.action.lower() == "reject":
            success = await org_hierarchy.reject_request(
                approver_id=agent_id,
                request_id=response.request_id,
                reasoning=response.reasoning
            )
        else:
            raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
        
        if success:
            return {"success": True, "message": f"Request {response.action.lower()}ed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to process approval response")
            
    except Exception as e:
        logger.log_error(e, {"action": "respond_to_approval"})
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/approvals/pending/{agent_id}")
async def get_pending_approvals(agent_id: str):
    """Get pending approval requests for an agent"""
    pending_requests = org_hierarchy.get_pending_approvals_for_agent(agent_id)
    
    return {
        "pending_approvals": [
            {
                "id": req.id,
                "requesting_agent_id": req.requesting_agent_id,
                "decision_type": req.decision_type.value,
                "title": req.title,
                "description": req.description,
                "justification": req.justification,
                "requested_amount": req.requested_amount,
                "priority": req.priority,
                "created_at": req.created_at,
                "deadline": req.deadline
            }
            for req in pending_requests
        ]
    }


@router.get("/approvals/{request_id}")
async def get_approval_request(request_id: str):
    """Get details of a specific approval request"""
    request = org_hierarchy.approval_requests.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return {
        "id": request.id,
        "requesting_agent_id": request.requesting_agent_id,
        "decision_type": request.decision_type.value,
        "title": request.title,
        "description": request.description,
        "justification": request.justification,
        "requested_amount": request.requested_amount,
        "priority": request.priority,
        "status": request.status.value,
        "current_approver_id": request.current_approver_id,
        "approval_chain": request.approval_chain,
        "rejection_reason": request.rejection_reason,
        "escalation_reason": request.escalation_reason,
        "created_at": request.created_at,
        "updated_at": request.updated_at
    }


# Delegation Endpoints
@router.post("/delegation/delegate")
async def delegate_task(agent_id: str, delegation: DelegationRequestModel):
    """Delegate a task to another agent"""
    try:
        delegation_id = await org_hierarchy.delegate_task(
            delegator_id=agent_id,
            delegate_to_id=delegation.delegate_to_id,
            task_id=delegation.task_id,
            title=delegation.title,
            description=delegation.description,
            deadline=delegation.deadline,
            authority_granted=delegation.authority_granted
        )
        
        return {"success": True, "delegation_id": delegation_id}
        
    except Exception as e:
        logger.log_error(e, {"action": "delegate_task"})
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/delegation/received/{agent_id}")
async def get_delegated_tasks(agent_id: str, status: Optional[str] = Query(None)):
    """Get tasks delegated to an agent"""
    delegated_tasks = [
        task for task in org_hierarchy.delegated_tasks.values()
        if task.delegated_to == agent_id and (not status or task.status == status)
    ]
    
    return {
        "delegated_tasks": [
            {
                "id": task.id,
                "task_id": task.task_id,
                "delegated_by": task.delegated_by,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "deadline": task.deadline,
                "authority_granted": task.authority_granted,
                "status": task.status,
                "delegation_date": task.delegation_date,
                "expected_deliverables": task.expected_deliverables
            }
            for task in delegated_tasks
        ]
    }


@router.get("/delegation/assigned/{agent_id}")
async def get_assigned_delegations(agent_id: str):
    """Get tasks that an agent has delegated to others"""
    assigned_tasks = [
        task for task in org_hierarchy.delegated_tasks.values()
        if task.delegated_by == agent_id
    ]
    
    return {
        "assigned_delegations": [
            {
                "id": task.id,
                "task_id": task.task_id,
                "delegated_to": task.delegated_to,
                "title": task.title,
                "status": task.status,
                "deadline": task.deadline,
                "delegation_date": task.delegation_date,
                "progress_updates": len(task.progress_updates)
            }
            for task in assigned_tasks
        ]
    }


# Authority and Permission Endpoints
@router.get("/authority/{agent_id}")
async def get_agent_authority(agent_id: str):
    """Get authority level and permissions for an agent"""
    position = org_hierarchy.org_chart.positions.get(agent_id) if org_hierarchy.org_chart else None
    if not position:
        raise HTTPException(status_code=404, detail="Agent position not found")
    
    return {
        "agent_id": agent_id,
        "authority_level": position.authority_level.value,
        "budget_authority": position.budget_authority,
        "can_approve": [dt.value for dt in position.can_approve],
        "direct_reports_count": len(position.direct_reports),
        "delegation_level": position.delegation_level
    }


@router.get("/authority/{agent_id}/can-approve")
async def check_approval_authority(
    agent_id: str, 
    decision_type: DecisionType, 
    amount: Optional[int] = Query(None)
):
    """Check if an agent can approve a specific decision"""
    can_approve = org_hierarchy.can_approve_decision(agent_id, decision_type, amount)
    
    authority_level = org_hierarchy.get_authority_level(agent_id)
    
    return {
        "can_approve": can_approve,
        "agent_authority_level": authority_level.value if authority_level else None,
        "decision_type": decision_type.value,
        "requested_amount": amount
    }


# Accountability and Audit Endpoints
@router.get("/audit-trail")
async def get_audit_trail(
    agent_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Get audit trail entries"""
    filtered_entries = org_hierarchy.audit_trail
    
    if agent_id:
        filtered_entries = [e for e in filtered_entries if e.agent_id == agent_id]
    
    if action_type:
        filtered_entries = [e for e in filtered_entries if e.action_type == action_type]
    
    # Sort by timestamp (newest first) and limit
    filtered_entries.sort(key=lambda e: e.timestamp, reverse=True)
    limited_entries = filtered_entries[:limit]
    
    return {
        "audit_entries": [
            {
                "id": entry.id,
                "agent_id": entry.agent_id,
                "action_type": entry.action_type,
                "action_description": entry.action_description,
                "authority_used": entry.authority_used.value if entry.authority_used else None,
                "affected_agents": entry.affected_agents,
                "compliance_status": entry.compliance_status,
                "business_impact": entry.business_impact,
                "timestamp": entry.timestamp
            }
            for entry in limited_entries
        ],
        "total_entries": len(filtered_entries)
    }


@router.get("/metrics/organizational")
async def get_organizational_metrics():
    """Get current organizational performance metrics"""
    metrics = org_hierarchy.get_organizational_metrics()
    if not metrics:
        return {"message": "No metrics available yet"}
    
    return {
        "reporting_period": metrics.reporting_period,
        "avg_decision_time_hours": metrics.avg_decision_time,
        "escalation_rate_percent": metrics.escalation_rate,
        "delegation_effectiveness_percent": metrics.delegation_effectiveness,
        "policy_adherence_rate_percent": metrics.policy_adherence_rate,
        "audit_findings": metrics.audit_findings,
        "compliance_violations": metrics.compliance_violations,
        "generated_at": metrics.generated_at,
        "performance_summary": {
            "overall_productivity": metrics.overall_productivity,
            "cross_team_collaboration": metrics.cross_team_collaboration,
            "communication_efficiency": metrics.communication_efficiency,
            "goal_achievement_rate": metrics.goal_achievement_rate
        }
    }


@router.get("/compliance/status")
async def get_compliance_status():
    """Get current compliance status and violations"""
    if not org_hierarchy.org_chart:
        raise HTTPException(status_code=404, detail="Organizational chart not initialized")
    
    # Count compliance violations from audit trail
    recent_violations = [
        entry for entry in org_hierarchy.audit_trail
        if entry.compliance_status == "violation" and 
        (datetime.now() - entry.timestamp).days <= 30
    ]
    
    # Group violations by agent
    violations_by_agent = {}
    for violation in recent_violations:
        if violation.agent_id not in violations_by_agent:
            violations_by_agent[violation.agent_id] = []
        violations_by_agent[violation.agent_id].append({
            "action_type": violation.action_type,
            "description": violation.action_description,
            "timestamp": violation.timestamp,
            "business_impact": violation.business_impact
        })
    
    return {
        "total_violations_last_30_days": len(recent_violations),
        "agents_with_violations": len(violations_by_agent),
        "compliance_rules_active": len(org_hierarchy.org_chart.compliance_rules),
        "violations_by_agent": violations_by_agent,
        "escalation_rules_active": len(org_hierarchy.org_chart.escalation_rules)
    }


# System Status Endpoints
@router.get("/status")
async def get_hierarchy_status():
    """Get organizational hierarchy system status"""
    if not org_hierarchy.org_chart:
        return {"status": "not_initialized", "message": "Organizational hierarchy not initialized"}
    
    return {
        "status": "operational",
        "org_chart_id": org_hierarchy.org_chart.id,
        "total_positions": len(org_hierarchy.org_chart.positions),
        "total_departments": len(org_hierarchy.org_chart.departments),
        "pending_approvals": len(org_hierarchy.org_chart.pending_approvals),
        "active_delegations": len(org_hierarchy.org_chart.active_delegations),
        "total_approval_requests": len(org_hierarchy.approval_requests),
        "total_delegated_tasks": len(org_hierarchy.delegated_tasks),
        "audit_trail_size": len(org_hierarchy.audit_trail),
        "metrics_history_size": len(org_hierarchy.metrics_history),
        "last_updated": org_hierarchy.org_chart.last_updated
    }