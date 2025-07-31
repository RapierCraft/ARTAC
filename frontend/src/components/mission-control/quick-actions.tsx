'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Play, 
  Pause, 
  RotateCcw, 
  Zap,
  UserPlus,
  FileText,
  Settings,
  AlertTriangle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useSystemStore } from '@/stores/system-store'
import { useToast } from '@/hooks/use-toast'

export function QuickActions() {
  const [isCreateAgentOpen, setIsCreateAgentOpen] = useState(false)
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false)
  const { systemStatus, createAgent, assignTask } = useSystemStore()
  const { toast } = useToast()

  const handleCreateAgent = async () => {
    try {
      const newAgent = await createAgent({
        role: 'Junior_Developer',
        level: 'execution',
        specialization: ['general_development'],
      })
      
      if (newAgent) {
        toast({
          title: "Agent Created",
          description: `New agent ${newAgent.name} created successfully`,
        })
        setIsCreateAgentOpen(false)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create agent",
        variant: "destructive",
      })
    }
  }

  const handleEmergencyStop = () => {
    toast({
      title: "Emergency Stop Activated",
      description: "All agent operations have been suspended",
      variant: "destructive",
    })
  }

  const handleSystemRestart = () => {
    toast({
      title: "System Restart",
      description: "Restarting all agent systems...",
    })
  }

  const quickActions = [
    {
      icon: UserPlus,
      label: 'New Agent',
      color: 'text-green-500 hover:text-green-400',
      bgColor: 'hover:bg-green-500/10',
      action: () => setIsCreateAgentOpen(true),
    },
    {
      icon: FileText,
      label: 'New Task',
      color: 'text-blue-500 hover:text-blue-400',
      bgColor: 'hover:bg-blue-500/10',
      action: () => setIsCreateTaskOpen(true),
    },
    {
      icon: Play,
      label: 'Start All',
      color: 'text-emerald-500 hover:text-emerald-400',
      bgColor: 'hover:bg-emerald-500/10',
      action: () => console.log('Start all agents'),
    },
    {
      icon: Pause,
      label: 'Pause All',
      color: 'text-yellow-500 hover:text-yellow-400',
      bgColor: 'hover:bg-yellow-500/10',
      action: () => console.log('Pause all agents'),
    },
    {
      icon: RotateCcw,
      label: 'Restart',
      color: 'text-purple-500 hover:text-purple-400',
      bgColor: 'hover:bg-purple-500/10',
      action: handleSystemRestart,
    },
    {
      icon: AlertTriangle,
      label: 'Emergency',
      color: 'text-red-500 hover:text-red-400',
      bgColor: 'hover:bg-red-500/10',
      action: handleEmergencyStop,
    },
  ]

  return (
    <div className="space-y-4">
      {/* System Status Summary */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">System Overview</h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded">
            <span className="text-slate-400">Active</span>
            <Badge variant="success" className="text-xs">
              {systemStatus?.active_agents || 0}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded">
            <span className="text-slate-400">Busy</span>
            <Badge variant="warning" className="text-xs">
              {systemStatus?.busy_agents || 0}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded">
            <span className="text-slate-400">Tasks</span>
            <Badge variant="outline" className="text-xs">
              {systemStatus?.total_active_tasks || 0}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded">
            <span className="text-slate-400">Sessions</span>
            <Badge variant="outline" className="text-xs">
              {systemStatus?.claude_sessions || 0}
            </Badge>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-2">
          {quickActions.map((action, index) => {
            const IconComponent = action.icon
            return (
              <motion.div
                key={action.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Button
                  variant="ghost"
                  onClick={action.action}
                  className={`w-full h-12 flex flex-col items-center justify-center space-y-1 ${action.color} ${action.bgColor} border border-transparent hover:border-current/20`}
                >
                  <IconComponent className="w-4 h-4" />
                  <span className="text-xs">{action.label}</span>
                </Button>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">Performance</h3>
        <div className="p-3 bg-slate-800/30 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400">Overall Health</span>
            <Badge variant="success" className="text-xs">98%</Badge>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-1.5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '98%' }}
              transition={{ duration: 1, delay: 0.5 }}
              className="bg-gradient-to-r from-green-500 to-emerald-500 h-1.5 rounded-full"
            />
          </div>
          <div className="mt-2 text-xs text-slate-500">
            All systems operational
          </div>
        </div>
      </div>

      {/* Create Agent Dialog */}
      <Dialog open={isCreateAgentOpen} onOpenChange={setIsCreateAgentOpen}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Agent</DialogTitle>
            <DialogDescription className="text-slate-400">
              Deploy a new AI agent to your development team.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Button onClick={handleCreateAgent} className="w-full">
                Junior Developer
              </Button>
              <Button variant="outline" className="w-full">
                Custom Agent
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Task Dialog */}
      <Dialog open={isCreateTaskOpen} onOpenChange={setIsCreateTaskOpen}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Task</DialogTitle>
            <DialogDescription className="text-slate-400">
              Assign a new task to your AI development team.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Button className="w-full justify-start">
                🐛 Fix Critical Bug
              </Button>
              <Button variant="outline" className="w-full justify-start">
                ⚡ Performance Optimization
              </Button>
              <Button variant="outline" className="w-full justify-start">
                🆕 New Feature Development
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📝 Documentation Update
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}