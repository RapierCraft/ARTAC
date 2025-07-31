import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string | number) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

export function formatRelativeTime(date: Date | string | number) {
  const now = new Date()
  const targetDate = new Date(date)
  const diffInSeconds = Math.floor((now.getTime() - targetDate.getTime()) / 1000)

  if (diffInSeconds < 60) {
    return 'just now'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}m ago`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}h ago`
  } else {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}d ago`
  }
}

export function formatDuration(seconds: number) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  } else {
    return `${remainingSeconds}s`
  }
}

export function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

export function formatPercentage(value: number, decimals = 1) {
  return `${value.toFixed(decimals)}%`
}

export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export function generateId() {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function isValidUrl(string: string) {
  try {
    new URL(string)
    return true
  } catch (_) {
    return false
  }
}

export function getApiUrl(path: string = '') {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

export function getWebSocketUrl(path: string = '') {
  const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

export function capitalizeFirst(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1)
}

export function camelToKebab(string: string) {
  return string.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase()
}

export function kebabToCamel(string: string) {
  return string.replace(/-([a-z])/g, (g) => g[1].toUpperCase())
}

export function getStatusColor(status: string) {
  switch (status.toLowerCase()) {
    case 'active':
    case 'online':
    case 'completed':
    case 'success':
      return 'text-green-500'
    case 'busy':
    case 'in_progress':
    case 'running':
    case 'pending':
      return 'text-yellow-500'
    case 'suspended':
    case 'paused':
    case 'warning':
      return 'text-orange-500'
    case 'terminated':
    case 'failed':
    case 'error':
    case 'offline':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

export function getStatusBadgeVariant(status: string) {
  switch (status.toLowerCase()) {
    case 'active':
    case 'online':
    case 'completed':
    case 'success':
      return 'success'
    case 'busy':
    case 'in_progress':
    case 'running':
    case 'pending':
      return 'warning'
    case 'suspended':
    case 'paused':
      return 'secondary'
    case 'terminated':
    case 'failed':
    case 'error':
    case 'offline':
      return 'destructive'
    default:
      return 'outline'
  }
}

export function parseJSON<T>(value: string | null, fallback: T): T {
  try {
    return value ? JSON.parse(value) : fallback
  } catch {
    return fallback
  }
}

export function stringifyJSON(value: any): string {
  try {
    return JSON.stringify(value)
  } catch {
    return ''
  }
}

export const API_ENDPOINTS = {
  AGENTS: '/api/v1/agents',
  TASKS: '/api/v1/tasks',
  CONVERSATIONS: '/api/v1/conversations',
  SYSTEM: '/api/v1/system',
  HEALTH: '/health',
} as const