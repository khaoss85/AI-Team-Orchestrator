// frontend/src/hooks/useWorkspaceWebSocket.ts
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface WorkspaceUpdate {
  type: 'task_update' | 'agent_update' | 'deliverable_update' | 'general_update' | 'thinking_step' | 'goal_decomposition_start' | 'goal_decomposition_complete'
  data: any
  timestamp: string
}

interface UseWorkspaceWebSocketOptions {
  workspaceId: string
  onTaskUpdate?: (taskData: any) => void
  onAgentUpdate?: (agentData: any) => void
  onDeliverableUpdate?: (deliverableData: any) => void
  onGeneralUpdate?: (updateData: any) => void
  // 🧠 Real-time thinking callbacks (Claude/o3 style)
  onThinkingStep?: (thinkingData: any) => void
  onGoalDecompositionStart?: (goalData: any) => void
  onGoalDecompositionComplete?: (decompositionData: any) => void
}

export const useWorkspaceWebSocket = ({
  workspaceId,
  onTaskUpdate,
  onAgentUpdate,
  onDeliverableUpdate,
  onGeneralUpdate,
  onThinkingStep,
  onGoalDecompositionStart,
  onGoalDecompositionComplete
}: UseWorkspaceWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false)
  const [realtimeUpdates, setRealtimeUpdates] = useState<WorkspaceUpdate[]>([])
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const addUpdate = useCallback((update: WorkspaceUpdate) => {
    setRealtimeUpdates(prev => [...prev.slice(-19), update]) // Keep last 20 updates
  }, [])

  // Check if backend is available before connecting
  const checkBackendHealth = useCallback(async () => {
    try {
      // Create AbortController for timeout (better browser compatibility)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
      
      const response = await fetch('http://localhost:8000/health', { 
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      return response.ok
    } catch (error) {
      console.warn('Backend health check failed:', error)
      return false
    }
  }, [])

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    // Check backend health before attempting WebSocket connection
    const isBackendHealthy = await checkBackendHealth()
    if (!isBackendHealthy) {
      setConnectionError('Backend server not available')
      console.warn('Skipping WebSocket connection - backend not healthy')
      return
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${workspaceId}`
      console.log(`Attempting WebSocket connection to: ${wsUrl}`)
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        setConnectionError(null)
        reconnectAttempts.current = 0
        
        addUpdate({
          type: 'general_update',
          data: { message: 'WebSocket connected' },
          timestamp: new Date().toISOString()
        })
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          switch (message.type) {
            case 'connection_confirmed':
              // Connection acknowledged
              break
              
            case 'task_update':
              if (message.data) {
                onTaskUpdate?.(message.data)
                addUpdate({
                  type: 'task_update',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            case 'thinking_step':
              // 🧠 Real-time thinking step updates (Claude/o3 style)
              if (message.data) {
                onThinkingStep?.(message.data)
                addUpdate({
                  type: 'thinking_step',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            case 'goal_decomposition_start':
              // 🎯 Goal decomposition started
              if (message.data) {
                onGoalDecompositionStart?.(message.data)
                addUpdate({
                  type: 'goal_decomposition_start',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            case 'goal_decomposition_complete':
              // ✅ Goal decomposition completed
              if (message.data) {
                onGoalDecompositionComplete?.(message.data)
                addUpdate({
                  type: 'goal_decomposition_complete',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            case 'agent_update':
              if (message.data) {
                onAgentUpdate?.(message.data)
                addUpdate({
                  type: 'agent_update',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            case 'deliverable_update':
              if (message.data) {
                onDeliverableUpdate?.(message.data)
                addUpdate({
                  type: 'deliverable_update',
                  data: message.data,
                  timestamp: message.timestamp
                })
              }
              break
              
            default:
              onGeneralUpdate?.(message)
              addUpdate({
                type: 'general_update',
                data: message,
                timestamp: message.timestamp || new Date().toISOString()
              })
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      wsRef.current.onclose = (event) => {
        setIsConnected(false)
        
        // Enhanced close event logging
        console.log(`WebSocket closed - Code: ${event.code}, Reason: ${event.reason || 'No reason'}, Clean: ${event.wasClean}`)
        
        // 🔧 FIX: Always try to reconnect unless explicitly told not to (code 1000 with 'shutdown' reason)
        const shouldReconnect = event.code !== 1001 && // Avoid reconnecting during intentional shutdowns
                               !(event.code === 1000 && event.reason?.includes('shutdown')) &&
                               reconnectAttempts.current < maxReconnectAttempts
                               
        if (shouldReconnect) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectAttempts.current++
          
          console.log(`WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(async () => {
            await connect()
          }, delay)
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setConnectionError('Max reconnection attempts reached')
          console.error('WebSocket max reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (error) => {
        // Enhanced error logging with more context
        console.error('WebSocket error occurred:', {
          error,
          readyState: wsRef.current?.readyState,
          url: wsUrl,
          workspaceId,
          timestamp: new Date().toISOString()
        })
        setConnectionError(`WebSocket connection error (${wsUrl})`)
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Failed to create WebSocket connection')
    }
  }, [workspaceId, onTaskUpdate, onAgentUpdate, onDeliverableUpdate, onGeneralUpdate, addUpdate])

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
  }, [])

  const manualReconnect = useCallback(() => {
    reconnectAttempts.current = 0
    setConnectionError(null)
    disconnect()
    setTimeout(async () => {
      await connect()
    }, 100)
  }, [connect, disconnect])

  const subscribeToTask = useCallback((taskId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const subscribeMessage = {
        type: 'subscribe_task',
        task_id: taskId
      }
      wsRef.current.send(JSON.stringify(subscribeMessage))
    }
  }, [])

  // Initial connection and cleanup
  useEffect(() => {
    if (workspaceId) {
      connect().catch(console.error)
    }

    return () => {
      disconnect()
    }
  }, [workspaceId, connect, disconnect])

  return {
    isConnected,
    realtimeUpdates,
    connectionError,
    manualReconnect,
    subscribeToTask
  }
}