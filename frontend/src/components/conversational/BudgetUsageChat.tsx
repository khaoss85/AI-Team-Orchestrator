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
  const enhanced = stats.enhanced_tracking || {}
  
  // Extract usage data from different possible structures
  const requestsPerMinute = stats.requests_per_minute || {}
  const requestsPerDay = stats.requests_per_day || {}
  const tokensPerMinute = stats.tokens_per_minute || {}
  
  const rpmCurrent = requestsPerMinute.current || 0
  const rpmLimit = requestsPerMinute.limit || 500
  const rpmPercentage = requestsPerMinute.percentage || 0
  
  const rpdCurrent = requestsPerDay.current || 0
  const rpdLimit = requestsPerDay.limit || 10000
  const rpdPercentage = requestsPerDay.percentage || 0
  
  const tpmCurrent = tokensPerMinute.current || 0
  const tpmLimit = tokensPerMinute.limit || 150000
  const tpmPercentage = tokensPerMinute.percentage || 0
  
  const remainingToday = rpdLimit - rpdCurrent
  const remainingTokens = tpmLimit - tpmCurrent
  
  // Enhanced tracking data
  const modelsBreakdown = enhanced.models_breakdown || {}
  const apiMethodsBreakdown = enhanced.api_methods_breakdown || {}
  const recentActivity = enhanced.recent_activity || []
  
  // Cost intelligence alerts
  const [costAlerts, setCostAlerts] = useState([])
  const [showAlerts, setShowAlerts] = useState(true)
  
  // Listen for cost intelligence alerts via WebSocket
  useEffect(() => {
    if (quotaStatus.ws) {
      const handleMessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'cost_intelligence_alerts') {
            setCostAlerts(prev => [...data.alerts, ...prev.slice(0, 4)]) // Keep last 5 alerts
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }
      
      quotaStatus.ws.addEventListener('message', handleMessage)
      return () => quotaStatus.ws.removeEventListener('message', handleMessage)
    }
  }, [quotaStatus.ws])
  
  // Alert severity colors and icons
  const getAlertStyle = (severity) => {
    switch (severity) {
      case 'critical': return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', icon: '🚨' }
      case 'high': return { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', icon: '⚠️' }
      case 'medium': return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', icon: '💡' }
      case 'low': return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', icon: '📊' }
      default: return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800', icon: 'ℹ️' }
    }
  }

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

      {/* Emergency Banner - Quota Exhausted */}
      {quotaStatus.status === 'quota_exceeded' && (
        <div className="bg-red-600 rounded-xl p-4 sm:p-6 border-2 border-red-700 animate-pulse">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🚨</span>
            <div className="flex-1">
              <div className="font-bold text-white text-lg">
                CRITICAL: OpenAI Quota Exhausted
              </div>
              <div className="text-red-100 text-sm mt-1">
                AI operations are currently unavailable. Please check your OpenAI billing or upgrade your plan.
              </div>
              <div className="mt-2">
                <a 
                  href="https://platform.openai.com/account/billing" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-3 py-1 bg-white text-red-600 rounded-md text-sm font-medium hover:bg-red-50"
                >
                  Check OpenAI Billing →
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

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

        {/* Minute Rate - Requests */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-orange-50 rounded-lg">
                <span className="text-lg">⚡</span>
              </div>
              <span className="font-medium text-gray-900">API Requests/Minute</span>
            </div>
            <span className="text-sm text-gray-500">
              Resets in {timeUntilResets.minute}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">API Calls Made</span>
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
              {rpmPercentage.toFixed(1)}% used • {rpmLimit - rpmCurrent} calls remaining
            </div>
          </div>
        </div>

        {/* Minute Rate - Tokens */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-purple-50 rounded-lg">
                <span className="text-lg">🔤</span>
              </div>
              <span className="font-medium text-gray-900">Tokens/Minute</span>
            </div>
            <span className="text-sm text-gray-500">
              Resets in {timeUntilResets.minute}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Tokens Consumed</span>
              <span className="font-medium">
                {tpmCurrent.toLocaleString()} / {tpmLimit.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={tpmPercentage} aria-valuemin={0} aria-valuemax={100} aria-label={`Token usage: ${tpmPercentage.toFixed(1)}%`}>
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  tpmPercentage > 80 ? 'bg-red-500' : 
                  tpmPercentage > 50 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(tpmPercentage, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500">
              {tpmPercentage.toFixed(1)}% used • {remainingTokens.toLocaleString()} tokens remaining
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

      {/* Model Usage Breakdown */}
      {Object.keys(modelsBreakdown).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-1 bg-indigo-50 rounded-lg">
              <span className="text-lg">🤖</span>
            </div>
            <span className="font-medium text-gray-900">Model Usage Breakdown</span>
          </div>
          <div className="space-y-3">
            {Object.entries(modelsBreakdown).map(([model, data]: [string, any]) => {
              const modelData = data || { request_count: 0, tokens_used: 0 }
              const modelPercentage = rpdCurrent > 0 ? (modelData.request_count / rpdCurrent) * 100 : 0
              
              return (
                <div key={model} className="border-l-4 border-indigo-500 pl-3 py-2">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <div className="font-medium text-gray-800">{model}</div>
                      <div className="text-xs text-gray-500">
                        {modelData.request_count} requests • {modelData.tokens_used.toLocaleString()} tokens
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-indigo-600">
                        {modelPercentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div
                      className="h-1.5 rounded-full bg-indigo-500 transition-all duration-300"
                      style={{ width: `${Math.min(modelPercentage, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* API Method Breakdown */}
      {Object.keys(apiMethodsBreakdown).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-1 bg-teal-50 rounded-lg">
              <span className="text-lg">⚙️</span>
            </div>
            <span className="font-medium text-gray-900">API Method Usage</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(apiMethodsBreakdown).slice(0, 6).map(([method, data]: [string, any]) => {
              const methodData = data || { request_count: 0, error_count: 0 }
              const errorRate = methodData.request_count > 0 
                ? (methodData.error_count / methodData.request_count) * 100 
                : 0
              
              return (
                <div key={method} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 truncate">{method}</div>
                  <div className="text-lg font-semibold text-gray-800">
                    {methodData.request_count}
                  </div>
                  {methodData.error_count > 0 && (
                    <div className="text-xs text-red-600">
                      {methodData.error_count} errors ({errorRate.toFixed(0)}%)
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          {Object.keys(apiMethodsBreakdown).length > 6 && (
            <div className="text-xs text-gray-500 mt-2 text-center">
              +{Object.keys(apiMethodsBreakdown).length - 6} more methods
            </div>
          )}
        </div>
      )}

      {/* Recent Activity */}
      {recentActivity.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-1 bg-amber-50 rounded-lg">
              <span className="text-lg">📜</span>
            </div>
            <span className="font-medium text-gray-900">Recent Activity</span>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {recentActivity.slice(0, 5).map((activity, index) => {
              const time = new Date(activity.timestamp).toLocaleTimeString()
              return (
                <div key={index} className="flex items-start space-x-2 text-xs">
                  <span className={`mt-0.5 ${activity.success ? 'text-green-500' : 'text-red-500'}`}>
                    {activity.success ? '✓' : '✗'}
                  </span>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">{activity.model}</span>
                      <span className="text-gray-500">{time}</span>
                    </div>
                    <div className="text-gray-600">
                      {activity.api_method} • {activity.tokens_used} tokens
                    </div>
                    {activity.error && (
                      <div className="text-red-600 truncate">{activity.error}</div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* AI Cost Intelligence Alerts */}
      {showAlerts && costAlerts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-purple-50 rounded-lg">
                <span className="text-lg">🧠</span>
              </div>
              <span className="font-medium text-gray-900">AI Cost Optimization</span>
            </div>
            <button 
              onClick={() => setShowAlerts(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Dismiss All
            </button>
          </div>
          
          {costAlerts.slice(0, 3).map((alert) => {
            const alertStyle = getAlertStyle(alert.severity)
            return (
              <div key={alert.id} className={`rounded-lg p-4 border ${alertStyle.bg} ${alertStyle.border}`}>
                <div className="flex items-start space-x-3">
                  <span className="text-xl">{alertStyle.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className={`text-sm font-medium ${alertStyle.text}`}>
                        {alert.title}
                      </h4>
                      <span className="text-xs bg-white px-2 py-1 rounded-full font-medium">
                        ${alert.potential_savings?.toFixed(3)}/day
                      </span>
                    </div>
                    <p className={`text-xs ${alertStyle.text} opacity-90 mb-2`}>
                      {alert.description}
                    </p>
                    <div className="bg-white bg-opacity-50 rounded-md p-2 text-xs">
                      <span className="font-medium">💡 Recommendation:</span>
                      <span className="ml-1">{alert.recommendation}</span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs opacity-75">
                      <span>Confidence: {Math.round(alert.confidence * 100)}%</span>
                      <span>{new Date(alert.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
          
          {costAlerts.length > 3 && (
            <div className="text-center">
              <button 
                onClick={() => {/* Could expand to show all alerts */}}
                className="text-sm text-purple-600 hover:text-purple-800 font-medium"
              >
                View {costAlerts.length - 3} more optimization opportunities →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Model Usage Breakdown */}
      {Object.keys(modelsBreakdown).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-1 bg-indigo-50 rounded-lg">
              <span className="text-lg">🤖</span>
            </div>
            <span className="font-medium text-gray-900">Model Usage Breakdown</span>
          </div>
          
          <div className="space-y-3">
            {Object.entries(modelsBreakdown).map(([model, data]) => {
              const usage = data as { request_count: number; tokens_used: number }
              const totalRequests = Object.values(modelsBreakdown).reduce((sum, d) => sum + (d as any).request_count, 0)
              const percentage = totalRequests > 0 ? (usage.request_count / totalRequests) * 100 : 0
              
              return (
                <div key={model} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{model}</span>
                      <div className="text-xs text-gray-500">
                        {usage.request_count} calls • {usage.tokens_used.toLocaleString()} tokens
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          model.includes('gpt-4') ? 'bg-red-500' : 
                          model.includes('gpt-3.5') ? 'bg-blue-500' : 
                          'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {percentage.toFixed(1)}% of total requests
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {recentActivity.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-1 bg-green-50 rounded-lg">
              <span className="text-lg">⚡</span>
            </div>
            <span className="font-medium text-gray-900">Recent API Activity</span>
          </div>
          
          <div className="space-y-2">
            {recentActivity.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                <div className="flex items-center space-x-3">
                  <span className={`text-sm ${activity.success ? 'text-green-600' : 'text-red-600'}`}>
                    {activity.success ? '✅' : '❌'}
                  </span>
                  <div>
                    <span className="text-sm font-medium text-gray-700">{activity.model}</span>
                    <span className="text-xs text-gray-500 ml-2">{activity.api_method}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">{activity.tokens_used} tokens</div>
                  <div className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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