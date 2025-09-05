'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/utils/api'
import { 
  UsageData, 
  BudgetStatus, 
  CostIntelligence, 
  ModelComparison
} from '@/types/usage'

interface BudgetUsageChatEnhancedProps {
  workspaceId: string
}

export default function BudgetUsageChatEnhanced({ workspaceId }: BudgetUsageChatEnhancedProps) {
  const [monthlyUsage, setMonthlyUsage] = useState<UsageData | null>(null)
  const [todayUsage, setTodayUsage] = useState<UsageData | null>(null)
  const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null)
  const [costIntelligence, setCostIntelligence] = useState<CostIntelligence | null>(null)
  const [modelComparison, setModelComparison] = useState<ModelComparison | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAlerts, setShowAlerts] = useState(true)
  const [selectedTab, setSelectedTab] = useState<'overview' | 'models' | 'alerts'>('overview')

  // Time until end of month
  const [timeUntilMonthEnd, setTimeUntilMonthEnd] = useState('')

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date()
      const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      const msRemaining = endOfMonth.getTime() - now.getTime()
      const daysRemaining = Math.floor(msRemaining / (1000 * 60 * 60 * 24))
      const hoursRemaining = Math.floor((msRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
      
      setTimeUntilMonthEnd(`${daysRemaining}d ${hoursRemaining}h`)
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [])

  // Load all usage data
  useEffect(() => {
    console.log('💰 BudgetUsageChatEnhanced: Initializing with workspaceId:', workspaceId)
    loadUsageData()
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      console.log('💰 BudgetUsageChatEnhanced: Auto-refreshing data (30s interval)')
      loadUsageData()
    }, 30000)
    return () => {
      console.log('💰 BudgetUsageChatEnhanced: Cleaning up interval')
      clearInterval(interval)
    }
  }, [workspaceId])

  const loadUsageData = async () => {
    try {
      console.log('💰 BudgetUsageChatEnhanced: Loading usage data...')
      setIsLoading(true)
      setError(null)

      const [monthly, today, budget, intelligence, models] = await Promise.all([
        api.usage.getCurrentMonth().catch((e) => {
          console.warn('Failed to load monthly usage:', e)
          return null
        }),
        api.usage.getToday().catch((e) => {
          console.warn('Failed to load today usage:', e)
          return null
        }),
        api.usage.getBudgetStatus().catch((e) => {
          console.warn('Failed to load budget status:', e)
          return null
        }),
        api.usage.getCostIntelligence(workspaceId).catch((e) => {
          console.warn('Failed to load cost intelligence:', e)
          return null
        }),
        api.usage.getModelComparison().catch((e) => {
          console.warn('Failed to load model comparison:', e)
          return null
        }),
      ])

      console.log('💰 BudgetUsageChatEnhanced: Data loaded:', {
        hasMonthly: !!monthly,
        hasToday: !!today,
        hasBudget: !!budget,
        budgetStatus: budget?.status,
        budgetAlertLevel: budget?.budget_alert_level,
        budgetUsedPercent: budget?.budget_used_percent
      })

      setMonthlyUsage(monthly)
      setTodayUsage(today)
      setBudgetStatus(budget)
      setCostIntelligence(intelligence)
      setModelComparison(models)
    } catch (err) {
      console.error('💰 BudgetUsageChatEnhanced: Error loading usage data:', err)
      setError('Failed to load usage data')
    } finally {
      setIsLoading(false)
    }
  }

  // Get budget status display with null-safe checks and fallback logic
  const getBudgetDisplay = () => {
    if (!budgetStatus) return { emoji: '❓', text: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50' }
    
    // Check both budget_alert_level and status fields for compatibility
    const alertLevel = budgetStatus.budget_alert_level || budgetStatus.status || 'unknown'
    
    // Also determine status from budget usage percentage if alert level is missing
    let derivedAlertLevel = alertLevel
    if (!budgetStatus.budget_alert_level && budgetStatus.status === 'normal') {
      const usagePercent = budgetStatus.budget_used_percentage ?? budgetStatus.budget_used_percent ?? 0
      if (usagePercent >= 100) {
        derivedAlertLevel = 'critical'
      } else if (usagePercent >= 80) {
        derivedAlertLevel = 'warning'
      } else {
        derivedAlertLevel = 'normal'
      }
    }
    
    switch (derivedAlertLevel) {
      case 'normal':
        return { emoji: '✅', text: 'WITHIN BUDGET', color: 'text-green-600', bg: 'bg-green-50' }
      case 'warning':
        return { emoji: '⚠️', text: 'APPROACHING LIMIT', color: 'text-yellow-600', bg: 'bg-yellow-50' }
      case 'critical':
        return { emoji: '🚨', text: 'OVER BUDGET', color: 'text-red-600', bg: 'bg-red-50' }
      default:
        // If we have budget data but unknown status, show within budget if usage is low
        const usage = budgetStatus.budget_used_percentage ?? budgetStatus.budget_used_percent ?? 0
        if (usage < 80) {
          return { emoji: '✅', text: 'WITHIN BUDGET', color: 'text-green-600', bg: 'bg-green-50' }
        }
        return { emoji: '❓', text: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50' }
    }
  }

  // Get alert style based on severity
  const getAlertStyle = (severity: string) => {
    switch (severity) {
      case 'critical': 
        return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', icon: '🚨' }
      case 'high': 
        return { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', icon: '⚠️' }
      case 'medium': 
        return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', icon: '💡' }
      case 'low': 
        return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', icon: '📊' }
      default: 
        return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800', icon: 'ℹ️' }
    }
  }

  // Format currency with null-safe check
  const formatCurrency = (amount: number | undefined | null) => {
    const safeAmount = amount ?? 0
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(safeAmount)
  }

  const budgetDisplay = getBudgetDisplay()

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

  if (error && !budgetStatus) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-red-600">
          <div className="text-2xl mb-2">❌</div>
          <div className="text-sm">Failed to load budget data</div>
          <div className="text-xs text-gray-500 mt-1">{error}</div>
          <button 
            onClick={loadUsageData}
            className="mt-3 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
        <div className="flex items-center space-x-3 mb-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <span className="text-lg">💰</span>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              Budget & Usage
            </h2>
            <p className="text-sm text-gray-600">
              Real-time OpenAI cost tracking and optimization
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Month ends in</div>
            <div className="text-sm font-medium text-gray-700">{timeUntilMonthEnd}</div>
          </div>
        </div>
      </div>

      {/* Budget Status Card */}
      {budgetStatus && (
        <div className={`rounded-xl p-4 sm:p-6 ${budgetDisplay.bg} border ${budgetDisplay.color} border-opacity-20`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{budgetDisplay.emoji}</span>
              <div>
                <div className={`font-semibold ${budgetDisplay.color}`}>
                  {budgetDisplay.text}
                </div>
                <div className="text-sm text-gray-600">
                  Monthly Budget: {formatCurrency(budgetStatus.monthly_budget)}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(budgetStatus?.current_spend)}
              </div>
              <div className="text-sm text-gray-600">
                {/* Handle both budget_used_percentage and budget_used_percent field names */}
                {((budgetStatus?.budget_used_percentage ?? budgetStatus?.budget_used_percent ?? 0) as number).toFixed(1)}% used
              </div>
            </div>
          </div>

          {/* Budget Progress Bar with null-safe checks */}
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  ((budgetStatus?.budget_used_percentage ?? budgetStatus?.budget_used_percent ?? 0) as number) > 90 ? 'bg-red-500' : 
                  ((budgetStatus?.budget_used_percentage ?? budgetStatus?.budget_used_percent ?? 0) as number) > 75 ? 'bg-yellow-500' : 
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(((budgetStatus?.budget_used_percentage ?? budgetStatus?.budget_used_percent ?? 0) as number), 100)}%` }}
              />
            </div>
          </div>

          {/* Budget Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-600">Daily Average</div>
              <div className="font-semibold text-gray-900">
                {formatCurrency(budgetStatus.daily_average)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Projected</div>
              <div className="font-semibold text-gray-900">
                {formatCurrency(budgetStatus.projected_monthly_spend ?? budgetStatus.projected_monthly ?? 0)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Remaining</div>
              <div className="font-semibold text-gray-900">
                {formatCurrency(budgetStatus.monthly_budget - budgetStatus.current_spend)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Days Left</div>
              <div className="font-semibold text-gray-900">
                {budgetStatus.days_remaining}
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {budgetStatus.recommendations && budgetStatus.recommendations.length > 0 && (
            <div className="mt-4 p-3 bg-white bg-opacity-50 rounded-lg">
              <div className="text-sm font-medium text-gray-700 mb-2">📋 Recommendations:</div>
              <ul className="space-y-1">
                {budgetStatus.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start">
                    <span className="mr-2">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setSelectedTab('overview')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            selectedTab === 'overview' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setSelectedTab('models')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            selectedTab === 'models' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          Model Costs
        </button>
        <button
          onClick={() => setSelectedTab('alerts')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors relative ${
            selectedTab === 'alerts' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          AI Insights
          {costIntelligence && (costIntelligence?.total_alerts ?? 0) > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
              {costIntelligence?.total_alerts ?? 0}
            </span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {/* Overview Tab */}
        {selectedTab === 'overview' && (
          <>
            {/* Today's Usage */}
            {todayUsage && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-1 bg-green-50 rounded-lg">
                      <span className="text-lg">📊</span>
                    </div>
                    <span className="font-medium text-gray-900">Today's Usage</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {formatCurrency(todayUsage?.total_cost)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Requests</div>
                    <div className="font-semibold text-gray-900">
                      {(todayUsage?.total_requests ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Tokens</div>
                    <div className="font-semibold text-gray-900">
                      {(todayUsage?.total_tokens ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Avg Cost/Request</div>
                    <div className="font-semibold text-gray-900">
                      {formatCurrency((todayUsage?.total_cost ?? 0) / Math.max(todayUsage?.total_requests ?? 1, 1))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* This Month's Usage */}
            {monthlyUsage && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-1 bg-purple-50 rounded-lg">
                      <span className="text-lg">📈</span>
                    </div>
                    <span className="font-medium text-gray-900">This Month</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {formatCurrency(monthlyUsage?.total_cost)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Total Requests</div>
                    <div className="font-semibold text-gray-900">
                      {(monthlyUsage?.total_requests ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Total Tokens</div>
                    <div className="font-semibold text-gray-900">
                      {((monthlyUsage?.total_tokens ?? 0) / 1000000).toFixed(2)}M
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Models Used</div>
                    <div className="font-semibold text-gray-900">
                      {monthlyUsage.model_breakdown?.length || 0}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Models Tab */}
        {selectedTab === 'models' && (
          <>
            {/* Model Usage Breakdown */}
            {monthlyUsage && monthlyUsage.model_breakdown && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-1 bg-indigo-50 rounded-lg">
                    <span className="text-lg">🤖</span>
                  </div>
                  <span className="font-medium text-gray-900">Model Usage This Month</span>
                </div>
                <div className="space-y-3">
                  {monthlyUsage.model_breakdown.map((model) => {
                    const percentage = monthlyUsage.total_cost > 0 
                      ? (model.total_cost / monthlyUsage.total_cost) * 100 
                      : 0
                    
                    return (
                      <div key={model.model} className="border-l-4 border-indigo-500 pl-3 py-2">
                        <div className="flex justify-between items-start mb-1">
                          <div>
                            <div className="font-medium text-gray-800">{model.model}</div>
                            <div className="text-xs text-gray-500">
                              {model.request_count.toLocaleString()} requests • 
                              {' '}{((model.total_input_tokens + model.total_output_tokens) / 1000).toFixed(1)}k tokens
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold text-indigo-600">
                              {formatCurrency(model.total_cost)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {percentage.toFixed(1)}% of total
                            </div>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                          <div
                            className="h-1.5 rounded-full bg-indigo-500 transition-all duration-300"
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Model Comparison */}
            {modelComparison && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-1 bg-teal-50 rounded-lg">
                    <span className="text-lg">💰</span>
                  </div>
                  <span className="font-medium text-gray-900">Model Cost Comparison</span>
                </div>
                <div className="space-y-3">
                  {modelComparison.models.map((model) => (
                    <div key={model.model} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium text-gray-800">
                            {model.model}
                            {model.model === modelComparison.recommended_model && (
                              <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                                Recommended
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-600">
                            Efficiency Score: {model.efficiency_score.toFixed(1)}/10
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-gray-900">
                            {formatCurrency(model.projected_monthly)}
                          </div>
                          <div className="text-xs text-gray-500">per month</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-green-600 font-medium">Pros:</span>
                          <ul className="mt-1 space-y-0.5">
                            {model.pros.map((pro, idx) => (
                              <li key={idx} className="text-gray-600">• {pro}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <span className="text-red-600 font-medium">Cons:</span>
                          <ul className="mt-1 space-y-0.5">
                            {model.cons.map((con, idx) => (
                              <li key={idx} className="text-gray-600">• {con}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {modelComparison.estimated_savings > 0 && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="text-sm font-medium text-green-800">
                      💡 Potential Savings: {formatCurrency(modelComparison.estimated_savings)}/month
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* AI Insights Tab */}
        {selectedTab === 'alerts' && costIntelligence && (
          <div className="space-y-3">
            {(costIntelligence?.total_alerts ?? 0) > 0 ? (
              <>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-1 bg-purple-50 rounded-lg">
                      <span className="text-lg">🧠</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">AI Cost Optimization</span>
                      <div className="text-sm text-gray-600">
                        Potential savings: {formatCurrency(costIntelligence?.potential_monthly_savings)}/month
                      </div>
                    </div>
                  </div>
                  {showAlerts && (
                    <button 
                      onClick={() => setShowAlerts(false)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Dismiss All
                    </button>
                  )}
                </div>

                {showAlerts && (costIntelligence?.alerts ?? []).map((alert) => {
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
                              {formatCurrency(alert?.potential_savings)}/day
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
                            <span>Confidence: {Math.round((alert?.confidence ?? 0) * 100)}%</span>
                            <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </>
            ) : (
              <div className="bg-green-50 rounded-xl p-6 border border-green-200 text-center">
                <span className="text-2xl mb-2">✅</span>
                <div className="text-green-800 font-medium">No optimization alerts</div>
                <div className="text-sm text-green-600 mt-1">
                  Your usage patterns are already optimized!
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Live Updates Indicator */}
      <div className="flex items-center justify-center space-x-3 py-3">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-sm text-gray-600 font-medium">Live updates every 30 seconds</span>
        </div>
      </div>
    </div>
  )
}