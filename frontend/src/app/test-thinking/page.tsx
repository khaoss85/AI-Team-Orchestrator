'use client'

import { useEffect, useState } from 'react'
import useWorkspaceThinking from '@/hooks/useWorkspaceThinking'

export default function TestThinkingPage() {
  const [testWorkspaceId] = useState('550e8400-e29b-41d4-a716-446655440000')
  const [manualFetchResult, setManualFetchResult] = useState<any>(null)
  const [manualFetchError, setManualFetchError] = useState<string | null>(null)
  
  // Use the hook
  const {
    thinkingProcesses,
    isLoading,
    error,
    refresh,
    hasActiveProcesses,
    recentProcessCount
  } = useWorkspaceThinking(testWorkspaceId)

  // Manual fetch test
  const testManualFetch = async () => {
    setManualFetchError(null)
    setManualFetchResult(null)
    
    try {
      const url = `http://localhost:8000/api/thinking/workspace/${testWorkspaceId}?limit=10`
      console.log('Manual fetch URL:', url)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      })
      
      console.log('Manual fetch response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Manual fetch data:', data)
      setManualFetchResult(data)
    } catch (err) {
      console.error('Manual fetch error:', err)
      setManualFetchError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    console.log('TestThinkingPage mounted')
    console.log('Test workspace ID:', testWorkspaceId)
  }, [testWorkspaceId])

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Thinking API Test Page</h1>
      
      <div className="space-y-6">
        {/* Hook Test Section */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-3">useWorkspaceThinking Hook Test</h2>
          
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Workspace ID:</span> {testWorkspaceId}
            </div>
            <div>
              <span className="font-medium">Loading:</span> {isLoading ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="font-medium">Error:</span> {error || 'None'}
            </div>
            <div>
              <span className="font-medium">Processes Count:</span> {thinkingProcesses.length}
            </div>
            <div>
              <span className="font-medium">Has Active:</span> {hasActiveProcesses ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="font-medium">Recent Count:</span> {recentProcessCount}
            </div>
          </div>

          <button
            onClick={refresh}
            className="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Refresh Hook Data
          </button>

          {thinkingProcesses.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium mb-2">Thinking Processes:</h3>
              <pre className="bg-white p-2 rounded text-xs overflow-auto max-h-60">
                {JSON.stringify(thinkingProcesses, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Manual Fetch Test Section */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-3">Manual Fetch Test</h2>
          
          <button
            onClick={testManualFetch}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Test Manual Fetch
          </button>

          {manualFetchError && (
            <div className="mt-3 p-2 bg-red-100 text-red-700 rounded">
              Error: {manualFetchError}
            </div>
          )}

          {manualFetchResult && (
            <div className="mt-4">
              <h3 className="font-medium mb-2">Manual Fetch Result:</h3>
              <pre className="bg-white p-2 rounded text-xs overflow-auto max-h-60">
                {JSON.stringify(manualFetchResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Browser Console Instructions */}
        <div className="bg-yellow-50 p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-3">Debugging Instructions</h2>
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Open browser Developer Tools (F12)</li>
            <li>Go to Console tab to see debug logs</li>
            <li>Go to Network tab to see API calls</li>
            <li>Look for requests to /api/thinking/workspace/</li>
            <li>Check request headers and response</li>
          </ol>
        </div>
      </div>
    </div>
  )
}