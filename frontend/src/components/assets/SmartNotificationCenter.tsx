'use client';

import React, { useState, useEffect } from 'react';
import { useRealTimeAssets } from '@/hooks/useRealTimeAssets';

interface SmartNotification {
  id: string;
  type: 'dependency_update' | 'batch_opportunity' | 'quality_improvement' | 'urgent_action' | 'automation_available';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  expires_at?: string;
  actions: NotificationAction[];
  context: any;
  dismissed: boolean;
  batch_id?: string;
  estimated_impact: number;
  estimated_effort: string;
  affected_assets: string[];
}

interface NotificationAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'danger';
  action: () => Promise<void>;
  loading?: boolean;
}

interface BatchSuggestion {
  id: string;
  assets: string[];
  estimated_time_saving: string;
  quality_improvement: number;
  business_impact: string;
  confidence: number;
}

interface Props {
  workspaceId: string;
  className?: string;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxVisible?: number;
}

export const SmartNotificationCenter: React.FC<Props> = ({
  workspaceId,
  className = '',
  position = 'top-right',
  maxVisible = 5
}) => {
  const { updates, isConnected, liveMetrics } = useRealTimeAssets(workspaceId);
  const [notifications, setNotifications] = useState<SmartNotification[]>([]);
  const [batchSuggestions, setBatchSuggestions] = useState<BatchSuggestion[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [smartFilters, setSmartFilters] = useState({
    enableBatching: true,
    priorityThreshold: 'medium',
    autoHideCompleted: true,
    groupSimilar: true
  });

  // Generate smart notifications from real-time updates
  useEffect(() => {
    if (updates.length === 0) return;

    const latestUpdate = updates[0];
    generateSmartNotifications(latestUpdate);
  }, [updates]);

  const generateSmartNotifications = (update: any) => {
    const notifications: SmartNotification[] = [];

    // High-impact dependency updates
    if (update.type === 'dependency_detected' && update.impact_score > 0.7) {
      notifications.push({
        id: `dep_${update.asset_id}_${Date.now()}`,
        type: 'dependency_update',
        title: '🔗 High-Impact Dependencies Detected',
        message: `Changes to ${update.data.source_asset?.name} affect ${update.affected_assets?.length} related assets`,
        priority: update.impact_score > 0.9 ? 'critical' : 'high',
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour
        actions: [
          {
            id: 'review',
            label: 'Review Changes',
            type: 'primary',
            action: async () => { /* Handle review */ }
          },
          {
            id: 'batch',
            label: 'Add to Batch',
            type: 'secondary', 
            action: async () => { /* Add to batch */ }
          }
        ],
        context: update,
        dismissed: false,
        estimated_impact: update.impact_score,
        estimated_effort: update.impact_score > 0.8 ? '15-30 min' : '5-15 min',
        affected_assets: update.affected_assets || []
      });
    }

    // Batch opportunity notifications
    if (updates.filter(u => u.auto_applicable).length >= 3) {
      const batchableUpdates = updates.filter(u => u.auto_applicable).slice(0, 5);
      
      notifications.push({
        id: `batch_${Date.now()}`,
        type: 'batch_opportunity',
        title: '⚡ Smart Batch Update Available',
        message: `${batchableUpdates.length} auto-applicable updates can be batched for efficiency`,
        priority: 'medium',
        created_at: new Date().toISOString(),
        actions: [
          {
            id: 'apply_batch',
            label: `Apply All (${batchableUpdates.length})`,
            type: 'primary',
            action: async () => { await handleBatchApply(batchableUpdates); }
          },
          {
            id: 'review_batch',
            label: 'Review Selection',
            type: 'secondary',
            action: async () => { /* Show batch review */ }
          }
        ],
        context: { batch_updates: batchableUpdates },
        dismissed: false,
        estimated_impact: 0.7,
        estimated_effort: '2-5 min',
        affected_assets: batchableUpdates.flatMap(u => u.affected_assets || [])
      });
    }

    // Quality improvement opportunities
    if (liveMetrics.avgImpactScore > 0.6 && liveMetrics.autoApplicableUpdates > 0) {
      notifications.push({
        id: `quality_${Date.now()}`,
        type: 'quality_improvement',
        title: '📈 Quality Enhancement Opportunity',
        message: `${liveMetrics.autoApplicableUpdates} improvements available with avg ${Math.round(liveMetrics.avgImpactScore * 100)}% impact`,
        priority: 'medium',
        created_at: new Date().toISOString(),
        actions: [
          {
            id: 'apply_quality',
            label: 'Enhance Quality',
            type: 'primary',
            action: async () => { /* Apply quality improvements */ }
          }
        ],
        context: { metrics: liveMetrics },
        dismissed: false,
        estimated_impact: liveMetrics.avgImpactScore,
        estimated_effort: 'Auto-applied',
        affected_assets: []
      });
    }

    setNotifications(prev => [...notifications, ...prev].slice(0, 20)); // Keep last 20
  };

  const handleBatchApply = async (updates: any[]) => {
    // Implement batch application logic
    console.log('Applying batch updates:', updates);
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, dismissed: true } : n));
  };

  const dismissAll = () => {
    setNotifications(prev => prev.map(n => ({ ...n, dismissed: true })));
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left': return 'top-4 left-4';
      case 'top-right': return 'top-4 right-4';
      case 'bottom-left': return 'bottom-4 left-4';
      case 'bottom-right': return 'bottom-4 right-4';
      default: return 'top-4 right-4';
    }
  };

  const getPriorityStyles = (priority: string) => {
    switch (priority) {
      case 'critical': return 'border-red-500 bg-red-50 text-red-900';
      case 'high': return 'border-orange-500 bg-orange-50 text-orange-900';
      case 'medium': return 'border-blue-500 bg-blue-50 text-blue-900';
      default: return 'border-gray-500 bg-gray-50 text-gray-900';
    }
  };

  const visibleNotifications = notifications
    .filter(n => !n.dismissed)
    .filter(n => {
      if (smartFilters.priorityThreshold === 'high') return ['high', 'critical'].includes(n.priority);
      if (smartFilters.priorityThreshold === 'medium') return ['medium', 'high', 'critical'].includes(n.priority);
      return true;
    })
    .slice(0, maxVisible);

  const totalUnread = notifications.filter(n => !n.dismissed).length;

  return (
    <div className={`fixed ${getPositionClasses()} z-50 ${className}`}>
      {/* Connection Status Indicator */}
      <div className={`mb-2 px-3 py-1 rounded-full text-xs font-medium ${
        isConnected 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800 animate-pulse'
      }`}>
        {isConnected ? '🟢 Live Updates' : '🔴 Disconnected'}
      </div>

      {/* Notification Toggle */}
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="relative">
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5-5-5h5z" />
            </svg>
            {totalUnread > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {totalUnread > 9 ? '9+' : totalUnread}
              </span>
            )}
          </div>
          <span className="text-sm font-medium text-gray-700">
            Smart Updates {totalUnread > 0 && `(${totalUnread})`}
          </span>
        </button>

        {totalUnread > 1 && (
          <button
            onClick={dismissAll}
            className="ml-2 px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Notifications List */}
      {isExpanded && (
        <div className="space-y-2 max-w-sm">
          {visibleNotifications.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
              <div className="text-center text-gray-500 text-sm">
                <div className="text-2xl mb-2">✨</div>
                <p>All caught up! No pending updates.</p>
              </div>
            </div>
          ) : (
            visibleNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`bg-white border-l-4 rounded-lg shadow-sm p-4 ${getPriorityStyles(notification.priority)} transition-all duration-300 hover:shadow-md`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-sm mb-1">{notification.title}</h4>
                    <p className="text-xs mb-3 opacity-90">{notification.message}</p>
                    
                    <div className="flex items-center space-x-4 text-xs opacity-75 mb-3">
                      <span>Impact: {Math.round(notification.estimated_impact * 100)}%</span>
                      <span>Effort: {notification.estimated_effort}</span>
                      <span>Assets: {notification.affected_assets.length}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {notification.actions.map((action) => (
                        <button
                          key={action.id}
                          onClick={action.action}
                          disabled={action.loading}
                          className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                            action.type === 'primary' 
                              ? 'bg-blue-600 text-white hover:bg-blue-700' 
                              : action.type === 'danger'
                              ? 'bg-red-600 text-white hover:bg-red-700'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          } disabled:opacity-50`}
                        >
                          {action.loading ? '...' : action.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => dismissNotification(notification.id)}
                    className="ml-2 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Smart Filters (when expanded) */}
      {isExpanded && totalUnread > 3 && (
        <div className="mt-3 p-3 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h5 className="text-xs font-medium text-gray-700 mb-2">Smart Filters</h5>
          <div className="space-y-2">
            <label className="flex items-center text-xs">
              <input
                type="checkbox"
                checked={smartFilters.enableBatching}
                onChange={(e) => setSmartFilters({...smartFilters, enableBatching: e.target.checked})}
                className="mr-2"
              />
              Enable Smart Batching
            </label>
            <label className="flex items-center text-xs">
              <input
                type="checkbox"
                checked={smartFilters.autoHideCompleted}
                onChange={(e) => setSmartFilters({...smartFilters, autoHideCompleted: e.target.checked})}
                className="mr-2"
              />
              Auto-hide Completed
            </label>
          </div>
        </div>
      )}
    </div>
  );
};