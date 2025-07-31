'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  User, 
  Code, 
  GitBranch,
  Zap,
  AlertCircle
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useSystemStore } from '@/stores/system-store'
import { formatRelativeTime, cn } from '@/lib/utils'

interface ActivityItem {
  id: string
  type: 'task_completed' | 'task_failed' | 'agent_created' | 'agent_suspended' | 'deployment' | 'alert'
  title: string
  description: string
  timestamp: string
  agent?: string
  icon: any
  color: string
  bgColor: string
}

export function RecentActivity() {
  const { tasks, agents } = useSystemStore()

  // Generate recent activity items
  const activityItems = useMemo(() => {
    const items: ActivityItem[] = []

    // Add completed tasks
    tasks
      .filter(task => task.status === 'completed')
      .sort((a, b) => new Date(b.completed_at || b.updated_at).getTime() - new Date(a.completed_at || a.updated_at).getTime())
      .slice(0, 3)
      .forEach(task => {
        const assignedAgent = agents.find(agent => agent.id === task.assigned_agent_id)
        items.push({
          id: `task-${task.id}`,
          type: 'task_completed',
          title: 'Task Completed',
          description: task.title,
          timestamp: task.completed_at || task.updated_at,
          agent: assignedAgent?.name || 'Unknown Agent',
          icon: CheckCircle,
          color: 'text-green-500',
          bgColor: 'bg-green-500/10'
        })
      })

    // Add failed tasks
    tasks
      .filter(task => task.status === 'failed')
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 2)
      .forEach(task => {
        const assignedAgent = agents.find(agent => agent.id === task.assigned_agent_id)
        items.push({
          id: `task-failed-${task.id}`,
          type: 'task_failed',
          title: 'Task Failed',
          description: task.title,
          timestamp: task.updated_at,
          agent: assignedAgent?.name || 'Unknown Agent',
          icon: XCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-500/10'
        })
      })

    // Add recently created agents
    agents
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 2)
      .forEach(agent => {
        items.push({
          id: `agent-${agent.id}`,
          type: 'agent_created',
          title: 'Agent Deployed',
          description: `${agent.role} agent joined the team`,
          timestamp: agent.created_at,
          agent: agent.name,
          icon: User,
          color: 'text-blue-500',
          bgColor: 'bg-blue-500/10'
        })
      })

    // Add some mock system events
    const now = new Date()
    const mockEvents = [
      {
        id: 'deploy-1',
        type: 'deployment' as const,
        title: 'Deployment Successful',
        description: 'Version 1.2.3 deployed to production',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        icon: GitBranch,
        color: 'text-purple-500',
        bgColor: 'bg-purple-500/10'
      },
      {
        id: 'alert-1',
        type: 'alert' as const,
        title: 'Performance Alert',
        description: 'CPU usage exceeded 80% threshold',
        timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        icon: AlertCircle,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500/10'
      }
    ]

    items.push(...mockEvents)

    // Sort by timestamp and return latest 8 items
    return items
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 8)
  }, [tasks, agents])

  return (
    <div className="space-y-3">
      {activityItems.length === 0 ? (
        <div className="text-center py-6">
          <Clock className="w-8 h-8 text-slate-500 mx-auto mb-2" />
          <p className="text-sm text-slate-500">No recent activity</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
          {activityItems.map((item, index) => {
            const IconComponent = item.icon
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  "flex items-start space-x-3 p-3 rounded-lg border transition-all duration-200",
                  "hover:bg-slate-800/30 border-slate-700/50",
                  item.bgColor
                )}
              >
                <div className={cn("p-1.5 rounded-full", item.bgColor)}>
                  <IconComponent className={cn("w-3 h-3", item.color)} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-white truncate">
                      {item.title}
                    </h4>
                    <span className="text-xs text-slate-500 whitespace-nowrap ml-2">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                  </div>
                  
                  <p className="text-xs text-slate-400 truncate mb-1">
                    {item.description}
                  </p>
                  
                  {item.agent && (
                    <div className="flex items-center space-x-1">
                      <Badge variant="outline" className="text-xs px-1.5 py-0">
                        {item.agent}
                      </Badge>
                    </div>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Activity Summary */}
      <div className="pt-3 border-t border-slate-700/50">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Completed Today</span>
            <span className="text-green-400 font-medium">
              {tasks.filter(task => {
                if (task.status !== 'completed' || !task.completed_at) return false
                const completedDate = new Date(task.completed_at)
                const today = new Date()
                return completedDate.toDateString() === today.toDateString()
              }).length}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Failed Today</span>
            <span className="text-red-400 font-medium">
              {tasks.filter(task => {
                if (task.status !== 'failed') return false
                const updatedDate = new Date(task.updated_at)
                const today = new Date()
                return updatedDate.toDateString() === today.toDateString()
              }).length}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="pt-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full text-xs text-slate-400 hover:text-slate-300 py-2 border border-slate-700/50 rounded-md hover:bg-slate-800/30 transition-all duration-200"
        >
          View All Activity
        </motion.button>
      </div>
    </div>
  )
}