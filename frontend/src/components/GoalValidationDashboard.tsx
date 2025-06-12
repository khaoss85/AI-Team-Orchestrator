// frontend/src/components/GoalValidationDashboard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface ValidationResult {
  target_requirement: string;
  actual_achievement: string;
  achievement_percentage: number;
  gap_percentage: number;
  is_valid: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
  validation_details: any;
  recommendations: string[];
}

interface QualityGateResult {
  can_transition: boolean;
  readiness_score: number;
  missing_requirements: string[];
  quality_issues: any[];
  recommendations: string[];
}

interface CompletionReadinessResult {
  ready_for_completion: boolean;
  completion_score: number;
  missing_deliverables: string[];
  quality_concerns: any[];
  final_recommendations: string[];
}

interface GoalValidationDashboardProps {
  workspaceId: string;
  className?: string;
}

export const GoalValidationDashboard: React.FC<GoalValidationDashboardProps> = ({
  workspaceId,
  className = ''
}) => {
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [qualityGate, setQualityGate] = useState<QualityGateResult | null>(null);
  const [completionReadiness, setCompletionReadiness] = useState<CompletionReadinessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'validation' | 'quality-gate' | 'completion'>('validation');

  const fetchValidationData = async () => {
    try {
      setError(null);
      
      // Fetch workspace validation
      const validationResponse = await api.goalValidation.validateWorkspace(workspaceId);
      if (validationResponse.validation_results) {
        setValidationResults(validationResponse.validation_results);
      }

      // Fetch quality gate status
      try {
        const qualityGateResponse = await api.goalValidation.checkQualityGate(workspaceId, 'completion');
        if (qualityGateResponse) {
          setQualityGate(qualityGateResponse);
        }
      } catch (qgError) {
        console.warn('Quality gate check not available:', qgError);
      }

      // Fetch completion readiness
      try {
        const completionResponse = await api.goalValidation.checkCompletionReadiness(workspaceId);
        if (completionResponse) {
          setCompletionReadiness(completionResponse);
        }
      } catch (crError) {
        console.warn('Completion readiness check not available:', crError);
      }

    } catch (err) {
      console.error('Error fetching validation data:', err);
      setError('Failed to load validation data');
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await fetchValidationData();
    setRefreshing(false);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchValidationData();
      setLoading(false);
    };

    loadData();
  }, [workspaceId]);

  const getSeverityColor = (severity: ValidationResult['severity']): string => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mr-2"></div>
          Loading validation data...
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

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">🎯 Goal Validation Dashboard</h2>
          <button 
            onClick={refreshData}
            disabled={refreshing}
            className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            {refreshing ? '🔄' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8 px-4">
          <button
            onClick={() => setSelectedTab('validation')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'validation'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Goal Validation ({validationResults.length})
          </button>
          <button
            onClick={() => setSelectedTab('quality-gate')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'quality-gate'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Quality Gate
          </button>
          <button
            onClick={() => setSelectedTab('completion')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'completion'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Completion Readiness
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="p-4">
        {selectedTab === 'validation' && (
          <div className="space-y-4">
            {validationResults.length === 0 ? (
              <div className="text-center text-gray-500 py-6">
                <div className="text-4xl mb-2">🎯</div>
                <p>No validation results available.</p>
                <p className="text-sm">Goal validation will appear here once goals are defined.</p>
              </div>
            ) : (
              validationResults.map((result, index) => (
                <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-1">
                        {result.target_requirement}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">
                        <span className="font-medium">Actual:</span> {result.actual_achievement}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded border ${getSeverityColor(result.severity)}`}>
                        {result.severity.toUpperCase()}
                      </span>
                      <span className={`text-lg font-bold ${getScoreColor(result.achievement_percentage)}`}>
                        {result.achievement_percentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          result.achievement_percentage >= 100 ? 'bg-green-500' :
                          result.achievement_percentage >= 70 ? 'bg-blue-500' :
                          result.achievement_percentage >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(result.achievement_percentage, 100)}%` }}
                      />
                    </div>
                    {result.gap_percentage > 0 && (
                      <div className="text-xs text-gray-500 mt-1">
                        Gap: {result.gap_percentage.toFixed(1)}%
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {result.recommendations && result.recommendations.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Recommendations:</h4>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {result.recommendations.slice(0, 3).map((rec, recIndex) => (
                          <li key={recIndex} className="flex items-start">
                            <span className="text-blue-500 mr-2">•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'quality-gate' && (
          <div className="space-y-4">
            {qualityGate ? (
              <>
                {/* Quality Gate Status */}
                <div className={`p-4 rounded-lg border ${qualityGate.can_transition ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">
                        {qualityGate.can_transition ? '✅ Ready for Next Phase' : '❌ Quality Gate Blocked'}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Readiness Score: <span className={`font-bold ${getScoreColor(qualityGate.readiness_score)}`}>
                          {qualityGate.readiness_score.toFixed(0)}%
                        </span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Missing Requirements */}
                {qualityGate.missing_requirements.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Missing Requirements</h3>
                    <ul className="space-y-2">
                      {qualityGate.missing_requirements.map((req, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-red-500 mr-2">⚠️</span>
                          <span className="text-sm text-gray-700">{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Quality Issues */}
                {qualityGate.quality_issues.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Quality Issues</h3>
                    <div className="space-y-2 text-sm text-gray-600">
                      {qualityGate.quality_issues.slice(0, 5).map((issue, index) => (
                        <div key={index} className="flex items-start">
                          <span className="text-yellow-500 mr-2">⚠️</span>
                          <span>{typeof issue === 'string' ? issue : JSON.stringify(issue)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {qualityGate.recommendations.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Recommendations</h3>
                    <ul className="space-y-2">
                      {qualityGate.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-500 mr-2">💡</span>
                          <span className="text-sm text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-gray-500 py-6">
                <div className="text-4xl mb-2">🚪</div>
                <p>Quality gate information not available.</p>
                <p className="text-sm">Quality gate status will appear here once configured.</p>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'completion' && (
          <div className="space-y-4">
            {completionReadiness ? (
              <>
                {/* Completion Status */}
                <div className={`p-4 rounded-lg border ${completionReadiness.ready_for_completion ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">
                        {completionReadiness.ready_for_completion ? '🎉 Ready for Completion' : '⏳ Not Ready for Completion'}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Completion Score: <span className={`font-bold ${getScoreColor(completionReadiness.completion_score)}`}>
                          {completionReadiness.completion_score.toFixed(0)}%
                        </span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Missing Deliverables */}
                {completionReadiness.missing_deliverables.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Missing Deliverables</h3>
                    <ul className="space-y-2">
                      {completionReadiness.missing_deliverables.map((deliverable, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-red-500 mr-2">📋</span>
                          <span className="text-sm text-gray-700">{deliverable}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Quality Concerns */}
                {completionReadiness.quality_concerns.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Quality Concerns</h3>
                    <div className="space-y-2 text-sm text-gray-600">
                      {completionReadiness.quality_concerns.slice(0, 5).map((concern, index) => (
                        <div key={index} className="flex items-start">
                          <span className="text-yellow-500 mr-2">⚠️</span>
                          <span>{typeof concern === 'string' ? concern : JSON.stringify(concern)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Final Recommendations */}
                {completionReadiness.final_recommendations.length > 0 && (
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">Final Recommendations</h3>
                    <ul className="space-y-2">
                      {completionReadiness.final_recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-500 mr-2">🎯</span>
                          <span className="text-sm text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-gray-500 py-6">
                <div className="text-4xl mb-2">🏁</div>
                <p>Completion readiness information not available.</p>
                <p className="text-sm">Completion status will appear here once goals are defined.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GoalValidationDashboard;