// frontend/src/hooks/useWorkspaceWebSocket.ts
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface WorkspaceUpdate {
  type: 'task_update' | 'agent_update' | 'deliverable_update' | 'general_update'
  data: any
  timestamp: string
}

interface UseWorkspaceWebSocketOptions {
  workspaceId: string
  onTaskUpdate?: (taskData: any) => void
  onAgentUpdate?: (agentData: any) => void
  onDeliverableUpdate?: (deliverableData: any) => void
  onGeneralUpdate?: (updateData: any) => void
}

export const useWorkspaceWebSocket = ({
  workspaceId,
  onTaskUpdate,
  onAgentUpdate,
  onDeliverableUpdate,
  onGeneralUpdate
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

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${workspaceId}`
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
        
        if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectAttempts.current++
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setConnectionError('Max reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionError('WebSocket connection error')
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
    setTimeout(connect, 100)
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
      connect()
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