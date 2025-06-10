'use client';

import React, { useState, useEffect } from 'react';
import { AssetHistory, AssetVersion } from '@/hooks/useAssetDependencies';

interface Props {
  assetId: string;
  workspaceId: string;
  className?: string;
}

interface VersionComparison {
  from_version: string;
  to_version: string;
  changes: {
    added: string[];
    removed: string[];
    modified: string[];
  };
  summary: string;
  quality_improvement: number;
  business_impact: string;
}

export const AssetHistoryPanel: React.FC<Props> = ({
  assetId,
  workspaceId,
  className = ''
}) => {
  const [history, setHistory] = useState<AssetHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<{from: string; to: string}>({
    from: '',
    to: ''
  });
  const [comparison, setComparison] = useState<VersionComparison | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null);

  useEffect(() => {
    if (assetId) {
      fetchHistory();
    }
  }, [assetId]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with real API call
      const mockHistory: AssetHistory = {
        asset_id: assetId,
        asset_name: 'Marketing Strategy Analysis',
        asset_type: 'analysis',
        current_version: 'v3.0',
        total_iterations: 5,
        first_created: '2024-01-01T10:00:00Z',
        last_modified: '2024-01-15T10:30:00Z',
        versions: [
          {
            version: 'v3.0',
            created_at: '2024-01-15T10:30:00Z',
            created_by: 'Marketing Team',
            changes_summary: 'Updated market analysis with Q4 data and revised competitor positioning',
            quality_metrics: {
              actionability: 0.92,
              completeness: 0.95,
              accuracy: 0.89,
              business_relevance: 0.94
            },
            size_indicators: {
              word_count: 3500,
              data_points: 45,
              sections: 8
            },
            content_preview: 'Executive Summary: Market analysis reveals strong growth opportunities in Q4...'
          },
          {
            version: 'v2.1',
            created_at: '2024-01-10T14:15:00Z',
            created_by: 'Strategy Analyst',
            changes_summary: 'Fixed calculation errors in financial projections',
            quality_metrics: {
              actionability: 0.88,
              completeness: 0.90,
              accuracy: 0.92,
              business_relevance: 0.87
            },
            size_indicators: {
              word_count: 3200,
              data_points: 38,
              sections: 7
            },
            content_preview: 'Updated financial projections show corrected revenue forecasts and market sizing...'
          },
          {
            version: 'v2.0',
            created_at: '2024-01-05T09:00:00Z',
            created_by: 'Project Manager',
            changes_summary: 'Major restructure: added executive summary and recommendations',
            quality_metrics: {
              actionability: 0.85,
              completeness: 0.82,
              accuracy: 0.88,
              business_relevance: 0.89
            },
            size_indicators: {
              word_count: 2800,
              data_points: 30,
              sections: 6
            },
            content_preview: 'Major restructure introduces executive summary with strategic recommendations...'
          },
          {
            version: 'v1.0',
            created_at: '2024-01-01T12:00:00Z',
            created_by: 'Research Team',
            changes_summary: 'Initial version with basic market research and analysis',
            quality_metrics: {
              actionability: 0.75,
              completeness: 0.70,
              accuracy: 0.85,
              business_relevance: 0.78
            },
            size_indicators: {
              word_count: 2100,
              data_points: 22,
              sections: 5
            },
            content_preview: 'Initial market research covering competitive landscape and basic market sizing...'
          }
        ]
      };
      setHistory(mockHistory);
    } catch (error) {
      console.error('Failed to fetch asset history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompareVersions = async () => {
    if (!selectedVersions.from || !selectedVersions.to) return;
    
    try {
      setCompareLoading(true);
      // Mock comparison data - replace with real API call
      const mockComparison: VersionComparison = {
        from_version: selectedVersions.from,
        to_version: selectedVersions.to,
        changes: {
          added: ['New competitor analysis section', 'Updated market trends data', 'Q4 financial projections'],
          removed: ['Outdated Q3 data', 'Legacy formatting'],
          modified: ['Executive summary', 'Strategic recommendations', 'Risk assessment']
        },
        summary: `Upgraded from ${selectedVersions.from} to ${selectedVersions.to} with significant improvements in market analysis and data accuracy.`,
        quality_improvement: 12,
        business_impact: 'Major enhancement to strategic decision-making capabilities with updated market intelligence.'
      };
      setComparison(mockComparison);
    } catch (error) {
      console.error('Failed to compare versions:', error);
    } finally {
      setCompareLoading(false);
    }
  };

  const getQualityTrend = (currentScore: number, previousScore?: number) => {
    if (!previousScore) return null;
    const diff = currentScore - previousScore;
    if (diff > 0.05) return { trend: 'up', color: 'green', icon: '📈' };
    if (diff < -0.05) return { trend: 'down', color: 'red', icon: '📉' };
    return { trend: 'stable', color: 'gray', icon: '➡️' };
  };

  const formatQualityScore = (metrics: AssetVersion['quality_metrics']) => {
    if (!metrics) return 75; // Default score if metrics are undefined
    const overall = (metrics.actionability + metrics.completeness + metrics.accuracy + metrics.business_relevance) / 4;
    return Math.round(overall * 100);
  };

  const getVersionAge = (createdAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffInHours = Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return `${Math.floor(diffInHours / 168)}w ago`;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!history) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">📜</div>
          <p>No history available for this asset</p>
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
            <h3 className="text-lg font-semibold text-gray-900">Asset History</h3>
            <p className="text-sm text-gray-600">
              {history.asset_name} • {history.total_iterations} iterations • Current: v{history.current_version}
            </p>
          </div>
          <div className="text-xs text-gray-500">
            Created {getVersionAge(history.first_created)}
          </div>
        </div>
      </div>

      {/* Version Comparison Controls */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Compare:</label>
            <select
              value={selectedVersions.from}
              onChange={(e) => setSelectedVersions({...selectedVersions, from: e.target.value})}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">From version...</option>
              {history.versions.map(version => (
                <option key={version.version} value={version.version}>
                  v{version.version}
                </option>
              ))}
            </select>
            
            <span className="text-gray-400">to</span>
            
            <select
              value={selectedVersions.to}
              onChange={(e) => setSelectedVersions({...selectedVersions, to: e.target.value})}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">To version...</option>
              {history.versions.map(version => (
                <option key={version.version} value={version.version}>
                  v{version.version}
                </option>
              ))}
            </select>
          </div>
          
          <button
            onClick={handleCompareVersions}
            disabled={!selectedVersions.from || !selectedVersions.to || compareLoading}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {compareLoading ? 'Comparing...' : 'Compare'}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            Comparison: v{comparison.from_version} → v{comparison.to_version}
          </h4>
          <p className="text-sm text-blue-700 mb-3">{comparison.summary}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {comparison.changes.added.length > 0 && (
              <div>
                <div className="font-medium text-green-700 mb-1">✅ Added ({comparison.changes.added.length})</div>
                <ul className="list-disc list-inside text-green-600 space-y-1">
                  {comparison.changes.added.slice(0, 3).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                  {comparison.changes.added.length > 3 && (
                    <li className="text-green-500">+{comparison.changes.added.length - 3} more...</li>
                  )}
                </ul>
              </div>
            )}
            
            {comparison.changes.modified.length > 0 && (
              <div>
                <div className="font-medium text-yellow-700 mb-1">📝 Modified ({comparison.changes.modified.length})</div>
                <ul className="list-disc list-inside text-yellow-600 space-y-1">
                  {comparison.changes.modified.slice(0, 3).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                  {comparison.changes.modified.length > 3 && (
                    <li className="text-yellow-500">+{comparison.changes.modified.length - 3} more...</li>
                  )}
                </ul>
              </div>
            )}
            
            {comparison.changes.removed.length > 0 && (
              <div>
                <div className="font-medium text-red-700 mb-1">❌ Removed ({comparison.changes.removed.length})</div>
                <ul className="list-disc list-inside text-red-600 space-y-1">
                  {comparison.changes.removed.slice(0, 3).map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                  {comparison.changes.removed.length > 3 && (
                    <li className="text-red-500">+{comparison.changes.removed.length - 3} more...</li>
                  )}
                </ul>
              </div>
            )}
          </div>
          
          <div className="mt-3 flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <span className="text-gray-600">Quality Change:</span>
              <span className={`font-medium ${comparison.quality_improvement > 0 ? 'text-green-600' : comparison.quality_improvement < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {comparison.quality_improvement > 0 ? '+' : ''}{Math.round(comparison.quality_improvement * 100)}%
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-gray-600">Business Impact:</span>
              <span className="font-medium text-blue-600">{comparison.business_impact}</span>
            </div>
          </div>
        </div>
      )}

      {/* Version Timeline */}
      <div className="max-h-96 overflow-y-auto">
        {history.versions.map((version, index) => {
          const isExpanded = expandedVersion === version.version;
          const isCurrent = version.version === history.current_version;
          const previousVersion = history.versions[index + 1];
          const qualityScore = formatQualityScore(version.quality_metrics);
          const previousQualityScore = previousVersion ? formatQualityScore(previousVersion.quality_metrics) : null;
          const qualityTrend = getQualityTrend(qualityScore / 100, previousQualityScore ? previousQualityScore / 100 : undefined);

          return (
            <div key={version.version} className={`border-b border-gray-100 ${isCurrent ? 'bg-green-50' : ''}`}>
              <div 
                className="px-6 py-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setExpandedVersion(isExpanded ? null : version.version)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      <div className={`w-3 h-3 rounded-full ${isCurrent ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900">
                          Version {version.version}
                          {isCurrent && (
                            <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Current
                            </span>
                          )}
                        </h4>
                        
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>{qualityScore}% quality</span>
                          {qualityTrend && (
                            <span className={`text-${qualityTrend.color}-600`}>
                              {qualityTrend.icon}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-2">{version.changes_summary}</p>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>By {version.created_by}</span>
                        <span>{getVersionAge(version.created_at)}</span>
                        {version.size_indicators?.word_count && (
                          <span>{version.size_indicators.word_count.toLocaleString()} words</span>
                        )}
                        {version.size_indicators?.data_points && (
                          <span>{version.size_indicators.data_points} data points</span>
                        )}
                        {version.size_indicators?.sections && (
                          <span>{version.size_indicators.sections} sections</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex-shrink-0">
                    <svg 
                      className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>
              
              {/* Expanded Details */}
              {isExpanded && (
                <div className="px-6 pb-4 border-t border-gray-100 bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {/* Quality Metrics */}
                    <div>
                      <h5 className="text-sm font-medium text-gray-900 mb-2">Quality Metrics</h5>
                      <div className="space-y-2">
                        {version.quality_metrics ? Object.entries(version.quality_metrics).map(([metric, score]) => (
                          <div key={metric} className="flex items-center justify-between">
                            <span className="text-xs text-gray-600 capitalize">
                              {metric.replace('_', ' ')}
                            </span>
                            <div className="flex items-center space-x-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs text-gray-700 w-8 text-right">
                                {Math.round(score * 100)}%
                              </span>
                            </div>
                          </div>
                        )) : (
                          <div className="text-xs text-gray-500">No quality metrics available</div>
                        )}
                      </div>
                    </div>
                    
                    {/* Content Preview */}
                    <div>
                      <h5 className="text-sm font-medium text-gray-900 mb-2">Content Preview</h5>
                      <div className="text-xs text-gray-600 bg-white p-3 rounded border max-h-32 overflow-y-auto">
                        {version.content_preview}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 text-xs text-gray-500">
        Last modified: {getVersionAge(history.last_modified)}
      </div>
    </div>
  );
};