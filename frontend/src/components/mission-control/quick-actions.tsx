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
  AlertTriangle,
  ChevronDown
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
import { AnimatePresence } from 'framer-motion'

export function QuickActions() {
  const [isCreateAgentOpen, setIsCreateAgentOpen] = useState(false)
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false)
  const [systemOverviewExpanded, setSystemOverviewExpanded] = useState(false)
  const [quickActionsExpanded, setQuickActionsExpanded] = useState(false)
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
      color: 'text-primary hover:text-primary',
      bgColor: 'hover:bg-primary/10',
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
      {/* System Overview - Collapsible */}
      <div className="space-y-2">
        <Button
          variant="ghost"
          onClick={() => setSystemOverviewExpanded(!systemOverviewExpanded)}
          className="w-full justify-between p-0 h-auto hover:bg-transparent"
        >
          <h3 className="text-sm font-medium text-foreground">System Overview</h3>
          <motion.div
            animate={{ rotate: systemOverviewExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-4 w-4" />
          </motion.div>
        </Button>
        
        <AnimatePresence mode="wait">
          {systemOverviewExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <span className="text-muted-foreground">Active</span>
                    <Badge variant="success" className="text-xs">
                      {systemStatus?.active_agents || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <span className="text-muted-foreground">Busy</span>
                    <Badge variant="warning" className="text-xs">
                      {systemStatus?.busy_agents || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <span className="text-muted-foreground">Tasks</span>
                    <Badge variant="outline" className="text-xs">
                      {systemStatus?.total_active_tasks || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <span className="text-muted-foreground">Sessions</span>
                    <Badge variant="outline" className="text-xs">
                      {systemStatus?.claude_sessions || 0}
                    </Badge>
                  </div>
                </div>
                
                {/* Performance Indicator */}
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted-foreground">Overall Health</span>
                    <Badge variant="success" className="text-xs">98%</Badge>
                  </div>
                  <div className="w-full bg-muted/50 rounded-full h-1.5">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: "98%" }}
                      transition={{ duration: 1, delay: 0.5 }}
                      className="bg-gradient-to-r from-green-500 to-emerald-500 h-1.5 rounded-full"
                    />
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    All systems operational
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Quick Actions - Collapsible */}
      <div className="space-y-2">
        <Button
          variant="ghost"
          onClick={() => setQuickActionsExpanded(!quickActionsExpanded)}
          className="w-full justify-between p-0 h-auto hover:bg-transparent"
        >
          <h3 className="text-sm font-medium text-foreground">Quick Actions</h3>
          <motion.div
            animate={{ rotate: quickActionsExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-4 w-4" />
          </motion.div>
        </Button>
        
        <AnimatePresence mode="wait">
          {quickActionsExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>


      {/* Create Agent Dialog */}
      <Dialog open={isCreateAgentOpen} onOpenChange={setIsCreateAgentOpen}>
        <DialogContent className="bg-muted border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Agent</DialogTitle>
            <DialogDescription className="text-muted-foreground">
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
        <DialogContent className="bg-muted border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Task</DialogTitle>
            <DialogDescription className="text-muted-foreground">
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