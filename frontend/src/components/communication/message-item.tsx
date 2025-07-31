'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  MoreVertical, 
  MessageSquare, 
  Pin, 
  Edit2, 
  Trash2,
  Reply,
  Smile
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { 
  HoverCard,
  HoverCardContent,
  HoverCardTrigger
} from '@/components/ui/hover-card'
import { useCommunicationStore } from '@/stores/communication-store'
import { Message, User } from '@/types/communication'
import { formatRelativeTime, cn } from '@/lib/utils'

interface MessageItemProps {
  message: Message
  user?: User
  isGrouped?: boolean
}

export function MessageItem({ message, user, isGrouped = false }: MessageItemProps) {
  const {
    currentUser,
    addReaction,
    removeReaction,
    setActiveThread,
    pinMessage,
    unpinMessage,
    deleteMessage
  } = useCommunicationStore()

  const [showActions, setShowActions] = useState(false)
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)

  const isOwn = currentUser?.id === message.userId
  const canEdit = isOwn && new Date().getTime() - new Date(message.timestamp).getTime() < 15 * 60 * 1000 // 15 minutes
  const canDelete = isOwn || currentUser?.role === 'CEO'

  const handleReaction = async (emoji: string) => {
    const existingReaction = message.reactions.find(r => r.emoji === emoji)
    const hasReacted = existingReaction?.users.includes(currentUser?.id || '')

    if (hasReacted) {
      await removeReaction(message.id, emoji)
    } else {
      await addReaction(message.id, emoji)
    }
  }

  const handleStartThread = () => {
    setActiveThread(message.id)
  }

  const handlePinToggle = async () => {
    if (message.isPinned) {
      await unpinMessage(message.id)
    } else {
      await pinMessage(message.id)
    }
  }

  const renderMentions = (content: string) => {
    return content.replace(/@(\w+)/g, '<span class="text-primary font-medium bg-primary/10 px-1 rounded">@$1</span>')
  }

  const quickEmojis = ['👍', '❤️', '😂', '😮', '😢', '🔥', '👏', '🎉']

  if (!user) return null

  return (
    <motion.div
      className={cn(
        "group relative hover:bg-muted/30 -mx-2 px-2 py-1 rounded transition-colors",
        message.isPinned && "bg-yellow-500/5 border-l-2 border-l-yellow-500",
        isGrouped && "mt-1"
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex space-x-3">
        {/* Avatar */}
        {!isGrouped && (
          <HoverCard>
            <HoverCardTrigger asChild>
              <div className="flex-shrink-0 cursor-pointer">
                <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-sm font-medium">
                  {user.avatar || user.name.charAt(0)}
                </div>
              </div>
            </HoverCardTrigger>
            <HoverCardContent className="w-80" side="right">
              <div className="flex items-center space-x-3">
                <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-lg font-medium">
                  {user.avatar || user.name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-sm font-semibold">{user.name}</h4>
                  <p className="text-sm text-muted-foreground">{user.role}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <div className={cn(
                      "h-2 w-2 rounded-full",
                      user.status === 'online' && "bg-green-500",
                      user.status === 'away' && "bg-yellow-500",
                      user.status === 'busy' && "bg-red-500",
                      user.status === 'offline' && "bg-gray-500"
                    )} />
                    <span className="text-xs text-muted-foreground capitalize">{user.status}</span>
                  </div>
                </div>
              </div>
            </HoverCardContent>
          </HoverCard>
        )}

        {/* Grouped message spacing */}
        {isGrouped && <div className="w-10" />}

        {/* Message Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          {!isGrouped && (
            <div className="flex items-baseline space-x-2 mb-1">
              <span className="font-semibold text-sm text-foreground">{user.name}</span>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(message.timestamp)}
              </span>
              {message.editedAt && (
                <span className="text-xs text-muted-foreground">(edited)</span>
              )}
              {message.isPinned && (
                <Badge variant="secondary" className="text-xs">
                  <Pin className="h-3 w-3 mr-1" />
                  Pinned
                </Badge>
              )}
            </div>
          )}

          {/* Message Text */}
          <div 
            className="text-sm text-foreground leading-relaxed"
            dangerouslySetInnerHTML={{ __html: renderMentions(message.content) }}
          />

          {/* Thread Reply Indicator */}
          {message.replyTo && (
            <div className="mt-2 text-xs text-muted-foreground">
              <MessageSquare className="h-3 w-3 inline mr-1" />
              Reply to thread
            </div>
          )}

          {/* Reactions */}
          {message.reactions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {message.reactions.map((reaction) => (
                <Button
                  key={reaction.emoji}
                  variant="secondary"
                  size="sm"
                  className={cn(
                    "h-6 px-2 text-xs",
                    reaction.users.includes(currentUser?.id || '') && "bg-primary/20 border-primary/50"
                  )}
                  onClick={() => handleReaction(reaction.emoji)}
                >
                  <span className="mr-1">{reaction.emoji}</span>
                  {reaction.users.length}
                </Button>
              ))}
            </div>
          )}
        </div>

        {/* Message Actions */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ 
            opacity: showActions ? 1 : 0,
            scale: showActions ? 1 : 0.9
          }}
          className="absolute top-0 right-2 bg-background border border-border rounded-md shadow-sm"
        >
          <div className="flex items-center">
            {/* Quick Reactions */}
            <div className="flex">
              {quickEmojis.slice(0, 3).map((emoji) => (
                <Button
                  key={emoji}
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-sm hover:bg-muted"
                  onClick={() => handleReaction(emoji)}
                >
                  {emoji}
                </Button>
              ))}
            </div>

            {/* More Actions */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleStartThread}>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Start Thread
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowEmojiPicker(true)}>
                  <Smile className="h-4 w-4 mr-2" />
                  Add Reaction
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handlePinToggle}>
                  <Pin className="h-4 w-4 mr-2" />
                  {message.isPinned ? 'Unpin' : 'Pin'} Message
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {canEdit && (
                  <DropdownMenuItem>
                    <Edit2 className="h-4 w-4 mr-2" />
                    Edit Message
                  </DropdownMenuItem>
                )}
                {canDelete && (
                  <DropdownMenuItem 
                    className="text-destructive"
                    onClick={() => deleteMessage(message.id)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Message
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </motion.div>
      </div>

      {/* Emoji Picker Modal */}
      {showEmojiPicker && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute top-0 right-0 bg-background border border-border rounded-lg p-3 shadow-lg z-50"
        >
          <div className="grid grid-cols-4 gap-2">
            {quickEmojis.map((emoji) => (
              <Button
                key={emoji}
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-lg hover:bg-muted"
                onClick={() => {
                  handleReaction(emoji)
                  setShowEmojiPicker(false)
                }}
              >
                {emoji}
              </Button>
            ))}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-2 text-xs"
            onClick={() => setShowEmojiPicker(false)}
          >
            Close
          </Button>
        </motion.div>
      )}
    </motion.div>
  )
}