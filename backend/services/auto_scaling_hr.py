"""
Auto-scaling HR (AHR) Service
Intelligent organizational scaling based on performance, workload, and strategic needs
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import statistics

from models.auto_scaling_hr import (
    ScalingTrigger, ScalingAction, HiringCriteria, PerformanceThreshold,
    WorkloadMetrics, ScalingRecommendation, SkillGapAnalysis,
    OrganizationalScalingPlan, AutoScalingRule, AgentLifecycleEvent,
    ScalingDashboard
)
from models.agent import Agent, AgentRole, AgentStatus, Skill, SkillLevel, PersonalityTrait
from models.organizational_hierarchy import AuthorityLevel, PerformanceRating
from services.organizational_hierarchy import org_hierarchy
from services.talent_pool import talent_pool
from services.ollama_service import ollama_service
from services.inter_agent_communication import inter_agent_comm, MessagePriority
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class AutoScalingHRService:
    """Intelligent Auto-scaling HR system"""
    
    def __init__(self):
        self.scaling_recommendations: Dict[str, ScalingRecommendation] = {}
        self.workload_metrics_history: List[WorkloadMetrics] = []
        self.skill_gap_analyses: List[SkillGapAnalysis] = []
        self.scaling_plans: Dict[str, OrganizationalScalingPlan] = {}
        self.auto_scaling_rules: Dict[str, AutoScalingRule] = {}
        self.agent_lifecycle_events: List[AgentLifecycleEvent] = {}
        self.performance_thresholds: List[PerformanceThreshold] = []
        
        # Scaling parameters
        self.max_org_size = 200  # Maximum organization size
        self.min_org_size = 3    # Minimum organization size
        self.budget_per_agent = 100000  # Average annual cost per agent
        self.scaling_cooldown_hours = 24  # Minimum time between scaling actions
        
        # Performance monitoring
        self.last_scaling_action = None
        self.scaling_actions_today = 0
        self.daily_scaling_limit = 5
        
    async def initialize(self):
        """Initialize the auto-scaling HR system"""
        logger.log_system_event("ahr_system_initializing", {})
        
        # Set up default performance thresholds
        await self._setup_default_thresholds()
        
        # Set up default auto-scaling rules
        await self._setup_default_scaling_rules()
        
        # Start monitoring loops
        asyncio.create_task(self._performance_monitoring_loop())
        asyncio.create_task(self._workload_monitoring_loop())
        asyncio.create_task(self._skill_gap_monitoring_loop())
        asyncio.create_task(self._scaling_execution_loop())
        
        logger.log_system_event("ahr_system_initialized", {
            "performance_thresholds": len(self.performance_thresholds),
            "auto_scaling_rules": len(self.auto_scaling_rules),
            "max_org_size": self.max_org_size
        })
    
    async def _setup_default_thresholds(self):
        """Set up default performance thresholds for scaling"""
        default_thresholds = [
            PerformanceThreshold(
                metric_name="task_completion_rate",
                threshold_value=0.7,  # Below 70% completion rate
                comparison="below",
                action_to_take=ScalingAction.HIRE_AGENT,
                severity="high"
            ),
            PerformanceThreshold(
                metric_name="capacity_utilization",
                threshold_value=0.9,  # Above 90% utilization
                comparison="above",
                action_to_take=ScalingAction.HIRE_AGENT,
                severity="high"
            ),
            PerformanceThreshold(
                metric_name="error_rate",
                threshold_value=0.1,  # Above 10% error rate
                comparison="above",
                action_to_take=ScalingAction.HIRE_AGENT,
                severity="critical"
            ),
            PerformanceThreshold(
                metric_name="burnout_risk_score",
                threshold_value=0.8,  # Above 80% burnout risk
                comparison="above",
                action_to_take=ScalingAction.HIRE_AGENT,
                severity="critical"
            ),
            PerformanceThreshold(
                metric_name="productivity_trend",
                threshold_value=-0.2,  # 20% decline in productivity
                comparison="below",
                action_to_take=ScalingAction.HIRE_AGENT,
                severity="medium"
            )
        ]
        
        self.performance_thresholds = default_thresholds
    
    async def _setup_default_scaling_rules(self):
        """Set up default auto-scaling rules"""
        rules = [
            AutoScalingRule(
                id=str(uuid.uuid4()),
                name="High Workload Auto-Scale",
                description="Automatically hire agents when department workload exceeds capacity",
                trigger_type=ScalingTrigger.WORKLOAD_OVERFLOW,
                conditions={
                    "capacity_utilization": {"min": 0.85},
                    "overdue_tasks": {"min": 5},
                    "consecutive_periods": 2
                },
                scaling_action=ScalingAction.HIRE_AGENT,
                action_parameters={
                    "priority": "high",
                    "role_preference": "based_on_department"
                },
                requires_approval=True,
                approval_authority=AuthorityLevel.SENIOR_MANAGEMENT,
                created_by="system"
            ),
            AutoScalingRule(
                id=str(uuid.uuid4()),
                name="Performance-Based Termination",
                description="Recommend termination for consistently underperforming agents",
                trigger_type=ScalingTrigger.PERFORMANCE_DECLINE,
                conditions={
                    "performance_rating": {"max": "needs_improvement"},
                    "consecutive_periods": 3,
                    "improvement_plan_failed": True
                },
                scaling_action=ScalingAction.TERMINATE_AGENT,
                action_parameters={
                    "require_documentation": True,
                    "severance_calculation": True
                },
                requires_approval=True,
                approval_authority=AuthorityLevel.EXECUTIVE,
                created_by="system"
            ),
            AutoScalingRule(
                id=str(uuid.uuid4()),
                name="Skill Gap Auto-Hire",
                description="Automatically initiate hiring when critical skills are missing",
                trigger_type=ScalingTrigger.SKILL_GAP,
                conditions={
                    "critical_skill_shortage": True,
                    "impact_score": {"min": 0.7}
                },
                scaling_action=ScalingAction.HIRE_AGENT,
                action_parameters={
                    "skill_targeted": True,
                    "urgency": "high"
                },
                requires_approval=True,
                approval_authority=AuthorityLevel.SENIOR_MANAGEMENT,
                created_by="system"
            ),
            AutoScalingRule(
                id=str(uuid.uuid4()),
                name="Budget Optimization",
                description="Optimize team size when budget constraints are detected",
                trigger_type=ScalingTrigger.BUDGET_OPTIMIZATION,
                conditions={
                    "budget_utilization": {"min": 0.95},
                    "productivity_per_dollar": {"max": "threshold"}
                },
                scaling_action=ScalingAction.TERMINATE_AGENT,
                action_parameters={
                    "target_lowest_performers": True,
                    "cost_benefit_analysis": True
                },
                requires_approval=True,
                approval_authority=AuthorityLevel.EXECUTIVE,
                created_by="system"
            )
        ]
        
        for rule in rules:
            self.auto_scaling_rules[rule.id] = rule
    
    async def _performance_monitoring_loop(self):
        """Monitor agent and organizational performance for scaling triggers"""
        while True:
            try:
                await self._analyze_performance_metrics()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.log_error(e, {"action": "performance_monitoring"})
                await asyncio.sleep(3600)
    
    async def _workload_monitoring_loop(self):
        """Monitor workload across departments for scaling needs"""
        while True:
            try:
                await self._analyze_workload_metrics()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.log_error(e, {"action": "workload_monitoring"})
                await asyncio.sleep(1800)
    
    async def _skill_gap_monitoring_loop(self):
        """Monitor skill gaps and generate hiring recommendations"""
        while True:
            try:
                await self._analyze_skill_gaps()
                await asyncio.sleep(86400)  # Check daily
            except Exception as e:
                logger.log_error(e, {"action": "skill_gap_monitoring"})
                await asyncio.sleep(86400)
    
    async def _scaling_execution_loop(self):
        """Execute approved scaling recommendations"""
        while True:
            try:
                await self._execute_scaling_actions()
                await asyncio.sleep(600)  # Check every 10 minutes
            except Exception as e:
                logger.log_error(e, {"action": "scaling_execution"})
                await asyncio.sleep(600)
    
    async def _analyze_performance_metrics(self):
        """Analyze performance metrics and generate scaling recommendations"""
        if not org_hierarchy.org_chart:
            return
        
        # Get current organizational metrics
        current_metrics = org_hierarchy.get_organizational_metrics()
        if not current_metrics:
            return
        
        # Check each performance threshold
        for threshold in self.performance_thresholds:
            metric_value = getattr(current_metrics, threshold.metric_name, None)
            if metric_value is None:
                continue
            
            # Check if threshold is breached
            is_breached = False
            if threshold.comparison == "below" and metric_value < threshold.threshold_value:
                is_breached = True
            elif threshold.comparison == "above" and metric_value > threshold.threshold_value:
                is_breached = True
            elif threshold.comparison == "equals" and abs(metric_value - threshold.threshold_value) < 0.01:
                is_breached = True
            
            if is_breached:
                await self._generate_performance_based_recommendation(threshold, metric_value)
    
    async def _analyze_workload_metrics(self):
        """Analyze workload across departments"""
        if not org_hierarchy.org_chart:
            return
        
        # Simulate workload metrics for each department
        for dept_name, agent_ids in org_hierarchy.org_chart.departments.items():
            workload_metrics = await self._calculate_department_workload(dept_name, agent_ids)
            self.workload_metrics_history.append(workload_metrics)
            
            # Check for scaling triggers
            await self._check_workload_triggers(workload_metrics)
        
        # Keep only last 30 days of metrics
        cutoff_date = datetime.now() - timedelta(days=30)
        self.workload_metrics_history = [
            m for m in self.workload_metrics_history if m.measurement_date >= cutoff_date
        ]
    
    async def _calculate_department_workload(self, dept_name: str, agent_ids: List[str]) -> WorkloadMetrics:
        """Calculate workload metrics for a department"""
        if not agent_ids:
            return WorkloadMetrics(department=dept_name)
        
        # Simulate realistic workload data based on department and current time
        base_utilization = {
            "Technology": 0.75,
            "Operations": 0.85,
            "Security": 0.65,
            "Executive": 0.90
        }.get(dept_name, 0.70)
        
        # Add some realistic variation
        variation = random.uniform(-0.2, 0.3)
        capacity_utilization = min(1.0, max(0.0, base_utilization + variation))
        
        # Calculate other metrics based on utilization
        active_tasks = int(len(agent_ids) * capacity_utilization * 8)  # 8 tasks per agent at full capacity
        overdue_tasks = max(0, int(active_tasks * (capacity_utilization - 0.8) * 0.5)) if capacity_utilization > 0.8 else 0
        
        return WorkloadMetrics(
            department=dept_name,
            active_tasks=active_tasks,
            overdue_tasks=overdue_tasks,
            avg_task_completion_time=24.0 * (1.0 + capacity_utilization),
            capacity_utilization=capacity_utilization,
            burnout_risk_score=max(0.0, (capacity_utilization - 0.7) * 2.0),
            error_rate=max(0.0, (capacity_utilization - 0.8) * 0.5),
            productivity_trend=random.uniform(-0.1, 0.1),
            collaboration_score=random.uniform(0.6, 0.9),
            cost_per_task=random.uniform(50, 200)
        )
    
    async def _check_workload_triggers(self, metrics: WorkloadMetrics):
        """Check if workload metrics trigger scaling actions"""
        triggers = []
        
        # High capacity utilization
        if metrics.capacity_utilization > 0.9:
            triggers.append((ScalingTrigger.WORKLOAD_OVERFLOW, "high_utilization"))
        
        # High burnout risk
        if metrics.burnout_risk_score > 0.8:
            triggers.append((ScalingTrigger.TEAM_BURNOUT, "burnout_risk"))
        
        # Too many overdue tasks
        if metrics.overdue_tasks > 5:
            triggers.append((ScalingTrigger.DEADLINE_PRESSURE, "overdue_tasks"))
        
        # High error rate
        if metrics.error_rate > 0.1:
            triggers.append((ScalingTrigger.QUALITY_ISSUES, "high_error_rate"))
        
        # Generate recommendations for each trigger
        for trigger, reason in triggers:
            await self._generate_workload_based_recommendation(trigger, metrics, reason)
    
    async def _analyze_skill_gaps(self):
        """Analyze organizational skill gaps"""
        if not org_hierarchy.org_chart:
            return
        
        # Get current skills in organization
        current_skills = await self._analyze_current_skills()
        
        # Determine required skills (this would be based on strategic planning)
        required_skills = await self._determine_required_skills()
        
        # Calculate gaps
        skill_gaps = self._calculate_skill_gaps(current_skills, required_skills)
        
        # Generate skill gap analysis
        analysis = SkillGapAnalysis(
            id=str(uuid.uuid4()),
            current_skills=current_skills,
            required_skills=required_skills,
            skill_shortages=skill_gaps["shortages"],
            skill_surpluses=skill_gaps["surpluses"],
            impact_score=self._calculate_skill_gap_impact(skill_gaps),
            next_analysis_date=datetime.now() + timedelta(days=7)
        )
        
        # Generate hiring recommendations for critical gaps
        for skill, levels in skill_gaps["shortages"].items():
            if skill in ["Python", "Security", "DevOps", "Leadership"]:  # Critical skills
                hiring_criteria = await self._generate_skill_based_hiring_criteria(skill, levels)
                analysis.hiring_recommendations.append(hiring_criteria)
        
        self.skill_gap_analyses.append(analysis)
        
        # Generate scaling recommendations for critical gaps
        if analysis.impact_score > 0.7:
            await self._generate_skill_gap_recommendation(analysis)
    
    async def _analyze_current_skills(self) -> Dict[str, Dict[str, int]]:
        """Analyze current skills in the organization"""
        current_skills = defaultdict(lambda: defaultdict(int))
        
        all_agents = talent_pool.get_all_agents()
        for agent in all_agents:
            for skill in agent.skills:
                current_skills[skill.name][skill.level.value] += 1
        
        return dict(current_skills)
    
    async def _determine_required_skills(self) -> Dict[str, Dict[str, int]]:
        """Determine required skills based on strategic goals and current projects"""
        # This would normally be based on strategic planning and project requirements
        # For now, we'll use a simplified model
        required_skills = {
            "Python": {"advanced": 2, "expert": 1},
            "Docker": {"intermediate": 3, "advanced": 1},
            "Security": {"advanced": 2, "expert": 1},
            "Leadership": {"intermediate": 2, "advanced": 1},
            "DevOps": {"intermediate": 2, "advanced": 1},
            "React": {"intermediate": 2, "advanced": 1},
            "PostgreSQL": {"intermediate": 2, "advanced": 1}
        }
        return required_skills
    
    def _calculate_skill_gaps(self, current: Dict[str, Dict[str, int]], 
                             required: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Calculate skill gaps between current and required skills"""
        shortages = defaultdict(lambda: defaultdict(int))
        surpluses = defaultdict(lambda: defaultdict(int))
        
        # Check for shortages
        for skill, levels in required.items():
            for level, needed in levels.items():
                current_count = current.get(skill, {}).get(level, 0)
                if current_count < needed:
                    shortages[skill][level] = needed - current_count
        
        # Check for surpluses
        for skill, levels in current.items():
            for level, current_count in levels.items():
                required_count = required.get(skill, {}).get(level, 0)
                if current_count > required_count:
                    surpluses[skill][level] = current_count - required_count
        
        return {
            "shortages": dict(shortages),
            "surpluses": dict(surpluses)
        }
    
    def _calculate_skill_gap_impact(self, skill_gaps: Dict[str, Dict[str, Dict[str, int]]]) -> float:
        """Calculate the business impact of skill gaps"""
        impact_weights = {
            "Python": 0.9,
            "Security": 1.0,
            "DevOps": 0.8,
            "Leadership": 0.7,
            "React": 0.6,
            "PostgreSQL": 0.7
        }
        
        total_impact = 0.0
        max_possible_impact = 0.0
        
        for skill, levels in skill_gaps["shortages"].items():
            skill_weight = impact_weights.get(skill, 0.5)
            for level, shortage in levels.items():
                level_multiplier = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.9, "expert": 1.0}.get(level, 0.5)
                total_impact += shortage * skill_weight * level_multiplier
                max_possible_impact += skill_weight
        
        return min(1.0, total_impact / max(max_possible_impact, 1.0))
    
    async def _generate_skill_based_hiring_criteria(self, skill: str, levels: Dict[str, int]) -> HiringCriteria:
        """Generate hiring criteria for skill gaps"""
        # Determine the highest level needed
        highest_level = "beginner"
        for level in ["expert", "advanced", "intermediate", "beginner"]:
            if level in levels and levels[level] > 0:
                highest_level = level
                break
        
        # Map skills to roles
        skill_to_role = {
            "Python": AgentRole.DEVELOPER,
            "Security": AgentRole.SECURITY,
            "DevOps": AgentRole.DEVOPS,
            "Leadership": AgentRole.ANALYST,
            "React": AgentRole.DEVELOPER,
            "PostgreSQL": AgentRole.DEVELOPER
        }
        
        role = skill_to_role.get(skill, AgentRole.DEVELOPER)
        skill_level = SkillLevel(highest_level)
        
        return HiringCriteria(
            required_role=role,
            required_skills=[skill],
            minimum_skill_levels={skill: skill_level},
            authority_level=AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
            department=self._get_department_for_role(role),
            urgency="high" if highest_level in ["advanced", "expert"] else "normal",
            budget_allocated=self._calculate_salary_for_skill(skill, skill_level)
        )
    
    def _get_department_for_role(self, role: AgentRole) -> str:
        """Get department for a role"""
        role_to_dept = {
            AgentRole.DEVELOPER: "Technology",
            AgentRole.DEVOPS: "Operations",
            AgentRole.SECURITY: "Security",
            AgentRole.CEO: "Executive",
            AgentRole.ANALYST: "Strategy"
        }
        return role_to_dept.get(role, "General")
    
    def _calculate_salary_for_skill(self, skill: str, level: SkillLevel) -> int:
        """Calculate appropriate salary for skill and level"""
        base_salaries = {
            "beginner": 60000,
            "intermediate": 80000,
            "advanced": 120000,
            "expert": 150000
        }
        
        skill_multipliers = {
            "Python": 1.1,
            "Security": 1.3,
            "DevOps": 1.2,
            "Leadership": 1.4,
            "React": 1.0,
            "PostgreSQL": 1.1
        }
        
        base = base_salaries.get(level.value, 80000)
        multiplier = skill_multipliers.get(skill, 1.0)
        
        return int(base * multiplier)
    
    async def _generate_performance_based_recommendation(self, threshold: PerformanceThreshold, 
                                                       current_value: float):
        """Generate scaling recommendation based on performance threshold breach"""
        recommendation_id = str(uuid.uuid4())
        
        if threshold.action_to_take == ScalingAction.HIRE_AGENT:
            title = f"Hire Additional Agent - {threshold.metric_name} Below Threshold"
            description = f"Performance metric '{threshold.metric_name}' is at {current_value:.2f}, below threshold of {threshold.threshold_value}. Additional capacity needed."
        else:
            title = f"Performance-Based Action - {threshold.action_to_take.value}"
            description = f"Performance metric '{threshold.metric_name}' triggered action due to value {current_value:.2f}"
        
        recommendation = ScalingRecommendation(
            id=recommendation_id,
            trigger=ScalingTrigger.PERFORMANCE_DECLINE,
            recommended_action=threshold.action_to_take,
            title=title,
            description=description,
            justification=f"Metric {threshold.metric_name} consistently {threshold.comparison} threshold",
            expected_outcome="Improved performance and capacity",
            risk_assessment="Low risk - performance-based decision",
            cost_impact=self.budget_per_agent if threshold.action_to_take == ScalingAction.HIRE_AGENT else 0,
            urgency_level=threshold.severity
        )
        
        self.scaling_recommendations[recommendation_id] = recommendation
        
        # Send notification to leadership
        await self._notify_scaling_recommendation(recommendation)
    
    async def _generate_workload_based_recommendation(self, trigger: ScalingTrigger, 
                                                    metrics: WorkloadMetrics, reason: str):
        """Generate scaling recommendation based on workload analysis"""
        recommendation_id = str(uuid.uuid4())
        
        if trigger == ScalingTrigger.WORKLOAD_OVERFLOW:
            action = ScalingAction.HIRE_AGENT
            title = f"Scale Up {metrics.department} Department - High Workload"
            description = f"Department utilization at {metrics.capacity_utilization:.1%} with {metrics.overdue_tasks} overdue tasks"
        elif trigger == ScalingTrigger.TEAM_BURNOUT:
            action = ScalingAction.HIRE_AGENT
            title = f"Prevent Burnout in {metrics.department} - Additional Resources Needed"
            description = f"Burnout risk score at {metrics.burnout_risk_score:.1%} - immediate action required"
        else:
            action = ScalingAction.HIRE_AGENT
            title = f"Address {trigger.value} in {metrics.department}"
            description = f"Workload metrics indicate need for scaling: {reason}"
        
        recommendation = ScalingRecommendation(
            id=recommendation_id,
            trigger=trigger,
            recommended_action=action,
            target_department=metrics.department,
            title=title,
            description=description,
            justification=f"Workload analysis shows {reason} in {metrics.department}",
            expected_outcome="Reduced workload pressure and improved performance",
            risk_assessment="Medium risk - workload-based scaling",
            cost_impact=self.budget_per_agent,
            urgency_level="high" if trigger == ScalingTrigger.TEAM_BURNOUT else "normal",
            supporting_metrics={
                "capacity_utilization": metrics.capacity_utilization,
                "overdue_tasks": metrics.overdue_tasks,
                "burnout_risk": metrics.burnout_risk_score,
                "error_rate": metrics.error_rate
            }
        )
        
        self.scaling_recommendations[recommendation_id] = recommendation
        await self._notify_scaling_recommendation(recommendation)
    
    async def _generate_skill_gap_recommendation(self, analysis: SkillGapAnalysis):
        """Generate scaling recommendation based on skill gap analysis"""
        recommendation_id = str(uuid.uuid4())
        
        critical_skills = [skill for skill in analysis.skill_shortages.keys() 
                          if skill in ["Python", "Security", "DevOps", "Leadership"]]
        
        recommendation = ScalingRecommendation(
            id=recommendation_id,
            trigger=ScalingTrigger.SKILL_GAP,
            recommended_action=ScalingAction.HIRE_AGENT,
            title=f"Address Critical Skill Gaps - {', '.join(critical_skills[:3])}",
            description=f"Skill gap analysis shows critical shortages in {len(critical_skills)} key areas",
            justification=f"Impact score of {analysis.impact_score:.1%} indicates business-critical skill gaps",
            expected_outcome="Enhanced organizational capabilities and reduced project risk",
            risk_assessment="High business risk if not addressed",
            cost_impact=len(analysis.hiring_recommendations) * self.budget_per_agent,
            urgency_level="high" if analysis.impact_score > 0.8 else "normal",
            supporting_metrics={
                "impact_score": analysis.impact_score,
                "critical_gaps": len(critical_skills),
                "hiring_recommendations": len(analysis.hiring_recommendations)
            }
        )
        
        self.scaling_recommendations[recommendation_id] = recommendation
        await self._notify_scaling_recommendation(recommendation)
    
    async def _notify_scaling_recommendation(self, recommendation: ScalingRecommendation):
        """Send notification about scaling recommendation to leadership"""
        # Find appropriate authority to notify based on cost impact
        if recommendation.cost_impact > 500000:  # > $500K
            target_authority = AuthorityLevel.EXECUTIVE
        elif recommendation.cost_impact > 100000:  # > $100K
            target_authority = AuthorityLevel.SENIOR_MANAGEMENT
        else:
            target_authority = AuthorityLevel.MIDDLE_MANAGEMENT
        
        # Find agents with required authority
        target_agents = []
        if org_hierarchy.org_chart:
            for agent_id, position in org_hierarchy.org_chart.positions.items():
                if position.authority_level == target_authority:
                    target_agents.append(agent_id)
        
        if not target_agents:
            return
        
        # Send notification to first available authority
        target_agent = target_agents[0]
        
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "critical": MessagePriority.URGENT
        }
        
        message_content = f"""
🏢 SCALING RECOMMENDATION

Title: {recommendation.title}
Trigger: {recommendation.trigger.value.replace('_', ' ').title()}
Action: {recommendation.recommended_action.value.replace('_', ' ').title()}
Urgency: {recommendation.urgency_level.upper()}

Description:
{recommendation.description}

Justification:
{recommendation.justification}

Expected Outcome:
{recommendation.expected_outcome}

Cost Impact: ${recommendation.cost_impact:,.2f}
Risk Assessment: {recommendation.risk_assessment}

Please review and approve/reject this recommendation.
Recommendation ID: {recommendation.id}
"""
        
        await inter_agent_comm.send_direct_message(
            from_agent_id="ahr_system",
            to_agent_id=target_agent,
            subject=f"🚨 SCALING NEEDED: {recommendation.title}",
            content=message_content,
            priority=priority_map.get(recommendation.urgency_level, MessagePriority.NORMAL),
            metadata={
                "recommendation_id": recommendation.id,
                "trigger": recommendation.trigger.value,
                "cost_impact": recommendation.cost_impact
            }
        )
        
        logger.log_system_event("scaling_recommendation_sent", {
            "recommendation_id": recommendation.id,
            "trigger": recommendation.trigger.value,
            "action": recommendation.recommended_action.value,
            "target_agent": target_agent,
            "cost_impact": recommendation.cost_impact
        })
    
    async def _execute_scaling_actions(self):
        """Execute approved scaling recommendations"""
        if self.scaling_actions_today >= self.daily_scaling_limit:
            return
        
        # Check for approved recommendations
        approved_recommendations = [
            rec for rec in self.scaling_recommendations.values()
            if rec.status == "approved" and rec.implemented_at is None
        ]
        
        for recommendation in approved_recommendations:
            if await self._can_execute_scaling_action():
                await self._execute_recommendation(recommendation)
                self.scaling_actions_today += 1
                
                if self.scaling_actions_today >= self.daily_scaling_limit:
                    break
    
    async def _can_execute_scaling_action(self) -> bool:
        """Check if scaling action can be executed (cooldown, limits, etc.)"""
        if self.last_scaling_action:
            time_since_last = (datetime.now() - self.last_scaling_action).total_seconds() / 3600
            if time_since_last < self.scaling_cooldown_hours:
                return False
        
        return self.scaling_actions_today < self.daily_scaling_limit
    
    async def _execute_recommendation(self, recommendation: ScalingRecommendation):
        """Execute a specific scaling recommendation"""
        try:
            if recommendation.recommended_action == ScalingAction.HIRE_AGENT:
                await self._execute_hire_agent(recommendation)
            elif recommendation.recommended_action == ScalingAction.TERMINATE_AGENT:
                await self._execute_terminate_agent(recommendation)
            elif recommendation.recommended_action == ScalingAction.PROMOTE_AGENT:
                await self._execute_promote_agent(recommendation)
            # Add other actions as needed
            
            recommendation.status = "implemented"
            recommendation.implemented_at = datetime.now()
            self.last_scaling_action = datetime.now()
            
            logger.log_system_event("scaling_action_executed", {
                "recommendation_id": recommendation.id,
                "action": recommendation.recommended_action.value,
                "cost_impact": recommendation.cost_impact
            })
            
        except Exception as e:
            recommendation.status = "failed"
            logger.log_error(e, {
                "action": "execute_scaling_recommendation",
                "recommendation_id": recommendation.id
            })
    
    async def _execute_hire_agent(self, recommendation: ScalingRecommendation):
        """Execute hiring of a new agent"""
        # This would integrate with Ollama to generate a new agent
        if not ollama_service:
            return
        
        # Determine role based on department or recommendation
        target_role = AgentRole.DEVELOPER  # Default
        if recommendation.target_department == "Security":
            target_role = AgentRole.SECURITY
        elif recommendation.target_department == "Operations":
            target_role = AgentRole.DEVOPS
        
        # Generate new agent using Ollama
        new_agents = await ollama_service.generate_agents_for_role(target_role.value, 1)
        
        if new_agents and len(new_agents) > 0:
            new_agent = new_agents[0]
            
            # Record lifecycle event
            event = AgentLifecycleEvent(
                id=str(uuid.uuid4()),
                agent_id=new_agent.id,
                event_type="hired",
                triggered_by="ahr_system",
                reason=f"AHR scaling: {recommendation.trigger.value}",
                new_role=new_agent.role,
                new_authority=AuthorityLevel.INDIVIDUAL_CONTRIBUTOR,
                new_department=recommendation.target_department or "General",
                new_salary=int(recommendation.cost_impact),
                cost_impact=recommendation.cost_impact
            )
            
            self.agent_lifecycle_events[event.id] = event
            
            # Add to organizational hierarchy
            if org_hierarchy.org_chart:
                # This would be implemented to add the agent to the org chart
                pass
    
    async def _execute_terminate_agent(self, recommendation: ScalingRecommendation):
        """Execute termination of an agent"""
        if not recommendation.target_agent_id:
            return
        
        # Record lifecycle event
        event = AgentLifecycleEvent(
            id=str(uuid.uuid4()),
            agent_id=recommendation.target_agent_id,
            event_type="terminated",
            triggered_by="ahr_system",
            reason=f"AHR scaling: {recommendation.trigger.value}",
            cost_impact=-recommendation.cost_impact  # Negative for savings
        )
        
        self.agent_lifecycle_events[event.id] = event
        
        # Remove from talent pool and org chart
        # This would be implemented to remove the agent
    
    async def _execute_promote_agent(self, recommendation: ScalingRecommendation):
        """Execute promotion of an agent"""
        if not recommendation.target_agent_id:
            return
        
        # This would be implemented to promote the agent
        # Record lifecycle event, update org chart, etc.
        pass
    
    # Public API methods
    
    async def approve_recommendation(self, recommendation_id: str, approver_id: str) -> bool:
        """Approve a scaling recommendation"""
        recommendation = self.scaling_recommendations.get(recommendation_id)
        if not recommendation:
            return False
        
        recommendation.status = "approved"
        recommendation.approved_by = approver_id
        recommendation.approved_at = datetime.now()
        
        logger.log_system_event("scaling_recommendation_approved", {
            "recommendation_id": recommendation_id,
            "approver": approver_id,
            "action": recommendation.recommended_action.value
        })
        
        return True
    
    async def reject_recommendation(self, recommendation_id: str, approver_id: str, reason: str) -> bool:
        """Reject a scaling recommendation"""
        recommendation = self.scaling_recommendations.get(recommendation_id)
        if not recommendation:
            return False
        
        recommendation.status = "rejected"
        recommendation.approved_by = approver_id
        recommendation.approved_at = datetime.now()
        
        # Add rejection reason to metadata
        if "rejection_reason" not in recommendation.supporting_metrics:
            recommendation.supporting_metrics["rejection_reason"] = reason
        
        logger.log_system_event("scaling_recommendation_rejected", {
            "recommendation_id": recommendation_id,
            "approver": approver_id,
            "reason": reason
        })
        
        return True
    
    def get_scaling_dashboard(self) -> ScalingDashboard:
        """Get current scaling dashboard data"""
        if not org_hierarchy.org_chart:
            return ScalingDashboard(id=str(uuid.uuid4()), total_agents=0)
        
        # Calculate dashboard metrics
        total_agents = len(org_hierarchy.org_chart.positions)
        agents_by_role = defaultdict(int)
        agents_by_department = defaultdict(int)
        agents_by_authority = defaultdict(int)
        
        for position in org_hierarchy.org_chart.positions.values():
            # This would map position to agent to get role
            agents_by_authority[position.authority_level] += 1
            agents_by_department[position.department] += 1
        
        # Calculate recent activity
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_events = [
            event for event in self.agent_lifecycle_events.values()
            if event.event_date >= thirty_days_ago
        ]
        
        hires = len([e for e in recent_events if e.event_type == "hired"])
        terminations = len([e for e in recent_events if e.event_type == "terminated"])
        promotions = len([e for e in recent_events if e.event_type == "promoted"])
        
        # Get pending recommendations
        pending_recommendations = [
            rec for rec in self.scaling_recommendations.values()
            if rec.status == "pending"
        ]
        
        return ScalingDashboard(
            id=str(uuid.uuid4()),
            total_agents=total_agents,
            agents_by_department=dict(agents_by_department),
            agents_by_authority=dict(agents_by_authority),
            hires_last_30_days=hires,
            terminations_last_30_days=terminations,
            promotions_last_30_days=promotions,
            monthly_payroll=total_agents * (self.budget_per_agent / 12),
            predicted_scaling_needs=pending_recommendations[:5],
            critical_alerts=[
                rec.title for rec in pending_recommendations 
                if rec.urgency_level in ["high", "critical"]
            ],
            pending_approvals=len(pending_recommendations)
        )
    
    def get_recommendations(self, status: Optional[str] = None) -> List[ScalingRecommendation]:
        """Get scaling recommendations, optionally filtered by status"""
        recommendations = list(self.scaling_recommendations.values())
        
        if status:
            recommendations = [r for r in recommendations if r.status == status]
        
        # Sort by urgency and creation date
        urgency_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        recommendations.sort(
            key=lambda r: (urgency_order.get(r.urgency_level, 3), r.created_at),
            reverse=True
        )
        
        return recommendations
    
    def get_skill_gap_analysis(self) -> Optional[SkillGapAnalysis]:
        """Get the latest skill gap analysis"""
        return self.skill_gap_analyses[-1] if self.skill_gap_analyses else None


# Global service instance
auto_scaling_hr = AutoScalingHRService()