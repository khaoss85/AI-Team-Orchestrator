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
    <div className="p-6">
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
      <div className="">
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
          <DeliverablesTab 
            deliverables={objectiveData.deliverables || []} 
            metadata={objectiveData.metadata}
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
        <div>No additional details available</div>
      </div>
    )
  }

  // Helper function to format field names in a user-friendly way
  const formatFieldName = (key: string): string => {
    const fieldMappings: Record<string, string> = {
      'business_value': 'Business Value',
      'autonomy_level': 'Autonomy Level',
      'autonomy_reason': 'AI Assistance Details',
      'user_confirmed': 'User Confirmed',
      'confidence': 'Confidence Level',
      'available_tools': 'Available Tools',
      'execution_phase': 'Execution Phase',
      'deliverable_type': 'Deliverable Type',
      'human_input_required': 'Human Input Required',
      'acceptance_criteria': 'Acceptance Criteria',
      'estimated_effort': 'Estimated Effort',
      'full_description': 'Full Description',
      'contributes_to_metrics': 'Contributes to Metrics',
      'is_strategic_deliverable': 'Strategic Deliverable',
      'semantic_context': 'Technical Details',
      'base_type': 'Base Type',
      'deliverables': 'Related Deliverables',
      'original_extraction': 'Original Extraction'
    }
    return fieldMappings[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  // Helper function to format values in a user-friendly way
  const formatValue = (value: any): JSX.Element => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">Not specified</span>
    }

    if (typeof value === 'boolean') {
      return (
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
          value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {value ? '✓ Yes' : '✗ No'}
        </span>
      )
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-gray-400 italic">None specified</span>
      }
      return (
        <div className="space-y-1">
          {value.map((item, index) => (
            <div key={index} className="flex items-start space-x-2">
              <span className="text-blue-500 mt-1">•</span>
              <span className="text-sm">{String(item)}</span>
            </div>
          ))}
        </div>
      )
    }

    if (typeof value === 'object') {
      // Don't show complex technical objects to users
      return <span className="text-gray-400 italic">Technical configuration available</span>
    }

    if (typeof value === 'number') {
      if (value >= 0 && value <= 1) {
        return <span className="font-medium">{Math.round(value * 100)}%</span>
      }
      return <span className="font-medium">{value}</span>
    }

    // String values - format nicely
    const stringValue = String(value)
    if (stringValue.length > 200) {
      return (
        <div className="space-y-2">
          <p className="text-sm leading-relaxed">{stringValue}</p>
        </div>
      )
    }

    return <span className="text-sm">{stringValue}</span>
  }

  // Filter out technical fields that users don't need to see
  const userFriendlyFields = Object.entries(metadata).filter(([key, value]) => {
    const hiddenFields = ['semantic_context', 'base_type', 'original_extraction']
    return !hiddenFields.includes(key)
  })

  return (
    <div className="space-y-4">
      {userFriendlyFields.map(([key, value]) => (
        <div key={key} className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">
            {formatFieldName(key)}
          </h4>
          <div className="text-gray-700">
            {formatValue(value)}
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
  metadata?: Record<string, any>
}

function DeliverablesTab({ deliverables, metadata }: DeliverablesTabProps) {
  const [expandedDeliverable, setExpandedDeliverable] = useState<number | null>(null)

  if (!deliverables || deliverables.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <div className="text-3xl mb-2">📦</div>
        <div>No deliverables available yet</div>
        <div className="text-sm mt-2">Deliverables will appear here as tasks are completed</div>
      </div>
    )
  }

  // 🎯 ENHANCED: Check for business value warnings in deliverables
  const hasBusinessValueWarning = deliverables.some((d: any) => 
    d.content?.businessValueWarning || d.content?.type === 'no_business_content'
  )

  const renderDeliverableContent = (content: any) => {
    if (!content) return <div className="text-gray-500 italic">No content available</div>
    
    // 🧠 ENHANCED: Handle thinking-only deliverables
    if (content.type === 'thinking_only' && content.hasThinking) {
      return (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="text-blue-500 text-xl">🧠</div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Strategic Thinking Process</h4>
                <p className="text-sm text-blue-700 mb-3">{content.summary}</p>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-medium">Thinking Tasks:</span> {content.businessMetrics.thinkingTasksFound}
                  </div>
                  <div>
                    <span className="font-medium">Avg Score:</span> {content.businessMetrics.averageThinkingScore.toFixed(1)}
                  </div>
                </div>
                <div className="mt-3 text-xs text-blue-600">
                  This goal was completed through strategic planning and analysis. 
                  View the thinking process below to understand the reasoning.
                </div>
              </div>
            </div>
          </div>
          
          {/* Thinking Steps */}
          <div className="space-y-3">
            <h5 className="font-medium text-gray-800 flex items-center">
              <span className="text-blue-500 mr-2">💭</span>
              Strategic Reasoning Steps
            </h5>
            {content.thinkingTasks?.map((thinkingTask: any, idx: number) => (
              <div key={idx} className="border border-blue-200 rounded-lg p-3 bg-blue-50">
                <div className="flex items-center justify-between mb-2">
                  <h6 className="font-medium text-blue-800 text-sm">{thinkingTask.name}</h6>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                    Thinking Score: {thinkingTask.businessValueScore}
                  </span>
                </div>
                <div className="text-sm text-blue-700">
                  {thinkingTask.result?.summary || 'Strategic analysis completed'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }
    
    // 🚨 ENHANCED: Handle business value warnings
    if (content.businessValueWarning || content.type === 'no_business_content') {
      return (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="text-amber-500 text-xl">⚠️</div>
              <div>
                <h4 className="font-medium text-amber-800 mb-2">Business Value Warning</h4>
                <p className="text-sm text-amber-700 mb-3">{content.summary}</p>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-medium">Total Tasks:</span> {content.totalTasks}
                  </div>
                  <div>
                    <span className="font-medium">Meta-Tasks:</span> {content.metaTasksCount}
                  </div>
                </div>
                <div className="mt-3 text-xs text-amber-600">
                  This goal appears to be numerically complete but lacks substantial business deliverables. 
                  Most tasks created sub-tasks rather than actual content.
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    }
    
    // 🎯 ENHANCED: Show business metrics for real deliverables
    if (content.businessMetrics) {
      return (
        <div className="space-y-4">
          {/* Business Quality Metrics */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-3 flex items-center">
              <span className="text-blue-500 mr-2">📊</span>
              Business Value Metrics
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-600 font-medium">High-Value Tasks:</span> {content.businessMetrics.highValueTasksFound}
              </div>
              <div>
                <span className="text-blue-600 font-medium">Average Score:</span> {content.businessMetrics.averageBusinessScore.toFixed(1)}
              </div>
              <div>
                <span className="text-blue-600 font-medium">Content Types:</span> {content.businessMetrics.contentTypes.join(', ')}
              </div>
              <div>
                <span className="text-blue-600 font-medium">Total Analyzed:</span> {content.businessMetrics.totalTasksAnalyzed}
              </div>
            </div>
          </div>
          
          {/* Actual Business Content */}
          <div className="space-y-3">
            {content.sections?.map((section: any, idx: number) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-gray-800">{section.title}</h5>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      section.businessValueScore >= 70 ? 'bg-green-100 text-green-800' :
                      section.businessValueScore >= 40 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      Score: {section.businessValueScore}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                      {section.contentType}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-700">
                  {renderBusinessContent(section.content)}
                </div>
              </div>
            ))}
          </div>
          
          {/* 🧠 ENHANCED: Show thinking process if available */}
          {content.thinkingProcess && (
            <div className="space-y-3 border-t border-gray-200 pt-4">
              <h5 className="font-medium text-gray-800 flex items-center">
                <span className="text-blue-500 mr-2">🧠</span>
                Strategic Thinking Process
                <span className="ml-2 text-xs text-gray-500">
                  ({content.thinkingProcess.thinkingSteps.length} steps, avg score: {content.thinkingProcess.averageThinkingScore.toFixed(1)})
                </span>
              </h5>
              <div className="grid gap-2">
                {content.thinkingProcess.thinkingSteps.map((step: any, stepIdx: number) => (
                  <div key={stepIdx} className="border border-blue-100 rounded-lg p-3 bg-blue-50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-blue-800 text-sm">{step.title}</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        {step.businessValueScore}
                      </span>
                    </div>
                    <div className="text-xs text-blue-700">
                      {step.reasoning}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )
    }

    if (typeof content === 'string') {
      // Check if content is HTML
      if (content.trim().startsWith('<') && content.includes('</')) {
        return (
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        )
      } else {
        // Regular text content with markdown-style formatting
        const formattedContent = content
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n---\n/g, '<hr class="my-4 border-gray-300">')
          .replace(/\n\n/g, '</p><p>')
          .replace(/^/, '<p>')
          .replace(/$/, '</p>')
        
        return (
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: formattedContent }}
          />
        )
      }
    }

    if (typeof content === 'object') {
      // If it's structured content, try to render it nicely
      if (content.summary || content.sections || content.deliverables) {
        return (
          <div className="space-y-4">
            {content.summary && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Executive Summary</h4>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">{content.summary}</div>
              </div>
            )}
            
            {content.sections && Array.isArray(content.sections) && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Sections</h4>
                <div className="space-y-3">
                  {content.sections.map((section: any, idx: number) => (
                    <div key={idx} className="border-l-2 border-blue-200 pl-4">
                      <h5 className="font-medium text-gray-800">{section.title || `Section ${idx + 1}`}</h5>
                      <div className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                        {section.content || section.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {content.deliverables && Array.isArray(content.deliverables) && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Key Deliverables</h4>
                <ul className="space-y-1">
                  {content.deliverables.map((item: any, idx: number) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start">
                      <span className="text-blue-500 mr-2">•</span>
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
          <div className="bg-gray-50 rounded p-3 text-xs">
            <pre className="whitespace-pre-wrap text-gray-700">
              {JSON.stringify(content, null, 2)}
            </pre>
          </div>
        )
      }
    }

    return <div className="text-gray-500 italic">Content format not supported</div>
  }
  
  // 🎯 ENHANCED: Helper function to render business content with enhanced formatting
  const renderBusinessContent = (content: any) => {
    if (typeof content === 'string') {
      // Check if content is HTML
      if (content.trim().startsWith('<') && content.includes('</')) {
        return (
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        )
      } else {
        // Regular text content with markdown-style formatting
        const formattedContent = content
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n---\n/g, '<hr class="my-4 border-gray-300">')
          .replace(/\n\n/g, '</p><p>')
          .replace(/^/, '<p>')
          .replace(/$/, '</p>')
        
        return (
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: formattedContent }}
          />
        )
      }
    }
    
    return <div className="text-gray-500 italic">Content format not supported</div>
  }

  return (
    <div className="space-y-3">
      {/* 🚨 ENHANCED: Show overall business value warning if any deliverable has issues */}
      {hasBusinessValueWarning && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
          <div className="flex items-center space-x-2 text-sm text-amber-700">
            <span className="text-amber-500">⚠️</span>
            <span className="font-medium">Business Value Alert:</span>
            <span>Some deliverables may lack substantial business content</span>
          </div>
        </div>
      )}
      
      {/* 🔒 COMPLETION GUARANTEE: Show completion guarantee notice */}
      {metadata?.completion_guaranteed && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <div className="flex items-center space-x-2 text-sm text-blue-700">
            <span className="text-blue-500">🔒</span>
            <span className="font-medium">Completion Guarantee:</span>
            <span>This goal was completed through progress guarantee (90%+ completion threshold)</span>
          </div>
          <div className="text-xs text-blue-600 mt-1">
            Original business score: {metadata?.original_business_score?.toFixed(1) || 'N/A'} • 
            Guaranteed on: {metadata?.completion_guarantee_timestamp ? new Date(metadata.completion_guarantee_timestamp).toLocaleDateString() : 'Unknown'}
          </div>
        </div>
      )}
      
      {deliverables.map((deliverable, index) => {
        const hasWarning = deliverable.content?.businessValueWarning || deliverable.content?.type === 'no_business_content'
        const hasMetrics = deliverable.content?.businessMetrics
        
        return (
        <div key={index} className={`border rounded-lg overflow-hidden ${
          hasWarning ? 'border-amber-300' : 'border-gray-200'
        }`}>
          <div 
            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => setExpandedDeliverable(expandedDeliverable === index ? null : index)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 flex items-center">
                  {hasWarning && <span className="text-amber-500 mr-2">⚠️</span>}
                  {hasMetrics && <span className="text-blue-500 mr-2">📊</span>}
                  {deliverable.title || `Deliverable ${index + 1}`}
                  <svg 
                    className={`ml-2 h-4 w-4 text-gray-400 transition-transform ${
                      expandedDeliverable === index ? 'rotate-180' : ''
                    }`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </h4>
                <p className="text-sm text-gray-600 mt-1">
                  {hasWarning ? 'Warning: Low business value detected' :
                   hasMetrics ? `Business Score: ${deliverable.content.businessMetrics.averageBusinessScore.toFixed(1)} | ${deliverable.content.businessMetrics.highValueTasksFound} high-value tasks` :
                   (deliverable.description || 'Click to view content')}
                </p>
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <span>Created: {new Date(deliverable.created_at || '').toLocaleDateString()}</span>
                  <span>Type: {deliverable.type || 'Unknown'}</span>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs rounded-full ${
                hasWarning ? 'bg-amber-100 text-amber-800' :
                hasMetrics ? 'bg-blue-100 text-blue-800' :
                'bg-green-100 text-green-800'
              }`}>
                {hasWarning ? 'Low Value' :
                 hasMetrics ? 'High Value' :
                 'Completed'}
              </span>
            </div>
          </div>
          
          {/* Expanded Content */}
          {expandedDeliverable === index && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <h5 className="font-medium text-gray-900 mb-3">Document Content</h5>
              <div className="bg-white rounded border p-4 max-h-96 overflow-y-auto">
                {renderDeliverableContent(deliverable.content)}
              </div>
            </div>
          )}
        </div>
        )
      })}
    </div>
  )
}