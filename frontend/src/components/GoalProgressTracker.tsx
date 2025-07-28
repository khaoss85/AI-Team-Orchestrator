// frontend/src/components/GoalProgressTracker.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface WorkspaceGoal {
  id: string;
  metric_type: string;
  target_value: number;
  current_value: number;
  unit: string;
  description: string;
  status: 'active' | 'completed' | 'paused';
  priority: number;
  created_at: string;
  last_progress_date?: string;
  completion_pct?: number;
  gap_value?: number;
  urgency_score?: number;
  semantic_context?: {
    deliverable_type?: string;
    business_value?: string;
    acceptance_criteria?: string[];
    execution_phase?: string;
    autonomy_level?: string;
    autonomy_reason?: string;
    available_tools?: string[];
    human_input_required?: string[];
    is_strategic_deliverable?: boolean;
  };
}

interface GoalProgressTrackerProps {
  workspaceId: string;
  showValidation?: boolean;
  autoRefresh?: boolean;
  className?: string;
  onViewAssets?: () => void; // Optional callback to view project assets
}

interface ValidationStatus {
  overall_achievement: number;
  validation_status: 'excellent' | 'good' | 'needs_improvement' | 'critical';
  critical_issues: number;
  recommendations: string[];
}

export const GoalProgressTracker: React.FC<GoalProgressTrackerProps> = ({
  workspaceId,
  showValidation = true,
  autoRefresh = false,
  className = '',
  onViewAssets
}) => {
  const [goals, setGoals] = useState<WorkspaceGoal[]>([]);
  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [expandedGoalId, setExpandedGoalId] = useState<string | null>(null);
  
  // 🎯 NEW: Goal-specific deliverables state
  const [goalDeliverables, setGoalDeliverables] = useState<{[goalId: string]: any[]}>({});
  const [deliverablesLoading, setDeliverablesLoading] = useState<{[goalId: string]: boolean}>({});
  
  // Team control states
  const [workspaceStatus, setWorkspaceStatus] = useState<'active' | 'paused' | 'completed' | 'created'>('active');
  const [teamControlLoading, setTeamControlLoading] = useState(false);

  const fetchWorkspaceStatus = async () => {
    try {
      const response = await api.workspaces.get(workspaceId);
      if (response.status) {
        setWorkspaceStatus(response.status);
      }
    } catch (error) {
      console.error('Error fetching workspace status:', error);
    }
  };

  const handlePauseTeam = async () => {
    setTeamControlLoading(true);
    try {
      const response = await api.workspaces.pause(workspaceId);
      if (response.success) {
        setWorkspaceStatus('paused');
        await refreshData(); // Refresh goals and validation
      } else {
        setError('Errore durante la pausa del team');
      }
    } catch (error) {
      console.error('Error pausing team:', error);
      setError('Errore durante la pausa del team');
    } finally {
      setTeamControlLoading(false);
    }
  };

  const handleResumeTeam = async () => {
    setTeamControlLoading(true);
    try {
      const response = await api.workspaces.resume(workspaceId);
      if (response.success) {
        setWorkspaceStatus('active');
        await refreshData(); // Refresh goals and validation
      } else {
        setError('Errore durante il riavvio del team');
      }
    } catch (error) {
      console.error('Error resuming team:', error);
      setError('Errore durante il riavvio del team');
    } finally {
      setTeamControlLoading(false);
    }
  };

  const fetchGoals = async () => {
    try {
      // Fetch ALL goals (not just active ones) to show completed goals in recap
      const response = await api.workspaceGoals.getAll(workspaceId);
      if (response.success) {
        // Calculate completion percentages
        const goalsWithProgress = response.goals.map((goal: any) => ({
          ...goal,
          completion_pct: goal.target_value > 0 ? (goal.current_value / goal.target_value * 100) : 0,
          gap_value: goal.target_value - goal.current_value
        }));
        
        // Sort goals: active first, then completed, then others
        const sortedGoals = goalsWithProgress.sort((a: any, b: any) => {
          if (a.status === 'active' && b.status !== 'active') return -1;
          if (b.status === 'active' && a.status !== 'active') return 1;
          if (a.status === 'completed' && b.status !== 'completed') return -1;
          if (b.status === 'completed' && a.status !== 'completed') return 1;
          return 0;
        });
        
        setGoals(sortedGoals);
      }
    } catch (err) {
      console.error('Error fetching goals:', err);
      setError('Failed to load goals');
    }
  };

  const fetchValidation = async () => {
    if (!showValidation) return;
    
    try {
      const response = await api.goalValidation.validateWorkspace(workspaceId);
      if (response.validation_results) {
        // Process validation results into summary
        const validations = response.validation_results;
        const avgAchievement = validations.reduce((sum: number, v: any) => 
          sum + (v.achievement_percentage || 0), 0) / validations.length;
        
        const criticalCount = validations.filter((v: any) => 
          v.severity === 'critical').length;
        
        let status: ValidationStatus['validation_status'] = 'excellent';
        if (avgAchievement < 30) status = 'critical';
        else if (avgAchievement < 60) status = 'needs_improvement';
        else if (avgAchievement < 85) status = 'good';

        setValidationStatus({
          overall_achievement: avgAchievement,
          validation_status: status,
          critical_issues: criticalCount,
          recommendations: validations.flatMap((v: any) => v.recommendations || []).slice(0, 3)
        });
      }
    } catch (err) {
      console.error('Error fetching validation:', err);
    }
  };

  // 🎯 NEW: Goal-specific deliverable functions
  const fetchGoalDeliverables = async (goalId: string) => {
    if (deliverablesLoading[goalId]) return;
    
    setDeliverablesLoading(prev => ({ ...prev, [goalId]: true }));
    try {
      const deliverables = await api.monitoring.getGoalDeliverables(workspaceId, goalId);
      setGoalDeliverables(prev => ({ ...prev, [goalId]: deliverables || [] }));
    } catch (error) {
      console.error(`Error fetching deliverables for goal ${goalId}:`, error);
      setGoalDeliverables(prev => ({ ...prev, [goalId]: [] }));
    } finally {
      setDeliverablesLoading(prev => ({ ...prev, [goalId]: false }));
    }
  };

  const createGoalDeliverable = async (goalId: string) => {
    setDeliverablesLoading(prev => ({ ...prev, [goalId]: true }));
    try {
      const result = await api.monitoring.createGoalDeliverable(workspaceId, goalId);
      if (result.success) {
        // Refresh deliverables for this goal
        await fetchGoalDeliverables(goalId);
      }
      return result;
    } catch (error) {
      console.error(`Error creating deliverable for goal ${goalId}:`, error);
      throw error;
    } finally {
      setDeliverablesLoading(prev => ({ ...prev, [goalId]: false }));
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([fetchGoals(), fetchValidation(), fetchWorkspaceStatus()]);
    setRefreshing(false);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchGoals(), fetchValidation(), fetchWorkspaceStatus()]);
      setLoading(false);
    };

    loadData();

    // Auto-refresh every 10 minutes if enabled (reduced to prevent rate limiting)
    if (autoRefresh) {
      const interval = setInterval(refreshData, 10 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [workspaceId, showValidation, autoRefresh]);

  const getGoalStatusColor = (goal: WorkspaceGoal): string => {
    if (goal.status === 'completed') return 'text-green-600';
    if (goal.completion_pct! < 30) return 'text-red-600';
    if (goal.completion_pct! < 70) return 'text-yellow-600';
    return 'text-blue-600';
  };

  const getValidationBadgeStyle = (status: ValidationStatus['validation_status']): string => {
    switch (status) {
      case 'excellent': return 'bg-green-100 text-green-800 border-green-200';
      case 'good': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'needs_improvement': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatMetricType = (type: string): string => {
    // Convert metric types to user-friendly names
    const typeMap: Record<string, string> = {
      'email_sequences': 'Sequenze Email',
      'deliverables': 'Deliverable', 
      'engagement_rate': 'Tasso Engagement',
      'contacts': 'Contatti ICP',
      'conversion_rate': 'Tasso Conversione',
      'revenue': 'Ricavi',
      'users': 'Utenti',
      'content_calendar': 'Calendario Contenuti',
      'strategy_document': 'Documento Strategico',
      'performance_monitoring': 'Monitoraggio Performance'
    };
    
    return typeMap[type] || type.replace(/_/g, ' ').split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatDescription = (description: string, goal: WorkspaceGoal): string => {
    // If description is too generic, create a more specific one
    if (description.toLowerCase().includes('create') && description.length < 50) {
      const friendlyType = formatMetricType(goal.metric_type);
      return `Completare ${friendlyType} per il progetto`;
    }
    
    // Truncate very long descriptions
    if (description.length > 80) {
      return description.substring(0, 77) + '...';
    }
    
    return description;
  };

  const getAutonomyInfo = (autonomyLevel: string | undefined) => {
    switch (autonomyLevel) {
      case 'autonomous':
        return { 
          icon: '🤖', 
          label: 'Autonomo', 
          color: 'bg-green-100 text-green-800',
          description: 'AI può completare autonomamente'
        };
      case 'assisted':
        return { 
          icon: '🤝', 
          label: 'Assistito', 
          color: 'bg-yellow-100 text-yellow-800',
          description: 'Richiede supervisione umana'
        };
      case 'human_required':
        return { 
          icon: '👤', 
          label: 'Umano', 
          color: 'bg-red-100 text-red-800',
          description: 'Richiede intervento umano diretto'
        };
      default:
        return { 
          icon: '❓', 
          label: 'Da analizzare', 
          color: 'bg-gray-100 text-gray-600',
          description: 'Autonomia non ancora determinata'
        };
    }
  };

  const toggleGoalExpansion = (goalId: string) => {
    setExpandedGoalId(expandedGoalId === goalId ? null : goalId);
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mr-2"></div>
          Loading goal progress...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="text-red-600 text-center">{error}</div>
      </div>
    );
  }

  // Calculate overall progress based on active and completed goals
  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');
  
  const overallProgress = goals.length > 0 
    ? (
        (activeGoals.reduce((sum, goal) => sum + goal.completion_pct!, 0) + (completedGoals.length * 100)) 
        / goals.length
      )
    : 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Overall Progress Summary */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-semibold flex items-center">
                🎯 Goal Progress Overview
              </h2>
              {completedGoals.length > 0 && (
                <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded border border-green-200">
                  {completedGoals.length} Completed
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {/* Team Control Buttons */}
              {workspaceStatus === 'active' ? (
                <button 
                  onClick={handlePauseTeam}
                  disabled={teamControlLoading}
                  className="px-3 py-1 text-sm border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50 disabled:opacity-50 transition-colors"
                  title="Metti in pausa le attività del team"
                >
                  {teamControlLoading ? '⏳' : '⏸️'} Pausa Team
                </button>
              ) : workspaceStatus === 'paused' ? (
                <button 
                  onClick={handleResumeTeam}
                  disabled={teamControlLoading}
                  className="px-3 py-1 text-sm border border-green-300 text-green-700 rounded-md hover:bg-green-50 disabled:opacity-50 transition-colors"
                  title="Riavvia le attività del team"
                >
                  {teamControlLoading ? '⏳' : '▶️'} Riavvia Team
                </button>
              ) : null}
              
              <button 
                onClick={() => setExpanded(!expanded)}
                className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50"
              >
                {expanded ? '📋 Compatta' : '📊 Dettagli'}
              </button>
              <button 
                onClick={refreshData}
                disabled={refreshing}
                className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                {refreshing ? '🔄' : '↻'} Refresh
              </button>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            {/* Overall Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium flex items-center gap-2">
                  Overall Progress
                  {workspaceStatus === 'paused' && (
                    <span className="px-2 py-0.5 text-xs bg-orange-100 text-orange-700 rounded border border-orange-200">
                      ⏸️ Team in Pausa
                    </span>
                  )}
                  {workspaceStatus === 'active' && (
                    <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded border border-green-200">
                      ▶️ Team Attivo
                    </span>
                  )}
                </span>
                <span className="text-sm text-gray-600">{overallProgress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    workspaceStatus === 'paused' ? 'bg-orange-500' : 'bg-blue-600'
                  }`}
                  style={{ width: `${Math.min(overallProgress, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Validation Status */}
            {showValidation && validationStatus && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">Validation Status:</span>
                  <span className={`px-2 py-1 text-xs rounded border ${getValidationBadgeStyle(validationStatus.validation_status)}`}>
                    {validationStatus.validation_status.replace('_', ' ').toUpperCase()}
                  </span>
                  {validationStatus.critical_issues > 0 && (
                    <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-800 border border-red-200">
                      {validationStatus.critical_issues} Critical Issues
                    </span>
                  )}
                </div>
                <span className="text-sm text-gray-600">
                  {validationStatus.overall_achievement.toFixed(1)}% Achievement
                </span>
              </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-bold text-green-700">
                  {goals.filter(g => g.status === 'completed').length}
                </div>
                <div className="text-xs text-green-600">Completed</div>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-bold text-blue-700">
                  {goals.filter(g => g.status === 'active' && g.completion_pct! >= 50).length}
                </div>
                <div className="text-xs text-blue-600">In Progress</div>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <div className="text-lg font-bold text-yellow-700">
                  {goals.filter(g => g.status === 'active' && g.completion_pct! < 50).length}
                </div>
                <div className="text-xs text-yellow-600">Behind</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Compact Summary - Show only when not expanded */}
      {!expanded && goals.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="text-sm text-gray-600 space-y-3">
            <div className="flex items-center justify-between">
              <span>📋 Todo List ({goals.length} obiettivi)</span>
              <span className="text-xs text-gray-500">Clicca "Dettagli" per visualizzazione completa</span>
            </div>
            
            {(() => {
              // Separate goals into metrics and deliverables
              const metrics = goals.filter(goal => 
                !goal.unit.includes('deliverable') && 
                ['contacts', 'engagement_rate', 'conversion_rate', 'revenue', 'users'].includes(goal.metric_type)
              );
              const deliverables = goals.filter(goal => 
                goal.unit.includes('deliverable') || 
                !['contacts', 'engagement_rate', 'conversion_rate', 'revenue', 'users'].includes(goal.metric_type)
              );
              
              // Show up to 5 total goals (prioritize showing at least some of each type)
              const goalsToShow = [];
              
              // Add up to 3 metrics first
              goalsToShow.push(...metrics.slice(0, 3));
              
              // Add deliverables to fill up to 5 total
              const remainingSlots = 5 - goalsToShow.length;
              goalsToShow.push(...deliverables.slice(0, remainingSlots));
              
              // If we still have slots and more metrics, add them
              if (goalsToShow.length < 5 && metrics.length > 3) {
                const additionalSlots = 5 - goalsToShow.length;
                goalsToShow.push(...metrics.slice(3, 3 + additionalSlots));
              }
              
              return (
                <div className="space-y-3">
                  {/* Final Metrics Section */}
                  {metrics.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-blue-600 mb-2">🎯 Metriche Finali</h4>
                      <div className="grid grid-cols-1 gap-1">
                        {goalsToShow.filter(goal => metrics.includes(goal)).map((goal) => (
                          <div key={goal.id} className="bg-blue-50 rounded border border-blue-100 overflow-hidden transition-all duration-200">
                            <div 
                              className="flex items-center justify-between p-2 cursor-pointer hover:bg-blue-100 transition-colors group"
                              onClick={() => toggleGoalExpansion(goal.id)}
                            >
                              <div className="flex items-center space-x-2 flex-1">
                                <span className="text-xs">
                                  {goal.status === 'completed' ? '✅' : goal.completion_pct! < 30 ? '⚠️' : '📊'}
                                </span>
                                <span className="text-sm font-medium">{formatMetricType(goal.metric_type)}</span>
                                <span className="text-xs text-blue-400 group-hover:text-blue-600 transition-colors">
                                  clicca per dettagli
                                </span>
                              </div>
                              <div className="text-xs text-gray-600 font-medium">
                                {goal.current_value}/{goal.target_value} {goal.unit}
                              </div>
                            </div>
                            
                            {/* Expanded Details con animazione smooth */}
                            <div className={`transition-all duration-300 ease-in-out ${
                              expandedGoalId === goal.id ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                            } overflow-hidden`}>
                              <div className="px-3 pb-3 border-t border-blue-200 bg-blue-25">
                                <div className="space-y-3 pt-3">
                                  <div className="text-xs text-gray-700">
                                    <strong>📝 Descrizione:</strong> {goal.description}
                                  </div>
                                  
                                  {/* Progress Bar visuale */}
                                  <div>
                                    <div className="flex justify-between items-center mb-1">
                                      <span className="text-xs font-medium text-gray-700">📈 Progresso</span>
                                      <span className="text-xs font-bold text-blue-600">{goal.completion_pct?.toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-blue-100 rounded-full h-2">
                                      <div 
                                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                        style={{ width: `${Math.min(goal.completion_pct || 0, 100)}%` }}
                                      ></div>
                                    </div>
                                    {goal.gap_value && goal.gap_value > 0 && (
                                      <div className="text-xs text-gray-600 mt-1">
                                        🎯 Mancano ancora <strong>{goal.gap_value} {goal.unit}</strong> per completare
                                      </div>
                                    )}
                                  </div>

                                  {goal.semantic_context?.autonomy_level && (
                                    <div className="bg-white rounded p-2 border border-blue-200">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <span className="text-xs font-medium">🤖 Modalità Esecuzione:</span>
                                        <span className={`px-2 py-1 text-xs rounded ${getAutonomyInfo(goal.semantic_context.autonomy_level).color}`}>
                                          {getAutonomyInfo(goal.semantic_context.autonomy_level).icon} {getAutonomyInfo(goal.semantic_context.autonomy_level).label}
                                        </span>
                                      </div>
                                      <div className="text-xs text-gray-600">
                                        {getAutonomyInfo(goal.semantic_context.autonomy_level).description}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {goal.semantic_context?.business_value && (
                                    <div className="text-xs text-gray-700 bg-white rounded p-2 border border-blue-200">
                                      <strong>💰 Valore Business:</strong> {goal.semantic_context.business_value}
                                    </div>
                                  )}
                                  
                                  {goal.semantic_context?.execution_phase && (
                                    <div className="text-xs text-gray-600">
                                      <strong>⏱️ Fase Progetto:</strong> {goal.semantic_context.execution_phase}
                                    </div>
                                  )}

                                  {/* 🎯 NEW: Goal-specific deliverable details */}
                                  {goal.completion_pct! >= 80 && (
                                    <div className="bg-white rounded p-2 border border-green-200">
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs font-medium text-green-700">📦 Goal Deliverables</span>
                                        <div className="flex space-x-1">
                                          {!goalDeliverables[goal.id] && (
                                            <button
                                              onClick={() => fetchGoalDeliverables(goal.id)}
                                              disabled={deliverablesLoading[goal.id]}
                                              className="px-2 py-1 bg-purple-100 text-purple-700 hover:bg-purple-200 rounded text-xs font-medium border border-purple-200 transition-colors disabled:opacity-50"
                                            >
                                              {deliverablesLoading[goal.id] ? '⏳' : '📋'} Check
                                            </button>
                                          )}
                                          {goalDeliverables[goal.id] && goalDeliverables[goal.id].length === 0 && (
                                            <button
                                              onClick={() => createGoalDeliverable(goal.id)}
                                              disabled={deliverablesLoading[goal.id]}
                                              className="px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs font-medium border border-green-200 transition-colors disabled:opacity-50"
                                            >
                                              {deliverablesLoading[goal.id] ? '⏳' : '📦'} Create
                                            </button>
                                          )}
                                        </div>
                                      </div>
                                      
                                      {goalDeliverables[goal.id] && goalDeliverables[goal.id].length > 0 ? (
                                        <div className="space-y-2">
                                          {goalDeliverables[goal.id].map((deliverable, idx) => (
                                            <div key={idx} className={`rounded p-2 border ${
                                              deliverable.type === 'low_value_warning' 
                                                ? 'bg-yellow-50 border-yellow-200' 
                                                : 'bg-green-50 border-green-100'
                                            }`}>
                                              {deliverable.type === 'low_value_warning' ? (
                                                <>
                                                  <div className="flex items-center mb-1">
                                                    <div className="text-yellow-600 mr-1">⚠️</div>
                                                    <div className="text-xs font-medium text-yellow-800">
                                                      System Improvement Notice
                                                    </div>
                                                  </div>
                                                  <div className="text-xs text-yellow-700">
                                                    AI planner generated abstract tasks. System is learning to create more concrete outputs.
                                                  </div>
                                                  <div className="text-xs text-yellow-600 mt-1">
                                                    Created: {new Date(deliverable.created_at).toLocaleDateString()}
                                                  </div>
                                                </>
                                              ) : (
                                                <>
                                                  <div className="text-xs font-medium text-green-800">
                                                    {deliverable.title || 'Goal Deliverable'}
                                                  </div>
                                                  <div className="text-xs text-green-600 mt-1">
                                                    Created: {new Date(deliverable.created_at).toLocaleDateString()}
                                                  </div>
                                                </>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      ) : goalDeliverables[goal.id] && goalDeliverables[goal.id].length === 0 ? (
                                        <div className="text-xs text-gray-600">
                                          No deliverables yet. This goal is eligible for deliverable creation.
                                        </div>
                                      ) : deliverablesLoading[goal.id] ? (
                                        <div className="text-xs text-gray-600">
                                          ⏳ Loading deliverables...
                                        </div>
                                      ) : (
                                        <div className="text-xs text-gray-600">
                                          Click "Check" to see if deliverables are available for this goal.
                                        </div>
                                      )}
                                    </div>
                                  )}

                                  {/* Informazioni aggiuntive per l'utente */}
                                  <div className="text-xs text-gray-500 bg-gray-50 rounded p-2 border-l-2 border-blue-300">
                                    <strong>ℹ️ Info:</strong> Questo obiettivo viene aggiornato automaticamente quando i task correlati vengono completati dal team di agenti.
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Strategic Deliverables Section */}
                  {deliverables.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-green-600 mb-2">📋 Asset Strategici</h4>
                      <div className="grid grid-cols-1 gap-1">
                        {goalsToShow.filter(goal => deliverables.includes(goal)).map((goal) => (
                          <div key={goal.id} className="bg-green-50 rounded border border-green-100 overflow-hidden transition-all duration-200">
                            <div 
                              className="flex items-center justify-between p-2 cursor-pointer hover:bg-green-100 transition-colors group"
                              onClick={() => toggleGoalExpansion(goal.id)}
                            >
                              <div className="flex items-center space-x-2 flex-1">
                                <span className="text-xs">
                                  {goal.status === 'completed' ? '✅' : goal.completion_pct! < 30 ? '⚠️' : '📊'}
                                </span>
                                <span className="text-sm font-medium">{formatMetricType(goal.metric_type)}</span>
                                <span className="text-xs text-green-400 group-hover:text-green-600 transition-colors">
                                  clicca per dettagli
                                </span>
                              </div>
                              <div className="text-xs text-gray-600 font-medium">
                                {goal.current_value}/{goal.target_value} {goal.unit}
                              </div>
                            </div>
                            
                            {/* Expanded Details con animazione smooth */}
                            <div className={`transition-all duration-300 ease-in-out ${
                              expandedGoalId === goal.id ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                            } overflow-hidden`}>
                              <div className="px-3 pb-3 border-t border-green-200 bg-green-25">
                                <div className="space-y-3 pt-3">
                                  <div className="text-xs text-gray-700">
                                    <strong>📝 Descrizione:</strong> {goal.description}
                                  </div>
                                  
                                  {/* Progress Bar visuale */}
                                  <div>
                                    <div className="flex justify-between items-center mb-1">
                                      <span className="text-xs font-medium text-gray-700">📈 Progresso</span>
                                      <span className="text-xs font-bold text-green-600">{goal.completion_pct?.toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-green-100 rounded-full h-2">
                                      <div 
                                        className="bg-green-500 h-2 rounded-full transition-all duration-500"
                                        style={{ width: `${Math.min(goal.completion_pct || 0, 100)}%` }}
                                      ></div>
                                    </div>
                                    {goal.gap_value && goal.gap_value > 0 && (
                                      <div className="text-xs text-gray-600 mt-1">
                                        🎯 Mancano ancora <strong>{goal.gap_value} {goal.unit}</strong> per completare
                                      </div>
                                    )}
                                  </div>

                                  {goal.semantic_context?.deliverable_type && (
                                    <div className="text-xs text-green-600 bg-white rounded p-2 border border-green-200">
                                      <strong>🔧 Tipo Asset:</strong> {goal.semantic_context.deliverable_type}
                                    </div>
                                  )}

                                  {goal.semantic_context?.autonomy_level && (
                                    <div className="bg-white rounded p-2 border border-green-200">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <span className="text-xs font-medium">🤖 Modalità Esecuzione:</span>
                                        <span className={`px-2 py-1 text-xs rounded ${getAutonomyInfo(goal.semantic_context.autonomy_level).color}`}>
                                          {getAutonomyInfo(goal.semantic_context.autonomy_level).icon} {getAutonomyInfo(goal.semantic_context.autonomy_level).label}
                                        </span>
                                      </div>
                                      <div className="text-xs text-gray-600">
                                        {getAutonomyInfo(goal.semantic_context.autonomy_level).description}
                                      </div>
                                      {goal.semantic_context?.autonomy_reason && (
                                        <div className="text-xs text-gray-500 mt-1 italic">
                                          "{goal.semantic_context.autonomy_reason}"
                                        </div>
                                      )}
                                    </div>
                                  )}
                                  
                                  {goal.semantic_context?.business_value && (
                                    <div className="text-xs text-gray-700 bg-white rounded p-2 border border-green-200">
                                      <strong>💰 Valore Business:</strong> {goal.semantic_context.business_value}
                                    </div>
                                  )}
                                  
                                  {goal.semantic_context?.execution_phase && (
                                    <div className="text-xs text-gray-600">
                                      <strong>⏱️ Fase Progetto:</strong> {goal.semantic_context.execution_phase}
                                    </div>
                                  )}

                                  {goal.semantic_context?.acceptance_criteria && goal.semantic_context.acceptance_criteria.length > 0 && (
                                    <div className="bg-white rounded p-2 border border-green-200">
                                      <div className="text-xs text-gray-600 mb-1">
                                        <strong>✅ Criteri di Successo:</strong>
                                      </div>
                                      <ul className="text-xs text-gray-600 space-y-1">
                                        {goal.semantic_context.acceptance_criteria.slice(0, 3).map((criteria: string, idx: number) => (
                                          <li key={idx} className="flex items-start">
                                            <span className="text-green-500 mr-1">•</span>
                                            <span>{criteria}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {/* Strumenti AI disponibili */}
                                  {goal.semantic_context?.available_tools && goal.semantic_context.available_tools.length > 0 && (
                                    <div className="bg-blue-50 rounded p-2 border border-blue-200">
                                      <div className="text-xs text-blue-700 mb-1">
                                        <strong>🛠️ Strumenti AI Utilizzati:</strong>
                                      </div>
                                      <div className="flex flex-wrap gap-1">
                                        {goal.semantic_context.available_tools.map((tool: string, idx: number) => (
                                          <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                            {tool}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Input umano richiesto */}
                                  {goal.semantic_context?.human_input_required && goal.semantic_context.human_input_required.length > 0 && (
                                    <div className="bg-yellow-50 rounded p-2 border border-yellow-200">
                                      <div className="text-xs text-yellow-700 mb-1">
                                        <strong>👤 Input Umano Necessario:</strong>
                                      </div>
                                      <div className="text-xs text-yellow-600">
                                        {goal.semantic_context.human_input_required.join(', ')}
                                      </div>
                                    </div>
                                  )}

                                  {/* Informazioni aggiuntive per l'utente */}
                                  <div className="text-xs text-gray-500 bg-gray-50 rounded p-2 border-l-2 border-green-300">
                                    <strong>ℹ️ Info:</strong> Questo asset verrà creato automaticamente dal team di agenti quando i prerequisiti saranno soddisfatti.
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Individual Goals - Show only when expanded */}
      {expanded && (
        <div className="space-y-3">
          {goals.map((goal) => (
          <div key={goal.id} className={`bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow ${
            goal.status === 'completed' ? 'border-green-200 bg-green-50' : ''
          }`}>
            <div className="p-4">
              <div className="space-y-3">
                {/* Goal Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`text-lg ${getGoalStatusColor(goal)}`}>
                      {goal.status === 'completed' ? '✅' : goal.completion_pct! < 30 ? '⚠️' : goal.completion_pct! < 70 ? '🕐' : '📈'}
                    </span>
                    <h3 className={`font-medium ${goal.status === 'completed' ? 'text-green-900' : 'text-gray-900'}`}>
                      {formatMetricType(goal.metric_type)}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded border ${
                      goal.status === 'completed' 
                        ? 'bg-green-100 text-green-800 border-green-200' 
                        : 'bg-gray-100 text-gray-700 border-gray-200'
                    }`}>
                      Priority {goal.priority}
                    </span>
                    {goal.status === 'completed' && (
                      <span className="px-2 py-1 text-xs bg-green-200 text-green-800 rounded border border-green-300 font-medium">
                        COMPLETED
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${goal.status === 'completed' ? 'text-green-800' : ''}`}>
                      {goal.current_value} / {goal.target_value}
                    </div>
                    <div className={`text-xs ${goal.status === 'completed' ? 'text-green-600' : 'text-gray-500'}`}>
                      {goal.unit}
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-600">{formatDescription(goal.description, goal)}</span>
                    <span className="text-sm font-medium">{goal.completion_pct!.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        goal.completion_pct! >= 100 ? 'bg-green-500' :
                        goal.completion_pct! >= 70 ? 'bg-blue-500' :
                        goal.completion_pct! >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(goal.completion_pct!, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Goal Details */}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-4">
                    {goal.status !== 'completed' && goal.gap_value! > 0 && (
                      <span className="flex items-center">
                        ⬆️ {goal.gap_value} remaining
                      </span>
                    )}
                    {goal.last_progress_date && (
                      <span>
                        Last updated: {new Date(goal.last_progress_date).toLocaleDateString()}
                      </span>
                    )}
                    {goal.status === 'completed' && (
                      <span className="flex items-center text-green-600">
                        🎉 Goal achieved! 
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {/* 🎯 NEW: Goal-specific deliverable actions */}
                    {goal.completion_pct! >= 80 && (
                      <div className="flex items-center space-x-1">
                        {!goalDeliverables[goal.id] && !deliverablesLoading[goal.id] && (
                          <button
                            onClick={() => fetchGoalDeliverables(goal.id)}
                            className="px-2 py-1 bg-purple-100 text-purple-700 hover:bg-purple-200 rounded text-xs font-medium border border-purple-200 transition-colors"
                          >
                            📋 Check Deliverables
                          </button>
                        )}
                        {goalDeliverables[goal.id] && goalDeliverables[goal.id].length === 0 && (
                          <button
                            onClick={() => createGoalDeliverable(goal.id)}
                            disabled={deliverablesLoading[goal.id]}
                            className="px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs font-medium border border-green-200 transition-colors disabled:opacity-50"
                          >
                            {deliverablesLoading[goal.id] ? '⏳' : '📦'} Create Deliverable
                          </button>
                        )}
                        {goalDeliverables[goal.id] && goalDeliverables[goal.id].length > 0 && (
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${
                            goalDeliverables[goal.id].some(d => d.type === 'low_value_warning')
                              ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
                              : 'bg-green-100 text-green-700 border-green-200'
                          }`}>
                            {goalDeliverables[goal.id].some(d => d.type === 'low_value_warning') ? '⚠️' : '✅'} 
                            {goalDeliverables[goal.id].length} Deliverable{goalDeliverables[goal.id].length > 1 ? 's' : ''}
                            {goalDeliverables[goal.id].some(d => d.type === 'low_value_warning') && ' (Review)'}
                          </span>
                        )}
                        {deliverablesLoading[goal.id] && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                            ⏳ Loading...
                          </span>
                        )}
                      </div>
                    )}
                    
                    {goal.status === 'completed' && onViewAssets && (
                      <button
                        onClick={onViewAssets}
                        className="px-3 py-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded text-xs font-medium border border-blue-200 transition-colors"
                      >
                        📦 View Assets
                      </button>
                    )}
                    {goal.status !== 'completed' && goal.completion_pct! > 90 && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                        Almost Done!
                      </span>
                    )}
                    {goal.status !== 'completed' && goal.completion_pct! < 30 && (
                      <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">
                        Needs Attention
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        </div>
      )}

      {/* Recommendations */}
      {validationStatus?.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h3 className="text-sm font-medium text-gray-700">
              💡 Recommendations
            </h3>
          </div>
          <div className="p-4">
            <ul className="space-y-2 text-sm text-gray-600">
              {validationStatus.recommendations.map((rec, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {goals.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6 text-center text-gray-500">
          <div className="text-4xl mb-2">🎯</div>
          <p className="font-medium">No goals found for this workspace.</p>
          <p className="text-sm">Goals will appear here once they are created and will remain visible even after completion.</p>
        </div>
      )}
    </div>
  );
};

export default GoalProgressTracker;