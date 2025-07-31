'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { VoiceInterface } from './voice-interface'

export function RightPanel() {
  const [isVoiceActive, setIsVoiceActive] = useState(false)

  return (
    <div className="h-full p-4 space-y-4 overflow-y-auto custom-scrollbar bg-card relative z-20">
      {/* Voice Interface */}
      <Card className="bg-card border-border shadow-lg relative z-30">
        <CardHeader className="pb-3">
          <CardTitle className="text-foreground text-sm flex items-center gap-2">
            🎤 Voice Interface
          </CardTitle>
        </CardHeader>
        <CardContent className="relative z-40">
          <VoiceInterface 
            isActive={isVoiceActive} 
            onToggle={() => setIsVoiceActive(!isVoiceActive)} 
          />
        </CardContent>
      </Card>

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