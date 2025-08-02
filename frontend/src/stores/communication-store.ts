import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { User, Channel, Message, Thread, Memo, NotificationSettings } from '@/types/communication'

interface CommunicationStore {
  // State
  currentUser: User | null
  users: User[]
  channels: Channel[]
  allChannels: Channel[] // All channels from backend
  messages: Record<string, Message[]> // channelId -> messages
  threads: Record<string, Thread> // messageId -> thread
  memos: Memo[]
  activeChannel: string | null
  activeThread: string | null
  isLoading: boolean
  error: string | null
  notificationSettings: NotificationSettings | null
  
  // AI Agent typing states
  agentTyping: Record<string, { agentName: string; isTyping: boolean }> // channelId -> agent info
  
  // Auto-refresh
  refreshInterval: NodeJS.Timeout | null
  
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
  loadChannels: () => Promise<void>
  loadMessages: (channelId: string) => Promise<void>
  checkBackendConnection: () => Promise<boolean>
  initialize: () => Promise<void>
  
  // Project-based channel filtering
  filterChannelsForProject: (projectId: string | null) => void
  getHomeChannels: () => Channel[]
  getProjectChannels: (projectId: string) => Channel[]
  
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
      id: 'ceo-001',
      name: 'ARTAC CEO',
      role: 'CEO',
      status: 'online',
      avatar: '👑'
    },
    {
      id: 'current-user',
      name: 'User',
      role: 'User',
      status: 'online',
      avatar: '👤'
    },
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
      id: 'channel-ceo',
      name: 'ceo',
      description: 'CEO Communication Channel',
      type: 'public',
      members: users.map(u => u.id),
      createdBy: 'ceo-001',
      createdAt: new Date('2024-01-01'),
      unreadCount: 2
    },
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
    'channel-ceo': [
      {
        id: 'ceo-msg-1',
        channelId: 'channel-ceo',
        userId: 'current-user',
        content: 'Hello @ceo-001, I wanted to discuss the quarterly projections and get your thoughts on our strategic direction.',
        type: 'text',
        timestamp: new Date('2024-07-31T08:00:00Z'),
        mentions: ['ceo-001'],
        reactions: []
      },
      {
        id: 'ceo-msg-2',
        channelId: 'channel-ceo',
        userId: 'ceo-001',
        content: 'Great question! Our Q4 strategy focuses on three key areas:\n\n**1. AI Agent Expansion** 🤖\n- Scale our multi-agent architecture\n- Implement advanced decision-making capabilities\n\n**2. Market Penetration** 📈\n- Target enterprise clients in finance and healthcare\n- Expand our SaaS offerings\n\n**3. Innovation Pipeline** 🚀\n- Voice-first interfaces\n- Real-time collaboration tools\n\nWhat specific areas would you like to dive deeper into?',
        type: 'text',
        timestamp: new Date('2024-07-31T08:05:00Z'),
        mentions: ['current-user'],
        reactions: [
          { emoji: '🚀', users: ['current-user'] },
          { emoji: '💯', users: ['current-user'] }
        ],
        replyTo: 'ceo-msg-1'
      },
      {
        id: 'ceo-msg-3',
        channelId: 'channel-ceo',
        userId: 'current-user',
        content: 'This looks fantastic! I\'m particularly interested in the **Voice-first interfaces**. How do you see this integrating with our current platform?',
        type: 'text',
        timestamp: new Date('2024-07-31T08:10:00Z'),
        mentions: ['ceo-001'],
        reactions: [],
        replyTo: 'ceo-msg-2'
      }
    ],
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

// Generate mock AI responses for offline mode
const generateMockAIResponse = (userMessage: string, channelId: string, agentName: string): Message | null => {
  const responses = {
    'ARTAC CEO': [
      "Excellent point! Let me think about the strategic implications of this approach.",
      "That's a great question. Our roadmap focuses on sustainable growth while maintaining innovation excellence.",
      "I appreciate your insights. This aligns perfectly with our Q4 objectives.",
      "Thank you for bringing this up. Let's schedule a follow-up to dive deeper into the details.",
      "This is exactly the kind of forward-thinking we need. Great work!"
    ],
    'HR Manager': [
      "Thanks for reaching out! I'll review the employee handbook and get back to you within 24 hours.",
      "That's a great suggestion for improving our workplace culture. Let me discuss this with the team.",
      "I understand your concern. Let's set up a meeting to address this properly.",
      "Employee wellbeing is our top priority. I'll make sure this gets the attention it deserves."
    ],
    'Tech Lead': [
      "Good catch! Let me review the technical specifications and provide detailed feedback.",
      "This looks promising. Have you considered the scalability implications?",
      "I'll need to run some tests, but this approach should work well with our current architecture.",
      "Great implementation! This will definitely improve our system performance."
    ],
    'AI Agent': [
      "I'm analyzing your request and will provide a comprehensive response shortly.",
      "Based on our conversation history, I recommend exploring these options further.",
      "That's an interesting perspective. Let me gather some additional data to support this.",
      "I understand your requirements. Here's my analysis of the situation."
    ]
  }

  const agentResponses = responses[agentName as keyof typeof responses] || responses['AI Agent']
  const randomResponse = agentResponses[Math.floor(Math.random() * agentResponses.length)]

  return {
    id: `ai-response-${Date.now()}`,
    channelId,
    userId: agentName === 'ARTAC CEO' ? 'ceo-001' : 'ai-agent',
    content: randomResponse,
    type: 'text',
    timestamp: new Date(),
    mentions: [],
    reactions: [],
    isPinned: false
  }
}

export const useCommunicationStore = create<CommunicationStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentUser: null,
      users: [],
      channels: [], // Filtered channels based on active project
      allChannels: [], // All channels from backend
      messages: {},
      threads: {},
      memos: [],
      activeChannel: null,
      activeThread: null,
      isLoading: false,
      error: null,
      notificationSettings: null,
      agentTyping: {},
      refreshInterval: null,
      
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
              ? { ...channel, members: [...Array.from(new Set([...channel.members, currentUser.id]))] }
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
        if (!currentUser) {
          console.error('No current user found')
          return
        }

        console.log('Communication store sendMessage:', { channelId, content, mentions })

        // Create user message immediately and show it
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          channelId,
          userId: currentUser.id,
          content,
          type: 'text',
          timestamp: new Date(),
          mentions,
          reactions: [],
          isPinned: false,
          replyTo
        }

        // Show user message immediately for instant feedback
        set(state => ({
          messages: {
            ...state.messages,
            [channelId]: [...(state.messages[channelId] || []), userMessage]
          }
        }))

        // Persist to localStorage for page reload recovery
        const currentMessages = get().messages[channelId] || []
        const updatedMessages = [...currentMessages, userMessage]
        try {
          localStorage.setItem(`artac_messages_${channelId}`, JSON.stringify(updatedMessages))
        } catch (error) {
          console.warn('Failed to persist messages to localStorage:', error)
        }

        // Determine which agent will respond
        let agentName = 'AI Agent'
        const isCEOChannel = (
          channelId === 'ceo' || 
          channelId === 'channel-ceo' || 
          channelId.includes('ceo') ||
          mentions.includes('ceo') || 
          content.toLowerCase().includes('@ceo')
        )

        if (isCEOChannel) {
          agentName = 'ARTAC CEO'
        }

        try {
          // Show typing indicator
          set(state => ({
            agentTyping: {
              ...state.agentTyping,
              [channelId]: { agentName, isTyping: true }
            }
          }))

          // Send message to backend
          const response = await fetch(`http://localhost:8000/api/v1/communication/channels/${channelId}/messages`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              channel_id: channelId,
              content: content,
              mentions: mentions,
              reply_to: replyTo
            })
          })

          if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`)
          }

          // If CEO channel, get AI response
          if (isCEOChannel) {
            setTimeout(async () => {
              try {
                const ceoResponse = await fetch('http://localhost:8000/api/v1/ceo/chat', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    message: content,
                    user_id: currentUser.id
                  })
                })

                if (ceoResponse.ok) {
                  const data = await ceoResponse.json()
                  
                  // Add CEO response directly to UI
                  const aiResponse: Message = {
                    id: `ceo-${Date.now()}`,
                    channelId,
                    userId: 'ceo-001',
                    content: data.message,
                    type: 'text',
                    timestamp: new Date(),
                    mentions: [],
                    reactions: [],
                    isPinned: false
                  }

                  set(state => ({
                    messages: {
                      ...state.messages,
                      [channelId]: [...(state.messages[channelId] || []), aiResponse]
                    },
                    agentTyping: {
                      ...state.agentTyping,
                      [channelId]: { agentName: '', isTyping: false }
                    }
                  }))

                  // Persist CEO response to localStorage
                  const allMessages = [...(get().messages[channelId] || []), aiResponse]
                  try {
                    localStorage.setItem(`artac_messages_${channelId}`, JSON.stringify(allMessages))
                  } catch (error) {
                    console.warn('Failed to persist CEO response to localStorage:', error)
                  }
                } else {
                  // Fallback to mock response
                  const mockResponse = generateMockAIResponse(content, channelId, agentName)
                  if (mockResponse) {
                    set(state => ({
                      messages: {
                        ...state.messages,
                        [channelId]: [...(state.messages[channelId] || []), mockResponse]
                      },
                      agentTyping: {
                        ...state.agentTyping,
                        [channelId]: { agentName: '', isTyping: false }
                      }
                    }))
                    
                    // Persist mock response to localStorage
                    const allMessages = [...(get().messages[channelId] || []), mockResponse]
                    try {
                      localStorage.setItem(`artac_messages_${channelId}`, JSON.stringify(allMessages))
                    } catch (error) {
                      console.warn('Failed to persist mock response to localStorage:', error)
                    }
                  }
                }
              } catch (error) {
                console.error('CEO API error:', error)
                // Clear typing indicator
                set(state => ({
                  agentTyping: {
                    ...state.agentTyping,
                    [channelId]: { agentName: '', isTyping: false }
                  }
                }))
              }
            }, 1500) // 1.5 second delay for realism
          } else {
            // For non-CEO channels, just clear typing indicator
            setTimeout(() => {
              set(state => ({
                agentTyping: {
                  ...state.agentTyping,
                  [channelId]: { agentName: '', isTyping: false }
                }
              }))
            }, 1000)
          }

        } catch (error) {
          console.error('Failed to send message:', error)
          
          // Clear typing indicator and show mock response for offline mode
          set(state => ({
            agentTyping: {
              ...state.agentTyping,
              [channelId]: { agentName: '', isTyping: false }
            }
          }))

          // Show offline mock response if CEO
          if (isCEOChannel) {
            setTimeout(() => {
              const mockResponse = generateMockAIResponse(content, channelId, agentName)
              if (mockResponse) {
                set(state => ({
                  messages: {
                    ...state.messages,
                    [channelId]: [...(state.messages[channelId] || []), mockResponse]
                  }
                }))
                
                // Persist offline mock response to localStorage
                const allMessages = [...(get().messages[channelId] || []), mockResponse]
                try {
                  localStorage.setItem(`artac_messages_${channelId}`, JSON.stringify(allMessages))
                } catch (error) {
                  console.warn('Failed to persist offline mock response to localStorage:', error)
                }
              }
            }, 2000)
          }
        }
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
                  participants: [...Array.from(new Set([...existingThread.participants, currentUser.id]))],
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
              ? { ...memo, readBy: [...Array.from(new Set([...memo.readBy, currentUser.id]))] }
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
        set({ isLoading: true, error: null })
        
        console.log('Communication store: Attempting to fetch data from backend...')
        
        try {
          // Try to fetch real data from API with timeout
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
          
          const channelsResponse = await fetch('http://localhost:8000/api/v1/communication/channels', {
            signal: controller.signal,
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          })
          
          clearTimeout(timeoutId)
          
          if (!channelsResponse.ok) {
            throw new Error(`Backend returned ${channelsResponse.status}: ${channelsResponse.statusText}`)
          }
          
          const channelsData = await channelsResponse.json()
          console.log('Successfully fetched channels from backend:', channelsData.length)
          
          // Load messages for all channels from backend
          let messagesData: Record<string, Message[]> = {}
          
          // First, load any persisted messages from localStorage
          const loadPersistedMessages = (channelId: string): Message[] => {
            try {
              const persistedData = localStorage.getItem(`artac_messages_${channelId}`)
              if (persistedData) {
                const parsed = JSON.parse(persistedData)
                return parsed.map((msg: any) => ({
                  ...msg,
                  timestamp: new Date(msg.timestamp)
                }))
              }
            } catch (error) {
              console.warn(`Failed to load persisted messages for ${channelId}:`, error)
            }
            return []
          }
          
          for (const channel of channelsData) {
            try {
              // Load persisted messages first
              const persistedMessages = loadPersistedMessages(channel.id)
              
              const messagesResponse = await fetch(`http://localhost:8000/api/v1/communication/channels/${channel.id}/messages`, {
                headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json'
                }
              })
              
              if (messagesResponse.ok) {
                const channelMessages = await messagesResponse.json()
                console.log(`Successfully fetched ${channelMessages.length} messages for channel ${channel.id}`)
                
                // Transform API response to match frontend Message interface
                const transformedMessages = channelMessages.map((msg: any) => ({
                  id: msg.id,
                  channelId: msg.channel_id,
                  userId: msg.user_id,
                  content: msg.content,
                  type: 'text',
                  timestamp: new Date(msg.timestamp),
                  mentions: msg.mentions || [],
                  reactions: [],
                  isPinned: false,
                  replyTo: msg.reply_to
                }))
                
                // Merge backend messages with persisted local messages
                const allMessages = [...transformedMessages, ...persistedMessages]
                // Remove duplicates based on content and timestamp similarity
                const uniqueMessages = allMessages.filter((msg, index, arr) => {
                  return !arr.some((otherMsg, otherIndex) => 
                    otherIndex < index &&
                    otherMsg.content === msg.content &&
                    otherMsg.userId === msg.userId &&
                    Math.abs(otherMsg.timestamp.getTime() - msg.timestamp.getTime()) < 5000 // 5 seconds tolerance
                  )
                })
                uniqueMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
                
                messagesData[channel.id] = uniqueMessages
              } else {
                // Use persisted messages if backend fails
                messagesData[channel.id] = persistedMessages
              }
            } catch (msgError) {
              console.warn(`Failed to fetch messages for channel ${channel.id}:`, msgError)
              // Fallback to persisted messages
              messagesData[channel.id] = loadPersistedMessages(channel.id)
            }
          }
          
          // Get active agents for users
          let realUsers: User[] = [
            {
              id: 'current-user',
              name: 'User',
              role: 'User',
              status: 'online',
              avatar: '👤'
            }
          ]
          
          try {
            const agentsResponse = await fetch('http://localhost:8000/api/v1/communication/agents')
            if (agentsResponse.ok) {
              const agents = await agentsResponse.json()
              const agentUsers = agents.map((agent: any) => ({
                id: agent.id,
                name: agent.name,
                role: agent.role,
                status: agent.claude_session?.active ? 'online' : 'idle',
                avatar: agent.role === 'ceo' ? '👑' : 
                       agent.role === 'cto' ? '🔧' :
                       agent.role === 'developer' ? '💻' :
                       agent.role === 'qa_engineer' ? '🧪' :
                       agent.role === 'devops' ? '⚙️' : '🤖'
              }))
              realUsers = [...realUsers, ...agentUsers]
              console.log(`Loaded ${agentUsers.length} active agents as users`)
            }
          } catch (agentError) {
            console.warn('Failed to fetch agents:', agentError)
          }
          
          // Transform channels for frontend
          const transformedChannels = channelsData.map((channel: any) => ({
            id: channel.id,
            name: channel.name,
            description: channel.description,
            type: channel.type as 'public' | 'private',
            members: realUsers.map(u => u.id), // Add all users to public channels
            createdBy: 'system',
            createdAt: new Date(channel.created_at || new Date()),
            unreadCount: channel.unread_count || 0,
            avatar: channel.id === 'ceo' ? '👑' : 
                   channel.type === 'project' ? '🎯' : 
                   channel.id === 'general' ? '💬' : 
                   channel.id === 'development' ? '💻' :
                   channel.id === 'leadership' ? '🏢' : '📁'
          }))
          
          console.log('🎉 Communication store: Connected to backend successfully ✅')
          console.log('📊 USING ONLY REAL DATA - NO MOCK DATA!')
          console.log(`📋 Loaded ${transformedChannels.length} real channels`)
          console.log(`👥 Loaded ${realUsers.length} real users`) 
          console.log(`💬 Loaded ${Object.keys(messagesData).length} channels with messages`)
          
          // Filter channels for Home organization (base channels only)
          const homeChannels = transformedChannels.filter(channel => 
            !channel.id.startsWith('project-') // Home shows non-project channels
          )
          
          set({
            users: realUsers,
            allChannels: transformedChannels, // Store all channels
            channels: homeChannels, // Show only Home channels initially
            messages: messagesData,
            memos: [], // No mock memos when backend is available
            currentUser: realUsers.find(u => u.id === 'current-user') || realUsers[0],
            activeChannel: 'ceo', // Use real CEO channel ID
            isLoading: false,
            error: null
          })
          
          // Force a refresh of the store to trigger UI updates
          get().setActiveChannel('ceo')
          
          console.log(`🏠 Home organization: Showing ${homeChannels.length} base channels`)
          
        } catch (error) {
          console.warn('Communication store: Backend unavailable, using offline mode ⚠️')
          console.warn('Error details:', error)
          
          // Load persisted messages even in offline mode
          const mockData = generateMockData()
          const offlineMessages = { ...mockData.messages }
          
          // Try to load persisted messages for key channels
          const keyChannels = ['ceo', 'channel-ceo', 'general', 'channel-general']
          keyChannels.forEach((channelId: string) => {
            try {
              const persistedData = localStorage.getItem(`artac_messages_${channelId}`)
              if (persistedData) {
                const parsed = JSON.parse(persistedData)
                const messages = parsed.map((msg: any) => ({
                  ...msg,
                  timestamp: new Date(msg.timestamp)
                }))
                if (messages.length > 0) {
                  offlineMessages[channelId] = messages
                  console.log(`Loaded ${messages.length} persisted messages for ${channelId}`)
                }
              }
            } catch (error) {
              console.warn(`Failed to load persisted messages for ${channelId}:`, error)
            }
          })
          
          set({
            users: mockData.users,
            channels: mockData.channels,
            messages: offlineMessages,
            memos: mockData.memos,
            currentUser: mockData.users.find(u => u.id === 'current-user') || mockData.users[0],
            activeChannel: 'channel-ceo',
            isLoading: false,
            error: 'Offline Mode - Backend unavailable'
          })
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
      },

      // Real API integration methods
      checkBackendConnection: async () => {
        try {
          const response = await fetch('http://localhost:8000/api/v1/communication/agents')
          return response.ok
        } catch {
          return false
        }
      },

      loadChannels: async () => {
        try {
          const response = await fetch('http://localhost:8000/api/v1/communication/channels')
          if (response.ok) {
            const channels = await response.json()
            set({ 
              channels: channels.map((channel: any) => ({
                id: channel.id,
                name: channel.name,
                description: channel.description,
                type: channel.type as 'public' | 'private',
                unreadCount: channel.unread_count || 0,
                lastActivity: new Date(),
                avatar: channel.id === 'ceo' ? '👑' : 
                       channel.type === 'project' ? '🎯' : 
                       channel.id === 'general' ? '💬' : '📁'
              }))
            })
          }
        } catch (error) {
          console.error('Failed to load channels:', error)
        }
      },

      loadMessages: async (channelId: string) => {
        console.log('Loading messages for channel:', channelId)
        try {
          const response = await fetch(`http://localhost:8000/api/v1/communication/channels/${channelId}/messages`)
          if (response.ok) {
            const messages = await response.json()
            set(state => ({
              messages: {
                ...state.messages,
                [channelId]: messages.map((msg: any) => ({
                  id: msg.id,
                  channelId: msg.channel_id,
                  userId: msg.user_id,
                  content: msg.content,
                  type: 'text' as const,
                  timestamp: new Date(msg.timestamp),
                  mentions: msg.mentions || [],
                  reactions: []
                }))
              }
            }))
          }
        } catch (error) {
          console.error('Failed to load messages:', error)
        }
      },

      // Initialize store with real data when backend is available
      initialize: async () => {
        const isBackendOnline = await get().checkBackendConnection()
        if (isBackendOnline) {
          console.log('Backend is online - loading ONLY real data (no mock data)')
          // Use fetchData which now loads only real data when backend is available
          await get().fetchData()
        } else {
          console.log('Backend is offline - using mock data as fallback')
          const mockData = generateMockData()
          set({
            users: mockData.users,
            channels: mockData.channels,
            messages: mockData.messages,
            memos: mockData.memos,
            currentUser: mockData.users.find(u => u.id === 'current-user') || mockData.users[0],
            activeChannel: 'channel-ceo',
            isLoading: false,
            error: 'Offline Mode - Backend unavailable'
          })
        }
      },

      // Project-based channel filtering methods
      filterChannelsForProject: (projectId: string | null) => {
        const { allChannels } = get()
        
        if (projectId === null) {
          // Home organization - show base channels only
          const homeChannels = allChannels.filter(channel => 
            !channel.id.startsWith('project-')
          )
          set({ channels: homeChannels, activeChannel: 'ceo' })
          console.log(`🏠 Switched to Home: ${homeChannels.length} base channels`)
        } else {
          // Project organization - show only that project's channels
          const projectChannels = allChannels.filter(channel => 
            channel.id === projectId || channel.id.startsWith(`${projectId}-`)
          )
          set({ 
            channels: projectChannels, 
            activeChannel: projectChannels[0]?.id || null
          })
          console.log(`🎯 Switched to project ${projectId}: ${projectChannels.length} channels`)
        }
      },

      getHomeChannels: () => {
        const { allChannels } = get()
        return allChannels.filter(channel => !channel.id.startsWith('project-'))
      },

      getProjectChannels: (projectId: string) => {
        const { allChannels } = get()
        return allChannels.filter(channel => 
          channel.id === projectId || channel.id.startsWith(`${projectId}-`)
        )
      }
    }),
    {
      name: 'communication-store'
    }
  )
)