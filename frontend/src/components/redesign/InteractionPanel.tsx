'use client'
import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '@/utils/api'
import type { Workspace } from '@/types'

interface Props {
  workspace: Workspace
  onWorkspaceUpdate: (w: Workspace) => void
  hasFinalDeliverables?: boolean
  finalDeliverablesCount?: number
}

const InteractionPanel: React.FC<Props> = ({ workspace, onWorkspaceUpdate, hasFinalDeliverables, finalDeliverablesCount }) => {
  const [starting, setStarting] = useState(false)
  const [showQuestionModal, setShowQuestionModal] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showIterationModal, setShowIterationModal] = useState(false)
  const [showChangesModal, setShowChangesModal] = useState(false)
  
  // Form states
  const [questionText, setQuestionText] = useState('')
  const [feedbackText, setFeedbackText] = useState('')
  const [iterationText, setIterationText] = useState('')
  const [changesText, setChangesText] = useState('')
  const [changesPriority, setChangesPriority] = useState<'low' | 'medium' | 'high'>('medium')

  // Debug: log workspace status and props
  console.log('InteractionPanel render:', {
    workspaceStatus: workspace.status,
    hasFinalDeliverables,
    finalDeliverablesCount,
    showingCompletedUI: workspace.status === 'completed' || hasFinalDeliverables,
    showChangesModal
  })

  const handleStart = async () => {
    try {
      setStarting(true)
      await api.monitoring.startTeam(workspace.id)
      const updated = await api.workspaces.get(workspace.id)
      onWorkspaceUpdate(updated)
    } catch (e) {
      console.error(e)
      alert('Failed to start team. Please try again.')
    } finally {
      setStarting(false)
    }
  }

  const handleApproveCompletion = async () => {
    try {
      await api.interaction.approveCompletion(workspace.id)
      const updated = await api.workspaces.get(workspace.id)
      onWorkspaceUpdate(updated)
      alert('Project approved successfully!')
    } catch (e) {
      console.error(e)
      alert('Failed to approve completion. Please try again.')
    }
  }

  const handleSendQuestion = async () => {
    try {
      await api.interaction.askQuestion(workspace.id, questionText)
      setQuestionText('')
      setShowQuestionModal(false)
      alert('Question sent to the team!')
    } catch (e) {
      console.error(e)
      alert('Failed to send question. Please try again.')
    }
  }

  const handleSendFeedback = async () => {
    try {
      await api.interaction.provideFeedback(workspace.id, feedbackText)
      setFeedbackText('')
      setShowFeedbackModal(false)
      alert('Feedback sent to the team!')
    } catch (e) {
      console.error(e)
      alert('Failed to send feedback. Please try again.')
    }
  }

  const handleRequestIteration = async () => {
    try {
      await api.interaction.requestIteration(workspace.id, [iterationText])
      setIterationText('')
      setShowIterationModal(false)
      alert('Iteration request sent!')
    } catch (e) {
      console.error(e)
      alert('Failed to request iteration. Please try again.')
    }
  }

  const handleRequestChanges = async () => {
    try {
      console.log('Sending changes request:', { changesText, changesPriority })
      const response = await api.interaction.requestChanges(workspace.id, changesText, changesPriority)
      console.log('Changes request response:', response)
      setChangesText('')
      setShowChangesModal(false)
      alert('Change request sent successfully!')
    } catch (e) {
      console.error('Error requesting changes:', e)
      alert(`Failed to request changes: ${e.message || e}`)
    }
  }

  // Show different UI based on workspace status
  if (workspace.status === 'active') {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">🤖 AI Team Active</h3>
              <p className="text-blue-700 text-sm">
                Your AI team is currently working on deliverables. You can provide feedback or ask questions.
              </p>
            </div>
            <div className="flex items-center text-blue-600">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse mr-2"></div>
              <span className="text-sm font-medium">Working...</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => setShowQuestionModal(true)}
              className="bg-white border border-blue-200 text-blue-700 py-3 px-4 rounded-lg font-medium hover:bg-blue-50 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Ask Questions
            </button>
            
            <button 
              onClick={() => setShowFeedbackModal(true)}
              className="bg-white border border-blue-200 text-blue-700 py-3 px-4 rounded-lg font-medium hover:bg-blue-50 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-1.586l-4.414 4.414z" />
              </svg>
              Give Feedback
            </button>
            
            <button 
              onClick={() => setShowIterationModal(true)}
              className="bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Request Iteration
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show different UI if work is completed but not yet reviewed
  if (workspace.status === 'completed' || hasFinalDeliverables) {
    return (
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200 p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-green-900 mb-2">✅ Work Completed</h3>
            <p className="text-green-700 text-sm">
              Your AI team has produced {finalDeliverablesCount || 'final'} deliverables. Review the results and provide feedback if needed.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button 
              onClick={handleApproveCompletion}
              className="bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Approve Results
            </button>
            
            <button 
              onClick={() => {
                console.log('Request Changes button clicked!')
                setShowChangesModal(true)
              }}
              className="bg-white border border-green-200 text-green-700 py-3 px-4 rounded-lg font-medium hover:bg-green-50 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Request Changes
            </button>
          </div>
        </div>

        {/* Changes Modal - Using Portal */}
        {showChangesModal && createPortal(
          <div 
            className="fixed inset-0 flex items-center justify-center p-4" 
            style={{
              zIndex: 99999, 
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              pointerEvents: 'auto'
            }}
          >
            <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-2xl">
              <h3 className="text-lg font-semibold mb-4">Request Changes</h3>
              <textarea
                value={changesText}
                onChange={(e) => setChangesText(e.target.value)}
                placeholder="Describe specific changes needed for the final deliverables..."
                className="w-full border border-gray-300 rounded-lg p-3 mb-4 resize-none"
                rows={4}
              />
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                <select 
                  value={changesPriority}
                  onChange={(e) => setChangesPriority(e.target.value as 'low' | 'medium' | 'high')}
                  className="w-full border border-gray-300 rounded-lg p-2"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowChangesModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleRequestChanges}
                  disabled={!changesText.trim()}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg disabled:opacity-50 hover:bg-green-700"
                >
                  Submit Changes
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
      <div className="space-y-4">
        {/* Simple header */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Start?</h3>
          <p className="text-gray-600 text-sm">
            Launch your AI team to begin producing deliverables and assets for this project.
          </p>
        </div>

        {/* Start button - the main action */}
        <button 
          onClick={handleStart} 
          disabled={starting} 
          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-4 px-6 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all duration-200 flex items-center justify-center shadow-lg"
        >
          {starting ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Starting AI Team...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              🚀 Start AI Team
            </>
          )}
        </button>

        {/* Status info */}
        <div className="text-xs text-gray-500">
          Status: <span className="capitalize font-medium text-gray-700">{workspace.status}</span>
        </div>
      </div>

      {/* Question Modal */}
      {showQuestionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4" style={{zIndex: 9999}}>
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Ask a Question</h3>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder="What would you like to ask the team?"
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 resize-none"
              rows={4}
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowQuestionModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={handleSendQuestion}
                disabled={!questionText.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
              >
                Send Question
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Provide Feedback</h3>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Share your feedback about the current work..."
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 resize-none"
              rows={4}
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={handleSendFeedback}
                disabled={!feedbackText.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
              >
                Send Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Iteration Modal */}
      {showIterationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Request Iteration</h3>
            <textarea
              value={iterationText}
              onChange={(e) => setIterationText(e.target.value)}
              placeholder="Describe the changes you'd like to see..."
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 resize-none"
              rows={4}
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowIterationModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={handleRequestIteration}
                disabled={!iterationText.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
              >
                Request Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Changes Modal - Using Portal */}
      {showChangesModal && createPortal(
        <div 
          className="fixed inset-0 flex items-center justify-center p-4" 
          style={{
            zIndex: 99999, 
            backgroundColor: 'rgba(0, 0, 0, 0.7)', // Darker overlay for better visibility
            pointerEvents: 'auto'
          }}
        >
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-semibold mb-4">Request Changes</h3>
            <textarea
              value={changesText}
              onChange={(e) => setChangesText(e.target.value)}
              placeholder="Describe specific changes needed for the final deliverables..."
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 resize-none"
              rows={4}
            />
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
              <select 
                value={changesPriority}
                onChange={(e) => setChangesPriority(e.target.value as 'low' | 'medium' | 'high')}
                className="w-full border border-gray-300 rounded-lg p-2"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowChangesModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={handleRequestChanges}
                disabled={!changesText.trim()}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
              >
                Submit Changes
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default InteractionPanel