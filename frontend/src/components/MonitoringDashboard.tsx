import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '@/utils/api';
import TasksViewer from './TasksViewer';
import { Agent, ExecutorDetailedStats, ExecutorStatus, ActivityLog, BudgetSummary } from '@/types'; // Assicurati che i tipi siano importati correttamente

// Definisci qui le interfacce se non sono globali in @/types
// interface ActivityLog { ... } // Se non già in types/index.ts
// interface BudgetSummary { ... } // Se non già in types/index.ts

interface MonitoringDashboardProps {
  workspaceId: string;
  agentsInWorkspace: Agent[]; // Prop per passare la lista degli agenti
}

export default function MonitoringDashboard({ workspaceId, agentsInWorkspace }: MonitoringDashboardProps) {
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [budget, setBudget] = useState<BudgetSummary | null>(null);
  const [executorStatus, setExecutorStatus] = useState<ExecutorStatus | null>(null);
  const [detailedStats, setDetailedStats] = useState<ExecutorDetailedStats | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const agentNameMap = useMemo(() => {
    const map = new Map<string, string>();
    if (agentsInWorkspace) {
        agentsInWorkspace.forEach(agent => map.set(agent.id, agent.name));
    }
    return map;
  }, [agentsInWorkspace]);

  const fetchData = useCallback(async (isManualRefresh = false) => {
    const isInitialLoad = !activity.length && !budget && !executorStatus && !detailedStats;
    
    if (isInitialLoad && !isManualRefresh) setLoading(true); // Solo per il primo caricamento assoluto
    if (isManualRefresh) setIsRefreshing(true);
    
    try {
      const promises = [
        api.monitoring.getWorkspaceActivity(workspaceId, 20),
        api.monitoring.getWorkspaceBudget(workspaceId),
        api.monitoring.getExecutorStatus(),
        api.monitoring.getExecutorDetailedStats(),
      ];
      
      const results = await Promise.allSettled(promises);
      let overallError: string | null = null;

      if (results[0].status === 'fulfilled') {
        setActivity(results[0].value as ActivityLog[]);
      } else {
        console.error('Error fetching activity:', results[0].reason);
        if (!overallError) overallError = results[0].reason instanceof Error ? results[0].reason.message : String(results[0].reason);
      }

      if (results[1].status === 'fulfilled') {
        setBudget(results[1].value as BudgetSummary);
      } else {
        console.error('Error fetching budget:', results[1].reason);
        if (!overallError) overallError = results[1].reason instanceof Error ? results[1].reason.message : String(results[1].reason);
      }
      
      if (results[2].status === 'fulfilled') {
        setExecutorStatus(results[2].value as ExecutorStatus);
      } else {
        console.error('Error fetching executor status:', results[2].reason);
        if (!overallError) overallError = results[2].reason instanceof Error ? results[2].reason.message : String(results[2].reason);
      }

      if (results[3].status === 'fulfilled') {
        setDetailedStats(results[3].value as ExecutorDetailedStats);
      } else {
        console.error('Error fetching detailed stats:', results[3].reason);
        if (!overallError) overallError = results[3].reason instanceof Error ? results[3].reason.message : String(results[3].reason);
      }
      
      setError(overallError); 
    } catch (err) { 
      console.error('Unhandled error fetching monitoring data:', err);
      setError(err instanceof Error ? err.message : 'Impossibile caricare i dati di monitoraggio');
    } finally {
      if (isInitialLoad || isManualRefresh) setLoading(false); // setLoading a false dopo il primo caricamento o refresh
      if (isManualRefresh) setIsRefreshing(false);
    }
  }, [workspaceId]); // Rimosse dipendenze che causavano re-fetch continui

  useEffect(() => {
    fetchData(true); // Caricamento iniziale marcato come "manuale" per impostare loading
    const interval = setInterval(() => fetchData(), 30000);
    return () => clearInterval(interval);
  }, [fetchData]); // fetchData è ora stabile

  const handlePauseExecutor = async () => {
    setIsActionLoading(true);
    setError(null);
    try {
      const result = await api.monitoring.pauseExecutor();
      console.log(result.message);
      await fetchData(true); 
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore durante la messa in pausa dell\'esecutore');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleResumeExecutor = async () => {
    setIsActionLoading(true);
    setError(null);
    try {
      const result = await api.monitoring.resumeExecutor();
      console.log(result.message);
      await fetchData(true); 
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore durante la ripresa dell\'esecutore');
    } finally {
      setIsActionLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return { date: 'N/A', time: 'N/A' };
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString('it-IT'),
      time: date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
  };

  const getEventIcon = (event: string = "default") => {
    switch (event) {
      case 'task_started': return '▶️';
      case 'task_completed': return '✅';
      case 'task_failed': return '❌';
      case 'task_error': return '❗';
      case 'initial_task_created': return '🆕';
      case 'handoff_requested': return '🤝';
      default: return '📝';
    }
  };

  const getEventColor = (event: string = "default") => {
    switch (event) {
      case 'task_started': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'task_completed': return 'bg-green-50 text-green-700 border-green-200';
      case 'task_failed': return 'bg-red-50 text-red-700 border-red-200';
      case 'task_error': return 'bg-red-50 text-red-700 border-red-200';
      case 'initial_task_created': return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'handoff_requested': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const formatCost = (cost: number | undefined) => {
    if (typeof cost !== 'number') return '$?.??';
    return `$${cost.toFixed(6)}`;
  };

  const ExecutorControls = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Controllo Esecutore Globale</h3>
      {executorStatus ? (
        <div className="flex items-center space-x-4">
          <p>
            Stato Esecutore: <span className={`font-semibold px-2 py-1 rounded-full text-xs ${
              executorStatus.status_string === 'running' ? 'bg-green-100 text-green-700' :
              executorStatus.status_string === 'paused' ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>{executorStatus.status_string.toUpperCase()}</span>
          </p>
          {executorStatus.is_running && (
            <>
              {executorStatus.is_paused ? (
                <button
                  onClick={handleResumeExecutor}
                  disabled={isActionLoading}
                  className="px-3 py-1.5 bg-green-500 text-white rounded-md text-sm hover:bg-green-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isActionLoading ? 'Riprendendo...' : 'Riprendi Esecuzione'}
                </button>
              ) : (
                <button
                  onClick={handlePauseExecutor}
                  disabled={isActionLoading}
                  className="px-3 py-1.5 bg-yellow-500 text-white rounded-md text-sm hover:bg-yellow-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isActionLoading ? 'In Pausa...' : 'Pausa Esecutore'}
                </button>
              )}
            </>
          )}
           {!executorStatus.is_running && executorStatus.status_string === 'stopped' && (
             <p className="text-sm text-gray-500">L'esecutore è fermo. Per avviarlo, potrebbe essere necessario riavviare il backend.</p>
          )}
        </div>
      ) : (
        <p className="text-sm text-gray-500">Caricamento stato esecutore...</p>
      )}
    </div>
  );

  const DetailedStatsDisplay = () => {
    if (loading && !detailedStats) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 text-center text-gray-500">Caricamento statistiche dettagliate...</div>;
    if (!detailedStats) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 text-center text-gray-500">Statistiche non disponibili.</div>;


    const { 
      tasks_in_queue = 0, 
      tasks_actively_processing = 0, 
      session_stats,
      max_concurrent_tasks = 0
    } = detailedStats;

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Recap Esecuzione</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-center">
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <p className="text-2xl font-bold text-blue-700">{tasks_in_queue}</p>
            <p className="text-xs text-blue-600">Task in Coda</p>
          </div>
          <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200">
            <p className="text-2xl font-bold text-indigo-700">{tasks_actively_processing} / {max_concurrent_tasks}</p>
            <p className="text-xs text-indigo-600">Task in Esecuzione / Max</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <p className="text-2xl font-bold text-green-700">{session_stats?.tasks_completed_successfully ?? 0}</p>
            <p className="text-xs text-green-600">Task Completati</p>
          </div>
          <div className="bg-red-50 p-3 rounded-lg border border-red-200">
            <p className="text-2xl font-bold text-red-700">{session_stats?.tasks_failed ?? 0}</p>
            <p className="text-xs text-red-600">Task Falliti</p>
          </div>
        </div>
        {session_stats?.agent_activity && Object.keys(session_stats.agent_activity).length > 0 && (
          <div>
            <h4 className="text-md font-semibold text-gray-800 mb-3">Attività per Agente (Sessione Corrente Log)</h4>
            <div className="space-y-2 max-h-60 overflow-y-auto bg-gray-50 p-3 rounded-md custom-scrollbar">
              {Object.entries(session_stats.agent_activity).map(([agentId, stats]) => (
                <div key={agentId} className="p-2 rounded-md border border-gray-200 bg-white">
                  <p className="text-sm font-medium text-gray-700 truncate" title={agentNameMap.get(agentId) || agentId}>
                    {agentNameMap.get(agentId) || `ID: ${agentId.substring(0,8)}...`}
                  </p>
                  <div className="flex justify-between text-xs mt-1 text-gray-600">
                    <span>Completati: <span className="font-semibold text-green-600">{stats.completed}</span></span>
                    <span>Falliti: <span className="font-semibold text-red-600">{stats.failed}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const BudgetOverviewDisplay = () => ( // Rinominato per coerenza
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Budget Overview</h3>
        {budget && (
          <div className="text-sm text-gray-500">
            Ultimo agg.: {formatTimestamp(new Date().toISOString()).time}
          </div>
        )}
      </div>
      
      {loading && !budget ? ( // Mostra loader se sta caricando E il budget non c'è ancora
        <div className="text-center py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
        </div>
      ) : !budget ? ( // Mostra messaggio se non ci sono dati budget (e non sta caricando)
         <p className="text-sm text-gray-500 text-center py-4">Dati budget non disponibili.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-600 font-medium">Costo Totale Workspace</p>
              <p className="text-2xl font-bold text-blue-800">{formatCost(budget.total_cost)}</p>
              <p className="text-xs text-blue-600 mt-1">{budget.currency}</p>
            </div>
            
            <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <p className="text-sm text-green-600 font-medium">Token Totali (Estimati)</p>
              <p className="text-lg font-semibold text-green-800">
                {((budget.total_tokens?.input || 0) + (budget.total_tokens?.output || 0)).toLocaleString()}
              </p>
              <p className="text-xs text-green-600 mt-1">
                {(budget.total_tokens?.input || 0).toLocaleString()} input + {(budget.total_tokens?.output || 0).toLocaleString()} output
              </p>
            </div>
            
            {typeof budget.budget_limit === 'number' && budget.budget_limit > 0 ? (
              <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                <p className="text-sm text-purple-600 font-medium">Utilizzo Budget Limite</p>
                <div className="flex items-center mt-2">
                  <div className="w-full bg-purple-200 rounded-full h-3 mr-3">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-purple-600 h-3 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(budget.budget_percentage || 0, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-purple-800 font-semibold text-sm">
                    {(budget.budget_percentage || 0).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-purple-600 mt-1">
                  Limite: {budget.budget_limit.toLocaleString()} {budget.currency}
                </p>
              </div>
            ) : (
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 font-medium">Limite Budget</p>
                <p className="text-lg text-gray-800">Non impostato</p>
              </div>
            )}
          </div>

          {budget.agent_costs && Object.keys(budget.agent_costs).length > 0 && (
            <div className="border-t border-gray-200 pt-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Costi Dettagliati per Agente (Estimati)</h4>
              <div className="space-y-3 max-h-72 overflow-y-auto custom-scrollbar">
                {Object.entries(budget.agent_costs)
                  .sort(([,aCost], [,bCost]) => bCost - aCost) 
                  .map(([agentId, cost]) => {
                    const agentName = agentNameMap.get(agentId) || `Agente ID: ${agentId.substring(0, 8)}...`;
                    const percentage = budget.total_cost > 0 ? (cost / budget.total_cost) * 100 : 0;
                    return (
                      <div key={agentId} className="bg-gray-50 p-4 rounded-lg border border-gray-100 hover:shadow-sm transition-shadow">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-800 truncate" title={agentName}>
                            {agentName}
                          </span>
                          <span className="font-semibold text-gray-700">{formatCost(cost)}</span>
                        </div>
                        {budget.total_cost > 0 && (
                           <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div 
                              className="bg-indigo-500 h-2.5 rounded-full transition-all duration-500"
                              style={{ width: `${percentage}%` }}
                              title={`${percentage.toFixed(1)}% del totale workspace`}
                            ></div>
                          </div>
                        )}
                         {budget.total_cost > 0 && (
                            <p className="text-xs text-gray-500 mt-1.5">
                            {percentage.toFixed(1)}% del costo totale del workspace.
                            </p>
                         )}
                      </div>
                    );
                  })
                }
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );

  const ActivityLogDisplay = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Log Attività Recente</h3>
        <button 
          onClick={() => fetchData(true)}
          disabled={isRefreshing || isActionLoading}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isRefreshing ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Aggiornamento...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-2">
                <path fillRule="evenodd" d="M15.312 11.424a5.5 5.5 0 0 1-9.456-4.424l-.262-.524a.75.75 0 0 1 1.338-.668l.262.524A5.502 5.502 0 0 1 15.312 11.424ZM4.688 8.576a5.5 5.5 0 0 1 9.456 4.424l.262.524a.75.75 0 1 1-1.338.668l-.262-.524A5.502 5.502 0 0 1 4.688 8.576Z" clipRule="evenodd" />
              </svg>
              Aggiorna Log
            </>
          )}
        </button>
      </div>
      
      {loading && activity.length === 0 ? (
         <div className="text-center py-12">
          <div className="animate-pulse h-6 w-3/4 bg-gray-200 rounded mx-auto mb-4"></div>
          <div className="animate-pulse h-4 w-1/2 bg-gray-200 rounded mx-auto"></div>
        </div>
      ): activity.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <p className="text-gray-500 text-lg">Nessuna attività registrata per questo workspace.</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
          {activity.map((log, index) => {
            const formattedTime = formatTimestamp(log.timestamp);
            const agentName = log.agent_id ? (agentNameMap.get(log.agent_id) || log.agent_id.substring(0,8)+"...") : 'Sistema';
            return (
              <div key={`${log.timestamp}-${index}-${log.event}`} className={`border rounded-lg p-3.5 text-xs ${getEventColor(log.event)}`}>
                <div className="flex justify-between items-start mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">{getEventIcon(log.event)}</span>
                    <div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border`}>
                        {log.event.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {formattedTime.date} {formattedTime.time}
                      </div>
                    </div>
                  </div>
                  {typeof log.cost === 'number' && (
                    <div className="text-right">
                      <span className="text-sm font-semibold">{formatCost(log.cost)}</span>
                      <div className="text-2xs text-gray-500">costo</div>
                    </div>
                  )}
                </div>
                
                {(log.task_name || log.task_id) && (
                    <p className="text-2xs text-gray-600 mt-1 mb-0.5 truncate" title={log.task_name}>
                        <strong>Task:</strong> {log.task_name || 'N/D'} (<span className="font-mono">{log.task_id?.substring(0,8)}...</span>)
                    </p>
                )}
                 {log.agent_id && (
                     <p className="text-2xs text-gray-600 mb-0.5">
                        <strong>Agente:</strong> <span title={log.agent_id}>{agentName}</span>
                     </p>
                 )}
                {log.model && (
                    <p className="text-2xs text-gray-500 mb-0.5"><strong>Modello:</strong> {log.model}</p>
                )}
                {typeof log.execution_time === 'number' && (
                    <p className="text-2xs text-gray-500 mb-0.5"><strong>Tempo Esec.:</strong> {log.execution_time.toFixed(2)}s</p>
                )}
                {log.result_summary && (
                  <div className="mt-1.5 p-1.5 bg-white bg-opacity-60 rounded text-2xs">
                    <strong className="text-gray-500">Risultato:</strong>
                    <p className="text-gray-600 mt-0.5 break-words leading-tight">{log.result_summary}</p>
                  </div>
                )}
                {log.error && (
                  <div className="mt-1.5 p-1.5 bg-red-50 border border-red-100 rounded text-2xs">
                    <strong className="text-red-600">Errore:</strong>
                    <p className="text-red-500 mt-0.5 break-words leading-tight">{log.error}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="animate-pulse h-16 bg-gray-200 rounded w-full"></div>
        <div className="animate-pulse h-48 bg-gray-200 rounded w-full"></div>
        <div className="animate-pulse h-64 bg-gray-200 rounded w-full"></div>
        <div className="animate-pulse h-80 bg-gray-200 rounded w-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Si è verificato un errore: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <ExecutorControls />
      <DetailedStatsDisplay />
      <BudgetOverviewDisplay /> 
      <ActivityLogDisplay />
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
         <h3 className="text-lg font-semibold text-gray-900 mb-4">Visualizzatore Task del Workspace</h3>
         <TasksViewer workspaceId={workspaceId} />
      </div>
    </div>
  );
}