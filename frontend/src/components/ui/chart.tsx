import React from 'react'

interface BarChartProps {
  data: Array<{
    name: string
    value: number
    color?: string
  }>
  height?: number
}

export function BarChart({ data, height = 200 }: BarChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))
  
  return (
    <div className="w-full" style={{ height }}>
      <div className="flex items-end h-full space-x-2">
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center space-y-2">
            <div 
              className="w-full bg-primary rounded-t"
              style={{ 
                height: `${(item.value / maxValue) * 80}%`,
                backgroundColor: item.color || 'hsl(var(--primary))',
                minHeight: '4px'
              }}
            />
            <div className="text-xs text-muted-foreground text-center">
              <div className="font-medium">{item.value}</div>
              <div className="truncate w-full">{item.name}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface LineChartProps {
  data: Array<{
    name: string
    value: number
  }>
  height?: number
}

export function LineChart({ data, height = 200 }: LineChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value))
  const range = maxValue - minValue || 1

  return (
    <div className="w-full" style={{ height }}>
      <div className="relative h-full">
        <svg className="w-full h-full">
          <polyline
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="2"
            points={data.map((point, index) => {
              const x = (index / (data.length - 1)) * 100
              const y = 100 - ((point.value - minValue) / range) * 80
              return `${x},${y}`
            }).join(' ')}
          />
          {data.map((point, index) => {
            const x = (index / (data.length - 1)) * 100
            const y = 100 - ((point.value - minValue) / range) * 80
            return (
              <circle
                key={index}
                cx={`${x}%`}
                cy={`${y}%`}
                r="3"
                fill="hsl(var(--primary))"
              />
            )
          })}
        </svg>
        <div className="flex justify-between mt-2">
          {data.map((item, index) => (
            <div key={index} className="text-xs text-muted-foreground text-center">
              {item.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

interface DonutChartProps {
  data: Array<{
    name: string
    value: number
    color: string
  }>
  size?: number
}

export function DonutChart({ data, size = 120 }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = 0
  
  const radius = size / 2 - 10
  const innerRadius = radius * 0.6
  
  return (
    <div className="flex items-center space-x-4">
      <div style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          {data.map((item, index) => {
            const percentage = item.value / total
            const angle = percentage * 2 * Math.PI
            const startAngle = currentAngle
            const endAngle = currentAngle + angle
            
            const x1 = size/2 + Math.cos(startAngle) * radius
            const y1 = size/2 + Math.sin(startAngle) * radius
            const x2 = size/2 + Math.cos(endAngle) * radius
            const y2 = size/2 + Math.sin(endAngle) * radius
            
            const largeArcFlag = angle > Math.PI ? 1 : 0
            
            const pathData = [
              `M ${size/2} ${size/2}`,
              `L ${x1} ${y1}`,
              `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
              'Z'
            ].join(' ')
            
            currentAngle = endAngle
            
            return (
              <path
                key={index}
                d={pathData}
                fill={item.color}
                opacity={0.8}
              />
            )
          })}
          <circle
            cx={size/2}
            cy={size/2}
            r={innerRadius}
            fill="hsl(var(--background))"
          />
        </svg>
      </div>
      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm">{item.name}: {item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}