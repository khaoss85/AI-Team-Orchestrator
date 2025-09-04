'use client'

import React, { useEffect, useState } from 'react'
import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'

interface BudgetUsageChatProps {
  workspaceId: string
}

export default function BudgetUsageChat({ workspaceId }: BudgetUsageChatProps) {
  const { quotaStatus, isLoading, error } = useQuotaMonitor({
    workspaceId,
    enableWebSocket: true,
    showNotifications: false, // We handle display ourselves
    autoRefresh: true,
    refreshInterval: 10000, // Refresh every 10 seconds
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
      
      // Minute reset (every 60 seconds)
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

  // Get status emoji and color
  const getStatusDisplay = () => {
    switch (quotaStatus.status) {
      case 'normal':
        return { emoji: '🟢', text: 'Normal', color: 'text-green-600', bg: 'bg-green-50' }
      case 'warning':
        return { emoji: '🟡', text: 'Warning', color: 'text-yellow-600', bg: 'bg-yellow-50' }
      case 'rate_limited':
        return { emoji: '🟠', text: 'Rate Limited', color: 'text-orange-600', bg: 'bg-orange-50' }
      case 'quota_exceeded':
        return { emoji: '🔴', text: 'Quota Exceeded', color: 'text-red-600', bg: 'bg-red-50' }
      case 'degraded':
        return { emoji: '⚠️', text: 'Degraded', color: 'text-gray-600', bg: 'bg-gray-50' }
      default:
        return { emoji: '❓', text: 'Unknown', color: 'text-gray-500', bg: 'bg-gray-50' }
    }
  }

  const statusDisplay = getStatusDisplay()
  const stats = quotaStatus.statistics || quotaStatus.rawData || {}
  
  // Extract usage data from different possible structures
  const requestsPerMinute = stats.requests_per_minute || {}
  const requestsPerDay = stats.requests_per_day || {}
  
  const rpmCurrent = requestsPerMinute.current || 0
  const rpmLimit = requestsPerMinute.limit || 500
  const rpmPercentage = requestsPerMinute.percentage || 0
  
  const rpdCurrent = requestsPerDay.current || 0
  const rpdLimit = requestsPerDay.limit || 10000
  const rpdPercentage = requestsPerDay.percentage || 0
  
  const remainingToday = rpdLimit - rpdCurrent

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mx-auto mb-2"></div>
          <div className="text-sm">Loading budget information...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-red-600">
          <div className="text-2xl mb-2">❌</div>
          <div className="text-sm">Failed to load budget data</div>
          <div className="text-xs text-gray-500 mt-1">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div 
      className="p-4 sm:p-6 space-y-4 sm:space-y-6 max-w-4xl mx-auto" 
      role="main" 
      aria-label="Budget and Usage Monitor"
    >
      {/* Welcome Message */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
        <div className="flex items-center space-x-3 mb-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <span className="text-lg">💰</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Budget & Usage Monitor
            </h2>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          Real-time tracking of your OpenAI API usage and quotas. All values update automatically.
        </p>
      </div>

      {/* Status Card */}
      <div className={`rounded-xl p-4 sm:p-6 ${statusDisplay.bg} border border-opacity-50`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{statusDisplay.emoji}</span>
            <div>
              <div className={`font-semibold ${statusDisplay.color}`}>
                Status: {statusDisplay.text}
              </div>
              <div className="text-sm text-gray-600">{quotaStatus.message}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Last updated</div>
            <div className="text-xs font-medium text-gray-700">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      <div className="space-y-4">
        {/* Daily Usage */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-green-50 rounded-lg">
                <span className="text-lg">📊</span>
              </div>
              <span className="font-medium text-gray-900">Today's Usage</span>
            </div>
            <span className="text-sm text-gray-500">
              Resets in {timeUntilResets.daily}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Requests Used</span>
              <span className="font-medium">
                {rpdCurrent.toLocaleString()} / {rpdLimit.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={rpdPercentage} aria-valuemin={0} aria-valuemax={100} aria-label={`Daily usage: ${rpdPercentage.toFixed(1)}%`}>
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  rpdPercentage > 80 ? 'bg-red-500' : 
                  rpdPercentage > 50 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(rpdPercentage, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500">
              {rpdPercentage.toFixed(1)}% used • {remainingToday.toLocaleString()} remaining
            </div>
          </div>
        </div>

        {/* Minute Rate */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-orange-50 rounded-lg">
                <span className="text-lg">⚡</span>
              </div>
              <span className="font-medium text-gray-900">Current Minute</span>
            </div>
            <span className="text-sm text-gray-500">
              Resets in {timeUntilResets.minute}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Requests Used</span>
              <span className="font-medium">
                {rpmCurrent} / {rpmLimit}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={rpmPercentage} aria-valuemin={0} aria-valuemax={100} aria-label={`Current minute usage: ${rpmPercentage.toFixed(1)}%`}>
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  rpmPercentage > 80 ? 'bg-red-500' : 
                  rpmPercentage > 50 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(rpmPercentage, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500">
              {rpmPercentage.toFixed(1)}% used • {rpmLimit - rpmCurrent} remaining
            </div>
          </div>
        </div>
      </div>

      {/* Remaining Budget */}
      <div className="bg-blue-50 rounded-xl p-4 sm:p-6 border border-blue-200">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-1 bg-blue-100 rounded-lg">
            <span className="text-lg">💳</span>
          </div>
          <span className="font-medium text-blue-800">Remaining Budget</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-blue-600">Today</div>
            <div className="text-xl font-semibold text-blue-800">
              {remainingToday.toLocaleString()}
            </div>
            <div className="text-xs text-blue-600">requests available</div>
          </div>
          <div>
            <div className="text-blue-600">This Minute</div>
            <div className="text-xl font-semibold text-blue-800">
              {rpmLimit - rpmCurrent}
            </div>
            <div className="text-xs text-blue-600">requests available</div>
          </div>
        </div>
      </div>

      {/* Suggested Actions */}
      {quotaStatus.suggestedActions && quotaStatus.suggestedActions.length > 0 && (
        <div className="bg-yellow-50 rounded-xl p-4 sm:p-6 border border-yellow-200">
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-1 bg-yellow-100 rounded-lg">
              <span className="text-lg">💡</span>
            </div>
            <span className="font-medium text-yellow-800">Suggested Actions</span>
          </div>
          <ul className="space-y-1">
            {quotaStatus.suggestedActions.map((action, index) => (
              <li key={index} className="text-sm text-yellow-700 flex items-start">
                <span className="mr-2">•</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Live Updates Indicator */}
      <div className="flex items-center justify-center space-x-3 py-3">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-sm text-gray-600 font-medium">Live updates every 10 seconds</span>
        </div>
      </div>
    </div>
  )
}