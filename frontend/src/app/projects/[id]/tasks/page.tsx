'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Task, Agent } from '@/types';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectTasksPage({ params: paramsPromise, searchParams }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch real tasks from monitoring API
      const tasksResponse = await fetch(`${api.getBaseUrl()}/monitoring/workspace/${id}/tasks`);
      if (!tasksResponse.ok) {
        throw new Error(`Failed to fetch tasks: ${tasksResponse.status}`);
      }
      const realTasksData = await tasksResponse.json();
      const realTasks = Array.isArray(realTasksData) ? realTasksData : realTasksData.tasks;
      setTasks(realTasks);
      
      // Fetch real agents
      const agentsData = await api.agents.list(id);
      setAgents(agentsData);
      
      setError(null);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError(err instanceof Error ? err.message : 'Impossibile caricare i task');
      
      // Fallback to mock data only if API fails
      const mockTasks: Task[] = [
        {
          id: '1',
          workspace_id: id,
          agent_id: '1',
          name: 'Pianificazione campagna marketing',
          description: 'Creare strategia completa per la campagna di marketing digitale',
          status: 'completed',
          result: {
            summary: 'Strategia completata con focus su Instagram e LinkedIn',
            deliverables: ['Piano editoriale', 'Budget allocazione', 'Timeline']
          },
          created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
          updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
        {
          id: '2',
          workspace_id: id,
          agent_id: '2',
          name: 'Analisi hashtag Instagram',
          description: 'Ricerca e analisi degli hashtag più efficaci per il nostro target',
          status: 'in_progress',
          created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
          updated_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '3',
          workspace_id: id,
          agent_id: '3',
          name: 'Creazione contenuti visual',
          description: 'Sviluppo di template e grafiche per i post Instagram',
          status: 'pending',
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
          updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
        {
          id: '4',
          workspace_id: id,
          agent_id: '1',
          name: 'Setup campagne pubblicitarie',
          description: 'Configurazione campagne Meta Ads e Google Ads',
          status: 'failed',
          result: {
            error: 'Errore di autenticazione con Meta Business API',
            retry_needed: true
          },
          created_at: new Date(Date.now() - 86400000).toISOString(),
          updated_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        },
        {
          id: '5',
          workspace_id: id,
          agent_id: '2',
          name: 'Monitoraggio competitor',
          description: 'Analisi delle strategie dei principali competitor su social media',
          status: 'completed',
          result: {
            summary: 'Identificati 5 competitor principali con analisi delle loro strategie',
            insights: ['Uso intensivo di video content', 'Focus su storytelling', 'Collaborazioni con micro-influencer']
          },
          created_at: new Date(Date.now() - 86400000 * 4).toISOString(),
          updated_at: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: '6',
          workspace_id: id,
          agent_id: '3',
          name: 'Ottimizzazione landing page',
          description: 'Miglioramento della landing page per aumentare conversioni',
          status: 'in_progress',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          updated_at: new Date(Date.now() - 1800000).toISOString(),
        }
      ];

      setTasks(mockTasks);
      
      // Try to fetch agents anyway for mock data
      try {
        const agentsData = await api.agents.list(id);
        setAgents(agentsData);
      } catch (agentErr) {
        console.error('Error fetching agents:', agentErr);
        setError(prev => prev + ' + Errore caricamento agenti');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'canceled': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'completed': return 'Completato';
      case 'in_progress': return 'In Corso';
      case 'pending': return 'In Attesa';
      case 'failed': return 'Fallito';
      case 'canceled': return 'Annullato';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'completed': return '✅';
      case 'in_progress': return '🔄';
      case 'pending': return '⏳';
      case 'failed': return '❌';
      case 'canceled': return '🚫';
      default: return '❓';
    }
  };

  // Filter and sort tasks
  const filteredAndSortedTasks = React.useMemo(() => {
    let filtered = tasks;
    
    if (filterStatus !== 'all') {
      filtered = tasks.filter(task => task.status === filterStatus);
    }
    
    return filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });
  }, [tasks, filterStatus, sortBy, sortOrder]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Agente Sconosciuto';
  };

  // Enhanced statistics including cost tracking and insights
  const taskStats = React.useMemo(() => {
    const stats = {
      total: tasks.length,
      completed: tasks.filter(t => t.status === 'completed').length,
      in_progress: tasks.filter(t => t.status === 'in_progress').length,
      pending: tasks.filter(t => t.status === 'pending').length,
      failed: tasks.filter(t => t.status === 'failed').length,
    };
    
    // Calculate cost and value metrics
    const costMetrics = tasks.reduce((acc, task) => {
      const result = task.result || {};
      const cost = parseFloat(result.cost_estimated || '0');
      const executionTime = parseFloat(result.execution_time_seconds || '0');
      
      acc.totalCost += cost;
      acc.totalTime += executionTime;
      
      if (task.status === 'completed') {
        acc.completedCost += cost;
        acc.completedTime += executionTime;
        
        // Count deliverables and insights
        if (result.detailed_results_json) {
          try {
            const detailed = typeof result.detailed_results_json === 'string' 
              ? JSON.parse(result.detailed_results_json) 
              : result.detailed_results_json;
            
            if (detailed.structured_content) acc.structuredOutputs++;
            if (detailed.rendered_html) acc.renderedOutputs++;
            if (detailed.actionable_insights) acc.totalInsights += detailed.actionable_insights.length;
          } catch (e) {
            // Ignore JSON parsing errors
          }
        }
      }
      
      return acc;
    }, {
      totalCost: 0,
      completedCost: 0,
      totalTime: 0,
      completedTime: 0,
      structuredOutputs: 0,
      renderedOutputs: 0,
      totalInsights: 0
    });
    
    return {
      ...stats,
      ...costMetrics,
      success_rate: stats.total > 0 ? ((stats.completed / stats.total) * 100).toFixed(1) : '0',
      failure_rate: stats.total > 0 ? ((stats.failed / stats.total) * 100).toFixed(1) : '0',
      avgCostPerTask: stats.completed > 0 ? (costMetrics.completedCost / stats.completed) : 0,
      avgTimePerTask: stats.completed > 0 ? (costMetrics.completedTime / stats.completed) : 0
    };
  }, [tasks]);

  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento task...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm mb-2 block">
            ← Torna al progetto
          </Link>
          <h1 className="text-2xl font-semibold">Tutte le Attività</h1>
          <p className="text-gray-600">Gestione completa delle attività del progetto</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Totale attività</p>
          <p className="text-2xl font-bold">{tasks.length}</p>
        </div>
      </div>

      {/* Cost and Value Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-4">💰 Recap Costi e Valore Generato</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-700">
              ${taskStats.totalCost.toFixed(4)}
            </div>
            <div className="text-sm text-blue-600">Costo Totale</div>
            <div className="text-xs text-blue-500">
              Medio: ${taskStats.avgCostPerTask.toFixed(6)}/task
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-700">
              {taskStats.structuredOutputs}
            </div>
            <div className="text-sm text-green-600">Asset Strutturati</div>
            <div className="text-xs text-green-500">
              {taskStats.renderedOutputs} con markup HTML
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-700">
              {taskStats.totalInsights}
            </div>
            <div className="text-sm text-purple-600">Insights Azionabili</div>
            <div className="text-xs text-purple-500">
              Da {taskStats.completed} task completati
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-700">
              {(taskStats.completedTime / 60).toFixed(1)}m
            </div>
            <div className="text-sm text-orange-600">Tempo Elaborazione</div>
            <div className="text-xs text-orange-500">
              Medio: {taskStats.avgTimePerTask.toFixed(1)}s/task
            </div>
          </div>
        </div>
        
        {/* Value calculation */}
        {taskStats.totalInsights > 0 && (
          <div className="mt-4 p-3 bg-white rounded-lg">
            <div className="text-sm text-gray-600">
              🎯 <strong>Valore Generato:</strong> {taskStats.totalInsights} insights azionabili 
              da {taskStats.structuredOutputs} asset pronti all'uso
              {taskStats.totalCost > 0 && (
                <span className="ml-2 text-green-600">
                  (Costo per insight: ${(taskStats.completedCost / taskStats.totalInsights).toFixed(4)})
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
          <div className="text-2xl font-bold text-green-700">{taskStats.completed}</div>
          <div className="text-xs text-green-600">Completati</div>
          <div className="text-xs text-green-500 mt-1">{taskStats.success_rate}% successo</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-center">
          <div className="text-2xl font-bold text-blue-700">{taskStats.in_progress}</div>
          <div className="text-xs text-blue-600">In Corso</div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 text-center">
          <div className="text-2xl font-bold text-yellow-700">{taskStats.pending}</div>
          <div className="text-xs text-yellow-600">In Attesa</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-center">
          <div className="text-2xl font-bold text-red-700">{taskStats.failed}</div>
          <div className="text-xs text-red-600">Falliti</div>
          <div className="text-xs text-red-500 mt-1">{taskStats.failure_rate}% fallimenti</div>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-700">{agents.length}</div>
          <div className="text-xs text-gray-600">Agenti Attivi</div>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="all">Tutti</option>
                <option value="pending">In Attesa</option>
                <option value="in_progress">In Corso</option>
                <option value="completed">Completati</option>
                <option value="failed">Falliti</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ordina per</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="created_at">Data Creazione</option>
                <option value="updated_at">Ultimo Aggiornamento</option>
                <option value="name">Nome</option>
                <option value="status">Stato</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Direzione</label>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm hover:bg-gray-50"
              >
                {sortOrder === 'asc' ? '↑ Crescente' : '↓ Decrescente'}
              </button>
            </div>
          </div>
          
          <div className="text-sm text-gray-500">
            {filteredAndSortedTasks.length} di {tasks.length} attività
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          <div className="flex items-center">
            <span className="mr-2">⚠️</span>
            <div>
              <strong>Errore caricamento dati:</strong> {error}
              <div className="text-sm mt-1">Mostrando dati di esempio. Verifica la connessione al server.</div>
            </div>
          </div>
        </div>
      )}

      {/* Tasks List */}
      <div className="space-y-4">
        {filteredAndSortedTasks.map((task) => (
          <div key={task.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-xl">{getStatusIcon(task.status)}</span>
                  <h3 className="text-lg font-semibold text-gray-900">{task.name}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(task.status)}`}>
                    {getStatusLabel(task.status)}
                  </span>
                </div>
                <p className="text-gray-600 mb-3">{task.description}</p>
                
                <div className="flex items-center space-x-6 text-sm text-gray-500">
                  <div>
                    <span className="font-medium">Agente:</span> {getAgentName(task.agent_id || '')}
                  </div>
                  <div>
                    <span className="font-medium">Creato:</span> {formatDate(task.created_at)}
                  </div>
                  <div>
                    <span className="font-medium">Aggiornato:</span> {formatDate(task.updated_at)}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Enhanced Task Results/Details */}
            {task.result && (
              <div className="mt-4 space-y-3">
                {/* Rich Content Detection */}
                {(() => {
                  const result = task.result;
                  let hasRichContent = false;
                  let structuredContent = null;
                  let visualSummary = null;
                  let keyInsights = [];
                  let renderableContent = null;
                  
                  // Check for detailed_results_json with structured content
                  if (result.detailed_results_json) {
                    try {
                      const detailed = typeof result.detailed_results_json === 'string' 
                        ? JSON.parse(result.detailed_results_json) 
                        : result.detailed_results_json;
                      
                      // Check for pre-rendered HTML
                      if (detailed.rendered_html) {
                        hasRichContent = true;
                        renderableContent = detailed.rendered_html;
                      }
                      
                      // Check for structured content indicators
                      if (detailed.structured_content || detailed.editorial_calendar || detailed.competitor_analysis) {
                        hasRichContent = true;
                        structuredContent = detailed;
                      }
                      
                      // Extract visual summary
                      if (detailed.visual_summary) {
                        visualSummary = detailed.visual_summary;
                      }
                      
                      // Extract insights
                      if (detailed.actionable_insights) {
                        keyInsights = detailed.actionable_insights;
                      } else if (detailed.key_insights) {
                        keyInsights = detailed.key_insights;
                      }
                    } catch (e) {
                      // Ignore JSON parsing errors
                    }
                  }
                  
                  return (
                    <div>
                      {/* High-Value Content Badge */}
                      {hasRichContent && (
                        <div className="mb-3 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                          ✨ Contenuto Strutturato Disponibile
                        </div>
                      )}
                      
                      {/* Main Results Container */}
                      <div className={`p-4 rounded-md ${
                        hasRichContent 
                          ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200' 
                          : 'bg-gray-50'
                      }`}>
                        <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                          📊 Risultati
                          {hasRichContent && (
                            <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Rich Content</span>
                          )}
                        </h4>
                        
                        {task.status === 'completed' && (
                          <div className="space-y-3">
                            {/* Visual Summary (Priority Display) */}
                            {visualSummary && (
                              <div className="bg-white p-3 rounded border border-blue-200">
                                <h5 className="text-sm font-medium text-blue-900 mb-2">📈 Riepilogo Visivo</h5>
                                <pre className="text-sm text-gray-700 whitespace-pre-line font-sans">{visualSummary}</pre>
                              </div>
                            )}
                            
                            {/* Key Insights */}
                            {keyInsights.length > 0 && (
                              <div className="bg-white p-3 rounded border border-green-200">
                                <h5 className="text-sm font-medium text-green-900 mb-2">💡 Insights Chiave</h5>
                                <ul className="space-y-1">
                                  {keyInsights.slice(0, 3).map((insight: string, index: number) => (
                                    <li key={index} className="text-sm text-gray-700 flex items-start">
                                      <span className="text-green-600 mr-2 mt-0.5">•</span>
                                      {insight}
                                    </li>
                                  ))}
                                </ul>
                                {keyInsights.length > 3 && (
                                  <p className="text-xs text-gray-500 mt-2">+ altri {keyInsights.length - 3} insights</p>
                                )}
                              </div>
                            )}
                            
                            {/* Structured Content Preview */}
                            {structuredContent && (
                              <div className="bg-white p-3 rounded border border-purple-200">
                                <h5 className="text-sm font-medium text-purple-900 mb-2">🗂️ Contenuto Strutturato</h5>
                                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                                  {structuredContent.editorial_calendar && (
                                    <div className="flex items-center">
                                      <span className="text-blue-600 mr-1">📅</span>
                                      Calendar: {structuredContent.editorial_calendar.length} items
                                    </div>
                                  )}
                                  {structuredContent.competitor_analysis && (
                                    <div className="flex items-center">
                                      <span className="text-orange-600 mr-1">🏆</span>
                                      Competitors: {structuredContent.competitor_analysis.length} analyzed
                                    </div>
                                  )}
                                  {structuredContent.metrics && (
                                    <div className="flex items-center">
                                      <span className="text-green-600 mr-1">📊</span>
                                      Metrics: {Object.keys(structuredContent.metrics).length} tracked
                                    </div>
                                  )}
                                  {renderableContent && (
                                    <div className="flex items-center">
                                      <span className="text-purple-600 mr-1">🎨</span>
                                      HTML Ready
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {/* Standard Summary (fallback or additional) */}
                            {result.summary && !visualSummary && (
                              <div className="bg-white p-3 rounded border">
                                <h5 className="text-sm font-medium text-gray-900 mb-2">📝 Riepilogo</h5>
                                <p className="text-sm text-gray-700">{result.summary}</p>
                              </div>
                            )}
                            
                            {/* Legacy fields (backwards compatibility) */}
                            {result.output && !hasRichContent && (
                              <div className="bg-white p-3 rounded border">
                                <h5 className="text-sm font-medium text-gray-900 mb-2">📄 Output</h5>
                                <div className="text-sm text-gray-700 max-h-32 overflow-y-auto">
                                  {typeof result.output === 'string' ? result.output : JSON.stringify(result.output, null, 2)}
                                </div>
                              </div>
                            )}
                            
                            {result.deliverables && Array.isArray(result.deliverables) && (
                              <div className="bg-white p-3 rounded border">
                                <h5 className="text-sm font-medium text-gray-900 mb-2">📦 Deliverables</h5>
                                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                  {result.deliverables.map((item: string, index: number) => (
                                    <li key={index}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {result.insights && Array.isArray(result.insights) && keyInsights.length === 0 && (
                              <div className="bg-white p-3 rounded border border-yellow-200">
                                <h5 className="text-sm font-medium text-yellow-900 mb-2">💭 Legacy Insights</h5>
                                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                  {result.insights.map((insight: string, index: number) => (
                                    <li key={index}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                        
                        {task.status === 'failed' && (
                          <div className="bg-red-50 p-3 rounded border border-red-200">
                            <p className="text-sm text-red-700 font-medium flex items-center">
                              <span className="mr-2">❌</span>
                              Errore:
                            </p>
                            <p className="text-sm text-red-600 mt-1">{result.error}</p>
                            {result.retry_needed && (
                              <p className="text-xs text-red-500 mt-2 flex items-center">
                                <span className="mr-1">🔄</span>
                                Richiesto nuovo tentativo
                              </p>
                            )}
                          </div>
                        )}
                        
                        {/* Execution Metadata */}
                        <div className="mt-3 pt-3 border-t border-gray-200 flex flex-wrap gap-4 text-xs text-gray-500">
                          {result.execution_time_seconds && (
                            <div className="flex items-center">
                              <span className="mr-1">⏱️</span>
                              {result.execution_time_seconds}s
                            </div>
                          )}
                          {result.cost_estimated && (
                            <div className="flex items-center">
                              <span className="mr-1">💰</span>
                              ${result.cost_estimated.toFixed(6)}
                            </div>
                          )}
                          {hasRichContent && (
                            <div className="flex items-center text-blue-600">
                              <span className="mr-1">✨</span>
                              Rich Content Available
                            </div>
                          )}
                          {keyInsights.length > 0 && (
                            <div className="flex items-center text-green-600">
                              <span className="mr-1">💡</span>
                              {keyInsights.length} Insights
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {filteredAndSortedTasks.length === 0 && (
        <div className="text-center py-10 bg-white rounded-lg shadow-sm">
          <div className="text-4xl mb-4">📋</div>
          <p className="text-gray-500">Nessuna attività trovata con i filtri attuali</p>
          {filterStatus !== 'all' && (
            <button 
              onClick={() => setFilterStatus('all')}
              className="mt-3 text-indigo-600 hover:underline text-sm"
            >
              Mostra tutte le attività
            </button>
          )}
        </div>
      )}
    </div>
  );
}