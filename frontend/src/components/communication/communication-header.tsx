'use client'

import { useState } from 'react'
import { 
  Settings, 
  Bell, 
  Search, 
  Users, 
  Hash,
  MessageSquare,
  Home,
  Zap,
  WifiOff,
  Wifi
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { StatusBadge } from '@/components/ui/status-badge'
import { NotificationBell } from '@/components/notifications/notification-bell'
import { SettingsPanel } from '@/components/settings/settings-panel'
import { useCommunicationStore } from '@/stores/communication-store'
import { useProjectStore } from '@/stores/project-store'
import { motion } from 'framer-motion'
import Link from 'next/link'

export function CommunicationHeader() {
  const { activeChannel, channels, toggleUserList, showUserList, error } = useCommunicationStore()
  const { activeProject, projects } = useProjectStore()
  const [searchQuery, setSearchQuery] = useState('')
  
  const currentChannel = channels.find(c => c.id === activeChannel)
  const currentProject = projects.find(p => p.id === activeProject)
  const isOffline = error && error.includes('Offline')
  const isHome = activeProject === null

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-4">
      {/* Left Section */}
      <div className="flex items-center space-x-4">
        {/* ARTAC Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-primary to-accent"
          >
            <Zap className="h-4 w-4 text-white" />
          </motion.div>
          <span className="font-bold text-lg gradient-text">ARTAC</span>
        </Link>

        {/* Context Info */}
        <div className="flex items-center space-x-2">
          {isHome ? (
            // Home Organization Context
            <>
              <Home className="h-4 w-4 text-blue-500" />
              <span className="font-semibold">Organization Overview</span>
            </>
          ) : currentProject && currentChannel ? (
            // Project Context
            <>
              <div className="text-lg">{currentProject.icon}</div>
              <span className="font-semibold">{currentProject.name}</span>
              <span className="text-muted-foreground">|</span>
              <Hash className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{currentChannel.name}</span>
            </>
          ) : currentChannel ? (
            // Fallback to channel info
            <>
              <Hash className="h-4 w-4 text-muted-foreground" />
              <span className="font-semibold">{currentChannel.name}</span>
              {currentChannel.description && (
                <span className="text-sm text-muted-foreground">
                  | {currentChannel.description}
                </span>
              )}
            </>
          ) : (
            // Default fallback
            <>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span className="font-semibold">Communication</span>
            </>
          )}
          
          {/* Offline Indicator */}
          {isOffline && (
            <StatusBadge variant="offline" size="sm" icon={<WifiOff className="h-3 w-3" />}>
              Offline Mode
            </StatusBadge>
          )}
        </div>
      </div>

      {/* Center Section - Search */}
      <div className="flex-1 max-w-md mx-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-2">
        {/* User List Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleUserList}
          className={showUserList ? "bg-muted text-primary" : ""}
        >
          <Users className="h-4 w-4" />
        </Button>

        {/* Notifications */}
        <NotificationBell />

        {/* Settings */}
        <SettingsPanel />

        {/* Back to Mission Control */}
        <Link href="/">
          <Button variant="ghost" size="sm">
            <Home className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </header>
  )
}