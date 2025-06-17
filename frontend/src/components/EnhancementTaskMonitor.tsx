'use client'

import React, { useState, useEffect } from 'react'

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

const EnhancementTaskMonitor: React.FC<EnhancementTaskMonitorProps> = ({
  workspaceId,
  taskId,
  onTaskCompleted
}) => {
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [isVisible, setIsVisible] = useState(true) // Maintain visibility state

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, `[${timestamp}] ${message}`])
  }

  const fetchTaskStatus = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/monitoring/task/${id}/status`)
      if (response.ok) {
        const task = await response.json()
        setTaskStatus(task)
        
        // Log status changes only on actual changes (prevent spam)
        if (!taskStatus || taskStatus.status !== task.status) {
          addLog(`Task status changed: ${task.status}`)
          
          if (task.status === 'completed' && onTaskCompleted) {
            onTaskCompleted(task.id, task.result)
            addLog('✅ Task completed successfully!')
          } else if (task.status === 'failed') {
            addLog('❌ Task failed')
          }
        }
        
        return task
      }
    } catch (error) {
      console.error('Error fetching task status:', error)
      addLog(`❌ Error fetching status: ${error}`)
    }
    return null
  }

  const startMonitoring = (id: string) => {
    setIsMonitoring(true)
    setLogs([])
    addLog(`🔍 Starting monitoring for task ${id.slice(0, 8)}...`)
    
    const interval = setInterval(async () => {
      const task = await fetchTaskStatus(id)
      
      if (task && (task.status === 'completed' || task.status === 'failed')) {
        clearInterval(interval)
        setIsMonitoring(false)
        addLog('📋 Monitoring stopped - task finished')
      }
    }, 5000) // Check every 5 seconds (reduced frequency to prevent flashing)
    
    // Stop monitoring after 5 minutes max
    setTimeout(() => {
      clearInterval(interval)
      setIsMonitoring(false)
      addLog('⏰ Monitoring stopped - timeout reached')
    }, 300000)
  }

  useEffect(() => {
    if (taskId) {
      startMonitoring(taskId)
    }
  }, [taskId])

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

  if (!taskId || !taskStatus) {
    return null
  }

  // Prevent unnecessary re-renders during polling
  if (!isVisible) {
    return null
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-gray-900">🔍 Enhancement Task Monitor</h4>
        {isMonitoring && (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            <span className="text-sm text-blue-600">Monitoring...</span>
          </div>
        )}
      </div>

      {/* Current Task Status */}
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(taskStatus.status)} mb-3`}>
        <span className="mr-2">{getStatusIcon(taskStatus.status)}</span>
        {taskStatus.status.toUpperCase()}
      </div>

      {/* Task Details */}
      <div className="space-y-2 text-sm">
        <div><strong>Task ID:</strong> {taskStatus.id.slice(0, 8)}...</div>
        <div><strong>Name:</strong> {taskStatus.name}</div>
        {taskStatus.agent_name && (
          <div><strong>Assigned Agent:</strong> {taskStatus.agent_name}</div>
        )}
        <div><strong>Created:</strong> {new Date(taskStatus.created_at).toLocaleString()}</div>
        <div><strong>Last Updated:</strong> {new Date(taskStatus.updated_at).toLocaleString()}</div>
      </div>

      {/* Progress Logs */}
      {logs.length > 0 && (
        <div className="mt-4">
          <h5 className="font-medium text-gray-700 mb-2">📋 Monitoring Log</h5>
          <div className="bg-gray-50 rounded p-2 max-h-32 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index} className="text-xs text-gray-600 font-mono">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Task Result */}
      {taskStatus.result && (
        <div className="mt-4">
          <h5 className="font-medium text-gray-700 mb-2">📄 Task Result</h5>
          <div className="bg-green-50 rounded p-2 text-sm">
            <pre className="whitespace-pre-wrap text-green-800">
              {JSON.stringify(taskStatus.result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

// Use React.memo to prevent unnecessary re-renders
export default React.memo(EnhancementTaskMonitor)