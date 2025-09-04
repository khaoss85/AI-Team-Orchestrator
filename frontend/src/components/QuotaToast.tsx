'use client'

import React, { createContext, useContext, useCallback } from 'react'
import { toast } from 'react-hot-toast'
import { 
  AlertTriangle, 
  Info, 
  XCircle,
  CheckCircle,
  X 
} from 'lucide-react'

// Toast notification functions for quota monitoring
export const useQuotaToasts = () => {
  const showQuotaError = useCallback((message: string, options?: { duration?: number }) => {
    toast.error(message, {
      icon: <XCircle className="w-5 h-5" />,
      duration: options?.duration || 8000,
      className: 'quota-toast-error',
      style: {
        background: '#F9FAFB',
        border: '1px solid #E5E7EB',
        color: '#374151',
      },
      position: 'top-right',
    })
  }, [])

  const showQuotaWarning = useCallback((message: string, options?: { duration?: number }) => {
    toast(message, {
      icon: <AlertTriangle className="w-5 h-5 text-gray-600" />,
      duration: options?.duration || 6000,
      className: 'quota-toast-warning',
      style: {
        background: '#F9FAFB',
        border: '1px solid #E5E7EB',
        color: '#374151',
      },
      position: 'top-right',
    })
  }, [])

  const showQuotaInfo = useCallback((message: string, options?: { duration?: number }) => {
    toast(message, {
      icon: <Info className="w-5 h-5 text-gray-600" />,
      duration: options?.duration || 4000,
      className: 'quota-toast-info',
      style: {
        background: '#FFFFFF',
        border: '1px solid #E5E7EB',
        color: '#374151',
      },
      position: 'top-right',
    })
  }, [])

  const showQuotaSuccess = useCallback((message: string, options?: { duration?: number }) => {
    toast.success(message, {
      icon: <CheckCircle className="w-5 h-5" />,
      duration: options?.duration || 4000,
      className: 'quota-toast-success',
      style: {
        background: '#FFFFFF',
        border: '1px solid #E5E7EB',
        color: '#374151',
      },
      position: 'top-right',
    })
  }, [])

  return {
    showQuotaError,
    showQuotaWarning,
    showQuotaInfo,
    showQuotaSuccess
  }
}

// QuotaNotification component for banners/alerts
interface QuotaNotificationProps {
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
  onDismiss?: () => void
  className?: string
}

export const QuotaNotification: React.FC<QuotaNotificationProps> = ({
  status,
  message,
  canMakeRequest,
  waitSeconds,
  statistics,
  suggestedActions,
  onDismiss,
  className = ''
}) => {
  // Don't show notification if status is normal
  if (status === 'normal') {
    return null
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'quota_exceeded':
        return {
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-900',
          iconColor: 'text-gray-600',
          icon: XCircle,
          title: 'API Quota Exceeded'
        }
      case 'rate_limited':
        return {
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-900',
          iconColor: 'text-gray-600',
          icon: AlertTriangle,
          title: 'API Rate Limited'
        }
      case 'warning':
        return {
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-900',
          iconColor: 'text-gray-600',
          icon: AlertTriangle,
          title: 'API Usage Warning'
        }
      case 'degraded':
        return {
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-800',
          iconColor: 'text-gray-500',
          icon: Info,
          title: 'API Service Degraded'
        }
      default:
        return {
          bgColor: 'bg-white',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-900',
          iconColor: 'text-gray-600',
          icon: Info,
          title: 'API Status Update'
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <div className={`rounded-xl border p-4 ${config.bgColor} ${config.borderColor} ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={`h-5 w-5 ${config.iconColor}`} />
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${config.textColor}`}>
            {config.title}
          </h3>
          <div className={`mt-1 text-sm ${config.textColor}`}>
            <p>{message}</p>
            
            {/* Show wait time for rate limiting */}
            {status === 'rate_limited' && waitSeconds && (
              <p className="mt-1 font-semibold">
                Please wait {waitSeconds} seconds before retrying.
              </p>
            )}
            
            {/* Show usage statistics if available */}
            {statistics && (
              <div className="mt-2 text-xs space-y-1">
                <div>Requests this minute: {statistics.requestsThisMinute}</div>
                <div>Requests today: {statistics.requestsToday}</div>
                <div>
                  Usage: {Math.max(statistics.minuteUsagePercent, statistics.dailyUsagePercent).toFixed(1)}%
                </div>
              </div>
            )}
            
            {/* Show suggested actions */}
            {suggestedActions && suggestedActions.length > 0 && (
              <div className="mt-2">
                <p className="font-medium">Suggested actions:</p>
                <ul className="mt-1 list-disc list-inside text-xs space-y-1">
                  {suggestedActions.map((action, index) => (
                    <li key={index}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
        
        {/* Dismiss button */}
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onDismiss}
                className={`inline-flex rounded-md p-1.5 text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500`}
              >
                <span className="sr-only">Dismiss</span>
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Context for quota notifications (if needed for global state)
interface QuotaNotificationContextType {
  showNotification: (props: Omit<QuotaNotificationProps, 'onDismiss'>) => void
  hideNotification: () => void
}

const QuotaNotificationContext = createContext<QuotaNotificationContextType | null>(null)

export const useQuotaNotification = () => {
  const context = useContext(QuotaNotificationContext)
  if (!context) {
    throw new Error('useQuotaNotification must be used within QuotaNotificationProvider')
  }
  return context
}

export const QuotaNotificationProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [notification, setNotification] = React.useState<Omit<QuotaNotificationProps, 'onDismiss'> | null>(null)

  const showNotification = useCallback((props: Omit<QuotaNotificationProps, 'onDismiss'>) => {
    setNotification(props)
  }, [])

  const hideNotification = useCallback(() => {
    setNotification(null)
  }, [])

  return (
    <QuotaNotificationContext.Provider value={{ showNotification, hideNotification }}>
      {children}
      {notification && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <QuotaNotification
            {...notification}
            onDismiss={hideNotification}
          />
        </div>
      )}
    </QuotaNotificationContext.Provider>
  )
}

export default QuotaNotification