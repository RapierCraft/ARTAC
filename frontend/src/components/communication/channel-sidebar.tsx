'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Hash, 
  Lock, 
  Users, 
  Plus, 
  Search,
  MessageCircle,
  Pin,
  Settings,
  Bell,
  BellOff,
  MoreVertical,
  Hash as HashIcon,
  MessageSquare,
  FileText,
  Mic,
  MicOff,
  Headphones
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { useCommunicationStore } from '@/stores/communication-store'
import { CreateChannelDialog } from './create-channel-dialog'
import { cn } from '@/lib/utils'

export function ChannelSidebar() {
  const {
    channels,
    activeChannel,
    currentUser,
    setActiveChannel,
    showMemoPanel,
    toggleMemoPanel,
    getUnreadCount
  } = useCommunicationStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateChannel, setShowCreateChannel] = useState(false)
  const [isMicMuted, setIsMicMuted] = useState(false)
  const [isDeafened, setIsDeafened] = useState(false)

  const filteredChannels = channels.filter(channel =>
    channel.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    channel.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const publicChannels = filteredChannels.filter(c => c.type === 'public')
  const privateChannels = filteredChannels.filter(c => c.type === 'private')
  const directMessages = filteredChannels.filter(c => c.type === 'direct')

  const totalUnread = getUnreadCount()

  return (
    <div className="h-full flex flex-col bg-muted/30">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">ARTAC Chat</h2>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleMemoPanel}
              className={cn(
                "relative",
                showMemoPanel && "bg-muted text-primary"
              )}
            >
              <FileText className="h-4 w-4" />
              {/* Memo notification badge could go here */}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Bell className="h-4 w-4 mr-2" />
                  Notifications
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search channels..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-background border-border"
          />
        </div>
      </div>

      {/* Channel Lists */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-4">
          {/* Public Channels */}
          <div>
            <div className="flex items-center justify-between px-2 py-1 mb-2">
              <div className="flex items-center space-x-2">
                <HashIcon className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Channels
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => setShowCreateChannel(true)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="space-y-1">
              {publicChannels.map((channel) => (
                <motion.div
                  key={channel.id}
                  whileHover={{ x: 2 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start px-2 py-1.5 h-auto",
                      activeChannel === channel.id && "bg-primary/20 text-primary"
                    )}
                    onClick={() => setActiveChannel(channel.id)}
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center space-x-2 min-w-0">
                        <Hash className="h-4 w-4 flex-shrink-0" />
                        <span className="text-sm truncate">{channel.name}</span>
                      </div>
                      {channel.unreadCount && channel.unreadCount > 0 && (
                        <Badge 
                          variant="destructive" 
                          className="h-5 min-w-[20px] text-xs px-1.5"
                        >
                          {channel.unreadCount > 99 ? '99+' : channel.unreadCount}
                        </Badge>
                      )}
                    </div>
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Private Channels */}
          {privateChannels.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 px-2 py-1 mb-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Private
                </span>
              </div>
              
              <div className="space-y-1">
                {privateChannels.map((channel) => (
                  <motion.div
                    key={channel.id}
                    whileHover={{ x: 2 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <Button
                      variant="ghost"
                      className={cn(
                        "w-full justify-start px-2 py-1.5 h-auto",
                        activeChannel === channel.id && "bg-primary/20 text-primary"
                      )}
                      onClick={() => setActiveChannel(channel.id)}
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center space-x-2 min-w-0">
                          <Lock className="h-4 w-4 flex-shrink-0" />
                          <span className="text-sm truncate">{channel.name}</span>
                        </div>
                        {channel.unreadCount && channel.unreadCount > 0 && (
                          <Badge 
                            variant="destructive" 
                            className="h-5 min-w-[20px] text-xs px-1.5"
                          >
                            {channel.unreadCount > 99 ? '99+' : channel.unreadCount}
                          </Badge>
                        )}
                      </div>
                    </Button>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Direct Messages */}
          <div>
            <div className="flex items-center space-x-2 px-2 py-1 mb-2">
              <MessageCircle className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Direct Messages
              </span>
            </div>
            
            <div className="space-y-1">
              {directMessages.map((channel) => (
                <motion.div
                  key={channel.id}
                  whileHover={{ x: 2 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start px-2 py-1.5 h-auto",
                      activeChannel === channel.id && "bg-primary/20 text-primary"
                    )}
                    onClick={() => setActiveChannel(channel.id)}
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center space-x-2 min-w-0">
                        <div className="h-2 w-2 bg-green-500 rounded-full flex-shrink-0" />
                        <span className="text-sm truncate">{channel.name}</span>
                      </div>
                      {channel.unreadCount && channel.unreadCount > 0 && (
                        <Badge 
                          variant="destructive" 
                          className="h-5 min-w-[20px] text-xs px-1.5"
                        >
                          {channel.unreadCount > 99 ? '99+' : channel.unreadCount}
                        </Badge>
                      )}
                    </div>
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* User Status */}
      {currentUser && (
        <div className="border-t border-border flex-shrink-0 bg-background">
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <div className="relative">
                  <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-base font-medium">
                    {currentUser.avatar || currentUser.name.charAt(0)}
                  </div>
                  <div className={cn(
                    "absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-background",
                    currentUser.status === 'online' && "bg-green-500",
                    currentUser.status === 'away' && "bg-yellow-500", 
                    currentUser.status === 'busy' && "bg-red-500",
                    currentUser.status === 'offline' && "bg-gray-500"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{currentUser.name}</div>
                  <div className="text-xs text-muted-foreground capitalize">{currentUser.status}</div>
                </div>
              </div>
              
              {/* Voice and Settings Controls */}
              <div className="flex items-center space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-8 w-8 p-0",
                    isMicMuted && "bg-red-500/20 text-red-500 hover:bg-red-500/30"
                  )}
                  onClick={() => setIsMicMuted(!isMicMuted)}
                  title={isMicMuted ? "Unmute microphone" : "Mute microphone"}
                >
                  {isMicMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-8 w-8 p-0",
                    isDeafened && "bg-gray-500/20 text-gray-500 hover:bg-gray-500/30"
                  )}
                  onClick={() => setIsDeafened(!isDeafened)}
                  title={isDeafened ? "Undeafen" : "Deafen"}
                >
                  <Headphones className="h-4 w-4" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  title="User settings"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              <strong>Online</strong> • Ready to collaborate
            </div>
          </div>
        </div>
      )}

      {/* Create Channel Dialog */}
      <CreateChannelDialog
        open={showCreateChannel}
        onOpenChange={setShowCreateChannel}
      />
    </div>
  )
}