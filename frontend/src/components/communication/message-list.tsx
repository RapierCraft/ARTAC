'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCommunicationStore } from '@/stores/communication-store'
import { MessageItem } from './message-item'
import { formatDate } from '@/lib/utils'

interface MessageListProps {
  channelId: string
}

export function MessageList({ channelId }: MessageListProps) {
  const { messages, users } = useCommunicationStore()
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const channelMessages = messages[channelId] || []

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [channelMessages.length])

  // Group messages by date
  const groupedMessages = channelMessages.reduce((groups, message) => {
    const date = new Date(message.timestamp).toDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(message)
    return groups
  }, {} as Record<string, typeof channelMessages>)

  if (channelMessages.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-muted-foreground text-sm">No messages yet</div>
          <div className="text-xs text-muted-foreground mt-1">
            Be the first to send a message!
          </div>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div ref={scrollRef} className="p-4 space-y-4">
        {Object.entries(groupedMessages).map(([date, dayMessages]) => (
          <div key={date}>
            {/* Date Separator */}
            <div className="flex items-center my-6">
              <div className="flex-1 h-px bg-border" />
              <div className="px-3 text-xs text-muted-foreground bg-background">
                {new Date(date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Messages for this date */}
            <div className="space-y-3">
              {dayMessages.map((message, index) => {
                const previousMessage = index > 0 ? dayMessages[index - 1] : null
                const isGrouped = previousMessage &&
                  previousMessage.userId === message.userId &&
                  new Date(message.timestamp).getTime() - new Date(previousMessage.timestamp).getTime() < 5 * 60 * 1000 // 5 minutes

                return (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <MessageItem
                      message={message}
                      user={users.find(u => u.id === message.userId)}
                      isGrouped={isGrouped}
                    />
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}
        
        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}