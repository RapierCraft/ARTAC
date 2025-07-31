'use client'

import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useSystemStore } from '@/stores/system-store'

export function SystemHealthChart() {
  const { systemStatus, isOfflineMode } = useSystemStore()
  
  // In real implementation, this would come from API with historical data
  // For now, show current status as a single point or placeholder
  const data = useMemo(() => {
    if (!systemStatus || (systemStatus.total_agents === 0 && !isOfflineMode)) {
      return []
    }
    
    // If in offline mode, generate some demo data
    if (isOfflineMode) {
      const now = new Date()
      const demoData = []
      
      for (let i = 5; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 10 * 60 * 1000) // 10 minute intervals
        demoData.push({
          time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          timestamp: time.getTime(),
          systemHealth: Math.max(85, Math.min(99, 92 + Math.sin(i * 0.3) * 5 + Math.random() * 3)),
          activeAgents: Math.max(3, Math.min(5, 4 + Math.random())),
          activeTasks: Math.max(5, Math.min(15, 10 + Math.random() * 3)),
          cpuUsage: Math.max(20, Math.min(40, 30 + Math.random() * 8)),
          memoryUsage: Math.max(30, Math.min(50, 40 + Math.random() * 5)),
        })
      }
      return demoData
    }
    
    // For real data, show current status
    const now = new Date()
    const systemHealth = systemStatus.total_agents > 0 
      ? (systemStatus.active_agents / systemStatus.total_agents) * 100 
      : 0
      
    return [{
      time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: now.getTime(),
      systemHealth: systemHealth,
      activeAgents: systemStatus.active_agents || 0,
      activeTasks: systemStatus.total_active_tasks || 0,
      cpuUsage: 0, // Would come from real metrics
      memoryUsage: 0, // Would come from real metrics
    }]
  }, [systemStatus, isOfflineMode])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-muted border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-muted-foreground text-sm font-medium mb-2">{`Time: ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value.toFixed(1)}${entry.name.includes('Usage') ? '%' : entry.name === 'System Health' ? '%' : ''}`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (data.length === 0) {
    return (
      <div className="space-y-6">
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="text-muted-foreground text-sm">No system data available</div>
            <div className="text-xs text-muted-foreground mt-1">
              {isOfflineMode ? "Connect to backend to see real metrics" : "Start some agents to see system health"}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* System Health Area Chart */}
      <div className="h-64">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">
          System Health Over Time {isOfflineMode && <span className="text-xs text-yellow-500">(Demo Data)</span>}
        </h4>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <defs>
              <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis 
              dataKey="time" 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              domain={[80, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="systemHealth"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#healthGradient)"
              name="System Health"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Resource Usage Multi-line Chart */}
      <div className="h-64">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">Resource Usage</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis 
              dataKey="time" 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="cpuUsage"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="CPU Usage"
            />
            <Line
              type="monotone"
              dataKey="memoryUsage"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              name="Memory Usage"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Agent & Task Activity */}
      <div className="h-48">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">Activity Levels</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis 
              dataKey="time" 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="activeAgents"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
              name="Active Agents"
            />
            <Line
              type="monotone"
              dataKey="activeTasks"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="Active Tasks"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Current Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-700/50">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">
            {data[data.length - 1]?.systemHealth.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">System Health</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-primary">
            {data[data.length - 1]?.cpuUsage.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">CPU Usage</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-400">
            {data[data.length - 1]?.memoryUsage.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">Memory Usage</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-cyan-400">
            {systemStatus?.claude_sessions || 0}
          </div>
          <div className="text-xs text-muted-foreground">Claude Sessions</div>
        </div>
      </div>
    </div>
  )
}