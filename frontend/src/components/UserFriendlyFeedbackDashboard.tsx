'use client'

import React, { useState, useEffect } from 'react'

interface FeedbackRequest {
  id: string
  workspace_id: string
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  request_type: string
  status: string
  created_at: string
  expires_at: string
  proposed_actions: Array<{
    action: string
    description: string
  }>
  context: {
    deliverable_data?: any
    quality_assessment?: any
    workspace_goal?: string
  }
}

interface UserFriendlyFeedbackDashboardProps {
  workspaceId?: string // If provided, show only requests for this workspace
}

const UserFriendlyFeedbackDashboard: React.FC<UserFriendlyFeedbackDashboardProps> = ({ 
  workspaceId 
}) => {
  const [requests, setRequests] = useState<FeedbackRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRequest, setSelectedRequest] = useState<FeedbackRequest | null>(null)
  const [filter, setFilter] = useState<'all' | 'urgent' | 'medium' | 'low'>('all')

  useEffect(() => {
    fetchFeedbackRequests()
  }, [workspaceId])

  const fetchFeedbackRequests = async () => {
    try {
      const url = workspaceId 
        ? `http://localhost:8000/human-feedback/pending?workspace_id=${workspaceId}`
        : 'http://localhost:8000/human-feedback/pending'
      
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setRequests(data.pending_requests || [])
      }
    } catch (error) {
      console.error('Error fetching feedback requests:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (requestId: string, feedback?: string) => {
    try {
      const response = await fetch(`http://localhost:8000/human-feedback/${requestId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'approved',
          feedback: feedback || 'Approved by user'
        })
      })

      if (response.ok) {
        await fetchFeedbackRequests() // Refresh list
        setSelectedRequest(null)
      }
    } catch (error) {
      console.error('Error approving request:', error)
    }
  }

  const handleReject = async (requestId: string, reason: string) => {
    try {
      const response = await fetch(`http://localhost:8000/human-feedback/${requestId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'rejected',
          feedback: reason
        })
      })

      if (response.ok) {
        await fetchFeedbackRequests() // Refresh list
        setSelectedRequest(null)
      }
    } catch (error) {
      console.error('Error rejecting request:', error)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return '🚨'
      case 'high': return '🔴'
      case 'medium': return '🟡'
      case 'low': return '🟢'
      default: return '⚪'
    }
  }

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date()
    const expires = new Date(expiresAt)
    const diff = expires.getTime() - now.getTime()
    
    if (diff <= 0) return 'Expired'
    
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) return `${hours}h ${minutes}m remaining`
    return `${minutes}m remaining`
  }

  const extractDeliverablePreview = (request: FeedbackRequest) => {
    const deliverable = request.context?.deliverable_data
    if (!deliverable) return null

    // Extract meaningful preview content
    const summary = deliverable.summary || deliverable.description || ''
    const title = deliverable.title || deliverable.name || request.title
    
    return {
      title,
      summary: summary.slice(0, 200) + (summary.length > 200 ? '...' : ''),
      quality_score: request.context?.quality_assessment?.overall_score,
      ready_for_use: request.context?.quality_assessment?.ready_for_use,
      key_points: deliverable.key_insights || deliverable.next_steps || []
    }
  }

  const filteredRequests = requests.filter(request => {
    if (filter === 'all') return true
    if (filter === 'urgent') return ['critical', 'high'].includes(request.priority)
    return request.priority === filter
  })

  const urgentCount = requests.filter(r => ['critical', 'high'].includes(r.priority)).length

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading feedback requests...</span>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {workspaceId ? 'Project Deliverables Ready for Review' : 'Feedback Dashboard'}
            </h1>
            <p className="text-gray-600 mt-1">
              {workspaceId 
                ? 'Your AI team has completed work that needs your approval before proceeding'
                : 'Review and approve deliverables from your AI teams'
              }
            </p>
          </div>
          {urgentCount > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-red-600 font-medium">🚨 {urgentCount} urgent reviews needed</span>
              </div>
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex space-x-4 mt-4">
          {['all', 'urgent', 'medium', 'low'].map(filterType => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === filterType
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filterType === 'all' ? `All (${requests.length})` :
               filterType === 'urgent' ? `Urgent (${urgentCount})` :
               `${filterType.charAt(0).toUpperCase() + filterType.slice(1)} (${requests.filter(r => r.priority === filterType).length})`}
            </button>
          ))}
        </div>
      </div>

      {filteredRequests.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
          <p className="text-gray-600">No pending reviews at the moment.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredRequests.map(request => {
            const preview = extractDeliverablePreview(request)
            const timeRemaining = getTimeRemaining(request.expires_at)
            
            return (
              <div
                key={request.id}
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedRequest(request)}
              >
                {/* Priority Badge */}
                <div className="flex items-center justify-between mb-4">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(request.priority)}`}>
                    {getPriorityIcon(request.priority)} {request.priority.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-500">{timeRemaining}</span>
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {preview?.title || request.title}
                </h3>

                {/* Quality Score */}
                {preview?.quality_score && (
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Quality Score</span>
                      <span className={`font-medium ${preview.quality_score > 0.8 ? 'text-green-600' : preview.quality_score > 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {Math.round(preview.quality_score * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className={`h-2 rounded-full ${preview.quality_score > 0.8 ? 'bg-green-500' : preview.quality_score > 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${preview.quality_score * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Summary */}
                {preview?.summary && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {preview.summary}
                  </p>
                )}

                {/* Key Points */}
                {preview?.key_points && preview.key_points.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Key deliverables:</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {preview.key_points.slice(0, 3).map((point, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          <span className="line-clamp-1">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Actions Preview */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{request.proposed_actions?.length || 0} actions proposed</span>
                  <span className="text-blue-600 hover:text-blue-800">Click to review →</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Detailed Review Modal */}
      {selectedRequest && (
        <ReviewModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </div>
  )
}

// Separate component for the detailed review modal
const ReviewModal: React.FC<{
  request: FeedbackRequest
  onClose: () => void
  onApprove: (id: string, feedback?: string) => void
  onReject: (id: string, reason: string) => void
}> = ({ request, onClose, onApprove, onReject }) => {
  const [feedback, setFeedback] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectionForm, setShowRejectionForm] = useState(false)

  const preview = {
    title: request.context?.deliverable_data?.title || request.title,
    summary: request.context?.deliverable_data?.summary || '',
    detailed_results: request.context?.deliverable_data?.detailed_results_json || '{}',
    next_steps: request.context?.deliverable_data?.next_steps || [],
    quality_score: request.context?.quality_assessment?.overall_score,
  }

  let detailedContent
  try {
    detailedContent = JSON.parse(preview.detailed_results)
  } catch {
    detailedContent = {}
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">{preview.title}</h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          {preview.quality_score && (
            <div className="mt-2">
              <span className="text-sm text-gray-600">Quality Score: </span>
              <span className={`font-medium ${preview.quality_score > 0.8 ? 'text-green-600' : preview.quality_score > 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                {Math.round(preview.quality_score * 100)}% - {preview.quality_score > 0.8 ? 'Excellent' : preview.quality_score > 0.6 ? 'Good' : 'Needs Improvement'}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Why Review Needed */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-blue-900 mb-2">🤔 Why does this need your review?</h3>
            <p className="text-blue-800">{request.description}</p>
          </div>

          {/* Summary */}
          {preview.summary && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">📋 Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700">{preview.summary}</p>
              </div>
            </div>
          )}

          {/* Deliverable Content */}
          {Object.keys(detailedContent).length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">📄 Deliverable Content</h3>
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(detailedContent, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Next Steps */}
          {preview.next_steps && preview.next_steps.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">🎯 Proposed Next Steps</h3>
              <ul className="space-y-2">
                {preview.next_steps.map((step, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-green-500 mr-3 mt-1">✓</span>
                    <span className="text-gray-700">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Proposed Actions */}
          {request.proposed_actions && request.proposed_actions.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">⚡ Proposed Actions</h3>
              <div className="space-y-3">
                {request.proposed_actions.map((action, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <h4 className="font-medium text-gray-800">{action.action}</h4>
                    <p className="text-gray-600 text-sm mt-1">{action.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feedback Form */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">💬 Your Feedback (Optional)</h3>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Add any comments or suggestions..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>

          {/* Rejection Form */}
          {showRejectionForm && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-medium text-red-900 mb-3">❌ Reason for Rejection</h3>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Please explain why this deliverable needs to be improved..."
                className="w-full p-3 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                rows={3}
                required
              />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6">
          <div className="flex space-x-4">
            {!showRejectionForm ? (
              <>
                <button
                  onClick={() => onApprove(request.id, feedback)}
                  className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  ✅ Approve & Continue
                </button>
                <button
                  onClick={() => setShowRejectionForm(true)}
                  className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-red-700 transition-colors"
                >
                  ❌ Request Changes
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setShowRejectionForm(false)}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => rejectionReason.trim() && onReject(request.id, rejectionReason)}
                  disabled={!rejectionReason.trim()}
                  className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Submit Rejection
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserFriendlyFeedbackDashboard