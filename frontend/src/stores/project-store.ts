'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Project, ProjectSettings, ProjectTemplate, ProjectInvite } from '@/types/projects'

interface ProjectState {
  projects: Project[]
  activeProject: string | null
  isLoading: boolean
  error: string | null
  
  // Actions
  createProject: (project: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>) => void
  updateProject: (projectId: string, updates: Partial<Project>) => void
  deleteProject: (projectId: string) => void
  setActiveProject: (projectId: string | null) => void
  joinProject: (inviteCode: string) => Promise<boolean>
  leaveProject: (projectId: string) => void
  
  // Project management
  updateProjectSettings: (projectId: string, settings: Partial<ProjectSettings>) => void
  inviteMember: (projectId: string, userId: string) => void
  removeMember: (projectId: string, userId: string) => void
  
  // Real project loading
  loadProjects: () => Promise<void>
  initializeStore: () => Promise<void>
  
  // Templates
  createFromTemplate: (templateId: string, projectName: string) => void
  getTemplates: () => ProjectTemplate[]
}

// Mock templates
const templates: ProjectTemplate[] = [
  {
    id: 'gaming',
    name: 'Gaming',
    description: 'Hang out and play games with friends',
    icon: '🎮',
    category: 'gaming',
    channels: [
      { name: 'general', type: 'text', category: 'Text Channels' },
      { name: 'gaming', type: 'text', category: 'Text Channels' },
      { name: 'General', type: 'voice', category: 'Voice Channels' },
      { name: 'Gaming', type: 'voice', category: 'Voice Channels' }
    ],
    roles: [
      { name: 'Admin', color: '#f04747', permissions: ['administrator'] },
      { name: 'Moderator', color: '#7289da', permissions: ['manage_messages', 'kick_members'] }
    ]
  },
  {
    id: 'study-group',
    name: 'Study Group',
    description: 'Study together and share resources',
    icon: '📚',
    category: 'education',
    channels: [
      { name: 'general', type: 'text', category: 'Study' },
      { name: 'homework-help', type: 'text', category: 'Study' },
      { name: 'resources', type: 'text', category: 'Study' },
      { name: 'Study Hall', type: 'voice', category: 'Voice Channels' }
    ],
    roles: [
      { name: 'Tutor', color: '#43b581', permissions: ['manage_messages'] },
      { name: 'Student', color: '#747f8d', permissions: ['send_messages'] }
    ]
  },
  {
    id: 'business',
    name: 'Company/Business',
    description: 'Collaborate with your team professionally',
    icon: '💼',
    category: 'business',
    channels: [
      { name: 'announcements', type: 'text', category: 'Information' },
      { name: 'general', type: 'text', category: 'General' },
      { name: 'projects', type: 'text', category: 'Work' },
      { name: 'meeting-room', type: 'voice', category: 'Meetings' }
    ],
    roles: [
      { name: 'Manager', color: '#e74c3c', permissions: ['administrator'] },
      { name: 'Team Lead', color: '#f39c12', permissions: ['manage_channels'] },
      { name: 'Employee', color: '#3498db', permissions: ['send_messages'] }
    ]
  },
  {
    id: 'creative',
    name: 'Creative Arts',
    description: 'Share and collaborate on creative projects',
    icon: '🎨',
    category: 'creative_arts',
    channels: [
      { name: 'showcase', type: 'text', category: 'Art' },
      { name: 'feedback', type: 'text', category: 'Art' },
      { name: 'collaboration', type: 'text', category: 'Art' },
      { name: 'Creative Lounge', type: 'voice', category: 'Voice Channels' }
    ],
    roles: [
      { name: 'Artist', color: '#9b59b6', permissions: ['send_messages', 'attach_files'] },
      { name: 'Critic', color: '#1abc9c', permissions: ['send_messages'] }
    ]
  }
]

// Load real projects from backend
const loadRealProjects = async (): Promise<Project[]> => {
  try {
    // Fetch project channels from backend
    const response = await fetch('http://localhost:8000/api/v1/communication/channels')
    if (!response.ok) {
      console.warn('Backend unavailable, no projects loaded')
      return []
    }
    
    const channels = await response.json()
    const projectChannels = channels.filter((channel: any) => channel.id.startsWith('project-'))
    
    // Convert project channels to projects
    const projects: Project[] = projectChannels.map((channel: any) => {
      // Extract project ID from channel ID (project-proj_xxxxx -> proj_xxxxx)
      const projectId = channel.id.replace('project-', '')
      
      return {
        id: channel.id, // Keep the full channel ID as project ID
        name: channel.name.replace('Project: ', ''), // Remove "Project: " prefix
        description: channel.description,
        icon: '🎯', // Default project icon
        color: '#3b82f6', // Default blue color
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
        owner: 'ceo-001', // CEO creates all projects
        members: ['current-user', 'ceo-001'], // Basic members
        channels: [channel.id], // The project channel itself
        settings: {
          isPublic: false,
          allowInvites: true,
          defaultNotifications: true,
          verificationLevel: 'medium',
          explicitContentFilter: 'members_without_roles',
          defaultMessageNotifications: 'only_mentions',
          systemChannelFlags: []
        }
      }
    })
    
    console.log(`✅ Loaded ${projects.length} real projects from backend`)
    return projects
    
  } catch (error) {
    console.warn('Failed to load projects from backend:', error)
    return []
  }
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projects: [], // Start with no projects - will be loaded from backend
      activeProject: null, // Default to Home (null = Home organization)
      isLoading: false,
      error: null,

      createProject: (projectData) => {
        const newProject: Project = {
          ...projectData,
          id: `project-${Date.now()}`,
          createdAt: new Date(),
          updatedAt: new Date()
        }
        
        set(state => ({
          projects: [...state.projects, newProject],
          activeProject: newProject.id
        }))
      },

      updateProject: (projectId, updates) => {
        set(state => ({
          projects: state.projects.map(project =>
            project.id === projectId
              ? { ...project, ...updates, updatedAt: new Date() }
              : project
          )
        }))
      },

      deleteProject: (projectId) => {
        set(state => ({
          projects: state.projects.filter(p => p.id !== projectId),
          activeProject: state.activeProject === projectId ? null : state.activeProject
        }))
      },

      setActiveProject: (projectId) => {
        set({ activeProject: projectId })
      },

      joinProject: async (inviteCode) => {
        // Simulate API call
        return new Promise((resolve) => {
          setTimeout(() => {
            // Mock join logic
            resolve(true)
          }, 1000)
        })
      },

      leaveProject: (projectId) => {
        set(state => ({
          projects: state.projects.filter(p => p.id !== projectId),
          activeProject: state.activeProject === projectId ? null : state.activeProject
        }))
      },

      updateProjectSettings: (projectId, settings) => {
        set(state => ({
          projects: state.projects.map(project =>
            project.id === projectId
              ? { 
                  ...project, 
                  settings: { ...project.settings, ...settings },
                  updatedAt: new Date()
                }
              : project
          )
        }))
      },

      inviteMember: (projectId, userId) => {
        set(state => ({
          projects: state.projects.map(project =>
            project.id === projectId
              ? { 
                  ...project, 
                  members: [...project.members, userId],
                  updatedAt: new Date()
                }
              : project
          )
        }))
      },

      removeMember: (projectId, userId) => {
        set(state => ({
          projects: state.projects.map(project =>
            project.id === projectId
              ? { 
                  ...project, 
                  members: project.members.filter(id => id !== userId),
                  updatedAt: new Date()
                }
              : project
          )
        }))
      },

      createFromTemplate: (templateId, projectName) => {
        const template = templates.find(t => t.id === templateId)
        if (!template) return

        const newProject: Project = {
          id: `project-${Date.now()}`,
          name: projectName,
          description: template.description,
          icon: template.icon,
          color: '#3b82f6',
          isActive: true,
          createdAt: new Date(),
          updatedAt: new Date(),
          owner: 'current-user',
          members: ['current-user'],
          channels: [], // Will be populated based on template
          settings: {
            isPublic: false,
            allowInvites: true,
            defaultNotifications: true,
            verificationLevel: 'low',
            explicitContentFilter: 'members_without_roles',
            defaultMessageNotifications: 'only_mentions',
            systemChannelFlags: []
          }
        }

        set(state => ({
          projects: [...state.projects, newProject],
          activeProject: newProject.id
        }))
      },

      getTemplates: () => templates,

      // Load projects from backend
      loadProjects: async () => {
        set({ isLoading: true, error: null })
        try {
          const realProjects = await loadRealProjects()
          set({ 
            projects: realProjects, 
            isLoading: false,
            error: null
          })
          console.log(`🎯 Project store: Loaded ${realProjects.length} real projects`)
        } catch (error) {
          console.error('Failed to load projects:', error)
          set({ 
            isLoading: false, 
            error: 'Failed to load projects',
            projects: [] // Ensure no mock projects on error
          })
        }
      },

      // Initialize store - load real projects from backend
      initializeStore: async () => {
        console.log('🏠 Project store: Initializing with Home organization (no static projects)')
        await get().loadProjects()
      }
    }),
    {
      name: 'project-store'
    }
  )
)