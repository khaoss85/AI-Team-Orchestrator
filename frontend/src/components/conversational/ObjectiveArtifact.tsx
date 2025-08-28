'use client'

import React, { useState, useEffect } from 'react'
import DeliverableActionBar from './DeliverableActionBar'
import MarkdownRenderer from './MarkdownRenderer'
import { api } from '@/utils/api'
import {
  GoalProgressDetail,
  DeliverableItem,
  UnblockRequest,
  DELIVERABLE_STATUS_CONFIG,
  UNBLOCK_ACTION_CONFIG,
  DeliverableStatus
} from '@/types/goal-progress'

interface ObjectiveData {
  objective: {
    id?: string
    description: string
    targetDate?: string
    progress?: number
  }
  progress: number
  deliverables: any[]
  goal_data?: any
  metadata?: Record<string, any>
  target_value?: number
  current_value?: number
  metric_type?: string
  status?: any
  priority?: any
  created_at?: string
  updated_at?: string
}

interface ObjectiveArtifactProps {
  objectiveData: ObjectiveData
  workspaceId: string
  title: string
}

export default function ObjectiveArtifact({ 
  objectiveData, 
  workspaceId, 
  title 
}: ObjectiveArtifactProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'deliverables'>('overview')
  const [goalProgressDetail, setGoalProgressDetail] = useState<GoalProgressDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [unblockingInProgress, setUnblockingInProgress] = useState<string | null>(null)
  
  const goalId = objectiveData.objective.id

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusColor = (status?: any) => {
    const statusStr = String(status || '').toLowerCase()
    switch (statusStr) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'active': return 'bg-blue-100 text-blue-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      case 'cancelled': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority?: any) => {
    const priorityStr = String(priority || '').toLowerCase()
    switch (priorityStr) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // Load goal progress details when component mounts or goalId changes
  useEffect(() => {
    if (goalId && workspaceId) {
      loadGoalProgressDetails()
    } else {
      setLoading(false)
    }
  }, [goalId, workspaceId])

  const loadGoalProgressDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const details = await api.goalProgress.getDetails(workspaceId, goalId!, true)
      setGoalProgressDetail(details)
    } catch (err) {
      console.error('Failed to load goal progress details:', err)
      setError(err instanceof Error ? err.message : 'Failed to load progress details')
    } finally {
      setLoading(false)
    }
  }

  const handleUnblockAction = async (action: string, deliverableIds?: string[]) => {
    if (!goalId) return
    
    try {
      setUnblockingInProgress(action)
      const unblockRequest: UnblockRequest = {
        action: action as any,
        deliverable_ids: deliverableIds
      }
      
      await api.goalProgress.unblock(workspaceId, goalId, unblockRequest)
      
      // Reload progress details to show updated status
      await loadGoalProgressDetails()
    } catch (err) {
      console.error('Failed to execute unblock action:', err)
      setError(err instanceof Error ? err.message : 'Failed to execute unblock action')
    } finally {
      setUnblockingInProgress(null)
    }
  }

  // Show loading state
  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Loading progress details...</span>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="p-6">
        <div className="border-b border-gray-100 pb-4 mb-6">
          <h1 className="text-xl font-semibold text-gray-900 mb-2">{title}</h1>
          <p className="text-gray-600 text-sm leading-relaxed">{objectiveData.objective.description}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">❌</span>
            <div>
              <h3 className="font-medium text-red-800">Failed to Load Progress Details</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                onClick={() => loadGoalProgressDetails()}
                className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 text-sm rounded"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Clean Header - Claude Code style */}
      <div className="border-b border-gray-100 pb-4 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-gray-900 mb-2">{title}</h1>
            <p className="text-gray-600 text-sm leading-relaxed">{objectiveData.objective.description}</p>
          </div>
          <div className="flex flex-col items-end space-y-1 ml-4">
            {objectiveData.status && (
              <span className={`px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(objectiveData.status)}`}>
                {String(objectiveData.status).charAt(0).toUpperCase() + String(objectiveData.status).slice(1)}
              </span>
            )}
            {objectiveData.priority && (
              <span className={`px-2 py-1 rounded-md text-xs font-medium ${getPriorityColor(objectiveData.priority)}`}>
                {String(objectiveData.priority).charAt(0).toUpperCase() + String(objectiveData.priority).slice(1)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-700">Progress</span>
          <span className="text-sm font-medium text-gray-900">{Math.round(objectiveData.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              objectiveData.progress >= 100 ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${Math.min(objectiveData.progress, 100)}%` }}
          ></div>
        </div>
        {objectiveData.current_value !== undefined && objectiveData.target_value !== undefined && (
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{objectiveData.current_value}</span>
            <span>{objectiveData.target_value}</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <TabButton 
          active={activeTab === 'overview'} 
          onClick={() => setActiveTab('overview')}
          label="Overview"
        />
        <TabButton 
          active={activeTab === 'deliverables'} 
          onClick={() => setActiveTab('deliverables')}
          label="Deliverables"
        />
      </div>

      {/* Content */}
      <div className="">
        {activeTab === 'overview' && (
          <OverviewTab 
            objectiveData={objectiveData} 
            goalProgressDetail={goalProgressDetail}
          />
        )}
        
        {activeTab === 'deliverables' && (
          <DeliverablesTab 
            deliverables={objectiveData.deliverables || []} 
            metadata={objectiveData.metadata}
            goalProgressDetail={goalProgressDetail}
            onUnblockAction={handleUnblockAction}
            unblockingInProgress={unblockingInProgress}
            objectiveData={objectiveData}
          />
        )}
      </div>
    </div>
  )
}

// Tab Button Component
interface TabButtonProps {
  active: boolean
  onClick: () => void
  label: string
}

function TabButton({ active, onClick, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        px-4 py-2 text-sm font-medium border-b-2 transition-colors
        ${active
          ? 'text-blue-600 border-blue-600'
          : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
        }
      `}
    >
      {label}
    </button>
  )
}

// Overview Tab Component
interface OverviewTabProps {
  objectiveData: ObjectiveData
  goalProgressDetail: GoalProgressDetail | null
}

function OverviewTab({ objectiveData, goalProgressDetail }: OverviewTabProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const progressPercentage = Math.round(objectiveData.progress)
  const isCompleted = progressPercentage >= 100

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <div className="text-center">
          <div className="text-4xl font-bold text-blue-600 mb-2">
            {progressPercentage}%
          </div>
          <div className="text-gray-700 mb-4">
            {isCompleted ? 'Objective Completed!' : 'Progress towards goal'}
          </div>
          <div className="w-full bg-white rounded-full h-4 shadow-inner mb-4">
            <div 
              className={`h-4 rounded-full transition-all duration-500 ${
                isCompleted ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            ></div>
          </div>
          
          {/* Progress Analysis */}
          {goalProgressDetail && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-sm">
              <div className="bg-white rounded-lg p-3 border">
                <div className="font-medium text-gray-700">Goal Progress</div>
                <div className="text-2xl font-bold text-blue-600">
                  {objectiveData.current_value}/{objectiveData.target_value}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Based on goal completion tracking
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 border">
                <div className="font-medium text-gray-700">API Deliverables</div>
                <div className="text-2xl font-bold text-green-600">
                  {goalProgressDetail.deliverable_stats.completed}/{goalProgressDetail.deliverable_stats.total}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {goalProgressDetail.progress_analysis.api_calculated_progress.toFixed(1)}% API completion
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Basic Information and Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Basic Information</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Metric Type:</span>
              <span className="font-medium">{objectiveData.metric_type || 'Not specified'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Current Value:</span>
              <span className="font-medium">{objectiveData.current_value || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Target Value:</span>
              <span className="font-medium">{objectiveData.target_value || 'Not set'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Created:</span>
              <span className="font-medium">{formatDate(objectiveData.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Updated:</span>
              <span className="font-medium">{formatDate(objectiveData.updated_at)}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Timeline</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Target Date:</span>
              <span className="font-medium">{formatDate(objectiveData.objective.targetDate)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Days Since Created:</span>
              <span className="font-medium">
                {objectiveData.created_at 
                  ? Math.floor((Date.now() - new Date(objectiveData.created_at).getTime()) / (1000 * 60 * 60 * 24))
                  : 'Unknown'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Summary */}
      {(objectiveData.current_value !== undefined || objectiveData.target_value !== undefined) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {objectiveData.current_value || 0}
            </div>
            <div className="text-sm text-gray-600">Current Value</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">
              {objectiveData.target_value || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Target Value</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-orange-600">
              {objectiveData.target_value && objectiveData.current_value 
                ? Math.max(0, objectiveData.target_value - objectiveData.current_value)
                : 'N/A'
              }
            </div>
            <div className="text-sm text-gray-600">Remaining</div>
          </div>
        </div>
      )}
    </div>
  )
}

// Simplified Deliverables Tab - Claude Code Style
interface DeliverablesTabProps {
  deliverables: any[]
  metadata?: Record<string, any>
  goalProgressDetail: GoalProgressDetail | null
  onUnblockAction: (action: string, deliverableIds?: string[]) => void
  unblockingInProgress: string | null
  objectiveData: ObjectiveData
}

function DeliverablesTab({ 
  deliverables, 
  metadata, 
  goalProgressDetail, 
  onUnblockAction, 
  unblockingInProgress,
  objectiveData
}: DeliverablesTabProps) {
  const [expandedDeliverable, setExpandedDeliverable] = useState<number | null>(null)
  const [autoCompletingMissing, setAutoCompletingMissing] = useState(false)

  if (!deliverables || deliverables.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📦</div>
        <div className="text-gray-600 mb-2">No deliverables available yet</div>
        <div className="text-sm text-gray-500 mb-6">Deliverables will appear here as tasks are completed</div>
        
        {/* Auto-completion button for missing deliverables */}
        {objectiveData.objective.id && (
          <button
            onClick={async () => {
              setAutoCompletingMissing(true)
              try {
                await fetch(`/api/auto-completion/workspace/${objectiveData.objective.id}/missing-deliverables`, {
                  method: 'POST'
                })
                // Reload the page or trigger a refresh
                window.location.reload()
              } catch (error) {
                console.error('Failed to auto-complete missing deliverables:', error)
              } finally {
                setAutoCompletingMissing(false)
              }
            }}
            disabled={autoCompletingMissing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
          >
            {autoCompletingMissing ? 'Creating deliverables...' : 'Auto-complete missing deliverables'}
          </button>
        )}
      </div>
    )
  }

  // Helper function to detect content type and format
  const detectContentType = (content: string): 'markdown' | 'html' | 'json' | 'text' => {
    if (!content || typeof content !== 'string') return 'text'
    
    // Check for markdown patterns
    if (content.includes('##') || content.includes('**') || content.includes('[](') || content.includes('- ') || 
        (content.includes('|') && content.includes('\n') && /\|.*\|.*\|/.test(content))) {
      return 'markdown'
    }
    
    // Check for HTML
    if (content.trim().startsWith('<') && content.includes('</')  {
      return 'html'
    }
    
    // Check for JSON
    if ((content.trim().startsWith('{') && content.trim().endsWith('}')) || 
        (content.trim().startsWith('[') && content.trim().endsWith(']'))) {
      try {
        JSON.parse(content)
        return 'json'
      } catch {
        return 'text'
      }
    }
    
    return 'text'
  }

  const renderContent = (content: any) => {
    if (!content) return <div className="text-gray-500 italic">No content available</div>
    
    if (typeof content === 'string') {
      const contentType = detectContentType(content)
      
      switch (contentType) {
        case 'markdown':
          return (
            <div className="prose prose-sm max-w-none">
              <MarkdownRenderer content={content} />
            </div>
          )
        
        case 'html':
          return (
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: content }}
            />
          )
        
        case 'json':
          try {
            const jsonContent = JSON.parse(content)
            return (
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 overflow-x-auto">
                  {JSON.stringify(jsonContent, null, 2)}
                </pre>
              </div>
            )
          } catch {
            // Fall through to text handling
          }
          break
        
        default:
          return (
            <div className="whitespace-pre-wrap text-sm text-gray-700">
              {content}
            </div>
          )
      }
    }

    if (typeof content === 'object') {
      // Handle structured content
      if (content.summary || content.sections || content.deliverables) {
        return (
          <div className="space-y-4">
            {content.summary && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">{content.summary}</div>
              </div>
            )}
            
            {content.sections && Array.isArray(content.sections) && (
              <div className="space-y-3">
                {content.sections.map((section: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-blue-200 pl-4">
                    <h5 className="font-medium text-gray-800 mb-1">{section.title || `Section ${idx + 1}`}</h5>
                    <div className="text-sm text-gray-600 whitespace-pre-wrap">
                      {section.content || section.description}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {content.deliverables && Array.isArray(content.deliverables) && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Key Deliverables</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  {content.deliverables.map((item: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-500 mr-2 mt-1">•</span>
                      <span>{typeof item === 'string' ? item : item.title || item.name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      } else {
        // Fallback: show as formatted JSON
        return (
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(content, null, 2)}
            </pre>
          </div>
        )
      }
    }

    return <div className="text-gray-500 italic">Content format not supported</div>
  }

  return (
    <div className="space-y-4">
      {/* Auto-completion for missing deliverables */}
      {objectiveData.current_value < objectiveData.target_value && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-blue-900 mb-1">Missing Deliverables</h4>
              <p className="text-sm text-blue-700">
                {objectiveData.current_value} of {objectiveData.target_value} deliverables completed
              </p>
            </div>
            <button
              onClick={async () => {
                setAutoCompletingMissing(true)
                try {
                  await fetch(`/api/auto-completion/workspace/${objectiveData.objective.id}/missing-deliverables`, {
                    method: 'POST'
                  })
                  // Reload the page or trigger a refresh
                  window.location.reload()
                } catch (error) {
                  console.error('Failed to auto-complete missing deliverables:', error)
                } finally {
                  setAutoCompletingMissing(false)
                }
              }}
              disabled={autoCompletingMissing}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50"
            >
              {autoCompletingMissing ? 'Creating...' : 'Auto-complete'}
            </button>
          </div>
        </div>
      )}
      
      {/* Clean deliverable list - Claude Code style */}
      <div className="space-y-3">
        {deliverables.map((deliverable, index) => {
          const isExpanded = expandedDeliverable === index
          
          return (
            <div key={deliverable.id || index} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Header */}
              <div 
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-100"
                onClick={() => setExpandedDeliverable(isExpanded ? null : index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-lg">📄</div>
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {deliverable.title || `Deliverable ${index + 1}`}
                      </h4>
                      <p className="text-sm text-gray-500">
                        Created {new Date(deliverable.created_at || '').toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                      Complete
                    </span>
                    <svg 
                      className={`h-5 w-5 text-gray-400 transition-transform ${
                        isExpanded ? 'rotate-180' : ''
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
          
              {/* Content - Claude Code style */}
              {isExpanded && (
                <div className="p-6 bg-gray-50">
                  <div className="bg-white rounded-lg border p-6">
                    {renderContent(deliverable.content)}
                  </div>
                  
                  {/* Action buttons */}
                  <div className="mt-4 flex items-center space-x-2">
                    <DeliverableActionBar 
                      deliverable={{
                        id: deliverable.id || `deliverable-${index}`,
                        title: deliverable.title || `Deliverable ${index + 1}`,
                        content: deliverable.content,
                        contentType: 'HTML',
                        type: deliverable.type
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}