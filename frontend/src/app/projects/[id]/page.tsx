'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, ProjectOutputExtended, Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'
import { useAssetManagement } from '@/hooks/useAssetManagement'
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
    deliverables,
    getAssetCompletionStats,
    loading: assetsLoading,
    error: assetError
  } = useAssetManagement(id)

  const [selectedOutput, setSelectedOutput] = useState<ProjectOutputExtended | null>(null)

  // Data for Mission Control section
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [missionLoading, setMissionLoading] = useState(true)
  const [missionError, setMissionError] = useState<string | null>(null)

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
      setMissionError(e.message || 'Errore caricamento mission control')
    } finally {
      setMissionLoading(false)
    }
  }

  useEffect(() => {
    fetchMissionControl()
  }, [id])

  useEffect(() => {
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

    fetchWorkspace()
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
        {deliverables && deliverables.key_outputs.map(output => (
          <DeliverableCard
            key={output.task_id}
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
