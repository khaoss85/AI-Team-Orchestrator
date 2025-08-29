'use client'

import { useState, useEffect, useCallback } from 'react'
import { api } from '@/utils/api'

interface ThinkingStep {
  id: string
  session_id: string
  step_type: string
  thinking_content: string
  meta_reasoning?: string
  confidence_level?: number
  quality_assessment?: any
  created_at: string
}

interface GoalThinkingData {
  goal: any
  decomposition: any
  todo_list: any[]
  thinking_steps: ThinkingStep[]
}

interface UseGoalThinkingReturn {
  thinkingData: GoalThinkingData | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  hasThinkingSteps: boolean
}

/**
 * Hook to fetch goal-specific thinking processes and todo list
 * This provides thinking steps that are specifically related to a goal/deliverable
 */
export function useGoalThinking(goalId: string, workspaceId: string): UseGoalThinkingReturn {
  const [thinkingData, setThinkingData] = useState<GoalThinkingData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchGoalThinking = useCallback(async () => {
    if (!goalId || !workspaceId) return

    setIsLoading(true)
    setError(null)

    try {
      console.log('🧠 [useGoalThinking] Fetching thinking data for goal:', goalId)
      
      // Use the goal-specific thinking endpoint
      const response = await fetch(`${api.getBaseUrl()}/api/thinking/goal/${goalId}/thinking?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch goal thinking data: ${response.status}`)
      }

      const data = await response.json()
      console.log('✅ [useGoalThinking] Goal thinking data loaded:', data)
      
      // Transform the data to match our interface
      const transformedData: GoalThinkingData = {
        goal: data.goal || {},
        decomposition: data.decomposition || {},
        todo_list: data.todo_list || [],
        thinking_steps: data.thinking_steps || []
      }
      
      setThinkingData(transformedData)

    } catch (err) {
      console.error('❌ [useGoalThinking] Error fetching goal thinking:', err)
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      setThinkingData(null)
    } finally {
      setIsLoading(false)
    }
  }, [goalId, workspaceId])

  // Initial load
  useEffect(() => {
    fetchGoalThinking()
  }, [fetchGoalThinking])

  // Auto-refresh every 60 seconds for goal-specific thinking updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchGoalThinking()
    }, 60000)

    return () => clearInterval(interval)
  }, [fetchGoalThinking])

  const hasThinkingSteps = (thinkingData?.thinking_steps?.length || 0) > 0

  return {
    thinkingData,
    isLoading,
    error,
    refresh: fetchGoalThinking,
    hasThinkingSteps,
  }
}

export default useGoalThinking