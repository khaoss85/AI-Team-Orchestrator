'use client'

import React, { useState } from 'react'

interface ProjectDescriptionArtifactProps {
  projectData: any
  content: string
  workspaceId: string
}

export default function ProjectDescriptionArtifact({ 
  projectData, 
  content, 
  workspaceId 
}: ProjectDescriptionArtifactProps) {
  const [activeView, setActiveView] = useState<'overview' | 'goals' | 'config' | 'raw'>('overview')

  if (!projectData) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">📋</div>
          <div className="text-lg font-medium mb-2">No Project Data</div>
          <div className="text-sm">Project description not available</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with view tabs */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            📋 {projectData.project_name || 'Project Description'}
          </h3>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{projectData.total_goals} goals</span>
            <span>•</span>
            <span>${projectData.estimated_budget} budget</span>
            <span>•</span>
            <span>{projectData.avg_confidence ? (projectData.avg_confidence * 100).toFixed(0) : 90}% confidence</span>
          </div>
        </div>
        
        <div className="flex space-x-1 overflow-x-auto">
          <ViewTab
            active={activeView === 'overview'}
            onClick={() => setActiveView('overview')}
            label="Overview"
            icon="📊"
          />
          <ViewTab
            active={activeView === 'goals'}
            onClick={() => setActiveView('goals')}
            label="Goals"
            icon="🎯"
          />
          <ViewTab
            active={activeView === 'config'}
            onClick={() => setActiveView('config')}
            label="Configuration"
            icon="⚙️"
          />
          <ViewTab
            active={activeView === 'raw'}
            onClick={() => setActiveView('raw')}
            label="Full Description"
            icon="📄"
          />
        </div>
      </div>

      {/* Content based on active view */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'overview' && (
          <ProjectOverviewTab projectData={projectData} />
        )}
        
        {activeView === 'goals' && (
          <ProjectGoalsTab projectData={projectData} />
        )}
        
        {activeView === 'config' && (
          <ProjectConfigTab projectData={projectData} />
        )}
        
        {activeView === 'raw' && (
          <ProjectRawTab content={content} />
        )}
      </div>
    </div>
  )
}

// View Tab Component
interface ViewTabProps {
  active: boolean
  onClick: () => void
  label: string
  icon: string
}

function ViewTab({ active, onClick, label, icon }: ViewTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap
        ${active
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }
      `}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  )
}

// Project Overview Tab
function ProjectOverviewTab({ projectData }: { projectData: any }) {
  return (
    <div className="p-4 space-y-6">
      {/* Project Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Project Summary</h4>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
            <div className="text-lg font-medium text-gray-900">
              {projectData.project_name || 'Unnamed Project'}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded border">
              {projectData.project_description || 'No description provided'}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Original Goal</label>
            <div className="text-sm text-gray-700 bg-blue-50 p-3 rounded border border-blue-200">
              {projectData.original_goal || 'No original goal specified'}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-blue-600">
            {projectData.total_goals || 0}
          </div>
          <div className="text-sm text-blue-700">Total Goals</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-green-600">
            {projectData.strategic_deliverables?.length || 0}
          </div>
          <div className="text-sm text-green-700">Deliverables</div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-purple-600">
            {projectData.metrics_goals?.length || 0}
          </div>
          <div className="text-sm text-purple-700">Metrics</div>
        </div>
        
        <div className="bg-orange-50 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-orange-600">
            {projectData.total_target_value || 0}
          </div>
          <div className="text-sm text-orange-700">Target Value</div>
        </div>
      </div>

      {/* Status & Timeline */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Project Status</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm font-medium text-gray-700">Status</span>
            </div>
            <div className="text-lg font-semibold text-green-600 capitalize">
              {projectData.status || 'Active'}
            </div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Created</div>
            <div className="text-sm text-gray-600">
              {projectData.created_at ? new Date(projectData.created_at).toLocaleDateString() : 'Unknown'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Project Goals Tab
function ProjectGoalsTab({ projectData }: { projectData: any }) {
  const strategicDeliverables = projectData.strategic_deliverables || []
  const metricsGoals = projectData.metrics_goals || []
  
  return (
    <div className="p-4 space-y-6">
      {/* Strategic Deliverables */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">
          🎯 Strategic Deliverables ({strategicDeliverables.length})
        </h4>
        {strategicDeliverables.length > 0 ? (
          <div className="space-y-3">
            {strategicDeliverables.map((goal: any, index: number) => (
              <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="font-medium text-gray-900">
                      {goal.metric_type?.replace(/_/g, ' ') || 'Unnamed Goal'}
                    </h5>
                    <p className="text-sm text-gray-600 mt-1">
                      {goal.description || 'No description available'}
                    </p>
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-lg font-bold text-green-600">
                      {goal.target_value} {goal.unit}
                    </div>
                    <div className="text-xs text-green-700">Target</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">
            No strategic deliverables defined
          </div>
        )}
      </div>

      {/* Metrics & KPIs */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">
          📊 Metrics & KPIs ({metricsGoals.length})
        </h4>
        {metricsGoals.length > 0 ? (
          <div className="space-y-3">
            {metricsGoals.map((goal: any, index: number) => (
              <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="font-medium text-gray-900">
                      {goal.metric_type?.replace(/_/g, ' ') || 'Unnamed Metric'}
                    </h5>
                    <p className="text-sm text-gray-600 mt-1">
                      {goal.description || 'No description available'}
                    </p>
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-lg font-bold text-blue-600">
                      {goal.target_value} {goal.unit}
                    </div>
                    <div className="text-xs text-blue-700">Target</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">
            No metrics defined
          </div>
        )}
      </div>
    </div>
  )
}

// Project Configuration Tab
function ProjectConfigTab({ projectData }: { projectData: any }) {
  return (
    <div className="p-4 space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Project Configuration</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-green-50 p-3 rounded border border-green-200">
            <div className="text-sm text-green-700 mb-1">Budget</div>
            <div className="text-2xl font-bold text-green-600">
              ${projectData.estimated_budget || 10}
            </div>
          </div>
          
          <div className="bg-purple-50 p-3 rounded border border-purple-200">
            <div className="text-sm text-purple-700 mb-1">Max Iterations</div>
            <div className="text-2xl font-bold text-purple-600">
              {projectData.max_iterations || 3}
            </div>
          </div>
          
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <div className="text-sm text-blue-700 mb-1">Quality Threshold</div>
            <div className="text-2xl font-bold text-blue-600">
              {projectData.quality_threshold || 85}%
            </div>
          </div>
          
          <div className="bg-orange-50 p-3 rounded border border-orange-200">
            <div className="text-sm text-orange-700 mb-1">Avg Confidence</div>
            <div className="text-2xl font-bold text-orange-600">
              {projectData.avg_confidence ? (projectData.avg_confidence * 100).toFixed(0) : 90}%
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Raw Content Tab
function ProjectRawTab({ content }: { content: string }) {
  return (
    <div className="p-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Full Project Description</h4>
        <div className="prose prose-sm max-w-none">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded border overflow-x-auto">
            {content}
          </pre>
        </div>
      </div>
    </div>
  )
}