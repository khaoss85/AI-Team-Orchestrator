/**
 * QuotaContext - Centralized Quota State Management
 * 
 * Solves the rate limiting issue by:
 * 1. Single source of truth for quota data
 * 2. Request deduplication and coalescing
 * 3. Intelligent caching with TTL
 * 4. Shared WebSocket connection
 * 5. Rate-limited API calls with exponential backoff
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/utils/api'
import { useQuotaToasts } from '@/components/QuotaToast'

// Types
export interface QuotaStatus {
  status: 'normal' | 'warning' | 'rate_limited' | 'quota_exceeded' | 'degraded'
  message: string
  canMakeRequest: boolean
  waitSeconds?: number
  statistics?: {
    requestsThisMinute: number
    requestsToday: number
    minuteUsagePercent: number
    dailyUsagePercent: number
  }
  suggestedActions?: string[]
  rawData?: any
}

interface QuotaContextValue {
  quotaStatus: QuotaStatus
  isLoading: boolean
  error: string | null
  isConnected: boolean
  canMakeRequest: () => Promise<boolean>
  refresh: () => Promise<void>
  getUsagePercentage: () => number
  getStatusColor: () => string
  subscribe: (callback: (status: QuotaStatus) => void) => () => void
}

interface QuotaProviderProps {
  children: React.ReactNode
  workspaceId?: string
  enableWebSocket?: boolean
  showNotifications?: boolean
}

// Cache configuration
const CACHE_TTL = 5000 // 5 seconds cache for status data
const MIN_REFRESH_INTERVAL = 30000 // Minimum 30 seconds between refreshes
const MAX_RETRY_DELAY = 60000 // Max 60 seconds retry delay

// Create context
const QuotaContext = createContext<QuotaContextValue | undefined>(undefined)

// Helper function to get status message
const getStatusMessage = (statusData: any) => {
  const status = statusData.status || 'normal'
  
  switch (status) {
    case 'normal':
      return 'API operating normally'
    case 'warning':
      const usage = Math.max(
        statusData.requests_per_minute?.percentage || 0,
        statusData.requests_per_day?.percentage || 0
      )
      return `API usage at ${usage.toFixed(1)}% - approaching limits`
    case 'rate_limited':
      return 'Rate limit reached. Please wait before making more requests.'
    case 'quota_exceeded':
      return 'Quota exceeded. Some features are temporarily limited.'
    case 'degraded':
      return 'Service operating with reduced capacity due to quota constraints.'
    default:
      return 'API status unknown'
  }
}

export const QuotaProvider: React.FC<QuotaProviderProps> = ({
  children,
  workspaceId,
  enableWebSocket = true,
  showNotifications = true
}) => {
  // State
  const [quotaStatus, setQuotaStatus] = useState<QuotaStatus>({
    status: 'normal',
    message: 'API operating normally',
    canMakeRequest: true
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  // Refs for managing state and timers
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastFetchRef = useRef<number>(0)
  const pendingFetchRef = useRef<Promise<void> | null>(null)
  const subscribersRef = useRef<Set<(status: QuotaStatus) => void>>(new Set())
  const retryDelayRef = useRef<number>(1000) // Start with 1 second retry delay
  const lastNotificationRef = useRef<string>('')

  const { showQuotaError, showQuotaWarning, showQuotaInfo } = useQuotaToasts()

  // Handle status notifications
  const handleStatusNotification = useCallback((status: QuotaStatus) => {
    if (!showNotifications) return

    const notificationKey = `${status.status}-${status.message}`
    
    // Avoid duplicate notifications
    if (lastNotificationRef.current === notificationKey) {
      return
    }
    lastNotificationRef.current = notificationKey

    switch (status.status) {
      case 'quota_exceeded':
        showQuotaError(status.message)
        break
      case 'rate_limited':
        showQuotaWarning(`Rate limited. Wait ${status.waitSeconds || 60} seconds.`)
        break
      case 'warning':
        if (status.statistics) {
          const usage = Math.max(
            status.statistics.minuteUsagePercent,
            status.statistics.dailyUsagePercent
          )
          showQuotaWarning(`API usage at ${usage.toFixed(0)}%`)
        }
        break
      case 'degraded':
        showQuotaWarning('API operating with limited functionality')
        break
      case 'normal':
        // Only show info if recovering from a problem state
        if (quotaStatus.status !== 'normal') {
          showQuotaInfo('API quota restored to normal')
        }
        break
    }
  }, [quotaStatus.status, showNotifications, showQuotaError, showQuotaWarning, showQuotaInfo])

  // Notify subscribers of status changes
  const notifySubscribers = useCallback((status: QuotaStatus) => {
    subscribersRef.current.forEach(callback => {
      try {
        callback(status)
      } catch (error) {
        console.error('Quota subscriber error:', error)
      }
    })
  }, [])

  // Fetch quota status with deduplication and caching
  const fetchQuotaStatus = useCallback(async (force: boolean = false) => {
    // Check cache validity
    const now = Date.now()
    const timeSinceLastFetch = now - lastFetchRef.current

    // If not forcing and within cache TTL, skip fetch
    if (!force && timeSinceLastFetch < CACHE_TTL) {
      console.log(`📊 Quota fetch skipped - using cache (${timeSinceLastFetch}ms old)`)
      return
    }

    // If a fetch is already pending, return the existing promise
    if (pendingFetchRef.current) {
      console.log('📊 Quota fetch already in progress - waiting for existing request')
      return pendingFetchRef.current
    }

    // Create new fetch promise
    const fetchPromise = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Make API calls with proper error handling
        const [statusResponse, checkResponse] = await Promise.all([
          api.quota.getStatus(workspaceId).catch(err => {
            console.error('Status API error:', err)
            return null
          }),
          api.quota.check().catch(err => {
            console.error('Check API error:', err)
            return null
          })
        ])

        if (!statusResponse) {
          throw new Error('Failed to fetch quota status')
        }

        const statusData = statusResponse.data || statusResponse
        const checkData = checkResponse?.data || checkResponse || {}

        const newStatus: QuotaStatus = {
          status: statusData.status || 'normal',
          message: getStatusMessage(statusData),
          canMakeRequest: checkData.can_make_request !== false,
          waitSeconds: checkData.wait_seconds,
          statistics: statusData.requests_per_minute ? {
            requestsThisMinute: statusData.requests_per_minute.current,
            requestsToday: statusData.requests_per_day.current,
            minuteUsagePercent: statusData.requests_per_minute.percentage,
            dailyUsagePercent: statusData.requests_per_day.percentage
          } : undefined,
          suggestedActions: checkData.suggested_actions,
          rawData: statusData
        }

        setQuotaStatus(prevStatus => {
          // Show notifications if status changed
          if (newStatus.status !== prevStatus.status) {
            handleStatusNotification(newStatus)
          }
          return newStatus
        })

        // Notify subscribers
        notifySubscribers(newStatus)

        // Update cache timestamp
        lastFetchRef.current = Date.now()
        
        // Reset retry delay on success
        retryDelayRef.current = 1000

        return newStatus
      } catch (err: any) {
        // Handle 429 rate limit error specially
        if (err.message?.includes('429') || err.message?.includes('Rate limit')) {
          console.error('📊 Rate limit hit - implementing exponential backoff')
          
          // Exponential backoff
          retryDelayRef.current = Math.min(retryDelayRef.current * 2, MAX_RETRY_DELAY)
          
          // Set error state but don't break the app
          setError(`Rate limited. Retrying in ${Math.round(retryDelayRef.current / 1000)}s`)
          
          // Schedule retry with backoff
          if (refreshTimeoutRef.current) {
            clearTimeout(refreshTimeoutRef.current)
          }
          refreshTimeoutRef.current = setTimeout(() => {
            fetchQuotaStatus(true)
          }, retryDelayRef.current)
        } else {
          console.error('Failed to fetch quota status:', err)
          setError('Failed to fetch quota status')
        }
        
        return null
      } finally {
        setIsLoading(false)
        pendingFetchRef.current = null
      }
    }

    pendingFetchRef.current = fetchPromise()
    return pendingFetchRef.current
  }, [workspaceId, handleStatusNotification, notifySubscribers])

  // Setup WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket) {
      console.log('Quota WebSocket disabled')
      return
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
      const wsEndpoint = `${wsUrl}/api/quota/ws`
      const finalUrl = workspaceId 
        ? `${wsEndpoint}?workspace_id=${workspaceId}`
        : wsEndpoint
      
      console.log(`📊 Connecting to quota WebSocket: ${finalUrl}`)
      const ws = new WebSocket(finalUrl)

      ws.onopen = () => {
        console.log('📊 Quota WebSocket connected')
        setIsConnected(true)
        
        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'quota_update' || data.type === 'quota_initial') {
            console.log('📊 Received quota update via WebSocket:', data.type)
            
            const statusData = data.data || data
            
            const newStatus: QuotaStatus = {
              status: statusData.status || 'normal',
              message: getStatusMessage(statusData),
              canMakeRequest: statusData.status === 'normal' || statusData.status === 'warning',
              waitSeconds: statusData.details?.retry_after || statusData.retry_after_seconds,
              statistics: statusData.requests_per_minute ? {
                requestsThisMinute: statusData.requests_per_minute.current,
                requestsToday: statusData.requests_per_day.current,
                minuteUsagePercent: statusData.requests_per_minute.percentage,
                dailyUsagePercent: statusData.requests_per_day.percentage
              } : undefined,
              rawData: statusData
            }
            
            setQuotaStatus(prevStatus => {
              if (newStatus.status !== prevStatus.status && data.type !== 'quota_initial') {
                handleStatusNotification(newStatus)
              }
              return newStatus
            })
            
            notifySubscribers(newStatus)
          } else if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }))
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.warn('Quota WebSocket error:', error)
        setIsConnected(false)
      }

      ws.onclose = (event) => {
        console.log(`Quota WebSocket disconnected (code: ${event.code})`)
        setIsConnected(false)
        wsRef.current = null
        
        // Reconnect if not a normal closure
        if (enableWebSocket && event.code !== 1000 && !reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect quota WebSocket...')
            connectWebSocket()
          }, 15000)
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.warn('Failed to create WebSocket connection:', error)
      setIsConnected(false)
    }
  }, [enableWebSocket, workspaceId, handleStatusNotification, notifySubscribers])

  // Initialize and setup refresh interval
  useEffect(() => {
    // Initial fetch
    fetchQuotaStatus()

    // Setup WebSocket
    if (enableWebSocket) {
      connectWebSocket()
    }

    // Setup conservative refresh interval (only if WebSocket is not connected)
    const refreshInterval = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.log('📊 Periodic quota refresh (WebSocket not connected)')
        fetchQuotaStatus()
      }
    }, MIN_REFRESH_INTERVAL)

    // Cleanup
    return () => {
      clearInterval(refreshInterval)
      
      if (wsRef.current) {
        wsRef.current.close()
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current)
      }
    }
  }, []) // Empty deps - only run once on mount

  // Public methods
  const canMakeRequest = useCallback(async (): Promise<boolean> => {
    try {
      const data = await api.quota.check()
      return data.can_make_request
    } catch (error) {
      console.error('Failed to check quota availability:', error)
      return false
    }
  }, [])

  const refresh = useCallback(() => {
    return fetchQuotaStatus(true) // Force refresh
  }, [fetchQuotaStatus])

  const getUsagePercentage = useCallback(() => {
    if (!quotaStatus.statistics) return 0
    return Math.max(
      quotaStatus.statistics.minuteUsagePercent,
      quotaStatus.statistics.dailyUsagePercent
    )
  }, [quotaStatus])

  const getStatusColor = useCallback(() => {
    switch (quotaStatus.status) {
      case 'normal':
        return 'green'
      case 'warning':
        return 'yellow'
      case 'rate_limited':
        return 'orange'
      case 'quota_exceeded':
        return 'red'
      case 'degraded':
        return 'gray'
      default:
        return 'gray'
    }
  }, [quotaStatus.status])

  const subscribe = useCallback((callback: (status: QuotaStatus) => void) => {
    subscribersRef.current.add(callback)
    
    // Return unsubscribe function
    return () => {
      subscribersRef.current.delete(callback)
    }
  }, [])

  const contextValue: QuotaContextValue = {
    quotaStatus,
    isLoading,
    error,
    isConnected,
    canMakeRequest,
    refresh,
    getUsagePercentage,
    getStatusColor,
    subscribe
  }

  return (
    <QuotaContext.Provider value={contextValue}>
      {children}
    </QuotaContext.Provider>
  )
}

// Custom hook to use quota context
export const useQuota = () => {
  const context = useContext(QuotaContext)
  if (!context) {
    throw new Error('useQuota must be used within a QuotaProvider')
  }
  return context
}

// Legacy hook compatibility wrapper
export const useQuotaMonitor = (options?: any) => {
  console.warn('useQuotaMonitor is deprecated. Use useQuota from QuotaContext instead.')
  
  // Return a compatibility object that matches the old interface
  const quota = useQuota()
  
  return {
    quotaStatus: quota.quotaStatus,
    isLoading: quota.isLoading,
    error: quota.error,
    canMakeRequest: quota.canMakeRequest,
    refresh: quota.refresh,
    getUsagePercentage: quota.getUsagePercentage,
    getStatusColor: quota.getStatusColor,
    isConnected: quota.isConnected
  }
}