'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Chat, WorkspaceContext } from './types'

interface ChatSidebarProps {
  chats: Chat[]
  activeChat: Chat | null
  workspaceContext: WorkspaceContext
  collapsed: boolean
  goalsLoading?: boolean
  goalsError?: string | null
  onChatSelect: (chat: Chat) => void
  onCreateChat: (objective: string) => Promise<void>
  onArchiveChat: (chatId: string) => Promise<void>
  onReactivateChat?: (chatId: string) => Promise<void>
  onRenameChat?: (chatId: string, newName: string) => Promise<void>
  onToggleCollapse: () => void
}

// Hook for feedback count
function useFeedbackCount(workspaceId: string) {
  const [pendingCount, setPendingCount] = useState(0)
  const [urgentCount, setUrgentCount] = useState(0)

  useEffect(() => {
    const fetchPendingCount = async () => {
      try {
        const response = await fetch(`http://localhost:8000/human-feedback/pending?workspace_id=${workspaceId}`)
        if (response.ok) {
          const data = await response.json()
          const requests = data || []
          setPendingCount(requests.length)
          
          const urgent = requests.filter((req: any) => 
            req.priority === 'critical' || req.priority === 'high'
          ).length
          setUrgentCount(urgent)
        }
      } catch (error) {
        console.error('Error fetching pending feedback count:', error)
      }
    }

    fetchPendingCount()
    const interval = setInterval(fetchPendingCount, 30000)
    return () => clearInterval(interval)
  }, [workspaceId])

  return { pendingCount, urgentCount }
}

export default function ChatSidebar({
  chats,
  activeChat,
  workspaceContext,
  collapsed,
  goalsLoading = false,
  goalsError = null,
  onChatSelect,
  onCreateChat,
  onArchiveChat,
  onReactivateChat,
  onRenameChat,
  onToggleCollapse
}: ChatSidebarProps) {
  const router = useRouter()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newObjective, setNewObjective] = useState('')
  const { pendingCount, urgentCount } = useFeedbackCount(workspaceContext.id)

  // Separate fixed and dynamic chats
  const fixedChats = chats.filter(chat => chat.type === 'fixed')
  // Debug: Log fixed chats to see if Knowledge Base is present
  console.log('ChatSidebar - Fixed Chats:', fixedChats.map(c => ({ id: c.id, title: c.title, systemType: c.systemType })))
  console.log('ChatSidebar - Knowledge Base chat present?', fixedChats.some(c => c.id === 'knowledge-base'))
  
  // Show ALL dynamic chats (active, completed, and in_progress) - not just active ones
  const activeObjectives = chats.filter(chat => chat.type === 'dynamic' && chat.status !== 'archived')
  const archivedChats = chats.filter(chat => chat.status === 'archived')

  const handleCreateChat = async () => {
    if (newObjective.trim()) {
      await onCreateChat(newObjective.trim())
      setNewObjective('')
      setShowCreateModal(false)
    }
  }

  // Direct chat selection with URL update through router
  const handleChatSelect = (chat: Chat) => {
    console.log('ChatSidebar: Selecting chat:', chat.id)
    
    // Update state
    onChatSelect(chat)
    
    // Update URL to match the selected chat
    if (chat.id.startsWith('goal-')) {
      const goalId = chat.id.replace('goal-', '')
      const params = new URLSearchParams(window.location.search)
      params.set('goalId', goalId)
      // Use replaceState to update URL without triggering navigation
      window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
    } else if (chat.type === 'fixed') {
      const params = new URLSearchParams(window.location.search)
      params.delete('goalId')
      const queryString = params.toString()
      const url = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname
      window.history.replaceState({}, '', url)
    }
  }

  if (collapsed) {
    return (
      <div className="h-full p-2">
        <button
          onClick={onToggleCollapse}
          className="w-full p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          title="Expand sidebar"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        
        {/* Collapsed chat indicators */}
        <div className="mt-4 space-y-2">
          {chats.slice(0, 6).map(chat => (
            <button
              key={chat.id}
              onClick={() => handleChatSelect(chat)}
              className={`w-full h-10 rounded-lg flex items-center justify-center transition-all ${
                activeChat?.id === chat.id 
                  ? 'bg-blue-100 text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
              title={`${chat.icon && chat.type === 'fixed' ? chat.icon + ' ' : ''}${chat.title}`}
            >
              <span className="text-xl">{chat.type === 'fixed' && chat.icon ? chat.icon : '💬'}</span>
              {chat.unreadCount && (
                <div className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></div>
              )}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Link
              href="/projects"
              className="p-1 text-gray-600 hover:bg-gray-100 rounded"
              title="Back to projects list"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-lg font-semibold text-gray-900 truncate">
              {workspaceContext.name}
            </h1>
          </div>
          <button
            onClick={onToggleCollapse}
            className="p-1 text-gray-600 hover:bg-gray-100 rounded"
            title="Collapse sidebar"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>
        
        <div className="text-xs text-gray-500">
          {workspaceContext.domain && `${workspaceContext.domain} • `}
          {workspaceContext.team.length} team members
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {/* Fixed System Chats */}
        <div className="p-3">
          <div className="text-xs font-medium text-gray-500 mb-2 px-1">
            SYSTEM
          </div>
          <div className="space-y-1">
            {fixedChats.map(chat => (
              <ChatItem 
                key={chat.id}
                chat={chat}
                isActive={activeChat?.id === chat.id}
                onClick={() => handleChatSelect(chat)}
                feedbackCount={chat.id === 'feedback-requests' ? pendingCount : undefined}
                urgentCount={chat.id === 'feedback-requests' && urgentCount > 0 ? urgentCount : undefined}
              />
            ))}
          </div>
        </div>

        {/* Objectives */}
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 px-1">
              OBJECTIVES
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-xs text-blue-600 hover:text-blue-700 px-1"
              title="Create new objective"
            >
              + New
            </button>
          </div>
          <div className="space-y-1">
            {goalsLoading ? (
              <div className="flex items-center px-1 py-2 text-xs text-gray-500">
                <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2"></div>
                Loading objectives...
              </div>
            ) : goalsError ? (
              <div className="text-xs text-red-500 px-1 py-2">
                Error: {goalsError}
              </div>
            ) : (
              <>
                {activeObjectives.map(chat => (
                  <ChatItem 
                    key={chat.id}
                    chat={chat}
                    isActive={activeChat?.id === chat.id}
                    onClick={() => handleChatSelect(chat)}
                    onArchive={() => onArchiveChat(chat.id)}
                    onRename={onRenameChat ? (newName) => onRenameChat(chat.id, newName) : undefined}
                  />
                ))}
                {activeObjectives.length === 0 && (
                  <div className="text-xs text-gray-400 px-1 py-2">
                    No active objectives
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Archived */}
        {archivedChats.length > 0 && (
          <div className="p-3">
            <div className="text-xs font-medium text-gray-500 mb-2 px-1">
              ARCHIVED
            </div>
            <div className="space-y-1">
              {archivedChats.slice(0, 3).map(chat => (
                <ChatItem 
                  key={chat.id}
                  chat={chat}
                  isActive={false}
                  onClick={() => handleChatSelect(chat)}
                  isArchived
                  onReactivate={onReactivateChat ? () => onReactivateChat(chat.id) : undefined}
                  onRename={onRenameChat ? (newName) => onRenameChat(chat.id, newName) : undefined}
                />
              ))}
              {archivedChats.length > 3 && (
                <div className="text-xs text-gray-400 px-1 py-1">
                  +{archivedChats.length - 3} more archived
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Objective Modal */}
      {showCreateModal && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-80">
            <h2 className="text-lg font-semibold mb-4">Create New Objective</h2>
            <input
              type="text"
              value={newObjective}
              onChange={(e) => setNewObjective(e.target.value)}
              placeholder="Enter objective description..."
              className="w-full px-3 py-2 border rounded-lg mb-4"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateChat()
                if (e.key === 'Escape') setShowCreateModal(false)
              }}
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateChat}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Chat Item Component
interface ChatItemProps {
  chat: Chat
  isActive: boolean
  onClick: () => void
  onArchive?: () => void
  onReactivate?: () => void
  onRename?: (newName: string) => void
  isArchived?: boolean
  feedbackCount?: number
  urgentCount?: number
}

function ChatItem({ 
  chat, 
  isActive, 
  onClick, 
  onArchive, 
  onReactivate, 
  onRename,
  isArchived = false,
  feedbackCount,
  urgentCount
}: ChatItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState(chat.title)
  const [showActions, setShowActions] = useState(false)

  const handleRename = () => {
    if (onRename && editedTitle.trim() && editedTitle !== chat.title) {
      onRename(editedTitle.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      setEditedTitle(chat.title)
      setIsEditing(false)
    }
  }

  const getStatusColor = () => {
    if (!chat.objective) return ''
    const progress = chat.objective.progress || 0
    if (progress >= 100) return 'bg-green-500'
    if (progress >= 75) return 'bg-blue-500'
    if (progress >= 50) return 'bg-yellow-500'
    if (progress >= 25) return 'bg-orange-500'
    return 'bg-gray-400'
  }

  const getStatusIndicator = () => {
    if (!chat.objective) return null
    const progress = chat.objective.progress || 0
    
    return (
      <div className="flex items-center space-x-1">
        <div className={`w-1.5 h-1.5 rounded-full ${getStatusColor()}`} />
        <span className="text-xs text-gray-500">{Math.round(progress)}%</span>
      </div>
    )
  }

  return (
    <div
      className={`
        relative group px-2 py-1.5 rounded-lg cursor-pointer transition-all
        ${isActive 
          ? 'bg-blue-50 text-blue-700 shadow-sm' 
          : 'hover:bg-gray-50 text-gray-700'
        }
        ${isArchived ? 'opacity-60' : ''}
      `}
      onClick={onClick}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex items-start space-x-2">
        {/* Icon only for system chats (fixed type) */}
        {chat.icon && chat.type === 'fixed' && (
          <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
            <span className="text-base leading-none">{chat.icon}</span>
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              onBlur={handleRename}
              onKeyDown={handleKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="w-full px-1 py-0 text-sm bg-white border rounded"
              autoFocus
            />
          ) : (
            <>
              <div className="text-sm font-medium truncate">
                {chat.title}
              </div>
              {chat.subtitle && (
                <div className="text-xs text-gray-500 truncate">
                  {chat.subtitle}
                </div>
              )}
              {chat.type === 'dynamic' && getStatusIndicator()}
            </>
          )}
        </div>
        
        {/* Action buttons */}
        {showActions && !isEditing && (onArchive || onReactivate || onRename) && (
          <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
            {onRename && !isArchived && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsEditing(true)
                }}
                className="p-0.5 text-gray-400 hover:text-gray-600"
                title="Rename"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            )}
            {onArchive && !isArchived && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onArchive()
                }}
                className="p-0.5 text-gray-400 hover:text-gray-600"
                title="Archive"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </button>
            )}
            {onReactivate && isArchived && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onReactivate()
                }}
                className="p-0.5 text-gray-400 hover:text-gray-600"
                title="Reactivate"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
          </div>
        )}
        
        {/* Feedback count badge */}
        {feedbackCount !== undefined && feedbackCount > 0 && (
          <div className="flex items-center space-x-1">
            {urgentCount && urgentCount > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                {urgentCount}
              </span>
            )}
            <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
              {feedbackCount}
            </span>
          </div>
        )}
        
        {/* Unread indicator */}
        {chat.unreadCount && chat.unreadCount > 0 && (
          <div className="absolute top-1 right-1">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
          </div>
        )}
      </div>
    </div>
  )
}

// Export for use in pages
export { ChatSidebar }