// frontend/src/hooks/useWebSocketTaskStatus.ts
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface TaskStatus {
  id: string
  name: string
  status: string
  created_at: string
  updated_at: string
  result: any
  agent_id?: string
  agent_name?: string
  workspace_id?: string
  progress_details?: any
}

interface WebSocketMessage {
  type: 'connection_confirmed' | 'task_update' | 'subscription_confirmed'
  task_id?: string
  data?: TaskStatus
  timestamp: string
  workspace_id?: string
}

interface UseWebSocketTaskStatusOptions {
  workspaceId: string
  taskId?: string
  onTaskCompleted?: (taskId: string, result: any) => void
  onTaskStatusChange?: (task: TaskStatus) => void
}

export const useWebSocketTaskStatus = ({
  workspaceId,
  taskId,
  onTaskCompleted,
  onTaskStatusChange
}: UseWebSocketTaskStatusOptions) => {
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev.slice(-9), `[${timestamp}] ${message}`]) // Keep last 10 logs
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${workspaceId}`
      addLog(`🔌 Connecting to WebSocket: ${wsUrl}`)
      
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        setConnectionError(null)
        reconnectAttempts.current = 0
        addLog('✅ WebSocket connected')

        // Subscribe to specific task if provided
        if (taskId && wsRef.current?.readyState === WebSocket.OPEN) {
          const subscribeMessage = {
            type: 'subscribe_task',
            task_id: taskId
          }
          wsRef.current.send(JSON.stringify(subscribeMessage))
          addLog(`🔔 Subscribed to task ${taskId.slice(0, 8)}...`)
        }
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          switch (message.type) {
            case 'connection_confirmed':
              addLog('🎯 Connection confirmed')
              break
              
            case 'subscription_confirmed':
              addLog(`📡 Subscription confirmed for task ${message.task_id?.slice(0, 8)}...`)
              break
              
            case 'task_update':
              if (message.data && message.task_id === taskId) {
                const newStatus = message.data
                setTaskStatus(newStatus)
                
                addLog(`📊 Task status: ${newStatus.status}`)
                
                // Call status change callback
                onTaskStatusChange?.(newStatus)
                
                // Handle completed tasks
                if (newStatus.status === 'completed' && onTaskCompleted) {
                  onTaskCompleted(newStatus.id, newStatus.result)
                  addLog('🎉 Task completed!')
                } else if (newStatus.status === 'failed') {
                  addLog('❌ Task failed')
                }
              }
              break
              
            default:
              addLog(`📝 Received: ${message.type}`)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
          addLog(`❌ Error parsing message: ${error}`)
        }
      }

      wsRef.current.onclose = (event) => {
        setIsConnected(false)
        
        if (event.wasClean) {
          addLog('👋 WebSocket closed cleanly')
        } else {
          addLog(`🔌 WebSocket disconnected (code: ${event.code})`)
          
          // Attempt to reconnect if not at max attempts
          if (reconnectAttempts.current < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000) // Exponential backoff, max 30s
            reconnectAttempts.current++
            
            addLog(`🔄 Reconnecting in ${delay/1000}s (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`)
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect()
            }, delay)
          } else {
            setConnectionError('Max reconnection attempts reached')
            addLog('❌ Max reconnection attempts reached')
          }
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionError('WebSocket connection error')
        addLog('❌ WebSocket error occurred')
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Failed to create WebSocket connection')
      addLog(`❌ Connection failed: ${error}`)
    }
  }, [workspaceId, taskId, onTaskCompleted, onTaskStatusChange, addLog])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting')
      wsRef.current = null
    }

    setIsConnected(false)
    addLog('🔌 Disconnected')
  }, [addLog])

  const manualReconnect = useCallback(() => {
    reconnectAttempts.current = 0
    setConnectionError(null)
    disconnect()
    setTimeout(connect, 100)
  }, [connect, disconnect])

  // Initial connection and cleanup
  useEffect(() => {
    if (workspaceId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [workspaceId, connect, disconnect])

  // Subscribe to new task when taskId changes
  useEffect(() => {
    if (taskId && wsRef.current?.readyState === WebSocket.OPEN) {
      const subscribeMessage = {
        type: 'subscribe_task',
        task_id: taskId
      }
      wsRef.current.send(JSON.stringify(subscribeMessage))
      addLog(`🔔 Subscribed to task ${taskId.slice(0, 8)}...`)
    }
  }, [taskId, addLog])

  return {
    taskStatus,
    isConnected,
    logs,
    connectionError,
    manualReconnect,
    isMonitoring: isConnected && !!taskId
  }
}