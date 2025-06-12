'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, ProjectOutputExtended, Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'
import { useAssetManagement } from '@/hooks/useAssetManagement'
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables'
import { useProjectResults } from '@/hooks/useProjectResults'
import ActionableHeroSection from '@/components/redesign/ActionableHeroSection'
import MissionControlSection from '@/components/redesign/MissionControlSection'
import DeliverableCard from '@/components/redesign/DeliverableCard'
import EnhancedDetailsDrillDown from '@/components/EnhancedDetailsDrillDown'
import ExecutionDetailsModal from '@/components/redesign/ExecutionDetailsModal'
import RationaleModal from '@/components/redesign/RationaleModal'
import InteractionPanel from '@/components/redesign/InteractionPanel'
import ActionableAssetCard from '@/components/ActionableAssetCard'
import SmartAssetViewer from '@/components/SmartAssetViewer'
import ProjectResultsOverview from '@/components/ProjectResultsOverview'
import GoalProgressTracker from '@/components/GoalProgressTracker'
import GoalValidationDashboard from '@/components/GoalValidationDashboard'

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

  const handleWorkspaceUpdate = (updatedWorkspace: Workspace) => {
    setWorkspace(updatedWorkspace)
    // Refresh other data that might be affected
    fetchMissionControl()
    // Note: refetchResults removed as it doesn't exist - data will refresh via useEffect
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
      <ActionableHeroSection 
        workspace={workspace} 
        assetStats={assetStats} 
        finalDeliverables={finalDeliverablesCount}
        completionPercentage={completionPercentage}
        finalizationStatus={finalizationStatus}
      />

      {/* 🎯 Goal-Driven System Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GoalProgressTracker 
          workspaceId={id}
          showValidation={true}
          autoRefresh={true}
        />
        <GoalValidationDashboard 
          workspaceId={id}
        />
      </div>

      <MissionControlSection
        workspaceId={id}
        agents={agents}
        feedback={feedback}
        taskAnalysis={taskAnalysis}
        budgetData={budgetData}
        loading={missionLoading}
        error={missionError}
        onRefresh={fetchMissionControl}
      />

      {/* Team Interaction Panel with Start Team button */}
      {workspace && (
        <InteractionPanel 
          workspace={workspace}
          onWorkspaceUpdate={handleWorkspaceUpdate}
          hasFinalDeliverables={hasFinalDeliverables}
          finalDeliverablesCount={finalDeliverablesCount}
        />
      )}

      {/* Unified Project Results Overview */}
      <ProjectResultsOverview projectId={id} />



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
