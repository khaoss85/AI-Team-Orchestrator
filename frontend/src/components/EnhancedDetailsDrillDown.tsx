// frontend/src/components/EnhancedDetailsDrillDown.tsx - USER FRIENDLY DETAILS POPUP
'use client'
import React, { useEffect, useState } from 'react'
import { api } from '@/utils/api'
import type { ProjectOutputExtended, TaskResultDetailsData } from '@/types'

interface Props {
  output: ProjectOutputExtended
  workspaceId: string
  onClose: () => void
}

const EnhancedDetailsDrillDown: React.FC<Props> = ({ output, workspaceId, onClose }) => {
  const [details, setDetails] = useState<TaskResultDetailsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'raw'>('overview')

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true)
        const data = await api.monitoring.getTaskResult(workspaceId, output.task_id)
        setDetails(data)
        setError(null)
      } catch (e: any) {
        console.log('API error fetching task details:', e.message)
        // Create rich fallback from available output data
        const fallbackDetails: TaskResultDetailsData = {
          task_id: output.task_id,
          task_name: output.task_name || output.title,
          summary: output.summary || output.output || 'No summary available',
          metrics: output.metrics || {},
          next_steps: output.next_steps || [],
          key_points: output.key_insights || [],
          status: output.type || output.category || 'completed',
          result: output.actionable_assets ? {
            actionable_assets: output.actionable_assets,
            detailed_results_json: JSON.stringify(output.actionable_assets, null, 2)
          } : undefined,
          content: output.content || {},
          agent_name: output.agent_name,
          agent_role: output.agent_role,
          execution_time_seconds: output.execution_time_seconds,
          cost_estimated: output.cost_estimated,
          tokens_used: output.tokens_used,
          model_used: output.model_used,
          rationale: output.rationale
        }
        setDetails(fallbackDetails)
        setError(null)
      } finally {
        setLoading(false)
      }
    }
    fetchDetails()
  }, [workspaceId, output.task_id])

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl p-8 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading details...</p>
        </div>
      </div>
    )
  }

  if (error || !details) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl p-8 text-center max-w-md">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold mb-2">Unable to Load Details</h3>
          <p className="text-gray-600 mb-4">{error || 'Details not available'}</p>
          <button onClick={onClose} className="px-4 py-2 bg-gray-500 text-white rounded-lg">
            Close
          </button>
        </div>
      </div>
    )
  }

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'final_deliverable': return '🎯'
      case 'analysis': return '📊'
      case 'recommendation': return '💡'
      case 'document': return '📄'
      default: return '📋'
    }
  }

  const parseDetailedResults = (jsonString?: string) => {
    if (!jsonString) return null
    try {
      return typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString
    } catch {
      return null
    }
  }

  const detailedResults = parseDetailedResults(details.result?.detailed_results_json)
  
  // Enhanced data extraction from multiple sources
  const getEnhancedSummary = () => {
    // Priority: result.summary > details.summary > output.summary
    return details.result?.summary || details.summary || output.summary || 'No summary available'
  }
  
  const getEnhancedNextSteps = () => {
    // Combine next steps from multiple sources
    const steps = []
    if (details.result?.next_steps && Array.isArray(details.result.next_steps)) {
      steps.push(...details.result.next_steps)
    }
    if (details.next_steps && Array.isArray(details.next_steps)) {
      steps.push(...details.next_steps)
    }
    if (output.next_steps && Array.isArray(output.next_steps)) {
      steps.push(...output.next_steps)
    }
    // Remove duplicates
    return [...new Set(steps)]
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">{getTypeIcon(output.type)}</div>
              <div>
                <h2 className="text-2xl font-bold">{details.task_name || output.title}</h2>
                <p className="opacity-90">
                  {details.agent_role && `Created by ${details.agent_role}`}
                  {details.agent_name && ` (${details.agent_name})`}
                </p>
              </div>
            </div>
            <button 
              onClick={onClose} 
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <div className="flex">
            {['overview', 'details', 'raw'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`px-6 py-3 font-medium text-sm border-b-2 transition ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600 bg-indigo-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab === 'overview' ? '📋 Overview' : tab === 'details' ? '🔍 Details' : '🔧 Raw Data'}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Summary Section - Enhanced */}
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                <h3 className="font-semibold text-blue-800 mb-4 flex items-center text-lg">
                  <span className="mr-2">📝</span>
                  Summary
                </h3>
                <div className="text-blue-900 leading-relaxed text-base">
                  {getEnhancedSummary().split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-3 last:mb-0">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </div>

              {/* Key Insights */}
              {details.key_points && details.key_points.length > 0 && (
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <h3 className="font-semibold text-green-800 mb-3 flex items-center">
                    <span className="mr-2">💡</span>
                    Key Insights
                  </h3>
                  <ul className="space-y-2">
                    {details.key_points.map((point: string, index: number) => (
                      <li key={index} className="flex items-start">
                        <span className="text-green-600 mr-2">•</span>
                        <span className="text-green-900">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Next Steps - Enhanced */}
              {getEnhancedNextSteps().length > 0 && (
                <div className="bg-orange-50 rounded-lg p-6 border border-orange-200">
                  <h3 className="font-semibold text-orange-800 mb-4 flex items-center text-lg">
                    <span className="mr-2">⏭️</span>
                    Recommended Next Steps
                  </h3>
                  <div className="space-y-3">
                    {getEnhancedNextSteps().map((step: string, index: number) => (
                      <div key={index} className="flex items-start bg-white rounded-lg p-3 shadow-sm">
                        <div className="bg-orange-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">
                          {index + 1}
                        </div>
                        <span className="text-orange-900 leading-relaxed">{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics */}
              {details.metrics && Object.keys(details.metrics).length > 0 && (
                <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                  <h3 className="font-semibold text-purple-800 mb-3 flex items-center">
                    <span className="mr-2">📊</span>
                    Metrics
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(details.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-purple-700 font-medium">{key.replace(/_/g, ' ')}:</span>
                        <span className="text-purple-900 font-bold">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'details' && (
            <div className="space-y-6">
              {/* Simplified Execution Stats */}
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-200">
                <h3 className="font-semibold text-indigo-800 mb-4 flex items-center text-lg">
                  <span className="mr-2">⚙️</span>
                  Execution Stats
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {details.execution_time_seconds && (
                    <div className="text-center">
                      <div className="text-2xl mb-1">⏱️</div>
                      <div className="text-lg font-bold text-indigo-900">{details.execution_time_seconds}s</div>
                      <div className="text-sm text-indigo-600">Duration</div>
                    </div>
                  )}
                  {details.cost_estimated && (
                    <div className="text-center">
                      <div className="text-2xl mb-1">💰</div>
                      <div className="text-lg font-bold text-indigo-900">${details.cost_estimated}</div>
                      <div className="text-sm text-indigo-600">Cost</div>
                    </div>
                  )}
                  {details.tokens_used && (
                    <div className="text-center">
                      <div className="text-2xl mb-1">🔤</div>
                      <div className="text-lg font-bold text-indigo-900">
                        {typeof details.tokens_used === 'object' 
                          ? `${(details.tokens_used as any).input + (details.tokens_used as any).output || 0}`
                          : details.tokens_used
                        }
                      </div>
                      <div className="text-sm text-indigo-600">Tokens</div>
                    </div>
                  )}
                  {details.model_used && (
                    <div className="text-center">
                      <div className="text-2xl mb-1">🤖</div>
                      <div className="text-sm font-bold text-indigo-900">{details.model_used}</div>
                      <div className="text-sm text-indigo-600">AI Model</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Agent Information */}
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                <h3 className="font-semibold text-green-800 mb-4 flex items-center text-lg">
                  <span className="mr-2">👤</span>
                  Agent Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-500 text-white rounded-full p-2">
                      <span className="text-lg">🎭</span>
                    </div>
                    <div>
                      <div className="font-medium text-green-900">{details.agent_role || 'AI Specialist'}</div>
                      <div className="text-sm text-green-600">Agent Role</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-500 text-white rounded-full p-2">
                      <span className="text-lg">✅</span>
                    </div>
                    <div>
                      <div className="font-medium text-green-900 capitalize">{details.status || 'Completed'}</div>
                      <div className="text-sm text-green-600">Status</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Rationale - Simplified */}
              {details.rationale && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
                  <h3 className="font-semibold text-purple-800 mb-4 flex items-center text-lg">
                    <span className="mr-2">🧠</span>
                    AI Decision Process
                  </h3>
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-purple-900 leading-relaxed">
                      {details.rationale.split('\n').map((paragraph, index) => (
                        <p key={index} className="mb-2 last:mb-0">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Key Results - Visual Cards */}
              {detailedResults && (
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-800 mb-4 flex items-center text-lg">
                    <span className="mr-2">📊</span>
                    Key Results
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(detailedResults).slice(0, 6).map(([key, value]) => (
                      <div key={key} className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-400">
                        <div className="font-medium text-gray-800 mb-2 text-sm">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div className="text-gray-600 text-sm leading-relaxed">
                          {(() => {
                            if (typeof value === 'object') {
                              if (Array.isArray(value)) {
                                if (value.length === 0) return 'Empty array'
                                
                                // Smart array display
                                const preview = value.slice(0, 2).map(item => {
                                  if (typeof item === 'object' && item !== null) {
                                    // Extract meaningful info from objects
                                    if (item.name) return item.name
                                    if (item.title) return item.title
                                    if (item.type) return item.type
                                    if (item.id) return `ID: ${item.id}`
                                    // Show first property value
                                    const firstEntry = Object.entries(item)[0]
                                    return firstEntry ? `${firstEntry[0]}: ${String(firstEntry[1]).substring(0, 25)}` : 'Object'
                                  }
                                  return String(item).substring(0, 30)
                                }).join(' • ')
                                
                                return (
                                  <div>
                                    <div className="font-medium text-gray-700">{value.length} items</div>
                                    <div className="mt-1">{preview}{value.length > 2 ? ' • ...' : ''}</div>
                                  </div>
                                )
                              } else if (value === null) {
                                return 'null'
                              } else {
                                // Smart object display
                                const entries = Object.entries(value)
                                if (entries.length === 0) return 'Empty object'
                                
                                // Show first few key-value pairs with better formatting
                                const preview = entries.slice(0, 3).map(([k, v]) => {
                                  const cleanKey = k.replace(/_/g, ' ')
                                  const cleanValue = typeof v === 'object' 
                                    ? (Array.isArray(v) ? `${v.length} items` : 'Object')
                                    : String(v).substring(0, 40)
                                  return `${cleanKey}: ${cleanValue}`
                                }).join(' • ')
                                
                                return (
                                  <div>
                                    <div className="font-medium text-gray-700">{entries.length} properties</div>
                                    <div className="mt-1">{preview}{entries.length > 3 ? ' • ...' : ''}</div>
                                  </div>
                                )
                              }
                            } else {
                              const stringValue = String(value)
                              if (stringValue.length > 120) {
                                return (
                                  <div>
                                    <div className="mb-1">{stringValue.substring(0, 120)}...</div>
                                    <div className="text-xs text-gray-500">({stringValue.length} characters total)</div>
                                  </div>
                                )
                              }
                              return stringValue
                            }
                          })()}
                        </div>
                      </div>
                    ))}
                  </div>
                  {Object.keys(detailedResults).length > 6 && (
                    <div className="mt-4 text-center">
                      <p className="text-sm text-gray-500">
                        + {Object.keys(detailedResults).length - 6} more results (see Raw Data tab)
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="space-y-4">
              <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
                <h3 className="text-white font-medium mb-3">Raw JSON Data</h3>
                <pre className="text-green-400 text-sm overflow-auto max-h-96">
                  {JSON.stringify(details, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="flex space-x-4">
            <button
              onClick={() => {
                const dataStr = 'data:application/json;charset=utf-8,' +
                  encodeURIComponent(JSON.stringify(details, null, 2))
                const link = document.createElement('a')
                link.href = dataStr
                link.download = `deliverable_${output.task_id}.json`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
              }}
              className="flex-1 bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center justify-center space-x-2"
            >
              <span>📥</span>
              <span>Download Data</span>
            </button>
            <button
              onClick={async () => {
                try {
                  await api.monitoring.submitDeliverableFeedback(workspaceId, {
                    feedback_type: 'request_changes',
                    message: 'Request modifications for this deliverable',
                    priority: 'medium',
                    specific_tasks: [output.task_id]
                  })
                  alert('Feedback submitted successfully!')
                } catch (e) {
                  console.error(e)
                  alert('Error submitting feedback')
                }
              }}
              className="flex-1 bg-orange-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-orange-700 transition flex items-center justify-center space-x-2"
            >
              <span>💬</span>
              <span>Request Changes</span>
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EnhancedDetailsDrillDown