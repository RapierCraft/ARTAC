'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  X, 
  Send, 
  Reply, 
  MoreVertical, 
  ChevronRight, 
  ChevronDown,
  MessageSquare,
  Users,
  Clock,
  Pin,
  Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Card } from '@/components/ui/card'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useCommunicationStore } from '@/stores/communication-store'
import { MessageItem } from './message-item'
import { ThreadMessage } from '@/types/communication'
import { cn, formatRelativeTime } from '@/lib/utils'

interface EnhancedThreadPanelProps {
  isOpen: boolean
  onClose: () => void
}

// Mock nested thread data
const mockThreadMessages: ThreadMessage[] = [
  {
    id: 'thread-msg-1',
    channelId: 'channel-dev',
    userId: 'user-2',
    content: 'We should implement real-time WebRTC for voice channels. What do you think about the architecture?',
    type: 'text',
    timestamp: new Date('2024-11-25T10:00:00'),
    mentions: [],
    reactions: [
      { emoji: '👍', users: ['user-3', 'user-4'] },
      { emoji: '🤔', users: ['user-1'] }
    ],
    threadDepth: 0,
    threadPath: []
  },
  {
    id: 'thread-msg-2',
    channelId: 'channel-dev',
    userId: 'user-3',
    content: 'Great idea! I suggest using PeerJS for simpler WebRTC implementation. It handles most of the complexity.',
    type: 'text',
    timestamp: new Date('2024-11-25T10:15:00'),
    replyTo: 'thread-msg-1',
    mentions: ['user-2'],
    reactions: [
      { emoji: '💡', users: ['user-2', 'user-4'] }
    ],
    threadDepth: 1,
    threadPath: ['thread-msg-1']
  },
  {
    id: 'thread-msg-3',
    channelId: 'channel-dev',
    userId: 'user-4',
    content: 'PeerJS is good for prototyping, but for production we might want native WebRTC for better control over connection quality.',
    type: 'text',
    timestamp: new Date('2024-11-25T10:30:00'),
    replyTo: 'thread-msg-2',
    mentions: ['user-3'],
    reactions: [
      { emoji: '⚡', users: ['user-1', 'user-2'] }
    ],
    threadDepth: 2,
    threadPath: ['thread-msg-1', 'thread-msg-2']
  },
  {
    id: 'thread-msg-4',
    channelId: 'channel-dev',
    userId: 'user-1',
    content: 'Both approaches have merit. Let\'s start with PeerJS for the MVP and then optimize with native WebRTC based on user feedback.',
    type: 'text',
    timestamp: new Date('2024-11-25T11:00:00'),
    replyTo: 'thread-msg-1',
    mentions: ['user-2', 'user-3', 'user-4'],
    reactions: [
      { emoji: '🎯', users: ['user-2', 'user-3', 'user-4'] },
      { emoji: '👏', users: ['user-2'] }
    ],
    threadDepth: 1,
    threadPath: ['thread-msg-1']
  },
  {
    id: 'thread-msg-5',
    channelId: 'channel-dev',
    userId: 'user-5',
    content: 'Sounds like a solid plan! I can help with the UI components for the voice channel controls.',
    type: 'text',
    timestamp: new Date('2024-11-25T11:15:00'),
    replyTo: 'thread-msg-4',
    mentions: ['user-1'],
    reactions: [
      { emoji: '🚀', users: ['user-1', 'user-2'] }
    ],
    threadDepth: 2,
    threadPath: ['thread-msg-1', 'thread-msg-4']
  }
]

export function EnhancedThreadPanel({ isOpen, onClose }: EnhancedThreadPanelProps) {
  const { users, currentUser } = useCommunicationStore()
  
  const [newReply, setNewReply] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [collapsedMessages, setCollapsedMessages] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const rootMessage = mockThreadMessages.find(m => m.threadDepth === 0)
  const rootUser = rootMessage ? users.find(u => u.id === rootMessage.userId) : null

  // Auto-scroll to bottom when new replies arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mockThreadMessages.length])

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newReply.trim() || !currentUser) return

    setIsLoading(true)
    try {
      // In real implementation, this would send the reply
      console.log('Sending thread reply:', { content: newReply, replyTo: replyingTo })
      setNewReply('')
      setReplyingTo(null)
    } catch (error) {
      console.error('Failed to send thread reply:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleMessageCollapse = (messageId: string) => {
    setCollapsedMessages(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  const getChildMessages = (parentId: string) => {
    return mockThreadMessages.filter(m => m.replyTo === parentId)
  }

  const renderThreadMessage = (message: ThreadMessage, depth: number = 0) => {
    const user = users.find(u => u.id === message.userId)
    const isCollapsed = collapsedMessages.has(message.id)
    const childMessages = getChildMessages(message.id)
    const hasChildren = childMessages.length > 0

    return (
      <div key={message.id} className="space-y-2">
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: depth * 0.1 }}
          className={cn(
            "relative",
            depth > 0 && "ml-6 pl-4 border-l-2 border-muted"
          )}
        >
          {/* Thread connector line */}
          {depth > 0 && (
            <div className="absolute -left-2 top-4 w-4 h-0.5 bg-muted" />
          )}

          <Card className={cn("p-3 hover:bg-muted/30 transition-colors", depth > 2 && "bg-muted/20")}>
            <div className="flex items-start space-x-3">
              {/* Avatar */}
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-sm font-medium">
                  {user?.avatar || user?.name.charAt(0)}
                </div>
              </div>

              {/* Message Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-medium text-sm">{user?.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {formatRelativeTime(message.timestamp)}
                  </span>
                  {depth > 0 && (
                    <Badge variant="outline" className="text-xs px-1 py-0">
                      Reply
                    </Badge>
                  )}
                </div>

                <div className="text-sm leading-relaxed mb-2">
                  {message.content}
                </div>

                {/* Reactions */}
                {message.reactions.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {message.reactions.map((reaction) => (
                      <Button
                        key={reaction.emoji}
                        variant="secondary"
                        size="sm"
                        className="h-6 px-2 text-xs"
                      >
                        <span className="mr-1">{reaction.emoji}</span>
                        {reaction.users.length}
                      </Button>
                    ))}
                  </div>
                )}

                {/* Message Actions */}
                <div className="flex items-center space-x-2 text-xs">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={() => setReplyingTo(message.id)}
                  >
                    <Reply className="h-3 w-3 mr-1" />
                    Reply
                  </Button>

                  {hasChildren && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      onClick={() => toggleMessageCollapse(message.id)}
                    >
                      {isCollapsed ? (
                        <ChevronRight className="h-3 w-3 mr-1" />
                      ) : (
                        <ChevronDown className="h-3 w-3 mr-1" />
                      )}
                      {childMessages.length} {childMessages.length === 1 ? 'reply' : 'replies'}
                    </Button>
                  )}

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Pin className="h-4 w-4 mr-2" />
                        Pin Message
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Star className="h-4 w-4 mr-2" />
                        Star Message
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          </Card>

          {/* Reply Input for this specific message */}
          <AnimatePresence>
            {replyingTo === message.id && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="ml-11 mt-2"
              >
                <Card className="p-3 bg-muted/50">
                  <div className="text-xs text-muted-foreground mb-2">
                    Replying to {user?.name}
                  </div>
                  <form onSubmit={handleSendReply} className="flex space-x-2">
                    <Input
                      value={newReply}
                      onChange={(e) => setNewReply(e.target.value)}
                      placeholder="Type your reply..."
                      className="flex-1"
                      disabled={isLoading}
                    />
                    <Button type="submit" size="sm" disabled={!newReply.trim() || isLoading}>
                      <Send className="h-4 w-4" />
                    </Button>
                    <Button 
                      type="button" 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setReplyingTo(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </form>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Render child messages */}
        <AnimatePresence>
          {hasChildren && !isCollapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2"
            >
              {childMessages.map(childMsg => 
                renderThreadMessage(childMsg, depth + 1)
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  if (!isOpen || !rootMessage || !rootUser) {
    return null
  }

  const totalReplies = mockThreadMessages.length - 1
  const participants = [...new Set(mockThreadMessages.map(m => m.userId))]

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-[480px] bg-background border-l border-border z-50 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-4 w-4" />
            <h3 className="font-semibold text-sm">Thread</h3>
            <Badge variant="secondary" className="text-xs">
              {totalReplies} {totalReplies === 1 ? 'reply' : 'replies'}
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs text-muted-foreground">
              <Users className="h-3 w-3" />
              <span>{participants.length} participants</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Thread Stats */}
        <div className="px-4 py-2 bg-muted/30 border-b border-border">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center space-x-4">
              <span>Started by {rootUser.name}</span>
              <span>{formatRelativeTime(rootMessage.timestamp)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>Last reply {formatRelativeTime(mockThreadMessages[mockThreadMessages.length - 1].timestamp)}</span>
            </div>
          </div>
        </div>

        {/* Thread Content */}
        <div className="flex-1 flex flex-col min-h-0">
          <ScrollArea className="flex-1">
            <div className="p-4 space-y-4">
              {renderThreadMessage(rootMessage)}
              
              {/* Scroll anchor */}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>

          {/* Quick Reply Input */}
          {!replyingTo && (
            <div className="p-4 border-t border-border">
              <form onSubmit={handleSendReply} className="flex space-x-2">
                <Input
                  value={newReply}
                  onChange={(e) => setNewReply(e.target.value)}
                  placeholder="Reply to thread..."
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
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}