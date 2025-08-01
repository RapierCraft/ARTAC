"use client"

import { useEffect, useRef } from 'react'
import { useCommunicationStore } from '@/stores/communication-store'

export function useConnectionStatus() {
  const { error } = useCommunicationStore()
  const previousOfflineStatus = useRef<boolean | null>(null)
  
  const isOffline = error && error.includes('Offline')
  
  useEffect(() => {
    // Track status changes for potential future notifications
    previousOfflineStatus.current = !!isOffline
  }, [isOffline])
  
  return {
    isOffline: !!isOffline,
    status: isOffline ? 'offline' : 'online'
  }
}