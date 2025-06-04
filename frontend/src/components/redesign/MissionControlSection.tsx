'use client'
import React, { useEffect, useState } from 'react'
import { api } from '@/utils/api'
import type { Workspace, Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'

interface Props {
  workspace: Workspace
}
const MissionControlSection: React.FC<Props> = ({ workspace }) => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState<FeedbackRequest[]>([])
  const [taskAnalysis, setTaskAnalysis] = useState<TaskAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [agentsData, feedbackData, analysisData] = await Promise.all([
        api.agents.list(workspace.id),
        api.humanFeedback.getPendingRequests(workspace.id),
        api.monitoring.getTaskAnalysis(workspace.id)
      ])
      setAgents(agentsData)
      setFeedback(feedbackData)
      setTaskAnalysis(analysisData)
      setError(null)
    } catch (e: any) {
      console.error(e)
      setError(e.message || 'Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [workspace.id])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center">Caricamento mission control...</div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center text-red-600">
        {error}
        <div className="mt-2">
          <button className="text-indigo-600" onClick={fetchData}>Riprova</button>
        </div>
      </div>
    )
  }

  const taskCounts = taskAnalysis?.task_counts || {}
  const totalTasks = Object.values(taskCounts).reduce((a, b) => a + b, 0)

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 space-y-4">
      <div className="flex justify-between">
        <h2 className="text-lg font-semibold">Mission Control</h2>
        <button className="text-sm text-indigo-600" onClick={fetchData}>Aggiorna</button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <div>
          <div className="font-medium">Agenti</div>
          <div>{agents.length}</div>
        </div>
        <div>
          <div className="font-medium">Richieste feedback</div>
          <div>{feedback.length}</div>
        </div>
        <div>
          <div className="font-medium">Task totali</div>
          <div>{totalTasks}</div>
        </div>
      </div>
    </div>
  )
}

export default MissionControlSection
