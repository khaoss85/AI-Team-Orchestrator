// frontend/src/utils/api.ts - COMPLETE ENHANCED VERSION WITH ASSET MANAGEMENT

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
  ExecutorDetailedStats,
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

// Determina l'URL base dell'API in base all'ambiente
const getBaseUrl = () => {
  // Controlla se il codice viene eseguito nel browser
  if (typeof window !== 'undefined') {
    // Se siamo in localhost, punta a localhost:8000
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
  
  // 🆕 NEW: Asset Management API
  assetManagement: {
    getRequirements: async (workspaceId: string): Promise<{
      workspace_id: string;
      deliverable_category: string;
      primary_assets_needed: AssetRequirement[];
      deliverable_structure: Record<string, any>;
      generated_at: string;
    }> => {
      try {
        const response = await fetch(`${API_BASE_URL}/asset-management/workspace/${workspaceId}/requirements`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
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
        const response = await fetch(`${API_BASE_URL}/asset-management/workspace/${workspaceId}/schemas`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
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
        const response = await fetch(`${API_BASE_URL}/asset-management/workspace/${workspaceId}/extraction-status`);
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
    
    // 🆕 ENHANCED: Project Deliverables with Asset Support
    getProjectDeliverables: async (workspaceId: string): Promise<ProjectDeliverablesExtended> => {
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/deliverables`);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        
        // 🆕 Enhanced validation and transformation for assets
        const transformedData: ProjectDeliverablesExtended = {
          ...data,
          key_outputs: data.key_outputs.map((output: any) => ({
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
            // 🆕 NEW: Asset-specific fields
            actionable_assets: output.actionable_assets || {},
            actionability_score: output.actionability_score || 0,
            automation_ready: output.automation_ready || false,
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

    getExecutorDetailedStats: async (): Promise<ExecutorDetailedStats> => {
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/executor/detailed-stats`);
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
          // Prepara i dati da inviare, assicurandoti che i campi specializzati vengano gestiti correttamente
          const updateData: any = { ...data };

          // Rimuovi campi che non devono essere inviati
          delete updateData.id;
          delete updateData.workspace_id;
          delete updateData.created_at;
          delete updateData.updated_at;

          // Assicurati che le strutture nidificate vengano serializzate correttamente se inviate come stringhe
          if (updateData.personality_traits && Array.isArray(updateData.personality_traits)) {
            updateData.personality_traits = updateData.personality_traits.map(trait => 
              typeof trait === 'object' ? trait.value || trait.toString() : trait);
          }

          // Stessa cosa per le skills
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

          // Se communication_style è un oggetto enum, prendi il suo valore stringa
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
  },
  
  // API Director
  director: {
    createProposal: async (config: DirectorConfig): Promise<DirectorTeamProposal> => {
      try {
        const response = await fetch(`${API_BASE_URL}/director/proposal`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    approveProposal: async (workspaceId: string, proposalId: string): Promise<any> => {
      try {
        const response = await fetch(`${API_BASE_URL}/director/approve/${workspaceId}?proposal_id=${proposalId}`, {
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
};