'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/utils/api'
import BudgetUsageChatEnhanced from './BudgetUsageChatEnhanced'
import BudgetUsageChat from './BudgetUsageChat'

interface BudgetUsageChatV2Props {
  workspaceId: string
}

/**
 * Smart Budget Usage component that automatically switches between:
 * - Enhanced version: Uses real OpenAI Usage API data when available
 * - Legacy version: Falls back to quota tracking when Usage API is unavailable
 */
export default function BudgetUsageChatV2({ workspaceId }: BudgetUsageChatV2Props) {
  const [useEnhanced, setUseEnhanced] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    // Check if real Usage API is available
    const checkUsageAPIAvailability = async () => {
      try {
        setChecking(true)
        // Try to fetch budget status to see if Usage API is configured
        const budgetStatus = await api.usage.getBudgetStatus()
        // If we get a valid response with monthly_budget, use enhanced version
        // Check for both possible field names and ensure we have valid data
        const hasValidBudget = budgetStatus && (budgetStatus.monthly_budget > 0 || false)
        const hasUsageData = budgetStatus && (
          budgetStatus.budget_used_percentage !== undefined || 
          budgetStatus.budget_used_percent !== undefined ||
          budgetStatus.current_spend !== undefined
        )
        
        if (hasValidBudget && hasUsageData) {
          setUseEnhanced(true)
        } else {
          console.log('Budget data incomplete or invalid, falling back to quota system')
          setUseEnhanced(false)
        }
      } catch (error) {
        console.log('Usage API not available, falling back to quota system:', error)
        setUseEnhanced(false)
      } finally {
        setChecking(false)
      }
    }

    checkUsageAPIAvailability()
  }, [])

  if (checking) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mx-auto mb-2"></div>
          <div className="text-sm">Initializing budget monitor...</div>
        </div>
      </div>
    )
  }

  // Use enhanced version with real costs if available, otherwise fallback to quota tracking
  return useEnhanced ? (
    <BudgetUsageChatEnhanced workspaceId={workspaceId} />
  ) : (
    <BudgetUsageChat workspaceId={workspaceId} />
  )
}