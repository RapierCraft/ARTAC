'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Filter, 
  Users, 
  Activity, 
  Clock, 
  Zap,
  MoreVertical,
  Play,
  Pause,
  Settings,
  Trash2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AgentCard } from './agent-card'
import { useSystemStore } from '@/stores/system-store'
import { cn } from '@/lib/utils'

export function AgentsMonitoring() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterLevel, setFilterLevel] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('performance')
  
  const { agents, agentStatuses } = useSystemStore()

  // Filter and sort agents
  const filteredAgents = useMemo(() => {
    let filtered = agents.filter(agent => {
      const matchesSearch = !searchTerm || 
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.role.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesLevel = filterLevel === 'all' || agent.level === filterLevel
      
      const status = agentStatuses[agent.id]?.status || agent.status
      const matchesStatus = filterStatus === 'all' || status === filterStatus
      
      return matchesSearch && matchesLevel && matchesStatus
    })

    // Sort agents
    filtered.sort((a, b) => {
      const aStatus = agentStatuses[a.id]
      const bStatus = agentStatuses[b.id]
      
      switch (sortBy) {
        case 'performance':
          const aPerf = aStatus?.performance_score || a.performance_score
          const bPerf = bStatus?.performance_score || b.performance_score
          return bPerf - aPerf
        case 'name':
          return a.name.localeCompare(b.name)
        case 'level':
          const levelOrder = ['executive', 'management', 'development', 'execution']
          return levelOrder.indexOf(a.level) - levelOrder.indexOf(b.level)
        case 'tasks':
          const aTasks = aStatus?.active_tasks || 0
          const bTasks = bStatus?.active_tasks || 0
          return bTasks - aTasks
        default:
          return 0
      }
    })

    return filtered
  }, [agents, agentStatuses, searchTerm, filterLevel, filterStatus, sortBy])

  // Calculate summary stats
  const stats = useMemo(() => {
    const total = filteredAgents.length
    const active = filteredAgents.filter(agent => 
      (agentStatuses[agent.id]?.status || agent.status) === 'active'
    ).length
    const busy = filteredAgents.filter(agent => 
      (agentStatuses[agent.id]?.status || agent.status) === 'busy'
    ).length
    const avgPerformance = total > 0 
      ? filteredAgents.reduce((sum, agent) => 
          sum + (agentStatuses[agent.id]?.performance_score || agent.performance_score), 0
        ) / total 
      : 0

    return { total, active, busy, avgPerformance }
  }, [filteredAgents, agentStatuses])

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Agent Monitoring</h1>
            <p className="text-muted-foreground">Monitor and manage your AI development team</p>
          </div>
          <Button className="bg-artac-600 hover:bg-accent">
            <Users className="w-4 h-4 mr-2" />
            Deploy New Agent
          </Button>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search agents by name or role..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-muted/50 border-slate-700 text-white"
              />
            </div>
          </div>
          
          <div className="flex gap-2">
            <Select value={filterLevel} onValueChange={setFilterLevel}>
              <SelectTrigger className="w-32 bg-muted/50 border-slate-700 text-white">
                <SelectValue placeholder="Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="executive">Executive</SelectItem>
                <SelectItem value="management">Management</SelectItem>
                <SelectItem value="development">Development</SelectItem>
                <SelectItem value="execution">Execution</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-32 bg-muted/50 border-slate-700 text-white">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="busy">Busy</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="terminated">Terminated</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-36 bg-muted/50 border-slate-700 text-white">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="performance">Performance</SelectItem>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="level">Level</SelectItem>
                <SelectItem value="tasks">Active Tasks</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-muted/30 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-primary" />
                <div>
                  <p className="text-2xl font-bold text-white">{stats.total}</p>
                  <p className="text-xs text-muted-foreground">Total Agents</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-muted/30 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-green-500" />
                <div>
                  <p className="text-2xl font-bold text-white">{stats.active}</p>
                  <p className="text-xs text-muted-foreground">Active</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-muted/30 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                <div>
                  <p className="text-2xl font-bold text-white">{stats.busy}</p>
                  <p className="text-xs text-muted-foreground">Busy</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-muted/30 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold text-white">{stats.avgPerformance.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">Avg Performance</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-6">
          {filteredAgents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Users className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-muted-foreground mb-2">No agents found</h3>
              <p className="text-muted-foreground text-center max-w-sm">
                Try adjusting your search terms or filters to find the agents you're looking for.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredAgents.map((agent, index) => (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <AgentCard 
                    agent={agent} 
                    status={agentStatuses[agent.id]} 
                  />
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}