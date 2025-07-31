export interface Agent {
  id: string
  name: string
  role: string
  level: 'executive' | 'management' | 'development' | 'execution'
  status: 'active' | 'busy' | 'suspended' | 'terminated'
  model_name: string
  specialization: string[]
  performance_score: number
  created_at: string
  updated_at: string
  metadata: Record<string, any>
}

export interface AgentRelationship {
  id: string
  parent_agent_id: string
  child_agent_id: string
  relationship_type: 'supervisor' | 'mentor' | 'peer'
  created_at: string
}

export interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assigned_agent_id?: string
  created_by_agent_id?: string
  parent_task_id?: string
  estimated_hours?: number
  actual_hours?: number
  git_branch?: string
  created_at: string
  updated_at: string
  completed_at?: string
  metadata: Record<string, any>
}

export interface AgentSession {
  agent_id: string
  session_id: string
  active: boolean
  working_directory: string
  process_id?: number
}

export interface AgentStatus {
  agent_id: string
  name: string
  role: string
  level: string
  status: string
  performance_score: number
  specialization: string[]
  active_tasks: number
  claude_session: AgentSession
  created_at?: string
}

export interface SystemStatus {
  initialized: boolean
  total_agents: number
  active_agents: number
  busy_agents: number
  total_active_tasks: number
  claude_sessions: number
}

export interface PerformanceMetric {
  id: string
  agent_id: string
  metric_type: string
  metric_value: number
  measurement_period: string
  measured_at: string
  details: Record<string, any>
}

export interface Conversation {
  id: string
  user_id: string
  session_id: string
  message_type: 'user_voice' | 'user_text' | 'agent_response'
  content: string
  agent_id?: string
  confidence_score?: number
  processing_time_ms?: number
  created_at: string
  metadata: Record<string, any>
}