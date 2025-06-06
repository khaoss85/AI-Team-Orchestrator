'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, ProjectOutputExtended, Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'
import { useAssetManagement } from '@/hooks/useAssetManagement'
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables'
import ActionableHeroSection from '@/components/redesign/ActionableHeroSection'
import MissionControlSection from '@/components/redesign/MissionControlSection'
import DeliverableCard from '@/components/redesign/DeliverableCard'
import EnhancedDetailsDrillDown from '@/components/EnhancedDetailsDrillDown'
import ExecutionDetailsModal from '@/components/redesign/ExecutionDetailsModal'
import RationaleModal from '@/components/redesign/RationaleModal'
import InteractionPanel from '@/components/redesign/InteractionPanel'
import ActionableAssetCard from '@/components/ActionableAssetCard'
import SmartAssetViewer from '@/components/SmartAssetViewer'

interface Props {
  params: Promise<{ id: string }>
}

export default function ModernProjectPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise)
  const id = params.id

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const {
    finalDeliverables,
    deliverables: assetDeliverables,
    assets,
    assetDisplayData,
    getAssetCompletionStats,
    loading: assetsLoading,
    error: assetError
  } = useAssetManagement(id)

  const {
    deliverables,
    loading: deliverablesLoading,
    error: deliverablesError,
    refetch: refetchDeliverables,
    finalDeliverables: projectFinalDeliverables,
    hasFinalDeliverables,
    finalDeliverablesCount
  } = useProjectDeliverables(id)

  const [selectedOutput, setSelectedOutput] = useState<ProjectOutputExtended | null>(null)
  const [executionOutput, setExecutionOutput] = useState<ProjectOutputExtended | null>(null)
  const [rationaleOutput, setRationaleOutput] = useState<ProjectOutputExtended | null>(null)
  const [selectedAsset, setSelectedAsset] = useState<any>(null)
  const [showAssetDetails, setShowAssetDetails] = useState(false)
  const [showAssetInteraction, setShowAssetInteraction] = useState(false)

  // Data for Mission Control section
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [budgetData, setBudgetData] = useState<any>(null)
  const [missionLoading, setMissionLoading] = useState(true)
  const [missionError, setMissionError] = useState<string | null>(null)
  
  // Emergency timeout to prevent infinite loading
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (missionLoading) {
        console.log('Emergency timeout: forcing mission loading to false')
        setMissionLoading(false)
        setMissionError('Timeout - using default values')
      }
    }, 12000) // 12 seconds emergency timeout
    
    return () => clearTimeout(timeout)
  }, [missionLoading])
  
  // Project completion tracking
  const [completionPercentage, setCompletionPercentage] = useState(0)
  const [finalizationStatus, setFinalizationStatus] = useState<any>(null)

  const fetchMissionControl = async () => {
    try {
      console.log('Starting mission control fetch for workspace:', id)
      setMissionLoading(true)
      setMissionError(null)
      
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      )
      
      const dataPromise = Promise.all([
        api.agents.list(id),
        api.humanFeedback.getPendingRequests(id),
        api.monitoring.getTaskAnalysis(id),
        api.monitoring.getWorkspaceBudget(id).catch(() => null) // Budget is optional
      ])
      
      const [agentsData, feedbackData, analysisData, budgetResponse] = await Promise.race([
        dataPromise,
        timeoutPromise
      ]) as [Agent[], FeedbackRequest[], TaskAnalysisResponse, any]
      
      console.log('Mission control data loaded:', { agentsData, feedbackData, analysisData, budgetResponse })
      setAgents(agentsData || [])
      setFeedback(feedbackData || [])
      setTaskAnalysis(analysisData || null)
      setBudgetData(budgetResponse)
      setMissionError(null)
    } catch (e: any) {
      console.error('Mission control fetch error:', e)
      setMissionError(e.message || 'Errore caricamento mission control')
      // Set default values even on error
      setAgents([])
      setFeedback([])
      setTaskAnalysis(null)
    } finally {
      console.log('Mission control fetch completed, setting loading to false')
      setMissionLoading(false)
    }
  }
  
  const fetchProjectCompletion = async () => {
    try {
      const finalizationData = await api.monitoring.getFinalizationStatus(id)
      setFinalizationStatus(finalizationData)
      setCompletionPercentage(finalizationData.project_completion_percentage || 0)
    } catch (e: any) {
      console.log('Project completion data not available:', e.message)
      // Calculate fallback completion based on available data
      if (taskAnalysis) {
        const completedTasks = taskAnalysis.completed_tasks_count || 0
        const totalTasks = taskAnalysis.total_tasks_count || 1
        setCompletionPercentage(Math.round((completedTasks / totalTasks) * 100))
      }
    }
  }

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        await fetchMissionControl()
        await fetchProjectCompletion()
      } catch (error) {
        console.error('Error loading initial data:', error)
      }
    }
    
    loadInitialData()
    
    // Set up auto-refresh for mission control and completion
    const interval = setInterval(() => {
      fetchMissionControl()
      fetchProjectCompletion()
      refetchDeliverables() // Also refresh deliverables
    }, 45000) // Every 45 seconds to reduce flickering
    
    return () => clearInterval(interval)
  }, [id])

  useEffect(() => {
    fetchWorkspace()
  }, [id])

  const fetchWorkspace = async () => {
    try {
      setLoading(true)
      const data = await api.workspaces.get(id)
      setWorkspace(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Impossibile caricare il progetto')
    } finally {
      setLoading(false)
    }
  }


  if (loading || assetsLoading) {
    return (
      <div className="container mx-auto py-20 text-center">Caricamento progetto...</div>
    )
  }

  if (error || assetError || !workspace) {
    return (
      <div className="container mx-auto py-20 text-center text-red-600">
        {error || assetError || 'Progetto non trovato'}
      </div>
    )
  }

  const assetStats = getAssetCompletionStats()
  
  // Asset management handlers
  const handleViewAssetDetails = (asset: any) => {
    setSelectedAsset(asset)
    setShowAssetDetails(true)
  }

  const handleInteractWithAsset = (asset: any) => {
    setSelectedAsset(asset)
    setShowAssetInteraction(true)
  }

  const handleDownloadAsset = (asset: any) => {
    // Create downloadable content
    const assetContent = JSON.stringify(asset.asset_data, null, 2)
    const blob = new Blob([assetContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${asset.asset_name}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container mx-auto space-y-6">
      <Link href="/projects" className="text-indigo-600 hover:underline text-sm">← Progetti</Link>
      <ActionableHeroSection 
        workspace={workspace} 
        assetStats={assetStats} 
        finalDeliverables={finalDeliverablesCount}
        completionPercentage={completionPercentage}
        finalizationStatus={finalizationStatus}
      />

      {/* Simple Navigation */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">{workspace?.name || 'Project'}</h1>
          <Link
            href={`/projects/${id}/results`}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            View Results
          </Link>
        </div>
        <p className="text-gray-600 mt-1">{workspace?.description}</p>
      </div>

      <MissionControlSection
        workspaceId={id}
        agents={agents}
        feedback={feedback}
        taskAnalysis={taskAnalysis}
        loading={missionLoading}
        error={missionError}
        onRefresh={fetchMissionControl}
      />

      {/* Project Components - Work in Progress */}
      <div className="mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Project Components</h2>
              <p className="text-sm text-gray-600">
                {deliverables && deliverables.key_outputs?.length > 0 
                  ? `${deliverables.key_outputs.filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable').length} components in development`
                  : 'Components will appear as work progresses'
                }
                {deliverablesLoading && <span className="ml-2">(Loading...)</span>}
                {deliverablesError && <span className="ml-2 text-red-500">(Error)</span>}
              </p>
            </div>
            <Link
              href={`/projects/${id}/results`}
              className="text-blue-600 hover:text-blue-700 font-medium text-sm"
            >
              View all →
            </Link>
          </div>
          
          {deliverables && deliverables.key_outputs.length > 0 ? (
            <div className="space-y-3">
              {deliverables.key_outputs
                .filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable')
                .slice(0, 3)
                .map((output, index) => (
                  <div
                    key={`deliverable-${output.task_id}-${index}`}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setSelectedOutput(output)}
                  >
                    <div>
                      <h3 className="font-medium text-gray-900">{output.title || output.task_name}</h3>
                      <p className="text-sm text-gray-600 line-clamp-1">
                        {(output.output || output.summary || '').substring(0, 100)}...
                      </p>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      {output.structured_content && (
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs mr-2">Enhanced</span>
                      )}
                      <span>View →</span>
                    </div>
                  </div>
                ))
              }
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-gray-400 text-2xl mb-2">📄</div>
              <p className="text-sm">{deliverablesLoading ? 'Loading components...' : 'No components available yet'}</p>
            </div>
          )}
        </div>
      </div>

      {/* Business-Ready Assets - Ready for Use */}
      {assetDisplayData && assetDisplayData.length > 0 && (
        <div className="mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Business-Ready Assets</h2>
                <p className="text-sm text-gray-600">{assetDisplayData.length} assets ready to use immediately</p>
              </div>
              <Link
                href={`/projects/${id}/results?filter=readyToUse`}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View all →
              </Link>
            </div>
            
            <div className="space-y-3">
              {assetDisplayData.slice(0, 3).map((assetData, index) => (
                <div
                  key={`asset-${assetData.asset.asset_name}-${index}`}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleViewAssetDetails(assetData.asset)}
                >
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {assetData.asset.asset_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-1">
                      {assetData.asset.usage_instructions || 'Ready for immediate deployment'}
                    </p>
                  </div>
                  <span className="text-sm text-blue-600">Ready to use →</span>
                </div>
              ))}
            </div>
            
            {assetDisplayData.length > 3 && (
              <div className="mt-4 text-center">
                <Link
                  href={`/projects/${id}/results?filter=readyToUse`}
                  className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                >
                  View {assetDisplayData.length - 3} more ready assets
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Project Completed - Final Summary */}
      {hasFinalDeliverables && projectFinalDeliverables.length > 0 && (
        <div className="mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Project Completed</h2>
              <p className="text-gray-600">
                {workspace?.goal || workspace?.description || 'All objectives accomplished successfully'}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6 text-center">
              <div>
                <div className="text-xl font-bold text-gray-900">{projectFinalDeliverables.length}</div>
                <div className="text-sm text-gray-600">Final deliverables</div>
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900">{assetDisplayData?.length || 0}</div>
                <div className="text-sm text-gray-600">Ready assets</div>
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900">{taskAnalysis?.task_counts?.completed || 0}</div>
                <div className="text-sm text-gray-600">Tasks completed</div>
              </div>
            </div>

            <div className="space-y-4">
              {projectFinalDeliverables.map((output, index) => (
                <div 
                  key={`final-${output.task_id}-${index}`} 
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => setSelectedOutput(output)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{output.title || output.task_name}</h3>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {(output.output || output.summary || '').substring(0, 150)}...
                      </p>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      {output.structured_content && (
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs mr-2">
                          Enhanced
                        </span>
                      )}
                      <span>View →</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center mt-6 pt-6 border-t border-gray-200">
              <Link
                href={`/projects/${id}/results`}
                className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
              >
                View complete project results
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}


      {selectedOutput && (
        <EnhancedDetailsDrillDown
          output={selectedOutput}
          workspaceId={id}
          onClose={() => setSelectedOutput(null)}
        />
      )}
      {executionOutput && (
        <ExecutionDetailsModal
          output={executionOutput}
          onClose={() => setExecutionOutput(null)}
        />
      )}
      {rationaleOutput && (
        <RationaleModal
          rationale={rationaleOutput.rationale || ''}
          onClose={() => setRationaleOutput(null)}
        />
      )}
      
      {/* Asset Viewer Modal - Smart Viewer */}
      {showAssetDetails && selectedAsset && (
        <SmartAssetViewer
          asset={selectedAsset}
          onClose={() => setShowAssetDetails(false)}
          onDownload={handleDownloadAsset}
          onRefine={handleInteractWithAsset}
        />
      )}
      
      {showAssetInteraction && selectedAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">Interact with Asset</h2>
                  <p className="opacity-90">Request modifications for {selectedAsset.asset_name}</p>
                </div>
                <button 
                  onClick={() => setShowAssetInteraction(false)} 
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6">
              <p className="text-gray-600">Asset interaction feature coming soon! This will allow you to refine and modify your business assets with AI assistance.</p>
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowAssetInteraction(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
