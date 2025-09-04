'use client'

import { useState, useEffect, useCallback } from 'react'
import { api } from '@/utils/api'

interface ThinkingStep {
  step_id: string
  step_type: string
  content: string
  confidence: number
  timestamp: string
  metadata?: Record<string, any>
}

interface ThinkingProcess {
  process_id: string
  workspace_id: string
  context: string
  steps: ThinkingStep[]
  final_conclusion?: string
  overall_confidence: number
  started_at: string
  completed_at?: string
}

interface UseWorkspaceThinkingReturn {
  thinkingProcesses: ThinkingProcess[]
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  hasActiveProcesses: boolean
  recentProcessCount: number
}

/**
 * Hook to fetch and manage real workspace thinking data
 * This replaces demo data with actual thinking processes from task execution
 */
export function useWorkspaceThinking(workspaceId: string): UseWorkspaceThinkingReturn {
  const [thinkingProcesses, setThinkingProcesses] = useState<ThinkingProcess[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchThinkingData = useCallback(async () => {
    if (!workspaceId) return

    setIsLoading(true)
    setError(null)

    try {
      // Construct the URL
      const baseUrl = api.getBaseUrl()
      const url = `${baseUrl}/api/thinking/workspace/${workspaceId}?limit=10`
      
      console.log('🧠 Fetching thinking data from:', url)
      console.log('🧠 Base URL:', baseUrl)
      console.log('🧠 Workspace ID:', workspaceId)

      // Fetch real thinking processes from the workspace
      // This calls the actual thinking engine endpoint, not demo
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add credentials to handle CORS
        credentials: 'include',
      })

      console.log('🧠 Response status:', response.status)
      console.log('🧠 Response ok:', response.ok)

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'No error text')
        console.error('🧠 Error response:', errorText)
        throw new Error(`Failed to fetch thinking data: ${response.status} - ${errorText}`)
      }

      const data = await response.json()
      console.log('🧠 Response data:', data)
      
      // Transform the data if needed to match our interface
      const processes: ThinkingProcess[] = Array.isArray(data) ? data : (data.processes || [])
      console.log('🧠 Processed thinking processes:', processes.length, 'items')
      setThinkingProcesses(processes)

    } catch (err) {
      console.error('🧠 Error fetching workspace thinking:', err)
      console.error('🧠 Error details:', {
        name: err instanceof Error ? err.name : 'Unknown',
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : undefined,
      })
      
      // Check if it's a network error
      if (err instanceof TypeError && err.message === 'Failed to fetch') {
        setError('Network error: Unable to connect to the backend. Please ensure the backend server is running on port 8000.')
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      }
      setThinkingProcesses([]) // Clear data on error
    } finally {
      setIsLoading(false)
    }
  }, [workspaceId])

  // Initial load
  useEffect(() => {
    fetchThinkingData()
  }, [fetchThinkingData])

  // Auto-refresh every 30 seconds for real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchThinkingData()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchThinkingData])

  // Calculate derived values
  const hasActiveProcesses = thinkingProcesses.some(process => !process.completed_at)
  const recentProcessCount = thinkingProcesses.filter(process => {
    const startTime = new Date(process.started_at)
    const now = new Date()
    const hourAgo = new Date(now.getTime() - 60 * 60 * 1000)
    return startTime > hourAgo
  }).length

  return {
    thinkingProcesses,
    isLoading,
    error,
    refresh: fetchThinkingData,
    hasActiveProcesses,
    recentProcessCount,
  }
}

export default useWorkspaceThinking