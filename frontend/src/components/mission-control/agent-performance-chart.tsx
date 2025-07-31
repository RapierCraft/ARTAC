'use client'

import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useSystemStore } from '@/stores/system-store'

const LEVEL_COLORS = {
  executive: '#eab308',   // yellow-500
  management: '#3b82f6',  // blue-500  
  development: '#10b981', // emerald-500
  execution: '#8b5cf6'    // purple-500
}

export function AgentPerformanceChart() {
  const { agents, agentStatuses } = useSystemStore()

  const chartData = useMemo(() => {
    // Group agents by level and calculate average performance
    const levelStats = agents.reduce((acc, agent) => {
      const level = agent.level
      const status = agentStatuses[agent.id]
      const performance = status?.performance_score || agent.performance_score
      
      if (!acc[level]) {
        acc[level] = {
          level: level.charAt(0).toUpperCase() + level.slice(1),
          totalPerformance: 0,
          count: 0,
          activeCount: 0,
          agents: []
        }
      }
      
      acc[level].totalPerformance += performance
      acc[level].count += 1
      acc[level].agents.push({ ...agent, currentPerformance: performance })
      
      if (status?.status === 'active') {
        acc[level].activeCount += 1
      }
      
      return acc
    }, {} as Record<string, any>)

    // Convert to chart data format
    return Object.keys(LEVEL_COLORS).map(level => {
      const stats = levelStats[level]
      if (!stats) {
        return {
          level: level.charAt(0).toUpperCase() + level.slice(1),
          avgPerformance: 0,
          activeAgents: 0,
          totalAgents: 0,
          color: LEVEL_COLORS[level as keyof typeof LEVEL_COLORS]
        }
      }
      
      return {
        level: stats.level,
        avgPerformance: stats.count > 0 ? stats.totalPerformance / stats.count : 0,
        activeAgents: stats.activeCount,
        totalAgents: stats.count,
        color: LEVEL_COLORS[level as keyof typeof LEVEL_COLORS],
        agents: stats.agents
      }
    })
  }, [agents, agentStatuses])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length && payload[0].payload.agents) {
      const data = payload[0].payload
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 shadow-lg min-w-[200px]">
          <p className="text-slate-300 text-sm font-semibold mb-2">{label} Level</p>
          <div className="space-y-1 text-xs">
            <p className="text-slate-400">
              Average Performance: <span style={{ color: data.color }} className="font-medium">{data.avgPerformance.toFixed(1)}%</span>
            </p>
            <p className="text-slate-400">
              Active Agents: <span className="text-green-400 font-medium">{data.activeAgents}</span> / {data.totalAgents}
            </p>
          </div>
          
          {data.agents.length > 0 && (
            <div className="mt-3 pt-2 border-t border-slate-600">
              <p className="text-slate-400 text-xs mb-1">Top Performers:</p>
              {data.agents
                .sort((a: any, b: any) => b.currentPerformance - a.currentPerformance)
                .slice(0, 3)
                .map((agent: any, index: number) => (
                  <div key={agent.id} className="flex justify-between text-xs">
                    <span className="text-slate-300 truncate">{agent.name}</span>
                    <span className="text-slate-400 ml-2">{agent.currentPerformance.toFixed(1)}%</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  const CustomBar = (props: any) => {
    const { fill, ...rest } = props
    return <Bar {...rest} fill={props.payload.color} />
  }

  return (
    <div className="space-y-6">
      {/* Performance by Level Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis 
              dataKey="level" 
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
            <Bar dataKey="avgPerformance" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Distribution */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {chartData.map((levelData) => (
          <div 
            key={levelData.level}
            className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/50"
          >
            <div className="flex items-center space-x-2 mb-3">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: levelData.color }}
              />
              <h4 className="text-sm font-medium text-white">{levelData.level}</h4>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Performance</span>
                <span 
                  className="text-sm font-semibold"
                  style={{ color: levelData.color }}
                >
                  {levelData.avgPerformance.toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Active</span>
                <span className="text-sm text-slate-300">
                  {levelData.activeAgents}/{levelData.totalAgents}
                </span>
              </div>
              
              {/* Performance bar */}
              <div className="w-full bg-slate-700/50 rounded-full h-1.5 mt-2">
                <div
                  className="h-1.5 rounded-full transition-all duration-1000"
                  style={{
                    width: `${levelData.avgPerformance}%`,
                    backgroundColor: levelData.color
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Performance Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-700/50">
        <div className="bg-slate-800/30 rounded-lg p-4">
          <h4 className="text-sm font-medium text-white mb-2">Highest Performing</h4>
          <div className="space-y-1">
            {agents
              .map(agent => ({
                ...agent,
                currentPerformance: agentStatuses[agent.id]?.performance_score || agent.performance_score
              }))
              .sort((a, b) => b.currentPerformance - a.currentPerformance)
              .slice(0, 3)
              .map((agent, index) => (
                <div key={agent.id} className="flex justify-between text-xs">
                  <span className="text-slate-300 truncate">{agent.name}</span>
                  <span className="text-green-400 ml-2">{agent.currentPerformance.toFixed(1)}%</span>
                </div>
              ))}
          </div>
        </div>

        <div className="bg-slate-800/30 rounded-lg p-4">
          <h4 className="text-sm font-medium text-white mb-2">Needs Attention</h4>
          <div className="space-y-1">
            {agents
              .map(agent => ({
                ...agent,
                currentPerformance: agentStatuses[agent.id]?.performance_score || agent.performance_score
              }))
              .filter(agent => agent.currentPerformance < 70)
              .sort((a, b) => a.currentPerformance - b.currentPerformance)
              .slice(0, 3)
              .map((agent, index) => (
                <div key={agent.id} className="flex justify-between text-xs">
                  <span className="text-slate-300 truncate">{agent.name}</span>
                  <span className="text-yellow-400 ml-2">{agent.currentPerformance.toFixed(1)}%</span>
                </div>
              ))}
          </div>
          {agents.filter(agent => (agentStatuses[agent.id]?.performance_score || agent.performance_score) < 70).length === 0 && (
            <p className="text-xs text-slate-500">All agents performing well</p>
          )}
        </div>

        <div className="bg-slate-800/30 rounded-lg p-4">
          <h4 className="text-sm font-medium text-white mb-2">Overall Health</h4>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Average Performance</span>
              <span className="text-slate-300">
                {agents.length > 0 
                  ? (agents.reduce((sum, agent) => sum + (agentStatuses[agent.id]?.performance_score || agent.performance_score), 0) / agents.length).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Active Agents</span>
              <span className="text-green-400">
                {Object.values(agentStatuses).filter(status => status.status === 'active').length}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Performance Trend</span>
              <span className="text-green-400">↗ +2.3%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}