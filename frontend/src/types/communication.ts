export interface User {
  id: string
  name: string
  avatar?: string
  role: string
  status: 'online' | 'away' | 'busy' | 'offline'
  lastSeen?: Date
  isInVoiceChannel?: string // Voice channel ID if user is in voice
  isSpeaking?: boolean
  isMuted?: boolean
  isDeafened?: boolean
  isTyping?: boolean
  typingIn?: string // Channel ID where user is typing
}

export interface Channel {
  id: string
  name: string
  description?: string
  type: 'public' | 'private' | 'direct' | 'voice' | 'forum'
  members: string[] // User IDs
  createdBy: string
  createdAt: Date
  lastActivity?: Date
  unreadCount?: number
  isPinned?: boolean
  // Voice channel specific
  voiceSettings?: VoiceChannelSettings
  connectedUsers?: string[] // User IDs currently in voice
  // Forum specific
  forumSettings?: ForumSettings
  posts?: ForumPost[]
}

export interface Message {
  id: string
  channelId: string
  userId: string
  content: string
  type: 'text' | 'file' | 'image' | 'memo' | 'task-assignment' | 'system'
  timestamp: Date
  editedAt?: Date
  replyTo?: string // Message ID for threads
  mentions: string[] // User IDs
  reactions: Reaction[]
  attachments?: Attachment[]
  isPinned?: boolean
  isTyping?: boolean // For typing indicators
}

export interface Reaction {
  emoji: string
  users: string[] // User IDs who reacted
}

export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url: string
}

export interface Thread {
  parentMessageId: string
  messages: Message[]
  participants: string[]
  lastActivity: Date
}

export interface Memo {
  id: string
  title: string
  content: string
  author: string
  recipients: string[] // User IDs or 'all'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  tags: string[]
  createdAt: Date
  readBy: string[] // User IDs
  isPinned?: boolean
}

export interface NotificationSettings {
  channels: {
    [channelId: string]: {
      muted: boolean
      desktop: boolean
      sound: boolean
    }
  }
  directMessages: {
    desktop: boolean
    sound: boolean
  }
  mentions: {
    desktop: boolean
    sound: boolean
  }
  memos: {
    desktop: boolean
    sound: boolean
  }
}

// Voice Channel Features
export interface VoiceChannelSettings {
  bitrate: number // Audio quality (64, 96, 128, 256, 320 kbps)
  userLimit?: number // Max users (null = unlimited)
  requirePermission: boolean // Push to talk or voice activation
  noiseReduction: boolean
  echoCancellation: boolean
}

export interface VoiceConnection {
  userId: string
  channelId: string
  isMuted: boolean
  isDeafened: boolean
  isSpeaking: boolean
  connectionId: string
  joinedAt: Date
}

// Forum Features
export interface ForumSettings {
  allowPosts: boolean
  requireApproval: boolean
  allowUpvotes: boolean
  allowDownvotes: boolean
  postCooldown: number // Minutes between posts
  categories: ForumCategory[]
}

export interface ForumCategory {
  id: string
  name: string
  description?: string
  color: string
  requirePermission?: boolean
  moderators: string[] // User IDs
}

export interface ForumPost {
  id: string
  channelId: string
  categoryId?: string
  title: string
  content: string
  author: string
  createdAt: Date
  editedAt?: Date
  isPinned: boolean
  isLocked: boolean
  upvotes: string[] // User IDs
  downvotes: string[] // User IDs
  replies: ForumReply[]
  tags: string[]
  attachments: Attachment[]
  views: number
}

export interface ForumReply {
  id: string
  postId: string
  content: string
  author: string
  createdAt: Date
  editedAt?: Date
  upvotes: string[]
  downvotes: string[]
  replyTo?: string // Reply to another reply ID
  attachments: Attachment[]
}

// Screen Sharing & Video
export interface MediaStream {
  id: string
  userId: string
  channelId: string
  type: 'screen' | 'camera' | 'both'
  isActive: boolean
  quality: 'low' | 'medium' | 'high'
  startedAt: Date
  viewers: string[] // User IDs watching
}

// Advanced Threading
export interface ThreadMessage extends Message {
  threadDepth: number // 0 = original, 1 = first reply, etc.
  threadPath: string[] // Array of parent message IDs
}

// Real-time Features
export interface TypingIndicator {
  userId: string
  channelId: string
  startedAt: Date
}

export interface UserPresence {
  userId: string
  status: 'online' | 'away' | 'busy' | 'offline'
  lastActivity: Date
  currentActivity?: string // What they're doing
  deviceType: 'desktop' | 'mobile' | 'web'
}

// File Sharing
export interface FileUpload {
  id: string
  name: string
  type: string
  size: number
  uploadedBy: string
  uploadedAt: Date
  channelId: string
  messageId?: string
  url: string
  thumbnailUrl?: string
  isPublic: boolean
  downloadCount: number
}

// Advanced Search
export interface SearchFilter {
  query: string
  channels?: string[] // Channel IDs to search in
  users?: string[] // Messages from specific users
  dateRange?: {
    start: Date
    end: Date
  }
  messageTypes?: string[]
  hasAttachments?: boolean
  isStarred?: boolean
  inThreads?: boolean
}

export interface SearchResult {
  id: string
  type: 'message' | 'file' | 'user' | 'channel' | 'forum_post'
  relevance: number
  content: string
  context: any // The actual message, file, etc.
  highlights: string[] // Highlighted search terms
}