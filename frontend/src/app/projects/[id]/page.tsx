'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables'
import { useUnifiedAssets } from '@/hooks/useUnifiedAssets'
import ProjectNavigationTabs from '@/components/ProjectNavigationTabs'
import ConcreteDeliverablesOverview from '@/components/ConcreteDeliverablesOverview'
import GoalProgressTracker from '@/components/GoalProgressTracker'
import MissionControlSection from '@/components/redesign/MissionControlSection'
import InteractionPanel from '@/components/redesign/InteractionPanel'
import SmartAssetViewer from '@/components/SmartAssetViewer'

interface Props {
  params: Promise<{ id: string }>
}

export default function SimplifiedProjectPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise)
  const id = params.id

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Simplified data hooks - focus only on deliverables and assets
  const {
    finalDeliverables,
    hasFinalDeliverables,
    finalDeliverablesCount,
    loading: deliverablesLoading
  } = useProjectDeliverables(id)

  const {
    assets,
    assetCount,
    loading: assetsLoading
  } = useUnifiedAssets(id)

  // Mission control data (simplified)
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [missionLoading, setMissionLoading] = useState(true)

  // Asset viewer state
  const [selectedAsset, setSelectedAsset] = useState<any>(null)
  const [showAssetDetails, setShowAssetDetails] = useState(false)

  const fetchMissionControl = async () => {
    try {
      setMissionLoading(true)
      
      const [agentsData, feedbackData, analysisData] = await Promise.all([
        api.agents.list(id).catch(() => []),
        api.humanFeedback.getPendingRequests(id).catch(() => []),
        api.monitoring.getTaskAnalysis(id).catch(() => null)
      ])
      
      setAgents(agentsData || [])
      setFeedback(feedbackData || [])
      setTaskAnalysis(analysisData || null)
    } catch (e: any) {
      console.error('Mission control fetch error:', e)
      setAgents([])
      setFeedback([])
      setTaskAnalysis(null)
    } finally {
      setMissionLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkspace()
    fetchMissionControl()
    
    // Handle hash fragment navigation for goal->asset linking
    if (window.location.hash === '#deliverables') {
      setTimeout(() => {
        const deliverablesSection = document.querySelector('[data-section="deliverables"]');
        if (deliverablesSection) {
          deliverablesSection.scrollIntoView({ behavior: 'smooth' });
        }
      }, 500); // Small delay to ensure components are loaded
    }
    
    // Simplified refresh interval
    const interval = setInterval(() => {
      fetchMissionControl()
    }, 30000) // Every 30 seconds
    
    return () => clearInterval(interval)
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

  const handleViewAssetDetails = (asset: any) => {
    // ✅ COMPATIBILITY: Convert unified asset to ActionableAsset format
    const actionableAsset = {
      asset_name: asset.name || asset.asset_name || 'Asset',
      name: asset.name || asset.asset_name || 'Asset',
      asset_data: asset.content || asset.asset_data || {},
      source_task_id: asset.sourceTaskId || '',
      extraction_method: asset.extraction_method || 'unified',
      validation_score: asset.quality_scores?.overall || 0.8,
      actionability_score: asset.business_actionability || 0.8,
      ready_to_use: asset.ready_to_use || true,
      // Keep original data for debugging
      _original: asset
    }
    
    console.log('🔍 [handleViewAssetDetails] Converting asset:', {
      original: asset,
      converted: actionableAsset
    });
    
    setSelectedAsset(actionableAsset)
    setShowAssetDetails(true)
  }

  const handleDownloadAsset = (asset: any) => {
    const assetContent = JSON.stringify(asset.asset_data || asset.content, null, 2)
    const blob = new Blob([assetContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${asset.asset_name || asset.name}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleWorkspaceUpdate = (updatedWorkspace: Workspace) => {
    setWorkspace(updatedWorkspace)
    fetchMissionControl()
  }

  if (loading || deliverablesLoading || assetsLoading) {
    return (
      <div className="container mx-auto py-20 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-4 text-gray-600">Caricamento progetto...</p>
      </div>
    )
  }

  if (error || !workspace) {
    return (
      <div className="container mx-auto py-20 text-center text-red-600">
        {error || 'Progetto non trovato'}
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Project Header - Simplified */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{workspace.name}</h1>
            <p className="text-gray-600 mt-2">{workspace.goal}</p>
            {workspace.status && (
              <span className={`inline-block mt-3 px-3 py-1 rounded-full text-sm font-medium ${
                workspace.status === 'active' ? 'bg-green-100 text-green-800' :
                workspace.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {workspace.status === 'active' ? '🚀 Attivo' :
                 workspace.status === 'completed' ? '✅ Completato' :
                 '⏳ In preparazione'}
              </span>
            )}
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">{assetCount}</div>
            <div className="text-sm text-gray-500">Asset Pronti</div>
            {finalDeliverablesCount > 0 && (
              <div className="mt-2">
                <div className="text-lg font-semibold text-green-600">{finalDeliverablesCount}</div>
                <div className="text-xs text-green-500">Deliverable Finali</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <ProjectNavigationTabs projectId={id} />

      {/* Goal Progress - Prominent Display */}
      <GoalProgressTracker 
        workspaceId={id}
        showValidation={true}
        autoRefresh={true}
        onViewAssets={() => {
          // Scroll to the deliverables section when View Assets is clicked
          const deliverablesSection = document.querySelector('[data-section="deliverables"]');
          if (deliverablesSection) {
            deliverablesSection.scrollIntoView({ behavior: 'smooth' });
          }
        }}
      />

      {/* Main Content: Focus on Concrete Deliverables */}
      <div data-section="deliverables">
        <ConcreteDeliverablesOverview 
          workspaceId={id}
          finalDeliverables={finalDeliverables}
          assets={assets}
          onViewAsset={handleViewAssetDetails}
          onDownloadAsset={handleDownloadAsset}
        />
      </div>

      {/* Mission Control - Simplified */}
      <MissionControlSection
        workspaceId={id}
        agents={agents}
        feedback={feedback}
        taskAnalysis={taskAnalysis}
        budgetData={null}
        loading={missionLoading}
        error={null}
        onRefresh={fetchMissionControl}
      />

      {/* Team Interaction Panel */}
      {workspace && (
        <InteractionPanel 
          workspace={workspace}
          onWorkspaceUpdate={handleWorkspaceUpdate}
          hasFinalDeliverables={hasFinalDeliverables}
          finalDeliverablesCount={finalDeliverablesCount}
        />
      )}

      {/* Asset Viewer Modal */}
      {showAssetDetails && selectedAsset && (
        <SmartAssetViewer
          asset={selectedAsset}
          onClose={() => setShowAssetDetails(false)}
          onDownload={handleDownloadAsset}
          onRefine={() => {
            // Asset refinement functionality
            console.log('Asset refinement requested for:', selectedAsset.name)
          }}
        />
      )}
    </div>
  )
}