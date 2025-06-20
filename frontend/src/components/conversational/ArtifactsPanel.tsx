'use client'

import React, { useState } from 'react'
import { DeliverableArtifact, TeamActivity, Chat } from './types'
import TeamThinkingStream from './TeamThinkingStream'
import ArtifactViewer from './ArtifactViewer'
import { DocumentsSection } from './DocumentsSection'

interface ArtifactsPanelProps {
  artifacts: DeliverableArtifact[]
  teamActivities: TeamActivity[]
  activeChat: Chat | null
  workspaceId: string
  collapsed: boolean
  onToggleCollapse: () => void
  onSendMessage?: (message: string) => Promise<void>
}

export default function ArtifactsPanel({
  artifacts,
  teamActivities,
  activeChat,
  workspaceId,
  collapsed,
  onToggleCollapse,
  onSendMessage
}: ArtifactsPanelProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<DeliverableArtifact | null>(null)
  const [activeTab, setActiveTab] = useState<'thinking' | 'artifacts' | 'documents' | 'viewer'>('thinking')

  // Auto-switch to artifacts when new ones arrive
  React.useEffect(() => {
    if (artifacts.length > 0 && activeTab === 'thinking') {
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
              <span className="text-sm">
                {artifact.type === 'deliverable' ? '📦' : 
                 artifact.type === 'progress' ? '📊' : 
                 artifact.type === 'team_status' ? '👥' : 
                 artifact.type === 'feedback' ? '💬' : '⚙️'}
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

        {/* Tabs */}
        <div className="flex space-x-1 mt-3">
          <TabButton
            active={activeTab === 'thinking'}
            onClick={() => setActiveTab('thinking')}
            icon="🧠"
            label="Thinking"
            count={teamActivities.length}
          />
          <TabButton
            active={activeTab === 'artifacts'}
            onClick={() => setActiveTab('artifacts')}
            icon="📋"
            label="Results"
            count={artifacts.length}
          />
          <TabButton
            active={activeTab === 'documents'}
            onClick={() => setActiveTab('documents')}
            icon="📁"
            label="Docs"
          />
          {selectedArtifact && (
            <TabButton
              active={activeTab === 'viewer'}
              onClick={() => setActiveTab('viewer')}
              icon="👁️"
              label="View"
            />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'thinking' && (
          <TeamThinkingStream activities={teamActivities} />
        )}

        {activeTab === 'artifacts' && (
          <ArtifactsList
            artifacts={artifacts}
            onSelectArtifact={(artifact) => {
              setSelectedArtifact(artifact)
              setActiveTab('viewer')
            }}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsSection 
            workspaceId={workspaceId}
            onSendMessage={onSendMessage || (async () => {})}
          />
        )}

        {activeTab === 'viewer' && selectedArtifact && (
          <ArtifactViewer
            artifact={selectedArtifact}
            workspaceId={workspaceId}
            onClose={() => {
              setSelectedArtifact(null)
              setActiveTab('artifacts')
            }}
            onArtifactUpdate={(updatedArtifact) => {
              setSelectedArtifact(updatedArtifact)
              // TODO: Notify parent component of artifact update
            }}
            onSendMessage={onSendMessage}
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
  icon: string
  label: string
  count?: number
}

function TabButton({ active, onClick, icon, label, count }: TabButtonProps) {
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

function ArtifactsList({ artifacts, onSelectArtifact }: ArtifactsListProps) {
  if (artifacts.length === 0) {
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
      default: return '📄'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div
      onClick={onClick}
      className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm cursor-pointer transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getTypeIcon(artifact.type)}</span>
          <div className="font-medium text-gray-900 text-sm line-clamp-1">
            {artifact.title}
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(artifact.status)}`}>
          {artifact.status.replace('_', ' ')}
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