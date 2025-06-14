'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Agent } from '@/types';
import GoalProgressTracker from '@/components/GoalProgressTracker';
import GoalValidationDashboard from '@/components/GoalValidationDashboard';

type Props = {
  params: Promise<{ id: string }>;
};

export default function ProjectProgressPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const [tasks, setTasks] = useState<any[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch simplified task data
      const tasksResponse = await fetch(`${api.getBaseUrl()}/monitoring/workspace/${id}/tasks`);
      if (tasksResponse.ok) {
        const tasksData = await tasksResponse.json();
        setTasks(Array.isArray(tasksData) ? tasksData : tasksData.tasks || []);
      }
      
      // Fetch agents
      const agentsData = await api.agents.list(id);
      setAgents(agentsData);
      
      setError(null);
    } catch (err) {
      console.error('Error fetching progress data:', err);
      setError(err instanceof Error ? err.message : 'Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  // Calculate simplified stats
  const stats = React.useMemo(() => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length;
    const pendingTasks = tasks.filter(t => t.status === 'pending').length;
    const failedTasks = tasks.filter(t => t.status === 'failed').length;
    
    const totalCost = tasks.reduce((sum, t) => sum + (t.result?.cost_estimated || 0), 0);
    const totalTime = tasks.reduce((sum, t) => sum + (t.result?.execution_time_seconds || 0), 0);
    
    const richContentTasks = tasks.filter(t => t.result?.detailed_results_json).length;
    
    return {
      totalTasks,
      completedTasks,
      inProgressTasks,
      pendingTasks,
      failedTasks,
      totalCost,
      totalTime,
      richContentTasks,
      completionRate: totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0,
      successRate: totalTasks > 0 ? Math.round((completedTasks / (completedTasks + failedTasks)) * 100) : 0
    };
  }, [tasks]);

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-20 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-4 text-gray-600">Caricamento progresso...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${id}`} className="text-blue-600 hover:underline text-sm mb-2 block">
            ← Torna al progetto
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Progresso Progetto</h1>
          <p className="text-gray-600">Stato avanzamento e obiettivi raggiunti</p>
        </div>
      </div>

      {/* Goal Progress - Primary Focus */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <GoalProgressTracker 
          workspaceId={id}
          showValidation={true}
          autoRefresh={true}
        />
        <GoalValidationDashboard 
          workspaceId={id}
        />
      </div>

      {/* Simplified Task Statistics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">📊 Riepilogo Esecuzione</h2>
        
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className={`p-4 rounded-lg border text-center ${getStatusColor('completed')}`}>
            <div className="text-2xl font-bold">{stats.completedTasks}</div>
            <div className="text-sm">Completati</div>
            <div className="text-xs mt-1">{stats.completionRate}% del totale</div>
          </div>
          <div className={`p-4 rounded-lg border text-center ${getStatusColor('in_progress')}`}>
            <div className="text-2xl font-bold">{stats.inProgressTasks}</div>
            <div className="text-sm">In Corso</div>
          </div>
          <div className={`p-4 rounded-lg border text-center ${getStatusColor('pending')}`}>
            <div className="text-2xl font-bold">{stats.pendingTasks}</div>
            <div className="text-sm">In Attesa</div>
          </div>
          <div className={`p-4 rounded-lg border text-center ${getStatusColor('failed')}`}>
            <div className="text-2xl font-bold">{stats.failedTasks}</div>
            <div className="text-sm">Falliti</div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-700">{stats.successRate}%</div>
            <div className="text-sm text-blue-600">Tasso di Successo</div>
            <div className="text-xs text-blue-500 mt-1">
              {stats.completedTasks} successi su {stats.completedTasks + stats.failedTasks} completati
            </div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-700">{stats.richContentTasks}</div>
            <div className="text-sm text-purple-600">Asset Strutturati</div>
            <div className="text-xs text-purple-500 mt-1">
              Contenuti avanzati generati
            </div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-700">
              ${stats.totalCost.toFixed(4)}
            </div>
            <div className="text-sm text-green-600">Costo Totale</div>
            <div className="text-xs text-green-500 mt-1">
              {(stats.totalTime / 60).toFixed(1)}m tempo elaborazione
            </div>
          </div>
        </div>
      </div>

      {/* Agent Performance Summary */}
      {agents.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">👥 Performance Team</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map(agent => {
              const agentTasks = tasks.filter(t => t.agent_id === agent.id);
              const completedTasks = agentTasks.filter(t => t.status === 'completed').length;
              const agentCost = agentTasks.reduce((sum, t) => sum + (t.result?.cost_estimated || 0), 0);
              const richTasks = agentTasks.filter(t => t.result?.detailed_results_json).length;
              
              return (
                <div key={agent.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium mr-3 ${
                      agent.seniority === 'expert' ? 'bg-purple-100 text-purple-700' :
                      agent.seniority === 'senior' ? 'bg-blue-100 text-blue-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {agent.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">
                        {agent.name}
                        {agent.seniority === 'expert' && (
                          <span className="ml-1 text-xs text-purple-600">★</span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">{agent.role}</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Task completati:</span>
                      <span className="font-medium">{completedTasks}/{agentTasks.length}</span>
                    </div>
                    {agentCost > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Costo:</span>
                        <span className="font-medium">${agentCost.toFixed(4)}</span>
                      </div>
                    )}
                    {richTasks > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Asset avanzati:</span>
                        <span className="font-medium text-purple-600">✨ {richTasks}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Activity - Simplified */}
      {tasks.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">🕐 Attività Recenti</h2>
            <Link
              href={`/projects/${id}/tasks`}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Visualizza tutti i task →
            </Link>
          </div>
          
          <div className="space-y-3">
            {tasks
              .filter(t => t.status === 'completed')
              .slice(0, 5)
              .map(task => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-green-600">✅</span>
                    <div>
                      <div className="font-medium text-gray-900">{task.name}</div>
                      <div className="text-sm text-gray-500">
                        {new Date(task.updated_at).toLocaleDateString('it-IT')}
                      </div>
                    </div>
                  </div>
                  {task.result?.detailed_results_json && (
                    <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                      ✨ Rich
                    </span>
                  )}
                </div>
              ))}
          </div>
          
          {stats.inProgressTasks > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-700">
                🔄 {stats.inProgressTasks} task attualmente in esecuzione
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-700">
            ⚠️ Errore nel caricamento dei dati: {error}
          </div>
        </div>
      )}
    </div>
  );
}