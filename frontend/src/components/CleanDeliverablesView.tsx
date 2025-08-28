'use client'

import React, { useState, useEffect } from 'react'
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables'
import { api } from '@/utils/api'
import DeliverableCard from './redesign/DeliverableCard'

interface CleanDeliverablesViewProps {
  workspaceId: string
  showMissingDeliverablesAlert?: boolean
}

interface MissingDeliverableAlert {
  goalId: string
  goalTitle: string
  missingDeliverables: string[]
  progress: number
  canAutoComplete: boolean
  blockedReason?: string
}

export default function CleanDeliverablesView({ 
  workspaceId, 
  showMissingDeliverablesAlert = true 
}: CleanDeliverablesViewProps) {
  const {
    deliverables,
    loading,
    error,
    refetch,
  } = useProjectDeliverables(workspaceId)

  const [autoCompletingTasks, setAutoCompletingTasks] = useState<string[]>([])
  const [missingDeliverables, setMissingDeliverables] = useState<MissingDeliverableAlert[]>([])
  const [loadingMissing, setLoadingMissing] = useState(true)

  // Load missing deliverables from API
  useEffect(() => {
    const loadMissingDeliverables = async () => {
      try {
        setLoadingMissing(true)
        const response = await fetch(`/api/auto-completion/workspace/${workspaceId}/missing-deliverables`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.missing_deliverables) {
            const formattedMissing: MissingDeliverableAlert[] = data.missing_deliverables.map((md: any) => ({
              goalId: md.goal_id,
              goalTitle: md.goal_title,
              missingDeliverables: md.missing_deliverables,
              progress: Math.round(md.progress_percentage || 0),
              canAutoComplete: md.can_auto_complete,
              blockedReason: md.blocked_reason
            }))
            setMissingDeliverables(formattedMissing)
          }
        }
      } catch (error) {
        console.error('Error loading missing deliverables:', error)
      } finally {
        setLoadingMissing(false)
      }
    }

    loadMissingDeliverables()
  }, [workspaceId])

  const handleAutoComplete = async (goalId: string, deliverableName: string) => {
    const taskKey = `${goalId}-${deliverableName}`
    setAutoCompletingTasks(prev => [...prev, taskKey])
    
    try {
      // Call backend API to trigger auto-completion
      const response = await fetch(`/api/auto-completion/goals/${goalId}/auto-complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          deliverable_name: deliverableName,
          workspace_id: workspaceId
        })
      })

      const result = await response.json()

      if (response.ok && result.success) {
        // Refresh deliverables after auto-completion
        setTimeout(() => {
          refetch()
          setAutoCompletingTasks(prev => prev.filter(t => t !== taskKey))
          // Also refresh missing deliverables
          loadMissingDeliverables()
        }, 2000)
      } else {
        console.error('Auto-completion failed:', result)
        setAutoCompletingTasks(prev => prev.filter(t => t !== taskKey))
      }
    } catch (error) {
      console.error('Auto-completion error:', error)
      setAutoCompletingTasks(prev => prev.filter(t => t !== taskKey))
    }

    // Helper function to reload missing deliverables
    const loadMissingDeliverables = async () => {
      try {
        const response = await fetch(`/api/auto-completion/workspace/${workspaceId}/missing-deliverables`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.missing_deliverables) {
            const formattedMissing: MissingDeliverableAlert[] = data.missing_deliverables.map((md: any) => ({
              goalId: md.goal_id,
              goalTitle: md.goal_title,
              missingDeliverables: md.missing_deliverables,
              progress: Math.round(md.progress_percentage || 0),
              canAutoComplete: md.can_auto_complete,
              blockedReason: md.blocked_reason
            }))
            setMissingDeliverables(formattedMissing)
          }
        }
      } catch (error) {
        console.error('Error reloading missing deliverables:', error)
      }
    }
  }

  const handleUnblock = async (goalId: string) => {
    try {
      // Call backend API to unblock stuck tasks
      const response = await fetch(`/api/auto-completion/goals/${goalId}/unblock`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workspace_id: workspaceId
        })
      })

      if (response.ok) {
        refetch()
        // Refresh missing deliverables to update blocked status
        const loadMissingDeliverables = async () => {
          try {
            const response = await fetch(`/api/auto-completion/workspace/${workspaceId}/missing-deliverables`)
            if (response.ok) {
              const data = await response.json()
              if (data.success && data.missing_deliverables) {
                const formattedMissing: MissingDeliverableAlert[] = data.missing_deliverables.map((md: any) => ({
                  goalId: md.goal_id,
                  goalTitle: md.goal_title,
                  missingDeliverables: md.missing_deliverables,
                  progress: Math.round(md.progress_percentage || 0),
                  canAutoComplete: md.can_auto_complete,
                  blockedReason: md.blocked_reason
                }))
                setMissingDeliverables(formattedMissing)
              }
            }
          } catch (error) {
            console.error('Error reloading missing deliverables:', error)
          }
        }
        loadMissingDeliverables()
      }
    } catch (error) {
      console.error('Unblock error:', error)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
          <div className="h-6 w-1/3 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 w-full bg-gray-200 rounded"></div>
            <div className="h-4 w-2/3 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center text-red-500">
        <div className="text-4xl mb-2">❌</div>
        <p className="mb-4">{error}</p>
        <button
          onClick={refetch}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!deliverables) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        <p>No deliverables available</p>
      </div>
    )
  }

  // Extract actionable assets from final deliverables
  const actionableAssets: Record<string, any> = {}
  
  deliverables.key_outputs
    .filter(output => output.type === 'final_deliverable')
    .forEach(output => {
      if (output.result?.actionable_assets) {
        Object.assign(actionableAssets, output.result.actionable_assets)
      }
    })

  const finalDeliverables = deliverables.key_outputs.filter(
    (o) => o.type === 'final_deliverable' || o.category === 'final_deliverable'
  )

  const hasActionableAssets = Object.keys(actionableAssets).length > 0

  return (
    <div className="space-y-6">
      {/* Missing Deliverables Alert - Auto-completion System */}
      {showMissingDeliverablesAlert && missingDeliverables.length > 0 && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                <span className="text-xl">⚠️</span>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-amber-800 mb-2">
                Missing Deliverables Detected
              </h3>
              <div className="space-y-4">
                {missingDeliverables.map((alert) => (
                  <div key={alert.goalId} className="bg-white rounded-lg p-4 border border-amber-200">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-medium text-gray-900">{alert.goalTitle}</h4>
                        <p className="text-sm text-gray-600">{alert.progress}% complete</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-amber-600 bg-amber-100 px-2 py-1 rounded">
                          {alert.missingDeliverables.length} missing
                        </span>
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <p className="text-sm text-gray-700 mb-2">Missing deliverables:</p>
                      <ul className="space-y-1">
                        {alert.missingDeliverables.map((deliverable, index) => (
                          <li key={index} className="flex items-center justify-between text-sm">
                            <span className="flex items-center space-x-2">
                              <span className="text-gray-400">•</span>
                              <span>{deliverable}</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              {autoCompletingTasks.includes(`${alert.goalId}-${deliverable}`) ? (
                                <span className="flex items-center space-x-2 text-blue-600">
                                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                                  <span className="text-xs">Auto-completing...</span>
                                </span>
                              ) : (
                                <button
                                  onClick={() => handleAutoComplete(alert.goalId, deliverable)}
                                  className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                                  disabled={!alert.canAutoComplete}
                                >
                                  Auto-complete
                                </button>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {!alert.canAutoComplete && alert.blockedReason && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                        <p className="text-sm text-red-700">
                          <strong>Blocked:</strong> {alert.blockedReason}
                        </p>
                        <button
                          onClick={() => handleUnblock(alert.goalId)}
                          className="mt-2 text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                        >
                          Unblock & Retry
                        </button>
                      </div>
                    )}

                    {alert.canAutoComplete && (
                      <div className="flex items-center space-x-2 text-sm text-green-700">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>System will automatically complete missing deliverables</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Business-Ready Assets - Claude Code Style */}
      {hasActionableAssets && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Business-Ready Assets</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(actionableAssets).map(([assetName, asset]) => {
              const assetAsOutput = {
                task_id: asset.source_task_id,
                task_name: assetName.replace(/_/g, ' ').toUpperCase(),
                title: assetName.replace(/_/g, ' ').toUpperCase(),
                output: `Business-ready ${assetName} asset with ${Object.keys(asset.asset_data || {}).length} data points`,
                summary: `Ready-to-use ${assetName} asset for immediate implementation`,
                type: 'final_deliverable',
                category: 'execution',
                agent_name: 'Asset Packager',
                agent_role: 'specialist',
                created_at: new Date().toISOString(),
                actionable_assets: {
                  [assetName]: asset
                },
                result: {
                  actionable_assets: {
                    [assetName]: asset
                  }
                },
                metrics: {
                  validation_score: Math.round((asset.validation_score || 0.8) * 100),
                  actionability_score: Math.round((asset.actionability_score || 0.9) * 100),
                  ready_to_use: asset.ready_to_use
                }
              }

              return (
                <DeliverableCard
                  key={assetName}
                  output={assetAsOutput}
                  workspaceId={workspaceId}
                  onViewDetails={() => {
                    // Handle asset view details
                    console.log('View asset details:', assetName, asset)
                  }}
                />
              )
            })}
          </div>
        </div>
      )}

      {/* Final Deliverables */}
      {finalDeliverables.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Final Deliverables</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {finalDeliverables.map(deliverable => (
              <DeliverableCard
                key={deliverable.task_id}
                output={deliverable}
                workspaceId={workspaceId}
                onViewDetails={() => {
                  // Handle deliverable view details
                  console.log('View deliverable details:', deliverable)
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasActionableAssets && finalDeliverables.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <div className="text-6xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No deliverables ready yet
          </h3>
          <p className="text-gray-600 mb-6">
            Deliverables will appear here as your team completes work and goals are achieved.
          </p>
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span>System actively working on your goals...</span>
          </div>
        </div>
      )}
    </div>
  )
}