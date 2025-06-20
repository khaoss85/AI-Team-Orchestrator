'use client'

import React, { useState, useCallback } from 'react'
import { ConversationMessage, Chat, DeliverableArtifact, TeamActivity, WorkspaceContext } from './types'
import ChatSidebar from './ChatSidebar'
import ConversationPanel from './ConversationPanel'
import ArtifactsPanel from './ArtifactsPanel'

interface ConversationalWorkspaceProps {
  workspaceId: string
  workspaceContext: any
  chats: Chat[]
  activeChat: Chat | null
  messages: ConversationMessage[]
  teamActivities: TeamActivity[]
  artifacts: DeliverableArtifact[]
  thinkingSteps: any[]
  suggestedActions: any[]
  artifactsPanelCollapsed: boolean
  sendingMessage: boolean
  onSetActiveChat: (chat: Chat) => void
  onSendMessage: (message: string) => Promise<void>
  onCreateDynamicChat: (objective: string) => Promise<void>
  onArchiveChat: (chatId: string) => Promise<void>
  onToggleArtifactsPanel: () => void
  onRefreshData: () => Promise<void>
}

export default function ConversationalWorkspace({
  workspaceId,
  workspaceContext,
  chats,
  activeChat,
  messages,
  teamActivities,
  artifacts,
  thinkingSteps,
  suggestedActions,
  artifactsPanelCollapsed,
  sendingMessage,
  onSetActiveChat,
  onSendMessage,
  onCreateDynamicChat,
  onArchiveChat,
  onToggleArtifactsPanel,
  onRefreshData
}: ConversationalWorkspaceProps) {
  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [artifactsPanelWidth, setArtifactsPanelWidth] = useState(() => {
    // Load saved width from localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('conversational-artifacts-width')
      return saved ? parseInt(saved) : 384
    }
    return 384
  })
  const [isResizing, setIsResizing] = useState(false)

  // Resizing handlers
  const startResize = useCallback((e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }, [])

  const stopResize = useCallback(() => {
    setIsResizing(false)
  }, [])

  const resize = useCallback((e: MouseEvent) => {
    if (isResizing) {
      const newWidth = window.innerWidth - e.clientX
      const minWidth = 300 // Minimum width
      const maxWidth = window.innerWidth * 0.6 // Maximum 60% of screen
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setArtifactsPanelWidth(newWidth)
        // Save to localStorage
        localStorage.setItem('conversational-artifacts-width', newWidth.toString())
      }
    }
  }, [isResizing])

  // Global mouse events for resizing
  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', resize)
      document.addEventListener('mouseup', stopResize)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'col-resize'
    } else {
      document.removeEventListener('mousemove', resize)
      document.removeEventListener('mouseup', stopResize)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }

    return () => {
      document.removeEventListener('mousemove', resize)
      document.removeEventListener('mouseup', stopResize)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [isResizing, resize, stopResize])

  return (
    <div className="flex h-full w-full bg-gray-50">
      {/* CHAT SIDEBAR - 20% */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-80'} transition-all duration-200 bg-white border-r`}>
        <ChatSidebar
          chats={chats}
          activeChat={activeChat}
          workspaceContext={workspaceContext}
          collapsed={sidebarCollapsed}
          onChatSelect={onSetActiveChat}
          onCreateChat={onCreateDynamicChat}
          onArchiveChat={onArchiveChat}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* CONVERSATION PANEL - Dynamic width */}
      <div className="flex-1 flex flex-col">
        <ConversationPanel
          activeChat={activeChat}
          messages={messages}
          teamActivities={teamActivities}
          thinkingSteps={thinkingSteps}
          suggestedActions={suggestedActions}
          onSendMessage={onSendMessage}
          loading={sendingMessage}
          workspaceId={workspaceId}
        />
      </div>

      {/* RESIZE HANDLE */}
      {!artifactsPanelCollapsed && (
        <div
          className={`w-2 bg-gray-200 hover:bg-blue-400 cursor-col-resize transition-all duration-150 relative group ${
            isResizing ? 'bg-blue-500 w-1' : ''
          }`}
          onMouseDown={startResize}
        >
          {/* Visual indicator dots */}
          <div className="absolute inset-y-0 left-0 w-full flex items-center justify-center">
            <div className="flex flex-col space-y-1 opacity-60 group-hover:opacity-100 transition-opacity">
              <div className="w-0.5 h-0.5 bg-gray-500 rounded-full" />
              <div className="w-0.5 h-0.5 bg-gray-500 rounded-full" />
              <div className="w-0.5 h-0.5 bg-gray-500 rounded-full" />
              <div className="w-0.5 h-0.5 bg-gray-500 rounded-full" />
              <div className="w-0.5 h-0.5 bg-gray-500 rounded-full" />
            </div>
          </div>
          
          {/* Tooltip */}
          <div className="absolute top-4 left-3 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            <div className="bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
              Drag to resize artifacts panel
            </div>
          </div>
        </div>
      )}

      {/* ARTIFACTS PANEL - Resizable */}
      <div 
        className={`${artifactsPanelCollapsed ? 'w-16' : ''} transition-all duration-200 bg-white border-l`}
        style={{ 
          width: artifactsPanelCollapsed ? '64px' : `${artifactsPanelWidth}px`,
          minWidth: artifactsPanelCollapsed ? '64px' : '300px',
          maxWidth: '60vw'
        }}
      >
        <ArtifactsPanel
          artifacts={artifacts}
          teamActivities={teamActivities}
          activeChat={activeChat}
          workspaceId={workspaceId}
          collapsed={artifactsPanelCollapsed}
          onToggleCollapse={onToggleArtifactsPanel}
          onSendMessage={onSendMessage}
        />
      </div>
    </div>
  )
}

// Export for use in page
export { ConversationalWorkspace }