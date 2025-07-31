'use client'

import * as React from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { cn } from '@/lib/utils'

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <div className="relative flex items-center space-x-1 rounded-lg border p-1">
      <button
        onClick={() => setTheme('light')}
        className={cn(
          "relative rounded-md p-1.5 transition-colors",
          theme === "light" ? "bg-background text-foreground" : "text-muted-foreground hover:text-foreground"
        )}
        aria-label="Light theme"
      >
        <Sun className="h-4 w-4" />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={cn(
          "relative rounded-md p-1.5 transition-colors",
          theme === "dark" ? "bg-background text-foreground" : "text-muted-foreground hover:text-foreground"
        )}
        aria-label="Dark theme"
      >
        <Moon className="h-4 w-4" />
      </button>
    </div>
  )
}