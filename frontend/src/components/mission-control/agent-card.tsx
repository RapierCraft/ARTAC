'use client'

import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Agent, AgentStatus } from '@/types/agent'
import { cn, formatRelativeTime } from '@/lib/utils'

interface AgentCardProps {
  agent: Agent
  status?: AgentStatus
}

export function AgentCard({ agent, status }: AgentCardProps) {
  const getStatusColor = (currentStatus: string) => {
    switch (currentStatus) {
      case 'active': return 'bg-green-500'
      case 'busy': return 'bg-yellow-500 animate-pulse'
      case 'suspended': return 'bg-orange-500'
      case 'terminated': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const currentStatus = status?.status || agent.status
  const performance = status?.performance_score || agent.performance_score

  return (
    <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring", stiffness: 300 }}>
      <Card className="bg-muted/50 border-slate-700/50 hover:bg-muted/70 transition-all duration-200">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className={cn("w-3 h-3 rounded-full", getStatusColor(currentStatus))} />
              <div>
                <h3 className="font-semibold text-white">{agent.name}</h3>
                <p className="text-sm text-muted-foreground">{agent.role}</p>
              </div>
            </div>
            <Badge variant="outline" className="capitalize">
              {agent.level}
            </Badge>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Performance</span>
              <span className={cn(
                "text-sm font-medium",
                performance >= 80 ? "text-green-400" : 
                performance >= 60 ? "text-yellow-400" : "text-red-400"
              )}>
                {performance.toFixed(1)}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Active Tasks</span>
              <span className="text-sm text-muted-foreground">{status?.active_tasks || 0}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Last Updated</span>
              <span className="text-sm text-muted-foreground">{formatRelativeTime(agent.updated_at)}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}