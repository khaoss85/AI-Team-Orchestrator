'use client'

import React, { useState, useEffect } from 'react'
import { useWebSocketTaskStatus } from '../hooks/useWebSocketTaskStatus'

interface EnhancementTaskMonitorProps {
  workspaceId: string
  taskId?: string
  onTaskCompleted?: (taskId: string, result: any) => void
}

interface TaskStatus {
  id: string
  name: string
  status: string
  created_at: string
  updated_at: string
  result: any
  agent_id?: string
  agent_name?: string
  progress_details?: any
}

const EnhancementTaskMonitorWebSocket: React.FC<EnhancementTaskMonitorProps> = ({
  workspaceId,
  taskId,
  onTaskCompleted
}) => {
  const [initialTaskData, setInitialTaskData] = useState<TaskStatus | null>(null)

  // Use WebSocket hook for real-time updates
  const {
    taskStatus,
    isConnected,
    logs,
    connectionError,
    manualReconnect,
    isMonitoring
  } = useWebSocketTaskStatus({
    workspaceId,
    taskId,
    onTaskCompleted,
    onTaskStatusChange: (task) => {
      // Update initial task data if we don't have it yet
      if (!initialTaskData) {
        setInitialTaskData(task)
      }
    }
  })

  // Fetch initial task data when taskId changes
  useEffect(() => {
    if (taskId && !taskStatus) {
      fetchInitialTaskData(taskId)
    }
  }, [taskId, taskStatus])

  const fetchInitialTaskData = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/monitoring/task/${id}/status`)
      if (response.ok) {
        const task = await response.json()
        setInitialTaskData(task)
      }
    } catch (error) {
      console.error('Error fetching initial task data:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-50'
      case 'in_progress': return 'text-blue-600 bg-blue-50'
      case 'completed': return 'text-green-600 bg-green-50'
      case 'failed': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'in_progress': return '🔄'
      case 'completed': return '✅'
      case 'failed': return '❌'
      default: return '❓'
    }
  }

  // Use real-time data if available, otherwise fall back to initial data
  const currentTask = taskStatus || initialTaskData

  if (!taskId || !currentTask) {
    return null
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-gray-900">📡 Real-time Task Monitor</h4>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600">Live</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-sm text-red-600">Disconnected</span>
              {connectionError && (
                <button
                  onClick={manualReconnect}
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Retry
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Current Task Status */}
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentTask.status)} mb-3`}>
        <span className="mr-2">{getStatusIcon(currentTask.status)}</span>
        {currentTask.status.toUpperCase()}
      </div>

      {/* Task Details */}
      <div className="space-y-2 text-sm">
        <div><strong>Task ID:</strong> {currentTask.id.slice(0, 8)}...</div>
        <div><strong>Name:</strong> {currentTask.name}</div>
        {currentTask.agent_name && (
          <div><strong>Assigned Agent:</strong> {currentTask.agent_name}</div>
        )}
        <div><strong>Created:</strong> {new Date(currentTask.created_at).toLocaleString()}</div>
        <div><strong>Last Updated:</strong> {new Date(currentTask.updated_at).toLocaleString()}</div>
      </div>

      {/* Real-time Activity Log */}
      {logs.length > 0 && (
        <div className="mt-4">
          <h5 className="font-medium text-gray-700 mb-2">📋 Real-time Activity</h5>
          <div className="bg-gray-50 rounded p-2 max-h-32 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index} className="text-xs text-gray-600 font-mono">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      {connectionError && (
        <div className="mt-4 p-2 bg-red-50 border border-red-200 rounded">
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600">⚠️ {connectionError}</span>
            <button
              onClick={manualReconnect}
              className="text-sm text-red-600 hover:text-red-800 underline"
            >
              Reconnect
            </button>
          </div>
        </div>
      )}

      {/* Task Result */}
      {currentTask.result && (
        <div className="mt-4">
          <h5 className="font-medium text-gray-700 mb-2">📄 Task Result</h5>
          <div className="bg-green-50 rounded p-2 text-sm">
            <pre className="whitespace-pre-wrap text-green-800">
              {JSON.stringify(currentTask.result, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Connection Info */}
      <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
        <span>🔗 WebSocket {isConnected ? 'Connected' : 'Disconnected'}</span>
        {isMonitoring && <span>👁️ Monitoring Active</span>}
      </div>
    </div>
  )
}

export default React.memo(EnhancementTaskMonitorWebSocket)