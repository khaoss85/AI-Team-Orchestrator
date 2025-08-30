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
export function useGoalThinking(goalId: string, workspaceId: string, deliverableTitle?: string): UseGoalThinkingReturn {
  const [thinkingData, setThinkingData] = useState<GoalThinkingData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchGoalThinking = useCallback(async () => {
    if (!goalId || !workspaceId) {
      return
    }
    setIsLoading(true)
    setError(null)

    try {
      // Use the workspace thinking endpoint with reduced limit for better performance
      const fetchUrl = `${api.getBaseUrl()}/api/thinking/workspace/${workspaceId}?limit=20`
      
      const response = await fetch(fetchUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch workspace thinking data: ${response.status}`)
      }

      const data = await response.json()
      
      // Filter thinking processes related to this goal
      const allProcesses = data.processes || []
      
      // OPTIMIZED: Use simplified filtering for better performance
      let goalRelatedProcesses: any[]
      
      if (goalId && (!deliverableTitle || deliverableTitle === 'undefined')) {
        // Use all processes for goal-specific requests (no complex filtering)
        goalRelatedProcesses = allProcesses
      } else {
        // Simplified filtering for better performance
        goalRelatedProcesses = allProcesses.filter((process: any) => {
          const context = process.context?.toLowerCase() || ''
          const goalIdLower = goalId.toLowerCase()
          
          // Simple matching: goal ID or deliverable title
          if (context.includes(goalIdLower)) {
            return true
          }
          
          if (deliverableTitle && deliverableTitle !== 'undefined') {
            const titleLower = deliverableTitle.toLowerCase()
            if (context.includes(titleLower)) {
              return true
            }
          }
          
          // Basic workspace content matching
          return context.includes('deliverable') || context.includes('task')
        })
      }
      
      
      // Transform thinking processes to match the thinking steps interface
      const transformedSteps: ThinkingStep[] = []
      goalRelatedProcesses.forEach((process: any) => {
        process.steps?.forEach((step: any, index: number) => {
          transformedSteps.push({
            id: step.step_id,
            session_id: process.process_id,
            step_type: step.step_type,
            thinking_content: step.content,
            meta_reasoning: step.metadata?.reasoning || process.final_conclusion,
            confidence_level: step.confidence,
            quality_assessment: step.metadata,
            created_at: step.timestamp
          })
        })
      })
      
      // Transform the data to match our interface
      const transformedData: GoalThinkingData = {
        goal: { id: goalId }, // Minimal goal data
        decomposition: {}, // Not available from thinking API
        todo_list: [], // Not available from thinking API  
        thinking_steps: transformedSteps
      }
      
      
      setThinkingData(transformedData)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      setThinkingData(null)
    } finally {
      setIsLoading(false)
    }
  }, [goalId, workspaceId, deliverableTitle])

  // Initial load
  useEffect(() => {
    fetchGoalThinking()
  }, [fetchGoalThinking])

  // Removed auto-refresh - only refresh manually to improve performance

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