import {
  Workspace,
  WorkspaceCreateData,
  Agent,
  AgentCreateData,
  Task,
  TaskCreateData,
  DirectorConfig,
  DirectorTeamProposal,
  Handoff,
  FeedbackRequest, 
  FeedbackResponse,
  ProjectDeliverables, 
  DeliverableFeedback
} from '@/types';

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
  
  // API Monitoring
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
    
    getProjectDeliverables: async (workspaceId: string): Promise<ProjectDeliverables> => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${workspaceId}/deliverables`);
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

    getExecutorStatus: async (): Promise<ExecutorStatus> => { // Assicurati che ExecutorStatus sia definito in @/types
      try {
        const response = await fetch(`${API_BASE_URL}/monitoring/executor/status`);
        if (!response.ok) throw new Error(`API error: ${response.status} ${await response.text()}`);
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },

    getExecutorDetailedStats: async (): Promise<ExecutorDetailedStats> => { // Assicurati che ExecutorDetailedStats sia definito
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
      
  // NUOVA SEZIONE PER GLI HANDOFF
  handoffs: {
    list: async (workspaceId: string): Promise<Handoff[]> => {
      try {
        // Assicurati che il path corrisponda all'endpoint definito nel backend
        const response = await fetch(`${API_BASE_URL}/agents/${workspaceId}/handoffs`); 
        if (!response.ok) {
          // Prova a leggere il corpo dell'errore per un messaggio più dettagliato
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
        return handleApiError(error); // handleApiError dovrebbe rilanciare l'errore
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
          // Nota: la trasformazione effettiva dipende da come l'API si aspetta i dati
          if (updateData.personality_traits && Array.isArray(updateData.personality_traits)) {
            // Conserva solo i valori stringa dei personality_traits per evitare problemi di serializzazione
            updateData.personality_traits = updateData.personality_traits.map(trait => 
              typeof trait === 'object' ? trait.value || trait.toString() : trait);
          }

          // Stessa cosa per le skills
          if (updateData.hard_skills && Array.isArray(updateData.hard_skills)) {
            updateData.hard_skills = updateData.hard_skills.map(skill => {
              if (typeof skill === 'object' && skill.level) {
                // Se il livello è un oggetto enum, prendi il suo valore stringa
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
                // Se il livello è un oggetto enum, prendi il suo valore stringa
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
    
    // Instagram API wrappers
    analyzeHashtags: async (hashtags: string[]): Promise<HashtagAnalysis> => {
      try {
        const hashtagsString = hashtags.join(',');
        const response = await fetch(`${API_BASE_URL}/tools/instagram/analyze-hashtags?hashtags=${encodeURIComponent(hashtagsString)}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    analyzeAccount: async (username: string): Promise<AccountAnalysis> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/instagram/analyze-account/${username}`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    },
    
    generateContentIdeas: async (topic: string, targetAudience: string, count: number = 5): Promise<ContentIdea[]> => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/instagram/generate-content-ideas`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            topic,
            target_audience: targetAudience,
            count
          }),
        });
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        return handleApiError(error);
      }
    }
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