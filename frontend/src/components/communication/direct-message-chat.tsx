'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useCommunicationStore } from '@/stores/communication-store'
import { EnhancedMarkdown } from './enhanced-markdown'
import type { User as UserType } from '@/types/communication'

interface DirectMessageChatProps {
  agent: UserType
  className?: string
}

export function DirectMessageChat({ agent, className = '' }: DirectMessageChatProps) {
  const { messages, sendMessage, currentUser } = useCommunicationStore()
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Use consistent channel ID - prefer 'ceo' for CEO agent, 'dm-*' for others
  let channelId: string
  if (agent.id === 'ceo-001' || agent.role === 'CEO') {
    channelId = 'ceo'
  } else {
    channelId = `dm-${currentUser?.id}-${agent.id}`
  }
  
  // Get messages for this channel
  let dmMessages = messages[channelId] || []
  
  // Fallback: if no messages in 'ceo' channel, try legacy 'channel-ceo'
  if (dmMessages.length === 0 && channelId === 'ceo') {
    dmMessages = messages['channel-ceo'] || []
    // If we found messages in the legacy channel, update channelId for consistency
    if (dmMessages.length > 0) {
      channelId = 'channel-ceo'
    }
  }

  
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [dmMessages.length])

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return
    
    const messageContent = input.trim()
    setInput('') // Clear input immediately
    setIsLoading(true)
    
    try {
      await sendMessage(channelId, messageContent)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore input on error
      setInput(messageContent)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className={`flex flex-col h-full min-h-0 bg-background ${className}`}>
      {/* Chat Header */}
      <div className="flex items-center space-x-3 p-4 border-b border-border bg-muted/20">
        <Avatar className="h-10 w-10">
          <AvatarFallback className={`text-sm font-medium ${
            agent.role === 'CEO' ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white' :
            agent.role === 'Developer' ? 'bg-blue-500 text-white' :
            agent.role === 'QA Engineer' ? 'bg-green-500 text-white' :
            agent.role === 'Designer' ? 'bg-purple-500 text-white' :
            'bg-gray-500 text-white'
          }`}>
            {agent.avatar || agent.name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-semibold text-foreground">{agent.name}</h3>
          <p className="text-sm text-muted-foreground">
            {agent.status}
          </p>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {dmMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className={`p-4 rounded-full mb-4 ${
              agent.role === 'CEO' ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-primary'
            }`}>
              <Bot className="h-8 w-8 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Chat with {agent.name}
            </h4>
            <p className="text-sm text-muted-foreground max-w-sm">
              {agent.role === 'CEO' ? 
                'Ask about projects, strategy, or organizational matters' :
                `Start a conversation with ${agent.name} about their work and expertise`
              }
            </p>
          </div>
        ) : (
          <>
            <AnimatePresence>
              {dmMessages.map((message) => {
                // Check if message is from current user - handle both 'current-user' and 'user-001' formats
                const isUserMessage = message.userId === currentUser?.id || 
                                    message.userId === 'current-user' ||
                                    message.userId === 'user-001' ||
                                    (message.userId !== agent.id && message.userId !== 'ceo-001')
                
                return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`flex items-end space-x-2 ${
                    isUserMessage ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {isUserMessage ? (
                    // USER MESSAGE: Right side, blue bubble, user avatar on right
                    <>
                      <div className="max-w-[80%] p-3 rounded-lg shadow-sm bg-blue-600 text-white rounded-br-sm">
                        <EnhancedMarkdown content={message.content} className="text-sm text-white" />
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </p>
                      </div>
                      <Avatar className="h-7 w-7 flex-shrink-0">
                        <AvatarFallback className="text-xs bg-blue-500 text-white">
                          <User className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                    </>
                  ) : (
                    // AGENT MESSAGE: Left side, gray bubble, agent avatar on left
                    <>
                      <Avatar className="h-7 w-7 flex-shrink-0">
                        <AvatarFallback className={`text-xs ${
                          agent.role === 'CEO' ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white' :
                          agent.role === 'Developer' ? 'bg-blue-500 text-white' :
                          agent.role === 'QA Engineer' ? 'bg-green-500 text-white' :
                          agent.role === 'Designer' ? 'bg-purple-500 text-white' :
                          'bg-gray-500 text-white'
                        }`}>
                          {agent.avatar || agent.name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="max-w-[80%] p-3 rounded-lg shadow-sm bg-card border border-border rounded-bl-sm">
                        <EnhancedMarkdown content={message.content} className="text-sm" />
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </p>
                      </div>
                    </>
                  )}
                </motion.div>
                )
              })}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-border bg-muted/20">
        <div className="flex space-x-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Message ${agent.name}...`}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            className="flex-1 bg-background"
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className={
              agent.role === 'CEO' ? 
                'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600' :
                'bg-primary hover:bg-primary/90'
            }
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}