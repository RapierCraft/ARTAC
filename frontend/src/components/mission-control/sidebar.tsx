'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Crown, 
  Shield, 
  Users, 
  Code, 
  Wrench,
  ChevronRight,
  ChevronDown,
  Plus,
  Play,
  Pause,
  Settings,
  Search,
  Filter,
  Activity
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { AgentHierarchyNode } from './agent-hierarchy-node'
import { QuickActions } from './quick-actions'
import { useSystemStore } from '@/stores/system-store'
import { cn } from '@/lib/utils'

interface SidebarProps {
  collapsed: boolean
}

const AGENT_LEVEL_ICONS = {
  executive: Crown,
  management: Shield,
  development: Code,
  execution: Wrench,
}

const AGENT_LEVEL_COLORS = {
  executive: 'text-yellow-500',
  management: 'text-primary', 
  development: 'text-green-500',
  execution: 'text-purple-500',
}

export function Sidebar({ collapsed }: SidebarProps) {
  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(
    new Set(['executive', 'management'])
  )
  const [searchTerm, setSearchTerm] = useState('')
  const [systemOverviewExpanded, setSystemOverviewExpanded] = useState(false)
  const [filterLevel, setFilterLevel] = useState<string | null>(null)
  
  const { agents, agentStatuses, systemStatus } = useSystemStore()
  
  // Group agents by level
  const agentsByLevel = useMemo(() => {
    const grouped = agents.reduce((acc, agent) => {
      if (!acc[agent.level]) {
        acc[agent.level] = []
      }
      acc[agent.level].push(agent)
      return acc
    }, {} as Record<string, typeof agents>)
    
    // Sort agents within each level by role and name
    Object.keys(grouped).forEach(level => {
      grouped[level].sort((a, b) => {
        if (a.role !== b.role) return a.role.localeCompare(b.role)
        return a.name.localeCompare(b.name)
      })
    })
    
    return grouped
  }, [agents])

  // Filter agents based on search and level filter
  const filteredAgentsByLevel = useMemo(() => {
    const filtered = { ...agentsByLevel }
    
    Object.keys(filtered).forEach(level => {
      filtered[level] = filtered[level].filter(agent => {
        const matchesSearch = !searchTerm || 
          agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          agent.role.toLowerCase().includes(searchTerm.toLowerCase())
        
        const matchesLevel = !filterLevel || agent.level === filterLevel
        
        return matchesSearch && matchesLevel
      })
    })
    
    return filtered
  }, [agentsByLevel, searchTerm, filterLevel])

  const toggleLevel = (level: string) => {
    const newExpanded = new Set(expandedLevels)
    if (newExpanded.has(level)) {
      newExpanded.delete(level)
    } else {
      newExpanded.add(level)
    }
    setExpandedLevels(newExpanded)
  }

  const getLevelStats = (level: string) => {
    const levelAgents = agentsByLevel[level] || []
    const active = levelAgents.filter(agent => 
      agentStatuses[agent.id]?.status === 'active'
    ).length
    const busy = levelAgents.filter(agent => 
      agentStatuses[agent.id]?.status === 'busy'
    ).length
    
    return { total: levelAgents.length, active, busy }
  }

  if (collapsed) {
    return (
      <div className="flex flex-col h-full p-2 space-y-2">
        {/* Collapsed Header */}
        <div className="flex flex-col items-center space-y-2 py-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center"
          >
            <Crown className="w-4 h-4 text-white" />
          </motion.div>
        </div>

        {/* Collapsed Level Indicators */}
        <div className="flex flex-col space-y-1">
          {Object.keys(AGENT_LEVEL_ICONS).map((level) => {
            const IconComponent = AGENT_LEVEL_ICONS[level as keyof typeof AGENT_LEVEL_ICONS]
            const stats = getLevelStats(level)
            const color = AGENT_LEVEL_COLORS[level as keyof typeof AGENT_LEVEL_COLORS]
            
            return (
              <Button
                key={level}
                variant="ghost"
                size="sm"
                className={cn(
                  "w-full h-10 p-0 justify-center relative",
                  "hover:bg-muted/50"
                )}
                onClick={() => toggleLevel(level)}
              >
                <IconComponent className={cn("w-4 h-4", color)} />
                {stats.active > 0 && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full text-xs flex items-center justify-center text-white">
                    {stats.active}
                  </div>
                )}
              </Button>
            )
          })}
        </div>

        {/* Quick Actions - Collapsed */}
        <div className="flex-1 flex flex-col justify-end space-y-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full h-10 p-0 justify-center text-green-500 hover:bg-green-500/10"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="w-full h-10 p-0 justify-center text-primary hover:bg-primary/10"
          >
            <Play className="w-4 h-4" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border flex-shrink-0">
        <div className="flex items-center space-x-3">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center"
          >
            <Crown className="w-4 h-4 text-white" />
          </motion.div>
          <div>
            <h2 className="text-lg font-semibold text-white">Agent Hierarchy</h2>
            <p className="text-xs text-muted-foreground">
              {systemStatus?.total_agents || 0} total agents
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="p-4 space-y-3 border-b border-border flex-shrink-0">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-muted/50 border border-border rounded-md text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary"
          />
        </div>

        {/* Level Filter */}
        <div className="flex space-x-1 overflow-x-auto pb-2 scrollbar-thin">
          <Button
            variant={filterLevel === null ? "default" : "ghost"}
            size="sm"
            onClick={() => setFilterLevel(null)}
            className="text-xs flex-shrink-0"
          >
            All
          </Button>
          {Object.keys(AGENT_LEVEL_ICONS).map((level) => (
            <Button
              key={level}
              variant={filterLevel === level ? "default" : "ghost"}
              size="sm"
              onClick={() => setFilterLevel(filterLevel === level ? null : level)}
              className="text-xs capitalize flex-shrink-0"
            >
              {level}
            </Button>
          ))}
        </div>
      </div>

      {/* Agent Hierarchy */}
      <div className="flex-1 overflow-y-auto custom-scrollbar min-h-0">
        <div className="p-2 space-y-1 pb-6">
          {Object.keys(AGENT_LEVEL_ICONS).map((level) => {
            const IconComponent = AGENT_LEVEL_ICONS[level as keyof typeof AGENT_LEVEL_ICONS]
            const color = AGENT_LEVEL_COLORS[level as keyof typeof AGENT_LEVEL_COLORS]
            const levelAgents = filteredAgentsByLevel[level] || []
            const stats = getLevelStats(level)
            const isExpanded = expandedLevels.has(level)
            
            if (levelAgents.length === 0 && filterLevel) return null

            return (
              <div key={level} className="space-y-1">
                {/* Level Header */}
                <Button
                  variant="ghost"
                  onClick={() => toggleLevel(level)}
                  className="w-full justify-start h-10 px-3 hover:bg-muted/50"
                >
                  <motion.div
                    animate={{ rotate: isExpanded ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </motion.div>
                  <IconComponent className={cn("w-4 h-4 ml-2", color)} />
                  <span className="ml-2 font-medium capitalize text-white">
                    {level}
                  </span>
                  <div className="ml-auto flex items-center space-x-1">
                    <Badge variant="outline" className="text-xs">
                      {stats.total}
                    </Badge>
                    {stats.active > 0 && (
                      <Badge variant="success" className="text-xs">
                        {stats.active}
                      </Badge>
                    )}
                    {stats.busy > 0 && (
                      <Badge variant="warning" className="text-xs">
                        {stats.busy}
                      </Badge>
                    )}
                  </div>
                </Button>

                {/* Level Agents */}
                <AnimatePresence mode="wait">
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="ml-6 space-y-1">
                        {levelAgents.map((agent) => (
                          <AgentHierarchyNode
                            key={agent.id}
                            agent={agent}
                            status={agentStatuses[agent.id]}
                          />
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </div>


      {/* Quick Actions */}
      <div className="p-4 border-t border-border flex-shrink-0">
        <QuickActions />
      </div>
    </div>
  )
}