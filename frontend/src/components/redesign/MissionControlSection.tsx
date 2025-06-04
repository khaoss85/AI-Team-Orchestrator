'use client'

import React, { useEffect, useRef } from 'react'
import type { Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'

interface Props {
  workspaceId: string
  agents: Agent[]
  feedback: FeedbackRequest[]
  taskAnalysis: TaskAnalysisResponse | null
  loading: boolean
  error?: string | null
  onRefresh: () => void
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

const MissionControlSection: React.FC<Props> = ({ workspaceId, agents, feedback, taskAnalysis, loading, error, onRefresh }) => {
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
  const completedTasks = taskCounts.completed || 0
  const failedTasks = taskCounts.failed || 0
  const successRate = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0

  const totalAgents = agents.length
  const activeAgents = agents.filter(a => a.status === 'active').length
  const healthyAgents = agents.filter(a => a.health?.status === 'healthy').length

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getInitials = (name: string) => {
    const parts = name.split(' ')
    const initials = parts.map(p => p[0]).join('')
    return initials.slice(0, 2).toUpperCase()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 space-y-4">
      <div className="flex justify-between">
        <h2 className="text-lg font-semibold">Mission Control</h2>
        <div className="flex items-center space-x-2">
          {loading && initialized.current && (
            <span className="text-sm text-gray-500">Updating...</span>
          )}
          <button className="text-sm text-indigo-600" onClick={onRefresh}>Aggiorna</button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        {/* Team Panel */}
        <div className="rounded-lg p-4 text-white bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md hover:shadow-lg hover:-translate-y-1 transition">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-xs uppercase opacity-80">Team</div>
              <div className="text-xl font-bold">{totalAgents}</div>
              <div className="text-xs opacity-90">
                {activeAgents} attivi · {healthyAgents} healthy
              </div>
            </div>
            <div className="flex -space-x-2">
              {agents.slice(0, 4).map(agent => (
                <div
                  key={agent.id}
                  className="w-8 h-8 rounded-full bg-white bg-opacity-20 flex items-center justify-center text-xs font-semibold"
                >
                  {getInitials(agent.name)}
                </div>
              ))}
              {agents.length > 4 && (
                <div className="w-8 h-8 rounded-full bg-white bg-opacity-20 flex items-center justify-center text-xs font-semibold">
                  +{agents.length - 4}
                </div>
              )}
            </div>
          </div>
          <a
            href={`/projects/${workspaceId}/configure`}
            className="text-xs mt-2 inline-block hover:underline"
          >
            Manage →
          </a>
        </div>

        {/* Human Feedback Panel */}
        <div className="rounded-lg p-4 text-white bg-gradient-to-br from-pink-500 to-rose-600 shadow-md hover:shadow-lg hover:-translate-y-1 transition">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-xs uppercase opacity-80">Feedback</div>
              <div className="text-xl font-bold">{feedback.length}</div>
            </div>
          </div>
          <div className="mt-2 space-y-1">
            {feedback.slice(0, 2).map(req => (
              <div key={req.id} className="flex justify-between items-center text-xs">
                <span className="truncate mr-2">{req.title}</span>
                <span className={`px-2 py-0.5 rounded-full ${getPriorityColor(req.priority)}`}>{req.priority}</span>
              </div>
            ))}
          </div>
          <a href="/human-feedback" className="text-xs mt-2 inline-block hover:underline">
            Review →
          </a>
        </div>

        {/* Logbook Panel */}
        <div className="rounded-lg p-4 text-white bg-gradient-to-br from-emerald-500 to-green-600 shadow-md hover:shadow-lg hover:-translate-y-1 transition">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-xs uppercase opacity-80">Logbook</div>
              <div className="text-xl font-bold">{totalTasks}</div>
              <div className="text-xs opacity-90">
                {completedTasks} completi · {failedTasks} fail
              </div>
            </div>
          </div>
          <div className="w-full bg-white bg-opacity-20 rounded-full h-2 mt-3">
            <div
              className="bg-white h-2 rounded-full"
              style={{ width: `${successRate}%` }}
            />
          </div>
          <a
            href={`/projects/${workspaceId}/tasks`}
            className="text-xs mt-2 inline-block hover:underline"
          >
            View All →
          </a>
        </div>
      </div>
    </div>
  )
}

export default MissionControlSection
