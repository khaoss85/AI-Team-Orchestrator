/**
 * useQuotaMonitor Hook
 * ====================
 * Manages OpenAI quota monitoring, WebSocket connections, and notifications.
 * Provides real-time quota status updates and usage tracking.
 * 
 * Features:
 * - API-based quota monitoring (always available)
 * - WebSocket real-time updates (requires workspaceId)
 * - Automatic fallback to polling when WebSocket unavailable
 * - Toast notifications for quota status changes
 * 
 * Usage:
 * - Without workspaceId: Uses API polling only (e.g., on projects page)
 * - With workspaceId: Enables WebSocket for real-time updates (e.g., in workspace)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { api } from '@/utils/api'
import { useQuotaToasts } from '@/components/QuotaToast'

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
}

interface UseQuotaMonitorOptions {
  workspaceId?: string
  enableWebSocket?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  showNotifications?: boolean
}

export const useQuotaMonitor = (options: UseQuotaMonitorOptions = {}) => {
  const {
    workspaceId,
    enableWebSocket = true,
    autoRefresh = true,
    refreshInterval = 30000,
    showNotifications = true
  } = options

  const [quotaStatus, setQuotaStatus] = useState<QuotaStatus>({
    status: 'normal',
    message: 'API operating normally',
    canMakeRequest: true
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastNotificationRef = useRef<string>('')

  const { showQuotaError, showQuotaWarning, showQuotaInfo } = useQuotaToasts()

  // Fetch quota status from API
  const fetchQuotaStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Get main status data - API returns {success: true, data: {...}}
      const statusResponse = await api.quota.getStatus()
      const statusData = statusResponse.data || statusResponse

      // Get check result - API returns {success: true, data: {...}}
      const checkResponse = await api.quota.check()
      const checkData = checkResponse.data || checkResponse

      const newStatus: QuotaStatus = {
        status: statusData.status || 'normal',
        message: _getStatusMessage(statusData),
        canMakeRequest: checkData.can_make_request !== false,
        waitSeconds: checkData.wait_seconds,
        statistics: statusData.requests_per_minute ? {
          requestsThisMinute: statusData.requests_per_minute.current,
          requestsToday: statusData.requests_per_day.current,
          minuteUsagePercent: statusData.requests_per_minute.percentage,
          dailyUsagePercent: statusData.requests_per_day.percentage
        } : undefined,
        suggestedActions: checkData.suggested_actions,
        // Add raw data for detailed display
        rawData: statusData
      }

      setQuotaStatus(newStatus)

      // Show notifications if status changed
      if (showNotifications && newStatus.status !== quotaStatus.status) {
        handleStatusNotification(newStatus)
      }

      return newStatus
    } catch (err) {
      console.error('Failed to fetch quota status:', err)
      setError('Failed to fetch quota status')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [quotaStatus.status, showNotifications])

  // Handle status change notifications
  const handleStatusNotification = useCallback((status: QuotaStatus) => {
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
  }, [quotaStatus.status, showQuotaError, showQuotaWarning, showQuotaInfo])

  // Setup WebSocket connection
  const connectWebSocket = useCallback(() => {
    // Skip WebSocket connection if not enabled
    if (!enableWebSocket) {
      console.log('Quota monitor: WebSocket disabled')
      return
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    
    // Use dedicated quota WebSocket endpoint if no workspaceId
    // Otherwise use workspace-specific endpoint for additional updates
    const wsEndpoint = workspaceId 
      ? `${wsUrl}/ws/${workspaceId}`  // Workspace-specific endpoint
      : `${wsUrl}/api/quota/ws`        // Dedicated quota endpoint
    
    console.log(`Quota monitor: Connecting to WebSocket at ${wsEndpoint}`)
    const ws = new WebSocket(wsEndpoint)

    ws.onopen = () => {
      console.log('Quota monitor WebSocket connected')
      // Clear any reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // Handle different message types from both endpoints
        if (data.type === 'quota_status_update' || data.type === 'quota_status') {
          console.log('Received quota update via WebSocket:', data)
          
          // Extract status data (may be nested in data.data for dedicated endpoint)
          const statusData = data.data || data
          
          // Update status immediately
          const newStatus: QuotaStatus = {
            status: statusData.status || 'normal',
            message: statusData.message || 'API operating normally',
            canMakeRequest: statusData.status === 'normal' || statusData.status === 'warning',
            waitSeconds: statusData.details?.retry_after || statusData.retry_after_seconds,
            statistics: statusData.statistics
          }
          
          setQuotaStatus(newStatus)
          
          // Show notification
          if (showNotifications) {
            handleStatusNotification(newStatus)
          }
          
          // Fetch full details for comprehensive update
          fetchQuotaStatus()
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('Quota monitor WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('Quota monitor WebSocket disconnected')
      wsRef.current = null
      
      // Attempt to reconnect after 5 seconds
      if (enableWebSocket && !reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...')
          connectWebSocket()
        }, 5000)
      }
    }

    wsRef.current = ws
  }, [enableWebSocket, workspaceId, fetchQuotaStatus, showNotifications, handleStatusNotification])

  // Setup WebSocket and initial fetch
  useEffect(() => {
    // Initial fetch
    fetchQuotaStatus()

    // Setup WebSocket
    connectWebSocket()

    // Setup auto-refresh
    let refreshInterval: NodeJS.Timeout | null = null
    if (autoRefresh) {
      refreshInterval = setInterval(fetchQuotaStatus, refreshInterval)
    }

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, []) // Only run once on mount

  // Check if request can be made
  const canMakeRequest = useCallback(async (): Promise<boolean> => {
    try {
      const data = await api.quota.check()
      return data.can_make_request
    } catch (error) {
      console.error('Failed to check quota availability:', error)
      return false
    }
  }, [])

  // Refresh quota status on demand
  const refresh = useCallback(() => {
    return fetchQuotaStatus()
  }, [fetchQuotaStatus])

  // Get usage percentage for display
  const getUsagePercentage = useCallback(() => {
    if (!quotaStatus.statistics) return 0
    return Math.max(
      quotaStatus.statistics.minuteUsagePercent,
      quotaStatus.statistics.dailyUsagePercent
    )
  }, [quotaStatus])

  // Get status color for UI
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

  return {
    quotaStatus,
    isLoading,
    error,
    canMakeRequest,
    refresh,
    getUsagePercentage,
    getStatusColor,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN
  }
}

export default useQuotaMonitor