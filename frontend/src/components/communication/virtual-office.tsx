'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  MessageSquare, 
  Activity, 
  TrendingUp, 
  Clock, 
  Zap,
  Target,
  Crown,
  Brain,
  Briefcase,
  BarChart3,
  PieChart,
  LineChart,
  Send,
  AlertCircle,
  CheckCircle,
  Timer,
  Server,
  Cpu,
  HardDrive,
  Wifi,
  Bot
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { BarChart, LineChart as CustomLineChart, DonutChart } from '@/components/ui/chart'
import { useCommunicationStore } from '@/stores/communication-store'
import { useProjectStore } from '@/stores/project-store'

interface ActivityItem {
  id: string
  type: 'project_created' | 'agent_hired' | 'message_sent' | 'task_completed'
  title: string
  description: string
  timestamp: Date
  actor: string
  icon: string
}

export function VirtualOffice() {
  const { users, allChannels, messages, sendMessage } = useCommunicationStore()
  const { projects } = useProjectStore()
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([])
  const [ceoChatInput, setCeoChatInput] = useState('')
  const [ceoMessages, setCeoMessages] = useState<any[]>([])
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 45,
    memory: 62,
    storage: 38,
    uptime: '7d 14h 23m'
  })

  // Load CEO messages from the CEO channel
  useEffect(() => {
    const ceoChannelMessages = messages['ceo'] || []
    setCeoMessages(ceoChannelMessages.slice(-5)) // Last 5 messages
  }, [messages])

  // Generate recent activity from channels and messages
  useEffect(() => {
    const activities: ActivityItem[] = []
    
    // Add project creation activities
    projects.forEach(project => {
      activities.push({
        id: `project-${project.id}`,
        type: 'project_created',
        title: 'New Project Launched',
        description: `${project.name} has been initiated by the CEO`,
        timestamp: project.createdAt,
        actor: 'ARTAC CEO',
        icon: '🎯'
      })
    })

    // Add recent messages from all channels
    Object.entries(messages).forEach(([channelId, channelMessages]) => {
      const recentMessages = channelMessages
        .filter(msg => msg.userId === 'ceo-001' && msg.content.includes('PROJECT'))
        .slice(-3)
        
      recentMessages.forEach(msg => {
        activities.push({
          id: `msg-${msg.id}`,
          type: 'message_sent',
          title: 'CEO Announcement',
          description: msg.content.substring(0, 100) + '...',
          timestamp: msg.timestamp,
          actor: 'ARTAC CEO',
          icon: '📢'
        })
      })
    })

    // Sort by timestamp and take most recent
    activities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    setRecentActivity(activities.slice(0, 8))
  }, [projects, messages])

  const activeAgents = users.filter(user => user.status === 'online' && user.id !== 'current-user')
  const currentUser = users.find(user => user.id === 'current-user') || users[0] // Fallback to first user
  const totalMessages = Object.values(messages).flat().length
  const projectChannels = allChannels.filter(channel => channel.id.startsWith('project-'))

  // Handle CEO chat message
  const handleCeoMessage = async () => {
    if (!ceoChatInput.trim()) return
    
    try {
      await sendMessage('ceo', ceoChatInput)
      setCeoChatInput('')
    } catch (error) {
      console.error('Failed to send CEO message:', error)
    }
  }

  // Generate mock analytics data
  const analyticsData = {
    projectsThisWeek: projects.length,
    agentsHired: activeAgents.length,
    tasksCompleted: Math.floor(Math.random() * 50) + 20,
    systemUptime: 99.8
  }

  return (
    <div className="h-full w-full bg-background overflow-hidden">
      <div className="h-full w-full flex gap-4 p-4">
        {/* Main Content Area - Fixed to utilize full available space */}
        <div className="flex-1 min-w-0 overflow-auto">
          <div className="space-y-6 p-2">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-1"
        >
          <h1 className="text-3xl font-light text-foreground">
            ARTAC Human Resources
          </h1>
          <p className="text-muted-foreground text-sm">
            Agent Management • Performance Monitoring • Organizational Intelligence
          </p>
        </motion.div>

        {/* Key Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Agents</p>
                  <p className="text-3xl font-bold">{users.length}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    <span className="text-green-600">{users.filter(u => u.status === 'online').length} online</span> • 
                    <span className="text-yellow-600 ml-1">{users.filter(u => u.status === 'busy').length} busy</span>
                  </p>
                </div>
                <Users className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Active Projects</p>
                  <p className="text-3xl font-bold">{projects.length}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {projects.length > 0 ? `${Math.round(85)}% avg completion` : 'No active projects'}
                  </p>
                </div>
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Messages Today</p>
                  <p className="text-3xl font-bold">{totalMessages}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {Math.round(totalMessages / Math.max(activeAgents.length, 1))} avg per agent
                  </p>
                </div>
                <MessageSquare className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">System Health</p>
                  <p className="text-3xl font-bold text-green-600">99.8%</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Uptime • Last incident: 3d ago
                  </p>
                </div>
                <Activity className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Agent Performance & Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {/* Agent Status Distribution */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Agent Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <DonutChart
                  data={[
                    { name: 'Online', value: users.filter(u => u.status === 'online').length, color: '#22c55e' },
                    { name: 'Busy', value: users.filter(u => u.status === 'busy').length, color: '#eab308' },
                    { name: 'Offline', value: users.filter(u => u.status === 'offline').length, color: '#6b7280' }
                  ]}
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Weekly Performance</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <BarChart
                  data={[
                    { name: 'Mon', value: 24 },
                    { name: 'Tue', value: 32 },
                    { name: 'Wed', value: 28 },
                    { name: 'Thu', value: 41 },
                    { name: 'Fri', value: 35 },
                    { name: 'Sat', value: 18 },
                    { name: 'Sun', value: 12 }
                  ]}
                  height={160}
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* System Resources */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">System Resources</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <span className="text-sm text-muted-foreground">{systemMetrics.cpu}%</span>
                  </div>
                  <Progress value={systemMetrics.cpu} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Memory</span>
                    <span className="text-sm text-muted-foreground">{systemMetrics.memory}%</span>
                  </div>
                  <Progress value={systemMetrics.memory} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Storage</span>
                    <span className="text-sm text-muted-foreground">{systemMetrics.storage}%</span>
                  </div>
                  <Progress value={systemMetrics.storage} className="h-2" />
                </div>
                <div className="pt-2 border-t">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Uptime</span>
                    <span className="text-sm font-medium text-green-600">{systemMetrics.uptime}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Enhanced Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Tasks Completed</p>
                  <p className="text-xl font-bold">{Math.floor(Math.random() * 50) + 147}</p>
                  <p className="text-xs text-green-600 mt-1">+23% this week</p>
                </div>
                <CheckCircle className="h-6 w-6 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Avg Response</p>
                  <p className="text-xl font-bold">1.8s</p>
                  <p className="text-xs text-green-600 mt-1">-0.7s improved</p>
                </div>
                <Timer className="h-6 w-6 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Success Rate</p>
                  <p className="text-xl font-bold">99.7%</p>
                  <p className="text-xs text-green-600 mt-1">+0.3% improved</p>
                </div>
                <Target className="h-6 w-6 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Agent Load</p>
                  <p className="text-xl font-bold">76%</p>
                  <p className="text-xs text-yellow-600 mt-1">Optimal range</p>
                </div>
                <TrendingUp className="h-6 w-6 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Satisfaction</p>
                  <p className="text-xl font-bold">4.8/5</p>
                  <p className="text-xs text-green-600 mt-1">+0.2 improved</p>
                </div>
                <Crown className="h-6 w-6 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Costs/Hour</p>
                  <p className="text-xl font-bold">$127</p>
                  <p className="text-xs text-green-600 mt-1">-8% reduced</p>
                </div>
                <Briefcase className="h-6 w-6 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Department Performance & Resource Allocation */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg font-medium">Department Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { dept: 'Customer Success', agents: 12, efficiency: 94, workload: 'High', color: 'bg-green-500' },
                  { dept: 'Technical Support', agents: 8, efficiency: 91, workload: 'Medium', color: 'bg-blue-500' },
                  { dept: 'Sales Assistance', agents: 6, efficiency: 97, workload: 'Low', color: 'bg-purple-500' },
                  { dept: 'Quality Assurance', agents: 4, efficiency: 89, workload: 'Medium', color: 'bg-orange-500' },
                ].map((dept, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${dept.color}`} />
                      <div>
                        <p className="text-sm font-medium">{dept.dept}</p>
                        <p className="text-xs text-muted-foreground">{dept.agents} agents</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{dept.efficiency}%</p>
                      <p className={`text-xs px-2 py-1 rounded ${
                        dept.workload === 'High' ? 'bg-red-100 text-red-700' :
                        dept.workload === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {dept.workload}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Skill Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={[
                  { name: 'Technical', value: 15, color: '#3b82f6' },
                  { name: 'Customer Service', value: 12, color: '#10b981' },
                  { name: 'Sales', value: 8, color: '#8b5cf6' },
                  { name: 'Leadership', value: 5, color: '#f59e0b' }
                ]}
                size={140}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Training Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { skill: 'AI Integration', progress: 85, agents: 12 },
                { skill: 'Advanced Analytics', progress: 72, agents: 8 },
                { skill: 'Leadership', progress: 91, agents: 5 },
                { skill: 'Communication', progress: 88, agents: 18 }
              ].map((training, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">{training.skill}</span>
                    <span className="text-sm text-muted-foreground">{training.progress}%</span>
                  </div>
                  <Progress value={training.progress} className="h-2" />
                  <p className="text-xs text-muted-foreground">{training.agents} agents enrolled</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Communication & Productivity Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Daily Message Volume</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <BarChart
                data={[
                  { name: '6AM', value: 12 },
                  { name: '9AM', value: 45 },
                  { name: '12PM', value: 78 },
                  { name: '3PM', value: 92 },
                  { name: '6PM', value: 56 },
                  { name: '9PM', value: 23 }
                ]}
                height={180}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Response Time Trends</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <CustomLineChart
                data={[
                  { name: 'Mon', value: 2.8 },
                  { name: 'Tue', value: 2.3 },
                  { name: 'Wed', value: 1.9 },
                  { name: 'Thu', value: 1.8 },
                  { name: 'Fri', value: 1.7 },
                  { name: 'Sat', value: 2.1 },
                  { name: 'Sun', value: 2.4 }
                ]}
                height={180}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Task Priority Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { priority: 'Critical', count: 3, color: 'bg-red-500', percentage: 8 },
                  { priority: 'High', count: 12, color: 'bg-orange-500', percentage: 32 },
                  { priority: 'Medium', count: 18, color: 'bg-yellow-500', percentage: 47 },
                  { priority: 'Low', count: 5, color: 'bg-green-500', percentage: 13 }
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${item.color}`} />
                      <span className="text-sm font-medium">{item.priority}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-muted-foreground">{item.count} tasks</span>
                      <span className="text-sm font-medium">{item.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity & Agent Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium flex items-center justify-between">
                  Recent Activity
                  <span className="text-xs text-muted-foreground font-normal">
                    Last 24 hours
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {recentActivity.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Activity className="h-8 w-8 mx-auto mb-2" />
                      <p className="text-sm">No recent activity</p>
                    </div>
                  ) : (
                    recentActivity.map((activity, index) => (
                      <div key={activity.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                        <div className="w-2 h-2 rounded-full bg-green-500 mt-2" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{activity.title}</p>
                          <p className="text-xs text-muted-foreground">{activity.actor}</p>
                          <p className="text-xs text-muted-foreground">
                            {activity.timestamp.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Top Performing Agents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {activeAgents.slice(0, 6).map((agent, index) => {
                    const performance = 85 + Math.floor(Math.random() * 15);
                    const tasksCompleted = Math.floor(Math.random() * 8) + 12;
                    const avgResponse = (1.2 + Math.random() * 1.5).toFixed(1);
                    
                    return (
                      <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="text-xs">{agent.avatar}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-sm font-medium">{agent.name}</p>
                            <p className="text-xs text-muted-foreground">{agent.role}</p>
                          </div>
                        </div>
                        <div className="text-right space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-medium">{performance}%</span>
                            <div className={`w-2 h-2 rounded-full ${
                              agent.status === 'online' ? 'bg-green-500' :
                              agent.status === 'busy' ? 'bg-yellow-500' :
                              'bg-gray-400'
                            }`} />
                          </div>
                          <p className="text-xs text-muted-foreground">{tasksCompleted} tasks • {avgResponse}s avg</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Comprehensive Agent Performance Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">Detailed Agent Performance Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left font-medium py-3 px-2">Agent</th>
                    <th className="text-left font-medium py-3 px-2">Department</th>
                    <th className="text-center font-medium py-3 px-2">Status</th>
                    <th className="text-center font-medium py-3 px-2">Tasks</th>
                    <th className="text-center font-medium py-3 px-2">Efficiency</th>
                    <th className="text-center font-medium py-3 px-2">Response Time</th>
                    <th className="text-center font-medium py-3 px-2">Satisfaction</th>
                    <th className="text-center font-medium py-3 px-2">Training</th>
                  </tr>
                </thead>
                <tbody>
                  {activeAgents.map((agent, index) => {
                    const departments = ['Customer Success', 'Technical Support', 'Sales Assistance', 'Quality Assurance'];
                    const department = departments[index % departments.length];
                    const tasksCount = Math.floor(Math.random() * 15) + 8;
                    const efficiency = 85 + Math.floor(Math.random() * 15);
                    const responseTime = (0.8 + Math.random() * 2.0).toFixed(1);
                    const satisfaction = (4.2 + Math.random() * 0.8).toFixed(1);
                    const trainingProgress = 70 + Math.floor(Math.random() * 30);
                    
                    return (
                      <tr key={agent.id} className="border-b hover:bg-muted/20">
                        <td className="py-3 px-2">
                          <div className="flex items-center space-x-2">
                            <Avatar className="h-6 w-6">
                              <AvatarFallback className="text-xs">{agent.avatar}</AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium">{agent.name}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">{department}</td>
                        <td className="py-3 px-2 text-center">
                          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                            agent.status === 'online' ? 'bg-green-100 text-green-800' :
                            agent.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {agent.status}
                          </div>
                        </td>
                        <td className="py-3 px-2 text-center font-medium">{tasksCount}</td>
                        <td className="py-3 px-2 text-center">
                          <div className="flex items-center justify-center space-x-1">
                            <span className={`font-medium ${efficiency >= 90 ? 'text-green-600' : efficiency >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {efficiency}%
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-2 text-center font-medium">{responseTime}s</td>
                        <td className="py-3 px-2 text-center">
                          <div className="flex items-center justify-center space-x-1">
                            <span className="font-medium">{satisfaction}</span>
                            <span className="text-yellow-500">★</span>
                          </div>
                        </td>
                        <td className="py-3 px-2 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <div className="w-12 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-500 h-2 rounded-full" 
                                style={{ width: `${trainingProgress}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium">{trainingProgress}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Project Performance Summary */}
        {projects.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Active Projects</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {projects.slice(0, 4).map((project, index) => (
                    <div key={project.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="text-sm font-medium">{project.name}</p>
                        <p className="text-xs text-muted-foreground">{project.members.length} agents</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-medium text-green-600">On Track</p>
                        <p className="text-xs text-muted-foreground">{Math.floor(75 + Math.random() * 20)}% complete</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">System Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">CPU</p>
                    <p className="text-lg font-medium">{systemMetrics.cpu}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Memory</p>
                    <p className="text-lg font-medium">{systemMetrics.memory}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Storage</p>
                    <p className="text-lg font-medium">{systemMetrics.storage}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Uptime</p>
                    <p className="text-lg font-medium text-green-600">{systemMetrics.uptime}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Organization Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Peak Hours</span>
                  <span className="text-sm font-medium">2PM - 4PM</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Best Department</span>
                  <span className="text-sm font-medium">Sales (97%)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Training Needed</span>
                  <span className="text-sm font-medium">AI Integration</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Next Review</span>
                  <span className="text-sm font-medium">Tomorrow 9AM</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
          </div>
        </div>

        {/* Right Chat Section - Maximum prominence and better space utilization */}
        <div className="w-80 xl:w-96 flex-shrink-0 border border-border rounded-lg bg-card/50 backdrop-blur-sm flex flex-col shadow-lg">
        {/* CEO Chat - Enhanced Header */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-border bg-muted/20 rounded-t-lg">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarFallback className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
                  👑
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-base">ARTAC CEO</h3>
                <div className="text-sm text-muted-foreground flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Online • Executive Command</span>
                </div>
              </div>
            </div>
          </div>

          {/* Chat Messages - Enhanced styling */}
          <div className="flex-1 p-4 space-y-3 overflow-auto min-h-0">
            {ceoMessages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="font-medium">Chat with ARTAC CEO</p>
                <p className="text-sm mt-1">Ask about projects, strategy, or organizational matters</p>
              </div>
            ) : (
              ceoMessages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex items-end space-x-2 ${message.userId !== 'ceo-001' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.userId !== 'ceo-001' ? (
                    // User message: bubble first, then avatar
                    <>
                      <div className="max-w-[80%] p-3 rounded-lg shadow-sm bg-primary text-primary-foreground rounded-br-sm">
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <Avatar className="h-7 w-7 flex-shrink-0">
                        <AvatarFallback className="text-xs bg-blue-500 text-white">
                          {currentUser?.avatar || currentUser?.name?.charAt(0) || 'U'}
                        </AvatarFallback>
                      </Avatar>
                    </>
                  ) : (
                    // CEO message: avatar first, then bubble
                    <>
                      <Avatar className="h-7 w-7 flex-shrink-0">
                        <AvatarFallback className="text-xs bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
                          👑
                        </AvatarFallback>
                      </Avatar>
                      <div className="max-w-[80%] p-3 rounded-lg shadow-sm bg-card border border-border rounded-bl-sm">
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </>
                  )}
                </motion.div>
              ))
            )}
          </div>

          {/* Chat Input - Enhanced */}
          <div className="p-4 border-t border-border bg-muted/20">
            <div className="flex space-x-3">
              <Input
                value={ceoChatInput}
                onChange={(e) => setCeoChatInput(e.target.value)}
                placeholder="Message the CEO..."
                onKeyPress={(e) => e.key === 'Enter' && handleCeoMessage()}
                className="flex-1 bg-background"
              />
              <Button 
                onClick={handleCeoMessage}
                disabled={!ceoChatInput.trim()}
                className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Quick Stats Panel - Enhanced */}
        <div className="p-4 border-t border-border bg-muted/10 rounded-b-lg">
          <h4 className="font-semibold mb-3 flex items-center space-x-2">
            <LineChart className="h-4 w-4 text-blue-500" />
            <span>Quick Stats</span>
          </h4>
          
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-3 rounded-lg bg-card border border-border">
              <div className="text-xl font-bold text-foreground">{analyticsData.projectsThisWeek}</div>
              <div className="text-xs text-muted-foreground font-medium">Projects</div>
            </div>
            
            <div className="text-center p-3 rounded-lg bg-card border border-border">
              <div className="text-xl font-bold text-foreground">{analyticsData.agentsHired}</div>
              <div className="text-xs text-muted-foreground font-medium">Agents</div>
            </div>
            
            <div className="text-center p-3 rounded-lg bg-card border border-border">
              <div className="text-xl font-bold text-foreground">{analyticsData.tasksCompleted}</div>
              <div className="text-xs text-muted-foreground font-medium">Tasks</div>
            </div>
            
            <div className="text-center p-3 rounded-lg bg-card border border-border">
              <div className="text-xl font-bold text-foreground">{analyticsData.systemUptime}%</div>
              <div className="text-xs text-muted-foreground font-medium">Uptime</div>
            </div>
          </div>

          {/* Live Activity Indicator - Enhanced */}
          <div className="mt-4 p-3 rounded-lg bg-card border border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                </div>
                <span className="text-sm font-semibold">Live Activity</span>
              </div>
              <span className="text-sm font-medium">
                {activeAgents.length}👥 • {projects.length}🎯
              </span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}