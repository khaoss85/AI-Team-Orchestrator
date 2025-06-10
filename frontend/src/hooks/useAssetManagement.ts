// frontend/src/hooks/useAssetManagement.ts - COMPLETE FIXED VERSION

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import type {
  ActionableAsset,
  AssetTaskInfo,
  AssetSchema,
  ProjectDeliverablesExtended,
  Task,
  UseAssetManagementReturn,
  AssetManagementState,
  AssetDisplayData,
  AssetCompletionStats,
  AssetProgress,
  EnhancedTaskContextData
} from '@/types';

// 🔍 Enhanced Asset Extraction from Raw Tasks
const extractAssetsFromRawTasks = (tasks: Task[]): Record<string, ActionableAsset> => {
  const extractedAssets: Record<string, ActionableAsset> = {};
  
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 [RAW TASK EXTRACTION] Starting extraction from', tasks.length, 'tasks');
  }
  
  tasks.forEach((task, index) => {
    const contextData = task.context_data as EnhancedTaskContextData;
    
    // ✅ FIRST: Check ALL completed tasks for dual output format
    if (task.status === 'completed' && task.result?.detailed_results_json) {
      try {
        const detailed = typeof task.result.detailed_results_json === 'string' 
          ? JSON.parse(task.result.detailed_results_json)
          : task.result.detailed_results_json;
        
        // Check for new dual output format
        if (detailed.structured_content) {
          // Create asset from structured content
          const assetName = task.name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
          const dualOutputAsset: ActionableAsset = {
            asset_name: assetName,
            asset_data: {
              structured_content: detailed.structured_content,
              rendered_html: detailed.rendered_html,
              visual_summary: detailed.visual_summary,
              actionable_insights: detailed.actionable_insights
            },
            source_task_id: task.id,
            extraction_method: 'dual_output_extraction',
            validation_score: 0.95,
            actionability_score: 0.9,
            ready_to_use: true,
            usage_instructions: detailed.visual_summary || 'AI-generated business asset ready for immediate use'
          };
          
          extractedAssets[assetName] = dualOutputAsset;
          
          if (process.env.NODE_ENV === 'development') {
            console.log(`✅ [RAW TASK EXTRACTION] Extracted dual output asset: ${assetName}`, {
              hasStructuredContent: !!detailed.structured_content,
              hasRenderedHtml: !!detailed.rendered_html,
              taskName: task.name
            });
          }
        }
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          console.log('🔍 [RAW TASK EXTRACTION] Failed to parse detailed_results_json:', e);
        }
      }
    }
    
    if (!contextData) return;
    
    // 🎯 PRIMARY LOCATION: context_data.precomputed_deliverable.actionable_assets
    if (contextData.precomputed_deliverable?.actionable_assets) {
      Object.entries(contextData.precomputed_deliverable.actionable_assets).forEach(([key, asset]) => {
        if (asset && typeof asset === 'object') {
          extractedAssets[key] = {
            ...asset,
            source_task_id: task.id,
            extraction_method: 'precomputed_deliverable'
          } as ActionableAsset;
        }
      });
    }
    
    // 🎯 SECONDARY LOCATION: Direct context_data assets
    if (contextData.actionable_assets) {
      Object.assign(extractedAssets, contextData.actionable_assets);
    }
    
    // 🎯 TERTIARY: Final deliverable task results
    if ((contextData.is_final_deliverable || contextData.deliverable_aggregation) && task.result) {
      if (task.result.actionable_assets) {
        Object.assign(extractedAssets, task.result.actionable_assets);
      }
      
      // ✅ NEW: Check for dual output format first
      if (task.result.detailed_results_json) {
        try {
          const detailed = typeof task.result.detailed_results_json === 'string' 
            ? JSON.parse(task.result.detailed_results_json)
            : task.result.detailed_results_json;
          
          // Check for new dual output format
          if (detailed.structured_content) {
            // Create asset from structured content
            const assetName = task.name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
            const dualOutputAsset: ActionableAsset = {
              asset_name: assetName,
              asset_data: {
                structured_content: detailed.structured_content,
                rendered_html: detailed.rendered_html,
                visual_summary: detailed.visual_summary,
                actionable_insights: detailed.actionable_insights
              },
              source_task_id: task.id,
              extraction_method: 'dual_output_extraction',
              validation_score: 0.95,
              actionability_score: 0.9,
              ready_to_use: true,
              usage_instructions: detailed.visual_summary || 'AI-generated business asset ready for immediate use'
            };
            
            extractedAssets[assetName] = dualOutputAsset;
            
            if (process.env.NODE_ENV === 'development') {
              console.log(`✅ [RAW TASK EXTRACTION] Extracted dual output asset: ${assetName}`, {
                hasStructuredContent: !!detailed.structured_content,
                hasRenderedHtml: !!detailed.rendered_html,
                taskName: task.name
              });
            }
          }
          // Fallback to old format
          else if (detailed.actionable_assets) {
            Object.assign(extractedAssets, detailed.actionable_assets);
          }
        } catch (e) {
          if (process.env.NODE_ENV === 'development') {
            console.log('🔍 [RAW TASK EXTRACTION] Failed to parse detailed_results_json:', e);
          }
        }
      }
    }
  });
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔍 [RAW TASK EXTRACTION] Total assets extracted: ${Object.keys(extractedAssets).length}`);
  }
  
  return extractedAssets;
};

// 🔍 Deliverable Assets Extraction (fallback method)
const extractDeliverablesAssets = (deliverables: ProjectDeliverablesExtended): Record<string, ActionableAsset> => {
  const extractedAssets: Record<string, ActionableAsset> = {};
  
  if (!deliverables.key_outputs) return extractedAssets;
  
  deliverables.key_outputs.forEach((output) => {
    // Direct actionable_assets
    if (output.actionable_assets && Object.keys(output.actionable_assets).length > 0) {
      Object.assign(extractedAssets, output.actionable_assets);
    }
    
    // Result actionable_assets
    if (output.result?.actionable_assets && Object.keys(output.result.actionable_assets).length > 0) {
      Object.assign(extractedAssets, output.result.actionable_assets);
    }
    
    // For final deliverables, create synthetic assets from structured content
    if (output.type === 'final_deliverable' && output.summary) {
      const syntheticAsset: ActionableAsset = {
        asset_name: `executive_summary_${output.task_id}`,
        asset_data: {
          executive_summary: output.summary,
          key_insights: output.key_insights || [],
          metrics: output.metrics || {},
          recommendations: output.next_steps || [],
          full_output: output.output
        },
        source_task_id: output.task_id,
        extraction_method: 'synthetic_deliverable',
        validation_score: 0.9,
        actionability_score: 0.8,
        ready_to_use: true,
        usage_instructions: 'Executive summary with actionable insights from final deliverable'
      };
      
      extractedAssets[syntheticAsset.asset_name] = syntheticAsset;
    }
  });
  
  return extractedAssets;
};

// Main Hook Implementation
export const useAssetManagement = (workspaceId: string): UseAssetManagementReturn => {
  const [state, setState] = useState<AssetManagementState>({
    tracking: null,
    requirements: null,
    schemas: {},
    extractionStatus: null,
    deliverables: null,
    finalDeliverables: [],
    deliverableAssets: {},
    processedAssets: [],
    loading: true,
    error: null,
  });

  const debugLog = useCallback((message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔍 [useAssetManagement] ${message}`, data || '');
    }
  }, []);

  const fetchAssetData = useCallback(async () => {
    if (!workspaceId) {
      debugLog('No workspaceId provided, skipping fetch');
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      debugLog(`Starting comprehensive fetch for workspace: ${workspaceId}`);

      // 🚀 Parallel fetch of all required data
      const [
        trackingResult,
        requirementsResult, 
        schemasResult,
        extractionResult,
        deliverablesResult,
        rawTasksResult
      ] = await Promise.allSettled([
        api.monitoring.getAssetTracking(workspaceId),
        api.assetManagement.getRequirements(workspaceId),
        api.assetManagement.getSchemas(workspaceId),
        api.assetManagement.getExtractionStatus(workspaceId),
        api.monitoring.getProjectDeliverables(workspaceId),
        // Reduced limit to improve performance
        api.monitoring.getWorkspaceTasks(workspaceId, { limit: 50 })
      ]);

      // Extract successful results
      const tracking = trackingResult.status === 'fulfilled' ? trackingResult.value : null;
      const requirements = requirementsResult.status === 'fulfilled' ? requirementsResult.value : null;
      const schemasResponse = schemasResult.status === 'fulfilled' ? schemasResult.value : null;
      const extractionStatus = extractionResult.status === 'fulfilled' ? extractionResult.value : null;
      const deliverables = deliverablesResult.status === 'fulfilled' ? deliverablesResult.value : null;
      const finalDeliverables = deliverables?.key_outputs
        ? deliverables.key_outputs.filter(output =>
            output.type === 'final_deliverable' || output.category === 'final_deliverable'
          )
        : [];
      const rawTasksResponse = rawTasksResult.status === 'fulfilled' ? rawTasksResult.value : null;

      const schemas = schemasResponse?.available_schemas || {};
      
      if (process.env.NODE_ENV === 'development') {
        debugLog('API Results received:', {
          hasTracking: !!tracking,
          hasRequirements: !!requirements,
          schemasCount: Object.keys(schemas).length,
          hasExtraction: !!extractionStatus,
          hasDeliverables: !!deliverables,
          hasRawTasksResponse: !!rawTasksResponse,
          trackingAssets: tracking?.asset_summary?.total_asset_tasks || 0,
          rawTasksCount: Array.isArray(rawTasksResponse) ? rawTasksResponse.length : rawTasksResponse?.tasks?.length || 0
        });
      }

      // 🎯 PRIMARY ASSET EXTRACTION: From Raw Tasks
      let extractedAssets: Record<string, ActionableAsset> = {};
      
      if (rawTasksResponse) {
        let tasksArray: Task[] = [];
        
        if (Array.isArray(rawTasksResponse)) {
          tasksArray = rawTasksResponse;
        } else if (rawTasksResponse.tasks && Array.isArray(rawTasksResponse.tasks)) {
          tasksArray = rawTasksResponse.tasks;
        }
          
        if (tasksArray.length > 0) {
          extractedAssets = extractAssetsFromRawTasks(tasksArray);
          debugLog(`✅ Processing ${tasksArray.length} raw tasks for context_data assets`);
        }
      }
      
      // 🎯 SECONDARY EXTRACTION: From Deliverables (if raw tasks failed)
      if (Object.keys(extractedAssets).length === 0 && deliverables) {
        const deliverableAssets = extractDeliverablesAssets(deliverables);
        Object.assign(extractedAssets, deliverableAssets);
        debugLog('No assets from raw tasks, using deliverables extraction');
      }

      // 🔄 Process assets into display format
      const processedAssets: AssetDisplayData[] = [];
      
      Object.entries(extractedAssets).forEach(([assetName, asset]) => {
        // Find corresponding task info from tracking
        const taskInfo: AssetTaskInfo = tracking?.completed_assets?.find(
          t => t.task_id === asset.source_task_id
        ) || {
          task_id: asset.source_task_id,
          task_name: asset.asset_name,
          asset_type: assetName,
          status: 'completed',
          agent_role: 'System'
        };

        processedAssets.push({
          asset,
          task_info: taskInfo,
          schema: schemas[assetName] || schemas[asset.asset_name]
        });
      });

      // 🔄 Add tracking assets that weren't found in extraction
      if (tracking?.completed_assets) {
        tracking.completed_assets.forEach(completedAsset => {
          const alreadyExists = processedAssets.some(
            p => p.task_info.task_id === completedAsset.task_id
          );
          
          if (!alreadyExists) {
            // Create placeholder asset
            const placeholderAsset: ActionableAsset = {
              asset_name: completedAsset.asset_type || `asset_${completedAsset.task_id.substring(0, 8)}`,
              asset_data: {
                status: 'Asset completed - awaiting final extraction',
                task_name: completedAsset.task_name,
                note: 'This asset will be available in the final deliverable'
              },
              source_task_id: completedAsset.task_id,
              extraction_method: 'tracking_placeholder',
              validation_score: 0.7,
              actionability_score: 0.5,
              ready_to_use: false,
              usage_instructions: 'Asset completed but pending final extraction'
            };

            processedAssets.push({
              asset: placeholderAsset,
              task_info: completedAsset,
              schema: schemas[completedAsset.asset_type || '']
            });
          }
        });
      }

      debugLog(`Total processed assets: ${processedAssets.length}`);

      // 🎯 Update state
      setState({
        tracking,
        requirements,
        schemas,
        extractionStatus,
        deliverables,
        finalDeliverables,
        deliverableAssets: extractedAssets,
        processedAssets,
        loading: false,
        error: null,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load asset data';
      debugLog('Fatal error:', err);
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, [workspaceId, debugLog]);

  // 🚀 Trigger asset analysis
  const triggerAssetAnalysis = useCallback(async () => {
    try {
      debugLog('Triggering asset analysis...');
      await api.projects.triggerAssetAnalysis(workspaceId);
      
      // Refresh data after analysis
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

  // 🔍 Check deliverable readiness
  const checkDeliverableReadiness = useCallback(async () => {
    try {
      const readiness = await api.monitoring.getDeliverableReadiness(workspaceId);
      return readiness.is_ready_for_deliverable;
    } catch (error) {
      debugLog('Could not check deliverable readiness:', error);
      return false;
    }
  }, [workspaceId]);

  // 📊 Computed values and helpers
  const getAssetProgress = useCallback((): AssetProgress => {
    if (!state.tracking?.asset_summary) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    
    const { completed_asset_tasks = 0, total_asset_tasks = 0 } = state.tracking.asset_summary;
    
    return {
      completed: completed_asset_tasks,
      total: total_asset_tasks,
      percentage: total_asset_tasks > 0 ? (completed_asset_tasks / total_asset_tasks) * 100 : 0,
    };
  }, [state.tracking]);

  const getAssetsByType = useCallback((assetType: string): AssetDisplayData[] => {
    return state.processedAssets.filter(asset => 
      asset.asset.asset_name === assetType || 
      asset.task_info.asset_type === assetType
    );
  }, [state.processedAssets]);

  const isDeliverableReady = useCallback((): boolean => {
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

  const getAssetTypeProgress = useCallback((assetType: string): AssetProgress => {
    if (!state.tracking?.asset_types_breakdown) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    
    const typeData = state.tracking.asset_types_breakdown[assetType];
    if (!typeData) return { completed: 0, total: 0, percentage: 0 };
    
    const { completed = 0, total = 0 } = typeData;
    
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
    
    const contextData = task.context_data as EnhancedTaskContextData;
    if (contextData?.asset_production || contextData?.asset_oriented_task) {
      return true;
    }
    
    // Check task name patterns
    const taskName = task.name || '';
    if (taskName.includes('PRODUCE ASSET:') || taskName.includes('Create Final')) {
      return true;
    }
    
    // Check if task is in tracking data
    if (state.tracking) {
      const allAssetTasks = [
        ...(state.tracking.completed_assets || []),
        ...(state.tracking.pending_assets || [])
      ];
      return allAssetTasks.some(assetTask => assetTask.task_id === task.id);
    }
    
    return false;
  }, [state.tracking]);

  const getAssetTypeFromTask = useCallback((task: any): string | null => {
    if (!task) return null;
    
    const contextData = task.context_data as EnhancedTaskContextData;
    if (contextData?.asset_type || contextData?.detected_asset_type) {
      return contextData.asset_type || contextData.detected_asset_type;
    }
    
    // Check tracking data for asset type
    if (state.tracking) {
      const allAssetTasks = [
        ...(state.tracking.completed_assets || []),
        ...(state.tracking.pending_assets || [])
      ];
      
      const assetTask = allAssetTasks.find(assetTask => assetTask.task_id === task.id);
      if (assetTask?.asset_type) {
        return assetTask.asset_type;
      }
    }
    
    // Infer from task name
    const taskName = task.name?.toLowerCase() || '';
    if (taskName.includes('calendar')) return 'content_calendar';
    if (taskName.includes('contact') || taskName.includes('database')) return 'contact_database';
    if (taskName.includes('strategy')) return 'strategy_document';
    if (taskName.includes('analysis')) return 'analysis_report';
    
    return null;
  }, [state.tracking]);

  const getAssetCompletionStats = useCallback((): AssetCompletionStats => {
    if (!state.tracking?.asset_summary) {
      return {
        totalAssets: 0,
        completedAssets: 0,
        pendingAssets: 0,
        completionRate: 0,
        isDeliverableReady: false,
      };
    }
    
    const {
      total_asset_tasks = 0,
      completed_asset_tasks = 0,
      pending_asset_tasks = 0,
      completion_rate = 0,
      deliverable_ready = false
    } = state.tracking.asset_summary;
    
    return {
      totalAssets: total_asset_tasks,
      completedAssets: completed_asset_tasks,
      pendingAssets: pending_asset_tasks,
      completionRate: completion_rate,
      isDeliverableReady: deliverable_ready,
    };
  }, [state.tracking]);

  // 🎯 Initialize data fetching
  useEffect(() => {
    debugLog('Hook initialized, starting initial fetch');
    fetchAssetData();
  }, [fetchAssetData]);

  // 🔄 Extracted arrays for easy access
  const assets = state.processedAssets.map(p => p.asset);
  const assetDisplayData = state.processedAssets;

  return {
    // Direct access to structured data
    tracking: state.tracking,
    requirements: state.requirements,
    schemas: state.schemas,
    extractionStatus: state.extractionStatus,

    deliverables: state.deliverables,
    finalDeliverables: state.finalDeliverables,
    
    // Direct access to processed assets
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