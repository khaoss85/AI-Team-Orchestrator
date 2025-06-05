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
import DetailsDrillDown from '@/components/redesign/DetailsDrillDown'
import ExecutionDetailsModal from '@/components/redesign/ExecutionDetailsModal'
import RationaleModal from '@/components/redesign/RationaleModal'
import InteractionPanel from '@/components/redesign/InteractionPanel'

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

  // Data for Mission Control section
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
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
        api.monitoring.getTaskAnalysis(id)
      ])
      
      const [agentsData, feedbackData, analysisData] = await Promise.race([
        dataPromise,
        timeoutPromise
      ]) as [Agent[], FeedbackRequest[], TaskAnalysisResponse]
      
      console.log('Mission control data loaded:', { agentsData, feedbackData, analysisData })
      setAgents(agentsData || [])
      setFeedback(feedbackData || [])
      setTaskAnalysis(analysisData || null)
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

      {/* Show final deliverables prominently if available */}
      {hasFinalDeliverables && projectFinalDeliverables.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4 text-green-800">🎯 Final Deliverables Ready</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {projectFinalDeliverables.map((output, index) => (
              <div key={`final-${output.task_id}-${index}`} className="transform scale-105">
                <DeliverableCard
                  output={output}
                  workspaceId={id}
                  onViewDetails={() => setSelectedOutput(output)}
                  onViewExecution={() => setExecutionOutput(output)}
                  onViewRationale={() => setRationaleOutput(output)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Regular deliverables grid */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-3">
          {hasFinalDeliverables ? 'Project Assets & Components' : 'Project Deliverables'}
          {deliverablesLoading && <span className="ml-2 text-sm text-gray-500">(Loading...)</span>}
          {deliverablesError && <span className="ml-2 text-sm text-red-500">(Error loading)</span>}
        </h2>
        
        {deliverables && deliverables.key_outputs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {deliverables.key_outputs
              .filter(output => output.type !== 'final_deliverable' && output.category !== 'final_deliverable')
              .map((output, index) => (
                <DeliverableCard
                  key={`${output.task_id}-${index}`}
                  output={output}
                  workspaceId={id}
                  onViewDetails={() => setSelectedOutput(output)}
                  onViewExecution={() => setExecutionOutput(output)}
                  onViewRationale={() => setRationaleOutput(output)}
                />
              ))
            }
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            {deliverablesLoading ? 'Loading deliverables...' : 'No deliverables available yet'}
          </div>
        )}
      </div>

      {selectedOutput && (
        <DetailsDrillDown
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
    </div>
  )
}
