'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function SecurityMonitoring() {
  return (
    <div className="h-full p-6">
      <Card className="bg-slate-800/50 border-slate-700/50 h-full">
        <CardHeader>
          <CardTitle className="text-white">Security Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-slate-400">Security monitoring interface coming soon...</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}