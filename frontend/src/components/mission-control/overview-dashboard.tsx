'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, 
  Users, 
  Clock, 
  Zap, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Code,
  Shield,
  Brain
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { MetricCard } from './metric-card'
import { SystemHealthChart } from './system-health-chart'
import { AgentPerformanceChart } from './agent-performance-chart'
import { RecentActivity } from './recent-activity'
import { useSystemStore } from '@/stores/system-store'

export function OverviewDashboard() {
  const { systemStatus, agents, agentStatuses, tasks } = useSystemStore()

  // Calculate metrics
  const metrics = useMemo(() => {
    const totalAgents = systemStatus?.total_agents || 0
    const activeAgents = systemStatus?.active_agents || 0
    const busyAgents = systemStatus?.busy_agents || 0
    const totalTasks = systemStatus?.total_active_tasks || 0
    
    const completedTasks = tasks.filter(task => task.status === 'completed').length
    const failedTasks = tasks.filter(task => task.status === 'failed').length
    
    const avgPerformance = agents.length > 0 
      ? agents.reduce((sum, agent) => sum + agent.performance_score, 0) / agents.length 
      : 0

    const systemHealth = totalAgents > 0 ? (activeAgents / totalAgents) * 100 : 0

    return {
      totalAgents,
      activeAgents,
      busyAgents,
      totalTasks,
      completedTasks,
      failedTasks,
      avgPerformance,
      systemHealth,
      taskSuccessRate: totalTasks > 0 ? ((completedTasks / totalTasks) * 100) : 100,
    }
  }, [systemStatus, agents, tasks])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="p-6 space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Mission Control Overview</h1>
            <p className="text-slate-400">Real-time system monitoring and analytics</p>
          </div>
          <div className="flex items-center space-x-3">
            <Badge 
              variant={metrics.systemHealth > 90 ? "success" : metrics.systemHealth > 70 ? "warning" : "destructive"}
              className="text-sm"
            >
              System Health: {metrics.systemHealth.toFixed(1)}%
            </Badge>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-slate-400">Live</span>
            </div>
          </div>
        </motion.div>

        {/* Key Metrics */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Active Agents"
            value={metrics.activeAgents}
            total={metrics.totalAgents}
            icon={Users}
            trend={+5}
            color="text-blue-500"
          />
          <MetricCard
            title="Active Tasks"
            value={metrics.totalTasks}
            icon={Code}
            trend={+12}
            color="text-green-500"
          />
          <MetricCard
            title="Success Rate"
            value={`${metrics.taskSuccessRate.toFixed(1)}%`}
            icon={CheckCircle}
            trend={+2.3}
            color="text-emerald-500"
          />
          <MetricCard
            title="Avg Performance"
            value={`${metrics.avgPerformance.toFixed(1)}%`}
            icon={TrendingUp}
            trend={+1.8}
            color="text-purple-500"
          />
        </motion.div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* System Health Chart */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <Card className="bg-slate-800/50 border-slate-700/50 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-artac-500" />
                  <span>System Health</span>
                </CardTitle>
                <CardDescription>Real-time system performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <SystemHealthChart />
              </CardContent>
            </Card>
          </motion.div>

          {/* Agent Status Summary */}
          <motion.div variants={itemVariants}>
            <Card className="bg-slate-800/50 border-slate-700/50 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Users className="w-5 h-5 text-blue-500" />
                  <span>Agent Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Agent Level Breakdown */}
                {['executive', 'management', 'development', 'execution'].map((level) => {
                  const levelAgents = agents.filter(agent => agent.level === level)
                  const activeLevelAgents = levelAgents.filter(agent => 
                    agentStatuses[agent.id]?.status === 'active'
                  ).length
                  
                  const levelColors = {
                    executive: 'text-yellow-500',
                    management: 'text-blue-500',
                    development: 'text-green-500',
                    execution: 'text-purple-500',
                  }

                  return (
                    <div key={level} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-medium capitalize ${levelColors[level as keyof typeof levelColors]}`}>
                          {level}
                        </span>
                        <span className="text-sm text-slate-400">
                          {activeLevelAgents}/{levelAgents.length}
                        </span>
                      </div>
                      <Progress 
                        value={levelAgents.length > 0 ? (activeLevelAgents / levelAgents.length) * 100 : 0}
                        className="h-2"
                      />
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </motion.div>

          {/* Agent Performance Chart */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <Card className="bg-slate-800/50 border-slate-700/50 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-purple-500" />
                  <span>Agent Performance</span>
                </CardTitle>
                <CardDescription>Performance metrics across agent hierarchy</CardDescription>
              </CardHeader>
              <CardContent>
                <AgentPerformanceChart />
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Activity */}
          <motion.div variants={itemVariants}>
            <Card className="bg-slate-800/50 border-slate-700/50 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-orange-500" />
                  <span>Recent Activity</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <RecentActivity />
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* System Alerts */}
        <motion.div variants={itemVariants}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                <span>System Alerts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {metrics.failedTasks > 0 && (
                  <div className="flex items-center space-x-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-400">
                        {metrics.failedTasks} tasks have failed
                      </p>
                      <p className="text-xs text-red-300/70">
                        Review and restart failed tasks in the Tasks tab
                      </p>
                    </div>
                  </div>
                )}
                
                {metrics.systemHealth < 80 && (
                  <div className="flex items-center space-x-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <Shield className="w-4 h-4 text-yellow-500" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-yellow-400">
                        System health below optimal
                      </p>
                      <p className="text-xs text-yellow-300/70">
                        Consider scaling up agent capacity
                      </p>
                    </div>
                  </div>
                )}

                {metrics.failedTasks === 0 && metrics.systemHealth >= 80 && (
                  <div className="flex items-center space-x-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-400">
                        All systems operational
                      </p>
                      <p className="text-xs text-green-300/70">
                        No critical alerts at this time
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}