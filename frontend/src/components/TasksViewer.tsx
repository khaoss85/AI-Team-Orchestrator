// frontend/src/components/TasksViewer.tsx - ENHANCED WITH ASSET SUPPORT

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { useAssetManagement } from '@/hooks/useAssetManagement';

interface Task {
  id: string;
  workspace_id: string;
  agent_id?: string;
  name: string;
  description?: string;
  status: string;
  result?: any;
  created_at: string;
  updated_at: string;
  context_data?: {
    asset_production?: boolean;
    asset_oriented_task?: boolean;
    asset_type?: string;
    detected_asset_type?: string;
    project_phase?: 'ANALYSIS' | 'IMPLEMENTATION' | 'FINALIZATION';
    is_final_deliverable?: boolean;
    deliverable_aggregation?: boolean;
    [key: string]: any;
  };
}

interface TasksViewerProps {
  workspaceId: string;
}

// Asset indicator component for tasks
const AssetTaskIndicator: React.FC<{ 
  task: Task; 
  assetType?: string | null;
}> = ({ task, assetType }) => {
  const getAssetIcon = (type: string | null) => {
    if (!type) return '🎯';
    const lowerType = type.toLowerCase();
    if (lowerType.includes('calendar')) return '📅';
    if (lowerType.includes('contact') || lowerType.includes('database')) return '📊';
    if (lowerType.includes('content')) return '📝';
    if (lowerType.includes('strategy')) return '🎯';
    if (lowerType.includes('analysis')) return '📈';
    return '🎯';
  };

  const getAssetColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'failed': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getAssetColor(task.status)}`}>
      <span className="mr-1">{getAssetIcon(assetType)}</span>
      <span>ASSET</span>
      {assetType && (
        <span className="ml-1 text-xs opacity-75">
          {assetType.replace(/_/g, ' ').toUpperCase()}
        </span>
      )}
    </div>
  );
};

// Final deliverable indicator
const FinalDeliverableIndicator: React.FC<{ task: Task }> = ({ task }) => {
  return (
    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-800 border border-purple-300">
      <span className="mr-1">🎯</span>
      <span className="font-bold">DELIVERABLE FINALE</span>
      {task.status === 'completed' && (
        <span className="ml-2 text-green-600">✅</span>
      )}
    </div>
  );
};

// Enhanced Task Card with Asset Support
const TaskCard: React.FC<{
  task: Task;
  assetType?: string | null;
  isAssetTask: boolean;
  isFinalDeliverable: boolean;
  onViewResult?: () => void;
}> = ({ task, assetType, isAssetTask, isFinalDeliverable, onViewResult }) => {
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('it-IT');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'canceled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'In attesa';
      case 'in_progress': return 'In corso';
      case 'completed': return 'Completato';
      case 'failed': return 'Fallito';
      case 'canceled': return 'Annullato';
      default: return status;
    }
  };

  const getTaskPriorityFromContext = () => {
    if (isFinalDeliverable) return 1;
    if (isAssetTask) return 2;
    return 3;
  };

  return (
    <div className={`border rounded-lg p-4 transition-all duration-200 ${
      isFinalDeliverable 
        ? 'border-purple-300 bg-gradient-to-r from-purple-50 to-indigo-50 shadow-lg'
        : isAssetTask 
          ? 'border-blue-300 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300'
    }`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 mb-2">{task.name}</h4>
          {task.description && (
            <p className="text-sm text-gray-600 mb-2">{task.description}</p>
          )}
          
          {/* Special indicators */}
          <div className="flex flex-wrap gap-2 mb-2">
            {isFinalDeliverable && <FinalDeliverableIndicator task={task} />}
            {isAssetTask && !isFinalDeliverable && (
              <AssetTaskIndicator task={task} assetType={assetType} />
            )}
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(task.status)}`}>
              {getStatusLabel(task.status)}
            </span>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
        <div>
          <span className="text-gray-500">Task ID:</span>
          <p className="font-mono">{task.id.substring(0, 8)}...</p>
        </div>
        
        {task.agent_id && (
          <div>
            <span className="text-gray-500">Agente ID:</span>
            <p className="font-mono">{task.agent_id.substring(0, 8)}...</p>
          </div>
        )}
        
        <div>
          <span className="text-gray-500">Creato:</span>
          <p>{formatTimestamp(task.created_at)}</p>
        </div>
      </div>

      {/* Enhanced result display for asset tasks */}
      {task.result && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <div className="flex justify-between items-center mb-2">
            <h5 className="text-sm font-medium text-gray-700">Risultato:</h5>
            {(isAssetTask || isFinalDeliverable) && onViewResult && (
              <button
                onClick={onViewResult}
                className="text-xs bg-indigo-600 text-white px-2 py-1 rounded hover:bg-indigo-700 transition"
              >
                Visualizza Asset
              </button>
            )}
          </div>
          
          {task.status === 'completed' && (
            <div>
              {/* Show summary */}
              <div className="text-sm text-gray-700 mb-2">
                {task.result.summary || task.result.output || 'Task completato con successo'}
              </div>
              
              {/* Asset-specific result indicators */}
              {isAssetTask && (
                <div className="bg-blue-100 border border-blue-200 rounded p-2 mb-2">
                  <div className="text-xs text-blue-800 font-medium mb-1">Asset Prodotto:</div>
                  <div className="text-xs text-blue-700">
                    {assetType ? `Tipo: ${assetType.replace(/_/g, ' ')}` : 'Asset generico'}
                  </div>
                  {task.result.detailed_results_json && (
                    <div className="text-xs text-blue-700">
                      ✅ Dati strutturati disponibili
                    </div>
                  )}
                </div>
              )}
              
              {/* Final deliverable indicators */}
              {isFinalDeliverable && (
                <div className="bg-purple-100 border border-purple-200 rounded p-2 mb-2">
                  <div className="text-xs text-purple-800 font-medium mb-1">🎯 Deliverable Finale Completato:</div>
                  {task.result.actionable_assets && (
                    <div className="text-xs text-purple-700">
                      📦 Asset azionabili inclusi: {Object.keys(task.result.actionable_assets).length}
                    </div>
                  )}
                  {task.result.automation_ready && (
                    <div className="text-xs text-purple-700">
                      🤖 Pronto per automazione
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {task.status === 'failed' && (
            <div className="text-sm text-red-700">
              ❌ Errore: {task.result.error || 'Task fallito'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function TasksViewer({ workspaceId }: TasksViewerProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [filterType, setFilterType] = useState<'all' | 'assets' | 'deliverables' | 'normal'>('all');

  // Use asset management hook
  const {
    isAssetTask,
    getAssetTypeFromTask,
    getAssetCompletionStats,
    loading: assetLoading
  } = useAssetManagement(workspaceId);

  // Enhanced tasks with asset information
  const enhancedTasks = React.useMemo(() => {
    return tasks.map(task => {
      const isAsset = isAssetTask(task);
      const assetType = isAsset ? getAssetTypeFromTask(task) : null;
      const isFinalDeliverable = Boolean(
        task.context_data?.is_final_deliverable ||
        task.context_data?.deliverable_aggregation ||
        task.name?.includes('🎯')
      );
      
      return {
        ...task,
        isAssetTask: isAsset,
        assetType,
        isFinalDeliverable,
        priority: isFinalDeliverable ? 1 : isAsset ? 2 : 3
      };
    }).sort((a, b) => a.priority - b.priority); // Sort by priority
  }, [tasks, isAssetTask, getAssetTypeFromTask]);

  // Filter tasks based on selected filter
  const filteredTasks = React.useMemo(() => {
    let filtered = enhancedTasks;
    
    switch (filterType) {
      case 'assets':
        filtered = enhancedTasks.filter(t => t.isAssetTask && !t.isFinalDeliverable);
        break;
      case 'deliverables':
        filtered = enhancedTasks.filter(t => t.isFinalDeliverable);
        break;
      case 'normal':
        filtered = enhancedTasks.filter(t => !t.isAssetTask && !t.isFinalDeliverable);
        break;
      default:
        // 'all' - no filtering
        break;
    }
    
    return filtered;
  }, [enhancedTasks, filterType]);

  const displayedTasks = showAll ? filteredTasks : filteredTasks.slice(0, 5);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000);
    return () => clearInterval(interval);
  }, [workspaceId]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${api.getBaseUrl()}/monitoring/workspace/${workspaceId}/tasks`);
      if (response.ok) {
        const tasksData = await response.json();
        setTasks(tasksData);
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Impossibile caricare i task');
    } finally {
      setLoading(false);
    }
  };

  const assetStats = getAssetCompletionStats();

  if (loading && tasks.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2">Caricamento task...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium">Task del Workspace</h3>
        <div className="flex items-center space-x-3">
          {/* Filter buttons */}
          <div className="flex rounded-md shadow-sm">
            {[
              { key: 'all', label: 'Tutti', count: enhancedTasks.length },
              { key: 'deliverables', label: '🎯 Finali', count: enhancedTasks.filter(t => t.isFinalDeliverable).length },
              { key: 'assets', label: '📦 Asset', count: enhancedTasks.filter(t => t.isAssetTask && !t.isFinalDeliverable).length },
              { key: 'normal', label: 'Normali', count: enhancedTasks.filter(t => !t.isAssetTask && !t.isFinalDeliverable).length },
            ].map((filter, index, array) => (
              <button
                key={filter.key}
                onClick={() => setFilterType(filter.key as any)}
                className={`px-3 py-1 text-xs font-medium ${
                  index === 0 ? 'rounded-l-md' : ''
                } ${
                  index === array.length - 1 ? 'rounded-r-md' : ''
                } ${
                  filterType === filter.key
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {filter.label}
                {filter.count > 0 && (
                  <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs ${
                    filterType === filter.key
                      ? 'bg-indigo-400 text-indigo-100'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {filter.count}
                  </span>
                )}
              </button>
            ))}
          </div>
          
          <button 
            onClick={fetchTasks}
            className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-md text-sm hover:bg-indigo-100 transition"
          >
            Aggiorna
          </button>
        </div>
      </div>

      {/* Asset completion summary */}
      {assetStats.totalAssets > 0 && (
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-blue-800">📦 Progresso Asset</h4>
            <span className="text-sm text-blue-700">
              {assetStats.completedAssets}/{assetStats.totalAssets} completati
            </span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${assetStats.completionRate}%` }}
            ></div>
          </div>
          {assetStats.isDeliverableReady && (
            <div className="mt-2 text-sm text-green-700 flex items-center">
              <span className="mr-1">🎯</span>
              Deliverable pronto per la creazione!
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          {error}
        </div>
      )}

      {filteredTasks.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          {filterType === 'all' 
            ? 'Nessun task trovato per questo workspace'
            : `Nessun task di tipo "${filterType}" trovato`
          }
        </p>
      ) : (
        <>
          <div className="space-y-4 max-h-96 overflow-y-auto custom-scrollbar pr-2">
            {displayedTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                assetType={task.assetType}
                isAssetTask={task.isAssetTask}
                isFinalDeliverable={task.isFinalDeliverable}
                onViewResult={() => {
                  // TODO: Open asset viewer modal or navigate to asset details
                  console.log('View asset result for task:', task.id);
                }}
              />
            ))}
          </div>
          
          {/* Show more/less buttons */}
          {!showAll && filteredTasks.length > 5 && (
            <div className="mt-4 text-center border-t pt-4">
              <button
                onClick={() => setShowAll(true)}
                className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md text-sm hover:bg-indigo-100 transition inline-flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                Mostra tutti i {filteredTasks.length} task
              </button>
            </div>
          )}
          
          {showAll && filteredTasks.length > 5 && (
            <div className="mt-4 text-center border-t pt-4">
              <button
                onClick={() => setShowAll(false)}
                className="px-4 py-2 bg-gray-50 text-gray-600 rounded-md text-sm hover:bg-gray-100 transition inline-flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
                Mostra meno
              </button>
            </div>
          )}
          
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              {showAll 
                ? `Visualizzati ${filteredTasks.length} su ${filteredTasks.length}` 
                : `Visualizzati ${Math.min(5, filteredTasks.length)} su ${filteredTasks.length}`
              } task ({filterType === 'all' ? 'tutti' : filterType})
            </p>
          </div>
        </>
      )}
    </div>
  );
}