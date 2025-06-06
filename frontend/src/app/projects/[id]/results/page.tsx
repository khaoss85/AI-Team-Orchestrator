'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useProjectResults, UnifiedResultItem } from '@/hooks/useProjectResults';
import { UnifiedResultCard } from '@/components/UnifiedResultCard';

type FilterType = 'all' | 'readyToUse' | 'inProgress' | 'final';
type SortType = 'impact' | 'actionability' | 'recent' | 'alphabetical';

export default function ProjectResultsPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const {
    results,
    categories,
    loading,
    error,
    stats,
    refreshResults
  } = useProjectResults(projectId);

  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<SortType>('impact');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResult, setSelectedResult] = useState<UnifiedResultItem | null>(null);

  const getFilteredResults = () => {
    let filtered = results;

    // Apply category filter
    switch (activeFilter) {
      case 'readyToUse':
        filtered = categories.readyToUse;
        break;
      case 'inProgress':
        filtered = categories.inProgress;
        break;
      case 'final':
        filtered = categories.finalDeliverables;
        break;
      default:
        filtered = results;
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(result =>
        result.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        result.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'impact':
          const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          return impactOrder[b.businessImpact] - impactOrder[a.businessImpact];
        case 'actionability':
          return b.actionabilityScore - a.actionabilityScore;
        case 'recent':
          return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
        case 'alphabetical':
          return a.title.localeCompare(b.title);
        default:
          return 0;
      }
    });
  };

  const filteredResults = getFilteredResults();

  const getBusinessImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-48 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Results</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={refreshResults}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* Navigation */}
          <div className="mb-6">
            <Link href={`/projects/${projectId}`} className="text-indigo-600 hover:underline text-sm">
              ← Back to Project
            </Link>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <Link
                href={`/projects/${projectId}`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Overview
              </Link>
              <Link
                href={`/projects/${projectId}/results`}
                className="py-2 px-1 border-b-2 border-indigo-500 font-medium text-sm text-indigo-600"
              >
                📊 Unified Results
              </Link>
              <Link
                href={`/projects/${projectId}/tasks`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Tasks
              </Link>
              <Link
                href={`/projects/${projectId}/team`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Team
              </Link>
            </nav>
          </div>

          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Project Results</h1>
              <p className="text-gray-600 mt-1">
                Unified view of all deliverables, assets, and actionable outputs
              </p>
            </div>
            
            <button
              onClick={refreshResults}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh Results
            </button>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{stats.readyToUse}</div>
              <div className="text-sm text-green-700">Ready to Use</div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
              <div className="text-sm text-blue-700">In Progress</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600">{stats.finalDeliverables}</div>
              <div className="text-sm text-purple-700">Final Deliverables</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-600">{stats.total}</div>
              <div className="text-sm text-gray-700">Total Results</div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search results..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filter */}
            <div className="flex gap-2">
              {[
                { key: 'all', label: 'All Results' },
                { key: 'readyToUse', label: 'Ready to Use' },
                { key: 'inProgress', label: 'In Progress' },
                { key: 'final', label: 'Final' }
              ].map(filter => (
                <button
                  key={filter.key}
                  onClick={() => setActiveFilter(filter.key as FilterType)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    activeFilter === filter.key
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortType)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="impact">Business Impact</option>
              <option value="actionability">Actionability</option>
              <option value="recent">Most Recent</option>
              <option value="alphabetical">Alphabetical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Grid */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {filteredResults.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
            <p className="text-gray-600">
              {searchQuery
                ? 'Try adjusting your search terms or filters.'
                : 'No results match the current filter.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResults.map((result) => (
              <UnifiedResultCard
                key={result.id}
                result={result}
                onViewDetails={(result) => setSelectedResult(result)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedResult.title}
                  </h2>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded-full ${getBusinessImpactColor(selectedResult.businessImpact)}`}>
                      {selectedResult.businessImpact.toUpperCase()} Impact
                    </span>
                    <span className="text-gray-600">
                      Actionability: {selectedResult.actionabilityScore}%
                    </span>
                    <span className="text-gray-600">
                      Validation: {selectedResult.validationScore}%
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="ml-4 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="prose max-w-none">
                <h3 className="text-lg font-semibold mb-4">Description</h3>
                <p className="text-gray-700 mb-6">{selectedResult.description}</p>
                
                {selectedResult.keyInsights && selectedResult.keyInsights.length > 0 && (
                  <>
                    <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
                    <ul className="list-disc list-inside space-y-2 mb-6">
                      {selectedResult.keyInsights.map((insight, index) => (
                        <li key={index} className="text-gray-700">{insight}</li>
                      ))}
                    </ul>
                  </>
                )}
                
                {selectedResult.nextActions && selectedResult.nextActions.length > 0 && (
                  <>
                    <h3 className="text-lg font-semibold mb-4">Recommended Actions</h3>
                    <ul className="list-disc list-inside space-y-2 mb-6">
                      {selectedResult.nextActions.map((action, index) => (
                        <li key={index} className="text-gray-700">{action}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
              
              <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setSelectedResult(null)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
                {selectedResult.readyToUse && (
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Use This Result
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}