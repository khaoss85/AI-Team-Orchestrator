'use client'

import React, { useState } from 'react'

interface ThinkingDebugPanelProps {
  workspaceId: string
  isConnected?: boolean
}

export default function ThinkingDebugPanel({ workspaceId, isConnected = false }: ThinkingDebugPanelProps) {
  const [loading, setLoading] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Get API base URL from environment
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/'

  const runThinkingDemo = async () => {
    setLoading(true)
    setError(null)
    setLastResult(null)

    try {
      const response = await fetch(`${apiBaseUrl}api/test-thinking/demo/${workspaceId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      setLastResult(result)
      console.log('🧠 Thinking demo result:', result)

    } catch (err: any) {
      console.error('🧠 Thinking demo error:', err)
      setError(err.message || 'Unknown error occurred')
    } finally {
      setLoading(false)
    }
  }

  const checkSystemStatus = async () => {
    setLoading(true)
    setError(null)
    setLastResult(null)

    try {
      const response = await fetch(`${apiBaseUrl}api/test-thinking/status`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      setLastResult(result)
      console.log('🧠 System status:', result)

    } catch (err: any) {
      console.error('🧠 System status error:', err)
      setError(err.message || 'Unknown error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">🔧</span>
          <h3 className="text-sm font-medium text-gray-900">Thinking System Debug</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
          <span className="text-xs text-gray-600">
            {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
          </span>
        </div>
      </div>

      <div className="flex space-x-2 mb-3">
        <button
          onClick={runThinkingDemo}
          disabled={loading}
          className="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Running...' : '🧠 Run Thinking Demo'}
        </button>
        
        <button
          onClick={checkSystemStatus}
          disabled={loading}
          className="px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Checking...' : '📊 Check Status'}
        </button>
      </div>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <span className="font-medium">Error:</span> {error}
        </div>
      )}

      {lastResult && (
        <div className="mb-3 p-3 bg-white border border-gray-200 rounded text-sm">
          <div className="font-medium text-gray-900 mb-2">Last Result:</div>
          <div className="space-y-2">
            {lastResult.success !== undefined && (
              <div className={`flex items-center space-x-2 ${lastResult.success ? 'text-green-700' : 'text-red-700'}`}>
                <span>{lastResult.success ? '✅' : '❌'}</span>
                <span>Success: {lastResult.success ? 'Yes' : 'No'}</span>
              </div>
            )}
            
            {lastResult.process_id && (
              <div className="text-gray-600">
                <span className="font-medium">Process ID:</span> {lastResult.process_id}
              </div>
            )}
            
            {lastResult.steps_created && (
              <div className="text-gray-600">
                <span className="font-medium">Steps Created:</span> {lastResult.steps_created}
              </div>
            )}
            
            {lastResult.status && (
              <div className={`text-${lastResult.status === 'operational' ? 'green' : 'red'}-600`}>
                <span className="font-medium">Status:</span> {lastResult.status}
              </div>
            )}
            
            {lastResult.message && (
              <div className="text-blue-600 font-medium">
                {lastResult.message}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500">
        💡 Run the demo to test real-time thinking steps. Watch the 'Thinking' tab for live updates!
      </div>
    </div>
  )
}