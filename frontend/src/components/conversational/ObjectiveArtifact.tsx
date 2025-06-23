'use client'

import React, { useState } from 'react'

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
  const [activeTab, setActiveTab] = useState<'overview' | 'metadata' | 'progress' | 'deliverables'>('overview')

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

  return (
    <div className="">
      {/* Minimal Header - Claude/ChatGPT style */}
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

      {/* Compact Progress Bar */}
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

      {/* Minimal Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <TabButton 
          active={activeTab === 'overview'} 
          onClick={() => setActiveTab('overview')}
          label="Overview"
        />
        <TabButton 
          active={activeTab === 'metadata'} 
          onClick={() => setActiveTab('metadata')}
          label="Details"
        />
        <TabButton 
          active={activeTab === 'progress'} 
          onClick={() => setActiveTab('progress')}
          label="Progress"
        />
        <TabButton 
          active={activeTab === 'deliverables'} 
          onClick={() => setActiveTab('deliverables')}
          label="Deliverables"
        />
      </div>

      {/* Content */}
      <div className="px-4 pb-4">
        {activeTab === 'overview' && (
          <OverviewTab objectiveData={objectiveData} />
        )}
        
        {activeTab === 'metadata' && (
          <MetadataTab metadata={objectiveData.metadata || {}} />
        )}
        
        {activeTab === 'progress' && (
          <ProgressTab objectiveData={objectiveData} />
        )}
        
        {activeTab === 'deliverables' && (
          <DeliverablesTab deliverables={objectiveData.deliverables || []} />
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
}

function OverviewTab({ objectiveData }: OverviewTabProps) {
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

  return (
    <div className="space-y-4">
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
    </div>
  )
}

// Metadata Tab Component
interface MetadataTabProps {
  metadata: Record<string, any>
}

function MetadataTab({ metadata }: MetadataTabProps) {
  if (!metadata || Object.keys(metadata).length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <div className="text-3xl mb-2">🏷️</div>
        <div>No metadata available for this objective</div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600 mb-4">
        Additional metadata and custom properties for this objective:
      </div>
      {Object.entries(metadata).map(([key, value]) => (
        <div key={key} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 capitalize">
                {key.replace('_', ' ')}
              </h4>
              <div className="mt-2 text-sm text-gray-600">
                {typeof value === 'object' ? (
                  <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                ) : (
                  <span>{String(value)}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Progress Tab Component
interface ProgressTabProps {
  objectiveData: ObjectiveData
}

function ProgressTab({ objectiveData }: ProgressTabProps) {
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
          <div className="w-full bg-white rounded-full h-4 shadow-inner">
            <div 
              className={`h-4 rounded-full transition-all duration-500 ${
                isCompleted ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Metrics */}
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

// Deliverables Tab Component
interface DeliverablesTabProps {
  deliverables: any[]
}

function DeliverablesTab({ deliverables }: DeliverablesTabProps) {
  if (!deliverables || deliverables.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <div className="text-3xl mb-2">📦</div>
        <div>No deliverables available yet</div>
        <div className="text-sm mt-2">Deliverables will appear here as tasks are completed</div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {deliverables.map((deliverable, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">
                {deliverable.title || `Deliverable ${index + 1}`}
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                {deliverable.description || 'No description available'}
              </p>
              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                <span>Created: {deliverable.created_at || 'Unknown'}</span>
                <span>Type: {deliverable.type || 'Unknown'}</span>
              </div>
            </div>
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              Completed
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}