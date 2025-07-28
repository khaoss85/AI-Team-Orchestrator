// frontend/src/utils/api.ts - COMPLETE ENHANCED VERSION WITH ALL MISSING METHODS

import {
  Workspace,
  WorkspaceCreateData,
  Agent,
  AgentCreateData,
  Task,
  TaskCreateData,
  TaskAnalysisResponse,
  DirectorConfig,
  DirectorTeamProposal,
  Handoff,
  FeedbackRequest, 
  FeedbackResponse,
  ProjectDeliverables, 
  DeliverableFeedback,
  ProjectDeliverablesExtended,
  ProjectOutputExtended,
  ExecutorStatus,
  CustomTool,
  CustomToolCreate,
} from '@/types';

// 🆕 NEW: Asset Management Types
export interface AssetRequirement {
  asset_type: string;
  asset_format: 'structured_data' | 'document' | 'spreadsheet';
  actionability_level: 'ready_to_use' | 'needs_customization' | 'template';
  business_impact: 'immediate' | 'short_term' | 'strategic';
  priority: number;
  validation_criteria: string[];
}

export interface AssetSchema {
  asset_name: string;
  schema_definition: Record<string, any>;
  validation_rules: string[];
  usage_instructions: string;
  automation_ready: boolean;
}

export interface ActionableAsset {
  asset_name: string;
  asset_data: Record<string, any>;
  source_task_id: string;
  validation_score: number;
  actionability_score: number;
  ready_to_use: boolean;
  usage_instructions?: string;
  file_download_url?: string;
}

export interface AssetTrackingData {
  workspace_id: string;
  asset_summary: {
    total_asset_tasks: number;
    completed_asset_tasks: number;
    pending_asset_tasks: number;
    completion_rate: number;
    deliverable_ready: boolean;
  };
  asset_types_breakdown: Record<string, {
    total: number;
    completed: number;
  }>;
  completed_assets: AssetTaskInfo[];
  pending_assets: AssetTaskInfo[];
  analysis_timestamp: string;
}

export interface AssetTaskInfo {
  task_id: string;
  task_name: string;
  asset_type?: string;
  status: string;
  agent_role?: string;
  created_at?: string;
  updated_at?: string;
}

// 🆕 NEW: Project-specific API Response Types
export interface ProjectAssetAnalysisResponse {
  success: boolean;
  message: string;
  workspace_id: string;
  analysis_results: {
    deliverable_category: string;
    assets_needed: number;
    asset_types: string[];
  };
  triggered_at: string;
}

export interface FinalizationResponse {
  success: boolean;
  message: string;
  workspace_id: string;
  finalization_type: 'normal' | 'forced';
  deliverable_id?: string;
  created_at: string;
}

export interface WorkspaceTasksResponse {
  workspace_id: string;
  tasks: Task[];
  total_count: number;
  completed_count: number;
  pending_count: number;
  failed_count: number;
  asset_tasks_count: number;
  last_updated: string;
}

// Determina l'URL base dell'API in base all'ambiente
const getBaseUrl = () => {
  // Controlla se il codice viene eseguito nel browser
  if (typeof window !== 'undefined') {
    // Se siamo in localhost, punta a localhost:8000 (main server)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  
  // Altrimenti usa l'URL configurato o il fallback
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getBaseUrl();

// Helper per gestire gli errori delle chiamate API
const handleApiError = (error: unknown) => {
  console.error('API Error:', error);
  throw error;
};

export const api = {
  getBaseUrl,
  
  // 🆕 UNIFIED: Asset Management API (Updated to use unified-assets endpoints)
  assetManagement: {
    // Legacy endpoints replaced with unified assets
    getRequirements: async (workspaceId: string): Promise<{
      workspace_id: string;
      deliverable_category: string;
      primary_assets_needed: AssetRequirement[];
      deliverable_structure: Record<string, any>;
      generated_at: string;
    }> => {
      try {
        // Use unified assets endpoint and extract requirements from response
        const unifiedAssets = await api.assetManagement.getUnifiedAssets(workspaceId);
        return {
          workspace_id: workspaceId,
          deliverable_category: "unified_assets",
          primary_assets_needed: Object.keys(unifiedAssets.assets || {}).map(key => ({
            asset_name: key,
            asset_type: unifiedAssets.assets[key]?.type || "unknown",
            priority: "high",
            description: `Asset: ${unifiedAssets.assets[key]?.name || key}`
          })),
          deliverable_structure: unifiedAssets.assets || {},
          generated_at: unifiedAssets.processing_timestamp || new Date().toISOString()
        };
      } catch (error) {
        return handleApiError(error);
      }
    },

    getSchemas: async (workspaceId: string): Promise<{
      workspace_id: string;
      available_schemas: Record<string, AssetSchema>;
      schema_count: number;
      generated_at: string;
    }> => {
      try {
        // Use unified assets endpoint and extract schemas from response
        const unifiedAssets = await api.assetManagement.getUnifiedAssets(workspaceId);
        const schemas: Record<string, AssetSchema> = {};
        
        Object.entries(unifiedAssets.assets || {}).forEach(([key, asset]: [string, any]) => {
          schemas[key] = {
            asset_name: asset.name || key,
            asset_type: asset.type || "unknown",
            required_fields: Object.keys(asset.content?.structured_content || {}),
            validation_rules: asset.quality_scores || {},
            example_structure: asset.content?.structured_content || {}
          };
        });

        return {
          workspace_id: workspaceId,
          available_schemas: schemas,
          schema_count: Object.keys(schemas).length,
          generated_at: unifiedAssets.processing_timestamp || new Date().toISOString()
        };
      } catch (error) {
        return handleApiError(error);
      }
    },

    getExtractionStatus: async (workspaceId: string): Promise<{
      workspace_id: string;
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
        output_size: number;
        extraction_ready: boolean;
        completed_at: string;
      }>;
      next_steps: string[];
      analyzed_at: string;
    }> => {
      try {
        // Use unified assets endpoint and derive extraction status
        const unifiedAssets = await api.assetManagement.getUnifiedAssets(workspaceId);
        const tasks = await api.monitoring.getWorkspaceTasks(workspaceId, { limit: 100 });
        const completedTasks = tasks.tasks?.filter((t: any) => t.status === 'completed') || [];
        
        return {
          workspace_id: workspaceId,
          extraction_summary: {
            total_completed_tasks: completedTasks.length,
            asset_production_tasks: Object.keys(unifiedAssets.assets || {}).length,
            extraction_ready_tasks: completedTasks.length,
            extraction_readiness_rate: completedTasks.length > 0 ? (Object.keys(unifiedAssets.assets || {}).length / completedTasks.length) : 0
          },
          extraction_candidates: completedTasks.map((task: any) => ({
            task_id: task.id,
            task_name: task.name,
            asset_type: "unified_asset",
            has_structured_output: true,
            output_size: JSON.stringify(task.result || {}).length,
            extraction_ready: true,
            completed_at: task.completed_at || task.updated_at || new Date().toISOString()
          })),
          next_steps: ["Assets ready for use", "Review asset quality scores"],
          analyzed_at: unifiedAssets.processing_timestamp || new Date().toISOString()
        };
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 UNIFIED: Get unified assets (main endpoint)
    getUnifiedAssets: async (workspaceId: string): Promise<{
      workspace_id: string;
      workspace_goal: string;
      assets: Record<string, any>;
      asset_count: number;
      total_versions: number;
      processing_timestamp: string;
      data_source: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/unified-assets/workspace/${workspaceId}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 UNIFIED: Refresh unified assets
    refreshUnifiedAssets: async (workspaceId: string): Promise<{
      workspace_id: string;
      workspace_goal: string;
      assets: Record<string, any>;
      asset_count: number;
      total_versions: number;
      processing_timestamp: string;
      data_source: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/unified-assets/workspace/${workspaceId}/refresh`, {
          method: 'POST'
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

  },
  
  // Enhanced Monitoring API with Asset Support
  monitoring: {
    getWorkspaceActivity: async (workspaceId: string, limit: number = 20): Promise<any[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/activity?limit=${limit}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    getWorkspaceBudget: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/budget`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getAgentBudget: async (agentId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/agent/${agentId}/budget`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    getWorkspaceStatus: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/status`);
         if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Get workspace tasks with enhanced filtering
    getWorkspaceTasks: async (
      workspaceId: string, 
      options?: {
        status?: string;
        agent_id?: string;
        asset_only?: boolean;
        limit?: number;
        offset?: number;
      }
    ): Promise<WorkspaceTasksResponse> => {
      try {
        const params = new URLSearchParams();
        if (options?.status) params.append('status', options.status);
        if (options?.agent_id) params.append('agent_id', options.agent_id);
        if (options?.asset_only) params.append('asset_only', 'true');
        if (options?.limit) params.append('limit', options.limit.toString());
        if (options?.offset) params.append('offset', options.offset.toString());

        const url = `${API_BASE_URL}/monitoring/workspace/${workspaceId}/tasks${params.toString() ? `?${params.toString()}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    startTeam: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/start`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    // Get enhanced task result with structured content
    getEnhancedTaskResult: async (workspaceId: string, taskId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/task/${taskId}/enhanced-result`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    // 🆕 ENHANCED: Project Deliverables with Asset Support and Goal Filtering
    getProjectDeliverables: async (workspaceId: string, goalId?: string): Promise<ProjectDeliverablesExtended> => {
      try {
        const url = goalId 
          ? `${API_BASE_URL}/api/deliverables/workspace/${workspaceId}?goal_id=${goalId}`
          : `${API_BASE_URL}/api/deliverables/workspace/${workspaceId}`;
        const response = await fetch(url);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        
        // Ensure data is valid
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid response data from deliverables API');
        }
        
        // 🆕 Enhanced validation and transformation for assets
        const transformedData: ProjectDeliverablesExtended = {
          workspace_id: workspaceId,
          project_name: data.project_name || '',
          status: data.status || 'unknown',
          completion_percentage: data.completion_percentage || 0,
          total_tasks: data.total_tasks || 0,
          completed_tasks: data.completed_tasks || 0,
          created_at: data.created_at || new Date().toISOString(),
          updated_at: data.updated_at || new Date().toISOString(),
          ...data,
          key_outputs: (data.key_outputs || []).map((output: any) => ({
            ...output,
            created_at: typeof output.created_at === 'string' 
              ? output.created_at 
              : new Date(output.created_at).toISOString(),
            // Assicura che i campi opzionali esistano
            key_insights: output.key_insights || [],
            metrics: output.metrics || {},
            title: output.title || output.task_name,
            description: output.description || '',
            category: output.category || 'general',
            // Preserve important classification fields
            type: output.type,
            // 🆕 NEW: Asset-specific fields
            actionable_assets: output.actionable_assets || {},
            actionability_score: output.actionability_score || 0,
            automation_ready: output.automation_ready || false,
            // Add visual_summary if available
            visual_summary: output.visual_summary || null,
          }))
        };
        
        return transformedData;
      } catch (error) {
        console.error('Error fetching deliverables:', error);
        return handleApiError(error);
      }
    },

    // Metodo specifico per recuperare solo deliverable finali
    getFinalDeliverables: async (workspaceId: string): Promise<ProjectOutputExtended[]> => {
      try {
        const deliverables = await api.monitoring.getProjectDeliverables(workspaceId);
        return deliverables.key_outputs.filter(output => 
          output.type === 'final_deliverable' || output.category === 'final_deliverable'
        );
      } catch (error) {
        console.error('Error fetching final deliverables:', error);
        return handleApiError(error);
      }
    },

    // Metodo per verificare se ci sono deliverable finali pronti
    checkFinalDeliverablesStatus: async (workspaceId: string): Promise<{
      hasFinalDeliverables: boolean;
      count: number;
      deliverables: ProjectOutputExtended[];
    }> => {
      try {
        const finalDeliverables = await api.monitoring.getFinalDeliverables(workspaceId);
        return {
          hasFinalDeliverables: finalDeliverables.length > 0,
          count: finalDeliverables.length,
          deliverables: finalDeliverables
        };
      } catch (error) {
        console.error('Error checking final deliverables status:', error);
        return {
          hasFinalDeliverables: false,
          count: 0,
          deliverables: []
        };
      }
    },

    // 🎯 NEW: Goal-specific deliverable methods
    getGoalDeliverables: async (workspaceId: string, goalId: string): Promise<any[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/deliverables/workspace/${workspaceId}/goal/${goalId}`);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching goal deliverables:', error);
        return handleApiError(error);
      }
    },

    createGoalDeliverable: async (workspaceId: string, goalId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/deliverables/workspace/${workspaceId}/goal/${goalId}/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        return await response.json();
      } catch (error) {
        console.error('Error creating goal deliverable:', error);
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Trigger final deliverable creation
    triggerFinalDeliverable: async (workspaceId: string): Promise<FinalizationResponse> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/deliverables/workspace/${workspaceId}/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Force project finalization (emergency)
    forceFinalization: async (workspaceId: string, reason?: string): Promise<FinalizationResponse> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/deliverables/workspace/${workspaceId}/force-finalize`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            reason: reason || 'Manual forced finalization',
            force_incomplete: true 
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  
    submitDeliverableFeedback: async (workspaceId: string, feedback: DeliverableFeedback): Promise<any> => {
        try {
          const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/deliverables/feedback`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(feedback),
          });
          if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
          return await response.json();
        } catch (error) {
          return handleApiError(error);
        }
    },
    
    getGlobalActivity: async (limit: number = 50): Promise<any[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/global/activity?limit=${limit}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getTaskAnalysis: async (workspaceId: string): Promise<TaskAnalysisResponse> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/task-analysis`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resetRunawayTasks: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/reset-runaway`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Fetch detailed output for a single task
    getTaskResult: async (workspaceId: string, taskId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/output/${taskId}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    pauseExecutor: async (): Promise<{ message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/executor/pause`, {
          method: 'POST',
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: `API error: ${response.status}` }));
          throw new Error(errorData.detail || `API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resumeExecutor: async (): Promise<{ message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/executor/resume`, {
          method: 'POST',
        });
         if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: `API error: ${response.status}` }));
          throw new Error(errorData.detail || `API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getExecutorStatus: async (): Promise<ExecutorStatus> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/executor/status`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

        
    getRunawayProtectionStatus: async (): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/runaway-protection/status`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    triggerRunawayCheck: async (): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/runaway-protection/check`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resumeWorkspaceAutoGeneration: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/resume-auto-generation`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getWorkspaceHealth: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/health`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 NEW: Workspace health status monitoring
    getWorkspaceHealthStatus: async (workspaceId: string): Promise<{
      workspace_id: string;
      status: 'healthy' | 'needs_intervention' | 'critical';
      is_blocked: boolean;
      last_activity: string;
      health_score: number;
      issues: Array<{
        type: string;
        severity: 'low' | 'medium' | 'high' | 'critical';
        description: string;
        detected_at: string;
        auto_resolvable: boolean;
      }>;
      blocked_reasons: string[];
      resolution_suggestions: string[];
      performance_metrics: {
        task_velocity: number;
        agent_utilization: number;
        error_rate: number;
        avg_task_duration: number;
      };
      last_checked: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/health-status`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 NEW: Manual workspace unblock
    unblockWorkspace: async (workspaceId: string, reason?: string): Promise<{
      success: boolean;
      message: string;
      previous_status: string;
      new_status: string;
      unblocked_at: string;
      reason: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/unblock`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: reason || 'Manual unblock from frontend' }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 NEW: Resume auto-generation for workspace
    resumeAutoGeneration: async (workspaceId: string): Promise<{
      success: boolean;
      message: string;
      actions_taken: string[];
      workspace_id: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/resume-auto-generation`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 NEW: Asset Tracking
    getAssetTracking: async (workspaceId: string): Promise<AssetTrackingData> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/asset-tracking`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Unified Assets API
    getUnifiedAssets: async (workspaceId: string): Promise<{
      workspace_id: string;
      workspace_goal: string;
      assets: Record<string, any>;
      asset_count: number;
      total_versions: number;
      processing_timestamp: string;
      data_source: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/unified-assets/workspace/${workspaceId}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🆕 NEW: Deliverable Readiness
    getDeliverableReadiness: async (workspaceId: string): Promise<{
      workspace_id: string;
      is_ready_for_deliverable: boolean;
      has_existing_deliverable: boolean;
      readiness_details: {
        total_tasks: number;
        completed_tasks: number;
        pending_tasks: number;
        completion_rate: number;
        asset_tasks: number;
        completed_assets: number;
        asset_completion_rate: number;
      };
      next_action: string;
      checked_at: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/deliverable-readiness`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Finalization status tracking
    getFinalizationStatus: async (workspaceId: string): Promise<{
      finalization_phase_active: boolean;
      finalization_tasks_completed: number;
      final_deliverables_completed: number;
      project_completion_percentage: number;
      next_action_needed: string;
      asset_production_status: {
        asset_tasks_in_finalization: number;
        completed_asset_tasks: number;
        asset_completion_rate: number;
      };
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/workspace/${workspaceId}/finalization-status`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // 🔥 NEW: Projects API Section (was missing)
  projects: {
    // 🔥 NEW: Trigger asset analysis
    triggerAssetAnalysis: async (workspaceId: string): Promise<ProjectAssetAnalysisResponse> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/trigger-asset-analysis`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Enhanced insights endpoint
    getProjectInsights: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/insights`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Asset insights endpoint 
    getAssetInsights: async (workspaceId: string): Promise<{
      workspace_id: string;
      deliverable_category: string;
      requirements_analysis: {
        total_assets_needed: number;
        required_asset_types: string[];
        asset_coverage_rate: number;
        covered_assets: string[];
        missing_assets: string[];
      };
      asset_schemas_available: Record<string, {
        automation_ready: boolean;
        validation_rules_count: number;
        main_fields: string[];
      }>;
      current_asset_tasks: Array<{
        task_id: string;
        name: string;
        status: string;
        asset_type: string;
        agent_role: string;
      }>;
      recommendations: string[];
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/asset-insights`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Enhanced deliverables endpoint 
    getDeliverables: async (workspaceId: string): Promise<ProjectDeliverablesExtended> => {
      // Delegate to monitoring for consistency
      return api.monitoring.getProjectDeliverables(workspaceId);
    },

    // Feedback on deliverables
    submitDeliverableFeedback: async (workspaceId: string, feedback: DeliverableFeedback): Promise<any> => {
      // Delegate to monitoring for consistency
      return api.monitoring.submitDeliverableFeedback(workspaceId, feedback);
    },
  },
      
  // Human Feedback API
  humanFeedback: {
    getPendingRequests: async (workspaceId?: string): Promise<FeedbackRequest[]> => {
      try {
        const url = workspaceId 
          ? `${API_BASE_URL}/human-feedback/pending?workspace_id=${workspaceId}`
          : `${API_BASE_URL}/human-feedback/pending`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    getRequest: async (requestId: string): Promise<FeedbackRequest> => {
      try {
        const response = await fetch(`${API_BASE_URL}/human-feedback/${requestId}`);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    respondToRequest: async (requestId: string, response: FeedbackResponse): Promise<void> => {
      try {
        const apiResponse = await fetch(`${API_BASE_URL}/human-feedback/${requestId}/respond`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(response),
        });
        if (!apiResponse.ok) throw new Error(`API error: ${apiResponse.status}`);
        return await apiResponse.json();
      } catch (error) {
        return handleApiError(error);
      }
    }
  },
      
  // API Workspace
  workspaces: {
    list: async (userId: string): Promise<Workspace[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/user/${userId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    get: async (id: string): Promise<Workspace> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    delete: async (id: string): Promise<boolean> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${id}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        return data.success;
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    create: async (data: WorkspaceCreateData): Promise<Workspace> => {
      try {
        // Transform frontend budget object to backend number format
        const requestData = {
          ...data,
          // Backend expects budget as a simple number, not an object
          budget: data.budget?.max_amount || undefined
        };
        
        const response = await fetch(`${API_BASE_URL}/workspaces`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Update workspace
    update: async (id: string, data: Partial<WorkspaceCreateData>): Promise<Workspace> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (response.status === 404) {
          throw new Error('Aggiornamento progetto non supportato dal backend');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Pause/Resume workspace
    pause: async (id: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/pause`, {
          method: 'POST',
        });
        if (response.status === 404) {
          throw new Error('Funzione di pausa progetto non disponibile');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resume: async (id: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/resume`, {
          method: 'POST',
        });
        if (response.status === 404) {
          throw new Error('Funzione di ripresa progetto non disponibile');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get workspace goals
    getGoals: async (id: string): Promise<{ goals: any[]; summary?: any }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${id}/goals`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Get workspace settings
    getSettings: async (id: string): Promise<{
      success: boolean;
      workspace_id: string;
      settings: {
        quality_threshold: number;
        max_iterations: number;
        max_concurrent_tasks: number;
        task_timeout: number;
        enable_quality_assurance: boolean;
        deliverable_threshold: number;
        max_deliverables: number;
        max_budget: number;
      };
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/settings`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
      
  // Handoffs API
  handoffs: {
    list: async (workspaceId: string): Promise<Handoff[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/handoffs`); 
        if (!response.ok) {
          let errorDetail = `API error: ${response.status}`;
          try {
            const errorData = await response.json();
            if (errorData && errorData.detail) {
              errorDetail = errorData.detail;
            }
          } catch (e) {
            // Non fa niente se il corpo dell'errore non è JSON
          }
          throw new Error(errorDetail);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Create handoff
    create: async (workspaceId: string, handoff: Omit<Handoff, 'id' | 'created_at'>): Promise<Handoff> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/handoffs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(handoff),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Delete handoff
    delete: async (workspaceId: string, handoffId: string): Promise<{ success: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/handoffs/${handoffId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
  
  // API Agents
  agents: {
    list: async (workspaceId: string): Promise<Agent[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    create: async (workspaceId: string, data: AgentCreateData): Promise<Agent> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
        
    update: async (workspaceId: string, agentId: string, data: Partial<AgentCreateData>): Promise<Agent> => {
       try {
          // Prepara i dati da inviare
          const updateData: any = { ...data };

          // Rimuovi campi che non devono essere inviati
          delete updateData.id;
          delete updateData.workspace_id;
          delete updateData.created_at;
          delete updateData.updated_at;

          // Normalizza personality_traits
          if (updateData.personality_traits && Array.isArray(updateData.personality_traits)) {
            updateData.personality_traits = updateData.personality_traits.map(trait => 
              typeof trait === 'object' ? trait.value || trait.toString() : trait);
          }

          // Normalizza skills
          if (updateData.hard_skills && Array.isArray(updateData.hard_skills)) {
            updateData.hard_skills = updateData.hard_skills.map(skill => {
              if (typeof skill === 'object' && skill.level) {
                if (typeof skill.level === 'object') {
                  return { ...skill, level: skill.level.value || skill.level.toString() };
                }
              }
              return skill;
            });
          }

          if (updateData.soft_skills && Array.isArray(updateData.soft_skills)) {
            updateData.soft_skills = updateData.soft_skills.map(skill => {
              if (typeof skill === 'object' && skill.level) {
                if (typeof skill.level === 'object') {
                  return { ...skill, level: skill.level.value || skill.level.toString() };
                }
              }
              return skill;
            });
          }

          // Normalizza communication_style
          if (updateData.communication_style && typeof updateData.communication_style === 'object') {
            updateData.communication_style = updateData.communication_style.value || updateData.communication_style.toString();
          }

          const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/${agentId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData),
          });

          if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
          }

          return await response.json();
        } catch (error) {
          return handleApiError(error);
        }
      },

    // 🔥 NEW: Get single agent
    get: async (workspaceId: string, agentId: string): Promise<Agent> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/${agentId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Delete agent
    delete: async (workspaceId: string, agentId: string): Promise<{ success: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/${agentId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Pause/Resume agent
    pause: async (workspaceId: string, agentId: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/${agentId}/pause`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resume: async (workspaceId: string, agentId: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/${agentId}/resume`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
  
  // API Tasks
  tasks: {
    create: async (workspaceId: string, data: TaskCreateData): Promise<Task> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/tasks`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    execute: async (workspaceId: string, taskId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/execute/${taskId}`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Get single task
    get: async (workspaceId: string, taskId: string): Promise<Task> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/tasks/${taskId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Update task
    update: async (workspaceId: string, taskId: string, data: Partial<TaskCreateData>): Promise<Task> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/tasks/${taskId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Delete task
    delete: async (workspaceId: string, taskId: string): Promise<{ success: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/tasks/${taskId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Reset failed task
    reset: async (workspaceId: string, taskId: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/tasks/${taskId}/reset`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
      
  // API Tool personalizzati
  tools: {
    listCustomTools: async (workspaceId: string): Promise<CustomTool[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/custom/${workspaceId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        return data.tools;
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    createCustomTool: async (toolData: CustomToolCreate): Promise<CustomTool> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/custom`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(toolData),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        return data.tool;
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    deleteCustomTool: async (toolId: string): Promise<boolean> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/custom/${toolId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return true;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Update custom tool
    updateCustomTool: async (toolId: string, toolData: Partial<CustomToolCreate>): Promise<CustomTool> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/custom/${toolId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(toolData),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        return data.tool;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Store data tool
    storeData: async (workspaceId: string, agentId: string, key: string, value: any): Promise<{ success: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/store-data`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            key,
            value,
            workspace_id: workspaceId,
            agent_id: agentId,
          }),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Retrieve data tool
    retrieveData: async (workspaceId: string, key: string): Promise<{ success: boolean; data: any; key: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/retrieve-data/${workspaceId}/${key}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
  
  // API Director
  director: {
    createProposal: async (config: DirectorConfig): Promise<DirectorTeamProposal> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/director/proposal`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        
        // Transform DirectorTeamProposalResponse to DirectorTeamProposal
        if (data.team_members && !data.agents) {
          return {
            id: data.proposal_id,
            workspace_id: config.workspace_id,
            agents: data.team_members,
            handoffs: [],
            estimated_cost: {
              total_estimated_cost: data.estimated_cost || 0
            },
            timeline: data.timeline || "30 days"
          };
        }
        
        return data;
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    approveProposal: async (workspaceId: string, proposalId: string): Promise<any> => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/director/approve/${workspaceId}?proposal_id=${proposalId}`,
          {
            method: 'POST'
          }
        );
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Get proposal details
    getProposal: async (proposalId: string): Promise<DirectorTeamProposal> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/director/proposal/${proposalId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // 🔥 NEW: Reject proposal
    rejectProposal: async (_workspaceId: string, proposalId: string, reason?: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/reject`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ reason: reason || 'No reason provided' }),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // 🔥 NEW: Delegation Analysis API
  delegation: {
    getAnalysis: async (workspaceId: string): Promise<{
      workspace_id: string;
      analysis_timestamp: string;
      summary: {
        total_delegation_attempts: number;
        successful_delegations: number;
        self_executions: number;
        escalations: number;
        failures: number;
        success_rate: number;
        health_score: number;
      };
      role_statistics: Record<string, {
        total_requests: number;
        successful_delegations: number;
        self_executions: number;
        escalations: number;
      }>;
      most_delegated_to: Record<string, number>;
      bottlenecks: Record<string, number>;
      recommendations: string[];
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/delegation/workspace/${workspaceId}/analysis`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  improvement: {
    startLoop: async (taskId: string, payload: Record<string, any>): Promise<{ approved: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/improvement/start/${taskId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getStatus: async (taskId: string): Promise<{ iteration_count: number; max_iterations?: number }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/improvement/status/${taskId}`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    closeLoop: async (taskId: string): Promise<{ closed: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/improvement/close/${taskId}`, { method: 'POST' });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    qaGate: async (taskId: string, payload: Record<string, any>): Promise<{ approved: boolean }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/improvement/qa/${taskId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // Human Interaction API - for human-in-the-loop workflow
  interaction: {
    askQuestion: async (workspaceId: string, question: string, targetAgent?: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/ask-question`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            question,
            target_agent: targetAgent 
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    provideFeedback: async (workspaceId: string, feedback: string, context?: any): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/provide-feedback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            feedback,
            context 
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    requestIteration: async (workspaceId: string, changes: string[]): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/request-iteration`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            changes 
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    approveCompletion: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/approve-completion`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    requestChanges: async (workspaceId: string, changes: string, priority: 'low' | 'medium' | 'high' = 'medium'): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/request-changes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            changes,
            priority 
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // Asset dependency management API endpoints
  assets: {
    // Asset Dependencies
    getDependencies: (assetId: string) =>
      fetch(`${API_BASE_URL}/api/assets/${assetId}/dependencies`).then(res => res.json()),
    
    updateDependencies: (assetId: string, updates: any) =>
      fetch(`${API_BASE_URL}/api/assets/${assetId}/apply-updates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }).then(res => res.json()),
    
    getHistory: (assetId: string, options?: any) =>
      fetch(`${API_BASE_URL}/api/assets/${assetId}/history${options ? `?${new URLSearchParams(options)}` : ''}`).then(res => res.json()),
    
    compareVersions: (assetId: string, fromVersion: string, toVersion: string) =>
      fetch(`${API_BASE_URL}/api/assets/${assetId}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_version: fromVersion, to_version: toVersion }),
      }).then(res => res.json()),
    
    predictImpact: (assetId: string, changeData: any) =>
      fetch(`${API_BASE_URL}/api/assets/${assetId}/predict-impact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changeData),
      }).then(res => res.json()),

    checkDependencies: async (assetId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/assets/${assetId}/dependencies`, {
          method: 'GET',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    applyDependencyUpdates: async (assetId: string, updateRequest: any): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/assets/${assetId}/apply-updates`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateRequest),
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getDependencyGraph: async (workspaceId: string, centralAssetId?: string): Promise<any> => {
      try {
        const url = centralAssetId 
          ? `${API_BASE_URL}/workspaces/${workspaceId}/dependency-graph?central_asset=${centralAssetId}`
          : `${API_BASE_URL}/workspaces/${workspaceId}/dependency-graph`;
        
        const response = await fetch(url, {
          method: 'GET',
        });
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // REMOVED DUPLICATE workspaces object - using the one with budget transformation above
  /*
    // Basic CRUD operations
    list: async (userId: string): Promise<Workspace[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/user/${userId}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    get: async (id: string): Promise<Workspace> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    create: async (data: WorkspaceCreateData): Promise<Workspace> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    update: async (id: string, data: Partial<WorkspaceCreateData>): Promise<Workspace> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (response.status === 404) {
          throw new Error('Aggiornamento progetto non supportato dal backend');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    delete: async (id: string): Promise<boolean> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        return data.success;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Asset management APIs
    getDependencyGraph: (workspaceId: string, options?: any) =>
      fetch(`${API_BASE_URL}/workspaces/${workspaceId}/dependency-graph${options ? `?${new URLSearchParams(options)}` : ''}`).then(res => res.json()),
    
    getAssets: (workspaceId: string, filters?: any) =>
      fetch(`${API_BASE_URL}/workspaces/${workspaceId}/assets${filters ? `?${new URLSearchParams(filters)}` : ''}`).then(res => res.json()),

    // Control operations
    pause: async (id: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/pause`, {
          method: 'POST',
        });
        if (response.status === 404) {
          throw new Error('Funzione di pausa progetto non disponibile');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    resume: async (id: string): Promise<{ success: boolean; message: string }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/resume`, {
          method: 'POST',
        });
        if (response.status === 404) {
          throw new Error('Funzione di ripresa progetto non disponibile');
        }
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Settings
    getSettings: async (id: string): Promise<{
      success: boolean;
      workspace_id: string;
      settings: {
        quality_threshold: number;
        max_iterations: number;
        max_concurrent_tasks: number;
        task_timeout: number;
        enable_quality_assurance: boolean;
        deliverable_threshold: number;
        max_deliverables: number;
        max_budget: number;
      };
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/workspaces/${id}/settings`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
  */

  // Analytics APIs
  analytics: {
    getAssetMetrics: (workspaceId: string, timeRange: string) =>
      fetch(`${API_BASE_URL}/analytics/assets/${workspaceId}/metrics?time_range=${timeRange}`).then(res => res.json()),
    
    getTrendData: (workspaceId: string, timeRange: string) =>
      fetch(`${API_BASE_URL}/analytics/assets/${workspaceId}/trends?time_range=${timeRange}`).then(res => res.json()),
  },

  // Workflow Automation APIs
  workflowAutomation: {
    getRules: (workspaceId: string) =>
      fetch(`${API_BASE_URL}/automation/rules?workspace_id=${workspaceId}`).then(res => res.json()),
    
    createRule: (workspaceId: string, rule: any) =>
      fetch(`${API_BASE_URL}/automation/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...rule, workspace_id: workspaceId }),
      }).then(res => res.json()),
    
    updateRule: (ruleId: string, updates: any) =>
      fetch(`${API_BASE_URL}/automation/rules/${ruleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }).then(res => res.json()),
    
    deleteRule: (ruleId: string) =>
      fetch(`${API_BASE_URL}/automation/rules/${ruleId}`, {
        method: 'DELETE',
      }).then(res => res.json()),
    
    getStats: (workspaceId: string) =>
      fetch(`${API_BASE_URL}/automation/stats?workspace_id=${workspaceId}`).then(res => res.json()),
  },

  // Real-time Updates APIs
  realTime: {
    getConnectionInfo: (workspaceId: string) =>
      fetch(`${API_BASE_URL}/ws/info/${workspaceId}`).then(res => res.json()),
  },

  // 🎯 Goal-Driven System APIs
  goalValidation: {
    // Validate workspace goal achievement
    validateWorkspace: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/goal-validation/${workspaceId}/validate`, {
          method: 'GET',
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Check quality gate for phase transition
    checkQualityGate: async (workspaceId: string, targetPhase: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/goal-validation/${workspaceId}/quality-gate/${targetPhase}`, {
          method: 'GET',
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Check project completion readiness
    checkCompletionReadiness: async (workspaceId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/goal-validation/${workspaceId}/completion-readiness`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Validate specific task against goals
    validateTask: async (workspaceId: string, taskId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/goal-validation/${workspaceId}/validate-task/${taskId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // 🎯 Workspace Goals Management APIs
  workspaceGoals: {
    // Create a new workspace goal
    create: async (workspaceId: string, goalData: any): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(goalData),
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get all goals for a workspace
    getAll: async (workspaceId: string, filters?: { status?: string; metric_type?: string }): Promise<any> => {
      try {
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        if (filters?.metric_type) params.append('metric_type', filters.metric_type);
        
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals?${params.toString()}`);
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Update goal progress
    updateProgress: async (workspaceId: string, goalId: string, progressData: any): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals/${goalId}/progress`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(progressData),
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Update goal details
    update: async (workspaceId: string, goalId: string, goalData: any): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals/${goalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(goalData),
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Delete a goal
    delete: async (workspaceId: string, goalId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals/${goalId}`, {
          method: 'DELETE',
        });
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get unmet goals (for task planning)
    getUnmet: async (workspaceId: string, thresholdPct: number = 80): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/goals/unmet?threshold_pct=${thresholdPct}`);
        return response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },

  // Document Management API
  documents: {
    // Upload a document
    upload: async (
      workspaceId: string,
      fileData: string, // base64
      filename: string,
      sharingScope: string = 'team',
      description?: string,
      tags?: string[]
    ): Promise<{
      success: boolean;
      document: {
        id: string;
        filename: string;
        file_size: number;
        mime_type: string;
        sharing_scope: string;
        vector_store_id: string;
        upload_date: string;
      };
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/documents/${workspaceId}/upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_data: fileData,
            filename,
            sharing_scope: sharingScope,
            description,
            tags
          }),
        });
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // List documents
    list: async (workspaceId: string, scope?: string): Promise<{
      documents: Array<{
        id: string;
        filename: string;
        file_size: number;
        mime_type: string;
        upload_date: string;
        uploaded_by: string;
        sharing_scope: string;
        description?: string;
        tags: string[];
      }>;
      total: number;
    }> => {
      try {
        const url = new URL(`${API_BASE_URL}/documents/${workspaceId}`);
        if (scope) url.searchParams.append('scope', scope);
        
        const response = await fetch(url.toString());
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Delete a document
    delete: async (workspaceId: string, documentId: string): Promise<{
      success: boolean;
      message: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/documents/${workspaceId}/${documentId}`, {
          method: 'DELETE',
        });
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get vector stores
    getVectorStores: async (workspaceId: string): Promise<{
      workspace_id: string;
      vector_store_ids: string[];
      count: number;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/documents/${workspaceId}/vector-stores`);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
  },
};