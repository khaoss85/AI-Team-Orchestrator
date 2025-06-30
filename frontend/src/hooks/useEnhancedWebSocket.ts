// frontend/src/hooks/useEnhancedWebSocket.ts
/**
 * 🔗 ENHANCED WEBSOCKET HOOK
 * 
 * Advanced WebSocket connection management with:
 * - Intelligent reconnection with exponential backoff
 * - Heartbeat handling and connection health monitoring
 * - Connection state persistence and recovery
 * - Graceful degradation and error handling
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
  PERMANENTLY_FAILED = 'permanently_failed'
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface ConnectionStats {
  totalConnections: number;
  reconnectionAttempts: number;
  messagesReceived: number;
  messagesSent: number;
  lastHeartbeat?: number;
  connectionAge?: number;
}

interface UseEnhancedWebSocketOptions {
  maxReconnectAttempts?: number;
  baseReconnectDelay?: number;
  maxReconnectDelay?: number;
  heartbeatInterval?: number;
  connectionTimeout?: number;
  enableHeartbeat?: boolean;
  enableAutoReconnect?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onConnectionChange?: (state: ConnectionState) => void;
  onError?: (error: Event) => void;
}

interface UseEnhancedWebSocketReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  sendMessage: (message: WebSocketMessage) => boolean;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  stats: ConnectionStats;
}

export function useEnhancedWebSocket(
  url: string,
  options: UseEnhancedWebSocketOptions = {}
): UseEnhancedWebSocketReturn {
  const {
    maxReconnectAttempts = 10,
    baseReconnectDelay = 1000,
    maxReconnectDelay = 30000,
    heartbeatInterval = 30000,
    connectionTimeout = 10000,
    enableHeartbeat = true,
    enableAutoReconnect = true,
    onMessage,
    onConnectionChange,
    onError
  } = options;

  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [stats, setStats] = useState<ConnectionStats>({
    totalConnections: 0,
    reconnectionAttempts: 0,
    messagesReceived: 0,
    messagesSent: 0
  });

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isIntentionalDisconnectRef = useRef(false);
  const connectionStartTimeRef = useRef<number | null>(null);
  const lastHeartbeatRef = useRef<number | null>(null);

  const updateConnectionState = useCallback((newState: ConnectionState) => {
    setConnectionState(newState);
    onConnectionChange?.(newState);
  }, [onConnectionChange]);

  const calculateReconnectDelay = useCallback((attempt: number): number => {
    const delay = Math.min(
      baseReconnectDelay * Math.pow(2, attempt),
      maxReconnectDelay
    );
    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }, [baseReconnectDelay, maxReconnectDelay]);

  const startHeartbeat = useCallback(() => {
    if (!enableHeartbeat || !websocketRef.current) return;

    const sendHeartbeat = () => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        try {
          websocketRef.current.send(JSON.stringify({
            type: 'heartbeat_response',
            timestamp: Date.now(),
            client_id: 'frontend'
          }));
          lastHeartbeatRef.current = Date.now();
        } catch (error) {
          console.warn('🔗 Failed to send heartbeat:', error);
        }
      }
    };

    heartbeatTimeoutRef.current = setInterval(sendHeartbeat, heartbeatInterval);
  }, [enableHeartbeat, heartbeatInterval]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearInterval(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const closeConnection = useCallback(() => {
    stopHeartbeat();
    
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }

    if (websocketRef.current) {
      // Remove event listeners to prevent recursive calls
      websocketRef.current.onopen = null;
      websocketRef.current.onclose = null;
      websocketRef.current.onerror = null;
      websocketRef.current.onmessage = null;
      
      if (websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.close(1000, 'Client disconnect');
      }
      websocketRef.current = null;
    }
  }, [stopHeartbeat]);

  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    closeConnection();
    updateConnectionState(ConnectionState.CONNECTING);
    
    try {
      connectionStartTimeRef.current = Date.now();
      websocketRef.current = new WebSocket(url);

      // Connection timeout
      connectionTimeoutRef.current = setTimeout(() => {
        if (websocketRef.current?.readyState === WebSocket.CONNECTING) {
          console.warn('🔗 Connection timeout');
          closeConnection();
          updateConnectionState(ConnectionState.ERROR);
          
          if (enableAutoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
            scheduleReconnect();
          } else {
            updateConnectionState(ConnectionState.PERMANENTLY_FAILED);
          }
        }
      }, connectionTimeout);

      websocketRef.current.onopen = () => {
        console.log('🔗 WebSocket connected to:', url);
        
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
        }

        reconnectAttemptsRef.current = 0;
        updateConnectionState(ConnectionState.CONNECTED);
        startHeartbeat();
        
        setStats(prev => ({
          ...prev,
          totalConnections: prev.totalConnections + 1,
          connectionAge: connectionStartTimeRef.current ? Date.now() - connectionStartTimeRef.current : 0
        }));
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          setStats(prev => ({
            ...prev,
            messagesReceived: prev.messagesReceived + 1,
            lastHeartbeat: message.type === 'heartbeat' ? Date.now() : prev.lastHeartbeat
          }));

          // Handle heartbeat from server
          if (message.type === 'heartbeat') {
            // Server heartbeat received, respond if needed
            if (websocketRef.current?.readyState === WebSocket.OPEN) {
              websocketRef.current.send(JSON.stringify({
                type: 'heartbeat_response',
                timestamp: Date.now()
              }));
            }
            return;
          }

          onMessage?.(message);
        } catch (error) {
          console.error('🔗 Failed to parse WebSocket message:', error);
        }
      };

      websocketRef.current.onclose = (event) => {
        console.log('🔗 WebSocket disconnected:', event.code, event.reason);
        
        stopHeartbeat();
        
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
        }

        if (isIntentionalDisconnectRef.current) {
          updateConnectionState(ConnectionState.DISCONNECTED);
          return;
        }

        // Determine if we should reconnect
        const shouldReconnect = enableAutoReconnect && 
                               reconnectAttemptsRef.current < maxReconnectAttempts &&
                               event.code !== 1008; // Don't reconnect on connection limit

        if (shouldReconnect) {
          updateConnectionState(ConnectionState.RECONNECTING);
          scheduleReconnect();
        } else {
          updateConnectionState(ConnectionState.PERMANENTLY_FAILED);
        }
      };

      websocketRef.current.onerror = (error) => {
        console.error('🔗 WebSocket error:', error);
        onError?.(error);
        updateConnectionState(ConnectionState.ERROR);
      };

    } catch (error) {
      console.error('🔗 Failed to create WebSocket:', error);
      updateConnectionState(ConnectionState.ERROR);
    }
  }, [url, updateConnectionState, startHeartbeat, stopHeartbeat, closeConnection, onMessage, onError, connectionTimeout, enableAutoReconnect, maxReconnectAttempts]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = calculateReconnectDelay(reconnectAttemptsRef.current);
    reconnectAttemptsRef.current++;
    
    setStats(prev => ({
      ...prev,
      reconnectionAttempts: prev.reconnectionAttempts + 1
    }));

    console.log(`🔗 Scheduling reconnection attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms`);

    reconnectTimeoutRef.current = setTimeout(() => {
      if (connectionState !== ConnectionState.CONNECTED) {
        connect();
      }
    }, delay);
  }, [calculateReconnectDelay, maxReconnectAttempts, connectionState, connect]);

  const disconnect = useCallback(() => {
    isIntentionalDisconnectRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    closeConnection();
    updateConnectionState(ConnectionState.DISCONNECTED);
  }, [closeConnection, updateConnectionState]);

  const reconnect = useCallback(() => {
    isIntentionalDisconnectRef.current = false;
    reconnectAttemptsRef.current = 0;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    connect();
  }, [connect]);

  const sendMessage = useCallback((message: WebSocketMessage): boolean => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      try {
        websocketRef.current.send(JSON.stringify(message));
        setStats(prev => ({
          ...prev,
          messagesSent: prev.messagesSent + 1
        }));
        return true;
      } catch (error) {
        console.error('🔗 Failed to send message:', error);
        return false;
      }
    }
    return false;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isIntentionalDisconnectRef.current = true;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      closeConnection();
    };
  }, [closeConnection]);

  // Auto-connect on mount
  useEffect(() => {
    if (url && connectionState === ConnectionState.DISCONNECTED) {
      isIntentionalDisconnectRef.current = false;
      connect();
    }
  }, [url, connect, connectionState]);

  return {
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    sendMessage,
    connect,
    disconnect,
    reconnect,
    stats: {
      ...stats,
      connectionAge: connectionStartTimeRef.current ? Date.now() - connectionStartTimeRef.current : undefined,
      lastHeartbeat: lastHeartbeatRef.current || undefined
    }
  };
}