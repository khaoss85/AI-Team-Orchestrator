'use client';

import React from 'react';
import Link from 'next/link';
import { useProjectResults } from '@/hooks/useProjectResults';

interface ProjectResultsOverviewProps {
  projectId: string;
}

const ProjectResultsOverview: React.FC<ProjectResultsOverviewProps> = ({ projectId }) => {
  const {
    readyToUse,
    inProgress, 
    finalDeliverables,
    totalResults,
    completionRate,
    qualityScore,
    loading,
    error
  } = useProjectResults(projectId);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <div className="text-red-600 text-sm">Error loading results: {error}</div>
      </div>
    );
  }

  const stats = [
    {
      label: 'Ready to Use',
      value: readyToUse.length,
      color: 'text-green-600 bg-green-50 border-green-200',
      icon: '✅'
    },
    {
      label: 'In Progress', 
      value: inProgress.length,
      color: 'text-blue-600 bg-blue-50 border-blue-200',
      icon: '⏳'
    },
    {
      label: 'Final Deliverables',
      value: finalDeliverables.length,
      color: 'text-purple-600 bg-purple-50 border-purple-200', 
      icon: '🎯'
    },
    {
      label: 'Total Results',
      value: totalResults,
      color: 'text-gray-600 bg-gray-50 border-gray-200',
      icon: '📊'
    }
  ];

  // Get top ready-to-use results for preview
  const topResults = readyToUse.slice(0, 3);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Project Results</h2>
            <p className="text-gray-600 text-sm mt-1">
              {completionRate}% complete • Quality score: {qualityScore}%
            </p>
          </div>
          <Link
            href={`/projects/${projectId}/conversation`}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center"
          >
            View in Chat
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {stats.map((stat, index) => (
            <div key={index} className={`${stat.color} border rounded-lg p-4 text-center`}>
              <div className="text-2xl mb-1">{stat.icon}</div>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="text-sm opacity-80">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Quick Preview of Top Results */}
        {topResults.length > 0 && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Ready to Use Highlights</h3>
            <div className="space-y-3">
              {topResults.map((result, index) => (
                <div key={result.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                      <span className="text-green-600 text-sm font-bold">{index + 1}</span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{result.title}</div>
                      <div className="text-sm text-gray-600">
                        {result.actionabilityScore}% actionable • {result.businessImpact} impact
                      </div>
                    </div>
                  </div>
                  <Link
                    href={`/projects/${projectId}/conversation`}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    View →
                  </Link>
                </div>
              ))}
            </div>
            
            {readyToUse.length > 3 && (
              <div className="mt-4 text-center">
                <Link
                  href={`/projects/${projectId}/conversation`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  + {readyToUse.length - 3} more ready-to-use results
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {totalResults === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-2">📋</div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No results yet</h3>
            <p className="text-gray-600 text-sm">
              Results will appear here as tasks complete and deliverables are generated.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectResultsOverview;