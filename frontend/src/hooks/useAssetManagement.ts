// frontend/src/hooks/useAssetManagement.ts - FIXED VERSION

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
    
    const tracking = state.tracking;
    const assetSummary = tracking.asset_summary;
    
    if (!assetSummary) return { completed: 0, total: 0, percentage: 0 };
    
    const completedTasks = assetSummary.completed_asset_tasks || 0;
    const totalTasks = assetSummary.total_asset_tasks || 0;
    
    return {
      completed: completedTasks,
      total: totalTasks,
      percentage: totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0,
    };
  }, [state.tracking]);

  const getAssetsByType = useCallback((assetType: string): AssetTaskInfo[] => {
    if (!state.tracking) return [];
    
    const tracking = state.tracking;
    const completedAssets = tracking.completed_assets || [];
    const pendingAssets = tracking.pending_assets || [];
    
    return [
      ...completedAssets,
      ...pendingAssets,
    ].filter(asset => asset.asset_type === assetType);
  }, [state.tracking]);

  const isDeliverableReady = useCallback(() => {
    if (!state.tracking || !state.tracking.asset_summary) return false;
    return state.tracking.asset_summary.deliverable_ready || false;
  }, [state.tracking]);

  const getRequiredAssetTypes = useCallback((): string[] => {
    if (!state.requirements) return [];
    
    const requirements = state.requirements;
    const primaryAssets = requirements.primary_assets_needed || [];
    
    return primaryAssets.map(req => req.asset_type);
  }, [state.requirements]);

  const getCompletedAssetTypes = useCallback((): string[] => {
    if (!state.tracking) return [];
    
    const tracking = state.tracking;
    const completedAssets = tracking.completed_assets || [];
    
    return completedAssets
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
    
    const tracking = state.tracking;
    const assetTypesBreakdown = tracking.asset_types_breakdown || {};
    const typeData = assetTypesBreakdown[assetType];
    
    if (!typeData) return { completed: 0, total: 0, percentage: 0 };
    
    const completed = typeData.completed || 0;
    const total = typeData.total || 0;
    
    return {
      completed,
      total,
      percentage: total > 0 ? (completed / total) * 100 : 0,
    };
  }, [state.tracking]);

  const canExtractAssets = useCallback((): boolean => {
    if (!state.extractionStatus) return false;
    
    const extractionStatus = state.extractionStatus;
    const extractionSummary = extractionStatus.extraction_summary;
    
    if (!extractionSummary) return false;
    
    return (extractionSummary.extraction_ready_tasks || 0) > 0;
  }, [state.extractionStatus]);

  const getExtractionCandidates = useCallback(() => {
    if (!state.extractionStatus) return [];
    return state.extractionStatus.extraction_candidates || [];
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
      const tracking = state.tracking;
      const completedAssets = tracking.completed_assets || [];
      const pendingAssets = tracking.pending_assets || [];
      const allAssetTasks = [...completedAssets, ...pendingAssets];
      
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
      const tracking = state.tracking;
      const completedAssets = tracking.completed_assets || [];
      const pendingAssets = tracking.pending_assets || [];
      const allAssetTasks = [...completedAssets, ...pendingAssets];
      
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

  const getAssetCompletionStats = useCallback(() => {
    if (!state.tracking || !state.tracking.asset_summary) {
      return {
        totalAssets: 0,
        completedAssets: 0,
        pendingAssets: 0,
        completionRate: 0,
        isDeliverableReady: false,
      };
    }
    
    const assetSummary = state.tracking.asset_summary;
    
    return {
      totalAssets: assetSummary.total_asset_tasks || 0,
      completedAssets: assetSummary.completed_asset_tasks || 0,
      pendingAssets: assetSummary.pending_asset_tasks || 0,
      completionRate: assetSummary.completion_rate || 0,
      isDeliverableReady: assetSummary.deliverable_ready || false,
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