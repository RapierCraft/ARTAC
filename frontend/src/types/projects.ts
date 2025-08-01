export interface Project {
  id: string
  name: string
  description?: string
  icon?: string
  banner?: string
  color?: string
  isActive: boolean
  createdAt: Date
  updatedAt: Date
  owner: string
  members: string[]
  channels: string[]
  settings: ProjectSettings
}

export interface ProjectSettings {
  isPublic: boolean
  allowInvites: boolean
  defaultNotifications: boolean
  verificationLevel: 'none' | 'low' | 'medium' | 'high'
  explicitContentFilter: 'disabled' | 'members_without_roles' | 'all_members'
  defaultMessageNotifications: 'all_messages' | 'only_mentions'
  systemChannelFlags: string[]
}

export interface ProjectInvite {
  id: string
  projectId: string
  code: string
  inviterId: string
  expiresAt?: Date
  maxUses?: number
  uses: number
  temporary: boolean
  createdAt: Date
}

export interface ProjectRole {
  id: string
  projectId: string
  name: string
  color: string
  permissions: ProjectPermission[]
  position: number
  mentionable: boolean
  hoist: boolean
}

export interface ProjectPermission {
  id: string
  name: string
  description: string
  category: 'general' | 'text' | 'voice' | 'advanced'
}

export interface ProjectTemplate {
  id: string
  name: string
  description: string
  icon: string
  category: 'gaming' | 'education' | 'science_tech' | 'entertainment' | 'creative_arts' | 'local_community' | 'business'
  channels: {
    name: string
    type: 'text' | 'voice' | 'forum'
    category?: string
  }[]
  roles: {
    name: string
    color: string
    permissions: string[]
  }[]
}