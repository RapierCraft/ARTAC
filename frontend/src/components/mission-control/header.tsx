'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Menu, 
  X, 
  Mic, 
  MicOff, 
  Settings, 
  Bell, 
  Power,
  Activity,
  Shield,
  Zap,
  RefreshCcw
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { VoiceInterface } from './voice-interface'
import { SystemStatusIndicator } from './system-status'
import { useSystemStore } from '@/stores/system-store'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/ui/theme-toggle'

interface HeaderProps {
  onToggleSidebar: () => void
  onToggleRightPanel: () => void
  sidebarCollapsed: boolean
  rightPanelCollapsed: boolean
}

export function Header({
  onToggleSidebar,
  onToggleRightPanel,
  sidebarCollapsed,
  rightPanelCollapsed
}: HeaderProps) {
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const { systemStatus, isOfflineMode } = useSystemStore()

  return (
    <header className="relative h-16 border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="flex h-full items-center justify-between px-4">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Sidebar Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleSidebar}
            className="text-muted-foreground hover:text-foreground"
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* ARTAC Logo & Title */}
          <div className="flex items-center space-x-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-primary to-accent"
            >
              <Zap className="h-4 w-4 text-white" />
            </motion.div>
            <div>
              <h1 className="text-lg font-bold gradient-text">ARTAC</h1>
              <p className="text-xs text-muted-foreground">Mission Control</p>
            </div>
          </div>

          {/* System Status */}
          <SystemStatusIndicator />

          {/* Offline Mode Indicator */}
          {isOfflineMode && (
            <Badge variant="secondary" className="bg-orange-500/20 text-orange-300 border-orange-500/30">
              Offline Mode
            </Badge>
          )}
        </div>

        {/* Center Section - Voice Interface */}
        <div className="flex-1 flex justify-center">
          <VoiceInterface
            isActive={isVoiceActive}
            onToggle={() => setIsVoiceActive(!isVoiceActive)}
          />
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-3">
          {/* System Metrics */}
          {systemStatus && (
            <div className="hidden md:flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <Activity className="h-4 w-4 text-green-500" />
                <span className="text-foreground">{systemStatus.active_agents}</span>
                <span className="text-muted-foreground">agents</span>
              </div>
              <div className="flex items-center space-x-1">
                <Shield className="h-4 w-4 text-primary" />
                <span className="text-foreground">{systemStatus.total_active_tasks}</span>
                <span className="text-muted-foreground">tasks</span>
              </div>
            </div>
          )}

          {/* Notifications */}
          <Button
            variant="ghost"
            size="sm"
            className="relative text-muted-foreground hover:text-foreground flex items-center gap-2"
          >
            <Bell className="h-4 w-4" />
            <div className="flex items-center gap-1">
              <div className="h-1.5 w-1.5 bg-destructive rounded-full" />
              <span className="text-xs">3</span>
            </div>
          </Button>

          {/* Refresh Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.location.reload()}
            className="text-muted-foreground hover:text-foreground"
          >
            <RefreshCcw className="h-4 w-4" />
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Settings */}
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-foreground"
          >
            <Settings className="h-5 w-5" />
          </Button>

          {/* Right Panel Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleRightPanel}
            className={cn(
              "text-muted-foreground hover:text-foreground",
              !rightPanelCollapsed && "text-foreground bg-muted"
            )}
          >
            <X className={cn("h-5 w-5", rightPanelCollapsed && "rotate-45")} />
          </Button>

          {/* Emergency Stop */}
          <Button
            variant="destructive"
            size="sm"
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            <Power className="h-4 w-4" />
            <span className="ml-1 hidden sm:inline">STOP</span>
          </Button>
        </div>
      </div>

      {/* Header Glow Effect */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
    </header>
  )
}