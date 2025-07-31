'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, MoreVertical } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useCommunicationStore } from '@/stores/communication-store'
import { MessageItem } from './message-item'
import { cn } from '@/lib/utils'

interface ThreadPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function ThreadPanel({ isOpen, onClose }: ThreadPanelProps) {
  const { 
    activeThread, 
    messages, 
    users, 
    currentUser,
    replyToThread,
    setActiveThread 
  } = useCommunicationStore()

  const [newReply, setNewReply] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Find the parent message
  const parentMessage = activeThread ? 
    Object.values(messages).flat().find(m => m.id === activeThread) : null

  // Find thread replies
  const threadReplies = parentMessage ? 
    Object.values(messages).flat().filter(m => m.replyTo === parentMessage.id) : []

  const parentUser = parentMessage ? users.find(u => u.id === parentMessage.userId) : null

  // Auto-scroll to bottom when new replies arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [threadReplies.length])

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newReply.trim() || !activeThread || !currentUser) return

    setIsLoading(true)
    try {
      await replyToThread(activeThread, newReply.trim())
      setNewReply('')
    } catch (error) {
      console.error('Failed to send thread reply:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setActiveThread(null)
    onClose()
  }

  if (!isOpen || !activeThread || !parentMessage || !parentUser) {
    return null
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-96 bg-background border-l border-border z-50 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-sm">Thread</h3>
            <Badge variant="secondary" className="text-xs">
              {threadReplies.length} {threadReplies.length === 1 ? 'reply' : 'replies'}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={handleClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Thread Content */}
        <div className="flex-1 flex flex-col min-h-0">
          <ScrollArea className="flex-1">
            <div className="p-4">
              {/* Original Message */}
              <div className="mb-4">
                <div className="text-xs text-muted-foreground mb-2 flex items-center">
                  <span className="bg-muted px-2 py-1 rounded">Original Message</span>
                </div>
                <MessageItem
                  message={parentMessage}
                  user={parentUser}
                  isGrouped={false}
                />
              </div>

              <Separator className="my-4" />

              {/* Thread Replies */}
              <div className="space-y-3">
                {threadReplies.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-muted-foreground text-sm">No replies yet</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Start the conversation!
                    </div>
                  </div>
                ) : (
                  threadReplies.map((reply, index) => {
                    const replyUser = users.find(u => u.id === reply.userId)
                    const previousReply = index > 0 ? threadReplies[index - 1] : null
                    const isGrouped = previousReply &&
                      previousReply.userId === reply.userId &&
                      new Date(reply.timestamp).getTime() - new Date(previousReply.timestamp).getTime() < 5 * 60 * 1000

                    return (
                      <motion.div
                        key={reply.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <MessageItem
                          message={reply}
                          user={replyUser}
                          isGrouped={isGrouped}
                        />
                      </motion.div>
                    )
                  })
                )}
              </div>

              {/* Scroll anchor */}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>

          {/* Reply Input */}
          <div className="p-4 border-t border-border">
            <form onSubmit={handleSendReply} className="flex space-x-2">
              <Input
                value={newReply}
                onChange={(e) => setNewReply(e.target.value)}
                placeholder={`Reply to ${parentUser.name}...`}
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                type="submit"
                size="sm"
                disabled={!newReply.trim() || isLoading}
                className="px-3"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <div className="text-xs text-muted-foreground mt-2">
              Reply to this thread to keep the conversation organized
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}