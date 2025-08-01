'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { NotificationSettings } from '@/types/communication'

export interface Notification {
  id: string
  type: 'mention' | 'reply' | 'message' | 'system' | 'call'
  title: string
  message: string
  channelId?: string
  userId?: string
  messageId?: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}

interface NotificationState {
  notifications: Notification[]
  settings: NotificationSettings
  unreadCount: number
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (notificationId: string) => void
  markAllAsRead: () => void
  removeNotification: (notificationId: string) => void
  clearAll: () => void
  updateSettings: (settings: Partial<NotificationSettings>) => void
  
  // Sound and desktop notifications
  playNotificationSound: (type: string) => void
  showDesktopNotification: (title: string, message: string, options?: NotificationOptions) => void
  
  // Permission handling
  requestNotificationPermission: () => Promise<NotificationPermission>
  checkNotificationPermission: () => NotificationPermission
}

// Default notification settings
const defaultSettings: NotificationSettings = {
  channels: {},
  directMessages: {
    desktop: true,
    sound: true
  },
  mentions: {
    desktop: true,
    sound: true
  },
  memos: {
    desktop: true,
    sound: true
  }
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set, get) => ({
      notifications: [],
      settings: defaultSettings,
      unreadCount: 0,

      addNotification: (notificationData) => {
        const notification: Notification = {
          ...notificationData,
          id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          read: false
        }

        set(state => ({
          notifications: [notification, ...state.notifications].slice(0, 100), // Keep only last 100
          unreadCount: state.unreadCount + 1
        }))

        // Play sound if enabled
        const { settings } = get()
        if (notification.type === 'mention' && settings.mentions.sound) {
          get().playNotificationSound('mention')
        } else if (notification.type === 'message' && notification.channelId) {
          const channelSettings = settings.channels[notification.channelId]
          if (channelSettings?.sound) {
            get().playNotificationSound('message')
          }
        }

        // Show desktop notification if enabled
        if (notification.type === 'mention' && settings.mentions.desktop) {
          get().showDesktopNotification(notification.title, notification.message)
        } else if (notification.type === 'message' && notification.channelId) {
          const channelSettings = settings.channels[notification.channelId]
          if (channelSettings?.desktop) {
            get().showDesktopNotification(notification.title, notification.message)
          }
        }
      },

      markAsRead: (notificationId) => {
        set(state => ({
          notifications: state.notifications.map(n => 
            n.id === notificationId ? { ...n, read: true } : n
          ),
          unreadCount: Math.max(0, state.unreadCount - 1)
        }))
      },

      markAllAsRead: () => {
        set(state => ({
          notifications: state.notifications.map(n => ({ ...n, read: true })),
          unreadCount: 0
        }))
      },

      removeNotification: (notificationId) => {
        set(state => {
          const notification = state.notifications.find(n => n.id === notificationId)
          const wasUnread = notification && !notification.read
          return {
            notifications: state.notifications.filter(n => n.id !== notificationId),
            unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount
          }
        })
      },

      clearAll: () => {
        set({
          notifications: [],
          unreadCount: 0
        })
      },

      updateSettings: (newSettings) => {
        set(state => ({
          settings: {
            ...state.settings,
            ...newSettings,
            channels: {
              ...state.settings.channels,
              ...newSettings.channels
            }
          }
        }))
      },

      playNotificationSound: (type: string) => {
        if (typeof window === 'undefined') return
        
        try {
          // Create different sounds for different notification types
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
          const oscillator = audioContext.createOscillator()
          const gainNode = audioContext.createGain()
          
          oscillator.connect(gainNode)
          gainNode.connect(audioContext.destination)
          
          // Different frequencies for different types
          switch (type) {
            case 'mention':
              oscillator.frequency.value = 800
              break
            case 'message':
              oscillator.frequency.value = 600
              break
            case 'system':
              oscillator.frequency.value = 400
              break
            default:
              oscillator.frequency.value = 500
          }
          
          oscillator.type = 'sine'
          gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
          
          oscillator.start(audioContext.currentTime)
          oscillator.stop(audioContext.currentTime + 0.3)
        } catch (error) {
          console.warn('Could not play notification sound:', error)
        }
      },

      showDesktopNotification: (title: string, message: string, options?: NotificationOptions) => {
        if (typeof window !== 'undefined' && get().checkNotificationPermission() === 'granted') {
          try {
            const notification = new Notification(title, {
              body: message,
              icon: '/favicon.ico',
              badge: '/favicon.ico',
              ...options
            })
            
            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000)
            
            // Optional click handler
            notification.onclick = () => {
              window.focus()
              notification.close()
            }
          } catch (error) {
            console.warn('Could not show desktop notification:', error)
          }
        }
      },

      requestNotificationPermission: async () => {
        if (typeof window !== 'undefined' && 'Notification' in window) {
          const permission = await Notification.requestPermission()
          return permission
        }
        return 'denied'
      },

      checkNotificationPermission: () => {
        if (typeof window !== 'undefined' && 'Notification' in window) {
          return Notification.permission
        }
        return 'denied'
      }
    }),
    {
      name: 'artac-notifications',
      partialize: (state) => ({
        settings: state.settings,
        // Don't persist notifications - they should be fresh on reload
      })
    }
  )
)