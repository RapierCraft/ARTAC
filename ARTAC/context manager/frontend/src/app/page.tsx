'use client'

import { useEffect, useState } from 'react'
import { MissionControlLayout } from '@/components/mission-control/layout'
import { LoadingScreen } from '@/components/ui/loading-screen'
import { useSystemStore } from '@/stores/system-store'

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true)
  const { initializeSystem, isInitialized } = useSystemStore()

  useEffect(() => {
    const initialize = async () => {
      try {
        await initializeSystem()
      } catch (error) {
        console.error('Failed to initialize system:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initialize()
  }, [initializeSystem])

  if (isLoading || !isInitialized) {
    return <LoadingScreen />
  }

  return <MissionControlLayout />
}