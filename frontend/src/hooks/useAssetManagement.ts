// frontend/src/hooks/useAssetManagement.ts - ENHANCED & FIXED VERSION

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import type { 
  AssetTrackingData, 
  ActionableAsset, 
  AssetTaskInfo,
  AssetRequirement,
  AssetSchema,
  ProjectDeliverablesExtended
} from '@/types';

export interface AssetDisplayData {
  asset: ActionableAsset;
  task_info: AssetTaskInfo;
  schema?: AssetSchema;
}

export interface AssetManagementState {
  // Raw API data
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
  
  // 🆕 NEW: Processed deliverable assets
  deliverableAssets: Record<string, ActionableAsset>;
  processedAssets: AssetDisplayData[];
  
  // States
  loading: boolean;
  error: string | null;
}

export const useAssetManagement = (workspaceId: string) => {
  const [state, setState] = useState<AssetManagementState>({
    tracking: null,
    requirements: null,
    schemas: {},
    extractionStatus: null,
    deliverableAssets: {},
    processedAssets: [],
    loading: true,
    error: null,
  });

  const fetchAssetData = useCallback(async () => {
    if (!workspaceId) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      // Fetch all asset-related data in parallel
      const [trackingResult, requirementsResult, schemasResult, extractionResult, deliverablesResult] = await Promise.allSettled([
        api.monitoring.getAssetTracking(workspaceId),
        api.assetManagement.getRequirements(workspaceId),
        api.assetManagement.getSchemas(workspaceId),
        api.assetManagement.getExtractionStatus(workspaceId),
        api.monitoring.getProjectDeliverables(workspaceId), // 🆕 Fetch deliverables for actionable assets
      ]);

      // Process results
      const tracking = trackingResult.status === 'fulfilled' ? trackingResult.value : null;
      const requirements = requirementsResult.status === 'fulfilled' ? requirementsResult.value : null;
      const schemas = schemasResult.status === 'fulfilled' ? schemasResult.value.available_schemas : {};
      const extractionStatus = extractionResult.status === 'fulfilled' ? extractionResult.value : null;
      const deliverables = deliverablesResult.status === 'fulfilled' ? deliverablesResult.value : null;

      // 🆕 Extract actionable assets from deliverables
      const deliverableAssets: Record<string, ActionableAsset> = {};
      if (deliverables) {
        deliverables.key_outputs
          .filter(output => output.type === 'final_deliverable')
          .forEach(output => {
            // Check different possible locations for actionable assets
            if (output.actionable_assets) {
              Object.assign(deliverableAssets, output.actionable_assets);
            }
            // Also check result structure
            if (output.result?.actionable_assets) {
              Object.assign(deliverableAssets, output.result.actionable_assets);
            }
            // Check detailed results
            if (output.result?.detailed_results_json) {
              try {
                const detailed = JSON.parse(output.result.detailed_results_json);
                if (detailed.actionable_assets) {
                  Object.assign(deliverableAssets, detailed.actionable_assets);
                }
              } catch (e) {
                console.debug('Could not parse detailed_results_json for assets');
              }
            }
          });
      }

      // 🆕 Create processed assets list combining tracking + deliverable assets
      const processedAssets: AssetDisplayData[] = [];
      
      // Add assets from tracking data
      if (tracking?.completed_assets) {
        for (const completedAsset of tracking.completed_assets) {
          const assetName = completedAsset.asset_type || 'unknown_asset';
          
          // Check if we have a real actionable asset from deliverables
          const actionableAsset = deliverableAssets[assetName];
          
          if (actionableAsset) {
            // Use real actionable asset
            processedAssets.push({
              asset: actionableAsset,
              task_info: completedAsset,
              schema: schemas[assetName]
            });
          } else {
            // Create mock asset for tracking purposes
            const mockAsset: ActionableAsset = {
              asset_name: assetName,
              asset_data: { 
                placeholder: 'Asset data extraction in progress',
                task_name: completedAsset.task_name,
                status: 'extracted',
                task_id: completedAsset.task_id
              },
              source_task_id: completedAsset.task_id,
              extraction_method: 'automatic',
              validation_score: 0.8,
              actionability_score: 0.7,
              ready_to_use: false,
              usage_instructions: 'Asset is being processed for actionable use',
            };

            processedAssets.push({
              asset: mockAsset,
              task_info: completedAsset,
              schema: schemas[assetName]
            });
          }
        }
      }

      // Add standalone deliverable assets not in tracking
      Object.entries(deliverableAssets).forEach(([assetName, asset]) => {
        const alreadyExists = processedAssets.some(p => p.asset.asset_name === assetName);
        if (!alreadyExists) {
          processedAssets.push({
            asset,
            task_info: {
              task_id: asset.source_task_id,
              task_name: `Deliverable Asset: ${assetName}`,
              asset_type: assetName,
              status: 'completed',
              agent_role: 'System',
            },
            schema: schemas[assetName]
          });
        }
      });

      setState(prev => ({
        ...prev,
        tracking,
        requirements,
        schemas,
        extractionStatus,
        deliverableAssets,
        processedAssets,
        loading: false,
        error: null,
      }));

      // Log any errors that occurred
      [trackingResult, requirementsResult, schemasResult, extractionResult, deliverablesResult].forEach((result, index) => {
        if (result.status === 'rejected') {
          const apiNames = ['tracking', 'requirements', 'schemas', 'extraction', 'deliverables'];
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

  // 🆕 Trigger asset analysis
  const triggerAssetAnalysis = useCallback(async () => {
    try {
      await api.projects.triggerAssetAnalysis(workspaceId);
      // Refresh data after analysis
      setTimeout(() => {
        fetchAssetData();
      }, 2000);
      return true;
    } catch (error) {
      console.error('Error triggering asset analysis:', error);
      throw error;
    }
  }, [workspaceId, fetchAssetData]);

  // 🆕 Check deliverable readiness
  const checkDeliverableReadiness = useCallback(async () => {
    try {
      const readiness = await api.monitoring.getDeliverableReadiness(workspaceId);
      return readiness.is_ready_for_deliverable;
    } catch (error) {
      console.warn('Could not check deliverable readiness:', error);
      return false;
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchAssetData();
  }, [fetchAssetData]);

  // 🆕 Enhanced helper methods with unified API
  const getAssetProgress = useCallback(() => {
    if (!state.tracking) return { completed: 0, total: 0, percentage: 0 };
    
    const assetSummary = state.tracking.asset_summary;
    if (!assetSummary) return { completed: 0, total: 0, percentage: 0 };
    
    const completedTasks = assetSummary.completed_asset_tasks || 0;
    const totalTasks = assetSummary.total_asset_tasks || 0;
    
    return {
      completed: completedTasks,
      total: totalTasks,
      percentage: totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0,
    };
  }, [state.tracking]);

  const getAssetsByType = useCallback((assetType: string): AssetDisplayData[] => {
    return state.processedAssets.filter(asset => 
      asset.asset.asset_name === assetType || 
      asset.task_info.asset_type === assetType
    );
  }, [state.processedAssets]);

  const isDeliverableReady = useCallback(() => {
    if (!state.tracking || !state.tracking.asset_summary) return false;
    return state.tracking.asset_summary.deliverable_ready || false;
  }, [state.tracking]);

  const getRequiredAssetTypes = useCallback((): string[] => {
    if (!state.requirements) return [];
    return (state.requirements.primary_assets_needed || []).map(req => req.asset_type);
  }, [state.requirements]);

  const getCompletedAssetTypes = useCallback((): string[] => {
    return state.processedAssets
      .filter(asset => asset.asset.ready_to_use)
      .map(asset => asset.asset.asset_name);
  }, [state.processedAssets]);

  const getMissingAssetTypes = useCallback((): string[] => {
    const required = getRequiredAssetTypes();
    const completed = getCompletedAssetTypes();
    return required.filter(type => !completed.includes(type));
  }, [getRequiredAssetTypes, getCompletedAssetTypes]);

  const getAssetTypeProgress = useCallback((assetType: string) => {
    if (!state.tracking) return { completed: 0, total: 0, percentage: 0 };
    
    const assetTypesBreakdown = state.tracking.asset_types_breakdown || {};
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
    const extractionSummary = state.extractionStatus.extraction_summary;
    return (extractionSummary?.extraction_ready_tasks || 0) > 0;
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
      const completedAssets = state.tracking.completed_assets || [];
      const pendingAssets = state.tracking.pending_assets || [];
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
      const completedAssets = state.tracking.completed_assets || [];
      const pendingAssets = state.tracking.pending_assets || [];
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

  // 🆕 NEW: Direct access to assets for components
  const assets = state.processedAssets.map(p => p.asset);
  const assetDisplayData = state.processedAssets;

  return {
    // 🆕 Direct access to structured data (for backwards compatibility)
    tracking: state.tracking,
    requirements: state.requirements,
    schemas: state.schemas,
    extractionStatus: state.extractionStatus,
    
    // 🆕 NEW: Direct access to processed assets
    assets,
    assetDisplayData,
    deliverableAssets: state.deliverableAssets,
    
    // States
    loading: state.loading,
    error: state.error,
    
    // Actions
    refresh: fetchAssetData,
    triggerAssetAnalysis,
    checkDeliverableReadiness,
    
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