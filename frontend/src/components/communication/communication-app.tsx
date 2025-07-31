'use client'

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { ChannelSidebar } from './channel-sidebar'
import { ChatArea } from './chat-area'
import { UserList } from './user-list'
import { ThreadPanel } from './thread-panel'
import { MemoPanel } from './memo-panel'
import { useCommunicationStore } from '@/stores/communication-store'
import { cn } from '@/lib/utils'

export function CommunicationApp() {
  const {
    fetchData,
    showUserList,
    showThreadPanel,
    showMemoPanel,
    isLoading
  } = useCommunicationStore()

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <div className="text-muted-foreground">Loading communication app...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full bg-background flex">
      {/* Channel Sidebar */}
      <div className="w-64 border-r border-border bg-muted/30 flex-shrink-0">
        <ChannelSidebar />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatArea />
      </div>

      {/* Right Panels */}
      <div className="flex">
        {/* User List */}
        <motion.div
          initial={false}
          animate={{
            width: showUserList ? 240 : 0,
            opacity: showUserList ? 1 : 0
          }}
          transition={{ duration: 0.3 }}
          className={cn(
            "border-l border-border bg-muted/20 overflow-hidden",
            !showUserList && "hidden"
          )}
        >
          <UserList />
        </motion.div>

        {/* Thread Panel */}
        <ThreadPanel 
          isOpen={showThreadPanel} 
          onClose={() => useCommunicationStore.getState().toggleThreadPanel()} 
        />

        {/* Memo Panel */}
        <MemoPanel 
          isOpen={showMemoPanel} 
          onClose={() => useCommunicationStore.getState().toggleMemoPanel()} 
        />
      </div>
    </div>
  )
}