'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Paperclip, 
  Smile,
  MoreVertical,
  Users,
  Pin,
  Search,
  Hash,
  Lock,
  MessageSquare,
  Reply
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useCommunicationStore } from '@/stores/communication-store'
import { MessageList } from './message-list'
import { cn } from '@/lib/utils'

export function ChatArea() {
  const {
    channels,
    activeChannel,
    currentUser,
    sendMessage,
    toggleUserList,
    showUserList,
    markChannelAsRead,
    agentTyping,
    messages
  } = useCommunicationStore()

  const [messageInput, setMessageInput] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const currentChannel = channels.find(c => c.id === activeChannel)

  useEffect(() => {
    if (activeChannel) {
      markChannelAsRead(activeChannel)
    }
  }, [activeChannel, markChannelAsRead])

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !activeChannel || !currentUser) return

    // Extract mentions (@username)
    const mentions = messageInput.match(/@(\w+)/g)?.map(m => m.slice(1)) || []
    
    // Store message content before clearing
    const messageContent = messageInput

    // Clear input immediately for better UX
    setMessageInput('')
    inputRef.current?.focus()

    // Send message with stored content
    await sendMessage(activeChannel, messageContent, mentions, replyingTo || undefined)
    
    // Clear reply context after sending
    setReplyingTo(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessageInput(e.target.value)
  }

  const handleReply = (messageId: string) => {
    setReplyingTo(messageId)
    inputRef.current?.focus()
  }

  const cancelReply = () => {
    setReplyingTo(null)
  }

  // Get the message being replied to
  const replyingToMessage = replyingTo ? (messages[activeChannel] || []).find(m => m.id === replyingTo) : null
  
  // Get agent typing info for current channel
  const currentAgentTyping = activeChannel ? agentTyping[activeChannel] : null

  if (!currentChannel) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Welcome to ARTAC Chat</h3>
          <p className="text-muted-foreground">Select a channel to start messaging</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Channel Header */}
      <div className="h-16 border-b border-border bg-muted/20 flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {currentChannel.type === 'public' && <Hash className="h-5 w-5 text-muted-foreground" />}
            {currentChannel.type === 'private' && <Lock className="h-5 w-5 text-muted-foreground" />}
            {currentChannel.type === 'direct' && <div className="h-2 w-2 bg-green-500 rounded-full" />}
            
            <h1 className="text-lg font-semibold text-foreground">
              {currentChannel.name}
            </h1>
          </div>
          
          {currentChannel.description && (
            <div className="hidden md:block">
              <span className="text-sm text-muted-foreground">
                {currentChannel.description}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleUserList}
            className={cn(showUserList && "bg-muted text-primary")}
          >
            <Users className="h-4 w-4" />
            <span className="ml-2 hidden sm:inline">
              {currentChannel?.members?.length || 0}
            </span>
          </Button>

          <Button variant="ghost" size="sm">
            <Search className="h-4 w-4" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Pin className="h-4 w-4 mr-2" />
                View Pinned Messages
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                Channel Settings
              </DropdownMenuItem>
              {currentChannel.type !== 'direct' && (
                <DropdownMenuItem className="text-destructive">
                  Leave Channel
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden min-h-0">
        <MessageList channelId={activeChannel} onReply={handleReply} />
      </div>

      {/* Agent Typing Indicator */}
      <AnimatePresence>
        {currentAgentTyping?.isTyping && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 py-2 border-t border-border flex-shrink-0"
          >
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <div className="flex space-x-1">
                <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span>{currentAgentTyping.agentName} is typing...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reply Context */}
      {replyingToMessage && (
        <div className="px-4 py-2 border-t border-border bg-muted/20 flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-2 text-sm">
              <Reply className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div>
                <span className="text-muted-foreground">Replying to </span>
                <span className="font-medium">User</span>
                <div className="text-xs text-muted-foreground truncate max-w-xs">
                  {replyingToMessage.content.length > 50 
                    ? `${replyingToMessage.content.substring(0, 50)}...` 
                    : replyingToMessage.content}
                </div>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={cancelReply}>
              ×
            </Button>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="p-4 border-t border-border bg-background flex-shrink-0">
        <div className="flex items-end space-x-3">
          <Button variant="ghost" size="sm">
            <Paperclip className="h-4 w-4" />
          </Button>

          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={messageInput}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder={`Message #${currentChannel.name}`}
              className="min-h-[40px] max-h-32 resize-none pr-12"
            />
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-2 top-1/2 transform -translate-y-1/2"
            >
              <Smile className="h-4 w-4" />
            </Button>
          </div>

          <Button
            onClick={handleSendMessage}
            disabled={!messageInput.trim()}
            className="h-10 w-10 p-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-2 text-xs text-muted-foreground">
          <strong>@mention</strong> someone, or type <strong>/</strong> for commands
        </div>
      </div>
    </div>
  )
}