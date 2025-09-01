'use client'

import React, { useState, useEffect } from 'react'
import { MacroTheme } from './types'
import { api } from '@/utils/api'
import DeliverableActionBar from './DeliverableActionBar'
import MarkdownRenderer from './MarkdownRenderer'

interface ThemeArtifactProps {
  theme: MacroTheme
  workspaceId: string
  onObjectiveClick?: (goalId: string) => void
}

interface ObjectiveCard {
  id: string
  title: string
  description: string
  progress: number
  status: string
  deliverables: any[]
  lastUpdated?: string
}

export default function ThemeArtifact({ theme, workspaceId, onObjectiveClick }: ThemeArtifactProps) {
  const [objectives, setObjectives] = useState<ObjectiveCard[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'objectives' | 'insights'>('overview')
  const [expandedObjectives, setExpandedObjectives] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchObjectivesForTheme()
  }, [theme, workspaceId])

  const fetchObjectivesForTheme = async () => {
    setLoading(true)
    try {
      // Fetch detailed goal data for each goal in the theme
      const objectivePromises = theme.goals.map(async (goalId) => {
        try {
          const response = await api.workspaceGoals.get(workspaceId, goalId)
          
          // Get deliverables for this goal
          const deliverables = theme.deliverables.filter(d => d.goal_id === goalId)
          
          return {
            id: goalId,
            title: response.description || `Goal ${goalId.slice(0, 8)}`,
            description: response.description || '',
            progress: response.progress || 0,
            status: response.status || 'active',
            deliverables: deliverables,
            lastUpdated: response.updated_at
          }
        } catch (error) {
          console.error(`Failed to fetch goal ${goalId}:`, error)
          return null
        }
      })

      const results = await Promise.all(objectivePromises)
      setObjectives(results.filter(obj => obj !== null) as ObjectiveCard[])
    } catch (error) {
      console.error('Failed to fetch objectives for theme:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleObjectiveExpansion = (objectiveId: string) => {
    setExpandedObjectives(prev => {
      const newSet = new Set(prev)
      if (newSet.has(objectiveId)) {
        newSet.delete(objectiveId)
      } else {
        newSet.add(objectiveId)
      }
      return newSet
    })
  }

  const getStatusColor = (status: string, progress: number) => {
    if (progress >= 100) return 'bg-green-100 text-green-800 border-green-200'
    if (status === 'completed') return 'bg-green-100 text-green-800 border-green-200'
    if (status === 'active' || status === 'in_progress') return 'bg-blue-100 text-blue-800 border-blue-200'
    return 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const getProgressBarColor = (progress: number) => {
    if (progress >= 100) return 'bg-green-500'
    if (progress >= 75) return 'bg-blue-500'
    if (progress >= 50) return 'bg-yellow-500'
    if (progress >= 25) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="h-full flex flex-col">
      {/* Theme Header */}
      <div className="border-b border-gray-100 px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">{theme.icon}</span>
              <h1 className="text-xl font-semibold text-gray-900">{theme.name}</h1>
              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                AI Confidence: {theme.confidence_score}%
              </span>
            </div>
            <p className="text-sm text-gray-600">{theme.description}</p>
            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
              <span>📊 {theme.statistics.total_goals} objectives</span>
              <span>📦 {theme.statistics.total_deliverables} deliverables</span>
              <span>✅ {theme.statistics.completed_deliverables} completed</span>
              <span>📈 {Math.round(theme.statistics.average_progress)}% overall progress</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex space-x-8 px-6">
          {(['overview', 'objectives', 'insights'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 border-b-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'overview' && '📋 Overview'}
              {tab === 'objectives' && '🎯 Objectives'}
              {tab === 'insights' && '💡 AI Insights'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-500">Loading theme data...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Business Value Section */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">💼 Business Value</h3>
                  <p className="text-sm text-blue-800">{theme.business_value}</p>
                </div>

                {/* Progress Overview */}
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <h3 className="font-medium text-gray-900 mb-4">Progress Overview</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Overall Theme Progress</span>
                        <span className="font-medium">{Math.round(theme.statistics.average_progress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`${getProgressBarColor(theme.statistics.average_progress)} h-2 rounded-full transition-all duration-300`}
                          style={{ width: `${Math.min(theme.statistics.average_progress, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Individual Objective Progress Summary */}
                    {objectives.map(obj => (
                      <div key={obj.id} className="pl-4">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-500 truncate max-w-xs">{obj.title}</span>
                          <span className="font-medium">{Math.round(obj.progress)}%</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1">
                          <div 
                            className={`${getProgressBarColor(obj.progress)} h-1 rounded-full`}
                            style={{ width: `${Math.min(obj.progress, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AI Reasoning */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">🤖 AI Theme Extraction Reasoning</h3>
                  <p className="text-sm text-gray-600">{theme.reasoning}</p>
                </div>
              </div>
            )}

            {/* Objectives Tab */}
            {activeTab === 'objectives' && (
              <div className="space-y-4">
                {objectives.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No objectives found in this theme
                  </div>
                ) : (
                  objectives.map(objective => (
                    <div 
                      key={objective.id}
                      className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
                    >
                      {/* Objective Header */}
                      <div 
                        className="p-4 cursor-pointer"
                        onClick={() => {
                          if (onObjectiveClick) {
                            onObjectiveClick(objective.id)
                          } else {
                            toggleObjectiveExpansion(objective.id)
                          }
                        }}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h3 className="font-medium text-gray-900">{objective.title}</h3>
                              <span className={`px-2 py-0.5 text-xs rounded-full border ${getStatusColor(objective.status, objective.progress)}`}>
                                {objective.progress >= 100 ? 'Completed' : objective.status}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{objective.description}</p>
                            
                            {/* Progress Bar */}
                            <div className="flex items-center space-x-3">
                              <div className="flex-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    className={`${getProgressBarColor(objective.progress)} h-2 rounded-full`}
                                    style={{ width: `${Math.min(objective.progress, 100)}%` }}
                                  />
                                </div>
                              </div>
                              <span className="text-sm font-medium text-gray-700">{Math.round(objective.progress)}%</span>
                            </div>

                            {/* Stats */}
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                              <span>📦 {objective.deliverables.length} deliverables</span>
                              <span>✅ {objective.deliverables.filter(d => d.status === 'completed').length} completed</span>
                              {objective.lastUpdated && (
                                <span>🕐 Updated {new Date(objective.lastUpdated).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>

                          {/* Expand/Collapse Icon */}
                          <div className="ml-4">
                            <svg 
                              className={`w-5 h-5 text-gray-400 transform transition-transform ${
                                expandedObjectives.has(objective.id) ? 'rotate-180' : ''
                              }`} 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {/* Expanded Deliverables */}
                      {expandedObjectives.has(objective.id) && objective.deliverables.length > 0 && (
                        <div className="border-t border-gray-100 bg-gray-50 p-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-3">Deliverables</h4>
                          <div className="space-y-2">
                            {objective.deliverables.map((deliverable, idx) => (
                              <div key={deliverable.id || idx} className="flex items-center space-x-2 text-sm">
                                <span className={`w-4 h-4 ${
                                  deliverable.status === 'completed' ? 'text-green-500' : 'text-gray-400'
                                }`}>
                                  {deliverable.status === 'completed' ? '✅' : '⏳'}
                                </span>
                                <span className={`flex-1 ${
                                  deliverable.status === 'completed' ? 'text-gray-700' : 'text-gray-500'
                                }`}>
                                  {deliverable.title || `Deliverable ${idx + 1}`}
                                </span>
                                {deliverable.progress !== undefined && (
                                  <span className="text-xs text-gray-500">{deliverable.progress}%</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* AI Insights Tab */}
            {activeTab === 'insights' && (
              <div className="space-y-6">
                {/* Theme Analysis */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
                  <h3 className="font-medium text-gray-900 mb-4">🧠 AI Theme Analysis</h3>
                  
                  <div className="space-y-4">
                    {/* Confidence Score */}
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-700">AI Confidence Score</span>
                        <span className="font-medium">{theme.confidence_score}%</span>
                      </div>
                      <div className="w-full bg-white rounded-full h-3">
                        <div 
                          className={`h-3 rounded-full ${
                            theme.confidence_score >= 80 ? 'bg-green-500' :
                            theme.confidence_score >= 60 ? 'bg-yellow-500' :
                            'bg-orange-500'
                          }`}
                          style={{ width: `${theme.confidence_score}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {theme.confidence_score >= 80 ? 'High confidence in theme grouping' :
                         theme.confidence_score >= 60 ? 'Moderate confidence - manual review recommended' :
                         'Low confidence - consider manual reorganization'}
                      </p>
                    </div>

                    {/* Business Impact */}
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">💼 Business Impact</h4>
                      <p className="text-sm text-gray-600">{theme.business_value}</p>
                    </div>

                    {/* AI Reasoning */}
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">🎯 Grouping Rationale</h4>
                      <p className="text-sm text-gray-600">{theme.reasoning}</p>
                    </div>

                    {/* Recommendations */}
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">💡 AI Recommendations</h4>
                      <ul className="space-y-2 text-sm text-gray-600">
                        {theme.statistics.average_progress < 30 && (
                          <li className="flex items-start">
                            <span className="text-orange-500 mr-2">⚠️</span>
                            <span>This theme has low overall progress ({Math.round(theme.statistics.average_progress)}%). Consider prioritizing resources here.</span>
                          </li>
                        )}
                        {theme.statistics.completed_deliverables === 0 && theme.statistics.total_deliverables > 0 && (
                          <li className="flex items-start">
                            <span className="text-red-500 mr-2">🚨</span>
                            <span>No deliverables completed yet. Review blockers and dependencies.</span>
                          </li>
                        )}
                        {theme.statistics.average_progress >= 80 && (
                          <li className="flex items-start">
                            <span className="text-green-500 mr-2">✨</span>
                            <span>Excellent progress! This theme is nearing completion.</span>
                          </li>
                        )}
                        {theme.statistics.total_goals === 1 && (
                          <li className="flex items-start">
                            <span className="text-blue-500 mr-2">💭</span>
                            <span>Single-objective theme. Consider if this needs its own theme or could be merged.</span>
                          </li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}