'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Hash, Crown, Code, Shield, Zap, MessageCircle, Users, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCommunicationStore } from '@/stores/communication-store'
import { MessageList } from '../communication/message-list'
import { cn } from '@/lib/utils'

const executives = [
  { id: 'ceo', name: 'CEO', icon: Crown, color: 'text-yellow-500', bgColor: 'bg-yellow-500/10' },
  { id: 'cto', name: 'CTO', icon: Code, color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  { id: 'cso', name: 'CSO', icon: Shield, color: 'text-green-500', bgColor: 'bg-green-500/10' },
  { id: 'cfo', name: 'CFO', icon: Zap, color: 'text-purple-500', bgColor: 'bg-purple-500/10' },
]

export function RightPanel() {
  const {
    channels,
    activeChannel,
    messages,
    currentUser,
    sendMessage,
    setActiveChannel,
    fetchData
  } = useCommunicationStore()

  const [messageInput, setMessageInput] = useState('')
  const [selectedExecutive, setSelectedExecutive] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize communication store
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Auto-select CEO channel when available
  useEffect(() => {
    const ceoChannel = channels.find(c => c.id === 'channel-ceo')
    if (ceoChannel && !activeChannel) {
      setActiveChannel(ceoChannel.id)
    }
  }, [channels, activeChannel, setActiveChannel])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, activeChannel])

  // Find executive channels, prioritizing CEO channel
  const executiveChannels = channels.filter(channel => 
    channel.id === 'channel-ceo' ||
    executives.some(exec => 
      channel.name.toLowerCase().includes(exec.name.toLowerCase()) ||
      channel.description?.toLowerCase().includes(exec.name.toLowerCase())
    )
  ).sort((a, b) => {
    if (a.id === 'channel-ceo') return -1
    if (b.id === 'channel-ceo') return 1
    return 0
  })

  const currentChannel = channels.find(c => c.id === activeChannel)
  const currentMessages = activeChannel ? messages[activeChannel] || [] : []


  const handleSendMessage = async () => {
    if (!messageInput.trim() || !activeChannel) return

    // Add mentions for selected executives
    const mentions = selectedExecutive ? [selectedExecutive] : []
    const content = selectedExecutive 
      ? `@${executives.find(e => e.id === selectedExecutive)?.name} ${messageInput}`
      : messageInput

    try {
      await sendMessage(activeChannel, content, mentions)
      setMessageInput('')
      setSelectedExecutive(null)
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setMessageInput(value)

    // Check for @ mentions
    const lastAtIndex = value.lastIndexOf('@')
    if (lastAtIndex !== -1) {
      const mention = value.slice(lastAtIndex + 1).toLowerCase()
      const exec = executives.find(e => e.name.toLowerCase().startsWith(mention))
      if (exec) {
        setSelectedExecutive(exec.id)
      }
    } else {
      setSelectedExecutive(null)
    }
  }

  const insertMention = (exec: typeof executives[0]) => {
    const newValue = messageInput + `@${exec.name} `
    setMessageInput(newValue)
    setSelectedExecutive(exec.id)
  }

  const selectChannel = (channelId: string) => {
    setActiveChannel(channelId)
  }

  return (
    <div className="h-full flex flex-col bg-card relative z-20">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-4 w-4 text-primary" />
          <h3 className="font-semibold text-foreground text-sm">Quick Chat</h3>
        </div>
        <p className="text-xs text-muted-foreground mt-1">Executive communication</p>
      </div>

      {/* Channels */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-muted-foreground">Channels:</p>
          <Button size="sm" variant="ghost" className="h-5 w-5 p-0">
            <Plus className="h-3 w-3" />
          </Button>
        </div>
        <ScrollArea className="h-20">
          <div className="space-y-1">
            {executiveChannels.length > 0 ? (
              executiveChannels.map((channel) => (
                <Button
                  key={channel.id}
                  onClick={() => selectChannel(channel.id)}
                  size="sm"
                  variant={activeChannel === channel.id ? "secondary" : "ghost"}
                  className="w-full justify-start h-6 text-xs px-2"
                >
                  <Hash className="h-3 w-3 mr-1" />
                  <span className="truncate">{channel.name}</span>
                  {channel.unreadCount > 0 && (
                    <Badge variant="destructive" className="ml-auto h-4 text-xs px-1">
                      {channel.unreadCount}
                    </Badge>
                  )}
                </Button>
              ))
            ) : (
              channels.slice(0, 3).map((channel) => (
                <Button
                  key={channel.id}
                  onClick={() => selectChannel(channel.id)}
                  size="sm"
                  variant={activeChannel === channel.id ? "secondary" : "ghost"}
                  className="w-full justify-start h-6 text-xs px-2"
                >
                  <Hash className="h-3 w-3 mr-1" />
                  <span className="truncate">{channel.name}</span>
                  {channel.unreadCount > 0 && (
                    <Badge variant="destructive" className="ml-auto h-4 text-xs px-1">
                      {channel.unreadCount}
                    </Badge>
                  )}
                </Button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Quick Executive Tags */}
      <div className="p-3 border-b border-border">
        <p className="text-xs text-muted-foreground mb-2">Quick tags:</p>
        <div className="grid grid-cols-2 gap-1">
          {executives.map((exec) => {
            const Icon = exec.icon
            return (
              <Button
                key={exec.id}
                onClick={() => insertMention(exec)}
                size="sm"
                variant="outline"
                className={cn(
                  "h-6 text-xs px-2",
                  selectedExecutive === exec.id && exec.bgColor
                )}
              >
                <Icon className={cn("h-3 w-3 mr-1", exec.color)} />
                @{exec.name}
              </Button>
            )
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        {currentChannel ? (
          <div className="h-full flex flex-col">
            <div className="px-3 py-2 border-b border-border">
              <div className="flex items-center gap-2">
                <Hash className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm font-medium">{currentChannel.name}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              <MessageList channelId={activeChannel} />
              <div ref={messagesEndRef} />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="text-center">
              <MessageCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Select a channel to start chatting</p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      {currentChannel && (
        <div className="p-3 border-t border-border">
          {selectedExecutive && (
            <div className="mb-2">
              <Badge variant="outline" className="text-xs">
                Tagging: {executives.find(e => e.id === selectedExecutive)?.name}
              </Badge>
            </div>
          )}
          <div className="flex gap-2">
            <Input
              value={messageInput}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Message..."
              className="flex-1 text-sm h-8"
            />
            <Button 
              onClick={handleSendMessage}
              size="sm"
              disabled={!messageInput.trim()}
              className="h-8 w-8 p-0"
            >
              <Send className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}