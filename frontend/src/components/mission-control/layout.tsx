'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Header } from './header'
import { Sidebar } from './sidebar'
import { MainContent } from './main-content'
import { RightPanel } from './right-panel'
import { cn } from '@/lib/utils'

export function MissionControlLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    typeof window !== 'undefined' ? window.innerWidth < 1024 : false
  )
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false) // Start with right panel open to show voice interface
  const [sidebarWidth, setSidebarWidth] = useState(320) // Increased default width

  // Handle responsive sidebar on window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
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
            width: sidebarCollapsed ? 60 : sidebarWidth,
          }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className={cn(
            'flex-shrink-0 border-r border-border bg-card relative',
            sidebarCollapsed && 'overflow-hidden'
          )}
        >
          <Sidebar collapsed={sidebarCollapsed} />
          
          {/* Resize Handle */}
          {!sidebarCollapsed && (
            <div
              className="absolute top-0 right-0 w-2 h-full cursor-col-resize bg-transparent hover:bg-primary/20 transition-colors group flex items-center justify-center"
              onMouseDown={(e) => {
                e.preventDefault()
                const startX = e.clientX
                const startWidth = sidebarWidth
                
                const handleMouseMove = (e: MouseEvent) => {
                  const newWidth = Math.max(280, Math.min(600, startWidth + (e.clientX - startX)))
                  setSidebarWidth(newWidth)
                }
                
                const handleMouseUp = () => {
                  document.removeEventListener('mousemove', handleMouseMove)
                  document.removeEventListener('mouseup', handleMouseUp)
                  document.body.style.cursor = ''
                  document.body.style.userSelect = ''
                }
                
                document.body.style.cursor = 'col-resize'
                document.body.style.userSelect = 'none'
                document.addEventListener('mousemove', handleMouseMove)
                document.addEventListener('mouseup', handleMouseUp)
              }}
            >
              <div className="w-0.5 h-8 bg-border group-hover:bg-primary/50 rounded-full transition-colors" />
            </div>
          )}
        </motion.aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6 relative z-10">
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
            'flex-shrink-0 border-l border-border bg-card overflow-y-auto relative z-20',
            rightPanelCollapsed && 'overflow-hidden'
          )}
        >
          {!rightPanelCollapsed && <RightPanel />}
        </motion.aside>
      </div>

      {/* Global Notifications */}
      <div className="fixed bottom-4 right-4 z-50">
        {/* Toast notifications will appear here */}
      </div>
    </div>
  )
}