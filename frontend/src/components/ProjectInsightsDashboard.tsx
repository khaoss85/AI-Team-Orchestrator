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
          <div className="grid grid-cols-3 gap-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
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
        <h2 className="text-lg font-medium">📊 Stato del Progetto</h2>
        <button 
          onClick={fetchInsights}
          className="text-indigo-600 text-sm hover:underline"
        >
          Aggiorna
        </button>
      </div>

      {/* Overview Cards - Solo le info più importanti */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Progress */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-blue-700 font-medium">Avanzamento</span>
            <span className="text-2xl font-bold text-blue-800">
              {insights.overview.progress_percentage}%
            </span>
          </div>
          <div className="text-xs text-blue-600 mb-2">
            {insights.overview.completed_tasks}/{insights.overview.total_tasks} task completati
          </div>
          <div className="bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${insights.overview.progress_percentage}%` }}
            ></div>
          </div>
        </div>

        {/* Timing */}
        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-purple-700 font-medium">Tempo</span>
            <span className="text-2xl">{getPhaseIcon(insights.current_state.phase)}</span>
          </div>
          <div className="text-sm text-purple-800 font-semibold">
            {insights.current_state.phase}
          </div>
          <div className="text-xs text-purple-600 mt-1">
            {Math.round(insights.timing.time_elapsed_days)} giorni trascorsi
          </div>
          {insights.timing.estimated_completion_date && (
            <div className="text-xs text-purple-600 mt-1">
              Fine prevista: {formatDate(insights.timing.estimated_completion_date)}
            </div>
          )}
        </div>

        {/* Health & Performance */}
        <div className={`p-4 rounded-lg border ${getHealthColor(insights.overview.health_score)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Stato Generale</span>
            <span className="text-2xl font-bold">
              {insights.overview.health_score}
            </span>
          </div>
          <div className="text-sm font-medium">
            {insights.overview.health_score >= 80 ? '🟢 Ottimo' : 
             insights.overview.health_score >= 60 ? '🟡 Buono' : '🔴 Attenzione'}
          </div>
          <div className="text-xs mt-1 opacity-75">
            ${insights.performance.total_cost.toFixed(2)} spesi totali
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 p-3 rounded text-center">
          <div className="text-2xl font-bold text-indigo-600">{insights.overview.in_progress_tasks}</div>
          <div className="text-xs text-gray-600">In corso</div>
        </div>
        <div className="bg-gray-50 p-3 rounded text-center">
          <div className="text-2xl font-bold text-orange-600">{insights.overview.pending_tasks}</div>
          <div className="text-xs text-gray-600">In attesa</div>
        </div>
        <div className="bg-gray-50 p-3 rounded text-center">
          <div className="text-2xl font-bold text-green-600">{insights.current_state.active_agents}</div>
          <div className="text-xs text-gray-600">Agenti attivi</div>
        </div>
        <div className="bg-gray-50 p-3 rounded text-center">
          <div className="text-2xl font-bold text-red-600">{insights.overview.failed_tasks}</div>
          <div className="text-xs text-gray-600">Task falliti</div>
        </div>
      </div>

      {/* Recent Activity - Solo gli eventi più importanti */}
      {insights.recent_highlights.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">🎯 Ultimi Eventi</h3>
          <div className="space-y-2">
            {insights.recent_highlights.slice(0, 3).map((event, index) => (
              <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                <div className="flex items-center space-x-3">
                  <span className="text-xs text-gray-500 min-w-0 flex-shrink-0">
                    {new Date(event.timestamp).toLocaleString('it-IT', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                  <span className="text-sm truncate">{event.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}