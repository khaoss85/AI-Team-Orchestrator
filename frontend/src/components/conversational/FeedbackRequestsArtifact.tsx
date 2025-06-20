'use client'

import React, { useState } from 'react'

interface FeedbackRequest {
  id: string
  title: string
  description: string
  type: 'deliverable' | 'quality' | 'validation' | 'review'
  status: 'pending' | 'in_progress' | 'completed' | 'rejected'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  createdAt: string
  dueDate?: string
  requestedBy: string
  assignedTo?: string
  content?: any
  metadata?: Record<string, any>
}

interface FeedbackRequestsArtifactProps {
  feedbackData: {
    requests: FeedbackRequest[]
    pendingCount: number
    completedCount: number
  }
  workspaceId: string
  onFeedbackUpdate?: (updatedFeedback: any) => void
}

export default function FeedbackRequestsArtifact({ 
  feedbackData, 
  workspaceId, 
  onFeedbackUpdate 
}: FeedbackRequestsArtifactProps) {
  const [activeView, setActiveView] = useState<'pending' | 'completed' | 'all' | 'analytics'>('pending')
  const [selectedRequest, setSelectedRequest] = useState<FeedbackRequest | null>(null)

  const { requests, pendingCount, completedCount } = feedbackData

  if (!requests || requests.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">💬</div>
          <div className="text-lg font-medium mb-2">No Feedback Requests</div>
          <div className="text-sm">
            Feedback requests will appear here when your team needs input
          </div>
        </div>
      </div>
    )
  }

  const filteredRequests = requests.filter(request => {
    switch (activeView) {
      case 'pending': return request.status === 'pending' || request.status === 'in_progress'
      case 'completed': return request.status === 'completed'
      case 'all': return true
      default: return true
    }
  })

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with view tabs */}
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          💬 Feedback Requests
        </h3>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-orange-50 p-2 rounded-lg">
            <div className="text-lg font-bold text-orange-600">{pendingCount}</div>
            <div className="text-xs text-orange-700">Pending</div>
          </div>
          <div className="bg-green-50 p-2 rounded-lg">
            <div className="text-lg font-bold text-green-600">{completedCount}</div>
            <div className="text-xs text-green-700">Completed</div>
          </div>
        </div>
        
        <div className="flex space-x-1 overflow-x-auto">
          <ViewTab
            active={activeView === 'pending'}
            onClick={() => setActiveView('pending')}
            label="Pending"
            icon="⏳"
            count={pendingCount}
          />
          <ViewTab
            active={activeView === 'completed'}
            onClick={() => setActiveView('completed')}
            label="Completed"
            icon="✅"
            count={completedCount}
          />
          <ViewTab
            active={activeView === 'all'}
            onClick={() => setActiveView('all')}
            label="All"
            icon="📋"
            count={requests.length}
          />
          <ViewTab
            active={activeView === 'analytics'}
            onClick={() => setActiveView('analytics')}
            label="Analytics"
            icon="📊"
          />
        </div>
      </div>

      {/* Content based on active view */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'analytics' ? (
          <FeedbackAnalyticsTab requests={requests} />
        ) : (
          <FeedbackRequestsList 
            requests={filteredRequests}
            onSelectRequest={setSelectedRequest}
            onRequestUpdate={onFeedbackUpdate}
          />
        )}
      </div>

      {/* Request Detail Modal */}
      {selectedRequest && (
        <RequestDetailModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onUpdate={onFeedbackUpdate}
        />
      )}
    </div>
  )
}

// View Tab Component
interface ViewTabProps {
  active: boolean
  onClick: () => void
  label: string
  icon: string
  count?: number
}

function ViewTab({ active, onClick, label, icon, count }: ViewTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap
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

// Feedback Requests List
interface FeedbackRequestsListProps {
  requests: FeedbackRequest[]
  onSelectRequest: (request: FeedbackRequest) => void
  onRequestUpdate?: (updatedRequest: any) => void
}

function FeedbackRequestsList({ 
  requests, 
  onSelectRequest, 
  onRequestUpdate 
}: FeedbackRequestsListProps) {
  if (requests.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">🎉</div>
          <div className="text-lg font-medium mb-2">All caught up!</div>
          <div className="text-sm">No feedback requests in this category</div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-3">
      {requests.map((request) => (
        <RequestCard
          key={request.id}
          request={request}
          onClick={() => onSelectRequest(request)}
          onQuickAction={onRequestUpdate}
        />
      ))}
    </div>
  )
}

// Request Card Component
interface RequestCardProps {
  request: FeedbackRequest
  onClick: () => void
  onQuickAction?: (action: any) => void
}

function RequestCard({ request, onClick, onQuickAction }: RequestCardProps) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'deliverable': return '📦'
      case 'quality': return '⭐'
      case 'validation': return '✅'
      case 'review': return '👁️'
      default: return '📄'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-orange-100 text-orange-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const isOverdue = request.dueDate && new Date(request.dueDate) < new Date()

  return (
    <div
      onClick={onClick}
      className={`p-3 border rounded-lg hover:border-gray-300 hover:shadow-sm cursor-pointer transition-all ${
        isOverdue ? 'border-red-200 bg-red-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-3">
          <span className="text-lg">{getTypeIcon(request.type)}</span>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${getPriorityColor(request.priority)}`} />
            <div className="font-medium text-gray-900 text-sm line-clamp-1">
              {request.title}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isOverdue && (
            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
              Overdue
            </span>
          )}
          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(request.status)}`}>
            {request.status.replace('_', ' ')}
          </span>
        </div>
      </div>

      {request.description && (
        <div className="text-sm text-gray-600 line-clamp-2 mb-2">
          {request.description}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          <div className="capitalize">{request.type}</div>
          <div>by {request.requestedBy}</div>
        </div>
        <div className="flex items-center space-x-2">
          {request.dueDate && (
            <div className={isOverdue ? 'text-red-600' : ''}>
              Due: {new Date(request.dueDate).toLocaleDateString()}
            </div>
          )}
          <div>{new Date(request.createdAt).toLocaleDateString()}</div>
        </div>
      </div>
    </div>
  )
}

// Feedback Analytics Tab
function FeedbackAnalyticsTab({ requests }: { requests: FeedbackRequest[] }) {
  const totalRequests = requests.length
  const byStatus = requests.reduce((acc, req) => {
    acc[req.status] = (acc[req.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const byType = requests.reduce((acc, req) => {
    acc[req.type] = (acc[req.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const byPriority = requests.reduce((acc, req) => {
    acc[req.priority] = (acc[req.priority] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const avgResponseTime = '2.3 days' // Mock calculation

  return (
    <div className="p-4 space-y-4">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{totalRequests}</div>
          <div className="text-sm text-blue-700">Total Requests</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{avgResponseTime}</div>
          <div className="text-sm text-purple-700">Avg Response Time</div>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Status Distribution</h4>
        <div className="space-y-2">
          {Object.entries(byStatus).map(([status, count]) => (
            <div key={status} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">{status.replace('_', ' ')}</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(count / totalRequests) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-8">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Type Distribution */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Request Types</h4>
        <div className="space-y-2">
          {Object.entries(byType).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">{type}</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${(count / totalRequests) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-8">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Priority Distribution */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Priority Levels</h4>
        <div className="space-y-2">
          {Object.entries(byPriority).map(([priority, count]) => (
            <div key={priority} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">{priority}</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-orange-600 h-2 rounded-full" 
                    style={{ width: `${(count / totalRequests) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-8">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Request Detail Modal
interface RequestDetailModalProps {
  request: FeedbackRequest
  onClose: () => void
  onUpdate?: (updatedRequest: any) => void
}

function RequestDetailModal({ request, onClose, onUpdate }: RequestDetailModalProps) {
  const [feedback, setFeedback] = useState('')
  const [status, setStatus] = useState(request.status)
  const [submitting, setSubmitting] = useState(false)

  const handleApprove = async () => {
    try {
      setSubmitting(true)
      const response = await fetch(`http://localhost:8000/human-feedback/${request.id}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'approved',
          feedback: feedback || 'Approved by user'
        })
      })

      if (response.ok) {
        if (onUpdate) {
          onUpdate({
            ...request,
            status: 'completed',
            feedback,
            updatedAt: new Date().toISOString()
          })
        }
        onClose()
      } else {
        alert('Failed to approve request')
      }
    } catch (error) {
      console.error('Error approving request:', error)
      alert('Error approving request')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReject = async () => {
    if (!feedback.trim()) {
      alert('Please provide feedback when rejecting')
      return
    }

    try {
      setSubmitting(true)
      const response = await fetch(`http://localhost:8000/human-feedback/${request.id}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'rejected',
          feedback: feedback
        })
      })

      if (response.ok) {
        if (onUpdate) {
          onUpdate({
            ...request,
            status: 'rejected',
            feedback,
            updatedAt: new Date().toISOString()
          })
        }
        onClose()
      } else {
        alert('Failed to reject request')
      }
    } catch (error) {
      console.error('Error rejecting request:', error)
      alert('Error rejecting request')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {request.title}
            </h3>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <div className="text-sm text-gray-900 p-3 bg-gray-50 rounded-lg">
                {request.description}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as any)}
                  className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <div className="text-sm text-gray-900 p-2 bg-gray-50 rounded-lg capitalize">
                  {request.priority}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Feedback
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Provide your feedback here..."
                className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none"
                rows={4}
              />
            </div>

            {request.content && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content to Review
                </label>
                <div className="text-sm text-gray-900 p-3 bg-gray-50 rounded-lg max-h-32 overflow-y-auto">
                  {typeof request.content === 'string' ? request.content : JSON.stringify(request.content, null, 2)}
                </div>
              </div>
            )}

            {/* Quality Score */}
            {request.metadata?.quality_assessment?.score && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quality Score
                </label>
                <div className={`text-lg font-bold p-2 rounded-lg text-center ${
                  request.metadata.quality_assessment.score >= 70 ? 'bg-green-100 text-green-800' :
                  request.metadata.quality_assessment.score >= 50 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {request.metadata.quality_assessment.score}% Quality
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  • &gt;70% = Ottimo • 50-70% = Buono • &lt;50% = Richiede miglioramenti
                </div>
              </div>
            )}

            {/* Why Review Needed */}
            {request.metadata?.why_review_needed && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Perché serve la tua review
                </label>
                <div className="text-sm text-gray-900 p-3 bg-blue-50 rounded-lg">
                  {request.metadata.why_review_needed}
                </div>
              </div>
            )}

            {/* Proposed Actions */}
            {request.metadata?.proposed_actions && request.metadata.proposed_actions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Azioni Proposte dal Team AI
                </label>
                <div className="space-y-2">
                  {request.metadata.proposed_actions.map((action: any, index: number) => (
                    <div key={index} className="p-2 bg-gray-50 rounded border-l-4 border-blue-500">
                      <div className="font-medium text-sm">✅ {action.action}</div>
                      <div className="text-xs text-gray-600">{action.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-4 border-t">
              <button
                onClick={onClose}
                disabled={submitting}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
              >
                Cancel
              </button>
              
              {request.status === 'pending' && (
                <>
                  <button
                    onClick={handleReject}
                    disabled={submitting}
                    className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    {submitting ? 'Processing...' : '❌ Rifiuta'}
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {submitting ? 'Processing...' : '✅ Approva'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}