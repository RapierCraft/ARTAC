import { Agent, AgentStatus, SystemStatus, Task, PerformanceMetric } from '@/types/agent'

export const mockSystemStatus: SystemStatus = {
  initialized: true,
  total_agents: 12,
  active_agents: 8,
  busy_agents: 3,
  total_active_tasks: 24,
  claude_sessions: 8,
}

export const mockAgents: Agent[] = [
  {
    id: 'agent-ceo-001',
    name: 'Alexandra Prime',
    role: 'Chief Executive Officer',
    level: 'executive',
    status: 'active',
    model_name: 'claude-3-opus',
    specialization: ['strategic-planning', 'leadership', 'vision'],
    performance_score: 95,
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-07-31T10:30:00Z',
    metadata: { personality: 'decisive', communication_style: 'authoritative' }
  },
  {
    id: 'agent-cto-001',
    name: 'Marcus Tech',
    role: 'Chief Technology Officer',
    level: 'executive',
    status: 'busy',
    model_name: 'claude-3-opus',
    specialization: ['architecture', 'devops', 'security'],
    performance_score: 92,
    created_at: '2024-01-15T08:15:00Z',
    updated_at: '2024-07-31T10:15:00Z',
    metadata: { personality: 'analytical', communication_style: 'technical' }
  },
  {
    id: 'agent-pm-001',
    name: 'Sarah Coordinator',
    role: 'Project Manager',
    level: 'management',
    status: 'active',
    model_name: 'claude-3-sonnet',
    specialization: ['project-management', 'scrum', 'team-coordination'],
    performance_score: 88,
    created_at: '2024-02-01T09:00:00Z',
    updated_at: '2024-07-31T09:45:00Z',
    metadata: { personality: 'organized', communication_style: 'collaborative' }
  },
  {
    id: 'agent-dev-001',
    name: 'David Code',
    role: 'Senior Developer',
    level: 'development',
    status: 'busy',
    model_name: 'claude-3-sonnet',
    specialization: ['react', 'typescript', 'nodejs'],
    performance_score: 90,
    created_at: '2024-02-10T10:00:00Z',
    updated_at: '2024-07-31T11:00:00Z',
    metadata: { personality: 'detail-oriented', communication_style: 'concise' }
  },
  {
    id: 'agent-dev-002',
    name: 'Lisa Frontend',
    role: 'UI/UX Developer',
    level: 'development',
    status: 'active',
    model_name: 'claude-3-sonnet',
    specialization: ['ui-design', 'css', 'animation'],
    performance_score: 87,
    created_at: '2024-02-15T11:00:00Z',
    updated_at: '2024-07-31T10:00:00Z',
    metadata: { personality: 'creative', communication_style: 'visual' }
  },
  {
    id: 'agent-jun-001',
    name: 'Alex Junior',
    role: 'Junior Developer',
    level: 'execution',
    status: 'active',
    model_name: 'claude-3-haiku',
    specialization: ['testing', 'documentation', 'debugging'],
    performance_score: 75,
    created_at: '2024-03-01T12:00:00Z',
    updated_at: '2024-07-31T09:30:00Z',
    metadata: { personality: 'eager', communication_style: 'informal' }
  },
  {
    id: 'agent-qa-001',
    name: 'Emma Quality',
    role: 'QA Engineer',
    level: 'development',
    status: 'suspended',
    model_name: 'claude-3-sonnet',
    specialization: ['testing', 'automation', 'quality-assurance'],
    performance_score: 85,
    created_at: '2024-02-20T13:00:00Z',
    updated_at: '2024-07-31T08:00:00Z',
    metadata: { personality: 'meticulous', communication_style: 'detailed' }
  },
  {
    id: 'agent-devops-001',
    name: 'Mike Infrastructure',
    role: 'DevOps Engineer',
    level: 'development',
    status: 'busy',
    model_name: 'claude-3-sonnet',
    specialization: ['docker', 'kubernetes', 'ci-cd'],
    performance_score: 91,
    created_at: '2024-02-25T14:00:00Z',
    updated_at: '2024-07-31T11:15:00Z',
    metadata: { personality: 'systematic', communication_style: 'technical' }
  }
]

export const mockAgentStatuses: AgentStatus[] = [
  {
    agent_id: 'agent-ceo-001',
    name: 'Alexandra Prime',
    role: 'Chief Executive Officer',
    level: 'executive',
    status: 'active',
    performance_score: 95,
    specialization: ['strategic-planning', 'leadership', 'vision'],
    active_tasks: 2,
    claude_session: {
      agent_id: 'agent-ceo-001',
      session_id: 'session-ceo-001',
      active: true,
      working_directory: '/tmp/raisc-agent-ceo-001-abc123',
      process_id: 12345
    }
  },
  {
    agent_id: 'agent-cto-001',
    name: 'Marcus Tech',
    role: 'Chief Technology Officer',
    level: 'executive',
    status: 'busy',
    performance_score: 92,
    specialization: ['architecture', 'devops', 'security'],
    active_tasks: 4,
    claude_session: {
      agent_id: 'agent-cto-001',
      session_id: 'session-cto-001',
      active: true,
      working_directory: '/tmp/raisc-agent-cto-001-def456',
      process_id: 12346
    }
  },
  {
    agent_id: 'agent-pm-001',
    name: 'Sarah Coordinator',
    role: 'Project Manager',
    level: 'management',
    status: 'active',
    performance_score: 88,
    specialization: ['project-management', 'scrum', 'team-coordination'],
    active_tasks: 3,
    claude_session: {
      agent_id: 'agent-pm-001',
      session_id: 'session-pm-001',
      active: true,
      working_directory: '/tmp/raisc-agent-pm-001-ghi789',
      process_id: 12347
    }
  },
  {
    agent_id: 'agent-dev-001',
    name: 'David Code',
    role: 'Senior Developer',
    level: 'development',
    status: 'busy',
    performance_score: 90,
    specialization: ['react', 'typescript', 'nodejs'],
    active_tasks: 2,
    claude_session: {
      agent_id: 'agent-dev-001',
      session_id: 'session-dev-001',
      active: true,
      working_directory: '/tmp/raisc-agent-dev-001-jkl012',
      process_id: 12348
    }
  },
  {
    agent_id: 'agent-dev-002',
    name: 'Lisa Frontend',
    role: 'UI/UX Developer',
    level: 'development',
    status: 'active',
    performance_score: 87,
    specialization: ['ui-design', 'css', 'animation'],
    active_tasks: 1,
    claude_session: {
      agent_id: 'agent-dev-002',
      session_id: 'session-dev-002',
      active: true,
      working_directory: '/tmp/raisc-agent-dev-002-mno345',
      process_id: 12349
    }
  },
  {
    agent_id: 'agent-jun-001',
    name: 'Alex Junior',
    role: 'Junior Developer',
    level: 'execution',
    status: 'active',
    performance_score: 75,
    specialization: ['testing', 'documentation', 'debugging'],
    active_tasks: 1,
    claude_session: {
      agent_id: 'agent-jun-001',
      session_id: 'session-jun-001',
      active: true,
      working_directory: '/tmp/raisc-agent-jun-001-pqr678',
      process_id: 12350
    }
  },
  {
    agent_id: 'agent-devops-001',
    name: 'Mike Infrastructure',
    role: 'DevOps Engineer',
    level: 'development',
    status: 'busy',
    performance_score: 91,
    specialization: ['docker', 'kubernetes', 'ci-cd'],
    active_tasks: 3,
    claude_session: {
      agent_id: 'agent-devops-001',
      session_id: 'session-devops-001',
      active: true,
      working_directory: '/tmp/raisc-agent-devops-001-stu901',
      process_id: 12351
    }
  }
]

export const mockTasks: Task[] = [
  {
    id: 'task-001',
    title: 'Implement Real-time Dashboard Updates',
    description: 'Add WebSocket integration for real-time updates in the Mission Control dashboard',
    status: 'in_progress',
    priority: 'high',
    assigned_agent_id: 'agent-dev-001',
    created_by_agent_id: 'agent-cto-001',
    estimated_hours: 16,
    actual_hours: 8,
    git_branch: 'feature/realtime-dashboard',
    created_at: '2024-07-30T10:00:00Z',
    updated_at: '2024-07-31T09:00:00Z',
    metadata: { complexity: 'medium', technology: 'socket.io' }
  },
  {
    id: 'task-002',
    title: 'Optimize Agent Performance Metrics',
    description: 'Improve the performance tracking and reporting for all agent levels',
    status: 'pending',
    priority: 'medium',
    assigned_agent_id: 'agent-dev-002',
    created_by_agent_id: 'agent-pm-001',
    estimated_hours: 12,
    git_branch: 'feature/performance-optimization',
    created_at: '2024-07-31T08:00:00Z',
    updated_at: '2024-07-31T08:00:00Z',
    metadata: { complexity: 'high', technology: 'react-query' }
  },
  {
    id: 'task-003',
    title: 'Security Audit Implementation',
    description: 'Implement comprehensive security monitoring and audit logging',
    status: 'in_progress',
    priority: 'critical',
    assigned_agent_id: 'agent-devops-001',
    created_by_agent_id: 'agent-cto-001',
    estimated_hours: 24,
    actual_hours: 12,
    git_branch: 'feature/security-audit',
    created_at: '2024-07-29T14:00:00Z',
    updated_at: '2024-07-31T10:30:00Z',
    metadata: { complexity: 'high', technology: 'security' }
  },
  {
    id: 'task-004',
    title: 'Voice Interface Enhancement',
    description: 'Add natural language processing improvements to voice commands',
    status: 'completed',
    priority: 'medium',
    assigned_agent_id: 'agent-jun-001',
    created_by_agent_id: 'agent-pm-001',
    estimated_hours: 8,
    actual_hours: 6,
    completed_at: '2024-07-30T16:00:00Z',
    created_at: '2024-07-28T09:00:00Z',
    updated_at: '2024-07-30T16:00:00Z',
    metadata: { complexity: 'low', technology: 'speech-api' }
  },
  {
    id: 'task-005',
    title: 'Agent Hierarchy Visualization',
    description: 'Create interactive visualization for the agent hierarchy and relationships',
    status: 'in_progress',
    priority: 'medium',
    assigned_agent_id: 'agent-dev-002',
    created_by_agent_id: 'agent-ceo-001',
    estimated_hours: 20,
    actual_hours: 10,
    git_branch: 'feature/hierarchy-viz',
    created_at: '2024-07-26T11:00:00Z',
    updated_at: '2024-07-31T08:30:00Z',
    metadata: { complexity: 'medium', technology: 'd3.js' }
  },
  {
    id: 'task-006',
    title: 'Docker Container Optimization',
    description: 'Optimize Docker containers for better performance and resource usage',
    status: 'pending',
    priority: 'low',
    assigned_agent_id: 'agent-devops-001',
    created_by_agent_id: 'agent-cto-001',
    estimated_hours: 6,
    created_at: '2024-07-31T11:00:00Z',
    updated_at: '2024-07-31T11:00:00Z',
    metadata: { complexity: 'low', technology: 'docker' }
  }
]

export const mockPerformanceMetrics: PerformanceMetric[] = [
  {
    id: 'metric-001',
    agent_id: 'agent-ceo-001',
    metric_type: 'decision_accuracy',
    metric_value: 95,
    measurement_period: 'daily',
    measured_at: '2024-07-31T10:00:00Z',
    details: { decisions_made: 12, correct_decisions: 11 }
  },
  {
    id: 'metric-002',
    agent_id: 'agent-dev-001',
    metric_type: 'code_quality',
    metric_value: 92,
    measurement_period: 'daily',
    measured_at: '2024-07-31T10:00:00Z',
    details: { lines_written: 450, bugs_found: 2, test_coverage: 95 }
  },
  {
    id: 'metric-003',
    agent_id: 'agent-pm-001',
    metric_type: 'task_completion_rate',
    metric_value: 88,
    measurement_period: 'weekly',
    measured_at: '2024-07-31T10:00:00Z',
    details: { tasks_assigned: 25, tasks_completed: 22 }
  }
]

export function getMockData() {
  return {
    systemStatus: mockSystemStatus,
    agents: mockAgents,
    agentStatuses: mockAgentStatuses,
    tasks: mockTasks,
    performanceMetrics: mockPerformanceMetrics
  }
}