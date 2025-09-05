'use client'

import React, { useState, useEffect } from 'react'
import { DeliverableArtifact, TeamActivity, Chat } from './types'
import TeamThinkingStream from './TeamThinkingStream'
import ArtifactViewer from './ArtifactViewer'
import { DocumentsSection } from './DocumentsSection'
import AuthenticThinkingViewer from './AuthenticThinkingViewer'
import { validateUniqueIds } from '../../utils/uniqueId'
import BudgetCardV2 from './BudgetCardV2'

interface ArtifactsPanelProps {
  artifacts: DeliverableArtifact[]
  teamActivities: TeamActivity[]
  activeChat: Chat | null
  workspaceId: string
  collapsed: boolean
  onToggleCollapse: () => void
  onSendMessage?: (message: string) => Promise<void>
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onCheckWorkspaceHealth?: () => Promise<any>
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

export default function ArtifactsPanel({
  artifacts,
  teamActivities,
  activeChat,
  workspaceId,
  collapsed,
  onToggleCollapse,
  onSendMessage,
  workspaceHealthStatus,
  healthLoading,
  onCheckWorkspaceHealth,
  onUnblockWorkspace,
  onResumeAutoGeneration
}: ArtifactsPanelProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<DeliverableArtifact | null>(null)
  const [activeTab, setActiveTab] = useState<'artifacts' | 'viewer' | 'documents'>('artifacts')
  
  // Validate unique IDs in development mode
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && artifacts.length > 0) {
      const validation = validateUniqueIds(artifacts)
      if (!validation.isValid) {
        console.error('🚨 [ArtifactsPanel] Duplicate artifact IDs detected:', validation.duplicates)
        console.error('🚨 [ArtifactsPanel] Full artifacts list:', artifacts.map(a => ({
          id: a.id,
          type: a.type,
          title: a.title
        })))
      }
    }
  }, [artifacts])
  
  // Show documents tab when Knowledge Base chat is active
  const showDocumentsTab = activeChat?.id === 'knowledge-base'

  // Auto-switch to artifacts when new ones arrive
  React.useEffect(() => {
    if (artifacts.length > 0) {
      setActiveTab('artifacts')
    }
  }, [artifacts.length])

  if (collapsed) {
    return (
      <div className="h-full p-2 bg-white">
        <button
          onClick={onToggleCollapse}
          className="w-full p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          title="Expand artifacts panel"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        
        {/* Collapsed indicators */}
        <div className="mt-4 space-y-2">
          {teamActivities.length > 0 && (
            <div className="w-full h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
            </div>
          )}
          
          {artifacts.slice(0, 3).map((artifact) => (
            <div
              key={artifact.id}
              className="w-full h-8 bg-gray-100 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-200"
              onClick={() => {
                setSelectedArtifact(artifact)
                setActiveTab('viewer')
                onToggleCollapse()
              }}
              title={artifact.title}
            >
              <span className="text-xs text-gray-500">
                •
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Artifacts</h3>
          <button
            onClick={onToggleCollapse}
            className="p-1 text-gray-600 hover:bg-gray-100 rounded"
            title="Collapse panel"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Tabs - Simplified */}
        <div className="flex space-x-1 mt-3">
          <TabButton
            active={activeTab === 'artifacts'}
            onClick={() => setActiveTab('artifacts')}
            label="Results"
            count={artifacts.length}
          />
          {showDocumentsTab && (
            <TabButton
              active={activeTab === 'documents'}
              onClick={() => setActiveTab('documents')}
              label="📚 Documents"
            />
          )}
          {selectedArtifact && (
            <TabButton
              active={activeTab === 'viewer'}
              onClick={() => setActiveTab('viewer')}
              label="View"
            />
          )}
        </div>
      </div>

      {/* Content - Simplified */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'artifacts' && (
          <ArtifactsList
            artifacts={artifacts}
            workspaceId={workspaceId}
            activeChat={activeChat}
            onSelectArtifact={(artifact) => {
              setSelectedArtifact(artifact)
              setActiveTab('viewer')
            }}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsSection workspaceId={workspaceId} />
        )}

        {activeTab === 'viewer' && selectedArtifact && (
          <>
            {console.log('📋 [ArtifactsPanel] Rendering ArtifactViewer with workspaceId:', workspaceId, 'for artifact:', selectedArtifact.type)}
            <ArtifactViewer
              artifact={selectedArtifact}
              workspaceId={workspaceId}
              activeChat={activeChat}
              onClose={() => {
                setSelectedArtifact(null)
                setActiveTab('artifacts')
              }}
            onArtifactUpdate={(updatedArtifact) => {
              setSelectedArtifact(updatedArtifact)
              // Artifact successfully updated
            }}
            onSendMessage={onSendMessage}
            workspaceHealthStatus={workspaceHealthStatus}
            healthLoading={healthLoading}
            onCheckWorkspaceHealth={onCheckWorkspaceHealth}
            onUnblockWorkspace={onUnblockWorkspace}
            onResumeAutoGeneration={onResumeAutoGeneration}
          />
          </>
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
  count?: number
}

function TabButton({ active, onClick, label, count }: TabButtonProps) {
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
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span className={`
          text-xs px-1.5 py-0.5 rounded-full
          ${active ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-700'}
        `}>
          {count}
        </span>
      )}
    </button>
  )
}

// Artifacts List Component
interface ArtifactsListProps {
  artifacts: DeliverableArtifact[]
  onSelectArtifact: (artifact: DeliverableArtifact) => void
}

function ArtifactsList({ artifacts, onSelectArtifact, workspaceId, activeChat }: ArtifactsListProps & { workspaceId?: string, activeChat?: Chat | null }) {
  // Only show budget card when Budget & Usage chat is active
  const showBudgetCard = activeChat?.id === 'budget-usage'
  
  if (artifacts.length === 0 && !showBudgetCard) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">📦</div>
          <div className="text-lg font-medium mb-2">No artifacts yet</div>
          <div className="text-sm">
            Artifacts will appear here as your team completes work
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-3 overflow-y-auto">
      {/* Budget Card only when Budget & Usage chat is active */}
      {showBudgetCard && workspaceId && (
        <BudgetCardV2 workspaceId={workspaceId} />
      )}
      
      {/* Existing artifacts */}
      {artifacts.map((artifact) => (
        <ArtifactCard
          key={artifact.id}
          artifact={artifact}
          onClick={() => onSelectArtifact(artifact)}
        />
      ))}
    </div>
  )
}

// Artifact Card Component
interface ArtifactCardProps {
  artifact: DeliverableArtifact
  onClick: () => void
}

function ArtifactCard({ artifact, onClick }: ArtifactCardProps) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'deliverable': return '📦'
      case 'progress': return '📊'
      case 'team_status': return '👥'
      case 'configuration': return '⚙️'
      case 'feedback': return '💬'
      case 'knowledge': return '💡'
      default: return '📄'
    }
  }
  
  // Debug logging for knowledge artifacts
  React.useEffect(() => {
    if (artifact.type === 'knowledge') {
      console.log('💡 [ArtifactCard] Knowledge artifact rendered:', {
        id: artifact.id,
        title: artifact.title,
        description: artifact.description,
        contentKeys: artifact.content ? Object.keys(artifact.content) : [],
        status: artifact.status
      })
    }
  }, [artifact])

  const getStatusColor = (status: string, progress?: number) => {
    // If progress is 100%, always show as completed regardless of raw status
    if (progress !== undefined && progress >= 100) {
      return 'bg-green-100 text-green-800'
    }
    
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDisplayStatus = (status: string, progress?: number) => {
    // If progress is 100%, always show as completed regardless of raw status
    if (progress !== undefined && progress >= 100) {
      return 'completed'
    }
    
    return status
  }

  const getProgressFromArtifact = (artifact: DeliverableArtifact): number | undefined => {
    // Check for progress in various possible locations
    // 1. Direct progress in metadata
    if (artifact.metadata?.progress !== undefined) {
      return artifact.metadata.progress
    }
    
    // 2. Progress in content if it's an objective type
    if (artifact.type === 'progress' && artifact.content?.progress !== undefined) {
      return artifact.content.progress
    }
    
    // 3. Progress in content.objective (for objective artifacts)
    if (artifact.content?.objective?.progress !== undefined) {
      return artifact.content.objective.progress
    }
    
    // 4. Check if content is objectiveData with progress
    if (artifact.content?.progress !== undefined) {
      return artifact.content.progress
    }
    
    // 5. Check metadata.objectiveData
    if (artifact.metadata?.objectiveData?.progress !== undefined) {
      return artifact.metadata.objectiveData.progress
    }
    
    return undefined
  }

  return (
    <div
      onClick={onClick}
      className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm cursor-pointer transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <div className="font-medium text-gray-900 text-sm line-clamp-1">
            {artifact.title}
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(artifact.status, getProgressFromArtifact(artifact))}`}>
          {getDisplayStatus(artifact.status, getProgressFromArtifact(artifact)).replace('_', ' ')}
        </span>
      </div>

      {artifact.description && (
        <div className="text-sm text-gray-600 line-clamp-2 mb-2">
          {artifact.description}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="capitalize">{artifact.type.replace('_', ' ')}</div>
        <div>{new Date(artifact.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      </div>
    </div>
  )
}