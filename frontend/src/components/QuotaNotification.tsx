/**
 * QuotaNotification Component
 * ===========================
 * Displays OpenAI API quota status and notifications to users.
 * Supports real-time updates via WebSocket and provides user-friendly messages.
 */

import React, { useEffect, useState, useCallback } from 'react'
import { api } from '@/utils/api'

interface QuotaNotification {
  show_notification: boolean
  type: 'info' | 'warning' | 'error'
  title: string
  message: string
  actions: string[]
}

interface QuotaUsage {
  minute: {
    current: number
    limit: number
    percentage: number
  }
  daily: {
    current: number
    limit: number
    percentage: number
  }
}

interface QuotaNotificationProps {
  workspaceId?: string
  position?: 'top' | 'bottom' | 'inline'
  showUsageBar?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

export const QuotaNotification: React.FC<QuotaNotificationProps> = ({
  workspaceId,
  position = 'top',
  showUsageBar = true,
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [notification, setNotification] = useState<QuotaNotification | null>(null)
  const [usage, setUsage] = useState<QuotaUsage | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  // Fetch quota status from API
  const fetchQuotaStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      
      // Fetch notification data
      const notificationData = await api.quota.getNotifications()
      
      if (notificationData.show_notification && !isDismissed) {
        setNotification(notificationData)
      } else {
        setNotification(null)
      }
      
      // Fetch usage statistics if needed
      if (showUsageBar) {
        const usageData = await api.quota.getUsage('current')
        setUsage(usageData.usage)
      }
    } catch (error) {
      console.error('Failed to fetch quota status:', error)
    } finally {
      setIsLoading(false)
    }
  }, [isDismissed, showUsageBar])

  // Setup WebSocket connection for real-time updates
  useEffect(() => {
    if (!workspaceId) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const websocket = new WebSocket(`${wsUrl}/ws/${workspaceId}`)

    websocket.onopen = () => {
      console.log('Quota notification WebSocket connected')
    }

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // Handle quota status updates
        if (data.type === 'quota_status_update') {
          // Refresh quota status when update received
          fetchQuotaStatus()
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    setWs(websocket)

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [workspaceId, fetchQuotaStatus])

  // Initial load and periodic refresh
  useEffect(() => {
    fetchQuotaStatus()

    if (autoRefresh) {
      const interval = setInterval(fetchQuotaStatus, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [fetchQuotaStatus, autoRefresh, refreshInterval])

  // Handle notification dismissal
  const handleDismiss = () => {
    setIsDismissed(true)
    setNotification(null)
    
    // Reset dismissal after 1 hour
    setTimeout(() => setIsDismissed(false), 3600000)
  }

  // Get icon based on notification type - Minimal design approach
  const getIcon = () => {
    if (!notification) return null
    
    switch (notification.type) {
      case 'error':
        return <span className="text-gray-600 text-xl">⚠</span>
      case 'warning':
        return <span className="text-gray-600 text-xl">⚠</span>
      case 'info':
      default:
        return <span className="text-gray-600 text-xl">ℹ</span>
    }
  }

  // Get background color based on notification type - Minimal design approach
  const getBackgroundColor = () => {
    if (!notification) return ''
    
    switch (notification.type) {
      case 'error':
        return 'bg-gray-50 border-gray-200'
      case 'warning':
        return 'bg-gray-50 border-gray-200'
      case 'info':
      default:
        return 'bg-white border-gray-200'
    }
  }

  // Get progress bar color based on usage - Minimal design approach
  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-gray-400'
    if (percentage >= 75) return 'bg-gray-300'
    return 'bg-gray-900'
  }

  // Position classes
  const getPositionClasses = () => {
    switch (position) {
      case 'top':
        return 'fixed top-0 left-0 right-0 z-50'
      case 'bottom':
        return 'fixed bottom-0 left-0 right-0 z-50'
      case 'inline':
      default:
        return 'relative'
    }
  }

  // Render usage bar
  const renderUsageBar = () => {
    if (!showUsageBar || !usage) return null

    return (
      <div className="mt-3 space-y-2">
        <div className="text-xs text-gray-600">
          <div className="flex justify-between items-center mb-1">
            <span>Requests per minute</span>
            <span>{usage.minute.current} / {usage.minute.limit}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={usage.minute.percentage} aria-valuemin={0} aria-valuemax={100}>
            <div
              className={`${getProgressColor(usage.minute.percentage)} h-2 rounded-full transition-all duration-300`}
              style={{ width: `${Math.min(usage.minute.percentage, 100)}%` }}
            />
          </div>
        </div>
        
        <div className="text-xs text-gray-600">
          <div className="flex justify-between items-center mb-1">
            <span>Daily quota</span>
            <span>{usage.daily.current.toLocaleString()} / {usage.daily.limit.toLocaleString()}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={usage.daily.percentage} aria-valuemin={0} aria-valuemax={100}>
            <div
              className={`${getProgressColor(usage.daily.percentage)} h-2 rounded-full transition-all duration-300`}
              style={{ width: `${Math.min(usage.daily.percentage, 100)}%` }}
            />
          </div>
        </div>
      </div>
    )
  }

  // Don't render if no notification
  if (!notification || !notification.show_notification) {
    // Still show usage bar if requested and inline - Minimal design
    if (showUsageBar && usage && position === 'inline') {
      return (
        <div className="p-4 bg-white rounded-xl border border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-2">API Usage</h3>
          {renderUsageBar()}
        </div>
      )
    }
    return null
  }

  return (
    <div className={`${getPositionClasses()} p-4`}>
      <div className={`${getBackgroundColor()} border rounded-xl p-4`}>
        <div className="flex">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-gray-900">
              {notification.title}
            </h3>
            <div className="mt-2 text-sm text-gray-700">
              <p>{notification.message}</p>
            </div>
            {notification.actions && notification.actions.length > 0 && (
              <div className="mt-3">
                <div className="text-sm">
                  <ul className="list-disc list-inside space-y-1">
                    {notification.actions.map((action, index) => (
                      <li key={index} className="text-gray-600">
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            {renderUsageBar()}
          </div>
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={handleDismiss}
                className="inline-flex rounded-md p-1.5 text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <span className="sr-only">Dismiss</span>
                <span className="text-xl" aria-hidden="true">×</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default QuotaNotification