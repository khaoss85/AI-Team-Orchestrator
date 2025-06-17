'use client'

import React, { useState, useEffect } from 'react'
import UserFriendlyFeedbackDashboard from './UserFriendlyFeedbackDashboard'

interface ProjectFeedbackPanelProps {
  workspaceId: string
  isOpen: boolean
  onClose: () => void
}

const ProjectFeedbackPanel: React.FC<ProjectFeedbackPanelProps> = ({
  workspaceId,
  isOpen,
  onClose
}) => {
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    if (isOpen) {
      fetchPendingCount()
    }
  }, [isOpen, workspaceId])

  const fetchPendingCount = async () => {
    try {
      const response = await fetch(`http://localhost:8000/human-feedback/pending?workspace_id=${workspaceId}`)
      if (response.ok) {
        const data = await response.json()
        setPendingCount(data.pending_requests?.length || 0)
      }
    } catch (error) {
      console.error('Error fetching pending count:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header with Project Context */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Project Deliverables Review</h2>
            <p className="text-gray-600 text-sm mt-1">
              Your AI team has {pendingCount} deliverable{pendingCount !== 1 ? 's' : ''} ready for your review
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          <UserFriendlyFeedbackDashboard workspaceId={workspaceId} />
        </div>

        {/* Footer with Context Actions */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              💡 Tip: Approved deliverables will automatically advance your project goals
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => fetchPendingCount()}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
              >
                🔄 Refresh
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Back to Project
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProjectFeedbackPanel