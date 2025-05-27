// frontend/src/hooks/useAssetManagement.ts - DEEP ASSET EXTRACTION VERSION

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
  
  // Processed deliverable assets
  deliverableAssets: Record<string, ActionableAsset>;
  processedAssets: AssetDisplayData[];
  
  // States
  loading: boolean;
  error: string | null;
}

// 🔍 DEEP ASSET EXTRACTOR - Ispeziona ogni possibile location
const extractActionableAssets = (deliverables: ProjectDeliverablesExtended): Record<string, ActionableAsset> => {
  const extractedAssets: Record<string, ActionableAsset> = {};
  
  console.log('🔍 [DEEP EXTRACTION] Starting deep asset extraction...');
  console.log('🔍 [DEEP EXTRACTION] Total outputs to inspect:', deliverables.key_outputs?.length || 0);
  
  if (!deliverables.key_outputs) {
    console.log('🔍 [DEEP EXTRACTION] No key_outputs found');
    return extractedAssets;
  }

  deliverables.key_outputs.forEach((output, index) => {
    console.log(`🔍 [DEEP EXTRACTION] === Inspecting Output ${index + 1} ===`);
    console.log(`🔍 [DEEP EXTRACTION] Task ID: ${output.task_id}`);
    console.log(`🔍 [DEEP EXTRACTION] Type: ${output.type}`);
    console.log(`🔍 [DEEP EXTRACTION] Task Name: ${output.task_name}`);
    
    // 🎯 Location 1: Direct actionable_assets property
    if (output.actionable_assets) {
      console.log('🔍 [DEEP EXTRACTION] Found direct actionable_assets:', typeof output.actionable_assets);
      console.log('🔍 [DEEP EXTRACTION] Direct assets keys:', Object.keys(output.actionable_assets));
      Object.assign(extractedAssets, output.actionable_assets);
    }
    
    // 🎯 Location 2: result.actionable_assets
    if (output.result?.actionable_assets) {
      console.log('🔍 [DEEP EXTRACTION] Found result.actionable_assets:', typeof output.result.actionable_assets);
      console.log('🔍 [DEEP EXTRACTION] Result assets keys:', Object.keys(output.result.actionable_assets));
      Object.assign(extractedAssets, output.result.actionable_assets);
    }
    
    // 🎯 Location 3: detailed_results_json parsing
    if (output.result?.detailed_results_json) {
      console.log('🔍 [DEEP EXTRACTION] Found detailed_results_json, attempting to parse...');
      try {
        let detailed;
        if (typeof output.result.detailed_results_json === 'string') {
          console.log('🔍 [DEEP EXTRACTION] Parsing JSON string of length:', output.result.detailed_results_json.length);
          detailed = JSON.parse(output.result.detailed_results_json);
        } else {
          console.log('🔍 [DEEP EXTRACTION] Using object directly');
          detailed = output.result.detailed_results_json;
        }
        
        console.log('🔍 [DEEP EXTRACTION] Parsed detailed keys:', Object.keys(detailed));
        
        if (detailed.actionable_assets) {
          console.log('🔍 [DEEP EXTRACTION] Found detailed.actionable_assets:', Object.keys(detailed.actionable_assets));
          Object.assign(extractedAssets, detailed.actionable_assets);
        }
        
        // Check for other possible asset locations
        if (detailed.assets) {
          console.log('🔍 [DEEP EXTRACTION] Found detailed.assets:', Object.keys(detailed.assets));
          Object.assign(extractedAssets, detailed.assets);
        }
        
        if (detailed.business_assets) {
          console.log('🔍 [DEEP EXTRACTION] Found detailed.business_assets:', Object.keys(detailed.business_assets));
          Object.assign(extractedAssets, detailed.business_assets);
        }
        
      } catch (e) {
        console.log('🔍 [DEEP EXTRACTION] JSON parse failed:', e);
      }
    }
    
    // 🎯 Location 4: Check if the entire result contains asset-like data
    if (output.result && typeof output.result === 'object') {
      console.log('🔍 [DEEP EXTRACTION] Inspecting result object keys:', Object.keys(output.result));
      
      // Look for asset-like structures in the result
      Object.entries(output.result).forEach(([key, value]) => {
        if (key.toLowerCase().includes('asset') && typeof value === 'object' && value !== null) {
          console.log(`🔍 [DEEP EXTRACTION] Found potential asset in result.${key}:`, typeof value);
          
          if (Array.isArray(value)) {
            console.log(`🔍 [DEEP EXTRACTION] Asset array with ${value.length} items`);
          } else {
            console.log(`🔍 [DEEP EXTRACTION] Asset object with keys:`, Object.keys(value));
            
            // If it looks like a single asset, wrap it
            if (value.asset_name || value.source_task_id || value.actionability_score) {
              const assetName = value.asset_name || key;
              extractedAssets[assetName] = value as ActionableAsset;
              console.log(`🔍 [DEEP EXTRACTION] Added single asset: ${assetName}`);
            }
          }
        }
      });
    }

    // 🎯 Location 5: Check for structured data that could be assets
    if (output.result?.summary && output.type === 'final_deliverable') {
      console.log('🔍 [DEEP EXTRACTION] Creating synthetic asset from final deliverable summary...');
      
      // Create a synthetic asset from the final deliverable
      const syntheticAsset: ActionableAsset = {
        asset_name: 'final_deliverable_summary',
        asset_data: {
          executive_summary: output.result.summary,
          key_outputs: output.result.key_points || [],
          recommendations: output.result.next_steps || [],
          full_content: output.result,
          generated_from: 'final_deliverable'
        },
        source_task_id: output.task_id,
        extraction_method: 'synthetic',
        validation_score: 0.9,
        actionability_score: 0.8,
        ready_to_use: true,
        usage_instructions: 'Summary completo del progetto con raccomandazioni azionabili',
      };
      
      extractedAssets['final_deliverable_summary'] = syntheticAsset;
      console.log('🔍 [DEEP EXTRACTION] Added synthetic final deliverable asset');
    }
  });
  
  console.log(`🔍 [DEEP EXTRACTION] === EXTRACTION COMPLETE ===`);
  console.log(`🔍 [DEEP EXTRACTION] Total assets extracted: ${Object.keys(extractedAssets).length}`);
  console.log(`🔍 [DEEP EXTRACTION] Asset names: ${Object.keys(extractedAssets).join(', ')}`);
  
  return extractedAssets;
};

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

  const debugLog = (message: string, data?: any) => {
    console.log(`🔍 [useAssetManagement] ${message}`, data || '');
  };

  const fetchAssetData = useCallback(async () => {
    if (!workspaceId) {
      debugLog('No workspaceId provided, skipping fetch');
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      debugLog(`Starting fetch for workspace: ${workspaceId}`);

      // Fetch all asset-related data with individual error handling
      const fetchPromises = [
        api.monitoring.getAssetTracking(workspaceId).catch(err => {
          debugLog('Asset tracking failed:', err.message);
          return null;
        }),
        
        api.assetManagement.getRequirements(workspaceId).catch(err => {
          debugLog('Requirements failed:', err.message);
          return null;
        }),
        
        api.assetManagement.getSchemas(workspaceId).catch(err => {
          debugLog('Schemas failed:', err.message);
          return { available_schemas: {} };
        }),
        
        api.assetManagement.getExtractionStatus(workspaceId).catch(err => {
          debugLog('Extraction status failed:', err.message);
          return null;
        }),
        
        api.monitoring.getProjectDeliverables(workspaceId).catch(err => {
          debugLog('Deliverables failed:', err.message);
          return null;
        })
      ];

      const results = await Promise.all(fetchPromises);
      
      const [trackingResult, requirementsResult, schemasResult, extractionResult, deliverablesResult] = results;

      debugLog('API Results received:', {
        hasTracking: !!trackingResult,
        hasRequirements: !!requirementsResult,
        schemasCount: Object.keys(schemasResult?.available_schemas || {}).length,
        hasExtraction: !!extractionResult,
        hasDeliverables: !!deliverablesResult
      });

      const tracking = trackingResult as AssetTrackingData | null;
      const requirements = requirementsResult;
      const schemas = schemasResult?.available_schemas || {};
      const extractionStatus = extractionResult;
      const deliverables = deliverablesResult as ProjectDeliverablesExtended | null;

      // 🆕 ENHANCED: Use deep extraction
      let deliverableAssets: Record<string, ActionableAsset> = {};
      
      if (deliverables) {
        debugLog(`Processing ${deliverables.key_outputs?.length || 0} deliverable outputs`);
        deliverableAssets = extractActionableAssets(deliverables);
      }

      debugLog(`Total deliverable assets extracted: ${Object.keys(deliverableAssets).length}`);

      // Create processed assets list
      const processedAssets: AssetDisplayData[] = [];
      
      // Add assets from tracking data
      if (tracking?.completed_assets) {
        debugLog(`Processing ${tracking.completed_assets.length} completed asset tasks from tracking`);
        
        for (const completedAsset of tracking.completed_assets) {
          const assetName = completedAsset.asset_type || `asset_${completedAsset.task_id.substring(0, 8)}`;
          
          const actionableAsset = deliverableAssets[assetName] || deliverableAssets[completedAsset.asset_type || ''];
          
          if (actionableAsset) {
            processedAssets.push({
              asset: actionableAsset,
              task_info: completedAsset,
              schema: schemas[assetName] || schemas[completedAsset.asset_type || '']
            });
            debugLog(`Added real asset from deliverable: ${assetName}`);
          } else {
            // Create more detailed placeholder
            const mockAsset: ActionableAsset = {
              asset_name: assetName,
              asset_data: { 
                status: 'Asset completato - In processamento per deliverable finale',
                task_name: completedAsset.task_name,
                task_id: completedAsset.task_id,
                agent_role: completedAsset.agent_role || 'Unknown',
                completion_note: 'Questo asset sarà incluso nel deliverable finale',
                raw_tracking_data: completedAsset
              },
              source_task_id: completedAsset.task_id,
              extraction_method: 'tracking_placeholder',
              validation_score: 0.7,
              actionability_score: 0.5,
              ready_to_use: false,
              usage_instructions: 'Asset completato ma in attesa di estrazione finale. Controlla i deliverable per la versione finale.',
            };

            processedAssets.push({
              asset: mockAsset,
              task_info: completedAsset,
              schema: schemas[assetName] || schemas[completedAsset.asset_type || '']
            });
            debugLog(`Added detailed placeholder asset: ${assetName}`);
          }
        }
      }

      // Add standalone deliverable assets
      Object.entries(deliverableAssets).forEach(([assetName, asset]) => {
        const alreadyExists = processedAssets.some(p => 
          p.asset.asset_name === assetName || 
          p.asset.source_task_id === asset.source_task_id
        );
        
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
          debugLog(`Added standalone deliverable asset: ${assetName}`);
        }
      });

      debugLog(`Total processed assets: ${processedAssets.length}`);

      const newState = {
        tracking,
        requirements,
        schemas,
        extractionStatus,
        deliverableAssets,
        processedAssets,
        loading: false,
        error: null,
      };

      debugLog('Setting final state:', {
        hasTracking: !!newState.tracking,
        hasRequirements: !!newState.requirements,
        schemasCount: Object.keys(newState.schemas).length,
        hasExtractionStatus: !!newState.extractionStatus,
        deliverableAssetsCount: Object.keys(newState.deliverableAssets).length,
        processedAssetsCount: newState.processedAssets.length
      });

      setState(prev => ({ ...prev, ...newState }));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore nel caricamento asset';
      debugLog('Fatal error in fetchAssetData:', err);
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, [workspaceId]);

  const triggerAssetAnalysis = useCallback(async () => {
    try {
      debugLog('Triggering asset analysis...');
      await api.projects.triggerAssetAnalysis(workspaceId);
      debugLog('Asset analysis triggered successfully');
      
      setTimeout(() => {
        debugLog('Refreshing data after analysis...');
        fetchAssetData();
      }, 2000);
      
      return true;
    } catch (error) {
      debugLog('Error triggering asset analysis:', error);
      throw error;
    }
  }, [workspaceId, fetchAssetData]);

  const checkDeliverableReadiness = useCallback(async () => {
    try {
      const readiness = await api.monitoring.getDeliverableReadiness(workspaceId);
      debugLog('Deliverable readiness checked:', readiness.is_ready_for_deliverable);
      return readiness.is_ready_for_deliverable;
    } catch (error) {
      debugLog('Could not check deliverable readiness:', error);
      return false;
    }
  }, [workspaceId]);

  useEffect(() => {
    debugLog('Hook initialized, starting initial fetch');
    fetchAssetData();
  }, [fetchAssetData]);

  // Helper methods (keeping the same as before)
  const getAssetProgress = useCallback(() => {
    if (!state.tracking?.asset_summary) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    
    const assetSummary = state.tracking.asset_summary;
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
    return state.tracking?.asset_summary?.deliverable_ready || false;
  }, [state.tracking]);

  const getRequiredAssetTypes = useCallback((): string[] => {
    return (state.requirements?.primary_assets_needed || []).map(req => req.asset_type);
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
    return (state.extractionStatus?.extraction_summary?.extraction_ready_tasks || 0) > 0;
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
    
    const contextData = task.context_data || {};
    if (contextData.asset_production || contextData.asset_oriented_task) {
      return true;
    }
    
    const taskName = task.name || '';
    if (taskName.toUpperCase().includes('PRODUCE ASSET:')) {
      return true;
    }
    
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
    
    const contextData = task.context_data || {};
    if (contextData.asset_type || contextData.detected_asset_type) {
      return contextData.asset_type || contextData.detected_asset_type;
    }
    
    if (state.tracking) {
      const completedAssets = state.tracking.completed_assets || [];
      const pendingAssets = state.tracking.pending_assets || [];
      const allAssetTasks = [...completedAssets, ...pendingAssets];
      
      const assetTask = allAssetTasks.find(assetTask => assetTask.task_id === task.id);
      if (assetTask?.asset_type) {
        return assetTask.asset_type;
      }
    }
    
    const taskName = task.name?.toLowerCase() || '';
    if (taskName.includes('calendar')) return 'content_calendar';
    if (taskName.includes('contact') || taskName.includes('database')) return 'contact_database';
    if (taskName.includes('strategy')) return 'strategy_document';
    if (taskName.includes('analysis')) return 'analysis_report';
    
    return null;
  }, [state.tracking]);

  const getAssetCompletionStats = useCallback(() => {
    if (!state.tracking?.asset_summary) {
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

  const assets = state.processedAssets.map(p => p.asset);
  const assetDisplayData = state.processedAssets;

  debugLog('Hook returning state:', {
    hasTracking: !!state.tracking,
    hasRequirements: !!state.requirements,
    schemasCount: Object.keys(state.schemas).length,
    hasExtractionStatus: !!state.extractionStatus,
    assetsCount: assets.length,
    assetDisplayDataCount: assetDisplayData.length,
    deliverableAssetsCount: Object.keys(state.deliverableAssets).length,
    loading: state.loading,
    error: state.error
  });

  return {
    tracking: state.tracking,
    requirements: state.requirements,
    schemas: state.schemas,
    extractionStatus: state.extractionStatus,
    
    assets,
    assetDisplayData,
    deliverableAssets: state.deliverableAssets,
    
    loading: state.loading,
    error: state.error,
    
    refresh: fetchAssetData,
    triggerAssetAnalysis,
    checkDeliverableReadiness,
    
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