"""
Organizational Hierarchy Service
Manages organizational structure, authority, accountability, and governance
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from models.organizational_hierarchy import (
    OrganizationChart, OrganizationalPosition, AuthorityLevel, DecisionType,
    ApprovalRequest, ApprovalStatus, DelegatedTask, PerformanceReview,
    EscalationRule, ComplianceRule, AuditTrail, OrganizationalMetrics,
    PerformanceRating
)
from models.agent import Agent, AgentRole, AgentStatus
from services.inter_agent_communication import inter_agent_comm, MessagePriority
from services.talent_pool import talent_pool
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class OrganizationalHierarchyService:
    """Service managing organizational structure and accountability"""
    
    def __init__(self):
        self.org_chart: Optional[OrganizationChart] = None
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.delegated_tasks: Dict[str, DelegatedTask] = {}
        self.performance_reviews: Dict[str, PerformanceReview] = {}
        self.audit_trail: List[AuditTrail] = []
        self.metrics_history: List[OrganizationalMetrics] = []
        
        # Authority matrix - defines what each level can approve
        self.authority_matrix = {
            AuthorityLevel.EXECUTIVE: {
                "budget_limit": 1000000,
                "can_approve": list(DecisionType),
                "can_delegate_to": [AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.MIDDLE_MANAGEMENT],
                "requires_approval_for": []
            },
            AuthorityLevel.SENIOR_MANAGEMENT: {
                "budget_limit": 100000,
                "can_approve": [DecisionType.OPERATIONAL, DecisionType.TECHNICAL, DecisionType.HIRING],
                "can_delegate_to": [AuthorityLevel.MIDDLE_MANAGEMENT, AuthorityLevel.INDIVIDUAL_CONTRIBUTOR],
                "requires_approval_for": [DecisionType.STRATEGIC, DecisionType.POLICY]
            },
            AuthorityLevel.MIDDLE_MANAGEMENT: {
                "budget_limit": 25000,
                "can_approve": [DecisionType.OPERATIONAL, DecisionType.TECHNICAL],
                "can_delegate_to": [AuthorityLevel.INDIVIDUAL_CONTRIBUTOR],
                "requires_approval_for": [DecisionType.STRATEGIC, DecisionType.BUDGET, DecisionType.HIRING, DecisionType.POLICY]
            },
            AuthorityLevel.INDIVIDUAL_CONTRIBUTOR: {
                "budget_limit": 5000,
                "can_approve": [],
                "can_delegate_to": [],
                "requires_approval_for": [DecisionType.STRATEGIC, DecisionType.BUDGET, DecisionType.HIRING, DecisionType.POLICY, DecisionType.TECHNICAL]
            },
            AuthorityLevel.INTERN: {
                "budget_limit": 500,
                "can_approve": [],
                "can_delegate_to": [],
                "requires_approval_for": list(DecisionType)
            }
        }
    
    async def initialize(self):
        """Initialize the organizational hierarchy"""
        logger.log_system_event("organizational_hierarchy_initializing", {})
        
        # Create the organizational structure
        await self._create_initial_org_chart()
        
        # Set up default compliance and escalation rules
        await self._setup_governance_rules()
        
        # Start monitoring processes
        asyncio.create_task(self._monitor_approvals())
        asyncio.create_task(self._monitor_performance())
        
        logger.log_system_event("organizational_hierarchy_initialized", {
            "total_positions": len(self.org_chart.positions),
            "departments": len(self.org_chart.departments),
            "compliance_rules": len(self.org_chart.compliance_rules)
        })
    
    async def _create_initial_org_chart(self):
        """Create the initial organizational chart"""
        self.org_chart = OrganizationChart(
            id=str(uuid.uuid4()),
            name="ARTAC Autonomous Organization"
        )
        
        # Define the organizational structure
        org_structure = {
            "ceo-001": {
                "title": "Chief Executive Officer",
                "authority_level": AuthorityLevel.EXECUTIVE,
                "department": "Executive",
                "reports_to": None,
                "role": AgentRole.CEO
            },
            # Department heads reporting to CEO
            "cto-001": {
                "title": "Chief Technology Officer", 
                "authority_level": AuthorityLevel.SENIOR_MANAGEMENT,
                "department": "Technology",
                "reports_to": "ceo-001",
                "role": AgentRole.DEVELOPER
            },
            "head-security-001": {
                "title": "Head of Security",
                "authority_level": AuthorityLevel.SENIOR_MANAGEMENT,
                "department": "Security",
                "reports_to": "ceo-001", 
                "role": AgentRole.SECURITY
            },
            "head-ops-001": {
                "title": "Head of Operations",
                "authority_level": AuthorityLevel.SENIOR_MANAGEMENT,
                "department": "Operations",
                "reports_to": "ceo-001",
                "role": AgentRole.DEVOPS
            }
        }
        
        # Create positions for existing agents
        all_agents = talent_pool.get_all_agents()
        
        for agent in all_agents:
            # Use predefined structure if exists, otherwise create based on role
            if agent.id in org_structure:
                position_data = org_structure[agent.id]
            else:
                position_data = self._get_default_position_for_role(agent.role, agent.id)
            
            position = OrganizationalPosition(
                agent_id=agent.id,
                title=position_data["title"],
                authority_level=position_data["authority_level"],
                department=position_data["department"],
                reports_to=position_data.get("reports_to"),
                can_approve=self.authority_matrix[position_data["authority_level"]]["can_approve"],
                budget_authority=self.authority_matrix[position_data["authority_level"]]["budget_limit"]
            )
            
            self.org_chart.positions[agent.id] = position
        
        # Build reporting chains and department structures
        await self._build_reporting_chains()
        await self._build_department_structure()
        
        # Set up approval matrix
        self._setup_approval_matrix()
    
    def _get_default_position_for_role(self, role: AgentRole, agent_id: str) -> Dict[str, Any]:
        """Get default organizational position for an agent role"""
        role_mappings = {
            AgentRole.CEO: {
                "title": "Chief Executive Officer",
                "authority_level": AuthorityLevel.EXECUTIVE,
                "department": "Executive",
                "reports_to": None
            },
            AgentRole.DEVELOPER: {
                "title": "Senior Developer",
                "authority_level": AuthorityLevel.MIDDLE_MANAGEMENT,
                "department": "Technology", 
                "reports_to": "cto-001"
            },
            AgentRole.DEVOPS: {
                "title": "DevOps Engineer",
                "authority_level": AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
                "department": "Operations",
                "reports_to": "head-ops-001"
            },
            AgentRole.SECURITY: {
                "title": "Security Specialist",
                "authority_level": AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
                "department": "Security",
                "reports_to": "head-security-001"
            },
            AgentRole.DESIGNER: {
                "title": "UX/UI Designer",
                "authority_level": AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
                "department": "Design",
                "reports_to": "cto-001"
            },
            AgentRole.TESTER: {
                "title": "QA Engineer",
                "authority_level": AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
                "department": "Quality",
                "reports_to": "cto-001"
            },
            AgentRole.ANALYST: {
                "title": "Business Analyst",
                "authority_level": AuthorityLevel.MIDDLE_MANAGEMENT,
                "department": "Strategy",
                "reports_to": "ceo-001"
            }
        }
        
        return role_mappings.get(role, {
            "title": f"{role.value.title()} Specialist",
            "authority_level": AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
            "department": "General",
            "reports_to": "ceo-001"
        })
    
    async def _build_reporting_chains(self):
        """Build the reporting chain hierarchy"""
        self.org_chart.reporting_chains = {}
        
        for agent_id, position in self.org_chart.positions.items():
            chain = []
            current_id = agent_id
            
            # Build chain going up the hierarchy
            while current_id:
                chain.append(current_id)
                current_position = self.org_chart.positions.get(current_id)
                if current_position and current_position.reports_to:
                    current_id = current_position.reports_to
                else:
                    break
            
            self.org_chart.reporting_chains[agent_id] = chain
            
            # Update direct reports for managers
            if position.reports_to:
                manager_position = self.org_chart.positions.get(position.reports_to)
                if manager_position and agent_id not in manager_position.direct_reports:
                    manager_position.direct_reports.append(agent_id)
    
    async def _build_department_structure(self):
        """Build department organization"""
        self.org_chart.departments = defaultdict(list)
        
        for agent_id, position in self.org_chart.positions.items():
            self.org_chart.departments[position.department].append(agent_id)
    
    def _setup_approval_matrix(self):
        """Set up the approval matrix for different decision types"""
        self.org_chart.approval_matrix = {
            DecisionType.STRATEGIC: [AuthorityLevel.EXECUTIVE],
            DecisionType.BUDGET: [AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.EXECUTIVE],
            DecisionType.HIRING: [AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.EXECUTIVE],
            DecisionType.OPERATIONAL: [AuthorityLevel.MIDDLE_MANAGEMENT, AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.EXECUTIVE],
            DecisionType.TECHNICAL: [AuthorityLevel.MIDDLE_MANAGEMENT, AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.EXECUTIVE],
            DecisionType.POLICY: [AuthorityLevel.EXECUTIVE],
            DecisionType.EMERGENCY: [AuthorityLevel.MIDDLE_MANAGEMENT, AuthorityLevel.SENIOR_MANAGEMENT, AuthorityLevel.EXECUTIVE]
        }
    
    async def _setup_governance_rules(self):
        """Set up default governance and compliance rules"""
        # Escalation rules
        escalation_rules = [
            EscalationRule(
                id=str(uuid.uuid4()),
                name="Budget Approval Timeout",
                description="Escalate budget approvals that haven't been reviewed within 24 hours",
                trigger_conditions={"type": "timeout", "hours": 24, "decision_type": "budget"},
                escalate_to_level=AuthorityLevel.EXECUTIVE,
                notification_template="Budget approval request has been pending for 24 hours and requires immediate attention.",
                auto_escalate_after_hours=24
            ),
            EscalationRule(
                id=str(uuid.uuid4()),
                name="Emergency Decision Escalation",
                description="Immediately escalate emergency decisions to senior management",
                trigger_conditions={"type": "priority", "priority": "urgent", "decision_type": "emergency"},
                escalate_to_level=AuthorityLevel.SENIOR_MANAGEMENT,
                notification_template="Emergency decision requires immediate senior management attention.",
                auto_escalate_after_hours=1
            )
        ]
        
        # Compliance rules
        compliance_rules = [
            ComplianceRule(
                id=str(uuid.uuid4()),
                name="Budget Authority Compliance",
                description="Ensure agents don't approve budgets beyond their authority",
                rule_type="restriction",
                applies_to_levels=list(AuthorityLevel),
                applies_to_decisions=[DecisionType.BUDGET],
                requirements={"check_budget_limit": True, "require_documentation": True},
                violations_threshold=1,
                penalty_actions=["warning", "authority_review", "escalation"]
            ),
            ComplianceRule(
                id=str(uuid.uuid4()),
                name="Decision Documentation",
                description="All strategic decisions must be documented with justification",
                rule_type="audit",
                applies_to_decisions=[DecisionType.STRATEGIC, DecisionType.POLICY],
                requirements={"require_justification": True, "min_justification_length": 100},
                violations_threshold=2,
                penalty_actions=["reminder", "training_required"]
            )
        ]
        
        self.org_chart.escalation_rules = escalation_rules
        self.org_chart.compliance_rules = compliance_rules
    
    async def request_approval(self, requesting_agent_id: str, decision_type: DecisionType,
                             title: str, description: str, justification: str,
                             requested_amount: Optional[int] = None,
                             priority: str = "normal") -> str:
        """Request approval for a decision"""
        
        # Determine required approval level
        required_level = self._get_required_approval_level(decision_type, requested_amount)
        
        # Find appropriate approver
        approver_id = await self._find_approver(requesting_agent_id, required_level)
        
        if not approver_id:
            raise ValueError(f"No approver found for {decision_type.value} decision")
        
        # Create approval request
        request_id = str(uuid.uuid4())
        approval_request = ApprovalRequest(
            id=request_id,
            requesting_agent_id=requesting_agent_id,
            decision_type=decision_type,
            title=title,
            description=description,
            justification=justification,
            requested_amount=requested_amount,
            priority=priority,
            required_approver_level=required_level,
            current_approver_id=approver_id
        )
        
        self.approval_requests[request_id] = approval_request
        self.org_chart.pending_approvals.append(request_id)
        
        # Send approval request to approver
        await self._send_approval_notification(approval_request)
        
        # Log audit trail
        await self._log_audit_event(
            requesting_agent_id,
            "approval_request",
            f"Requested approval for {decision_type.value}: {title}",
            {"request_id": request_id, "approver": approver_id, "amount": requested_amount}
        )
        
        logger.log_system_event("approval_requested", {
            "request_id": request_id,
            "requesting_agent": requesting_agent_id,
            "approver": approver_id,
            "decision_type": decision_type.value,
            "priority": priority
        })
        
        return request_id
    
    def _get_required_approval_level(self, decision_type: DecisionType, 
                                   amount: Optional[int] = None) -> AuthorityLevel:
        """Determine the required approval level for a decision"""
        
        # Check if it's a budget decision with specific amount requirements
        if decision_type == DecisionType.BUDGET and amount:
            if amount > 100000:
                return AuthorityLevel.EXECUTIVE
            elif amount > 25000:
                return AuthorityLevel.SENIOR_MANAGEMENT
            elif amount > 5000:
                return AuthorityLevel.MIDDLE_MANAGEMENT
            else:
                return AuthorityLevel.INDIVIDUAL_CONTRIBUTOR
        
        # Use approval matrix for other decisions
        required_levels = self.org_chart.approval_matrix.get(decision_type, [AuthorityLevel.EXECUTIVE])
        return min(required_levels)  # Get the lowest level that can approve
    
    async def _find_approver(self, requesting_agent_id: str, 
                           required_level: AuthorityLevel) -> Optional[str]:
        """Find an appropriate approver for the request"""
        requesting_position = self.org_chart.positions.get(requesting_agent_id)
        if not requesting_position:
            return None
        
        # Go up the reporting chain to find someone with required authority
        chain = self.org_chart.reporting_chains.get(requesting_agent_id, [])
        
        for agent_id in chain[1:]:  # Skip the requesting agent themselves
            position = self.org_chart.positions.get(agent_id)
            if position and position.authority_level == required_level:
                return agent_id
        
        # If no one in chain has required level, find anyone with that level
        for agent_id, position in self.org_chart.positions.items():
            if position.authority_level == required_level:
                return agent_id
        
        return None
    
    async def _send_approval_notification(self, request: ApprovalRequest):
        """Send approval request notification to the approver"""
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "urgent": MessagePriority.URGENT
        }
        
        message_content = f"""
APPROVAL REQUEST

Title: {request.title}
Type: {request.decision_type.value.title()}
Requested by: {request.requesting_agent_id}
Priority: {request.priority.upper()}

Description:
{request.description}

Justification:
{request.justification}

{f"Requested Amount: ${request.requested_amount:,}" if request.requested_amount else ""}

Please review and respond with APPROVE or REJECT along with your reasoning.
Request ID: {request.id}
"""
        
        await inter_agent_comm.send_direct_message(
            from_agent_id="system",
            to_agent_id=request.current_approver_id,
            subject=f"APPROVAL NEEDED: {request.title}",
            content=message_content,
            priority=priority_map.get(request.priority, MessagePriority.NORMAL),
            metadata={"approval_request_id": request.id, "decision_type": request.decision_type.value}
        )
    
    async def approve_request(self, approver_id: str, request_id: str, 
                            reasoning: str) -> bool:
        """Approve an approval request"""
        request = self.approval_requests.get(request_id)
        if not request:
            return False
        
        if request.current_approver_id != approver_id:
            return False
        
        # Check if approver has authority
        approver_position = self.org_chart.positions.get(approver_id)
        if not approver_position:
            return False
        
        # Verify authority level
        if not self._has_approval_authority(approver_position, request.decision_type, request.requested_amount):
            # Escalate to higher authority
            return await self._escalate_request(request_id, "Insufficient authority level")
        
        # Approve the request
        request.status = ApprovalStatus.APPROVED
        request.approval_chain.append(approver_id)
        request.updated_at = datetime.now()
        
        # Remove from pending
        if request_id in self.org_chart.pending_approvals:
            self.org_chart.pending_approvals.remove(request_id)
        
        # Notify requester
        await inter_agent_comm.send_direct_message(
            from_agent_id=approver_id,
            to_agent_id=request.requesting_agent_id,
            subject=f"APPROVED: {request.title}",
            content=f"Your request has been approved.\n\nApprover reasoning: {reasoning}",
            priority=MessagePriority.HIGH,
            metadata={"approval_request_id": request_id, "status": "approved"}
        )
        
        # Log audit event
        await self._log_audit_event(
            approver_id,
            "approval_granted",
            f"Approved {request.decision_type.value}: {request.title}",
            {"request_id": request_id, "requester": request.requesting_agent_id, "reasoning": reasoning}
        )
        
        logger.log_system_event("approval_granted", {
            "request_id": request_id,
            "approver": approver_id,
            "requester": request.requesting_agent_id,
            "decision_type": request.decision_type.value
        })
        
        return True
    
    async def reject_request(self, approver_id: str, request_id: str, 
                           reasoning: str) -> bool:
        """Reject an approval request"""
        request = self.approval_requests.get(request_id)
        if not request or request.current_approver_id != approver_id:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reasoning
        request.updated_at = datetime.now()
        
        # Remove from pending
        if request_id in self.org_chart.pending_approvals:
            self.org_chart.pending_approvals.remove(request_id)
        
        # Notify requester
        await inter_agent_comm.send_direct_message(
            from_agent_id=approver_id,
            to_agent_id=request.requesting_agent_id,
            subject=f"REJECTED: {request.title}",
            content=f"Your request has been rejected.\n\nReason: {reasoning}",
            priority=MessagePriority.HIGH,
            metadata={"approval_request_id": request_id, "status": "rejected"}
        )
        
        # Log audit event
        await self._log_audit_event(
            approver_id,
            "approval_rejected",
            f"Rejected {request.decision_type.value}: {request.title}",
            {"request_id": request_id, "requester": request.requesting_agent_id, "reasoning": reasoning}
        )
        
        return True
    
    def _has_approval_authority(self, position: OrganizationalPosition, 
                              decision_type: DecisionType, amount: Optional[int] = None) -> bool:
        """Check if a position has authority to approve a decision"""
        
        # Check decision type authority
        if decision_type not in position.can_approve:
            return False
        
        # Check budget authority if applicable
        if decision_type == DecisionType.BUDGET and amount:
            return amount <= position.budget_authority
        
        return True
    
    async def delegate_task(self, delegator_id: str, delegate_to_id: str,
                          task_id: str, title: str, description: str,
                          deadline: Optional[datetime] = None,
                          authority_granted: List[str] = None) -> str:
        """Delegate a task down the hierarchy"""
        
        # Verify delegation authority
        if not await self._can_delegate_to(delegator_id, delegate_to_id):
            raise ValueError("Cannot delegate to this agent - not in reporting chain")
        
        delegation_id = str(uuid.uuid4())
        delegated_task = DelegatedTask(
            id=delegation_id,
            task_id=task_id,
            delegated_by=delegator_id,
            delegated_to=delegate_to_id,
            title=title,
            description=description,
            deadline=deadline,
            authority_granted=authority_granted or []
        )
        
        self.delegated_tasks[delegation_id] = delegated_task
        self.org_chart.active_delegations.append(delegation_id)
        
        # Notify delegate
        await inter_agent_comm.send_direct_message(
            from_agent_id=delegator_id,
            to_agent_id=delegate_to_id,
            subject=f"TASK DELEGATED: {title}",
            content=f"You have been assigned a new task:\n\n{description}\n\nDeadline: {deadline}\nAuthority granted: {', '.join(authority_granted or ['None'])}",
            priority=MessagePriority.HIGH,
            metadata={"delegation_id": delegation_id, "task_id": task_id}
        )
        
        # Log audit event
        await self._log_audit_event(
            delegator_id,
            "task_delegated",
            f"Delegated task: {title}",
            {"delegation_id": delegation_id, "delegate": delegate_to_id, "task_id": task_id}
        )
        
        return delegation_id
    
    async def _can_delegate_to(self, delegator_id: str, delegate_to_id: str) -> bool:
        """Check if delegator can delegate to the specified agent"""
        delegator_position = self.org_chart.positions.get(delegator_id)
        delegate_position = self.org_chart.positions.get(delegate_to_id)
        
        if not delegator_position or not delegate_position:
            return False
        
        # Check if delegate is in delegator's reporting chain or direct reports
        return (delegate_to_id in delegator_position.direct_reports or
                delegate_to_id in self.org_chart.reporting_chains.get(delegator_id, []))
    
    async def _monitor_approvals(self):
        """Monitor approval requests for timeouts and escalations"""
        while True:
            try:
                current_time = datetime.now()
                
                for request_id, request in self.approval_requests.items():
                    if request.status != ApprovalStatus.PENDING:
                        continue
                    
                    # Check for timeout
                    hours_since_request = (current_time - request.created_at).total_seconds() / 3600
                    
                    # Apply escalation rules
                    for rule in self.org_chart.escalation_rules:
                        if self._should_escalate(request, rule, hours_since_request):
                            await self._escalate_request(request_id, f"Auto-escalation: {rule.name}")
                            break
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in approval monitoring: {e}")
                await asyncio.sleep(3600)
    
    def _should_escalate(self, request: ApprovalRequest, rule: EscalationRule, 
                        hours_elapsed: float) -> bool:
        """Check if a request should be escalated based on rules"""
        if not rule.active:
            return False
        
        conditions = rule.trigger_conditions
        
        if conditions.get("type") == "timeout":
            required_hours = conditions.get("hours", 24)
            if hours_elapsed >= required_hours:
                return True
        
        if conditions.get("type") == "priority":
            if request.priority == conditions.get("priority"):
                return True
        
        return False
    
    async def _escalate_request(self, request_id: str, reason: str) -> bool:
        """Escalate an approval request to higher authority"""
        request = self.approval_requests.get(request_id)
        if not request:
            return False
        
        # Find next level approver
        current_approver = self.org_chart.positions.get(request.current_approver_id)
        if not current_approver or not current_approver.reports_to:
            return False
        
        # Update request
        request.status = ApprovalStatus.ESCALATED
        request.escalation_reason = reason
        request.current_approver_id = current_approver.reports_to
        request.updated_at = datetime.now()
        
        # Send escalation notification
        await self._send_approval_notification(request)
        
        logger.log_system_event("approval_escalated", {
            "request_id": request_id,
            "new_approver": request.current_approver_id,
            "reason": reason
        })
        
        return True
    
    async def _monitor_performance(self):
        """Monitor performance and generate metrics"""
        while True:
            try:
                await self._generate_organizational_metrics()
                await asyncio.sleep(86400)  # Generate daily metrics
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(86400)
    
    async def _generate_organizational_metrics(self):
        """Generate organizational performance metrics"""
        metrics_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Calculate various metrics
        metrics = OrganizationalMetrics(
            id=metrics_id,
            reporting_period=current_time.strftime("%Y-%m-%d"),
            avg_decision_time=self._calculate_avg_decision_time(),
            escalation_rate=self._calculate_escalation_rate(),
            delegation_effectiveness=self._calculate_delegation_effectiveness(),
            policy_adherence_rate=self._calculate_compliance_rate(),
            generated_at=current_time,
            generated_by="system"
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only last 30 days of metrics
        cutoff_date = current_time - timedelta(days=30)
        self.metrics_history = [m for m in self.metrics_history if m.generated_at >= cutoff_date]
    
    def _calculate_avg_decision_time(self) -> float:
        """Calculate average time to approve decisions"""
        completed_requests = [r for r in self.approval_requests.values() 
                            if r.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]]
        
        if not completed_requests:
            return 0.0
        
        total_time = sum((r.updated_at - r.created_at).total_seconds() for r in completed_requests)
        return total_time / len(completed_requests) / 3600  # Convert to hours
    
    def _calculate_escalation_rate(self) -> float:
        """Calculate percentage of requests that get escalated"""
        total_requests = len(self.approval_requests)
        if total_requests == 0:
            return 0.0
        
        escalated_requests = len([r for r in self.approval_requests.values() 
                                if r.status == ApprovalStatus.ESCALATED])
        return (escalated_requests / total_requests) * 100
    
    def _calculate_delegation_effectiveness(self) -> float:
        """Calculate success rate of delegated tasks"""
        completed_delegations = [d for d in self.delegated_tasks.values() 
                               if d.status == "completed"]
        total_delegations = len(self.delegated_tasks)
        
        if total_delegations == 0:
            return 0.0
        
        return (len(completed_delegations) / total_delegations) * 100
    
    def _calculate_compliance_rate(self) -> float:
        """Calculate compliance with organizational policies"""
        total_actions = len(self.audit_trail)
        if total_actions == 0:
            return 100.0
        
        compliant_actions = len([a for a in self.audit_trail 
                               if a.compliance_status == "compliant"])
        return (compliant_actions / total_actions) * 100
    
    async def _log_audit_event(self, agent_id: str, action_type: str, 
                             description: str, data: Dict[str, Any]):
        """Log an audit event for accountability tracking"""
        audit_event = AuditTrail(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            action_type=action_type,
            action_description=description,
            decision_data=data,
            timestamp=datetime.now()
        )
        
        self.audit_trail.append(audit_event)
        
        # Keep only last 1000 audit events to prevent memory issues
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]
    
    # Public methods for accessing organizational information
    
    def get_reporting_chain(self, agent_id: str) -> List[str]:
        """Get the reporting chain for an agent"""
        return self.org_chart.reporting_chains.get(agent_id, [])
    
    def get_direct_reports(self, agent_id: str) -> List[str]:
        """Get direct reports for an agent"""
        position = self.org_chart.positions.get(agent_id)
        return position.direct_reports if position else []
    
    def get_authority_level(self, agent_id: str) -> Optional[AuthorityLevel]:
        """Get authority level for an agent"""
        position = self.org_chart.positions.get(agent_id)
        return position.authority_level if position else None
    
    def can_approve_decision(self, agent_id: str, decision_type: DecisionType, 
                           amount: Optional[int] = None) -> bool:
        """Check if an agent can approve a specific decision"""
        position = self.org_chart.positions.get(agent_id)
        if not position:
            return False
        
        return self._has_approval_authority(position, decision_type, amount)
    
    def get_pending_approvals_for_agent(self, agent_id: str) -> List[ApprovalRequest]:
        """Get pending approval requests for an agent"""
        return [r for r in self.approval_requests.values() 
                if r.current_approver_id == agent_id and r.status == ApprovalStatus.PENDING]
    
    def get_organizational_metrics(self) -> Optional[OrganizationalMetrics]:
        """Get the latest organizational metrics"""
        return self.metrics_history[-1] if self.metrics_history else None


# Global service instance
org_hierarchy = OrganizationalHierarchyService()