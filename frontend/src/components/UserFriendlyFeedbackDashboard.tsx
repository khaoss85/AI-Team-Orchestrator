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
    workspace_name?: string
    why_review_needed?: string
    key_content?: string
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
  const [workspaceNames, setWorkspaceNames] = useState<{[key: string]: string}>({})

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
        const requestsData = data || []
        setRequests(requestsData)
        
        // Fetch workspace names for global view
        if (!workspaceId && requestsData.length > 0) {
          const uniqueWorkspaceIds = [...new Set(requestsData.map(r => r.workspace_id))]
          const workspaceNamesMap = {}
          
          for (const wsId of uniqueWorkspaceIds) {
            try {
              const wsResponse = await fetch(`http://localhost:8000/api/workspaces/${wsId}`)
              if (wsResponse.ok) {
                const wsData = await wsResponse.json()
                workspaceNamesMap[wsId] = wsData.name || `Progetto ${wsId.slice(0, 8)}`
              }
            } catch (err) {
              workspaceNamesMap[wsId] = `Progetto ${wsId.slice(0, 8)}`
            }
          }
          
          setWorkspaceNames(workspaceNamesMap)
        }
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
    const workspaceName = workspaceNames[request.workspace_id] || `Progetto ${request.workspace_id.slice(0, 8)}`
    
    // Parse description to extract key fields - prioritize "What to Review"
    const description = request.description || ''
    
    // Extract "What to Review" (prioritized) or "Why Review Needed" as fallback
    const whatToReviewMatch = description.match(/\*\*What to Review\*\*[:\s]*([^\*]+)/)
    const whyReviewMatch = description.match(/\*\*Why Review Needed\*\*[:\s]*([^\*]+)/)
    
    const reviewReason = whatToReviewMatch 
      ? whatToReviewMatch[1].trim().replace(/\n/g, ' ').slice(0, 100) + (whatToReviewMatch[1].length > 100 ? '...' : '')
      : whyReviewMatch 
        ? whyReviewMatch[1].trim().replace(/\n/g, ' ').slice(0, 100) + (whyReviewMatch[1].length > 100 ? '...' : '')
        : "Il team AI ha completato questo lavoro e necessita della tua verifica"
    
    // Extract clean title from Business Impact or fallback
    const businessImpactMatch = description.match(/\*\*Business Impact\*\*[:\s]*([^\*]+)/)
    const cleanTitle = businessImpactMatch
      ? businessImpactMatch[1].trim().slice(0, 70) + (businessImpactMatch[1].length > 70 ? '...' : '')
      : request.title.replace('Review ', '').replace(' Deliverable', '').replace('Validate ', '')
    
    return {
      title: cleanTitle,
      workspaceName,
      whyReviewNeeded: reviewReason,
      quality_score: request.context?.quality_assessment?.overall_score,
      ready_for_use: request.context?.quality_assessment?.ready_for_use
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
            {/* Breadcrumb navigation for filtered view */}
            {workspaceId && (
              <div className="flex items-center space-x-2 mb-2">
                <button
                  onClick={() => window.location.href = '/human-feedback'}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span>Tutti i progetti</span>
                </button>
                <span className="text-gray-400">→</span>
                <span className="text-sm text-gray-600">Questo progetto</span>
              </div>
            )}
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
        <div className="space-y-6">
          {/* Group requests by workspace for tree view */}
          {Object.entries(
            filteredRequests.reduce((groups, request) => {
              const workspaceName = workspaceNames[request.workspace_id] || `Progetto ${request.workspace_id.slice(0, 8)}`
              if (!groups[request.workspace_id]) {
                groups[request.workspace_id] = {
                  name: workspaceName,
                  requests: []
                }
              }
              groups[request.workspace_id].requests.push(request)
              return groups
            }, {} as Record<string, { name: string; requests: FeedbackRequest[] }>)
          ).map(([workspaceId, group]) => (
            <div key={workspaceId} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {/* Workspace Header */}
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">📁</span>
                    <h3 className="font-medium text-gray-900">{group.name}</h3>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {group.requests.length} {group.requests.length === 1 ? 'review' : 'reviews'}
                    </span>
                  </div>
                  {/* Show urgent count for this workspace */}
                  {group.requests.filter(r => ['critical', 'high'].includes(r.priority)).length > 0 && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      {group.requests.filter(r => ['critical', 'high'].includes(r.priority)).length} urgenti
                    </span>
                  )}
                </div>
              </div>

              {/* Request List */}
              <div className="divide-y divide-gray-100">
                {group.requests
                  .sort((a, b) => {
                    // Sort by priority: critical > high > medium > low
                    const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
                    return priorityOrder[b.priority] - priorityOrder[a.priority]
                  })
                  .map(request => {
                    const preview = extractDeliverablePreview(request)
                    const timeRemaining = getTimeRemaining(request.expires_at)
                    
                    return (
                      <div
                        key={request.id}
                        className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedRequest(request)}
                      >
                        <div className="flex items-center justify-between">
                          {/* Left side: Priority + Title + Description */}
                          <div className="flex items-center space-x-4 flex-1 min-w-0">
                            {/* Priority indicator */}
                            <div className="flex-shrink-0">
                              <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${getPriorityColor(request.priority)}`}>
                                {getPriorityIcon(request.priority)}
                              </span>
                            </div>
                            
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <h4 className="text-sm font-medium text-gray-900 truncate">
                                  {preview?.title}
                                </h4>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(request.priority)}`}>
                                  {request.priority.toUpperCase()}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 truncate">
                                {preview?.whyReviewNeeded}
                              </p>
                            </div>
                          </div>

                          {/* Right side: Metrics + Time */}
                          <div className="flex items-center space-x-4 flex-shrink-0">
                            {/* Quality Score with working tooltip */}
                            {preview?.quality_score && (
                              <div className="text-center group relative">
                                <div 
                                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                                    preview.quality_score > 0.7 ? 'bg-green-100 text-green-700' : 
                                    preview.quality_score > 0.5 ? 'bg-yellow-100 text-yellow-700' : 
                                    'bg-red-100 text-red-700'
                                  }`}
                                >
                                  {Math.round(preview.quality_score * 100)}%
                                </div>
                                <div className="text-xs text-gray-500 mt-1">qualità</div>
                                
                                {/* Tooltip */}
                                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 w-64">
                                  <div className="font-semibold mb-1">Punteggio Qualità:</div>
                                  <div>• >70% = Ottimo</div>
                                  <div>• 50-70% = Buono</div>
                                  <div>• &lt;50% = Richiede miglioramenti</div>
                                  <div className="mt-1 text-gray-300">Basato su completezza, accuratezza e usabilità</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Time remaining with working tooltip */}
                            <div className="text-center min-w-0 group relative">
                              <div 
                                className={`text-sm font-medium ${
                                  timeRemaining === 'Expired' ? 'text-red-600' :
                                  timeRemaining.includes('h') ? 'text-gray-900' : 'text-orange-600'
                                }`}
                              >
                                {timeRemaining === 'Expired' ? '⏰' : 
                                 timeRemaining.includes('h') ? timeRemaining.split(' ')[0] : timeRemaining.split('m')[0] + 'm'}
                              </div>
                              <div className="text-xs text-gray-500">
                                {timeRemaining === 'Expired' ? 'scaduto' : 'rimasti'}
                              </div>
                              
                              {/* Tooltip */}
                              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 w-48">
                                Tempo rimasto per approvare prima della scadenza automatica
                              </div>
                            </div>
                            
                            {/* Action arrow */}
                            <div className="text-blue-600 hover:text-blue-800">
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detailed Review Modal */}
      {selectedRequest && (
        <ReviewModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onApprove={handleApprove}
          onReject={handleReject}
          workspaceId={workspaceId}
          workspaceNames={workspaceNames}
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
  workspaceId?: string
  workspaceNames: {[key: string]: string}
}> = ({ request, onClose, onApprove, onReject, workspaceId, workspaceNames }) => {
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
          {/* Project Info per vista globale */}
          {!workspaceId && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <span className="text-gray-600 mr-2">📁</span>
                <div>
                  <p className="font-medium text-gray-900">Progetto: {workspaceNames[request.workspace_id] || `Progetto ${request.workspace_id.slice(0, 8)}`}</p>
                  <p className="text-sm text-gray-600">ID: {request.workspace_id}</p>
                </div>
              </div>
            </div>
          )}
          
          {/* What to Review and Why - COMPLETO */}
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            {(() => {
              const description = request.description || ''
              const whatToReviewMatch = description.match(/\*\*What to Review\*\*[:\s]*([^\*]+)/)
              const whyReviewMatch = description.match(/\*\*Why Review Needed\*\*[:\s]*([^\*]+)/)
              
              return (
                <>
                  {whatToReviewMatch && (
                    <div className="mb-3">
                      <h3 className="font-medium text-blue-900 mb-2 flex items-center">
                        <span className="mr-2">🔍</span>
                        Cosa verificare
                      </h3>
                      <div className="text-blue-800 leading-relaxed">
                        {whatToReviewMatch[1].trim().replace(/\n/g, ' ')}
                      </div>
                    </div>
                  )}
                  
                  {whyReviewMatch && (
                    <div>
                      <h3 className="font-medium text-blue-900 mb-2 flex items-center">
                        <span className="mr-2">💡</span>
                        Perché serve la tua review
                      </h3>
                      <div className="text-blue-800 leading-relaxed">
                        {whyReviewMatch[1].trim().replace(/\n/g, ' ')}
                      </div>
                    </div>
                  )}
                  
                  {!whatToReviewMatch && !whyReviewMatch && (
                    <div>
                      <h3 className="font-medium text-blue-900 mb-2 flex items-center">
                        <span className="mr-2">🔍</span>
                        Review richiesta
                      </h3>
                      <div className="text-blue-800 leading-relaxed">
                        {request.context?.why_review_needed || 
                         "Controlla il contenuto generato dal team AI per assicurarti che rispetti i tuoi standard di qualità."}
                      </div>
                    </div>
                  )}
                </>
              )
            })()}
          </div>

          {/* Quality Analysis & Technical Details */}
          <details className="mb-6 border border-gray-200 rounded-lg">
            <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:bg-gray-50 flex items-center">
              <svg className="w-4 h-4 mr-2 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              📊 Analisi Qualità & Dettagli Tecnici
            </summary>
            <div className="p-4 border-t border-gray-200 space-y-4">
              {/* Quality Breakdown */}
              {request.context?.quality_assessment && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-3 flex items-center">
                    <span className="mr-2">🎯</span>
                    Breakdown Punteggio Qualità ({Math.round((request.context.quality_assessment.overall_score || 0) * 100)}%)
                  </h4>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>📄 Completezza contenuto:</span>
                      <span className="font-medium">{request.context.quality_assessment.quality_issues?.includes('placeholder_data') ? '❌ Dati placeholder' : '✅ Dati completi'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>🎯 Usabilità business:</span>
                      <span className="font-medium">{request.context.quality_assessment.ready_for_use ? '✅ Pronto per uso' : '⚠️ Richiede modifiche'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>💼 Conformità requisiti:</span>
                      <span className="font-medium">{request.context.quality_assessment.needs_enhancement ? '⚠️ Miglioramenti necessari' : '✅ Conforme'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>🔍 Problemi identificati:</span>
                      <span className="font-medium">{request.context.quality_assessment.quality_issues?.length || 0}</span>
                    </div>
                  </div>
                  
                  {request.context.quality_assessment.improvement_suggestions && (
                    <div className="mt-3">
                      <h5 className="font-medium text-blue-800 mb-2">💡 Suggerimenti miglioramento:</h5>
                      <ul className="text-sm space-y-1">
                        {request.context.quality_assessment.improvement_suggestions.slice(0, 3).map((suggestion, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-blue-500 mr-2 mt-0.5">•</span>
                            <span className="text-blue-700">{suggestion.slice(0, 120)}...</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              
              {/* Summary */}
              {preview.summary && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800 mb-2">📝 Summary Task</h4>
                  <p className="text-gray-700 text-sm">{preview.summary}</p>
                </div>
              )}
              
              {/* Next Steps */}
              {preview.next_steps && preview.next_steps.length > 0 && (
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-800 mb-2">🎯 Next Steps</h4>
                  <ul className="space-y-1 text-sm">
                    {preview.next_steps.map((step, index) => (
                      <li key={index} className="flex items-start text-green-700">
                        <span className="text-green-500 mr-2 mt-0.5">✓</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Raw JSON - minimized */}
              {Object.keys(detailedContent).length > 0 && (
                <details className="bg-gray-800 rounded-lg">
                  <summary className="cursor-pointer p-3 text-white text-sm font-medium">
                    🔧 Dati Tecnici Raw (JSON)
                  </summary>
                  <div className="p-3 max-h-40 overflow-y-auto">
                    <pre className="text-xs text-green-400 font-mono">
                      {JSON.stringify(detailedContent, null, 2)}
                    </pre>
                  </div>
                </details>
              )}
            </div>
          </details>

          {/* Proposed Actions - MIGLIORATO */}
          {request.proposed_actions && request.proposed_actions.length > 0 && (
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                <span className="mr-2">⚡</span>
                Azioni Proposte dal Team AI
              </h3>
              <div className="space-y-3">
                {request.proposed_actions.map((action, index) => (
                  <div key={index} className="border border-green-200 rounded-lg p-4 bg-green-50">
                    <div className="flex items-start">
                      <div className="text-green-500 mr-3 mt-1">
                        {index === 0 ? '✅' : '📋'}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-green-800 mb-1">{action.action}</h4>
                        <p className="text-green-700 text-sm leading-relaxed">{action.description}</p>
                        {index === 0 && (
                          <span className="inline-block mt-2 px-2 py-1 bg-green-200 text-green-800 text-xs font-medium rounded">
                            Azione Principale
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600 flex items-center">
                  <span className="mr-2">💡</span>
                  <strong>Suggerimento:</strong> Approva se le azioni ti sembrano corrette, oppure rifiuta specificando cosa dovrebbe essere cambiato.
                </p>
              </div>
            </div>
          )}

          {/* Commenti aggiuntivi (opzionale) */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">💬 Commenti aggiuntivi (opzionale)</h3>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Aggiungi commenti o suggerimenti..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={2}
            />
          </div>

          {/* Form rifiuto */}
          {showRejectionForm && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-medium text-red-900 mb-3">❌ Motivo del rifiuto</h3>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Spiega cosa deve essere migliorato..."
                className="w-full p-3 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                rows={2}
                required
              />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-3">
            {!showRejectionForm ? (
              <>
                <button
                  onClick={() => onApprove(request.id, feedback)}
                  className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  ✅ Approva
                </button>
                <button
                  onClick={() => setShowRejectionForm(true)}
                  className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors"
                >
                  ❌ Rifiuta
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setShowRejectionForm(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={() => rejectionReason.trim() && onReject(request.id, rejectionReason)}
                  disabled={!rejectionReason.trim()}
                  className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Conferma Rifiuto
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