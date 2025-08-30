'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import ConversationalWorkspace from '@/components/conversational/ConversationalWorkspace'
import { useConversationalWorkspace } from '@/hooks/useConversationalWorkspace'

export default function ConversationPage() {
  // Next.js hooks - must be at the top
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Computed values
  const workspaceId = params.id as string
  const goalId = searchParams.get('goalId')
  const tab = searchParams.get('tab') || 'conversation'
  const initialChatId = goalId ? `goal-${goalId}` : undefined
  
  // Local state hooks
  const [artifactsPanelCollapsed, setArtifactsPanelCollapsed] = useState(false)

  // Custom hook - must come after local state
  const {
    chats,
    activeChat,
    messages,
    teamActivities,
    artifacts,
    workspaceContext,
    thinkingSteps,
    suggestedActions,
    loading,
    sendingMessage,
    error,
    goalsLoading,
    goalsError,
    assetsLoading,
    workspaceHealthStatus,
    healthLoading,
    setActiveChat,
    sendMessage,
    createDynamicChat,
    archiveChat,
    reactivateChat,
    renameChat,
    refreshData,
    loadFullAssets,
    refreshMessages,
    checkWorkspaceHealth,
    unblockWorkspace,
    resumeAutoGeneration
  } = useConversationalWorkspace(workspaceId, initialChatId)

  // 🎯 ARCHITECTURAL FIX: State-first, URL-following pattern - eliminates race conditions
  useEffect(() => {
    // SINGLE SOURCE OF TRUTH: Only sync URL to state, never the reverse
    if (goalId && chats.length > 0) {
      const targetChatId = `goal-${goalId}`
      
      // PREVENT RACE CONDITIONS: Check if we're already on the right chat
      if (activeChat?.id !== targetChatId) {
        const targetChat = chats.find(chat => chat.id === targetChatId)
        if (targetChat) {
          console.log('🎯 [URL->State] Single source sync: switching to goal chat:', targetChatId)
          setActiveChat(targetChat)
        } else {
          console.log('⚠️ [URL->State] Goal chat not found, creating placeholder')
          // Don't force switch to general - let the hook handle missing chats
        }
      }
    } else if (!goalId && chats.length > 0 && activeChat?.id?.startsWith('goal-')) {
      // URL has no goal but we're on a goal chat - switch to general
      const generalChat = chats.find(chat => chat.type === 'fixed' && chat.id === 'general')
      if (generalChat && activeChat.id !== 'general') {
        console.log('🎯 [URL->State] Switching to general chat (no goal in URL)')
        setActiveChat(generalChat)
      }
    }
    // CRITICAL: Only depend on URL and chats, never activeChat (prevents loops)
  }, [goalId, chats, setActiveChat])

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <div className="text-gray-600">Loading workspace...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-8">
          <div className="text-red-500 text-6xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Failed to load workspace
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={refreshData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // Simple handlers for navigation
  const handleTabChange = (newTab: 'conversation' | 'thinking') => {
    const params = new URLSearchParams(searchParams.toString())
    if (goalId) params.set('goalId', goalId)
    if (newTab === 'thinking') {
      params.set('tab', 'thinking')
    } else {
      params.delete('tab')
    }
    router.push(`/projects/${workspaceId}/conversation?${params.toString()}`, { scroll: false })
  }

  // 🎯 NAVIGATION: URL-only changes trigger state via useEffect above
  const handleGoalNavigate = (newGoalId: string | null) => {
    console.log('🎯 [Navigation] Goal navigate requested:', newGoalId)
    const params = new URLSearchParams(searchParams.toString())
    if (newGoalId) {
      params.set('goalId', newGoalId)
    } else {
      params.delete('goalId')
    }
    if (tab !== 'conversation') {
      params.set('tab', tab)
    }
    // URL change will trigger useEffect above -> setActiveChat
    router.push(`/projects/${workspaceId}/conversation?${params.toString()}`, { scroll: false })
  }

  return (
    <div className="h-screen w-full">
      <ConversationalWorkspace
        workspaceId={workspaceId}
        goalId={goalId}
        workspaceContext={workspaceContext}
        chats={chats}
        activeChat={activeChat}
        messages={messages}
        teamActivities={teamActivities}
        artifacts={artifacts}
        thinkingSteps={thinkingSteps}
        suggestedActions={suggestedActions}
        artifactsPanelCollapsed={artifactsPanelCollapsed}
        sendingMessage={sendingMessage}
        goalsLoading={goalsLoading}
        goalsError={goalsError}
        assetsLoading={assetsLoading}
        workspaceHealthStatus={workspaceHealthStatus}
        healthLoading={healthLoading}
        activeTab={tab as 'conversation' | 'thinking'}
        onSetActiveChat={setActiveChat}
        onSendMessage={sendMessage}
        onCreateDynamicChat={createDynamicChat}
        onArchiveChat={archiveChat}
        onReactivateChat={reactivateChat}
        onRenameChat={renameChat}
        onToggleArtifactsPanel={() => setArtifactsPanelCollapsed(!artifactsPanelCollapsed)}
        onRefreshData={refreshData}
        onLoadFullAssets={loadFullAssets}
        onRefreshMessages={refreshMessages}
        onCheckWorkspaceHealth={checkWorkspaceHealth}
        onUnblockWorkspace={unblockWorkspace}
        onResumeAutoGeneration={resumeAutoGeneration}
        onTabChange={handleTabChange}
        onGoalNavigate={handleGoalNavigate}
      />
    </div>
  )
}