'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  User, 
  Activity, 
  Clock, 
  Code, 
  MoreHorizontal,
  Play,
  Pause,
  Trash2,
  Settings
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Agent, AgentStatus } from '@/types/agent'
import { useSystemStore } from '@/stores/system-store'
import { cn, formatRelativeTime, getStatusColor } from '@/lib/utils'

interface AgentHierarchyNodeProps {
  agent: Agent
  status?: AgentStatus
}

export function AgentHierarchyNode({ agent, status }: AgentHierarchyNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { assignTask, updateAgentStatus } = useSystemStore()

  const handleAssignTask = async () => {
    // This would open a task assignment dialog
    console.log('Assign task to', agent.name)
  }

  const handleToggleStatus = async () => {
    if (status?.status === 'active') {
      await updateAgentStatus(agent.id, 'suspended')
    } else {
      await updateAgentStatus(agent.id, 'active')
    }
  }

  const handleTerminate = async () => {
    await updateAgentStatus(agent.id, 'terminated')
  }

  const getStatusIndicator = () => {
    const currentStatus = status?.status || agent.status
    
    switch (currentStatus) {
      case 'active':
        return <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
      case 'busy':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
      case 'suspended':
        return <div className="w-2 h-2 bg-orange-500 rounded-full" />
      case 'terminated':
        return <div className="w-2 h-2 bg-red-500 rounded-full" />
      default:
        return <div className="w-2 h-2 bg-gray-500 rounded-full" />
    }
  }

  const getPerformanceColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="group"
    >
      <Card className={cn(
        "bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/50 transition-all duration-200",
        "hover:border-artac-500/30"
      )}>
        <div className="p-3 space-y-2">
          {/* Agent Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 min-w-0 flex-1">
              {getStatusIndicator()}
              <div className="min-w-0 flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-medium text-white truncate">
                    {agent.name}
                  </h4>
                  <Badge 
                    variant="outline" 
                    className="text-xs shrink-0"
                  >
                    {agent.role}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 truncate">
                  {agent.specialization.slice(0, 2).join(', ')}
                  {agent.specialization.length > 2 && '...'}
                </p>
              </div>
            </div>

            {/* Agent Actions */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleAssignTask}>
                  <Code className="mr-2 h-4 w-4" />
                  Assign Task
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleToggleStatus}>
                  {status?.status === 'active' ? (
                    <>
                      <Pause className="mr-2 h-4 w-4" />
                      Suspend
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Activate
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  Configure
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={handleTerminate}
                  className="text-red-400 focus:text-red-400"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Terminate
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Agent Metrics */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1">
                <Activity className="w-3 h-3 text-slate-400" />
                <span className={getPerformanceColor(status?.performance_score || agent.performance_score)}>
                  {Math.round(status?.performance_score || agent.performance_score)}%
                </span>
              </div>
              
              {status?.active_tasks !== undefined && (
                <div className="flex items-center space-x-1">
                  <Code className="w-3 h-3 text-slate-400" />
                  <span className="text-slate-300">
                    {status.active_tasks} tasks
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-1 text-slate-500">
              <Clock className="w-3 h-3" />
              <span>{formatRelativeTime(agent.updated_at)}</span>
            </div>
          </div>

          {/* Claude Session Indicator */}
          {status?.claude_session && (
            <div className="flex items-center justify-between pt-2 border-t border-slate-700/50">
              <div className="flex items-center space-x-2">
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  status.claude_session.active ? "bg-green-500 animate-pulse" : "bg-gray-500"
                )} />
                <span className="text-xs text-slate-400">
                  Claude Session: {status.claude_session.active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              {status.claude_session.active && status.claude_session.process_id && (
                <Badge variant="outline" className="text-xs">
                  PID: {status.claude_session.process_id}
                </Badge>
              )}
            </div>
          )}

          {/* Expandable Details */}
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="pt-2 border-t border-slate-700/50 space-y-2"
            >
              <div className="text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Model:</span>
                  <span className="text-slate-300">{agent.model_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Level:</span>
                  <span className="text-slate-300 capitalize">{agent.level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Created:</span>
                  <span className="text-slate-300">{formatRelativeTime(agent.created_at)}</span>
                </div>
              </div>
              
              {agent.specialization.length > 0 && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Specializations:</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.specialization.map((spec, index) => (
                      <Badge 
                        key={index} 
                        variant="secondary" 
                        className="text-xs"
                      >
                        {spec.replace('_', ' ')}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Expand/Collapse Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full h-6 text-xs text-slate-500 hover:text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            {isExpanded ? 'Less' : 'More'} Details
          </Button>
        </div>
      </Card>
    </motion.div>
  )
}