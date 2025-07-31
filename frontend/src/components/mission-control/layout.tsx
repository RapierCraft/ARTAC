'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Header } from './header'
import { Sidebar } from './sidebar'
import { MainContent } from './main-content'
import { RightPanel } from './right-panel'
import { cn } from '@/lib/utils'

export function MissionControlLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

  return (
    <div className="h-screen bg-background text-foreground overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-background to-muted/50" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 dark:opacity-10" />
      
      {/* Main Layout */}
      <div className="relative flex flex-col h-full">
        {/* Header */}
        <Header
          onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          onToggleRightPanel={() => setRightPanelCollapsed(!rightPanelCollapsed)}
          sidebarCollapsed={sidebarCollapsed}
          rightPanelCollapsed={rightPanelCollapsed}
        />

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar */}
          <motion.aside
            initial={false}
            animate={{
              width: sidebarCollapsed ? 60 : 280,
            }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className={cn(
              'relative border-r border-border bg-card/50',
              'backdrop-blur-sm',
              sidebarCollapsed && 'overflow-hidden'
            )}
          >
            <Sidebar collapsed={sidebarCollapsed} />
          </motion.aside>

          {/* Main Content */}
          <main className="flex-1 overflow-hidden">
            <MainContent />
          </main>

          {/* Right Panel */}
          <motion.aside
            initial={false}
            animate={{
              width: rightPanelCollapsed ? 0 : 320,
            }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className={cn(
              'relative border-l border-slate-800/50 bg-slate-900/50',
              'backdrop-blur-sm',
              rightPanelCollapsed && 'overflow-hidden'
            )}
          >
            {!rightPanelCollapsed && <RightPanel />}
          </motion.aside>
        </div>
      </div>

      {/* Global Notifications */}
      <div className="fixed bottom-4 right-4 z-50">
        {/* Toast notifications will appear here */}
      </div>
    </div>
  )
}