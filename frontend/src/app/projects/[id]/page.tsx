'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, Agent, FeedbackRequest, TaskAnalysisResponse, ProjectOutputExtended } from '@/types'
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

export default function ProjectPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise)
  const id = params.id

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [missionLoading, setMissionLoading] = useState(true)
  const [missionError, setMissionError] = useState<string | null>(null)

  const { getAssetCompletionStats } = useAssetManagement(id)
  const { deliverables, finalDeliverables, loading: deliverablesLoading, error: deliverablesError, refetch } = useProjectDeliverables(id)

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

  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent" />
            <p className="mt-4 text-gray-600">Caricamento progetto...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !workspace) {
    return (
      <div className="container mx-auto">
        <div className="bg-red-50 text-red-700 p-6 rounded-lg mb-6">
          {error || 'Progetto non trovato'}
        </div>
        <div className="flex space-x-4">
          <button onClick={() => window.location.reload()} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition">Riprova</button>
          <Link href="/projects" className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition">Torna ai progetti</Link>
        </div>
      </div>
    )
  }

  const assetStats = getAssetCompletionStats()

  return (
    <div className="container mx-auto space-y-6">
      <Link href="/projects" className="text-indigo-600 hover:underline text-sm">← Progetti</Link>
      <ActionableHeroSection workspace={workspace} assetStats={assetStats} finalDeliverables={finalDeliverables.length} />
      <MissionControlSection
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
        {!deliverablesLoading && deliverables && deliverables.key_outputs.map(output => (
          <DeliverableCard key={output.task_id} output={output} onViewDetails={() => setSelectedOutput(output)} />
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
