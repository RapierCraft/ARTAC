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
        if (!currentUser) {
          console.error('No current user found')
          return
        }

        console.log('Communication store sendMessage:', { channelId, content, mentions })
        console.log('Current messages for this channel:', get().messages[channelId])

        // Determine which agent will respond based on channel (moved to top for both online/offline paths)
        let agentName = 'AI Agent'
        
        if (channelId === 'ceo' || channelId === 'channel-ceo' || mentions.includes('ceo') || content.toLowerCase().includes('@ceo')) {
          agentName = 'ARTAC CEO'
        } else if (channelId === 'hr' || channelId === 'channel-hr' || mentions.includes('hr') || content.toLowerCase().includes('@hr')) {
          agentName = 'HR Manager'
        } else if (channelId === 'tech' || channelId === 'channel-tech' || mentions.includes('tech') || content.toLowerCase().includes('@tech')) {
          agentName = 'Tech Lead'
        } else if (channelId === 'finance' || channelId === 'channel-finance' || mentions.includes('finance') || content.toLowerCase().includes('@finance')) {
          agentName = 'Finance Manager'
        }

        console.log('Determined agent for response:', agentName)

        // Check if backend is connected
        const isBackendOnline = await get().checkBackendConnection()

        try {
          if (isBackendOnline) {
            // Use real API
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
            
            if (response.ok) {
              // Message sent successfully, reload messages to get the latest
              await get().loadMessages(channelId)
              
              // Check if this is CEO channel and call real CEO API
              if (agentName === 'ARTAC CEO') {
                console.log('Triggering CEO response after successful message send...')
                
                // Show typing indicator
                set(state => ({
                  agentTyping: {
                    ...state.agentTyping,
                    [channelId]: { agentName, isTyping: true }
                  }
                }))
                
                // Call CEO API for response
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
                      const aiResponse: Message = {
                        id: `ai-${Date.now()}`,
                        channelId,
                        userId: 'ceo-001',
                        content: data.message,
                        type: 'text',
                        timestamp: new Date(),
                        mentions: [],
                        reactions: [],
                        isPinned: false
                      }
                      
                      // Add CEO response to messages
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
                    } else {
                      console.error('CEO API call failed:', ceoResponse.statusText)
                    }
                  } catch (error) {
                    console.error('CEO API error:', error)
                  }
                }, 1500) // 1.5 second delay for CEO response
              }
              return
            } else {
              console.error('Failed to send message via API:', response.statusText)
              // Fall through to mock implementation
            }
          }
          // 1. IMMEDIATELY add user message to UI (optimistic update)
          const userMessage: Message = {
            id: `temp-${Date.now()}`,
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

          // Show user message immediately
          set(state => ({
            messages: {
              ...state.messages,
              [channelId]: [...(state.messages[channelId] || []), userMessage]
            }
          }))

          // 2. Show typing indicator for AI agent response
          console.log('Showing AI agent typing indicator...')
          
          // Agent name already determined at top of function
          
          // Set agent typing state
          set(state => ({
            agentTyping: {
              ...state.agentTyping,
              [channelId]: { agentName, isTyping: true }
            }
          }))

          // 3. Send to backend API (with timeout and error handling)
          console.log(`Sending to ${channelId} via API...`)
          
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
          
          const response = await fetch(`http://localhost:8000/api/v1/communication/channels/${channelId}/messages`, {
            method: 'POST',
            signal: controller.signal,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({
              channel_id: channelId,
              content,
              mentions,
              reply_to: replyTo
            })
          })
          
          clearTimeout(timeoutId)

          if (response.ok) {
            console.log('Message sent to API successfully')
            
            // 4. Function to refresh and get real messages from backend
            const refreshMessages = async () => {
              const messagesResponse = await fetch(`http://localhost:8000/api/v1/communication/channels/${channelId}/messages`)
              if (messagesResponse.ok) {
                const updatedMessages = await messagesResponse.json()
                console.log('Updated messages received:', updatedMessages.length)
                
                // Transform API response to match frontend Message interface
                const transformedMessages = updatedMessages.map((msg: any) => ({
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
                
                // Check for mentions and trigger notifications
                const { currentUser } = get()
                transformedMessages.forEach(msg => {
                  // Skip if it's our own message
                  if (msg.userId === currentUser?.id) return
                  
                  // Check for mentions of current user
                  if (msg.mentions.includes(currentUser?.id || '')) {
                    // Use dynamic import to avoid circular dependency
                    import('./notification-store').then(({ useNotificationStore }) => {
                      const { addNotification } = useNotificationStore.getState()
                      addNotification({
                        type: 'mention',
                        title: `You were mentioned`,
                        message: `In #${state.channels.find(c => c.id === channelId)?.name || 'channel'}: ${msg.content.substring(0, 100)}`,
                        channelId: msg.channelId,
                        userId: msg.userId,
                        messageId: msg.id,
                        actionUrl: `/channel/${channelId}`
                      })
                    })
                  }
                  
                  // Check for replies to current user's messages
                  if (msg.replyTo) {
                    const originalMessage = state.messages[channelId]?.find(m => m.id === msg.replyTo)
                    if (originalMessage?.userId === currentUser?.id) {
                      import('./notification-store').then(({ useNotificationStore }) => {
                        const { addNotification } = useNotificationStore.getState()
                        addNotification({
                          type: 'reply',
                          title: `Someone replied to your message`,
                          message: `In #${state.channels.find(c => c.id === channelId)?.name || 'channel'}: ${msg.content.substring(0, 100)}`,
                          channelId: msg.channelId,
                          userId: msg.userId,
                          messageId: msg.id,
                          actionUrl: `/channel/${channelId}`
                        })
                      })
                    }
                  }
                })

                // Clear agent typing indicator and replace with real messages
                set(state => ({
                  messages: {
                    ...state.messages,
                    [channelId]: transformedMessages.filter(msg => !msg.isTyping)
                  },
                  agentTyping: {
                    ...state.agentTyping,
                    [channelId]: { agentName: state.agentTyping[channelId]?.agentName || 'AI Agent', isTyping: false }
                  }
                }))
                
                return updatedMessages.length
              }
              return 0
            }
            
            // 5. Poll for AI agent response
            let attempts = 0
            const maxAttempts = 10
            const pollInterval = 2000 // 2 seconds
            
            const pollForResponse = async () => {
              attempts++
              const messageCount = await refreshMessages()
              
              // If we found an AI response or reached max attempts, stop polling
              if (messageCount > 1 || attempts >= maxAttempts) {
                console.log(`AI agent response polling completed. Attempts: ${attempts}, Messages: ${messageCount}`)
                return
              }
              
              // Continue polling
              setTimeout(pollForResponse, pollInterval)
            }
            
            // Start polling after a short delay
            setTimeout(pollForResponse, 1000)
            
            // Clear typing indicator after max time regardless
            setTimeout(() => {
              set(state => ({
                agentTyping: {
                  ...state.agentTyping,
                  [channelId]: { agentName: state.agentTyping[channelId]?.agentName || 'AI Agent', isTyping: false }
                }
              }))
            }, maxAttempts * pollInterval)
          } else {
            console.warn('API response not ok:', response.status, response.statusText)
            throw new Error(`Backend returned ${response.status}: Failed to send message`)
          }
          
          // Check if this is CEO channel and call real API
          if (agentName === 'ARTAC CEO') {
            // Call real CEO API
            setTimeout(async () => {
              try {
                const response = await fetch('http://localhost:8000/api/v1/ceo/chat', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    message: content,
                    user_id: currentUser.id
                  })
                })
                
                if (response.ok) {
                  const data = await response.json()
                  const aiResponse: Message = {
                    id: `ai-${Date.now()}`,
                    channelId,
                    userId: 'ceo-001',
                    content: data.message,
                    type: 'text',
                    timestamp: new Date(),
                    mentions: [],
                    reactions: [],
                    metadata: data.project_data ? { projectData: data.project_data } : undefined
                  }
                  
                  set(state => ({
                    messages: {
                      ...state.messages,
                      [channelId]: [...(state.messages[channelId] || []), aiResponse]
                    },
                    agentTyping: {
                      ...state.agentTyping,
                      [channelId]: { agentName: agentName, isTyping: false }
                    }
                  }))
                } else {
                  console.error('CEO API call failed:', response.statusText)
                  // Fallback to mock response
                  const aiResponse = generateMockAIResponse(content, channelId, currentAgentName)
                  if (aiResponse) {
                    set(state => ({
                      messages: {
                        ...state.messages,
                        [channelId]: [...(state.messages[channelId] || []), aiResponse]
                      },
                      agentTyping: {
                        ...state.agentTyping,
                        [channelId]: { agentName: currentAgentName, isTyping: false }
                      }
                    }))
                  }
                }
              } catch (error) {
                console.error('CEO API error:', error)
                // Fallback to mock response
                const aiResponse = generateMockAIResponse(content, channelId, currentAgentName)
                if (aiResponse) {
                  set(state => ({
                    messages: {
                      ...state.messages,
                      [channelId]: [...(state.messages[channelId] || []), aiResponse]
                    },
                    agentTyping: {
                      ...state.agentTyping,
                      [channelId]: { agentName: agentName, isTyping: false }
                    }
                  }))
                }
              }
            }, 1500)
          } else {
            // Use mock responses for other agents
            setTimeout(() => {
              const currentState = get()
              const currentAgentName = currentState.agentTyping[channelId]?.agentName || 'AI Agent'
              const aiResponse = generateMockAIResponse(content, channelId, currentAgentName)
              if (aiResponse) {
                set(state => ({
                  messages: {
                    ...state.messages,
                    [channelId]: [...(state.messages[channelId] || []), aiResponse]
                  }
                }))
              }
            }, 2000) // 2 second delay for mock AI response
          }
        } catch (error) {
          console.warn('Failed to send message:', error)
          
          // Clear typing indicator
          set(state => ({
            agentTyping: {
              ...state.agentTyping,
              [channelId]: { agentName: state.agentTyping[channelId]?.agentName || 'AI Agent', isTyping: false }
            }
          }))
          
          // Show offline mode mock response
          setTimeout(() => {
            const aiResponse = generateMockAIResponse(content, channelId, agentName)
            if (aiResponse) {
              set(state => ({
                messages: {
                  ...state.messages,
                  [channelId]: [...(state.messages[channelId] || []), aiResponse]
                }
              }))
            }
          }, 2000)
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
          
          for (const channel of channelsData) {
            try {
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
                
                messagesData[channel.id] = transformedMessages
              } else {
                // Initialize empty messages for channels with no messages
                messagesData[channel.id] = []
              }
            } catch (msgError) {
              console.warn(`Failed to fetch messages for channel ${channel.id}:`, msgError)
              messagesData[channel.id] = []
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
          
          console.log(`🏠 Home organization: Showing ${homeChannels.length} base channels`)
          
        } catch (error) {
          console.warn('Communication store: Backend unavailable, using offline mode ⚠️')
          console.warn('Error details:', error)
          
          // Only use mock data when backend is completely unavailable
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