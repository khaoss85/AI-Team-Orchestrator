'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import ConversationalWorkspace from '@/components/conversational/ConversationalWorkspace'
import { useConversationalWorkspace } from '@/hooks/useConversationalWorkspace'

export default function ConversationPage() {
  const params = useParams()
  const router = useRouter()
  const workspaceId = params.id as string
  const [artifactsPanelCollapsed, setArtifactsPanelCollapsed] = useState(false)

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
    workspaceHealthStatus,
    healthLoading,
    setActiveChat,
    sendMessage,
    createDynamicChat,
    archiveChat,
    reactivateChat,
    renameChat,
    refreshData,
    refreshMessages,
    checkWorkspaceHealth,
    unblockWorkspace,
    resumeAutoGeneration
  } = useConversationalWorkspace(workspaceId)

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

  return (
    <div className="h-screen w-full">
      <ConversationalWorkspace
        workspaceId={workspaceId}
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
        workspaceHealthStatus={workspaceHealthStatus}
        healthLoading={healthLoading}
        onSetActiveChat={setActiveChat}
        onSendMessage={sendMessage}
        onCreateDynamicChat={createDynamicChat}
        onArchiveChat={archiveChat}
        onReactivateChat={reactivateChat}
        onRenameChat={renameChat}
        onToggleArtifactsPanel={() => setArtifactsPanelCollapsed(!artifactsPanelCollapsed)}
        onRefreshData={refreshData}
        onRefreshMessages={refreshMessages}
        onCheckWorkspaceHealth={checkWorkspaceHealth}
        onUnblockWorkspace={unblockWorkspace}
        onResumeAutoGeneration={resumeAutoGeneration}
      />
    </div>
  )
}