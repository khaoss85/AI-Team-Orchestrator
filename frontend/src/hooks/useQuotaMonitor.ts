/**
 * useQuotaMonitor Hook - DEPRECATED
 * ==================================
 * This hook is now a thin wrapper around the QuotaContext to maintain backward compatibility.
 * All new code should use the useQuota hook from QuotaContext directly.
 * 
 * Migration Guide:
 * - Import: `import { useQuota } from '@/contexts/QuotaContext'`
 * - Usage: `const { quotaStatus, isLoading, ... } = useQuota()`
 * 
 * The QuotaContext provides:
 * - Centralized quota state management
 * - Request deduplication and caching
 * - Shared WebSocket connection
 * - Rate-limited API calls with exponential backoff
 */

import { useQuota } from '@/contexts/QuotaContext'

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

interface UseQuotaMonitorOptions {
  workspaceId?: string
  enableWebSocket?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  showNotifications?: boolean
}

/**
 * DEPRECATED: Use useQuota from QuotaContext instead
 * 
 * This hook now acts as a compatibility wrapper around the centralized QuotaContext.
 * It prevents duplicate API calls and rate limiting issues by using shared state.
 * 
 * @deprecated Use `useQuota` from '@/contexts/QuotaContext' instead
 */
export const useQuotaMonitor = (options: UseQuotaMonitorOptions = {}) => {
  // Log deprecation warning in development
  if (process.env.NODE_ENV === 'development') {
    console.warn(
      '[useQuotaMonitor] This hook is deprecated. Please migrate to useQuota from QuotaContext.',
      'Component using deprecated hook:', new Error().stack?.split('\n')[2]
    )
  }

  // Use the centralized quota context
  const quota = useQuota()

  // Return compatibility interface
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

export default useQuotaMonitor