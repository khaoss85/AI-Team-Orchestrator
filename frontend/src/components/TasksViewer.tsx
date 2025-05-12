import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

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
}

interface TasksViewerProps {
  workspaceId: string;
}

export default function TasksViewer({ workspaceId }: TasksViewerProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
    // Refresh every 30 seconds
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
        <button 
          onClick={fetchTasks}
          className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-md text-sm hover:bg-indigo-100 transition"
        >
          Aggiorna
        </button>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          {error}
        </div>
      )}

      {tasks.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          Nessun task trovato per questo workspace
        </p>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div key={task.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium text-gray-900">{task.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(task.status)}`}>
                  {getStatusLabel(task.status)}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
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
              
              {task.result && (
                <div className="mt-4 p-3 bg-gray-50 rounded-md">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Risultato:</h5>
                  <pre className="text-xs text-gray-600 overflow-auto max-h-32">
                    {JSON.stringify(task.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}