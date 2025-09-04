'use client'

import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'
import { useEffect } from 'react'

export default function TestWebSocketPage() {
  const workspaceId = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  
  const { 
    quotaStatus, 
    isLoading, 
    error, 
    isConnected 
  } = useQuotaMonitor({
    workspaceId,
    enableWebSocket: true,
    showNotifications: false
  })

  useEffect(() => {
    console.log('WebSocket Test Page:', {
      isConnected,
      quotaStatus,
      isLoading,
      error
    })
  }, [isConnected, quotaStatus, isLoading, error])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">WebSocket Connection Test</h1>
      
      <div className="space-y-4">
        <div className="p-4 border rounded">
          <h2 className="font-semibold mb-2">Connection Status</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        <div className="p-4 border rounded">
          <h2 className="font-semibold mb-2">Quota Status</h2>
          <div className="space-y-1">
            <div>Status: {quotaStatus.status}</div>
            <div>Message: {quotaStatus.message}</div>
            <div>Can Make Request: {quotaStatus.canMakeRequest ? 'Yes' : 'No'}</div>
          </div>
        </div>

        {quotaStatus.statistics && (
          <div className="p-4 border rounded">
            <h2 className="font-semibold mb-2">Usage Statistics</h2>
            <div className="space-y-1">
              <div>Requests this minute: {quotaStatus.statistics.requestsThisMinute}</div>
              <div>Requests today: {quotaStatus.statistics.requestsToday}</div>
              <div>Minute usage: {quotaStatus.statistics.minuteUsagePercent.toFixed(1)}%</div>
              <div>Daily usage: {quotaStatus.statistics.dailyUsagePercent.toFixed(1)}%</div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 border border-red-500 rounded bg-red-50">
            <h2 className="font-semibold mb-2 text-red-700">Error</h2>
            <div className="text-red-600">{error}</div>
          </div>
        )}

        <div className="p-4 bg-gray-100 rounded">
          <h2 className="font-semibold mb-2">Test Info</h2>
          <div className="text-sm space-y-1">
            <div>Workspace ID: {workspaceId}</div>
            <div>Loading: {isLoading ? 'Yes' : 'No'}</div>
            <div>WebSocket Enabled: Yes</div>
          </div>
        </div>
      </div>
    </div>
  )
}