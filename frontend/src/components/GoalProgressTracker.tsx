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
}

interface GoalProgressTrackerProps {
  workspaceId: string;
  showValidation?: boolean;
  autoRefresh?: boolean;
  className?: string;
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
  className = ''
}) => {
  const [goals, setGoals] = useState<WorkspaceGoal[]>([]);
  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGoals = async () => {
    try {
      const response = await api.workspaceGoals.getAll(workspaceId, { status: 'active' });
      if (response.success) {
        // Calculate completion percentages
        const goalsWithProgress = response.goals.map((goal: any) => ({
          ...goal,
          completion_pct: goal.target_value > 0 ? (goal.current_value / goal.target_value * 100) : 0,
          gap_value: goal.target_value - goal.current_value
        }));
        setGoals(goalsWithProgress);
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

  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([fetchGoals(), fetchValidation()]);
    setRefreshing(false);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchGoals(), fetchValidation()]);
      setLoading(false);
    };

    loadData();

    // Auto-refresh every 5 minutes if enabled
    if (autoRefresh) {
      const interval = setInterval(refreshData, 5 * 60 * 1000);
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
    return type.replace(/_/g, ' ').toUpperCase();
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

  const overallProgress = goals.length > 0 
    ? goals.reduce((sum, goal) => sum + goal.completion_pct!, 0) / goals.length 
    : 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Overall Progress Summary */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center">
              🎯 Goal Progress Overview
            </h2>
            <button 
              onClick={refreshData}
              disabled={refreshing}
              className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            {/* Overall Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Overall Progress</span>
                <span className="text-sm text-gray-600">{overallProgress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
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
                  {goals.filter(g => g.completion_pct! >= 100).length}
                </div>
                <div className="text-xs text-green-600">Completed</div>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-bold text-blue-700">
                  {goals.filter(g => g.completion_pct! >= 50 && g.completion_pct! < 100).length}
                </div>
                <div className="text-xs text-blue-600">In Progress</div>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <div className="text-lg font-bold text-yellow-700">
                  {goals.filter(g => g.completion_pct! < 50).length}
                </div>
                <div className="text-xs text-yellow-600">Behind</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Goals */}
      <div className="space-y-3">
        {goals.map((goal) => (
          <div key={goal.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
            <div className="p-4">
              <div className="space-y-3">
                {/* Goal Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`text-lg ${getGoalStatusColor(goal)}`}>
                      {goal.status === 'completed' ? '✅' : goal.completion_pct! < 30 ? '⚠️' : goal.completion_pct! < 70 ? '🕐' : '📈'}
                    </span>
                    <h3 className="font-medium text-gray-900">
                      {formatMetricType(goal.metric_type)}
                    </h3>
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded border">
                      Priority {goal.priority}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">
                      {goal.current_value} / {goal.target_value}
                    </div>
                    <div className="text-xs text-gray-500">{goal.unit}</div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-600">{goal.description}</span>
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
                    {goal.gap_value! > 0 && (
                      <span className="flex items-center">
                        ⬆️ {goal.gap_value} remaining
                      </span>
                    )}
                    {goal.last_progress_date && (
                      <span>
                        Last updated: {new Date(goal.last_progress_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {goal.completion_pct! > 90 && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                        Almost Done!
                      </span>
                    )}
                    {goal.completion_pct! < 30 && (
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
          <p className="font-medium">No active goals found for this workspace.</p>
          <p className="text-sm">Goals will appear here once they are created.</p>
        </div>
      )}
    </div>
  );
};

export default GoalProgressTracker;