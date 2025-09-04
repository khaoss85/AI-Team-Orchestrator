'use client'

import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'
import { useEffect, useState } from 'react'

export default function TestQuotaPage() {
  const [testResult, setTestResult] = useState<string>('Testing quota monitoring...')
  const { quotaStatus, isConnected, error, refresh } = useQuotaMonitor({
    enableWebSocket: true,
    showNotifications: true,
    autoRefresh: false
  })

  useEffect(() => {
    // Test results
    const results = []
    
    // Check WebSocket connection
    if (isConnected) {
      results.push('✅ WebSocket: Connected')
    } else {
      results.push('❌ WebSocket: Disconnected')
    }
    
    // Check API connectivity
    if (quotaStatus.status) {
      results.push(`✅ API Status: ${quotaStatus.status}`)
    } else {
      results.push('❌ API Status: Not available')
    }
    
    // Check for errors
    if (error) {
      results.push(`❌ Error: ${error}`)
    }
    
    // Check statistics
    if (quotaStatus.statistics) {
      results.push(`✅ Statistics: ${quotaStatus.statistics.requestsToday || 0} requests today`)
    }
    
    setTestResult(results.join('\n'))
  }, [isConnected, quotaStatus, error])

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">Quota Monitoring Test</h1>
      
      <div className="bg-white rounded-lg shadow p-6 mb-4">
        <h2 className="text-lg font-semibold mb-2">Connection Status</h2>
        <pre className="bg-gray-100 p-4 rounded whitespace-pre-wrap">
          {testResult}
        </pre>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6 mb-4">
        <h2 className="text-lg font-semibold mb-2">Quota Details</h2>
        <div className="space-y-2">
          <p>Status: <span className={`font-medium ${quotaStatus.status === 'normal' ? 'text-green-600' : 'text-yellow-600'}`}>{quotaStatus.status}</span></p>
          <p>Message: {quotaStatus.message}</p>
          <p>Can Make Request: {quotaStatus.canMakeRequest ? '✅ Yes' : '❌ No'}</p>
          {quotaStatus.waitSeconds && (
            <p>Wait Time: {quotaStatus.waitSeconds} seconds</p>
          )}
        </div>
      </div>
      
      {quotaStatus.statistics && (
        <div className="bg-white rounded-lg shadow p-6 mb-4">
          <h2 className="text-lg font-semibold mb-2">Usage Statistics</h2>
          <div className="space-y-2">
            <p>Requests This Minute: {quotaStatus.statistics.requestsThisMinute}</p>
            <p>Requests Today: {quotaStatus.statistics.requestsToday}</p>
            <p>Minute Usage: {quotaStatus.statistics.minuteUsagePercent?.toFixed(1)}%</p>
            <p>Daily Usage: {quotaStatus.statistics.dailyUsagePercent?.toFixed(1)}%</p>
          </div>
        </div>
      )}
      
      <button 
        onClick={() => refresh()}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Refresh Quota Status
      </button>
      
      <div className="mt-8 p-4 bg-blue-50 rounded">
        <p className="text-sm text-gray-600">
          This test page verifies the quota monitoring system is working correctly.
          <br/>
          API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          <br/>
          WebSocket URL: {process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}
        </p>
      </div>
    </div>
  )
}