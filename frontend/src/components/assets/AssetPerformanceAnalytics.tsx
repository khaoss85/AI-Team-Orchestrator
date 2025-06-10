'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface PerformanceMetrics {
  asset_velocity: {
    assets_per_day: number;
    avg_processing_time: number;
    quality_trend: number;
    efficiency_score: number;
  };
  dependency_analysis: {
    total_dependencies: number;
    avg_cascade_size: number;
    critical_path_length: number;
    bottleneck_assets: string[];
  };
  quality_evolution: {
    current_avg_quality: number;
    quality_improvement_rate: number;
    high_quality_assets_percentage: number;
    quality_distribution: { [key: string]: number };
  };
  automation_impact: {
    automation_percentage: number;
    time_saved_hours: number;
    manual_interventions: number;
    roi_multiplier: number;
  };
  user_productivity: {
    avg_feedback_response_time: number;
    decisions_per_hour: number;
    value_extraction_rate: number;
    user_satisfaction_score: number;
  };
}

interface TrendData {
  date: string;
  assets_created: number;
  quality_score: number;
  processing_time: number;
  automation_rate: number;
}

interface Props {
  workspaceId: string;
  timeRange?: '7d' | '30d' | '90d' | '1y';
  className?: string;
}

export const AssetPerformanceAnalytics: React.FC<Props> = ({
  workspaceId,
  timeRange = '30d',
  className = ''
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<'velocity' | 'quality' | 'automation' | 'productivity'>('velocity');

  useEffect(() => {
    loadAnalytics();
  }, [workspaceId, timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [metricsResponse, trendsResponse] = await Promise.all([
        api.analytics.getAssetMetrics(workspaceId, timeRange),
        api.analytics.getTrendData(workspaceId, timeRange)
      ]);
      
      setMetrics(metricsResponse);
      setTrendData(trendsResponse.trends || []);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number, type: 'percentage' | 'rating' = 'percentage') => {
    const threshold = type === 'percentage' ? 80 : 4;
    if (score >= threshold) return 'text-green-600';
    if (score >= threshold * 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadge = (score: number, type: 'percentage' | 'rating' = 'percentage') => {
    const threshold = type === 'percentage' ? 80 : 4;
    if (score >= threshold) return { label: 'Excellent', color: 'bg-green-100 text-green-800', icon: '🟢' };
    if (score >= threshold * 0.7) return { label: 'Good', color: 'bg-yellow-100 text-yellow-800', icon: '🟡' };
    return { label: 'Needs Improvement', color: 'bg-red-100 text-red-800', icon: '🔴' };
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const renderMiniChart = (data: number[], color: string = '#3B82F6') => {
    if (data.length === 0) return null;
    
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    
    return (
      <div className="flex items-end space-x-1 h-12">
        {data.map((value, index) => (
          <div
            key={index}
            className="bg-current opacity-70 w-2 rounded-t"
            style={{
              height: `${((value - min) / range) * 100}%`,
              minHeight: '4px',
              color: color
            }}
          />
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">📊</div>
          <p>No analytics data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">📊 Asset Performance Analytics</h2>
            <p className="text-sm text-gray-600">Deep insights into asset creation and management efficiency</p>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-3 py-1"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="p-6 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {/* Asset Velocity */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-blue-900">Asset Velocity</div>
              <div className="text-blue-600">⚡</div>
            </div>
            <div className="text-2xl font-bold text-blue-700 mb-1">
              {metrics.asset_velocity.assets_per_day.toFixed(1)}/day
            </div>
            <div className="text-xs text-blue-600">
              Avg: {formatDuration(metrics.asset_velocity.avg_processing_time)}
            </div>
            <div className="mt-2">
              {renderMiniChart(trendData.map(d => d.assets_created), '#3B82F6')}
            </div>
          </div>

          {/* Quality Score */}
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-green-900">Quality Score</div>
              <div className="text-green-600">🎯</div>
            </div>
            <div className="text-2xl font-bold text-green-700 mb-1">
              {Math.round(metrics.quality_evolution.current_avg_quality * 100)}%
            </div>
            <div className="text-xs text-green-600">
              +{metrics.quality_evolution.quality_improvement_rate.toFixed(1)}% trend
            </div>
            <div className="mt-2">
              {renderMiniChart(trendData.map(d => d.quality_score), '#10B981')}
            </div>
          </div>

          {/* Automation Rate */}
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-purple-900">Automation</div>
              <div className="text-purple-600">🤖</div>
            </div>
            <div className="text-2xl font-bold text-purple-700 mb-1">
              {Math.round(metrics.automation_impact.automation_percentage * 100)}%
            </div>
            <div className="text-xs text-purple-600">
              {metrics.automation_impact.time_saved_hours}h saved
            </div>
            <div className="mt-2">
              {renderMiniChart(trendData.map(d => d.automation_rate), '#8B5CF6')}
            </div>
          </div>

          {/* ROI Multiplier */}
          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-orange-900">ROI Impact</div>
              <div className="text-orange-600">💰</div>
            </div>
            <div className="text-2xl font-bold text-orange-700 mb-1">
              {metrics.automation_impact.roi_multiplier.toFixed(1)}x
            </div>
            <div className="text-xs text-orange-600">
              {metrics.user_productivity.decisions_per_hour.toFixed(1)} decisions/h
            </div>
            <div className="mt-2">
              {renderMiniChart([85, 88, 82, 91, 95, 89, 93], '#EA580C')}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis Tabs */}
      <div className="px-6 py-4">
        <div className="flex space-x-4 border-b border-gray-200 mb-6">
          {[
            { id: 'velocity', label: 'Velocity Analysis', icon: '⚡' },
            { id: 'quality', label: 'Quality Trends', icon: '🎯' },
            { id: 'automation', label: 'Automation Impact', icon: '🤖' },
            { id: 'productivity', label: 'User Productivity', icon: '👥' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedMetric(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                selectedMetric === tab.id
                  ? 'bg-blue-100 text-blue-700 border-b-2 border-blue-500'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <span>{tab.icon}</span>
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {selectedMetric === 'velocity' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Asset Creation Velocity</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Assets per Day</span>
                  <span className="font-medium">{metrics.asset_velocity.assets_per_day.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Avg Processing Time</span>
                  <span className="font-medium">{formatDuration(metrics.asset_velocity.avg_processing_time)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Efficiency Score</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{Math.round(metrics.asset_velocity.efficiency_score * 100)}%</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${getScoreBadge(metrics.asset_velocity.efficiency_score * 100).color}`}>
                      {getScoreBadge(metrics.asset_velocity.efficiency_score * 100).label}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Dependency Analysis</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Total Dependencies</span>
                  <span className="font-medium">{metrics.dependency_analysis.total_dependencies}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Avg Cascade Size</span>
                  <span className="font-medium">{metrics.dependency_analysis.avg_cascade_size.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Critical Path Length</span>
                  <span className="font-medium">{metrics.dependency_analysis.critical_path_length}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'quality' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Quality Evolution</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Current Avg Quality</span>
                  <span className="font-medium">{Math.round(metrics.quality_evolution.current_avg_quality * 100)}%</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">Improvement Rate</span>
                  <span className="font-medium text-green-600">+{metrics.quality_evolution.quality_improvement_rate.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">High Quality Assets</span>
                  <span className="font-medium">{Math.round(metrics.quality_evolution.high_quality_assets_percentage * 100)}%</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Quality Distribution</h4>
              <div className="space-y-2">
                {Object.entries(metrics.quality_evolution.quality_distribution).map(([range, percentage]) => (
                  <div key={range} className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600 w-16">{range}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-12">{percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'automation' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Automation Impact</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                  <span className="text-sm text-gray-700">Automation Rate</span>
                  <span className="font-medium text-purple-700">{Math.round(metrics.automation_impact.automation_percentage * 100)}%</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                  <span className="text-sm text-gray-700">Time Saved</span>
                  <span className="font-medium text-purple-700">{metrics.automation_impact.time_saved_hours}h</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                  <span className="text-sm text-gray-700">ROI Multiplier</span>
                  <span className="font-medium text-purple-700">{metrics.automation_impact.roi_multiplier.toFixed(1)}x</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Manual Interventions</h4>
              <div className="text-center p-6 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-700 mb-2">
                  {metrics.automation_impact.manual_interventions}
                </div>
                <div className="text-sm text-gray-600">This period</div>
                <div className="mt-4 text-xs text-gray-500">
                  {((1 - metrics.automation_impact.automation_percentage) * 100).toFixed(1)}% of tasks required manual intervention
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedMetric === 'productivity' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">User Productivity</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                  <span className="text-sm text-gray-700">Avg Response Time</span>
                  <span className="font-medium">{formatDuration(metrics.user_productivity.avg_feedback_response_time)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                  <span className="text-sm text-gray-700">Decisions per Hour</span>
                  <span className="font-medium">{metrics.user_productivity.decisions_per_hour.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                  <span className="text-sm text-gray-700">Value Extraction Rate</span>
                  <span className="font-medium">{Math.round(metrics.user_productivity.value_extraction_rate * 100)}%</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Satisfaction Score</h4>
              <div className="text-center p-6 bg-green-50 rounded-lg">
                <div className="text-3xl font-bold text-green-700 mb-2">
                  {metrics.user_productivity.user_satisfaction_score.toFixed(1)}/5
                </div>
                <div className="text-sm text-green-600">User Satisfaction</div>
                <div className={`mt-2 inline-block px-3 py-1 rounded-full text-sm ${getScoreBadge(metrics.user_productivity.user_satisfaction_score, 'rating').color}`}>
                  {getScoreBadge(metrics.user_productivity.user_satisfaction_score, 'rating').icon} {getScoreBadge(metrics.user_productivity.user_satisfaction_score, 'rating').label}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};