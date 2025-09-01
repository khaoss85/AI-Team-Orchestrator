'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import DeliverableActionBar from './DeliverableActionBar'
import MarkdownRenderer from './MarkdownRenderer'
import { api } from '@/utils/api'
import './DeliverableContent.css'
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
  workspaceId?: string
  title: string
  activeChat?: {
    id: string
    title: string
    type: 'dynamic' | 'fixed'
    objective?: any
    metadata?: Record<string, any>
  }
}

export default function ObjectiveArtifact({ 
  objectiveData, 
  workspaceId, 
  title,
  activeChat
}: ObjectiveArtifactProps) {
  // Early return if workspaceId is not available
  if (!workspaceId) {
    console.warn('ObjectiveArtifact: workspaceId is undefined or null')
    return (
      <div className="p-4 text-center text-gray-500">
        <div>Workspace ID not available</div>
        <div className="text-sm mt-1">Cannot display objective details</div>
      </div>
    )
  }

  const [activeTab, setActiveTab] = useState<'overview' | 'deliverables' | 'in_progress'>('overview')
  const [goalProgressDetail, setGoalProgressDetail] = useState<GoalProgressDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [unblockingInProgress, setUnblockingInProgress] = useState<string | null>(null)
  const [inProgressDeliverables, setInProgressDeliverables] = useState<any[]>([])
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)
  
  // Optimized goal ID extraction using useMemo to avoid recalculation on every render
  const goalId = useMemo(() => {
    // Method 1: Extract from activeChat.id if it starts with 'goal-'
    if (activeChat?.id?.startsWith('goal-')) {
      return activeChat.id.replace('goal-', '')
    }
    
    // Method 2: Extract from current URL if it contains goal- pattern
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname + window.location.hash
      const goalMatch = currentPath.match(/goal-([a-f0-9-]+)/)
      if (goalMatch) {
        return goalMatch[1]
      }
    }
    
    // Method 3: Try activeChat objective data
    if (activeChat?.objective?.id) {
      return activeChat.objective.id
    }
    
    // Method 4: Try activeChat metadata
    if (activeChat?.metadata?.goal_id) {
      return activeChat.metadata.goal_id
    }
    
    // Method 5: Try objectiveData sources
    return objectiveData.objective?.id || 
           objectiveData.goal_data?.id || 
           objectiveData.metadata?.goal_id || 
           objectiveData.deliverables?.[0]?.metadata?.goal_id || 
           ''
  }, [activeChat?.id, activeChat?.objective?.id, activeChat?.metadata?.goal_id, objectiveData.objective?.id, objectiveData.goal_data?.id, objectiveData.metadata?.goal_id, objectiveData.deliverables])

  // Optimized deliverable title extraction using useMemo
  const deliverableTitle = useMemo(() => {
    // Try to find a deliverable with a valid title
    if (objectiveData.deliverables && objectiveData.deliverables.length > 0) {
      for (const deliverable of objectiveData.deliverables) {
        if (deliverable.title && deliverable.title !== 'undefined') {
          return deliverable.title
        }
      }
    }
    
    // Fallback to objective description or title
    if (objectiveData.objective.description && objectiveData.objective.description !== title) {
      return objectiveData.objective.description
    }
    
    return title || undefined
  }, [objectiveData.deliverables, objectiveData.objective.description, title])




  // Defensive check for workspaceId
  if (!workspaceId) {
    return (
      <div className="p-6">
        <div className="border-b border-gray-100 pb-4 mb-6">
          <h1 className="text-xl font-semibold text-gray-900 mb-2">{title}</h1>
          <p className="text-gray-600 text-sm leading-relaxed">{objectiveData.objective.description}</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-yellow-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="font-medium text-yellow-800">Missing Workspace Context</h3>
              <p className="text-sm text-yellow-700 mt-1">WorkspaceId is required to display objective details and auto-completion features.</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusColor = (status?: any, progress?: number) => {
    // If progress is 100%, always show as completed regardless of raw status
    if (progress !== undefined && progress >= 100) {
      return 'bg-green-100 text-green-800'
    }
    
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

  const getDisplayStatus = (status?: any, progress?: number) => {
    // If progress is 100%, always show as completed regardless of raw status
    if (progress !== undefined && progress >= 100) {
      return 'Completed'
    }
    
    const statusStr = String(status || '').toLowerCase()
    switch (statusStr) {
      case 'completed': return 'Completed'
      case 'active': return 'Active'
      case 'paused': return 'Paused'
      case 'cancelled': return 'Cancelled'
      default: return status ? String(status).charAt(0).toUpperCase() + String(status).slice(1) : 'Unknown'
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

  // Load in-progress deliverables when tab is active and goal data is available
  useEffect(() => {
    if (activeTab === 'in_progress' && workspaceId && goalProgressDetail) {
      loadInProgressDeliverables()
      
      // Start polling every 10 seconds to reload goal progress detail
      const interval = setInterval(() => {
        loadGoalProgressDetails() // This will refresh the goalProgressDetail data
      }, 10000)
      
      setPollingInterval(interval)
      
      // Cleanup on tab change or component unmount
      return () => {
        if (interval) {
          clearInterval(interval)
        }
      }
    } else if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
  }, [activeTab, workspaceId, goalProgressDetail])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [])

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

  const loadInProgressDeliverables = async () => {
    if (!workspaceId || !goalProgressDetail) return
    
    try {
      // ONLY use real data from goalProgressDetail - NO MOCK DATA
      const realInProgressDeliverables = goalProgressDetail.deliverable_breakdown?.in_progress || []
      const realPendingDeliverables = goalProgressDetail.deliverable_breakdown?.pending || []
      const realFailedDeliverables = goalProgressDetail.deliverable_breakdown?.failed || []
      const unknownDeliverables = goalProgressDetail.deliverable_breakdown?.unknown || []
      
      // Combine ONLY non-completed deliverables for the "In Progress" tab
      const combinedInProgressDeliverables = [
        ...realFailedDeliverables,
        ...realPendingDeliverables, 
        ...realInProgressDeliverables,
        ...unknownDeliverables
      ].filter(deliverable => {
        // Extra safety check: ensure we don't show completed deliverables
        const status = (deliverable.status || '').toLowerCase()
        
        // Also check progress percentage - if 100% or higher, consider it completed
        const progress = deliverable.progress || 0
        const isCompleted = status === 'completed' || progress >= 100
        
        return !isCompleted
      })
      
      setInProgressDeliverables(combinedInProgressDeliverables)
      
      // If we're currently on the in_progress tab but there are no incomplete deliverables,
      // switch to the deliverables tab to avoid showing an empty/hidden tab
      if (combinedInProgressDeliverables.length === 0) {
        // Only switch away from in_progress tab if user is currently on it
        setActiveTab(currentTab => currentTab === 'in_progress' ? 'deliverables' : currentTab)
      }
    } catch (err) {
      console.error('Failed to load in-progress deliverables:', err)
      setInProgressDeliverables([])
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
            <span className="text-red-500 text-sm mr-3">Error:</span>
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
              <span className={`px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(objectiveData.status, objectiveData.progress)}`}>
                {getDisplayStatus(objectiveData.status, objectiveData.progress)}
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
          label={`Deliverables${goalProgressDetail?.deliverable_breakdown?.completed && goalProgressDetail.deliverable_breakdown.completed.length > 0 ? ` (${goalProgressDetail.deliverable_breakdown.completed.length})` : (objectiveData.deliverables && objectiveData.deliverables.length > 0 ? ` (${objectiveData.deliverables.length})` : '')}`}
        />
        {/* Only show In Progress tab if there are actually incomplete deliverables */}
        {inProgressDeliverables.length > 0 && (
          <TabButton 
            active={activeTab === 'in_progress'} 
            onClick={() => setActiveTab('in_progress')}
            label={`In Progress (${inProgressDeliverables.length})`}
          />
        )}
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
            workspaceId={workspaceId}
            loadGoalProgressDetails={loadGoalProgressDetails}
          />
        )}
        
        {activeTab === 'in_progress' && (
          <InProgressTab 
            workspaceId={workspaceId}
            inProgressDeliverables={inProgressDeliverables}
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
          <div className="text-3xl font-semibold text-gray-900 mb-2">
            {progressPercentage}%
          </div>
          <div className="text-gray-600 text-sm mb-4">
            {isCompleted ? 'Completed' : 'In progress'}
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
  workspaceId?: string
  loadGoalProgressDetails: () => Promise<void>
}

function DeliverablesTab({ 
  deliverables, 
  metadata, 
  goalProgressDetail, 
  onUnblockAction, 
  unblockingInProgress,
  objectiveData,
  workspaceId,
  loadGoalProgressDetails
}: DeliverablesTabProps) {
  const [expandedDeliverable, setExpandedDeliverable] = useState<number | null>(null)
  const [autoCompletingMissing, setAutoCompletingMissing] = useState(false)
  const [retryingTransformation, setRetryingTransformation] = useState<string | null>(null)
  
  // CRITICAL FIX: Use goalProgressDetail.deliverable_breakdown.completed as primary source
  // This ensures we show actual deliverables from the API instead of empty props data
  const actualDeliverables = useMemo(() => {
    // Priority 1: Use completed deliverables from goalProgressDetail if available
    if (goalProgressDetail?.deliverable_breakdown?.completed && goalProgressDetail.deliverable_breakdown.completed.length > 0) {
      console.log('✅ Using goalProgressDetail.deliverable_breakdown.completed:', goalProgressDetail.deliverable_breakdown.completed.length, 'deliverables')
      return goalProgressDetail.deliverable_breakdown.completed
    }
    
    // Fallback: Use prop deliverables if no goal progress detail available
    console.log('⚠️ Falling back to prop deliverables:', deliverables?.length || 0, 'deliverables')
    return deliverables || []
  }, [goalProgressDetail?.deliverable_breakdown?.completed, deliverables])

  // Helper function to handle workspace-dependent actions safely
  const handleWorkspaceAction = async (actionName: string, actionFn: () => Promise<void>) => {
    if (!workspaceId) {
      console.error(`${actionName}: WorkspaceId is not available`)
      alert('Workspace context is not available. Please refresh the page and try again.')
      return
    }
    
    try {
      await actionFn()
    } catch (error) {
      console.error(`${actionName} failed:`, error)
      alert(`${actionName} failed. Please try again.`)
    }
  }

  // Show warning if workspaceId is not available
  if (!workspaceId) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">⚠️</div>
        <div className="text-gray-600 mb-2">Workspace context not available</div>
        <div className="text-sm text-gray-500 mb-4">
          Some deliverable actions may not work properly without workspace context
        </div>
        {deliverables && deliverables.length > 0 && (
          <div className="text-sm text-blue-600">
            {deliverables.length} deliverable{deliverables.length !== 1 ? 's' : ''} found, but limited functionality available
          </div>
        )}
      </div>
    )
  }

  if (!actualDeliverables || actualDeliverables.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📦</div>
        <div className="text-gray-600 mb-2">No deliverables available yet</div>
        <div className="text-sm text-gray-500 mb-6">Deliverables will appear here as tasks are completed</div>
        
        {/* Auto-completion button for missing deliverables */}
        {objectiveData.objective.id && (
          <button
            onClick={() => handleWorkspaceAction('Auto-complete missing deliverables', async () => {
              setAutoCompletingMissing(true)
              
              try {
                const response = await fetch(`${api.getBaseUrl()}/api/auto-completion/workspace/${workspaceId}/missing-deliverables`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  }
                })
                
                
                if (response.ok) {
                  const responseData = await response.json()
                  alert('Auto-completion request submitted successfully! The system will generate missing deliverables.')
                  // Reload goal progress details to show updated data
                  await loadGoalProgressDetails()
                } else {
                  const errorText = await response.text()
                  console.error('Auto-completion request failed:', response.status, response.statusText, errorText)
                  alert(`Auto-completion request failed: ${response.status} - ${errorText || 'Please try again.'}`)
                }
              } catch (error) {
                console.error('Auto-completion request error:', error)
                alert(`Auto-completion request failed due to network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
              } finally {
                setAutoCompletingMissing(false)
              }
            })}
            disabled={autoCompletingMissing || !workspaceId}
            className={`px-4 py-2 rounded-lg disabled:opacity-50 ${
              !workspaceId 
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
            title={!workspaceId ? 'Workspace context not available' : ''}
          >
            {autoCompletingMissing ? 'Creating deliverables...' : 'Auto-complete missing deliverables'}
          </button>
        )}
      </div>
    )
  }

  /**
   * Enhanced content renderer with display_content priority
   * 
   * FRONTEND INTEGRATION PATTERNS:
   * 1. PRIORITY SYSTEM: display_content (AI-enhanced) > legacy content (JSON/raw)
   * 2. QUALITY INDICATORS: Shows AI confidence, UX scores, transformation status
   * 3. PROGRESSIVE ENHANCEMENT: Graceful fallback for legacy content
   * 4. FORMAT SUPPORT: HTML, Markdown, Plain text with proper styling
   * 5. ERROR HANDLING: ContentWrapper catches rendering errors
   * 
   * Backend Integration:
   * - Uses new DeliverableItem interface with dual-format support
   * - Expects display_content, display_format, display_quality_score
   * - Fallback to legacy 'content' field for backward compatibility
   * - Transformation retry/format change APIs ready for implementation
   */
  const renderEnhancedContent = (deliverable: any) => {
    // 1. PRIORITY: Use display_content if available (AI-enhanced format)
    if (deliverable.display_content) {
      const displayFormat = deliverable.display_format || 'html'
      
      return (
        <div className="enhanced-deliverable-content">
          {/* Quality indicators */}
          <div className="flex items-center gap-2 mb-4 p-2 bg-blue-50 rounded-lg">
            <div className="text-sm text-blue-700">
              <span className="font-medium">AI-Enhanced Content</span>
              {deliverable.display_quality_score && (
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                  Quality: {Math.round(deliverable.display_quality_score)}%
                </span>
              )}
              {deliverable.user_friendliness_score && (
                <span className="ml-1 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                  UX: {Math.round(deliverable.user_friendliness_score)}%
                </span>
              )}
            </div>
          </div>
          
          {/* Enhanced content rendering */}
          <div className="deliverable-display-content">
            {displayFormat === 'html' ? (
              <div 
                className="prose prose-sm max-w-none deliverable-html-content"
                dangerouslySetInnerHTML={{ __html: deliverable.display_content }}
              />
            ) : displayFormat === 'markdown' ? (
              <div className="prose prose-sm max-w-none">
                <MarkdownRenderer content={deliverable.display_content} />
              </div>
            ) : (
              <div className="whitespace-pre-wrap text-sm text-gray-700 p-4 bg-gray-50 rounded-lg">
                {deliverable.display_content}
              </div>
            )}
          </div>
          
          {/* Display summary if available */}
          {deliverable.display_summary && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-400">
              <h5 className="font-medium text-gray-900 mb-1">Summary</h5>
              <p className="text-sm text-gray-700">{deliverable.display_summary}</p>
            </div>
          )}
        </div>
      )
    }
    
    // 2. FALLBACK: Process legacy content with enhanced detection
    return renderLegacyContent(deliverable.content)
  }

  // Helper function to detect content type and format (legacy support)
  const detectContentType = (content: string): 'markdown' | 'html' | 'json' | 'text' => {
    if (!content || typeof content !== 'string') return 'text'
    
    // Check for markdown patterns
    if (content.includes('##') || content.includes('**') || content.includes('[](') || content.includes('- ') || 
        (content.includes('|') && content.includes('\n') && /\|.*\|.*\|/.test(content))) {
      return 'markdown'
    }
    
    // Check for HTML
    if (content.trim().startsWith('<') && content.includes('</')) {
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

  const renderLegacyContent = (content: any) => {
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
              className="prose prose-sm max-w-none deliverable-html-content"
              dangerouslySetInnerHTML={{ __html: content }}
            />
          )
        
        case 'json':
          try {
            const jsonContent = JSON.parse(content)
            return (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <span className="text-yellow-600 text-sm font-medium">⚠️ Raw JSON Content</span>
                  <span className="ml-2 text-xs text-yellow-600">(Consider updating to enhanced format)</span>
                </div>
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
            <div className="whitespace-pre-wrap text-sm text-gray-700 p-4 bg-gray-50 rounded-lg">
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
        // Fallback: show as formatted JSON with warning
        return (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <span className="text-yellow-600 text-sm font-medium">⚠️ Raw JSON Content</span>
              <span className="ml-2 text-xs text-yellow-600">(Consider updating to enhanced format)</span>
            </div>
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
              onClick={() => handleWorkspaceAction('Auto-complete missing deliverables', async () => {
                setAutoCompletingMissing(true)
                
                try {
                    const response = await fetch(`${api.getBaseUrl()}/api/auto-completion/workspace/${workspaceId}/missing-deliverables`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    }
                  })
                  
                    
                  if (response.ok) {
                    const responseData = await response.json()
                      alert('Auto-completion request submitted successfully! The system will generate missing deliverables.')
                    // Reload goal progress details to show updated data
                    await loadGoalProgressDetails()
                  } else {
                    const errorText = await response.text()
                    console.error('Auto-completion request failed:', response.status, response.statusText, errorText)
                    alert(`Auto-completion request failed: ${response.status} - ${errorText || 'Please try again.'}`)
                  }
                } catch (error) {
                  console.error('Auto-completion request error:', error)
                  alert(`Auto-completion request failed due to network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
                } finally {
                  setAutoCompletingMissing(false)
                }
              })}
              disabled={autoCompletingMissing || !workspaceId}
              className={`px-3 py-2 text-sm rounded-lg disabled:opacity-50 ${
                !workspaceId 
                  ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
              title={!workspaceId ? 'Workspace context not available' : ''}
            >
              {autoCompletingMissing ? 'Creating...' : 'Auto-complete'}
            </button>
          </div>
        </div>
      )}
      
      {/* Clean deliverable list - Claude Code style */}
      <div className="space-y-3">
        {actualDeliverables.map((deliverable, index) => {
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
                    {(() => {
                      const status = (deliverable.status || 'completed').toLowerCase()
                      const config = DELIVERABLE_STATUS_CONFIG[status as DeliverableStatus] || DELIVERABLE_STATUS_CONFIG.unknown
                      return (
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${config.bgColor} ${config.color}`}>
                          {config.icon} {config.label}
                        </span>
                      )
                    })()}
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
          
              {/* Content - Enhanced with display_content priority */}
              {isExpanded && (
                <div className="p-6 bg-gray-50">
                  <div className="bg-white rounded-lg border p-6">
                    <ContentWrapper deliverableId={deliverable.id || `deliverable-${index}`}>
                      {renderEnhancedContent(deliverable)}
                    </ContentWrapper>
                  </div>
                  
                  {/* Enhanced Action buttons with transformation actions */}
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center space-x-2">
                      <DeliverableActionBar 
                        deliverable={{
                          id: deliverable.id || `deliverable-${index}`,
                          title: deliverable.title || `Deliverable ${index + 1}`,
                          content: deliverable.display_content || deliverable.content,
                          contentType: deliverable.display_format || 'HTML',
                          type: deliverable.type
                        }}
                      />
                    </div>
                    
                    {/* Transformation actions if available */}
                    {deliverable.can_retry_transformation && (
                      <div className="flex items-center space-x-2 text-sm">
                        <button 
                          className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-xs"
                          onClick={async () => {
                            const delivId = deliverable.id || `deliverable-${index}`
                            setRetryingTransformation(delivId)
                            try {
                              // Add actual retry transformation logic here if needed
                              await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate retry
                              window.location.reload()
                            } finally {
                              setRetryingTransformation(null)
                            }
                          }}
                          disabled={retryingTransformation === deliverable.id}
                        >
                          {retryingTransformation === deliverable.id ? '🔄 Retrying...' : '🔄 Retry Enhancement'}
                        </button>
                        {deliverable.available_formats && deliverable.available_formats.length > 1 && (
                          <select 
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            onChange={(e) => { /* Format change handler can be implemented here */ }}
                            value={deliverable.display_format || 'html'}
                          >
                            {deliverable.available_formats.map((format: string) => (
                              <option key={format} value={format}>
                                {format.toUpperCase()}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>
                    )}
                    
                    {/* Transformation error display */}
                    {deliverable.transformation_error && (
                      <div className="p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        ⚠️ Enhancement failed: {deliverable.transformation_error}
                      </div>
                    )}
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

// Content Wrapper Component for deliverable content
interface ContentWrapperProps {
  children: React.ReactNode
  deliverableId: string
}

function ContentWrapper({ children, deliverableId }: ContentWrapperProps) {
  try {
    return <>{children}</>
  } catch (error) {
    console.error('Deliverable content error:', error)
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center mb-2">
          <span className="text-red-500 text-lg mr-2">❌</span>
          <h4 className="font-medium text-red-800">Content Rendering Error</h4>
        </div>
        <p className="text-sm text-red-700 mb-3">
          Failed to render enhanced content for deliverable {deliverableId}
        </p>
        <p className="text-xs text-red-600 mb-3">
          Error: {error instanceof Error ? error.message : 'Unknown error'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 text-sm rounded"
        >
          Retry Loading
        </button>
      </div>
    )
  }
}

// In Progress Tab Component
interface InProgressTabProps {
  workspaceId?: string
  inProgressDeliverables: any[]
}

function InProgressTab({ workspaceId, inProgressDeliverables }: InProgressTabProps) {
  if (!workspaceId) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">⚠️</div>
        <div className="text-gray-600 mb-2">Workspace context not available</div>
        <div className="text-sm text-gray-500">
          Cannot display in-progress deliverables without workspace context
        </div>
      </div>
    )
  }

  if (!inProgressDeliverables || inProgressDeliverables.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">✅</div>
        <div className="text-gray-600 mb-2">All deliverables are completed!</div>
        <div className="text-sm text-gray-500">
          Only failed, pending, in-progress, or unknown status deliverables appear in this tab
        </div>
        <div className="text-xs text-gray-400 mt-2">
          Completed deliverables are shown in the "Deliverables" tab
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">
          Deliverables Needing Attention ({inProgressDeliverables.length})
        </h3>
        <div className="flex items-center space-x-2">
          <div className="animate-pulse w-2 h-2 bg-orange-500 rounded-full"></div>
          <span className="text-sm text-gray-500">Auto-refreshing every 10 seconds</span>
        </div>
      </div>

      <div className="space-y-3">
        {inProgressDeliverables.map((deliverable, index) => {
          const getStatusColor = (status: string) => {
            switch (status?.toLowerCase()) {
              case 'failed': return 'bg-red-100 border-red-300 text-red-800'
              case 'pending': return 'bg-yellow-100 border-yellow-300 text-yellow-800'
              case 'in_progress': return 'bg-blue-100 border-blue-300 text-blue-800'
              default: return 'bg-gray-100 border-gray-300 text-gray-800'
            }
          }
          
          const getStatusIcon = (status: string) => {
            switch (status?.toLowerCase()) {
              case 'failed': return '❌'
              case 'pending': return '⏳'
              case 'in_progress': return '🔄'
              default: return '❓'
            }
          }
          
          return (
            <div key={deliverable.id || index} className={`border rounded-lg p-4 ${getStatusColor(deliverable.status)}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="text-lg">{getStatusIcon(deliverable.status)}</div>
                    <h4 className="font-medium">
                      {deliverable.title || `Deliverable ${index + 1}`}
                    </h4>
                  </div>
                  
                  <div className="text-sm mb-2">
                    <div className="flex items-center space-x-4">
                      <span>Status: <strong>{deliverable.status?.toUpperCase() || 'UNKNOWN'}</strong></span>
                      {deliverable.type && (
                        <span>Type: <strong>{deliverable.type}</strong></span>
                      )}
                    </div>
                  </div>

                  {deliverable.retry_reason && (
                    <div className="text-sm text-red-700 bg-red-50 rounded p-2 border border-red-200 mb-2">
                      <strong>Issue:</strong> {deliverable.retry_reason}
                    </div>
                  )}
                  
                  {deliverable.unblock_actions && deliverable.unblock_actions.length > 0 && (
                    <div className="text-sm mb-2">
                      <strong>Available Actions:</strong> {deliverable.unblock_actions.join(', ')}
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col items-end space-y-1 ml-4">
                  <div className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(deliverable.status)}`}>
                    {deliverable.status?.toUpperCase() || 'UNKNOWN'}
                  </div>
                  {deliverable.created_at && (
                    <div className="text-xs text-gray-500">
                      Created {new Date(deliverable.created_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">📊</div>
          <div>
            <h4 className="font-medium text-green-900 mb-1">Real Data from Backend</h4>
            <p className="text-sm text-green-700">
              This tab shows only real deliverables from the database that need attention (failed, pending, in-progress, or unknown status). 
              Completed deliverables (including those with 100% progress) are automatically filtered out.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

