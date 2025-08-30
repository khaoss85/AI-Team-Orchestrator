'use client'

import React, { useState } from 'react'
import { DeliverableArtifact } from './types'
import TeamOverviewArtifact from './TeamOverviewArtifact'
import ConfigurationArtifact from './ConfigurationArtifact'
import FeedbackRequestsArtifact from './FeedbackRequestsArtifact'
import KnowledgeInsightsArtifact from './KnowledgeInsightsArtifact'
import ProjectDescriptionArtifact from './ProjectDescriptionArtifact'
import AvailableToolsArtifact from './AvailableToolsArtifact'
import ObjectiveArtifact from './ObjectiveArtifact'

interface ArtifactViewerProps {
  artifact: DeliverableArtifact
  workspaceId?: string
  activeChat?: {
    id: string
    title: string
    type: 'dynamic' | 'fixed'
    objective?: any
    metadata?: Record<string, any>
  } | null
  onClose: () => void
  onArtifactUpdate?: (updatedArtifact: DeliverableArtifact) => void
  onSendMessage?: (message: string) => void
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onCheckWorkspaceHealth?: () => Promise<any>
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

export default function ArtifactViewer({ 
  artifact, 
  workspaceId,
  activeChat, 
  onClose, 
  onArtifactUpdate,
  onSendMessage,
  workspaceHealthStatus,
  healthLoading,
  onCheckWorkspaceHealth,
  onUnblockWorkspace,
  onResumeAutoGeneration
}: ArtifactViewerProps) {
  const [activeView, setActiveView] = useState<'content' | 'metadata' | 'actions'>('content')

  // Check if this artifact type has a specialized component
  const hasSpecializedComponent = [
    'team_status', 'configuration', 'feedback', 'knowledge', 
    'project_description', 'tools', 'objective'
  ].includes(artifact.type)

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'deliverable': return '📦'
      case 'progress': return '📊'
      case 'team_status': return '👥'
      case 'configuration': return '⚙️'
      case 'feedback': return '💬'
      case 'knowledge': return '💡'
      case 'tools': return '🛠️'
      case 'objective': return '🎯'
      default: return '📄'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-600 bg-green-100'
      case 'in_progress': return 'text-yellow-600 bg-yellow-100'
      case 'completed': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  // For specialized components, render with minimal header
  if (hasSpecializedComponent) {
    return (
      <div className="h-full flex flex-col">
        {/* Minimal Header for specialized components */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getTypeIcon(artifact.type)}</span>
            <span className="text-sm text-gray-600">
              {new Date(artifact.lastUpdated).toLocaleString()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Direct specialized component content */}
        <div className="flex-1 overflow-y-auto">
          <ContentView 
            artifact={artifact} 
            workspaceId={workspaceId}
            activeChat={activeChat}
            onArtifactUpdate={onArtifactUpdate}
            onSendMessage={onSendMessage}
            workspaceHealthStatus={workspaceHealthStatus}
            healthLoading={healthLoading}
            onCheckWorkspaceHealth={onCheckWorkspaceHealth}
            onUnblockWorkspace={onUnblockWorkspace}
            onResumeAutoGeneration={onResumeAutoGeneration}
          />
        </div>
      </div>
    )
  }

  // For generic artifacts, use full header with tabs
  return (
    <div className="h-full flex flex-col">
      {/* Full Header for generic artifacts */}
      <div className="p-4 border-b">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">{getTypeIcon(artifact.type)}</span>
            <div>
              <h3 className="font-semibold text-gray-900 line-clamp-2">
                {artifact.title}
              </h3>
              {artifact.description && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {artifact.description}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex items-center justify-between">
          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(artifact.status)}`}>
            {artifact.status.replace('_', ' ')}
          </span>
          <span className="text-xs text-gray-500">
            {new Date(artifact.lastUpdated).toLocaleString()}
          </span>
        </div>

        {/* View Tabs */}
        <div className="flex space-x-1 mt-3">
          <ViewTab
            active={activeView === 'content'}
            onClick={() => setActiveView('content')}
            label="Content"
            icon="📄"
          />
          <ViewTab
            active={activeView === 'metadata'}
            onClick={() => setActiveView('metadata')}
            label="Details"
            icon="ℹ️"
          />
          <ViewTab
            active={activeView === 'actions'}
            onClick={() => setActiveView('actions')}
            label="Actions"
            icon="⚡"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'content' && (
          <ContentView 
            artifact={artifact} 
            workspaceId={workspaceId}
            activeChat={activeChat}
            onArtifactUpdate={onArtifactUpdate}
            onSendMessage={onSendMessage}
            workspaceHealthStatus={workspaceHealthStatus}
            healthLoading={healthLoading}
            onCheckWorkspaceHealth={onCheckWorkspaceHealth}
            onUnblockWorkspace={onUnblockWorkspace}
            onResumeAutoGeneration={onResumeAutoGeneration}
          />
        )}
        
        {activeView === 'metadata' && (
          <MetadataView artifact={artifact} />
        )}
        
        {activeView === 'actions' && (
          <ActionsView artifact={artifact} />
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
        flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
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

// Content View Component
interface ContentViewProps {
  artifact: DeliverableArtifact
  workspaceId?: string
  activeChat?: {
    id: string
    title: string
    type: 'dynamic' | 'fixed'
    objective?: any
    metadata?: Record<string, any>
  } | null
  onArtifactUpdate?: (updatedArtifact: DeliverableArtifact) => void
  onSendMessage?: (message: string) => void
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onCheckWorkspaceHealth?: () => Promise<any>
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

function ContentView({ 
  artifact, 
  workspaceId, 
  onArtifactUpdate, 
  onSendMessage,
  workspaceHealthStatus,
  healthLoading,
  onCheckWorkspaceHealth,
  onUnblockWorkspace,
  onResumeAutoGeneration,
  activeChat
}: ContentViewProps) {
  // Check if this artifact type has a specialized component - if so, render without additional wrapper
  const hasSpecializedComponent = [
    'team_status', 'configuration', 'feedback', 'knowledge', 
    'project_description', 'tools', 'objective'
  ].includes(artifact.type)
  
  // Use specialized components for specific artifact types
  if (artifact.type === 'team_status' && workspaceId) {
    // Extract team data and handoffs from artifact content
    const teamData = Array.isArray(artifact.content) ? artifact.content : artifact.content?.agents || []
    const handoffsData = artifact.content?.handoffs || []
    
    return (
      <TeamOverviewArtifact 
        team={teamData}
        handoffs={handoffsData}
        workspaceId={workspaceId}
        onTeamUpdate={(updatedTeam) => {
          if (onArtifactUpdate) {
            onArtifactUpdate({
              ...artifact,
              content: {
                ...artifact.content,
                agents: updatedTeam
              },
              lastUpdated: new Date().toISOString()
            })
          }
        }}
      />
    )
  }

  if (artifact.type === 'configuration' && workspaceId) {
    return (
      <ConfigurationArtifact
        configuration={artifact.content}
        workspaceId={workspaceId}
        onConfigUpdate={(update) => {
          if (update.action === 'send_message' && onSendMessage) {
            onSendMessage(update.message)
          } else if (onArtifactUpdate) {
            onArtifactUpdate({
              ...artifact,
              content: update,
              lastUpdated: new Date().toISOString()
            })
          }
        }}
        workspaceHealthStatus={workspaceHealthStatus}
        healthLoading={healthLoading}
        onUnblockWorkspace={onUnblockWorkspace}
        onCheckWorkspaceHealth={onCheckWorkspaceHealth}
        onResumeAutoGeneration={onResumeAutoGeneration}
      />
    )
  }

  if (artifact.type === 'feedback' && workspaceId) {
    return (
      <FeedbackRequestsArtifact
        feedbackData={artifact.content}
        workspaceId={workspaceId}
        onFeedbackUpdate={(updatedFeedback) => {
          if (onArtifactUpdate) {
            onArtifactUpdate({
              ...artifact,
              content: updatedFeedback,
              lastUpdated: new Date().toISOString()
            })
          }
        }}
      />
    )
  }

  if (artifact.type === 'knowledge' && workspaceId) {
    return (
      <KnowledgeInsightsArtifact
        knowledgeData={artifact.content}
        workspaceId={workspaceId}
        onInsightAction={(action, insight) => {
          console.log('Knowledge insight action:', action, insight)
          // Handle insight actions (apply learning, find similar, etc.)
        }}
      />
    )
  }

  if (artifact.type === 'project_description' && workspaceId) {
    // Extract project data from artifact metadata or content
    const projectData = artifact.content?.metadata?.project_data || artifact.content?.project_data || {}
    const content = artifact.content?.content || artifact.content || ''
    
    return (
      <ProjectDescriptionArtifact
        projectData={projectData}
        content={content}
        workspaceId={workspaceId}
      />
    )
  }

  if (artifact.type === 'tools' && workspaceId) {
    console.log('🛠️ [ArtifactViewer] Tools artifact content:', artifact.content)
    console.log('🛠️ [ArtifactViewer] Full artifact:', artifact)
    return (
      <AvailableToolsArtifact
        toolsData={artifact.content}
        workspaceId={workspaceId}
        onToolExecute={(toolName, parameters) => {
          console.log('🔧 Tool execution requested:', toolName, parameters)
          
          // Format tool execution as a message
          const message = parameters && Object.keys(parameters).length > 0
            ? `Execute ${toolName} with: ${Object.entries(parameters).map(([k, v]) => `${k}="${v}"`).join(', ')}`
            : `Execute ${toolName}`
          
          console.log('📤 Sending tool execution message:', message)
          
          // Send the tool execution as a chat message
          if (onSendMessage) {
            onSendMessage(message)
          } else {
            console.warn('⚠️ No onSendMessage handler available')
          }
        }}
      />
    )
  }

  if (artifact.type === 'objective') {
    console.log('🎯 [ArtifactViewer] Rendering ObjectiveArtifact with workspaceId:', workspaceId, 'activeChat:', activeChat ? activeChat.id : 'null/undefined')
    if (!workspaceId) {
      console.warn('🎯 [ArtifactViewer] WorkspaceId is undefined for objective artifact')
    }
    return (
      <ObjectiveArtifact
        objectiveData={artifact.content}
        workspaceId={workspaceId}
        activeChat={activeChat}
        title={artifact.title}
      />
    )
  }

  // Debug logging for deliverable content
  if (artifact.type === 'deliverable') {
    console.log('🔍 [DEBUG] Deliverable artifact:', artifact)
    console.log('🔍 [DEBUG] Content type:', typeof artifact.content)
    console.log('🔍 [DEBUG] Content length:', artifact.content ? (typeof artifact.content === 'string' ? artifact.content.length : JSON.stringify(artifact.content).length) : 0)
  }

  // Fallback to generic content view
  if (!artifact.content) {
    return (
      <div className="p-8 text-center text-gray-500">
        <div className="text-3xl mb-2">📭</div>
        <div>No content available</div>
        {artifact.type === 'deliverable' && (
          <div className="mt-2 text-xs text-red-500">
            Debug: Expected deliverable content but found none
          </div>
        )}
      </div>
    )
  }

  // Handle different content types
  const renderContent = () => {
    if (typeof artifact.content === 'string') {
      console.log('🔍 [DEBUG] Rendering string content for deliverable:', artifact.content.substring(0, 100) + '...')
      return (
        <div className="prose prose-sm max-w-none">
          {artifact.type === 'deliverable' && (
            <div className="mb-2 text-xs text-green-600 bg-green-50 p-2 rounded">
              ✅ Deliverable content found: {artifact.content.length} characters
            </div>
          )}
          <pre className="whitespace-pre-wrap text-sm text-gray-900">
            {artifact.content}
          </pre>
        </div>
      )
    }

    if (Array.isArray(artifact.content)) {
      return (
        <div className="space-y-2">
          {artifact.content.map((item, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-lg">
              {typeof item === 'string' ? item : JSON.stringify(item, null, 2)}
            </div>
          ))}
        </div>
      )
    }

    // Object content
    return (
      <div className="space-y-4">
        {Object.entries(artifact.content).map(([key, value]) => (
          <div key={key}>
            <h4 className="font-medium text-gray-900 mb-2 capitalize">
              {key.replace('_', ' ')}
            </h4>
            <div className="p-3 bg-gray-50 rounded-lg">
              {typeof value === 'string' ? (
                <div className="whitespace-pre-wrap text-sm">{value}</div>
              ) : (
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(value, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="p-4">
      {renderContent()}
    </div>
  )
}

// Metadata View Component
interface MetadataViewProps {
  artifact: DeliverableArtifact
}

function MetadataView({ artifact }: MetadataViewProps) {
  const metadata = artifact.metadata || {}

  return (
    <div className="p-4 space-y-4">
      <div>
        <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Type:</span>
            <span className="font-medium">{artifact.type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Status:</span>
            <span className="font-medium capitalize">{artifact.status}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Last Updated:</span>
            <span className="font-medium">
              {new Date(artifact.lastUpdated).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {Object.keys(metadata).length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Additional Metadata</h4>
          <div className="space-y-2">
            {Object.entries(metadata).map(([key, value]) => (
              <div key={key} className="p-3 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-700 mb-1 capitalize">
                  {key.replace('_', ' ')}
                </div>
                <div className="text-sm text-gray-600">
                  {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Actions View Component
interface ActionsViewProps {
  artifact: DeliverableArtifact
}

function ActionsView({ artifact }: ActionsViewProps) {
  const handleExport = () => {
    const dataStr = JSON.stringify(artifact, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${artifact.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleCopyContent = async () => {
    try {
      const content = typeof artifact.content === 'string' 
        ? artifact.content 
        : JSON.stringify(artifact.content, null, 2)
      await navigator.clipboard.writeText(content)
    } catch (error) {
      console.error('Failed to copy content:', error)
    }
  }

  return (
    <div className="p-4 space-y-3">
      <div className="text-sm font-medium text-gray-900 mb-3">
        Available Actions
      </div>

      <button
        onClick={handleCopyContent}
        className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">📋</span>
          <div>
            <div className="text-sm font-medium text-gray-900">Copy Content</div>
            <div className="text-xs text-gray-600">Copy artifact content to clipboard</div>
          </div>
        </div>
      </button>

      <button
        onClick={handleExport}
        className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">💾</span>
          <div>
            <div className="text-sm font-medium text-gray-900">Export as JSON</div>
            <div className="text-xs text-gray-600">Download complete artifact data</div>
          </div>
        </div>
      </button>

      <button
        disabled
        className="w-full p-3 text-left border border-gray-200 rounded-lg opacity-50"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">🔄</span>
          <div>
            <div className="text-sm font-medium text-gray-900">Request Update</div>
            <div className="text-xs text-gray-600">Ask team to refine this artifact</div>
          </div>
        </div>
      </button>

      <button
        disabled
        className="w-full p-3 text-left border border-gray-200 rounded-lg opacity-50"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">📤</span>
          <div>
            <div className="text-sm font-medium text-gray-900">Share</div>
            <div className="text-xs text-gray-600">Generate shareable link</div>
          </div>
        </div>
      </button>
    </div>
  )
}