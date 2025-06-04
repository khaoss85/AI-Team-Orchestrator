'use client'

import React, { useEffect, useState } from 'react'
import type { Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'
import { api } from '@/utils/api'

interface MissionControlSectionProps {
  workspaceId: string
}

const PanelWrapper: React.FC<React.PropsWithChildren<{ title: string; onRefresh: () => void }>> = ({ title, onRefresh, children }) => (
  <div className="bg-white rounded-lg p-4 border shadow-sm transition-all duration-300 hover:shadow-md hover:-translate-y-1 flex flex-col">
    <div className="flex justify-between items-center mb-2">
      <h3 className="font-semibold">{title}</h3>
      <button onClick={onRefresh} className="text-xs text-indigo-600 hover:underline">Aggiorna</button>
    </div>
    {children}
  </div>
)

const TeamControlPanel: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const data = await api.agents.list(workspaceId)
      setAgents(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Errore caricamento agenti')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [workspaceId])

  return (
    <PanelWrapper title="Team" onRefresh={fetchAgents}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center py-4">
          <div className="h-5 w-5 border-2 border-indigo-600 border-r-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : (
        <ul className="space-y-1 text-sm overflow-auto flex-1">
          {agents.map(agent => (
            <li key={agent.id} className="flex justify-between rounded hover:bg-gray-50 px-2 py-1 transition-colors">
              <span>{agent.name}</span>
              <span className="text-gray-500">{agent.status}</span>
            </li>
          ))}
        </ul>
      )}
    </PanelWrapper>
  )
}

const HumanFeedbackPanel: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const [requests, setRequests] = useState<FeedbackRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRequests = async () => {
    try {
      setLoading(true)
      const data = await api.humanFeedback.getPendingRequests(workspaceId)
      setRequests(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Errore caricamento feedback')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
    const id = setInterval(fetchRequests, 30000)
    return () => clearInterval(id)
  }, [workspaceId])

  return (
    <PanelWrapper title="Feedback Umano" onRefresh={fetchRequests}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center py-4">
          <div className="h-5 w-5 border-2 border-indigo-600 border-r-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : requests.length === 0 ? (
        <div className="text-sm text-gray-500 flex-1 flex items-center justify-center">Nessuna richiesta</div>
      ) : (
        <ul className="space-y-2 text-sm overflow-auto flex-1">
          {requests.slice(0, 5).map(req => (
            <li key={req.id} className="p-2 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors">
              <div className="font-medium">{req.title}</div>
              <div className="text-xs text-gray-500">{req.request_type.replace('_', ' ')}</div>
            </li>
          ))}
        </ul>
      )}
    </PanelWrapper>
  )
}

const LogbookPanel: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const [stats, setStats] = useState<TaskAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      const data = await api.monitoring.getTaskAnalysis(workspaceId)
      setStats(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Errore caricamento logbook')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [workspaceId])

  const totalTasks = stats ? Object.values(stats.task_counts || {}).reduce((a, b) => a + b, 0) : 0

  return (
    <PanelWrapper title="Logbook" onRefresh={fetchStats}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center py-4">
          <div className="h-5 w-5 border-2 border-indigo-600 border-r-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : stats ? (
        <div className="text-sm space-y-1">
          <div>Totale task: {totalTasks}</div>
          <div>Fail: {stats.failure_analysis.total_failures}</div>
          <div>Handoff: {stats.handoff_analysis.total_handoff_tasks}</div>
        </div>
      ) : null}
    </PanelWrapper>
  )
}

const MissionControlSection: React.FC<MissionControlSectionProps> = ({ workspaceId }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    <TeamControlPanel workspaceId={workspaceId} />
    <HumanFeedbackPanel workspaceId={workspaceId} />
    <LogbookPanel workspaceId={workspaceId} />
  </div>
)

export default MissionControlSection
