'use client'

import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'
import { useEffect, useState } from 'react'

// Progress bar component with minimal design
const ProgressBar = ({ value, max, label, color = 'blue' }: { 
  value: number, 
  max: number, 
  label: string, 
  color?: 'blue' | 'yellow' | 'red' | 'green' 
}) => {
  const percentage = max > 0 ? (value / max) * 100 : 0
  const colorClass = {
    green: 'bg-green-500',
    blue: 'bg-blue-500', 
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  }[color]
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600">
        <span>{label}</span>
        <span>{value.toLocaleString()}/{max.toLocaleString()} ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`${colorClass} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

// Status badge component
const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig = {
    normal: { color: 'bg-green-100 text-green-800', emoji: '✅' },
    warning: { color: 'bg-yellow-100 text-yellow-800', emoji: '⚠️' },
    rate_limited: { color: 'bg-orange-100 text-orange-800', emoji: '🚦' },
    quota_exceeded: { color: 'bg-red-100 text-red-800', emoji: '🚫' },
    degraded: { color: 'bg-gray-100 text-gray-800', emoji: '⚪' }
  }
  
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.normal
  
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
      <span className="mr-1">{config.emoji}</span>
      {status.replace('_', ' ')}
    </span>
  )
}

export default function TestQuotaPage() {
  const [testResult, setTestResult] = useState<string>('Testing quota monitoring...')
  const { quotaStatus, isConnected, error, refresh, isLoading } = useQuotaMonitor({
    enableWebSocket: true,
    showNotifications: true,
    autoRefresh: true,
    refreshInterval: 10000 // Refresh every 10 seconds for testing
  })

  useEffect(() => {
    // Test results
    const results = []
    
    // Check WebSocket connection
    if (isConnected) {
      results.push('✅ WebSocket: Connected')
    } else {
      results.push('❌ WebSocket: Disconnected')
    }
    
    // Check API connectivity
    if (quotaStatus.status) {
      results.push(`✅ API Status: ${quotaStatus.status}`)
    } else {
      results.push('❌ API Status: Not available')
    }
    
    // Check for errors
    if (error) {
      results.push(`❌ Error: ${error}`)
    }
    
    // Check statistics
    if (quotaStatus.statistics) {
      results.push(`✅ Statistics: ${quotaStatus.statistics.requestsToday || 0} requests today`)
    }
    
    // Check raw data availability
    if (quotaStatus.rawData) {
      results.push(`✅ Detailed Data: Available`)
    }
    
    setTestResult(results.join('\n'))
  }, [isConnected, quotaStatus, error])

  const rawData = quotaStatus.rawData || {}

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">OpenAI Quota Monitor</h1>
          <p className="text-gray-600">
            Real-time monitoring of OpenAI API usage and quota limits with comprehensive consumption details
          </p>
        </div>

        {/* Status Overview */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="mb-3">
                <StatusBadge status={quotaStatus.status} />
              </div>
              <p className="text-sm text-gray-600 mb-2">{quotaStatus.message}</p>
              <p className="text-sm">
                <span className="font-medium">Can Make Requests: </span>
                {quotaStatus.canMakeRequest ? (
                  <span className="text-green-600">✅ Yes</span>
                ) : (
                  <span className="text-red-600">❌ No</span>
                )}
              </p>
              {quotaStatus.waitSeconds && (
                <p className="text-sm text-orange-600 mt-1">
                  Wait {quotaStatus.waitSeconds} seconds before next request
                </p>
              )}
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Connection Status</h3>
              <pre className="bg-gray-50 p-3 rounded text-xs text-gray-600 font-mono">
                {testResult}
              </pre>
            </div>
          </div>
        </div>

        {/* Quota Consumption Details */}
        {rawData.requests_per_minute && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Quota Consumption</h2>
            
            <div className="space-y-6">
              {/* Requests per Minute */}
              <div>
                <ProgressBar
                  value={rawData.requests_per_minute.current}
                  max={rawData.requests_per_minute.limit}
                  label="Requests per Minute"
                  color={rawData.requests_per_minute.percentage > 90 ? 'red' : 
                         rawData.requests_per_minute.percentage > 70 ? 'yellow' : 'green'}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Rate limit resets every minute
                </p>
              </div>

              {/* Requests per Day */}
              <div>
                <ProgressBar
                  value={rawData.requests_per_day.current}
                  max={rawData.requests_per_day.limit}
                  label="Requests per Day"
                  color={rawData.requests_per_day.percentage > 90 ? 'red' :
                         rawData.requests_per_day.percentage > 70 ? 'yellow' : 'green'}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Daily quota resets at midnight UTC
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Statistics */}
        {(quotaStatus.statistics || rawData.errors) && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Statistics</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quotaStatus.statistics && (
                <>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Current Minute</h3>
                    <p className="text-2xl font-bold text-gray-900">
                      {quotaStatus.statistics.requestsThisMinute}
                    </p>
                    <p className="text-xs text-gray-500">
                      {quotaStatus.statistics.minuteUsagePercent?.toFixed(1)}% used
                    </p>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Today Total</h3>
                    <p className="text-2xl font-bold text-gray-900">
                      {quotaStatus.statistics.requestsToday.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">
                      {quotaStatus.statistics.dailyUsagePercent?.toFixed(1)}% used
                    </p>
                  </div>
                </>
              )}

              {rawData.errors && (
                <>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Error Count</h3>
                    <p className="text-2xl font-bold text-gray-900">
                      {rawData.errors.count}
                    </p>
                    <p className="text-xs text-gray-500">API errors</p>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Last Updated</h3>
                    <p className="text-sm font-mono text-gray-900">
                      {rawData.last_updated ? 
                        new Date(rawData.last_updated).toLocaleTimeString() : 
                        'Never'
                      }
                    </p>
                    <p className="text-xs text-gray-500">Live updates</p>
                  </div>
                </>
              )}
            </div>

            {rawData.errors?.last_error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="text-sm font-medium text-red-800 mb-1">Last Error</h4>
                <p className="text-sm text-red-600 font-mono">{rawData.errors.last_error}</p>
              </div>
            )}
          </div>
        )}

        {/* Remaining Quota */}
        {rawData.requests_per_minute && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Remaining Quota</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Per Minute Remaining</h3>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold text-blue-600">
                    {Math.max(0, rawData.requests_per_minute.limit - rawData.requests_per_minute.current).toLocaleString()}
                  </span>
                  <span className="text-sm text-gray-500">requests</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Resets in {60 - new Date().getSeconds()} seconds
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Per Day Remaining</h3>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold text-green-600">
                    {Math.max(0, rawData.requests_per_day.limit - rawData.requests_per_day.current).toLocaleString()}
                  </span>
                  <span className="text-sm text-gray-500">requests</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Resets at midnight UTC
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center space-x-4 mb-8">
          <button 
            onClick={() => refresh()}
            disabled={isLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Refreshing...' : 'Refresh Status'}
          </button>
          
          {error && (
            <div className="flex-1 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">Error: {error}</p>
            </div>
          )}
        </div>

        {/* System Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">System Information</h3>
          <div className="text-sm text-blue-700 space-y-1">
            <p>API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
            <p>WebSocket URL: {process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}</p>
            <p>Auto-refresh: Every 10 seconds</p>
            <p>Real-time updates: {isConnected ? 'Enabled' : 'Disabled'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}