'use client'

import React, { useEffect, useState } from 'react'
import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'

interface BudgetCardProps {
  workspaceId: string
}

export default function BudgetCard({ workspaceId }: BudgetCardProps) {
  const { quotaStatus, isLoading, error } = useQuotaMonitor({
    workspaceId,
    enableWebSocket: false, // Disable WebSocket to prevent connection issues
    showNotifications: false,
    autoRefresh: true, // Enable auto-refresh with controlled interval
    refreshInterval: 30000, // Refresh every 30 seconds
  })
  
  // Calculate time until resets
  const [timeUntilResets, setTimeUntilResets] = useState({ daily: '', minute: '' })
  
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date()
      
      // Daily reset at midnight
      const tomorrow = new Date(now)
      tomorrow.setDate(tomorrow.getDate() + 1)
      tomorrow.setHours(0, 0, 0, 0)
      const dailyMs = tomorrow.getTime() - now.getTime()
      const dailyHours = Math.floor(dailyMs / (1000 * 60 * 60))
      const dailyMinutes = Math.floor((dailyMs % (1000 * 60 * 60)) / (1000 * 60))
      
      // Minute reset
      const secondsLeft = 60 - now.getSeconds()
      
      setTimeUntilResets({
        daily: `${dailyHours}h ${dailyMinutes}m`,
        minute: `${secondsLeft}s`
      })
    }
    
    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [])

  // Get status badge styling (for the status pill only)
  const getStatusBadgeStyling = () => {
    switch (quotaStatus.status) {
      case 'normal':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'rate_limited':
        return 'bg-orange-100 text-orange-800'
      case 'quota_exceeded':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const statusBadgeStyling = getStatusBadgeStyling()
  const stats = quotaStatus.rawData || {}
  
  const requestsPerMinute = stats.requests_per_minute || {}
  const requestsPerDay = stats.requests_per_day || {}
  
  const rpmCurrent = requestsPerMinute.current || 0
  const rpmLimit = requestsPerMinute.limit || 500
  const rpmPercentage = requestsPerMinute.percentage || 0
  
  const rpdCurrent = requestsPerDay.current || 0
  const rpdLimit = requestsPerDay.limit || 10000
  const rpdPercentage = requestsPerDay.percentage || 0

  if (isLoading) {
    return (
      <div className="p-3 border border-gray-200 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-600"></div>
          <span className="text-sm text-gray-600">Loading budget information...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-3 border border-gray-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <span className="text-red-500">⚠️</span>
          <span className="text-sm text-red-600">Unable to load budget data</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">💰</span>
          <h3 className="font-medium text-gray-900">Budget & Usage</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${statusBadgeStyling}`}>
          {quotaStatus.status.replace('_', ' ')}
        </span>
      </div>

      {/* Today's Usage */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-600">Today's Usage</span>
          <span className="text-gray-900 font-medium">
            {rpdCurrent.toLocaleString()} / {rpdLimit.toLocaleString()}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all duration-300 ${
              rpdPercentage > 80 ? 'bg-red-500' : 
              rpdPercentage > 50 ? 'bg-yellow-500' : 
              'bg-green-500'
            }`}
            style={{ width: `${Math.min(rpdPercentage, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {rpdPercentage.toFixed(1)}% used • Resets in {timeUntilResets.daily}
        </div>
      </div>

      {/* Current Minute Rate */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-600">Current Minute</span>
          <span className="text-gray-900 font-medium">
            {rpmCurrent} / {rpmLimit}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all duration-300 ${
              rpmPercentage > 80 ? 'bg-red-500' : 
              rpmPercentage > 50 ? 'bg-yellow-500' : 
              'bg-green-500'
            }`}
            style={{ width: `${Math.min(rpmPercentage, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {rpmPercentage.toFixed(1)}% used • Resets in {timeUntilResets.minute}
        </div>
      </div>

      {/* Status Message */}
      {quotaStatus.message && (
        <div className="text-xs text-gray-600 mt-2 pt-2 border-t border-gray-200">
          {quotaStatus.message}
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-gray-200">
        <div>
          <div className="text-xs text-gray-500">Remaining Today</div>
          <div className="text-sm font-medium text-gray-900">
            {(rpdLimit - rpdCurrent).toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Available Now</div>
          <div className="text-sm font-medium text-gray-900">
            {rpmLimit - rpmCurrent}
          </div>
        </div>
      </div>

      {/* Live indicator */}
      <div className="flex items-center justify-center mt-3 pt-2 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500">Live monitoring</span>
        </div>
      </div>
    </div>
  )
}