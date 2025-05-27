// frontend/src/hooks/useAssetManagement.ts

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import type { 
  AssetTrackingData, 
  ActionableAsset, 
  AssetTaskInfo,
  AssetRequirement,
  AssetSchema
} from '@/types';

export interface AssetManagementState {
  tracking: AssetTrackingData | null;
  requirements: {
    workspace_id: string;
    deliverable_category: string;
    primary_assets_needed: AssetRequirement[];
    deliverable_structure: Record<string, any>;
    generated_at: string;
  } | null;
  schemas: Record<string, AssetSchema>;
  extractionStatus: {
    extraction_summary: {
      total_completed_tasks: number;
      asset_production_tasks: number;
      extraction_ready_tasks: number;
      extraction_readiness_rate: number;
    };
    extraction_candidates: Array<{
      task_id: string;
      task_name: string;
      asset_type?: string;
      has_structured_output: boolean;
      extraction_ready: boolean;
      completed_at: string;
    }>;
    next_steps: string[];
  } | null;
  loading: boolean;
  error: string | null;
}

export const useAssetManagement = (workspaceId: string) => {
  const [state, setState] = useState<AssetManagementState>({
    tracking: null,
    requirements: null,
    schemas: {},
    extractionStatus: null,
    loading: true,
    error: null,
  });

  const fetchAssetData = useCallback(async () => {
    if (!workspaceId) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      // Fetch all asset-related data in parallel
      const [trackingData, requirementsData, schemasData, extractionData] = await Promise.allSettled([
        api.monitoring.getAssetTracking(workspaceId),
        api.assetManagement.getRequirements(workspaceId),
        api.assetManagement.getSchemas(workspaceId),
        api.assetManagement.getExtractionStatus(workspaceId),
      ]);

      setState(prev => ({
        ...prev,
        tracking: trackingData.status === 'fulfilled' ? trackingData.value : null,
        requirements: requirementsData.status === 'fulfilled' ? requirementsData.value : null,
        schemas: schemasData.status === 'fulfilled' ? schemasData.value.available_schemas : {},
        extractionStatus: extractionData.status === 'fulfilled' ? extractionData.value : null,
        loading: false,
        error: null,
      }));

      // Log any errors that occurred
      [trackingData, requirementsData, schemasData, extractionData].forEach((result, index) => {
        if (result.status === 'rejected') {
          const apiNames = ['tracking', 'requirements', 'schemas', 'extraction'];
          console.warn(`Asset ${apiNames[index]} API failed:`, result.reason);
        }
      });

    } catch (err) {
      console.error('Error fetching asset data:', err);
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Errore nel caricamento asset',
      }));
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchAssetData();
  }, [fetchAssetData]);

  // Helper methods
  const getAssetProgress = useCallback(() => {
    if (!state.tracking) return { completed: 0, total: 0, percentage: 0 };
    
    const { completed_asset_tasks, total_asset_tasks } = state.tracking.asset_summary;
    return {
      completed: completed_asset_tasks,
      total: total_asset_tasks,
      percentage: total_asset_tasks > 0 ? (completed_asset_tasks / total_asset_tasks) * 100 : 0,
    };
  }, [state.tracking]);

  const getAssetsByType = useCallback((assetType: string): AssetTaskInfo[] => {
    if (!state.tracking) return [];
    
    return [
      ...state.tracking.completed_assets,
      ...state.tracking.pending_assets,
    ].filter(asset => asset.asset_type === assetType);
  }, [state.tracking]);

  const isDeliverableReady = useCallback(() => {
    return state.tracking?.asset_summary.deliverable_ready || false;
  }, [state.tracking]);

  const getRequiredAssetTypes = useCallback((): string[] => {
    if (!state.requirements) return [];
    
    return state.requirements.primary_assets_needed.map(req => req.asset_type);
  }, [state.requirements]);

  const getCompletedAssetTypes = useCallback((): string[] => {
    if (!state.tracking) return [];
    
    return state.tracking.completed_assets
      .map(asset => asset.asset_type)
      .filter((type): type is string => Boolean(type));
  }, [state.tracking]);

  const getMissingAssetTypes = useCallback((): string[] => {
    const required = getRequiredAssetTypes();
    const completed = getCompletedAssetTypes();
    
    return required.filter(type => !completed.includes(type));
  }, [getRequiredAssetTypes, getCompletedAssetTypes]);

  const getAssetTypeProgress = useCallback((assetType: string) => {
    if (!state.tracking) return { completed: 0, total: 0, percentage: 0 };
    
    const typeData = state.tracking.asset_types_breakdown[assetType];
    if (!typeData) return { completed: 0, total: 0, percentage: 0 };
    
    return {
      completed: typeData.completed,
      total: typeData.total,
      percentage: typeData.total > 0 ? (typeData.completed / typeData.total) * 100 : 0,
    };
  }, [state.tracking]);

  const canExtractAssets = useCallback((): boolean => {
    if (!state.extractionStatus) return false;
    
    return state.extractionStatus.extraction_summary.extraction_ready_tasks > 0;
  }, [state.extractionStatus]);

  const getExtractionCandidates = useCallback(() => {
    return state.extractionStatus?.extraction_candidates || [];
  }, [state.extractionStatus]);

  const hasAssetSchemas = useCallback((): boolean => {
    return Object.keys(state.schemas).length > 0;
  }, [state.schemas]);

  const getSchemaForAssetType = useCallback((assetType: string): AssetSchema | null => {
    return state.schemas[assetType] || null;
  }, [state.schemas]);

  const isAssetTask = useCallback((task: any): boolean => {
    if (!task) return false;
    
    // Check context_data for asset markers
    const contextData = task.context_data || {};
    if (contextData.asset_production || contextData.asset_oriented_task) {
      return true;
    }
    
    // Check task name for asset production markers
    const taskName = task.name || '';
    if (taskName.toUpperCase().includes('PRODUCE ASSET:')) {
      return true;
    }
    
    // Check if task is in our asset tracking data
    if (state.tracking) {
      const allAssetTasks = [
        ...state.tracking.completed_assets,
        ...state.tracking.pending_assets,
      ];
      return allAssetTasks.some(assetTask => assetTask.task_id === task.id);
    }
    
    return false;
  }, [state.tracking]);

  const getAssetTypeFromTask = useCallback((task: any): string | null => {
    if (!task) return null;
    
    // Try context_data first
    const contextData = task.context_data || {};
    if (contextData.asset_type || contextData.detected_asset_type) {
      return contextData.asset_type || contextData.detected_asset_type;
    }
    
    // Try to find in tracking data
    if (state.tracking) {
      const allAssetTasks = [
        ...state.tracking.completed_assets,
        ...state.tracking.pending_assets,
      ];
      const assetTask = allAssetTasks.find(assetTask => assetTask.task_id === task.id);
      if (assetTask?.asset_type) {
        return assetTask.asset_type;
      }
    }
    
    // Try to infer from task name
    const taskName = task.name?.toLowerCase() || '';
    if (taskName.includes('calendar')) return 'content_calendar';
    if (taskName.includes('contact') || taskName.includes('database')) return 'contact_database';
    if (taskName.includes('strategy')) return 'strategy_document';
    if (taskName.includes('analysis')) return 'analysis_report';
    
    return null;
  }, [state.tracking]);

  const getAssetCompletionStats = useCallback() => {
    if (!state.tracking) {
      return {
        totalAssets: 0,
        completedAssets: 0,
        pendingAssets: 0,
        completionRate: 0,
        isDeliverableReady: false,
      };
    }
    
    const { asset_summary } = state.tracking;
    return {
      totalAssets: asset_summary.total_asset_tasks,
      completedAssets: asset_summary.completed_asset_tasks,
      pendingAssets: asset_summary.pending_asset_tasks,
      completionRate: asset_summary.completion_rate,
      isDeliverableReady: asset_summary.deliverable_ready,
    };
  }, [state.tracking]);

  return {
    // State
    ...state,
    
    // Actions
    refresh: fetchAssetData,
    
    // Computed values and helpers
    getAssetProgress,
    getAssetsByType,
    isDeliverableReady,
    getRequiredAssetTypes,
    getCompletedAssetTypes,
    getMissingAssetTypes,
    getAssetTypeProgress,
    canExtractAssets,
    getExtractionCandidates,
    hasAssetSchemas,
    getSchemaForAssetType,
    isAssetTask,
    getAssetTypeFromTask,
    getAssetCompletionStats,
  };
};