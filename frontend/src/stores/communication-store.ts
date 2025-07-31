import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { User, Channel, Message, Thread, Memo, NotificationSettings } from '@/types/communication'

interface CommunicationStore {
  // State
  currentUser: User | null
  users: User[]
  channels: Channel[]
  messages: Record<string, Message[]> // channelId -> messages
  threads: Record<string, Thread> // messageId -> thread
  memos: Memo[]
  activeChannel: string | null
  activeThread: string | null
  isLoading: boolean
  error: string | null
  notificationSettings: NotificationSettings | null
  
  // UI State
  showUserList: boolean
  showThreadPanel: boolean
  showMemoPanel: boolean
  toggleUserList: () => void
  toggleThreadPanel: () => void
  toggleMemoPanel: () => void
  searchQuery: string
  selectedUsers: string[]
  
  // Actions
  setCurrentUser: (user: User) => void
  setActiveChannel: (channelId: string | null) => void
  setActiveThread: (messageId: string | null) => void
  
  // Channel operations
  createChannel: (name: string, description?: string, type?: 'public' | 'private') => Promise<void>
  joinChannel: (channelId: string) => Promise<void>
  leaveChannel: (channelId: string) => Promise<void>
  deleteChannel: (channelId: string) => Promise<void>
  
  // Message operations
  sendMessage: (channelId: string, content: string, mentions?: string[], replyTo?: string) => Promise<void>
  editMessage: (messageId: string, content: string) => Promise<void>
  deleteMessage: (messageId: string) => Promise<void>
  addReaction: (messageId: string, emoji: string) => Promise<void>
  removeReaction: (messageId: string, emoji: string) => Promise<void>
  pinMessage: (messageId: string) => Promise<void>
  unpinMessage: (messageId: string) => Promise<void>
  
  // Thread operations
  createThread: (messageId: string, content: string) => Promise<void>
  replyToThread: (parentMessageId: string, content: string) => Promise<void>
  
  // Memo operations
  createMemo: (title: string, content: string, recipients: string[], priority: 'low' | 'medium' | 'high' | 'urgent', tags?: string[]) => Promise<void>
  markMemoAsRead: (memoId: string) => Promise<void>
  deleteMemo: (memoId: string) => Promise<void>
  
  // Search and filter
  searchMessages: (query: string, channelId?: string) => Message[]
  searchUsers: (query: string) => User[]
  
  // UI actions
  toggleUserList: () => void
  toggleThreadPanel: () => void
  toggleMemoPanel: () => void
  setSearchQuery: (query: string) => void
  toggleUserSelection: (userId: string) => void
  clearSelectedUsers: () => void
  
  // Utility
  fetchData: () => Promise<void>
  markChannelAsRead: (channelId: string) => void
  getUnreadCount: () => number
}

// Mock data generator
const generateMockData = () => {
  const users: User[] = [
    {
      id: 'user-1',
      name: 'Alexandra Prime',
      role: 'CEO',
      status: 'online',
      avatar: '👑'
    },
    {
      id: 'user-2', 
      name: 'Marcus Tech',
      role: 'CTO',
      status: 'busy',
      avatar: '🔧'
    },
    {
      id: 'user-3',
      name: 'Sarah Coordinator',
      role: 'Project Manager', 
      status: 'online',
      avatar: '📋'
    },
    {
      id: 'user-4',
      name: 'David Code',
      role: 'Senior Developer',
      status: 'away',
      avatar: '💻'
    },
    {
      id: 'user-5',
      name: 'Lisa Frontend',
      role: 'UI/UX Developer',
      status: 'online',
      avatar: '🎨'
    }
  ]

  const channels: Channel[] = [
    {
      id: 'channel-general',
      name: 'general',
      description: 'Company-wide announcements and discussions',
      type: 'public',
      members: users.map(u => u.id),
      createdBy: 'user-1',
      createdAt: new Date('2024-01-01'),
      unreadCount: 3
    },
    {
      id: 'channel-dev',
      name: 'development',
      description: 'Development team discussions',
      type: 'public',
      members: ['user-2', 'user-4', 'user-5'],
      createdBy: 'user-2',
      createdAt: new Date('2024-01-02'),
      unreadCount: 7
    },
    {
      id: 'channel-design',
      name: 'design',
      description: 'Design and UX discussions',
      type: 'public',
      members: ['user-1', 'user-3', 'user-5'],
      createdBy: 'user-5',
      createdAt: new Date('2024-01-03'),
      unreadCount: 1
    },
    {
      id: 'channel-exec',
      name: 'executive',
      description: 'Executive team private channel',
      type: 'private',
      members: ['user-1', 'user-2', 'user-3'],
      createdBy: 'user-1',
      createdAt: new Date('2024-01-04'),
      unreadCount: 0
    }
  ]

  const messages: Record<string, Message[]> = {
    'channel-general': [
      {
        id: 'msg-1',
        channelId: 'channel-general',
        userId: 'user-1',
        content: 'Welcome to ARTAC Mission Control! 🚀 This is where our entire organization coordinates and collaborates.',
        type: 'text',
        timestamp: new Date('2024-07-31T09:00:00Z'),
        mentions: [],
        reactions: [
          { emoji: '🚀', users: ['user-2', 'user-3', 'user-4'] },
          { emoji: '👏', users: ['user-5'] }
        ]
      },
      {
        id: 'msg-2',
        channelId: 'channel-general',
        userId: 'user-3',
        content: 'Thanks @user-1! Excited to see how our AI agents will transform our workflow.',
        type: 'text',
        timestamp: new Date('2024-07-31T09:15:00Z'),
        mentions: ['user-1'],
        reactions: []
      },
      {
        id: 'msg-3',
        channelId: 'channel-general',
        userId: 'user-2',
        content: 'The new voice interface is incredible. We can now talk directly to our AI agents! 🎤',
        type: 'text',
        timestamp: new Date('2024-07-31T10:30:00Z'),
        mentions: [],
        reactions: [
          { emoji: '🎤', users: ['user-1', 'user-4', 'user-5'] }
        ]
      }
    ],
    'channel-dev': [
      {
        id: 'msg-4',
        channelId: 'channel-dev',
        userId: 'user-4',
        content: 'Just finished implementing the new dashboard components. The real-time data switching is working perfectly!',
        type: 'text',
        timestamp: new Date('2024-07-31T11:00:00Z'),
        mentions: [],
        reactions: [
          { emoji: '💯', users: ['user-2', 'user-5'] }
        ]
      },
      {
        id: 'msg-5',
        channelId: 'channel-dev',
        userId: 'user-5',
        content: 'The black theme looks amazing! Much better than the old blue theme. @user-4 great work! 🎨',
        type: 'text',
        timestamp: new Date('2024-07-31T11:30:00Z'),
        mentions: ['user-4'],
        reactions: [
          { emoji: '🎨', users: ['user-2'] },
          { emoji: '🔥', users: ['user-4'] }
        ]
      }
    ]
  }

  const memos: Memo[] = [
    {
      id: 'memo-1',
      title: 'Q4 Roadmap Update',
      content: 'Our focus for Q4 will be on scaling the AI agent infrastructure and implementing advanced voice capabilities. Key priorities include:\n\n1. Multi-agent orchestration\n2. Enhanced voice interface\n3. Real-time collaboration features\n4. Performance optimizations',
      author: 'user-1',
      recipients: ['all'],
      priority: 'high',
      tags: ['roadmap', 'q4', 'strategy'],
      createdAt: new Date('2024-07-30T14:00:00Z'),
      readBy: ['user-1', 'user-2', 'user-3'],
      isPinned: true
    },
    {
      id: 'memo-2',
      title: 'Security Protocol Updates',
      content: 'Please review the updated security protocols for AI agent deployment. All agents must now undergo additional validation checks before production deployment.',
      author: 'user-2',
      recipients: ['user-4', 'user-5'],
      priority: 'urgent',
      tags: ['security', 'deployment', 'protocols'],
      createdAt: new Date('2024-07-31T08:00:00Z'),
      readBy: ['user-2'],
      isPinned: false
    }
  ]

  return { users, channels, messages, memos }
}

export const useCommunicationStore = create<CommunicationStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentUser: null,
      users: [],
      channels: [],
      messages: {},
      threads: {},
      memos: [],
      activeChannel: null,
      activeThread: null,
      isLoading: false,
      error: null,
      notificationSettings: null,
      
      // UI State
      showUserList: true,
      showThreadPanel: false,
      showMemoPanel: false,
      searchQuery: '',
      selectedUsers: [],

      // Basic setters
      setCurrentUser: (user) => set({ currentUser: user }),
      setActiveChannel: (channelId) => set({ activeChannel: channelId, activeThread: null }),
      setActiveThread: (messageId) => set({ activeThread: messageId, showThreadPanel: !!messageId }),

      // Channel operations
      createChannel: async (name, description, type = 'public') => {
        const { currentUser, users } = get()
        if (!currentUser) return

        const newChannel: Channel = {
          id: `channel-${Date.now()}`,
          name,
          description,
          type,
          members: type === 'public' ? users.map(u => u.id) : [currentUser.id],
          createdBy: currentUser.id,
          createdAt: new Date(),
          unreadCount: 0
        }

        set(state => ({
          channels: [...state.channels, newChannel],
          messages: { ...state.messages, [newChannel.id]: [] }
        }))
      },

      joinChannel: async (channelId) => {
        const { currentUser } = get()
        if (!currentUser) return

        set(state => ({
          channels: state.channels.map(channel =>
            channel.id === channelId
              ? { ...channel, members: [...new Set([...channel.members, currentUser.id])] }
              : channel
          )
        }))
      },

      leaveChannel: async (channelId) => {
        const { currentUser } = get()
        if (!currentUser) return

        set(state => ({
          channels: state.channels.map(channel =>
            channel.id === channelId
              ? { ...channel, members: channel.members.filter(id => id !== currentUser.id) }
              : channel
          )
        }))
      },

      deleteChannel: async (channelId) => {
        set(state => {
          const { [channelId]: deleted, ...remainingMessages } = state.messages
          return {
            channels: state.channels.filter(c => c.id !== channelId),
            messages: remainingMessages,
            activeChannel: state.activeChannel === channelId ? null : state.activeChannel
          }
        })
      },

      // Message operations
      sendMessage: async (channelId, content, mentions = [], replyTo) => {
        const { currentUser } = get()
        if (!currentUser) return

        const newMessage: Message = {
          id: `msg-${Date.now()}`,
          channelId,
          userId: currentUser.id,
          content,
          type: 'text',
          timestamp: new Date(),
          mentions,
          reactions: [],
          replyTo
        }

        set(state => ({
          messages: {
            ...state.messages,
            [channelId]: [...(state.messages[channelId] || []), newMessage]
          }
        }))
      },

      editMessage: async (messageId, content) => {
        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].map(msg =>
              msg.id === messageId
                ? { ...msg, content, editedAt: new Date() }
                : msg
            )
          })
          return { messages: newMessages }
        })
      },

      deleteMessage: async (messageId) => {
        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].filter(msg => msg.id !== messageId)
          })
          return { messages: newMessages }
        })
      },

      addReaction: async (messageId, emoji) => {
        const { currentUser } = get()
        if (!currentUser) return

        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].map(msg => {
              if (msg.id === messageId) {
                const existingReaction = msg.reactions.find(r => r.emoji === emoji)
                if (existingReaction) {
                  if (!existingReaction.users.includes(currentUser.id)) {
                    existingReaction.users.push(currentUser.id)
                  }
                } else {
                  msg.reactions.push({ emoji, users: [currentUser.id] })
                }
              }
              return msg
            })
          })
          return { messages: newMessages }
        })
      },

      removeReaction: async (messageId, emoji) => {
        const { currentUser } = get()
        if (!currentUser) return

        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].map(msg => {
              if (msg.id === messageId) {
                msg.reactions = msg.reactions.map(reaction => {
                  if (reaction.emoji === emoji) {
                    reaction.users = reaction.users.filter(id => id !== currentUser.id)
                  }
                  return reaction
                }).filter(reaction => reaction.users.length > 0)
              }
              return msg
            })
          })
          return { messages: newMessages }
        })
      },

      pinMessage: async (messageId) => {
        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].map(msg =>
              msg.id === messageId ? { ...msg, isPinned: true } : msg
            )
          })
          return { messages: newMessages }
        })
      },

      unpinMessage: async (messageId) => {
        set(state => {
          const newMessages = { ...state.messages }
          Object.keys(newMessages).forEach(channelId => {
            newMessages[channelId] = newMessages[channelId].map(msg =>
              msg.id === messageId ? { ...msg, isPinned: false } : msg
            )
          })
          return { messages: newMessages }
        })
      },

      // Thread operations
      createThread: async (messageId, content) => {
        const { currentUser } = get()
        if (!currentUser) return

        const parentMessage = Object.values(get().messages)
          .flat()
          .find(msg => msg.id === messageId)
        
        if (!parentMessage) return

        const threadMessage: Message = {
          id: `thread-msg-${Date.now()}`,
          channelId: parentMessage.channelId,
          userId: currentUser.id,
          content,
          type: 'text',
          timestamp: new Date(),
          mentions: [],
          reactions: [],
          replyTo: messageId
        }

        set(state => ({
          threads: {
            ...state.threads,
            [messageId]: {
              parentMessageId: messageId,
              messages: [threadMessage],
              participants: [currentUser.id],
              lastActivity: new Date()
            }
          }
        }))
      },

      replyToThread: async (parentMessageId, content) => {
        const { currentUser } = get()
        if (!currentUser) return

        const threadMessage: Message = {
          id: `thread-msg-${Date.now()}`,
          channelId: '',
          userId: currentUser.id,
          content,
          type: 'text',
          timestamp: new Date(),
          mentions: [],
          reactions: [],
          replyTo: parentMessageId
        }

        set(state => {
          const existingThread = state.threads[parentMessageId]
          if (existingThread) {
            return {
              threads: {
                ...state.threads,
                [parentMessageId]: {
                  ...existingThread,
                  messages: [...existingThread.messages, threadMessage],
                  participants: [...new Set([...existingThread.participants, currentUser.id])],
                  lastActivity: new Date()
                }
              }
            }
          }
          return state
        })
      },

      // Memo operations
      createMemo: async (title, content, recipients, priority, tags = []) => {
        const { currentUser } = get()
        if (!currentUser) return

        const newMemo: Memo = {
          id: `memo-${Date.now()}`,
          title,
          content,
          author: currentUser.id,
          recipients,
          priority,
          tags,
          createdAt: new Date(),
          readBy: [currentUser.id]
        }

        set(state => ({
          memos: [newMemo, ...state.memos]
        }))
      },

      markMemoAsRead: async (memoId) => {
        const { currentUser } = get()
        if (!currentUser) return

        set(state => ({
          memos: state.memos.map(memo =>
            memo.id === memoId
              ? { ...memo, readBy: [...new Set([...memo.readBy, currentUser.id])] }
              : memo
          )
        }))
      },

      deleteMemo: async (memoId) => {
        set(state => ({
          memos: state.memos.filter(memo => memo.id !== memoId)
        }))
      },

      // Search functions
      searchMessages: (query, channelId) => {
        const { messages } = get()
        const messagesToSearch = channelId 
          ? messages[channelId] || []
          : Object.values(messages).flat()
        
        return messagesToSearch.filter(msg =>
          msg.content.toLowerCase().includes(query.toLowerCase())
        )
      },

      searchUsers: (query) => {
        const { users } = get()
        return users.filter(user =>
          user.name.toLowerCase().includes(query.toLowerCase()) ||
          user.role.toLowerCase().includes(query.toLowerCase())
        )
      },

      // UI actions
      toggleUserList: () => set(state => ({ showUserList: !state.showUserList })),
      toggleThreadPanel: () => set(state => ({ showThreadPanel: !state.showThreadPanel })),
      toggleMemoPanel: () => set(state => ({ showMemoPanel: !state.showMemoPanel })),
      setSearchQuery: (query) => set({ searchQuery: query }),
      toggleUserSelection: (userId) => {
        set(state => ({
          selectedUsers: state.selectedUsers.includes(userId)
            ? state.selectedUsers.filter(id => id !== userId)
            : [...state.selectedUsers, userId]
        }))
      },
      clearSelectedUsers: () => set({ selectedUsers: [] }),

      // Utility functions
      fetchData: async () => {
        set({ isLoading: true })
        try {
          const mockData = generateMockData()
          set({
            users: mockData.users,
            channels: mockData.channels,
            messages: mockData.messages,
            memos: mockData.memos,
            currentUser: mockData.users[0], // Set first user as current user for demo
            activeChannel: mockData.channels[0].id,
            isLoading: false
          })
        } catch (error) {
          set({ error: 'Failed to load communication data', isLoading: false })
        }
      },

      markChannelAsRead: (channelId) => {
        set(state => ({
          channels: state.channels.map(channel =>
            channel.id === channelId
              ? { ...channel, unreadCount: 0 }
              : channel
          )
        }))
      },

      getUnreadCount: () => {
        const { channels } = get()
        return channels.reduce((total, channel) => total + (channel.unreadCount || 0), 0)
      }
    }),
    {
      name: 'communication-store'
    }
  )
)