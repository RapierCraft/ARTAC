'use client'

import { ScrollArea } from '@/components/ui/scroll-area'
import { useCommunicationStore } from '@/stores/communication-store'
import { cn } from '@/lib/utils'

export function UserList() {
  const { users, currentUser, channels, activeChannel } = useCommunicationStore()

  const currentChannel = channels.find(c => c.id === activeChannel)
  const channelMembers = currentChannel?.members
    ? users.filter(user => currentChannel.members.includes(user.id))
    : users

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h3 className="text-sm font-medium text-foreground">
          Members ({channelMembers.length})
        </h3>
      </div>

      {/* User List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {channelMembers.map((user) => (
            <div
              key={user.id}
              className={cn(
                "flex items-center space-x-3 p-2 rounded hover:bg-muted/50 cursor-pointer transition-colors",
                user.id === currentUser?.id && "bg-muted/30"
              )}
            >
              <div className="relative">
                <div className="h-8 w-8 bg-primary rounded-full flex items-center justify-center text-sm font-medium">
                  {user.avatar || user.name.charAt(0)}
                </div>
                <div className={cn(
                  "absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background",
                  user.status === 'online' && "bg-green-500",
                  user.status === 'away' && "bg-yellow-500",
                  user.status === 'busy' && "bg-red-500",
                  user.status === 'offline' && "bg-gray-500"
                )} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{user.name}</div>
                <div className="text-xs text-muted-foreground">{user.role}</div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}