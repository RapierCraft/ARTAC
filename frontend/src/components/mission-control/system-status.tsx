'use client'

import { motion } from 'framer-motion'
import { CheckCircle, AlertCircle, XCircle, Loader } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useSystemStore } from '@/stores/system-store'
import { cn } from '@/lib/utils'

export function SystemStatusIndicator() {
  const { systemStatus, isInitialized, isLoading, error } = useSystemStore()

  const getStatusInfo = () => {
    if (isLoading) {
      return {
        icon: Loader,
        text: 'Initializing',
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/20'
      }
    }

    if (error) {
      return {
        icon: XCircle,
        text: 'Error',
        color: 'text-red-500',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/20'
      }
    }

    if (!isInitialized || !systemStatus) {
      return {
        icon: AlertCircle,
        text: 'Offline',
        color: 'text-orange-500',
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/20'
      }
    }

    return {
      icon: CheckCircle,
      text: 'Operational',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/20'
    }
  }

  const status = getStatusInfo()
  const IconComponent = status.icon

  return (
    <div className="flex items-center space-x-3">
      {/* Status Indicator */}
      <div className={cn(
        "flex items-center space-x-2 px-3 py-1.5 rounded-full border",
        status.bgColor,
        status.borderColor
      )}>
        <motion.div
          animate={isLoading ? { rotate: 360 } : {}}
          transition={isLoading ? { duration: 2, repeat: Infinity, ease: "linear" } : {}}
        >
          <IconComponent className={cn("h-4 w-4", status.color)} />
        </motion.div>
        <span className={cn("text-sm font-medium", status.color)}>
          {status.text}
        </span>
      </div>

      {/* System Metrics */}
      {systemStatus && isInitialized && (
        <div className="hidden lg:flex items-center space-x-4 text-xs text-muted-foreground">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>{systemStatus.active_agents}/{systemStatus.total_agents} Agents</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span>{systemStatus.claude_sessions} Sessions</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            <span>{systemStatus.total_active_tasks} Tasks</span>
          </div>
        </div>
      )}
    </div>
  )
}