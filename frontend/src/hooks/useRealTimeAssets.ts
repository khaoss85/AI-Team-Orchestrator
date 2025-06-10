'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { AssetDependency } from './useAssetDependencies';

interface RealTimeUpdate {
  type: 'asset_updated' | 'dependency_detected' | 'batch_completed' | 'quality_improved';
  asset_id: string;
  workspace_id: string;
  timestamp: string;
  data: any;
  impact_score: number;
  affected_assets?: string[];
  auto_applicable?: boolean;
}

interface AssetStream {
  id: string;
  name: string;
  status: 'processing' | 'completed' | 'failed' | 'queued';
  progress: number;
  eta_seconds?: number;
  quality_delta?: number;
  preview_content?: string;
}

interface StreamingStats {
  total_updates: number;
  active_streams: number;
  avg_processing_time: number;
  quality_improvements: number;
  auto_applied_updates: number;
}

export const useRealTimeAssets = (workspaceId: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [updates, setUpdates] = useState<RealTimeUpdate[]>([]);
  const [activeStreams, setActiveStreams] = useState<AssetStream[]>([]);
  const [stats, setStats] = useState<StreamingStats>({
    total_updates: 0,
    active_streams: 0,
    avg_processing_time: 0,
    quality_improvements: 0,
    auto_applied_updates: 0
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const [shouldConnect, setShouldConnect] = useState(true);

  // Connessione WebSocket con auto-reconnect
  const connect = useCallback(() => {
    if (!shouldConnect) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/assets/${workspaceId}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('🔌 Real-time asset updates connected');
        setIsConnected(true);
        
        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleRealTimeMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket connection closed');
        setIsConnected(false);
        
        // Auto-reconnect after 3 seconds
        if (shouldConnect) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
      
      // Retry connection after 5 seconds
      if (shouldConnect) {
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }
  }, [workspaceId, shouldConnect]);

  // Handler per messaggi real-time
  const handleRealTimeMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'asset_updated':
        handleAssetUpdate(message);
        break;
      case 'dependency_detected':
        handleDependencyDetected(message);
        break;
      case 'stream_progress':
        handleStreamProgress(message);
        break;
      case 'batch_completed':
        handleBatchCompleted(message);
        break;
      case 'stats_update':
        handleStatsUpdate(message);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }, []);

  const handleAssetUpdate = (message: RealTimeUpdate) => {
    setUpdates(prev => [message, ...prev.slice(0, 49)]); // Keep last 50 updates
    
    // Update stream if exists
    setActiveStreams(prev => 
      prev.map(stream => 
        stream.id === message.asset_id 
          ? { ...stream, status: 'completed', progress: 100 }
          : stream
      )
    );

    // Trigger browser notification for high-impact updates
    if (message.impact_score > 0.8 && 'Notification' in window) {
      new Notification(`Asset Updated: ${message.data.name}`, {
        body: `High-impact update completed. ${message.affected_assets?.length || 0} assets may need updates.`,
        icon: '/favicon.ico'
      });
    }
  };

  const handleDependencyDetected = (message: any) => {
    setUpdates(prev => [{
      type: 'dependency_detected',
      asset_id: message.source_asset_id,
      workspace_id: workspaceId,
      timestamp: new Date().toISOString(),
      data: message,
      impact_score: message.impact_score || 0.5,
      affected_assets: message.affected_assets,
      auto_applicable: message.auto_applicable
    }, ...prev.slice(0, 49)]);
  };

  const handleStreamProgress = (message: any) => {
    setActiveStreams(prev => {
      const existing = prev.find(s => s.id === message.asset_id);
      if (existing) {
        return prev.map(s => 
          s.id === message.asset_id 
            ? { ...s, ...message, progress: Math.min(100, message.progress || 0) }
            : s
        );
      } else {
        return [...prev, {
          id: message.asset_id,
          name: message.asset_name || 'Processing...',
          status: message.status || 'processing',
          progress: message.progress || 0,
          eta_seconds: message.eta_seconds,
          quality_delta: message.quality_delta,
          preview_content: message.preview_content
        }];
      }
    });
  };

  const handleBatchCompleted = (message: any) => {
    // Remove completed streams
    setActiveStreams(prev => 
      prev.filter(stream => !message.completed_asset_ids.includes(stream.id))
    );

    // Add summary update
    setUpdates(prev => [{
      type: 'batch_completed',
      asset_id: 'batch',
      workspace_id: workspaceId,
      timestamp: new Date().toISOString(),
      data: message,
      impact_score: 0.9,
      affected_assets: message.completed_asset_ids
    }, ...prev.slice(0, 49)]);
  };

  const handleStatsUpdate = (message: StreamingStats) => {
    setStats(message);
  };

  // Connessione automatica
  useEffect(() => {
    if (workspaceId && shouldConnect) {
      connect();
    }

    return () => {
      setShouldConnect(false);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [workspaceId, connect]);

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const clearUpdates = useCallback(() => {
    setUpdates([]);
  }, []);

  const clearCompletedStreams = useCallback(() => {
    setActiveStreams(prev => prev.filter(s => s.status !== 'completed'));
  }, []);

  // Utility per calcolare metriche live
  const liveMetrics = {
    recentHighImpactUpdates: updates.filter(u => u.impact_score > 0.7).length,
    avgImpactScore: updates.length > 0 ? updates.reduce((sum, u) => sum + u.impact_score, 0) / updates.length : 0,
    autoApplicableUpdates: updates.filter(u => u.auto_applicable).length,
    processingAssets: activeStreams.filter(s => s.status === 'processing').length,
    avgProgress: activeStreams.length > 0 ? activeStreams.reduce((sum, s) => sum + s.progress, 0) / activeStreams.length : 0
  };

  return {
    // Connection state
    isConnected,
    
    // Real-time data
    updates,
    activeStreams,
    stats,
    liveMetrics,
    
    // Actions
    sendMessage,
    clearUpdates,
    clearCompletedStreams,
    
    // Connection control
    connect,
    disconnect: () => {
      setShouldConnect(false);
      wsRef.current?.close();
    }
  };
};