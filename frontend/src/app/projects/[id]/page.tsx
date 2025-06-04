'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type {
  Workspace,
  Agent,
  FeedbackRequest,
  TaskAnalysisResponse,
  ProjectOutputExtended
} from '@/types'
import { useAssetManagement } from '@/hooks/useAssetManagement'
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables'
import ActionableHeroSection from '@/components/redesign/ActionableHeroSection'
import MissionControlSection from '@/components/redesign/MissionControlSection'
import DeliverableCard from '@/components/redesign/DeliverableCard'
import DetailsDrillDown from '@/components/redesign/DetailsDrillDown'
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
    getAssetCompletionStats,
    loading: assetsLoading,
    error: assetError
  } = useAssetManagement(id)

  const {
    deliverables,
    loading: deliverablesLoading,
    error: deliverablesError,
    refetch: refetchDeliverables
  } = useProjectDeliverables(id)

  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [missionLoading, setMissionLoading] = useState(true)
  const [missionError, setMissionError] = useState<string | null>(null)

  const [selectedOutput, setSelectedOutput] = useState<ProjectOutputExtended | null>(null)

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

  const fetchMissionControl = async () => {
    try {
      setMissionLoading(true)
      const [agentsData, feedbackData, analysisData] = await Promise.all([
        api.agents.list(id),
        api.humanFeedback.getPendingRequests(id),
        api.monitoring.getTaskAnalysis(id)
      ])
      setAgents(agentsData)
      setFeedback(feedbackData)
      setTaskAnalysis(analysisData)
      setMissionError(null)
    } catch (e: any) {
      console.error(e)
      setMissionError(e.message || 'Errore nel caricamento dei dati')
    } finally {
      setMissionLoading(false)
    }
  }

  useEffect(() => {
    fetchMissionControl()
  }, [id])

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
      <ActionableHeroSection workspace={workspace} assetStats={assetStats} finalDeliverables={finalDeliverables.length} />
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {deliverablesLoading && <div>Caricamento deliverable...</div>}
        {deliverablesError && <div className="text-red-600">{deliverablesError}</div>}
        {!deliverablesLoading && deliverables && deliverables.key_outputs.map((output, idx) => (
          <DeliverableCard
            key={`${output.task_id}-${idx}`}
            output={output}
            workspaceId={id}
            onViewDetails={() => setSelectedOutput(output)}
          />
        ))}
      </div>

      {selectedOutput && (
        <DetailsDrillDown
          output={selectedOutput}
          workspaceId={id}
          onClose={() => setSelectedOutput(null)}
        />
      )}
    </div>
  )
}
