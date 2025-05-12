import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import TasksViewer from './TasksViewer';

interface ActivityLog {
  timestamp: string;
  event: string;
  task_id?: string;
  agent_id?: string;
  workspace_id: string;
  execution_time?: number;
  cost?: number;
  result_summary?: string;
  error?: string;
}

interface BudgetSummary {
  total_cost: number;
  agent_costs: Record<string, number>;
  total_tokens: {
    input: number;
    output: number;
  };
  currency: string;
  budget_limit?: number;
  budget_percentage?: number;
}

interface MonitoringDashboardProps {
  workspaceId: string;
}

export default function MonitoringDashboard({ workspaceId }: MonitoringDashboardProps) {
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [budget, setBudget] = useState<BudgetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Auto-refresh interval
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [workspaceId]);

  const fetchData = async () => {
    const isInitialLoad = !activity.length && !budget;
    
    try {
      if (isInitialLoad) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      
      // Fetch activity logs and budget in parallel
      const [activityPromise, budgetPromise] = await Promise.allSettled([
        fetch(`${api.getBaseUrl()}/monitoring/workspace/${workspaceId}/activity?limit=20`),
        fetch(`${api.getBaseUrl()}/monitoring/workspace/${workspaceId}/budget`)
      ]);
      
      // Handle activity data
      if (activityPromise.status === 'fulfilled' && activityPromise.value.ok) {
        const logs = await activityPromise.value.json();
        setActivity(logs);
      }
      
      // Handle budget data
      if (budgetPromise.status === 'fulfilled' && budgetPromise.value.ok) {
        const budgetInfo = await budgetPromise.value.json();
        setBudget(budgetInfo);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching monitoring data:', err);
      setError('Impossibile caricare i dati di monitoraggio');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString('it-IT'),
      time: date.toLocaleTimeString('it-IT', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      })
    };
  };

  const getEventIcon = (event: string) => {
    switch (event) {
      case 'task_started': return '▶️';
      case 'task_completed': return '✅';
      case 'task_failed': return '❌';
      case 'initial_task_created': return '🆕';
      default: return '📝';
    }
  };

  const getEventColor = (event: string) => {
    switch (event) {
      case 'task_started': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'task_completed': return 'bg-green-50 text-green-700 border-green-200';
      case 'task_failed': return 'bg-red-50 text-red-700 border-red-200';
      case 'initial_task_created': return 'bg-purple-50 text-purple-700 border-purple-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(6)}`;
  };

  const BudgetOverview = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Budget Overview</h3>
        {budget && (
          <div className="text-sm text-gray-500">
            Aggiornato: {formatTimestamp(new Date().toISOString()).time}
          </div>
        )}
      </div>
      
      {!budget ? (
        <div className="text-center py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-600 font-medium">Costo Totale</p>
              <p className="text-2xl font-bold text-blue-800">{formatCost(budget.total_cost)}</p>
              <p className="text-xs text-blue-600 mt-1">{budget.currency}</p>
            </div>
            
            <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <p className="text-sm text-green-600 font-medium">Token Totali</p>
              <p className="text-lg font-semibold text-green-800">
                {(budget.total_tokens.input + budget.total_tokens.output).toLocaleString()}
              </p>
              <p className="text-xs text-green-600 mt-1">
                {budget.total_tokens.input.toLocaleString()} input + {budget.total_tokens.output.toLocaleString()} output
              </p>
            </div>
            
            {budget.budget_limit ? (
              <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                <p className="text-sm text-purple-600 font-medium">Budget Utilizzato</p>
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
                  Limite: €{budget.budget_limit}
                </p>
              </div>
            ) : (
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 font-medium">Nessun Limite</p>
                <p className="text-lg text-gray-800">Budget illimitato</p>
                <p className="text-xs text-gray-500 mt-1">Nessun limite impostato</p>
              </div>
            )}
          </div>

          {/* Agent Costs Breakdown */}
          {Object.keys(budget.agent_costs).length > 0 && (
            <div className="border-t pt-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Costi per Agente</h4>
              <div className="space-y-3">
                {Object.entries(budget.agent_costs)
                  .sort(([,a], [,b]) => b - a) // Sort by cost descending
                  .map(([agentId, cost]) => {
                    const percentage = budget.total_cost > 0 ? (cost / budget.total_cost) * 100 : 0;
                    return (
                      <div key={agentId} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-900">
                            Agente {agentId.substring(0, 8)}...
                          </span>
                          <span className="font-semibold text-gray-800">{formatCost(cost)}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% del totale</p>
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

  const ActivityLog = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Log Attività Recente</h3>
        <button 
          onClick={fetchData}
          disabled={isRefreshing}
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
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Aggiorna
            </>
          )}
        </button>
      </div>
      
      {activity.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <p className="text-gray-500 text-lg">Nessuna attività registrata</p>
          <p className="text-gray-400 text-sm mt-2">I log delle attività appariranno qui quando il team inizierà a lavorare</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {activity.map((log, index) => {
            const formattedTime = formatTimestamp(log.timestamp);
            return (
              <div key={index} className={`border rounded-lg p-4 transition-all duration-200 hover:shadow-md ${getEventColor(log.event)}`}>
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{getEventIcon(log.event)}</span>
                    <div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border`}>
                        {log.event.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      <div className="text-xs text-gray-500 mt-1">
                        {formattedTime.date} alle {formattedTime.time}
                      </div>
                    </div>
                  </div>
                  
                  {log.cost && (
                    <div className="text-right">
                      <span className="text-lg font-bold">{formatCost(log.cost)}</span>
                      <div className="text-xs text-gray-500">costo</div>
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {log.task_id && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500 w-16">Task:</span>
                      <span className="font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
                        {log.task_id.substring(0, 8)}...
                      </span>
                    </div>
                  )}
                  {log.agent_id && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500 w-16">Agente:</span>
                      <span className="font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
                        {log.agent_id.substring(0, 8)}...
                      </span>
                    </div>
                  )}
                  {log.execution_time && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500 w-16">Tempo:</span>
                      <span className="font-semibold">{log.execution_time}s</span>
                    </div>
                  )}
                </div>
                
                {log.result_summary && (
                  <div className="mt-3 p-3 bg-white bg-opacity-50 rounded-md">
                    <span className="text-gray-600 font-medium text-sm">Risultato:</span>
                    <p className="text-sm mt-1">{log.result_summary}</p>
                  </div>
                )}
                
                {log.error && (
                  <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded-md">
                    <span className="text-red-700 font-medium text-sm">Errore:</span>
                    <p className="text-sm text-red-600 mt-1">{log.error}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  if (loading && !activity.length && !budget) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center p-12 bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600 text-lg">Caricamento dashboard di monitoraggio...</p>
            <p className="text-gray-400 text-sm mt-2">Raccolta dati su budget e attività</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        </div>
      )}

      {/* Budget Overview */}
      <BudgetOverview />

      {/* Activity Log */}
      <ActivityLog />
      
      {/* Tasks Viewer */}
      <TasksViewer workspaceId={workspaceId} />
    </div>
  );
}