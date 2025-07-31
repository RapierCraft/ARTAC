import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { Agent, AgentStatus, SystemStatus, Task } from '@/types/agent'
import { getApiUrl } from '@/lib/utils'
import { getMockData } from '@/lib/placeholder-data'

interface SystemStore {
  // State
  isInitialized: boolean
  systemStatus: SystemStatus | null
  agents: Agent[]
  agentStatuses: Record<string, AgentStatus>
  tasks: Task[]
  isLoading: boolean
  error: string | null
  isOfflineMode: boolean

  // Actions
  initializeSystem: () => Promise<void>
  fetchSystemStatus: () => Promise<void>
  fetchAgents: () => Promise<void>
  fetchAgentStatuses: () => Promise<void>
  fetchTasks: () => Promise<void>
  createAgent: (agentData: Partial<Agent>) => Promise<Agent | null>
  assignTask: (agentId: string, taskData: Partial<Task>) => Promise<string | null>
  updateAgentStatus: (agentId: string, status: string) => Promise<void>
  setError: (error: string | null) => void
  clearError: () => void
  checkBackendHealth: () => Promise<boolean>
  startHealthCheck: () => void
  stopHealthCheck: () => void
}

let healthCheckInterval: NodeJS.Timeout | null = null

export const useSystemStore = create<SystemStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      isInitialized: false,
      systemStatus: null,
      agents: [],
      agentStatuses: {},
      tasks: [],
      isLoading: false,
      error: null,
      isOfflineMode: false,

      // Initialize the entire system
      initializeSystem: async () => {
        set({ isLoading: true, error: null })
        
        try {
          // Try to connect to backend with proper error handling
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 5000)
          
          const response = await fetch(getApiUrl('/health'), { 
            signal: controller.signal,
            mode: 'cors',
            credentials: 'omit'
          }).catch((err) => {
            clearTimeout(timeoutId)
            throw new Error(`Network error: ${err.message}`)
          })
          
          clearTimeout(timeoutId)
          
          if (!response.ok) {
            throw new Error(`Backend responded with status: ${response.status}`)
          }

          // Backend is available - fetch real data
          await Promise.all([
            get().fetchSystemStatus(),
            get().fetchAgents(),
            get().fetchAgentStatuses(),
            get().fetchTasks(),
          ])

          set({ isInitialized: true, isLoading: false, isOfflineMode: false })
          
          // Start health check polling
          get().startHealthCheck()
        } catch (error) {
          // Backend unavailable - this is expected when backend isn't running
          // Use mock data for offline mode
          const mockData = getMockData()
          const agentStatuses: Record<string, AgentStatus> = {}
          
          mockData.agentStatuses.forEach((status) => {
            agentStatuses[status.agent_id] = status
          })

          set({ 
            systemStatus: mockData.systemStatus,
            agents: mockData.agents,
            agentStatuses,
            tasks: mockData.tasks,
            isInitialized: true,
            isLoading: false,
            isOfflineMode: true,
            error: null
          })
          
          // Start health check polling even in offline mode
          get().startHealthCheck()
        }
      },

      // Fetch system status
      fetchSystemStatus: async () => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          // Return early if in offline mode - data already set
          return
        }

        try {
          const response = await fetch(getApiUrl('/api/v1/system/status'))
          if (!response.ok) throw new Error('Failed to fetch system status')
          
          const systemStatus = await response.json()
          set({ systemStatus })
        } catch (error) {
          // Silently handle - app is in offline mode
          set({ error: null })
        }
      },

      // Fetch all agents
      fetchAgents: async () => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          return
        }

        try {
          const response = await fetch(getApiUrl('/api/v1/agents'))
          if (!response.ok) throw new Error('Failed to fetch agents')
          
          const agents = await response.json()
          set({ agents })
        } catch (error) {
          console.error('Failed to fetch agents:', error)
          set({ error: 'Failed to fetch agents' })
        }
      },

      // Fetch agent statuses
      fetchAgentStatuses: async () => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          return
        }

        try {
          const response = await fetch(getApiUrl('/api/v1/agents/status'))
          if (!response.ok) throw new Error('Failed to fetch agent statuses')
          
          const statuses = await response.json()
          const agentStatuses: Record<string, AgentStatus> = {}
          
          statuses.forEach((status: AgentStatus) => {
            agentStatuses[status.agent_id] = status
          })
          
          set({ agentStatuses })
        } catch (error) {
          console.error('Failed to fetch agent statuses:', error)
          set({ error: 'Failed to fetch agent statuses' })
        }
      },

      // Fetch all tasks
      fetchTasks: async () => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          return
        }

        try {
          const response = await fetch(getApiUrl('/api/v1/tasks'))
          if (!response.ok) throw new Error('Failed to fetch tasks')
          
          const tasks = await response.json()
          set({ tasks })
        } catch (error) {
          console.error('Failed to fetch tasks:', error)
          set({ error: 'Failed to fetch tasks' })
        }
      },

      // Create a new agent
      createAgent: async (agentData: Partial<Agent>) => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          set({ error: 'Cannot create agents in offline mode' })
          return null
        }

        try {
          const response = await fetch(getApiUrl('/api/v1/agents'), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(agentData),
          })

          if (!response.ok) throw new Error('Failed to create agent')
          
          const newAgent = await response.json()
          
          // Update local state
          set(state => ({
            agents: [...state.agents, newAgent]
          }))
          
          // Refresh agent statuses
          await get().fetchAgentStatuses()
          
          return newAgent
        } catch (error) {
          console.error('Failed to create agent:', error)
          set({ error: 'Failed to create agent' })
          return null
        }
      },

      // Assign task to agent
      assignTask: async (agentId: string, taskData: Partial<Task>) => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          set({ error: 'Cannot assign tasks in offline mode' })
          return null
        }

        try {
          const response = await fetch(getApiUrl(`/api/v1/agents/${agentId}/tasks`), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData),
          })

          if (!response.ok) throw new Error('Failed to assign task')
          
          const result = await response.json()
          
          // Refresh tasks and agent statuses
          await Promise.all([
            get().fetchTasks(),
            get().fetchAgentStatuses(),
          ])
          
          return result.task_id
        } catch (error) {
          console.error('Failed to assign task:', error)
          set({ error: 'Failed to assign task' })
          return null
        }
      },

      // Update agent status
      updateAgentStatus: async (agentId: string, status: string) => {
        const { isOfflineMode } = get()
        
        if (isOfflineMode) {
          set({ error: 'Cannot update agent status in offline mode' })
          return
        }

        try {
          const response = await fetch(getApiUrl(`/api/v1/agents/${agentId}/status`), {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status }),
          })

          if (!response.ok) throw new Error('Failed to update agent status')
          
          // Refresh agent statuses
          await get().fetchAgentStatuses()
        } catch (error) {
          console.error('Failed to update agent status:', error)
          set({ error: 'Failed to update agent status' })
        }
      },

      // Set error
      setError: (error: string | null) => {
        set({ error })
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },

      // Check backend health
      checkBackendHealth: async () => {
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 3000)
          
          const response = await fetch(getApiUrl('/health'), { 
            signal: controller.signal,
            mode: 'cors',
            credentials: 'omit'
          })
          
          clearTimeout(timeoutId)
          return response.ok
        } catch (error) {
          return false
        }
      },

      // Start health check polling
      startHealthCheck: () => {
        // Clear any existing interval
        if (healthCheckInterval) {
          clearInterval(healthCheckInterval)
        }

        // Check every 10 seconds
        healthCheckInterval = setInterval(async () => {
          const { isOfflineMode } = get()
          const isHealthy = await get().checkBackendHealth()

          if (isOfflineMode && isHealthy) {
            // Backend came online - switch to real data
            console.log('🟢 Backend is now online, switching to real data...')
            try {
              await Promise.all([
                get().fetchSystemStatus(),
                get().fetchAgents(),
                get().fetchAgentStatuses(),
                get().fetchTasks(),
              ])
              set({ isOfflineMode: false, error: null })
              console.log('✅ Successfully switched to real data')
            } catch (error) {
              console.warn('⚠️ Failed to fetch real data, staying in offline mode')
            }
          } else if (!isOfflineMode && !isHealthy) {
            // Backend went offline - switch to fallback data
            console.log('🔴 Backend went offline, switching to fallback data...')
            const mockData = getMockData()
            const agentStatuses: Record<string, AgentStatus> = {}
            
            mockData.agentStatuses.forEach((status) => {
              agentStatuses[status.agent_id] = status
            })

            set({ 
              systemStatus: mockData.systemStatus,
              agents: mockData.agents,
              agentStatuses,
              tasks: mockData.tasks,
              isOfflineMode: true,
              error: null
            })
            console.log('✅ Successfully switched to fallback data')
          }
        }, 10000) // Check every 10 seconds
      },

      // Stop health check polling
      stopHealthCheck: () => {
        if (healthCheckInterval) {
          clearInterval(healthCheckInterval)
          healthCheckInterval = null
        }
      },
    }),
    {
      name: 'system-store',
    }
  )
)