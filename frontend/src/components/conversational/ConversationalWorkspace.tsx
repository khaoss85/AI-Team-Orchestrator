'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { ConversationMessage, Chat, DeliverableArtifact, TeamActivity, WorkspaceContext, MacroTheme } from './types'
import ChatSidebar from './ChatSidebar'
import ConversationPanel from './ConversationPanel'
import ArtifactsPanel from './ArtifactsPanel'
import { useWorkspaceWebSocket } from '@/hooks/useWorkspaceWebSocket'

interface ConversationalWorkspaceProps {
  workspaceId: string
  goalId?: string
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
  goalsLoading?: boolean
  goalsError?: string | null
  assetsLoading?: boolean
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onSetActiveChat: (chat: Chat) => void
  onSendMessage: (message: string) => Promise<void>
  onCreateDynamicChat: (objective: string) => Promise<void>
  onArchiveChat: (chatId: string) => Promise<void>
  onReactivateChat?: (chatId: string) => Promise<void>
  onRenameChat?: (chatId: string, newName: string) => Promise<void>
  onToggleArtifactsPanel: () => void
  onRefreshData: () => Promise<void>
  onRefreshMessages?: () => Promise<void>
  onCheckWorkspaceHealth?: () => Promise<any>
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
  activeTab?: 'conversation' | 'thinking'
  onTabChange?: (tab: 'conversation' | 'thinking') => void
  // 🎯 NEW: Enhanced navigation handler for SPA goal switching
  onGoalNavigate?: (goalId: string | null) => void
}

export default function ConversationalWorkspace({
  workspaceId,
  goalId,
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
  goalsLoading = false,
  goalsError = null,
  assetsLoading = false,
  workspaceHealthStatus,
  healthLoading,
  onSetActiveChat,
  onSendMessage,
  onCreateDynamicChat,
  onArchiveChat,
  onReactivateChat,
  onRenameChat,
  onToggleArtifactsPanel,
  onRefreshData,
  onRefreshMessages,
  onCheckWorkspaceHealth,
  onUnblockWorkspace,
  onResumeAutoGeneration,
  activeTab,
  onTabChange,
  onGoalNavigate
}: ConversationalWorkspaceProps) {
  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  // 🧠 Real-time thinking state (Claude/o3 style)
  const [realtimeThinkingSteps, setRealtimeThinkingSteps] = useState<any[]>([])
  const [currentGoalDecomposition, setCurrentGoalDecomposition] = useState<any>(null)
  // 🎯 AI Theme state
  const [selectedTheme, setSelectedTheme] = useState<MacroTheme | null>(null)

  // 🎯 FIX: Simple chat selection without URL manipulation to prevent loops
  const handleChatSelect = useCallback((chat: Chat) => {
    console.log('🎯 ConversationalWorkspace: Chat selected:', chat.id, chat.title)
    
    // Only update the active chat state - no URL manipulation here
    // The parent component will handle URL synchronization separately
    onSetActiveChat(chat)
    // Clear theme selection when selecting a regular chat
    setSelectedTheme(null)
  }, [onSetActiveChat])
  
  // 🎨 Handle AI theme selection
  const handleThemeSelect = useCallback((theme: MacroTheme) => {
    console.log('🎨 Theme selected:', theme.name, theme.theme_id)
    setSelectedTheme(theme)
    
    // Create a virtual chat for the theme with proper goal references
    const themeChat: Chat = {
      id: `theme-${theme.theme_id}`,
      type: 'dynamic',
      title: theme.name,
      icon: theme.icon,
      status: 'active',
      objective: {
        description: theme.description,
        progress: theme.statistics.average_progress,
        // 🎯 Include the actual goal IDs for this theme
        goals: theme.goals || []
      }
    }
    onSetActiveChat(themeChat)
  }, [onSetActiveChat])
  
  // 🧠 WebSocket integration for real-time thinking
  const { isConnected, realtimeUpdates } = useWorkspaceWebSocket({
    workspaceId,
    onThinkingStep: (thinkingData) => {
      console.log('🧠 Real-time thinking step received:', thinkingData)
      setRealtimeThinkingSteps(prev => [...prev, thinkingData])
    },
    onGoalDecompositionStart: (goalData) => {
      console.log('🎯 Goal decomposition started:', goalData)
      setCurrentGoalDecomposition({ ...goalData, status: 'in_progress' })
      setRealtimeThinkingSteps([]) // Clear previous thinking steps
    },
    onGoalDecompositionComplete: (decompositionData) => {
      console.log('✅ Goal decomposition completed:', decompositionData)
      setCurrentGoalDecomposition(prev => ({ ...prev, ...decompositionData, status: 'completed' }))
    },
    onGoalProgressUpdate: (progressData) => {
      console.log('🎯 Real-time goal progress update:', progressData)
      // Update the goal progress in the objectives state
      setObjectives(prev => prev.map(objective => 
        objective.id === progressData.goal_id 
          ? { 
              ...objective, 
              progress: progressData.progress || objective.progress,
              quality_score: progressData.quality_score || objective.quality_score,
              asset_completion_rate: progressData.asset_completion_rate || objective.asset_completion_rate
            }
          : objective
      ))
    }
  })
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
          goalsLoading={goalsLoading}
          goalsError={goalsError}
          onChatSelect={handleChatSelect} // 🎯 Use enhanced chat selection handler
          onCreateChat={onCreateDynamicChat}
          onArchiveChat={onArchiveChat}
          onReactivateChat={onReactivateChat}
          onRenameChat={onRenameChat}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onThemeSelect={handleThemeSelect} // 🎨 AI theme selection handler
        />
      </div>

      {/* CONVERSATION PANEL - Dynamic width */}
      <div className="flex-1 flex flex-col">
        <ConversationPanel
          activeChat={activeChat}
          messages={messages}
          teamActivities={teamActivities}
          thinkingSteps={[...thinkingSteps, ...realtimeThinkingSteps]} // 🧠 Merge static + real-time thinking
          suggestedActions={suggestedActions}
          onSendMessage={onSendMessage}
          onRefreshMessages={onRefreshMessages}
          loading={sendingMessage}
          workspaceId={workspaceId}
          goalId={goalId}
          // 🧠 Real-time thinking props
          isWebSocketConnected={isConnected}
          currentGoalDecomposition={currentGoalDecomposition}
          // URL-controlled tab state
          activeTab={activeTab}
          onTabChange={onTabChange}
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
          workspaceHealthStatus={workspaceHealthStatus}
          healthLoading={healthLoading}
          onCheckWorkspaceHealth={onCheckWorkspaceHealth}
          onUnblockWorkspace={onUnblockWorkspace}
          onResumeAutoGeneration={onResumeAutoGeneration}
          selectedTheme={selectedTheme} // 🎨 Pass selected theme for themed display
        />
      </div>
    </div>
  )
}

// Export for use in page
export { ConversationalWorkspace }