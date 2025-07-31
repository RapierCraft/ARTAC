'use client'

import { motion } from 'framer-motion'
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: string | number
  total?: number
  icon: LucideIcon
  trend?: number
  color: string
  description?: string
}

export function MetricCard({ 
  title, 
  value, 
  total, 
  icon: Icon, 
  trend, 
  color, 
  description 
}: MetricCardProps) {
  const isPositiveTrend = trend && trend > 0
  const TrendIcon = isPositiveTrend ? TrendingUp : TrendingDown

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <Card className="bg-slate-800/50 border-slate-700/50 hover:bg-slate-800/70 transition-all duration-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={cn("p-2 rounded-lg bg-black/20", color.replace('text-', 'bg-').replace('-500', '-500/20'))}>
              <Icon className={cn("w-5 h-5", color)} />
            </div>
            {trend && (
              <Badge 
                variant={isPositiveTrend ? "success" : "destructive"}
                className="text-xs"
              >
                <TrendIcon className="w-3 h-3 mr-1" />
                {Math.abs(trend)}%
              </Badge>
            )}
          </div>
          
          <div className="space-y-2">
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-white">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
              {total && (
                <span className="text-sm text-slate-400">
                  / {total.toLocaleString()}
                </span>
              )}
            </div>
            
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-slate-400">
                {title}
              </h3>
              {total && (
                <div className="text-xs text-slate-500">
                  {((Number(value) / total) * 100).toFixed(1)}%
                </div>
              )}
            </div>
            
            {description && (
              <p className="text-xs text-slate-500 mt-1">
                {description}
              </p>
            )}
          </div>
          
          {/* Progress bar for cards with totals */}
          {total && (
            <div className="mt-3">
              <div className="w-full bg-slate-700/50 rounded-full h-1">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(Number(value) / total) * 100}%` }}
                  transition={{ duration: 1, delay: 0.2 }}
                  className={cn(
                    "h-1 rounded-full",
                    color.includes('blue') && "bg-blue-500",
                    color.includes('green') && "bg-green-500", 
                    color.includes('emerald') && "bg-emerald-500",
                    color.includes('purple') && "bg-purple-500",
                    color.includes('yellow') && "bg-yellow-500",
                    color.includes('red') && "bg-red-500"
                  )}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}