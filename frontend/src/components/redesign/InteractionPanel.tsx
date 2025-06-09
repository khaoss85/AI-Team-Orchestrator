'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace } from '@/types'

interface Props {
  workspace: Workspace
  onWorkspaceUpdate: (w: Workspace) => void
}

const InteractionPanel: React.FC<Props> = ({ workspace, onWorkspaceUpdate }) => {
  const [starting, setStarting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleStart = async () => {
    try {
      setStarting(true)
      await api.monitoring.startTeam(workspace.id)
      const updated = await api.workspaces.get(workspace.id)
      onWorkspaceUpdate(updated)
    } catch (e) {
      console.error(e)
    } finally {
      setStarting(false)
    }
  }

  const handleDelete = async () => {
    const confirmDelete = window.confirm('Sei sicuro di voler eliminare il progetto?')
    if (!confirmDelete) return
    try {
      setDeleting(true)
      await api.workspaces.delete(workspace.id)
      window.location.href = '/projects'
    } catch (e) {
      console.error(e)
    } finally {
      setDeleting(false)
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim()) return
    try {
      setSending(true)
      // Here you would integrate with your feedback/task creation system
      await api.monitoring.submitDeliverableFeedback(workspace.id, {
        feedback_type: 'modification_request',
        message: message,
        priority: 'medium',
        specific_tasks: []
      })
      setMessage('')
      alert('Richiesta inviata al team AI!')
    } catch (e) {
      console.error(e)
      alert('Errore nell\'invio della richiesta')
    } finally {
      setSending(false)
    }
  }

  const quickSuggestions = [
    "Make the content more video-focused",
    "Add more social media platforms",
    "Focus on B2B instead of B2C",
    "Increase the posting frequency",
    "Make it more casual and friendly",
    "Add seasonal campaigns"
  ]

  const handleQuickSuggestion = (suggestion: string) => {
    setMessage(suggestion)
  }

  return (
    <div className="relative bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-xl shadow-lg border border-indigo-200/50 p-6 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-full -translate-y-16 translate-x-16 blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full translate-y-12 -translate-x-12 blur-2xl"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Talk to AI Team</h3>
              <p className="text-sm text-gray-600">Request changes or ask questions</p>
            </div>
          </div>
          {workspace.status === 'active' && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600 font-medium">Team Active</span>
            </div>
          )}
        </div>

        {/* Quick suggestions */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Quick Suggestions:</label>
          <div className="grid grid-cols-2 gap-2">
            {quickSuggestions.slice(0, 4).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleQuickSuggestion(suggestion)}
                className="text-left p-3 bg-white bg-opacity-60 backdrop-blur-sm border border-indigo-200/50 rounded-lg hover:bg-opacity-80 hover:border-indigo-300 transition-all duration-200 text-sm"
              >
                💡 {suggestion}
              </button>
            ))}
          </div>
        </div>

        {/* Message input */}
        <div className="space-y-3">
          <div className="relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your request here... (e.g., 'Make the calendar more video-focused')"
              className="w-full p-4 bg-white bg-opacity-70 backdrop-blur-sm border border-indigo-200/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              rows={3}
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-400">
              {message.length}/500
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handleSendMessage}
              disabled={sending || !message.trim()}
              className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all duration-200 flex items-center justify-center"
            >
              {sending ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Send Request
                </>
              )}
            </button>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 pt-2 border-t border-indigo-200/50">
          {(workspace.status === 'created' || workspace.status === 'paused' || workspace.status === 'error') && (
            <button 
              onClick={handleStart} 
              disabled={starting} 
              className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 px-4 rounded-lg text-sm hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 font-medium flex items-center justify-center shadow-lg transform hover:scale-105 transition-all duration-200"
            >
              {starting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Starting Team...
                </>
              ) : (
                <>
                  🚀 Start AI Team
                </>
              )}
            </button>
          )}
          
          {workspace.status === 'active' && (
            <button 
              onClick={handleStart} 
              disabled={starting} 
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-lg text-sm hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 font-medium flex items-center justify-center shadow-lg transform hover:scale-105 transition-all duration-200"
            >
              {starting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Restarting...
                </>
              ) : (
                <>
                  ⚡ Restart Team
                </>
              )}
            </button>
          )}
          
          <Link 
            href={`/projects/${workspace.id}/deliverables`} 
            className="flex-1 bg-white bg-opacity-70 backdrop-blur-sm border border-indigo-200/50 text-indigo-700 py-2 px-4 rounded-lg text-sm hover:bg-opacity-90 font-medium text-center transition-all"
          >
            📄 Deliverables
          </Link>
          
          <Link 
            href={`/projects/${workspace.id}/assets`} 
            className="flex-1 bg-white bg-opacity-70 backdrop-blur-sm border border-indigo-200/50 text-indigo-700 py-2 px-4 rounded-lg text-sm hover:bg-opacity-90 font-medium text-center transition-all"
          >
            🎯 Assets
          </Link>

          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-3 py-2 bg-white bg-opacity-70 backdrop-blur-sm border border-indigo-200/50 text-gray-600 rounded-lg text-sm hover:bg-opacity-90 transition-all"
          >
            <svg className={`w-4 h-4 transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Advanced options */}
        {showAdvanced && (
          <div className="mt-4 p-4 bg-white bg-opacity-50 backdrop-blur-sm border border-red-200/50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">⚠️ Advanced Actions</h4>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 disabled:opacity-50 font-medium"
            >
              {deleting ? 'Deleting...' : '🗑️ Delete Project'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default InteractionPanel
