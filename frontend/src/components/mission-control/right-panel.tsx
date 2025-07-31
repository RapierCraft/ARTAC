'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function RightPanel() {
  return (
    <div className="h-full p-4 space-y-4 overflow-y-auto custom-scrollbar">
      <Card className="bg-muted/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-white text-sm">Live Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-xs">Real-time metrics panel coming soon...</p>
        </CardContent>
      </Card>

      <Card className="bg-muted/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-white text-sm">System Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-xs">Live system logs coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}