'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
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
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newObjective, setNewObjective] = useState('')
  const { pendingCount, urgentCount } = useFeedbackCount(workspaceContext.id)

  // Separate fixed and dynamic chats
  const fixedChats = chats.filter(chat => chat.type === 'fixed')
  // Show ALL dynamic chats (active, completed, and in_progress) - not just active ones
  const activeObjectives = chats.filter(chat => chat.type === 'dynamic' && chat.status !== 'archived')
  const archivedChats = chats.filter(chat => chat.status === 'archived')
  
  console.log('🎯 [ChatSidebar] chats:', chats.length, 'activeObjectives:', activeObjectives.length, 'archived:', archivedChats.length)

  const handleCreateChat = async () => {
    if (newObjective.trim()) {
      await onCreateChat(newObjective.trim())
      setNewObjective('')
      setShowCreateModal(false)
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
              onClick={() => onChatSelect(chat)}
              className={`w-full h-10 rounded-lg flex items-center justify-center ${
                activeChat?.id === chat.id 
                  ? 'bg-blue-100 text-blue-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
              title={chat.title}
            >
              <span className="text-lg">{chat.icon || '💬'}</span>
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
            📌 SYSTEM
          </div>
          <div className="space-y-1">
            {fixedChats.map(chat => (
              <ChatItem 
                key={chat.id}
                chat={chat}
                isActive={activeChat?.id === chat.id}
                onClick={() => onChatSelect(chat)}
                feedbackCount={chat.id === 'feedback-requests' ? pendingCount : undefined}
                urgentCount={chat.id === 'feedback-requests' && urgentCount > 0 ? urgentCount : undefined}
              />
            ))}
          </div>
        </div>

        {/* Active Objectives */}
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 px-1">
              🎯 OBJECTIVES
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
                Error loading goals: {goalsError}
              </div>
            ) : (
              <>
                {activeObjectives.map(chat => (
                  <ChatItem 
                    key={chat.id}
                    chat={chat}
                    isActive={activeChat?.id === chat.id}
                    onClick={() => onChatSelect(chat)}
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
              🗄️ ARCHIVED
            </div>
            <div className="space-y-1">
              {archivedChats.slice(0, 3).map(chat => (
                <ChatItem 
                  key={chat.id}
                  chat={chat}
                  isActive={false}
                  onClick={() => onChatSelect(chat)}
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
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Objective</h3>
            <textarea
              value={newObjective}
              onChange={(e) => setNewObjective(e.target.value)}
              placeholder="Describe your objective (e.g., 'Create Q1 content strategy for LinkedIn')"
              className="w-full h-24 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              autoFocus
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateChat}
                disabled={!newObjective.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
  isArchived?: boolean
  onClick: () => void
  onArchive?: () => void
  onReactivate?: () => void
  onRename?: (newName: string) => void
  feedbackCount?: number
  urgentCount?: number
}

function ChatItem({ chat, isActive, isArchived, onClick, onArchive, onReactivate, onRename, feedbackCount, urgentCount }: ChatItemProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showRenameModal, setShowRenameModal] = useState(false)
  const [newName, setNewName] = useState(chat.title)

  const handleRename = () => {
    if (newName.trim() && newName !== chat.title && onRename) {
      onRename(newName.trim())
      setShowRenameModal(false)
    }
  }

  return (
    <div className={`
      group relative p-2 rounded-lg cursor-pointer transition-colors
      ${isActive 
        ? 'bg-blue-100 text-blue-900' 
        : isArchived
          ? 'text-gray-400 hover:text-gray-600'
          : 'text-gray-700 hover:bg-gray-100'
      }
    `}>
      <div onClick={onClick} className="flex items-center space-x-2 w-full">
        {/* Goal progress indicator instead of icon */}
        {chat.id.startsWith('goal-') ? (
          <div className="flex-shrink-0 w-3 h-3 rounded-full" title={`Goal ${chat.status || 'unknown'}`}>
            {(() => {
              const progress = chat.objective?.progress || 0
              if (progress >= 100) return <div className="w-3 h-3 bg-green-500 rounded-full" />
              if (progress >= 1) return <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />
              return <div className="w-3 h-3 bg-red-500 rounded-full" />
            })()}
          </div>
        ) : (
          <span className="text-sm flex-shrink-0">
            {chat.icon || (chat.type === 'fixed' ? '📌' : '🎯')}
          </span>
        )}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate flex items-center">
            {chat.title}
            {/* Progress percentage for goals */}
            {chat.id.startsWith('goal-') && chat.objective?.progress !== undefined && (
              <div className="ml-2 text-xs text-gray-500">
                {Math.round(chat.objective.progress)}%
              </div>
            )}
          </div>
          {chat.lastActivity && (
            <div className="text-xs opacity-75 truncate">
              {new Date(chat.lastActivity).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
        </div>
        {/* Show feedback count for feedback-requests chat */}
        {feedbackCount !== undefined && feedbackCount > 0 ? (
          <div className="relative flex-shrink-0">
            <div className={`text-white text-xs rounded-full w-5 h-5 flex items-center justify-center ${
              urgentCount && urgentCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-blue-500'
            }`}>
              {feedbackCount > 99 ? '99+' : feedbackCount}
            </div>
            {/* Urgent indicator dot */}
            {urgentCount && urgentCount > 0 ? (
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-600 rounded-full animate-ping"></div>
            ) : null}
          </div>
        ) : null}
        {/* Regular unread count for other chats */}
        {chat.unreadCount && feedbackCount === undefined && (
          <div className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0">
            {chat.unreadCount > 99 ? '99+' : chat.unreadCount}
          </div>
        )}
      </div>
      
      {/* Options dropdown for goal chats */}
      {(chat.id.startsWith('goal-') || chat.type === 'dynamic') && (
        <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowDropdown(!showDropdown)
            }}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Goal options"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
          
          {/* Dropdown Menu */}
          {showDropdown && (
            <div className="absolute right-0 top-6 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-32">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowRenameModal(true)
                  setShowDropdown(false)
                }}
                className="w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-gray-100"
              >
                ✏️ Rename
              </button>
              
              {isArchived && onReactivate ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onReactivate()
                    setShowDropdown(false)
                  }}
                  className="w-full px-3 py-1.5 text-left text-xs text-green-700 hover:bg-green-50"
                >
                  🔄 Reactivate
                </button>
              ) : (
                onArchive && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onArchive()
                      setShowDropdown(false)
                    }}
                    className="w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-gray-100"
                  >
                    🗄️ Archive
                  </button>
                )
              )}
              
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowDropdown(false)
                }}
                className="w-full px-3 py-1.5 text-left text-xs text-gray-500 hover:bg-gray-100"
              >
                ❌ Cancel
              </button>
            </div>
          )}
        </div>
      )}
      
      {/* Rename Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-4 w-full max-w-sm">
            <h3 className="text-sm font-semibold mb-3">Rename Goal</h3>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Enter new name"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename()
                if (e.key === 'Escape') setShowRenameModal(false)
              }}
            />
            <div className="flex justify-end space-x-2 mt-3">
              <button
                onClick={() => setShowRenameModal(false)}
                className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleRename}
                disabled={!newName.trim() || newName === chat.title}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  )
}