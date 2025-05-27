'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import ConfirmModal from '@/components/ConfirmModal';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';
import { useRouter } from 'next/navigation';
import AgentSkillRadarChart, { calculateTeamDimensions } from '@/components/AgentSkillRadarChart';
import AgentDetailRadarSection from '@/components/AgentDetailRadarSection';
import TaskResultDetails from '@/components/TaskResultDetails';
import ProjectActionsSection from '@/components/ProjectActionsSection';
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables';
import { useAssetManagement } from '@/hooks/useAssetManagement'; // 🆕 NEW
import { transformTaskToEnhancedResult } from '@/utils/deliverableHelpers';
import type { ProjectOutputExtended, Task, Agent } from '@/types';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

// 🆕 NEW: Asset Status Widget for Dashboard
const AssetStatusWidget: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const { 
    getAssetCompletionStats, 
    isDeliverableReady, 
    loading: assetLoading,
    error: assetError 
  } = useAssetManagement(workspaceId);

  const assetStats = getAssetCompletionStats();
  const deliverableReady = isDeliverableReady();

  if (assetLoading) {
    return (
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200 animate-pulse">
        <div className="h-4 bg-purple-200 rounded w-1/3 mb-2"></div>
        <div className="h-8 bg-purple-200 rounded"></div>
      </div>
    );
  }

  if (assetError || assetStats.totalAssets === 0) {
    return (
      <div className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-center">
          <span className="text-2xl mr-3">📦</span>
          <div>
            <h4 className="font-medium text-gray-800">Asset Production</h4>
            <p className="text-sm text-gray-600">Nessun asset in produzione</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg p-4 border transition-all duration-300 ${
      deliverableReady 
        ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-lg' 
        : 'bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center">
          <span className="text-2xl mr-3">{deliverableReady ? '🎯' : '📦'}</span>
          <div>
            <h4 className="font-medium text-gray-800">
              {deliverableReady ? 'Asset Pronti!' : 'Asset in Produzione'}
            </h4>
            <p className="text-sm text-gray-600">
              {assetStats.completedAssets}/{assetStats.totalAssets} asset completati
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-indigo-600">
            {Math.round(assetStats.completionRate)}%
          </div>
          {deliverableReady && (
            <div className="text-xs text-green-600 font-medium animate-pulse">
              Deliverable Ready!
            </div>
          )}
        </div>
      </div>
      
      <div className="mt-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              deliverableReady ? 'bg-green-500' : 'bg-indigo-500'
            }`}
            style={{ width: `${assetStats.completionRate}%` }}
          ></div>
        </div>
      </div>
      
      {deliverableReady && (
        <div className="mt-3">
          <Link
            href={`/projects/${workspaceId}/deliverables`}
            className="inline-flex items-center text-sm bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 transition"
          >
            <span className="mr-1">🎯</span>
            Visualizza Asset
          </Link>
        </div>
      )}
    </div>
  );
};

// 🆕 Enhanced Tab Navigation with Asset Indicators
const EnhancedTabNavigation: React.FC<{
  activeSection: string;
  setActiveSection: (section: string) => void;
  projectResults: any[];
  finalDeliverables: any[];
  tasks: any[];
  agents: any[];
  feedbackRequests: any[];
  assetStats: any;
}> = ({ 
  activeSection, 
  setActiveSection, 
  projectResults, 
  finalDeliverables,
  tasks, 
  agents, 
  feedbackRequests,
  assetStats 
}) => {
  const tabs = [
    {
      id: 'results',
      label: '💎 Risultati',
      count: projectResults.length,
      finalCount: finalDeliverables.length,
      assetCount: assetStats.completedAssets
    },
    {
      id: 'plan',
      label: '📋 Piano Attività',
      count: tasks.length,
      pendingCount: tasks.filter(t => t.status === 'pending').length,
      assetTaskCount: tasks.filter(t => 
        t.context_data?.asset_production || 
        t.context_data?.asset_oriented_task
      ).length
    },
    {
      id: 'team',
      label: '👥 Team',
      count: agents.length,
      activeCount: agents.filter(a => a.status === 'active').length
    },
    {
      id: 'details',
      label: '📊 Dettagli & Metriche',
      count: feedbackRequests.length,
      type: 'feedback'
    }
  ];

  return (
    <div className="flex border-b border-gray-200 mb-6 bg-white rounded-lg shadow-sm p-1">
      {tabs.map(tab => (
        <button 
          key={tab.id}
          onClick={() => setActiveSection(tab.id)}
          className={`relative px-4 py-3 font-medium text-sm rounded-md transition-all ${
            activeSection === tab.id
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center space-x-2">
            <span>{tab.label}</span>
            
            {/* Enhanced Count indicators with Asset support */}
            {tab.count > 0 && (
              <div className="flex items-center space-x-1">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  activeSection === tab.id
                    ? 'bg-white bg-opacity-20 text-white'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
                
                {/* Special Asset Indicators */}
                {tab.id === 'results' && tab.finalCount > 0 && (
                  <div className={`relative ${
                    activeSection === tab.id ? '' : 'animate-pulse'
                  }`}>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                      activeSection === tab.id
                        ? 'bg-yellow-400 text-yellow-900'
                        : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                    }`}>
                      🎯 {tab.finalCount}
                    </span>
                    {activeSection !== tab.id && assetStats.completedAssets > 0 && (
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-ping"></div>
                    )}
                  </div>
                )}

                {tab.id === 'results' && tab.assetCount > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    activeSection === tab.id
                      ? 'bg-green-400 text-green-900'
                      : 'bg-green-500 text-white'
                  }`}>
                    📦 {tab.assetCount}
                  </span>
                )}
                
                {tab.id === 'plan' && tab.pendingCount > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    activeSection === tab.id
                      ? 'bg-orange-400 text-orange-900'
                      : 'bg-orange-500 text-white'
                  }`}>
                    ⏳ {tab.pendingCount}
                  </span>
                )}

                {tab.id === 'plan' && tab.assetTaskCount > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    activeSection === tab.id
                      ? 'bg-purple-400 text-purple-900'
                      : 'bg-purple-500 text-white'
                  }`}>
                    🎯 {tab.assetTaskCount}
                  </span>
                )}
                
                {tab.id === 'team' && tab.activeCount > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    activeSection === tab.id
                      ? 'bg-green-400 text-green-900'
                      : 'bg-green-500 text-white'
                  }`}>
                    ⚡ {tab.activeCount}
                  </span>
                )}
                
                {tab.id === 'details' && tab.type === 'feedback' && tab.count > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    activeSection === tab.id
                      ? 'bg-red-400 text-red-900'
                      : 'bg-red-500 text-white animate-pulse'
                  }`}>
                    🚨 {tab.count}
                  </span>
                )}
              </div>
            )}
          </div>
          
          {/* Active indicator line */}
          {activeSection === tab.id && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-white bg-opacity-50 rounded-full"></div>
          )}
        </button>
      ))}
    </div>
  );
};

// Componente per la visualizzazione migliorata dei deliverable finali
function EnhancedFinalDeliverableView({ result }) {
  if (!result || !result.content) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-3">🎯</div>
        <p className="text-gray-500">Deliverable finale non disponibile</p>
      </div>
    );
  }

  const { content } = result;

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-lg border border-indigo-100">
        <h3 className="font-semibold text-indigo-800 text-lg mb-4 flex items-center">
          <span className="text-2xl mr-2">🎯</span>
          Executive Summary
        </h3>
        <div className="text-indigo-900 leading-relaxed bg-white bg-opacity-60 p-5 rounded-lg">
          {content.summary}
        </div>
      </div>

      {/* Key Insights */}
      {content.keyInsights && content.keyInsights.length > 0 && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-lg border border-green-100">
          <h3 className="font-semibold text-green-800 text-lg mb-4 flex items-center">
            <span className="text-2xl mr-2">💡</span>
            Key Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {content.keyInsights.map((insight, index) => (
              <div key={index} className="bg-white bg-opacity-60 p-4 rounded-lg border border-green-200">
                <div className="flex items-start">
                  <span className="bg-green-200 text-green-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-green-900 text-sm">{insight}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics Dashboard */}
      {content.metrics && Object.keys(content.metrics).length > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-6 rounded-lg border border-blue-100">
          <h3 className="font-semibold text-blue-800 text-lg mb-4 flex items-center">
            <span className="text-2xl mr-2">📊</span>
            Project Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(content.metrics).map(([key, values]) => (
              <div key={key} className="bg-white bg-opacity-60 p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-2 capitalize">{key.replace(/_/g, ' ')}</h4>
                <div className="space-y-1">
                  {Array.isArray(values) ? values.map((value, idx) => (
                    <div key={idx} className="text-sm text-blue-700 bg-blue-100 px-2 py-1 rounded">
                      {value}
                    </div>
                  )) : (
                    <div className="text-sm text-blue-700 bg-blue-100 px-2 py-1 rounded">
                      {values}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {content.recommendations && content.recommendations.length > 0 && (
        <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-6 rounded-lg border border-yellow-100">
          <h3 className="font-semibold text-yellow-800 text-lg mb-4 flex items-center">
            <span className="text-2xl mr-2">💭</span>
            Recommendations
          </h3>
          <ul className="space-y-3">
            {content.recommendations.map((rec, index) => (
              <li key={index} className="flex bg-white bg-opacity-60 p-3 rounded-lg">
                <span className="bg-yellow-200 text-yellow-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-yellow-900">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Steps */}
      {content.nextSteps && content.nextSteps.length > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-100">
          <h3 className="font-semibold text-purple-800 text-lg mb-4 flex items-center">
            <span className="text-2xl mr-2">🚀</span>
            Next Steps
          </h3>
          <ul className="space-y-3">
            {content.nextSteps.map((step, index) => (
              <li key={index} className="flex bg-white bg-opacity-60 p-3 rounded-lg">
                <span className="bg-purple-200 text-purple-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-purple-900">{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Additional Details */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
        <h3 className="font-semibold text-gray-800 text-lg mb-4 flex items-center">
          <span className="text-2xl mr-2">📋</span>
          Additional Details
        </h3>
        <TaskResultDetails result={content} />
      </div>
    </div>
  );
}

export default function ProjectDashboard({ params: paramsPromise }: Props) {
  const router = useRouter();
  const params = use(paramsPromise);
  const workspaceId = params.id;

  // 🆕 Enhanced hooks with Asset support
  const {
    deliverables,
    finalDeliverables,
    loading: deliverablesLoading,
    error: deliverablesError,
    refetch: refetchDeliverables,
    finalDeliverablesCount
  } = useProjectDeliverables(workspaceId);

  const {
    getAssetCompletionStats,
    isDeliverableReady,
    loading: assetLoading,
    error: assetError
  } = useAssetManagement(workspaceId);

  // Stati per i dati
  const [workspace, setWorkspace] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [feedbackRequests, setFeedbackRequests] = useState<any[]>([]);
  const [recentActivitySummary, setRecentActivitySummary] = useState<string>('');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  
  // Stati per il controllo dell'UI
  const [activeSection, setActiveSection] = useState('results');
  const [activeResultId, setActiveResultId] = useState('');
  const [showTeamRadar, setShowTeamRadar] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [isStartingTeam, setIsStartingTeam] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isBackgroundUpdating, setIsBackgroundUpdating] = useState(false);

  // 🆕 Get asset stats
  const assetStats = getAssetCompletionStats();
  const deliverableReady = isDeliverableReady();

  // Fetch dei dati iniziali
  useEffect(() => {
    fetchData();
  }, [workspaceId]);
  
  // 🆕 Enhanced fetchData with asset awareness
  const fetchData = async (silentUpdate = false) => {
    if (!workspaceId) return;
    
    try {
      if (!silentUpdate) {
        setLoading(true);
      }
      setError(null);

      // Fetch workspace
      const workspaceData = await api.workspaces.get(workspaceId);
      setWorkspace(workspaceData);

      // Fetch agents
      try {
        const agentsData = await api.agents.list(workspaceId);
        setAgents(agentsData);
      } catch (agentErr) {
        console.error('Failed to fetch agents:', agentErr);
      }

      // Fetch tasks con flag per loading specifico
      try {
        if (!silentUpdate) {
          setTasksLoading(true);
        }
        const response = await fetch(`${api.getBaseUrl()}/monitoring/workspace/${workspaceId}/tasks`);
        if (!response.ok) {
          throw new Error(`Failed to fetch tasks: ${response.status}`);
        }
        const tasksData = await response.json();
        setTasks(tasksData);
      } catch (taskErr) {
        console.error('Failed to fetch tasks:', taskErr);
      } finally {
        if (!silentUpdate) {
          setTasksLoading(false);
        }
      }
      
      // Fetch stats
      try {
        const statsData = await api.monitoring.getWorkspaceStatus(workspaceId);
        setStats(statsData);
      } catch (statsErr) {
        console.error('Failed to fetch stats:', statsErr);
      }
      
      // Fetch feedback requests
      try {
        const requests = await api.humanFeedback.getPendingRequests(workspaceId);
        setFeedbackRequests(requests);
      } catch (feedbackErr) {
        console.error('Failed to fetch feedback requests:', feedbackErr);
      }
      
    } catch (err) {
      console.error('Error fetching workspace data:', err);
      if (!silentUpdate) {
        setError(err instanceof Error ? err.message : 'Impossibile caricare i dettagli del progetto');
      }
    } finally {
      if (!silentUpdate) {
        setLoading(false);
      }    
    }
  };
  
  // 🆕 Enhanced polling for active workspaces with asset monitoring
  useEffect(() => {
    if (workspace?.status === 'active') {
      const id = setInterval(async () => {
        // Check for new final deliverables
        const { count } = await api.monitoring.checkFinalDeliverablesStatus(workspaceId);
        if (count > finalDeliverablesCount) {
          await refetchDeliverables();
        }
        
        // Update task data silently
        await fetchData(true);
      }, 30_000);
      return () => clearInterval(id);
    }
  }, [workspace?.status, workspaceId, finalDeliverables.length, refetchDeliverables]);

  // Funzioni di azione
  const handleStartTeam = async () => {
    try {
      setIsStartingTeam(true);
      await api.monitoring.startTeam(workspaceId);
      setWorkspace(prev => ({ ...prev, status: 'active' }));

      // Aggiornamento iniziale per cambiare lo stato del workspace
      await fetchData(true);

      // Indica che ci sono aggiornamenti in background
      setIsBackgroundUpdating(true);

      // Implementa una sequenza di polling limitata nel tempo
      let pollCount = 0;
      const maxPolls = 12; // Polling per circa 1 minuto (5s × 12)

      const pollData = async () => {
        await fetchData(true);
        pollCount++;

        if (pollCount < maxPolls) {
          setTimeout(pollData, 5000);
        } else {
          setIsBackgroundUpdating(false);
        }
      };

      // Avvia il polling dopo un breve ritardo
      setTimeout(pollData, 3000);

    } catch (err) {
      console.error('Error starting team:', err);
    } finally {
      setIsStartingTeam(false);
    }
  };
  
  const handleDeleteProject = async () => {
    try {
      await api.workspaces.delete(workspaceId);
      router.push('/projects');
    } catch (err) {
      console.error('Error deleting project:', err);
    }
  };

  const handleEditAgent = (agent) => {
    // Implementa la funzione per modificare un agente
    console.log('Edit agent:', agent);
  };
  
  const handleInteractWithAgent = (agent) => {
    // Implementa la funzione per interagire con un agente
    console.log('Interact with agent:', agent);
  };
    
  const onDeleteClick = () => {
    setIsDeleteModalOpen(true);
  };
  
  // 🆕 Enhanced calculations with asset awareness
  const calculateProgress = () => {
    if (!tasks || tasks.length === 0) return 0;
    const completed = tasks.filter(t => t.status === 'completed').length;
    return Math.round((completed / tasks.length) * 100);
  };
  
  // Stima del budget utilizzato
  const calculateBudgetUsage = () => {
    if (!stats) return 0;
    
    const budget = workspace?.budget?.max_amount || 0;
    const spent = stats?.budget?.total_cost || 0;
    
    if (budget === 0) return 0;
    return Math.round((spent / budget) * 100);
  };
  
  // Helper functions per la visualizzazione
  const getStatusColor = (status) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'final_deliverable': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusLabel = (status) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
      case 'paused': return 'In pausa';
      case 'error': return 'Errore';
      case 'completed': return 'Completato';
      case 'in_progress': return 'In Corso';
      case 'pending': return 'In Attesa';
      case 'failed': return 'Fallito';
      case 'final_deliverable': return 'Deliverable Finale';
      default: return status;
    }
  };
  
  const formatPersonalityTraits = (traits) => {
    if (!traits || !Array.isArray(traits) || traits.length === 0) return "Non specificati";
    return traits.map(trait => 
      typeof trait === 'string' 
        ? trait.replace(/_/g, ' ').replace(/-/g, ' ') 
        : String(trait).replace(/_/g, ' ').replace(/-/g, ' ')
    ).join(', ');
  };
  
  // Funzioni per i risultati
  const getAgentName = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Sistema';
  };
  
  // Funzione aggiornata formatTaskContent
  const formatTaskContent = (task) => {
    if (!task.result) return { 
      summary: 'Nessun risultato disponibile',
      keyPoints: [],
      details: '',
      keyInsights: [],
      metrics: {},
      recommendations: [],
      nextSteps: []
    };
    
    try {
      const result = typeof task.result === 'string' ? JSON.parse(task.result) : task.result;
      
      // Estrai dati aggiuntivi per deliverable finali
      let keyInsights = [];
      let metrics = {};
      let recommendations = [];
      let nextSteps = [];
      
      // Se è un deliverable finale, estrai dati strutturati
      if (task.context_data?.is_final_deliverable || task.context_data?.deliverable_aggregation) {
        try {
          const detailedData = result.detailed_results_json 
            ? JSON.parse(result.detailed_results_json) 
            : result;
          
          keyInsights = detailedData.key_findings || detailedData.key_insights || [];
          metrics = detailedData.project_metrics || detailedData.metrics || {};
          recommendations = detailedData.recommendations || detailedData.final_recommendations || [];
          nextSteps = detailedData.next_steps || detailedData.action_items || [];
        } catch (e) {
          console.warn('Could not parse detailed deliverable data:', e);
        }
      }
      
      // Logica esistente per altri campi
      let keyPoints = [];
      if (result.key_points) {
        keyPoints = result.key_points;
      } else if (result.insights) {
        keyPoints = result.insights;
      } else if (result.points) {
        keyPoints = result.points;
      } else if (result.steps) {
        keyPoints = result.steps;
      } else if (keyInsights.length > 0) {
        keyPoints = keyInsights.slice(0, 3); // Use insights as key points
      } else {
        keyPoints = [
          'Attività completata con successo',
          'Risultato generato dall\'agente ' + getAgentName(task.agent_id)
        ];
      }
      
      let summary = '';
      if (result.summary) {
        summary = result.summary;
      } else if (result.executive_summary) {
        summary = result.executive_summary;
      } else if (result.output) {
        summary = result.output;
      } else if (result.conclusion) {
        summary = result.conclusion;
      } else if (typeof result === 'string') {
        summary = result;
      } else {
        summary = 'Risultato completato con successo';
      }
      
      let details = '';
      if (result.details) {
        details = result.details;
      } else if (result.full_output) {
        details = result.full_output;
      } else if (result.description) {
        details = result.description;
      } else if (typeof result === 'string') {
        details = result;
      } else {
        details = JSON.stringify(result, null, 2);
      }
      
      return {
        summary,
        keyPoints: Array.isArray(keyPoints) ? keyPoints : [keyPoints],
        details,
        keyInsights,
        metrics,
        recommendations,
        nextSteps
      };
    } catch (e) {
      return { 
        summary: 'Risultato disponibile ma in formato non standard',
        keyPoints: ['Formato dati non standard', 'Richiede interpretazione'],
        details: typeof task.result === 'string' ? task.result : JSON.stringify(task.result, null, 2),
        keyInsights: [],
        metrics: {},
        recommendations: [],
        nextSteps: []
      };
    }
  };
  
  const getAgentEmoji = (role) => {
    const roleLower = (role || '').toLowerCase();
    if (roleLower.includes('project') || roleLower.includes('manager') || roleLower.includes('strategic')) return '🧠';
    if (roleLower.includes('content') || roleLower.includes('creat')) return '✍️';
    if (roleLower.includes('data') || roleLower.includes('analy')) return '📊';
    if (roleLower.includes('develop') || roleLower.includes('engineer')) return '💻';
    if (roleLower.includes('market') || roleLower.includes('promot')) return '📣';
    if (roleLower.includes('design')) return '🎨';
    if (roleLower.includes('research')) return '🔍';
    if (roleLower.includes('customer') || roleLower.includes('support')) return '🙋';
    return '👤';
  };
  
  const getRecentAgentActivity = (agent) => {
    if (!tasks || !agent) return 'Nessuna attività recente';
    
    const agentTasks = tasks.filter(t => t.agent_id === agent.id);
    if (!agentTasks.length) return 'Nessuna attività recente';
    
    const lastTask = agentTasks.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0];
    return `${lastTask.name} (${getStatusLabel(lastTask.status)})`;
  };
  
  // 🆕 Enhanced project results with asset awareness
  const projectResults = React.useMemo(() => {
    if (!tasks) return [];
    return tasks
      .filter(t => t.status === 'completed' && t.result)
      .map(t => transformTaskToEnhancedResult(t, agents))
      .sort((a, b) => (a.priority - b.priority) ||
        new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [tasks, agents]);

  // Usa il primo risultato come default se ce ne sono
  useEffect(() => {
    if (projectResults.length > 0 && !activeResultId) {
      setActiveResultId(projectResults[0].id);
    }
  }, [projectResults, activeResultId]);
    
  // Filtra il risultato attivo
  const activeResult = projectResults.find(r => r.id === activeResultId);
  
  // Raggruppa task per una visualizzazione a timeline
  const projectPlan = React.useMemo(() => {
    if (!tasks) return [];
    
    return tasks
      .map(task => ({
        id: task.id,
        name: task.name,
        description: task.description,
        status: task.status,
        dueDate: task.deadline ? new Date(task.deadline).toLocaleDateString() : 'Non specificata',
        agent: getAgentName(task.agent_id),
        agentId: task.agent_id,
        createdAt: new Date(task.created_at).toLocaleDateString(),
        updatedAt: new Date(task.updated_at).toLocaleDateString()
      }))
      .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
  }, [tasks, agents]);
  
  // Calcola le dimensioni del team
  const teamDimensions = calculateTeamDimensions(agents);
  
  // Rendering condizionale in base allo stato di caricamento
  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento progetto...</p>
        </div>
      </div>
    );
  }
  
  // Rendering in caso di errore
  if (error) {
    return (
      <div className="container mx-auto">
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => router.push('/projects')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition"
          >
            Torna alla lista progetti
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  // Verifica che workspace esista
  if (!workspace) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="text-3xl mb-3">😕</div>
          <h2 className="text-xl font-medium mb-2">Progetto non trovato</h2>
          <p className="text-gray-500 mb-4">Non è stato possibile trovare il progetto richiesto.</p>
          <Link 
            href="/projects"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Torna alla lista progetti
          </Link>
        </div>
      </div>
    );
  }

  // Componente principale
  return (
    <div className="container mx-auto">
      {/* 🆕 Enhanced Header with Asset Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
          <div className="mb-4 md:mb-0">
            <div className="flex items-baseline">
              <h1 className="text-2xl font-bold">{workspace.name}</h1>
              <Link href="/projects" className="text-indigo-600 hover:underline text-sm ml-3">
                ← Progetti
              </Link>
            </div>
            <p className="text-gray-600 mt-1">{workspace.description}</p>
            
            {/* 🆕 Enhanced Obiettivo with Asset Context */}
            {workspace.goal && (
              <div className="mt-3 p-3 bg-indigo-50 border-l-4 border-indigo-500 rounded-r-md">
                <div className="flex items-start">
                  <span className="text-indigo-600 text-lg mr-2">🎯</span>
                  <div>
                    <p className="text-sm font-medium text-indigo-700">Obiettivo del progetto:</p>
                    <p className="text-sm text-indigo-900">{workspace.goal}</p>
                    {deliverableReady && (
                      <div className="mt-2 text-xs text-green-700 bg-green-100 px-2 py-1 rounded">
                        📦 Asset azionabili pronti per il raggiungimento dell'obiettivo
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="flex space-x-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workspace.status)}`}>
              {getStatusLabel(workspace.status)}
            </span>
            <button 
              onClick={handleStartTeam} 
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
              disabled={isStartingTeam || workspace.status !== 'created'}
            >
              {isStartingTeam ? 'Avvio...' : workspace.status === 'created' ? 'Avvia Team' : 'Interagisci con il Team'}
            </button>
          </div>
        </div>
        
        {/* 🆕 Enhanced Progress bar with Asset Integration */}
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Progresso Progetto</span>
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium">{calculateProgress()}%</span>
              {assetStats.totalAssets > 0 && (
                <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">
                  📦 {assetStats.completedAssets} asset pronti
                </span>
              )}
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${calculateProgress()}%` }}></div>
          </div>
        </div>
      </div>
      
      {/* 🆕 Enhanced Navigation with Asset Indicators */}
      <EnhancedTabNavigation
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        projectResults={projectResults}
        finalDeliverables={finalDeliverables}
        tasks={tasks}
        agents={agents}
        feedbackRequests={feedbackRequests}
        assetStats={assetStats}
      />

      {/* 🆕 Enhanced Quick Status Summary with Asset Support */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-indigo-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Progresso</p>
              <p className="text-2xl font-bold text-indigo-600">{calculateProgress()}%</p>
            </div>
            <div className="text-indigo-500">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Deliverable Finali</p>
              <p className="text-2xl font-bold text-green-600">
                {finalDeliverables.length}
              </p>
            </div>
            <div className="text-green-500">
              🎯
            </div>
          </div>
        </div>

        {/* 🆕 NEW: Asset Status Card */}
        <div className={`rounded-lg shadow-sm p-4 border-l-4 ${
          deliverableReady 
            ? 'bg-white border-purple-500' 
            : assetStats.totalAssets > 0 
              ? 'bg-white border-orange-500'
              : 'bg-gray-50 border-gray-300'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Asset Azionabili</p>
              <p className={`text-2xl font-bold ${
                deliverableReady ? 'text-purple-600' : 'text-orange-600'
              }`}>
                {assetStats.completedAssets}
              </p>
            </div>
            <div className={deliverableReady ? 'text-purple-500' : 'text-orange-500'}>
              📦
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Agenti Attivi</p>
              <p className="text-2xl font-bold text-orange-600">
                {agents.filter(a => a.status === 'active').length}
              </p>
            </div>
            <div className="text-orange-500">
              👥
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Richiede Attenzione</p>
              <p className="text-2xl font-bold text-red-600">
                {feedbackRequests.length + tasks.filter(t => t.status === 'failed').length}
              </p>
            </div>
            <div className="text-red-500">
              🚨
            </div>
          </div>
        </div>
      </div>

      {/* 🆕 NEW: Asset Status Widget */}
      {assetStats.totalAssets > 0 && (
        <div className="mb-6">
          <AssetStatusWidget workspaceId={workspaceId} />
        </div>
      )}
      
      {/* Contenuto basato sulla tab selezionata */}
      {activeSection === 'results' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Enhanced Results list sidebar */}
          <div className="md:col-span-1 bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-lg font-semibold mb-4">Risultati Prodotti</h2>
            
            {projectResults.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <div className="text-5xl mb-3">📋</div>
                <p className="text-gray-600 mb-2">Nessun risultato disponibile</p>
                <p className="text-sm text-gray-500 mb-4">
                  {workspace.status === 'created' 
                    ? 'Avvia il team per iniziare a generare risultati' 
                    : 'Il team è al lavoro ma non ha ancora prodotto risultati'}
                </p>
                {workspace.status === 'created' && (
                  <button 
                    onClick={handleStartTeam}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                    disabled={isStartingTeam}
                  >
                    {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {/* Separare deliverable finali dai risultati normali */}
                {(() => {
                  const finals = finalDeliverables;
                  const normalResults = projectResults.filter(r => r.type !== 'final_deliverable');
                  
                  return (
                    <>
                      {/* Final Deliverables Section */}
                      {finals.length > 0 && (
                        <div className="mb-6">
                          <div className="flex items-center mb-3">
                            <span className="text-sm font-semibold text-indigo-700 bg-indigo-50 px-2 py-1 rounded-full">
                              🎯 Deliverable Finali
                            </span>
                          </div>
                          
                          {finals.map(result => (
                            <div 
                              key={result.id} 
                              onClick={() => setActiveResultId(result.id)}
                              className={`p-4 rounded-lg cursor-pointer transition-all border-2 mb-3 ${
                                result.id === activeResultId 
                                  ? 'border-indigo-400 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-lg' 
                                  : 'border-indigo-200 bg-gradient-to-r from-indigo-25 to-purple-25 hover:border-indigo-300 hover:shadow-md'
                              }`}
                            >
                              <div className="flex items-start">
                                <div className="text-3xl mr-3">{result.icon}</div>
                                <div className="flex-1">
                                  <div className="flex items-center mb-1">
                                    <h3 className="font-semibold text-indigo-900">{result.title}</h3>
                                    <span className="ml-2 text-xs bg-indigo-200 text-indigo-800 px-2 py-0.5 rounded-full">
                                      FINALE
                                    </span>
                                  </div>
                                  <p className="text-sm text-indigo-700 mb-2">{result.description}</p>
                                  
                                  {/* Preview di key insights */}
                                  {result.content?.keyInsights && result.content.keyInsights.length > 0 && (
                                    <div className="mb-2">
                                      <div className="text-xs text-indigo-600 mb-1">Key Insights:</div>
                                      <ul className="text-xs text-indigo-700 space-y-0.5">
                                        {result.content.keyInsights.slice(0, 2).map((insight, idx) => (
                                          <li key={idx} className="flex items-start">
                                            <span className="text-indigo-400 mr-1">•</span>
                                            <span>{insight}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  <div className="flex items-center justify-between mt-2">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                                        {result.creator}
                                      </span>
                                      <span className="text-xs text-indigo-500">{result.date}</span>
                                    </div>
                                    {result.content?.metrics && Object.keys(result.content.metrics).length > 0 && (
                                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                                        📊 Metriche
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Normal Results Section */}
                      {normalResults.length > 0 && (
                        <div>
                          <div className="flex items-center mb-3">
                            <span className="text-sm font-medium text-gray-600">
                              📋 Altri Risultati ({normalResults.length})
                            </span>
                          </div>
                          
                          {normalResults.map(result => (
                            <div 
                              key={result.id} 
                              onClick={() => setActiveResultId(result.id)}
                              className={`p-3 rounded-lg cursor-pointer transition border ${
                                result.id === activeResultId 
                                  ? 'border-indigo-300 bg-indigo-50' 
                                  : 'border-gray-200 hover:bg-gray-50'
                              }`}
                            >
                              {/* Existing normal result rendering */}
                              <div className="flex items-start">
                                <div className="text-2xl mr-3">{result.icon}</div>
                                <div>
                                  <h3 className="font-medium text-gray-900">{result.title}</h3>
                                  <p className="text-sm text-gray-500">{result.description}</p>
                                  <div className="flex items-center mt-2">
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(result.type)}`}>
                                      {result.type}
                                    </span>
                                    <span className="text-xs text-gray-500 ml-2">
                                      {result.date}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>
            )}
            
            {projectResults.length > 0 && (
              <button onClick={() => console.log('Richiedi nuovo output')} className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition text-sm">
                Richiedi Nuovo Output
              </button>
            )}
          </div>
          
          {/* Enhanced Result details panel */}
          <div className="md:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden border border-gray-200">
            {activeResult ? (
              <>
                {/* Enhanced header for final deliverables */}
                <div className={`border-b border-gray-200 ${
                  activeResult.type === 'final_deliverable' 
                    ? 'bg-gradient-to-r from-indigo-50 to-purple-50' 
                    : 'bg-gray-50'
                }`}>
                  <div className="flex justify-between items-center px-6 py-4">
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">{activeResult.icon}</span>
                      <div>
                        <div className="flex items-center">
                          <h2 className="text-xl font-semibold">{activeResult.title}</h2>
                          {activeResult.type === 'final_deliverable' && (
                            <span className="ml-3 text-xs bg-indigo-200 text-indigo-800 px-3 py-1 rounded-full font-medium">
                              🎯 DELIVERABLE FINALE
                            </span>
                          )}
                        </div>
                        <div className="flex items-center text-sm text-gray-500 mt-1">
                          <span>{activeResult.creator}</span>
                          <span className="mx-2">•</span>
                          <span>{activeResult.date}</span>
                          <span className={`ml-3 px-2 py-0.5 rounded-full text-xs ${getStatusColor(activeResult.type)}`}>
                            {activeResult.type}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-2">
                      {/* Navigazione tra risultati */}
                      {projectResults.length > 1 && (
                        <div className="flex border border-gray-200 rounded-md overflow-hidden">
                          <button 
                            onClick={() => {
                              const currentIndex = projectResults.findIndex(r => r.id === activeResultId);
                              if (currentIndex > 0) {
                                setActiveResultId(projectResults[currentIndex - 1].id);
                              }
                            }}
                            disabled={projectResults.findIndex(r => r.id === activeResultId) === 0}
                            className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Risultato precedente"
                          >
                            ← 
                          </button>
                          <div className="px-3 py-2 border-l border-r border-gray-200 text-sm">
                            {projectResults.findIndex(r => r.id === activeResultId) + 1} di {projectResults.length}
                          </div>
                          <button 
                            onClick={() => {
                              const currentIndex = projectResults.findIndex(r => r.id === activeResultId);
                              if (currentIndex < projectResults.length - 1) {
                                setActiveResultId(projectResults[currentIndex + 1].id);
                              }
                            }}
                            disabled={projectResults.findIndex(r => r.id === activeResultId) === projectResults.length - 1}
                            className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Risultato successivo"
                          >
                            →
                          </button>
                        </div>
                      )}
                      
                      <button 
                        onClick={() => {
                          // Funzione per esportare il risultato come file JSON
                          const task = tasks.find(t => t.id === activeResultId);
                          if (task && task.result) {
                            const jsonStr = JSON.stringify(task.result, null, 2);
                            const blob = new Blob([jsonStr], { type: 'application/json' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${task.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_result.json`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                          }
                        }} 
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
                      >
                        <span className="mr-1">↓</span> Esporta
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Enhanced content area */}
                <div className="p-6">
                  {activeResult.type === 'final_deliverable' ? (
                    <EnhancedFinalDeliverableView result={activeResult} />
                  ) : (
                    <TaskResultDetails result={tasks.find(t => t.id === activeResultId)?.result} />
                  )}
                  
                  {/* Feedback e azioni */}
                  <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
                    <div className="flex space-x-3">
                      <button 
                        onClick={() => console.log('Chiedi modifiche', activeResultId)} 
                        className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-md text-sm hover:bg-indigo-100 transition flex items-center"
                      >
                        <span className="mr-1">✏️</span> Chiedi Modifiche
                      </button>
                      <button 
                        onClick={() => console.log('Commenta', activeResultId)} 
                        className="px-4 py-2 bg-gray-50 text-gray-700 rounded-md text-sm hover:bg-gray-100 transition flex items-center"
                      >
                        <span className="mr-1">💬</span> Commenta
                      </button>
                    </div>
                    
                    <button 
                      onClick={() => console.log('Approva', activeResultId)} 
                      className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center"
                    >
                      <span className="mr-1">✓</span> Approva
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center p-12">
                <div className="text-5xl mb-4">💎</div>
                <h3 className="text-xl font-medium text-gray-700 mb-2">Seleziona un risultato</h3>
                <p className="text-gray-500 text-center max-w-md">
                  {projectResults.length > 0
                    ? 'Seleziona un risultato dalla lista a sinistra per visualizzarne i dettagli'
                    : 'Il team non ha ancora prodotto risultati'}
                </p>
                {/* CTA se nessun risultato disponibile */}
                {projectResults.length === 0 && workspace.status === 'created' && (
                  <button 
                    onClick={handleStartTeam}
                    className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                    disabled={isStartingTeam}
                  >
                    {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeSection === 'plan' && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-6">Piano di Esecuzione</h2>
          
          {projectPlan.length === 0 ? (
            <div className="text-center py-10 bg-gray-50 rounded-lg">
              <div className="text-5xl mb-3">📋</div>
              <p className="text-gray-600 mb-2">Nessuna attività pianificata</p>
              <p className="text-sm text-gray-500 mb-4">
                {workspace.status === 'created' 
                  ? 'Avvia il team per iniziare a generare il piano di lavoro' 
                  : 'Il team è al lavoro ma non ha ancora pianificato attività'}
              </p>
              {workspace.status === 'created' && (
                <button 
                  onClick={handleStartTeam}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  disabled={isStartingTeam}
                >
                  {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
                </button>
              )}
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
              
              <div className="space-y-8">
                {projectPlan.map((task) => (
                  <div key={task.id} className="relative pl-12">
                    {/* Timeline circle */}
                    <div className={`absolute left-1.5 w-7 h-7 rounded-full flex items-center justify-center ${
                      task.status === 'completed' ? 'bg-green-500 text-white' :
                      task.status === 'in_progress' ? 'bg-blue-500 text-white' :
                      task.status === 'failed' ? 'bg-red-500 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {task.status === 'completed' ? '✓' : 
                       task.status === 'in_progress' ? '▶' : 
                       task.status === 'failed' ? '✕' : '⌛'}
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{task.name}</h3>
                          {task.description && (
                            <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                          )}
                          {task.agent && (
                            <p className="text-sm text-gray-600 mt-1">
                              Assegnato a: {task.agent}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center">
                          <span className={`text-xs px-3 py-1 rounded-full mr-3 ${getStatusColor(task.status)}`}>
                            {getStatusLabel(task.status)}
                          </span>
                          <span className="text-sm text-gray-500 whitespace-nowrap">
                            {task.dueDate}
                          </span>
                        </div>
                      </div>
                      
                      {task.status === 'in_progress' && (
                        <div className="mt-4 flex space-x-3">
                          <button 
                            onClick={() => console.log('View details', task.id)} 
                            className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
                          >
                            Dettagli
                          </button>
                          <button 
                            onClick={() => console.log('Interact with task', task.id)} 
                            className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                          >
                            Interagisci
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {projectPlan.length > 0 && (
            <div className="mt-8 flex justify-between">
              <Link 
                href={`/projects/${workspaceId}/tasks`}
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
              >
                Visualizza Piano Completo
              </Link>
              <button 
                onClick={() => console.log('Add new task')} 
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                Aggiungi Nuova Attività
              </button>
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'team' && (
        <div className="space-y-6">
          {/* Header con titolo e link */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Team di Agenti</h2>
            <Link 
              href={`/projects/${workspaceId}/team`}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
            >
              <span>Gestisci Team</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </Link>
          </div>
          
          {/* Sezione Team Radar */}
          {agents.length > 1 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-lg font-semibold">Team Competency Matrix</h2>
                <button 
                  className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-md text-sm"
                  onClick={() => setShowTeamRadar(!showTeamRadar)}
                >
                  {showTeamRadar ? 'Nascondi grafico' : 'Mostra grafico'}
                </button>
              </div>
              
              {showTeamRadar && (
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg">
                  <div className="flex flex-col items-center">
                    <p className="text-purple-700 mb-4">
                      Questa visualizzazione mostra la competenza media del team su 6 dimensioni chiave
                    </p>
                    <AgentSkillRadarChart 
                      skills={teamDimensions} 
                      title="Team Matrix" 
                      size={450} 
                      colorScheme="team" 
                    />
                    
                    <div className="mt-6 w-full max-w-2xl">
                      <h4 className="text-md font-medium text-gray-800 mb-2">Dimensioni principali del team:</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {teamDimensions.map((dim, index) => (
                          <div key={index} className="bg-white p-2 rounded-md border border-gray-200 flex justify-between items-center">
                            <span className="text-sm font-medium">{dim.name}</span>
                            <div className="flex items-center">
                              <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                                <div 
                                  className="h-2 bg-purple-600 rounded-full"
                                  style={{ width: `${(dim.value / 5) * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs font-semibold">{dim.value}/5</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {agents.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center py-10">
                <div className="text-5xl mb-3">👥</div>
                <h3 className="text-lg font-medium text-gray-600 mb-2">Nessun agente nel team</h3>
                <p className="text-gray-500 mb-4">Configura il team per questo progetto</p>
                <Link 
                  href={`/projects/${workspaceId}/configure`}
                  className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                >
                  Configura Team
                </Link>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {agents.map(agent => (
                <div key={agent.id} className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-2xl">
                      {getAgentEmoji(agent.role)}
                    </div>
                    <div className="ml-3">
                      <h3 className="font-semibold">{agent.name}</h3>
                      <p className="text-gray-500 text-sm">{agent.role}</p>
                    </div>
                  </div>
                  
                  {/* Skill radar per ogni agente */}
                  <div className="mb-4">
                    <AgentDetailRadarSection agent={agent} />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Personalità:</span> {formatPersonalityTraits(agent.personality_traits)}
                      </p>
                    </div>
                    
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm text-blue-700">
                        <span className="font-medium">Attività Recente:</span> {getRecentAgentActivity(agent)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex space-x-3">
                    <button 
                      onClick={() => handleInteractWithAgent(agent)}
                      className="flex-1 px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                    >
                      Interagisci
                    </button>
                    <button 
                      onClick={() => handleEditAgent(agent)}
                      className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
                    >
                      Profilo
                    </button>
                  </div>
                </div>
              ))}
              
              {/* Sezione comunicazione di team */}
              {agents.length > 0 && (
                <div className="md:col-span-3 bg-white rounded-xl shadow-sm p-6">
                  <h3 className="font-semibold mb-4">Comunicazione di Team</h3>
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="space-y-4 max-h-64 overflow-y-auto">
                      {/* Mock di comunicazioni del team */}
                      {agents.length >= 2 && (
                        <>
                          <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                            <div className="flex items-start">
                              <div className="text-xl mr-2">{getAgentEmoji(agents[0].role)}</div>
                              <div>
                                <div className="flex items-center">
                                  <span className="font-medium">{agents[0].name}</span>
                                  <span className="ml-2 text-xs text-gray-500">recentemente</span>
                                </div>
                                <p className="text-sm mt-1">Sto lavorando sulle attività assegnate secondo il piano di progetto. Ci sono aspetti specifici su cui vorresti che mi concentrassi?</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                            <div className="flex items-start">
                              <div className="text-xl mr-2">{getAgentEmoji(agents[1].role)}</div>
                              <div>
                                <div className="flex items-center">
                                  <span className="font-medium">{agents[1].name}</span>
                                  <span className="ml-2 text-xs text-gray-500">recentemente</span>
                                </div>
                                <p className="text-sm mt-1">Ho completato l'analisi iniziale e sono pronto a procedere con le fasi successive del progetto. Collaborerò con il resto del team per garantire coerenza nell'approccio.</p>
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                    
                    <div className="mt-4 flex">
                      <input 
                        type="text" 
                        placeholder="Scrivi un messaggio al team..." 
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                      <button 
                        onClick={() => console.log('Send message to team')}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-r-md hover:bg-indigo-700 transition"
                      >
                        Invia
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'details' && (
        <div className="space-y-6">
          {/* Budget info */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Metriche e Dettagli Avanzati</h2>
            <p className="text-gray-500 mb-6">Visualizza statistiche dettagliate, monitoraggio costi e altre metriche del progetto.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                <h3 className="font-medium text-blue-800 mb-2">Budget Utilizzato</h3>
                <p className="text-3xl font-bold text-blue-900">
                  {stats?.budget?.total_cost?.toFixed(2) || '0.00'} {workspace.budget?.currency || 'EUR'}
                </p>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${calculateBudgetUsage()}%` }}></div>
                </div>
                <p className="text-xs text-blue-700 mt-1">
                  {calculateBudgetUsage()}% del budget totale ({workspace.budget?.max_amount || 0} {workspace.budget?.currency || 'EUR'})
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                <h3 className="font-medium text-green-800 mb-2">Task Completati</h3>
                <p className="text-3xl font-bold text-green-900">
                  {tasks.filter(t => t.status === 'completed').length} / {tasks.length}
                </p>
                <div className="mt-2 w-full bg-green-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: `${calculateProgress()}%` }}></div>
                </div>
                <p className="text-xs text-green-700 mt-1">{calculateProgress()}% dei task totali</p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                <h3 className="font-medium text-purple-800 mb-2">Agenti Attivi</h3>
                <p className="text-3xl font-bold text-purple-900">
                  {agents.filter(a => a.status === 'active').length} / {agents.length}
                </p>
                <div className="mt-2 w-full bg-purple-200 rounded-full h-2">
                  <div className="bg-purple-600 h-2 rounded-full" 
                    style={{ width: `${agents.length ? (agents.filter(a => a.status === 'active').length / agents.length) * 100 : 0}%` }}></div>
                </div>
                <p className="text-xs text-purple-700 mt-1">
                  {agents.filter(a => a.status === 'active').length} agenti attivi su {agents.length} totali
                </p>
              </div>
            </div>
            
            {/* Project insights dashboard */}
            <ProjectInsightsDashboard workspaceId={workspaceId} />
              
            <ProjectActionsSection 
              workspace={workspace}
              onStartTeam={handleStartTeam}
              onDeleteClick={onDeleteClick} 
              isStartingTeam={isStartingTeam}
              feedbackRequests={feedbackRequests}
            />
            
            <div className="text-center mt-6">
              <Link 
                href={`/projects/${workspaceId}/monitoring`}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                Visualizza Dashboard Completa
              </Link>
            </div>
          </div>
          
          {/* Feedback section */}
          {feedbackRequests.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Richieste di Feedback</h2>
              <div className="space-y-4">
                {feedbackRequests.map(request => (
                  <div 
                    key={request.id}
                    className={`p-4 rounded-lg border ${
                      request.priority === 'high' ? 'border-red-200 bg-red-50' :
                      request.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                      'border-blue-200 bg-blue-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{request.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        request.priority === 'high' ? 'bg-red-200 text-red-800' :
                        request.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {request.priority.toUpperCase()}
                      </span>
                    </div>
                    <div className="mt-3 flex space-x-3">
                      <Link
                        href={`/human-feedback?id=${request.id}`}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                      >
                        Rispondi
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Quick action buttons */}
      <div className="fixed bottom-8 right-8 flex flex-col space-y-4">
        <button 
          onClick={handleStartTeam}
          className="w-12 h-12 bg-green-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-green-700 transition"
          disabled={isStartingTeam || workspace.status !== 'created'}
          title={workspace.status === 'created' ? 'Avvia Team' : 'Team già attivo'}
        >
          <span className="text-xl">{isStartingTeam ? '⏳' : workspace.status === 'created' ? '▶️' : '✓'}</span>
        </button>
        <button 
          onClick={() => setActiveSection('team')}
          className="w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-indigo-700 transition"
          title="Interagisci con il Team"
        >
          <span className="text-xl">💬</span>
        </button>
      </div>
      
      {/* Modali */}
      <ConfirmModal
        isOpen={isDeleteModalOpen}
        title="Elimina progetto"
        message={`Sei sicuro di voler eliminare il progetto "${workspace?.name}"? Questa azione eliminerà anche tutti gli agenti, asset e i dati associati. Questa azione non può essere annullata.`}
        confirmText="Elimina"
        cancelText="Annulla"
        onConfirm={handleDeleteProject}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
          
      {/* 🆕 Background updating indicator */}
      {isBackgroundUpdating && (
        <div className="fixed bottom-4 left-4 bg-indigo-800 text-white px-4 py-2 rounded-full shadow-lg text-sm flex items-center z-40">
          <div className="h-3 w-3 bg-white rounded-full animate-pulse mr-2"></div>
          Sincronizzazione dati in corso...
        </div>
      )}
    </div>
  );
}