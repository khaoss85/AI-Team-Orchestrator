'use client'

import React, { useEffect, useState } from 'react'
import useGoalThinking from '@/hooks/useGoalThinking'

interface ThinkingDebuggerProps {
  goalId: string
  workspaceId: string
  deliverableTitle: string
}

export default function ThinkingDebugger({ goalId, workspaceId, deliverableTitle }: ThinkingDebuggerProps) {
  const [debugInfo, setDebugInfo] = useState<string[]>([])
  
  const addDebug = (message: string) => {
    setDebugInfo(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }

  useEffect(() => {
    addDebug('ThinkingDebugger mounted')
    addDebug(`Props: goalId=${goalId}, workspaceId=${workspaceId}, deliverableTitle=${deliverableTitle}`)
  }, [goalId, workspaceId, deliverableTitle])

  const { 
    thinkingData, 
    isLoading, 
    error,
    hasThinkingSteps,
    refresh
  } = useGoalThinking(goalId, workspaceId, deliverableTitle)

  useEffect(() => {
    addDebug(`Hook response changed: isLoading=${isLoading}, error=${error}, hasThinkingSteps=${hasThinkingSteps}, thinkingData=${thinkingData ? 'has data' : 'null'}`)
    if (thinkingData) {
      addDebug(`Thinking steps count: ${thinkingData.thinking_steps?.length || 0}`)
    }
  }, [thinkingData, isLoading, error, hasThinkingSteps])

  const handleTestDirectAPI = async () => {
    addDebug('Testing direct API call...')
    try {
      const response = await fetch(`http://localhost:8000/api/thinking/workspace/${workspaceId}?limit=50`)
      addDebug(`Direct API response status: ${response.status}`)
      
      if (response.ok) {
        const data = await response.json()
        addDebug(`Direct API returned ${data.processes?.length || 0} processes`)
      } else {
        addDebug(`Direct API error: ${response.status}`)
      }
    } catch (error) {
      addDebug(`Direct API error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="fixed top-4 right-4 w-96 bg-white border shadow-lg rounded-lg p-4 max-h-96 overflow-y-auto z-50">
      <h3 className="font-bold text-sm mb-2">🧠 Thinking System Debug</h3>
      
      <div className="space-y-2 mb-4">
        <div className="text-xs">
          <strong>Goal ID:</strong> {goalId}
        </div>
        <div className="text-xs">
          <strong>Workspace ID:</strong> {workspaceId}
        </div>
        <div className="text-xs">
          <strong>Title:</strong> {deliverableTitle}
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="text-xs">
          <strong>Loading:</strong> {isLoading.toString()}
        </div>
        <div className="text-xs">
          <strong>Error:</strong> {error || 'None'}
        </div>
        <div className="text-xs">
          <strong>Has Steps:</strong> {hasThinkingSteps.toString()}
        </div>
        <div className="text-xs">
          <strong>Steps Count:</strong> {thinkingData?.thinking_steps?.length || 0}
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={refresh}
          className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
        >
          Refresh Hook
        </button>
        <button
          onClick={handleTestDirectAPI}
          className="px-2 py-1 bg-green-500 text-white text-xs rounded"
        >
          Test Direct API
        </button>
      </div>

      <div className="border-t pt-2">
        <h4 className="font-semibold text-xs mb-2">Debug Log:</h4>
        <div className="space-y-1 text-xs max-h-32 overflow-y-auto">
          {debugInfo.map((info, index) => (
            <div key={index} className="text-gray-600">{info}</div>
          ))}
        </div>
      </div>
    </div>
  )
}