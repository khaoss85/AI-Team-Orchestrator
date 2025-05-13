import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface ProjectInsights {
  overview: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    pending_tasks: number;
    failed_tasks: number;
    progress_percentage: number;
    health_score: number;
  };
  timing: {
    time_elapsed_days: number;
    avg_task_completion_hours: number;
    estimated_completion_days?: number;
    estimated_completion_date?: string;
  };
  current_state: {
    phase: string;
    status: string;
    active_agents: number;
    total_agents: number;
  };
  performance: {
    cost_per_completed_task: number;
    total_cost: number;
    budget_utilization: number;
    agent_activity: {
      most_active_agent?: string;
      recently_active_agents: number;
      total_agents: number;
    };
  };
  recent_highlights: Array<{
    timestamp: string;
    event: string;
    description: string;
    task_name: string;
  }>;
}

interface ProjectInsightsDashboardProps {
  workspaceId: string;
}

export default function ProjectInsightsDashboard({ workspaceId }: ProjectInsightsDashboardProps) {
  const [insights, setInsights] = useState<ProjectInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInsights();
  }, [workspaceId]);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const data = await fetch(`${api.getBaseUrl()}/projects/${workspaceId}/insights`);
      if (!data.ok) throw new Error('Failed to fetch insights');
      const insightsData = await data.json();
      setInsights(insightsData);
      setError(null);
    } catch (err) {
      console.error('Error fetching insights:', err);
      setError('Impossibile caricare gli insights del progetto');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Non disponibile';
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatTime = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)} min`;
    if (hours < 24) return `${Math.round(hours)} ore`;
    return `${Math.round(hours / 24)} giorni`;
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getPhaseIcon = (phase: string) => {
    if (phase.includes('Initialization') || phase.includes('Planning')) return '🚀';
    if (phase.includes('Analysis') || phase.includes('Research')) return '🔍';
    if (phase.includes('Implementation') || phase.includes('Development')) return '⚙️';
    if (phase.includes('Testing') || phase.includes('Validation')) return '✅';
    if (phase.includes('Optimization')) return '📈';
    if (phase.includes('Completion') || phase.includes('Finalization')) return '🎯';
    return '📋';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-500 text-center">{error}</div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-gray-500 text-center">Nessun insight disponibile</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium">Stato del Progetto</h2>
        <button 
          onClick={fetchInsights}
          className="text-indigo-600 text-sm hover:underline"
        >
          Aggiorna
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Progress Card */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-blue-700 font-medium">Avanzamento</span>
            <span className="text-blue-600 text-xs">
              {insights.overview.completed_tasks}/{insights.overview.total_tasks} task
            </span>
          </div>
          <div className="flex items-center">
            <span className="text-2xl font-bold text-blue-800">
              {insights.overview.progress_percentage}%
            </span>
          </div>
          <div className="mt-2 bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${insights.overview.progress_percentage}%` }}
            ></div>
          </div>
        </div>

        {/* Health Score Card */}
        <div className={`p-4 rounded-lg border ${getHealthColor(insights.overview.health_score)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Salute Progetto</span>
            <span className="text-xs">0-100</span>
          </div>
          <div className="flex items-center">
            <span className="text-2xl font-bold">
              {insights.overview.health_score}
            </span>
            <span className="ml-2 text-sm">
              {insights.overview.health_score >= 80 ? '🟢' : 
               insights.overview.health_score >= 60 ? '🟡' : '🔴'}
            </span>
          </div>
          <div className="mt-1 text-xs opacity-75">
            {insights.overview.health_score >= 80 ? 'Ottimo' : 
             insights.overview.health_score >= 60 ? 'Buono' : 'Necessita attenzione'}
          </div>
        </div>

        {/* Current Phase Card */}
        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-purple-700 font-medium">Fase Attuale</span>
            <span className="text-2xl">{getPhaseIcon(insights.current_state.phase)}</span>
          </div>
          <div className="text-lg font-semibold text-purple-800">
            {insights.current_state.phase}
          </div>
          <div className="text-xs text-purple-600 mt-1">
            {insights.current_state.active_agents}/{insights.current_state.total_agents} agenti attivi
          </div>
        </div>
      </div>

      {/* Timing Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">⏱️ Tempi di Progetto</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Tempo trascorso:</span>
              <span className="font-medium">{Math.round(insights.timing.time_elapsed_days)} giorni</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tempo medio per task:</span>
              <span className="font-medium">{formatTime(insights.timing.avg_task_completion_hours)}</span>
            </div>
            {insights.timing.estimated_completion_date && (
              <div className="flex justify-between">
                <span className="text-gray-600">Completamento stimato:</span>
                <span className="font-medium text-indigo-600">
                  {formatDate(insights.timing.estimated_completion_date)}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">💰 Performance</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Costo totale:</span>
              <span className="font-medium">${insights.performance.total_cost.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Costo per task:</span>
              <span className="font-medium">${insights.performance.cost_per_completed_task.toFixed(2)}</span>
            </div>
            {insights.performance.agent_activity.most_active_agent && (
              <div className="flex justify-between">
                <span className="text-gray-600">Agente più attivo:</span>
                <span className="font-medium">{insights.performance.agent_activity.most_active_agent}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Highlights */}
      <div>
        <h3 className="font-medium text-gray-900 mb-3">📌 Eventi Recenti</h3>
        {insights.recent_highlights.length > 0 ? (
          <div className="space-y-2">
            {insights.recent_highlights.map((event, index) => (
              <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                <div className="flex items-center space-x-3">
                  <span className="text-xs text-gray-500">
                    {new Date(event.timestamp).toLocaleString('it-IT', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                  <span className="text-sm">{event.description}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Nessun evento recente</p>
        )}
      </div>
    </div>
  );
}