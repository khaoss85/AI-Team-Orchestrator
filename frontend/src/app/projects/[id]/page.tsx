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

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <Link
            href={`/projects/${id}`}
            className="py-2 px-1 border-b-2 border-indigo-500 font-medium text-sm text-indigo-600"
          >
            Overview
          </Link>
          <Link
            href={`/projects/${id}/results`}
            className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
          >
            📊 Unified Results
          </Link>
          <Link
            href={`/projects/${id}/tasks`}
            className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
          >
            Tasks
          </Link>
          <Link
            href={`/projects/${id}/team`}
            className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
          >
            Team
          </Link>
        </nav>
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
      <InteractionPanel workspace={workspace} onWorkspaceUpdate={setWorkspace} />

      {/* Enhanced Mission Control with Results Integration */}
      <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border border-blue-200 rounded-xl p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white text-xl mr-4">
              📊
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Smart Results Dashboard</h3>
              <p className="text-sm text-gray-600">Your assets now feature AI-powered markup and instant visualization</p>
            </div>
          </div>
          <Link
            href={`/projects/${id}/results`}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg text-sm font-medium hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            View Unified Results ⚡
          </Link>
        </div>
        
        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
            <div className="text-2xl font-bold text-green-600">{assetDisplayData?.length || 0}</div>
            <div className="text-xs text-gray-600 font-medium">Ready Assets</div>
            <div className="text-xs text-green-600">⚡ Instant view</div>
          </div>
          <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
            <div className="text-2xl font-bold text-purple-600">{deliverables?.key_outputs?.length || 0}</div>
            <div className="text-xs text-gray-600 font-medium">Deliverables</div>
            <div className="text-xs text-purple-600">🎨 AI Markup</div>
          </div>
          <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
            <div className="text-2xl font-bold text-blue-600">{finalDeliverablesCount}</div>
            <div className="text-xs text-gray-600 font-medium">Final Results</div>
            <div className="text-xs text-blue-600">🏆 Complete</div>
          </div>
          <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
            <div className="text-2xl font-bold text-indigo-600">{Math.round(completionPercentage)}%</div>
            <div className="text-xs text-gray-600 font-medium">Quality Score</div>
            <div className="text-xs text-indigo-600">📈 Business Ready</div>
          </div>
        </div>
      </div>

      {/* Business-Ready Assets Section - Enhanced */}
      {assetDisplayData && assetDisplayData.length > 0 && (
        <div className="mb-8">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-white text-lg mr-3">
                  ⚡
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Your Business-Ready Assets</h2>
                  <p className="text-green-700 text-sm">
                    {assetDisplayData.length} assets with AI-powered markup ready for immediate use
                  </p>
                </div>
              </div>
              <Link
                href={`/projects/${id}/results?filter=readyToUse`}
                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
              >
                View All Assets →
              </Link>
            </div>
            
            {/* Preview Grid - Show first 3 assets with enhanced preview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {assetDisplayData.slice(0, 3).map((assetData, index) => (
                <div
                  key={`asset-preview-${assetData.asset.asset_name}-${index}`}
                  className="bg-white rounded-lg border border-green-200 p-4 hover:shadow-lg transition-all cursor-pointer"
                  onClick={() => handleViewAssetDetails(assetData.asset)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center text-green-600 text-sm mr-2">
                        📋
                      </div>
                      <h3 className="font-medium text-gray-900 text-sm truncate">
                        {assetData.asset.asset_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h3>
                    </div>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Ready</span>
                  </div>
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                    {assetData.asset.usage_instructions || 'Business asset ready for immediate deployment'}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-green-600 font-medium">⚡ Instant view</span>
                    <span className="text-xs text-gray-500">Click to explore</span>
                  </div>
                </div>
              ))}
            </div>
            
            {assetDisplayData.length > 3 && (
              <div className="mt-4 text-center">
                <Link
                  href={`/projects/${id}/results?filter=readyToUse`}
                  className="text-green-600 text-sm hover:text-green-700 font-medium"
                >
                  View {assetDisplayData.length - 3} more business-ready assets →
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Project Completion Summary - Enhanced with Goals & Budget */}
      {hasFinalDeliverables && projectFinalDeliverables.length > 0 && (
        <div className="mb-8">
          <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border border-green-300 rounded-xl p-8 shadow-lg">
            {/* Header with Success Badge */}
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-3xl mx-auto mb-4 shadow-lg">
                🎯
              </div>
              <div className="inline-flex items-center bg-green-600 text-white px-4 py-2 rounded-full text-sm font-bold mb-3 shadow-md">
                ✅ PROJECT COMPLETED
              </div>
              <h2 className="text-3xl font-bold text-green-800 mb-2">Mission Accomplished!</h2>
              <p className="text-green-700 text-lg max-w-3xl mx-auto">
                Your AI team has successfully completed the project and delivered comprehensive results with AI-enhanced markup.
              </p>
            </div>

            {/* Project Summary Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Original Goal */}
              <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-xl p-6 border border-green-200">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600 text-lg mr-3">
                    📋
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Original Goal</h3>
                </div>
                <p className="text-gray-700 text-sm leading-relaxed">
                  {workspace?.goal || workspace?.description || 'Complete project objectives and deliver actionable business assets.'}
                </p>
              </div>

              {/* Budget Summary */}
              <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-xl p-6 border border-green-200">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600 text-lg mr-3">
                    💰
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Budget Performance</h3>
                </div>
                <div className="space-y-2">
                  {workspace?.budget && budgetData ? (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Budget:</span>
                        <span className="font-semibold text-gray-900">
                          {workspace.budget.currency} {workspace.budget.max_amount}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Spent:</span>
                        <span className="font-semibold text-gray-700">
                          {workspace.budget.currency} {budgetData.total_spent || 0}
                        </span>
                      </div>
                      <div className="w-full bg-green-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                          style={{ 
                            width: `${Math.min(100, ((budgetData.total_spent || 0) / workspace.budget.max_amount) * 100)}%` 
                          }}
                        />
                      </div>
                      <p className="text-xs text-green-600 font-medium">
                        {((budgetData.total_spent || 0) / workspace.budget.max_amount) <= 1 
                          ? 'Project completed within budget' 
                          : 'Budget exceeded - project value delivered'
                        }
                      </p>
                    </>
                  ) : workspace?.budget ? (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Budget:</span>
                        <span className="font-semibold text-gray-900">
                          {workspace.budget.currency} {workspace.budget.max_amount}
                        </span>
                      </div>
                      <div className="w-full bg-green-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                          style={{ width: '75%' }}
                        />
                      </div>
                      <p className="text-xs text-green-600 font-medium">Project completed successfully</p>
                    </>
                  ) : (
                    <div className="text-center py-2">
                      <div className="text-2xl font-bold text-green-600">✅</div>
                      <p className="text-sm text-gray-600">Project completed</p>
                      <p className="text-xs text-green-600 font-medium">Value delivered as planned</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Results Summary */}
              <div className="bg-white bg-opacity-70 backdrop-blur-sm rounded-xl p-6 border border-green-200">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600 text-lg mr-3">
                    📊
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Results Delivered</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Final deliverables:</span>
                    <span className="font-bold text-green-600">{projectFinalDeliverables.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Ready assets:</span>
                    <span className="font-bold text-green-600">{assetDisplayData?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">AI markup:</span>
                    <span className="font-bold text-green-600">✅ Enhanced</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Project Timeline */}
            <div className="mb-8 bg-white bg-opacity-50 rounded-xl p-6 border border-green-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">⏱️ Project Timeline</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-lg mx-auto mb-2">
                    🚀
                  </div>
                  <div className="text-sm font-medium text-gray-900">Started</div>
                  <div className="text-xs text-gray-600">
                    {workspace?.created_at ? new Date(workspace.created_at).toLocaleDateString() : 'N/A'}
                  </div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-600 text-lg mx-auto mb-2">
                    ⚙️
                  </div>
                  <div className="text-sm font-medium text-gray-900">Development</div>
                  <div className="text-xs text-gray-600">
                    {taskAnalysis?.task_counts?.completed || 0} tasks completed
                  </div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-lg mx-auto mb-2">
                    ✅
                  </div>
                  <div className="text-sm font-medium text-gray-900">Completed</div>
                  <div className="text-xs text-gray-600">
                    {new Date().toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Final Deliverables Cards */}
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4 text-center">📋 Final Deliverables</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {projectFinalDeliverables.map((output, index) => (
                  <div key={`final-${output.task_id}-${index}`} className="transform hover:scale-105 transition-all duration-200">
                    <div className="bg-white rounded-xl border-2 border-green-300 shadow-lg hover:shadow-xl transition-all">
                      <DeliverableCard
                        output={output}
                        workspaceId={id}
                        onViewDetails={() => setSelectedOutput(output)}
                        onViewExecution={() => setExecutionOutput(output)}
                        onViewRationale={() => setRationaleOutput(output)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Call to Action */}
            <div className="text-center bg-white bg-opacity-50 rounded-xl p-6 border border-green-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">🚀 Explore Your Complete Results</h4>
              <p className="text-gray-600 text-sm mb-4">
                View all your assets, components, and deliverables in the enhanced unified results dashboard with AI-powered markup.
              </p>
              <Link
                href={`/projects/${id}/results`}
                className="inline-flex items-center bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-4 rounded-xl text-base font-semibold hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                View Complete Results Dashboard
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}
      
      {/* Project Assets & Components - Enhanced with Results Integration */}
      <div className="mb-8">
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center text-white text-lg mr-3">
                🎨
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {hasFinalDeliverables ? 'Project Assets & Components' : 'Project Deliverables'}
                </h2>
                <p className="text-purple-700 text-sm">
                  {deliverables && deliverables.key_outputs?.length > 0 
                    ? `${deliverables.key_outputs.filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable').length} components with AI-enhanced markup`
                    : 'Components will appear here as they become available'
                  }
                  {deliverablesLoading && <span className="ml-2 text-gray-500">(Loading...)</span>}
                  {deliverablesError && <span className="ml-2 text-red-500">(Error loading)</span>}
                </p>
              </div>
            </div>
            <Link
              href={`/projects/${id}/results?filter=inProgress`}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
            >
              View All Components →
            </Link>
          </div>
          
          {deliverables && deliverables.key_outputs.length > 0 ? (
            <>
              {/* Preview Grid - Show first 3 deliverables with enhanced preview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {deliverables.key_outputs
                  .filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable')
                  .slice(0, 3)
                  .map((output, index) => (
                    <div
                      key={`deliverable-preview-${output.task_id}-${index}`}
                      className="bg-white rounded-lg border border-purple-200 p-4 hover:shadow-lg transition-all cursor-pointer"
                      onClick={() => setSelectedOutput(output)}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 text-sm mr-2">
                            📄
                          </div>
                          <h3 className="font-medium text-gray-900 text-sm truncate">
                            {output.title || output.task_name}
                          </h3>
                        </div>
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                          {output.type === 'final_deliverable' ? 'Final' : 'Component'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                        {(output.output || output.summary || '').substring(0, 100)}...
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-purple-600 font-medium">
                          {output.structured_content ? '🎨 AI Markup' : '📝 Standard'}
                        </span>
                        <span className="text-xs text-gray-500">Click to explore</span>
                      </div>
                    </div>
                  ))
                }
              </div>
              
              {deliverables.key_outputs.filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable').length > 3 && (
                <div className="mt-4 text-center">
                  <Link
                    href={`/projects/${id}/results`}
                    className="text-purple-600 text-sm hover:text-purple-700 font-medium"
                  >
                    View {deliverables.key_outputs.filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable').length - 3} more components in unified results →
                  </Link>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-gray-500 bg-white bg-opacity-50 rounded-lg">
              <div className="text-gray-400 text-4xl mb-2">📄</div>
              <p>{deliverablesLoading ? 'Loading deliverables...' : 'No deliverables available yet'}</p>
              <p className="text-xs mt-1">Components will appear here as your AI team completes tasks</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Markup Features Showcase */}
      <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 border border-indigo-200 rounded-xl p-6 mb-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center text-white text-2xl mx-auto mb-4">
            🚀
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Enhanced with AI-Powered Markup</h3>
          <p className="text-gray-600 text-sm mb-4 max-w-2xl mx-auto">
            Your results now feature automatic markup generation, instant visualization, and beautiful formatting. 
            No more raw JSON - see professional presentations immediately.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
              <div className="text-xl mb-2">⚡</div>
              <div className="text-sm font-medium text-gray-900">Instant Display</div>
              <div className="text-xs text-gray-600">Pre-rendered HTML ready to view</div>
            </div>
            <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
              <div className="text-xl mb-2">🎨</div>
              <div className="text-sm font-medium text-gray-900">Beautiful Formatting</div>
              <div className="text-xs text-gray-600">Professional cards, tables, and layouts</div>
            </div>
            <div className="bg-white bg-opacity-60 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-50">
              <div className="text-xl mb-2">💼</div>
              <div className="text-sm font-medium text-gray-900">Business Ready</div>
              <div className="text-xs text-gray-600">Copy-paste ready for presentations</div>
            </div>
          </div>
          
          <Link
            href={`/projects/${id}/results`}
            className="inline-flex items-center bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg text-sm font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Explore Enhanced Results
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </div>

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
