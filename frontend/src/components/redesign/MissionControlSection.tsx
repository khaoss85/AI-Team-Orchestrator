'use client'

import React, { useEffect, useState } from 'react'
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

const MissionControlSection: React.FC<Props> = ({ workspaceId, agents, feedback, taskAnalysis, loading, error, onRefresh }) => {

  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    setInitialized(true)

  }, [])
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
          <button className="text-indigo-600" onClick={onRefresh}>Riprova</button>
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
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Team Status</h2>
        {loading ? (
          <span className="text-sm text-gray-500">Loading...</span>
        ) : (
          <button className="text-sm text-blue-600 hover:text-blue-700" onClick={onRefresh}>
            Refresh
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-3 gap-6 text-center">
        {/* Team */}
        <div>
          <div className="text-xl font-bold text-gray-900">{totalAgents}</div>
          <div className="text-sm text-gray-600">Team Members</div>
          <div className="text-xs text-gray-500 mt-1">{activeAgents} active</div>
          <a href={`/projects/${workspaceId}/team`} className="text-xs text-blue-600 hover:text-blue-700 mt-1 block">
            Manage →
          </a>
        </div>

        {/* Feedback */}
        <div>
          <div className="text-xl font-bold text-gray-900">
            {feedback.length}
            {feedback.length > 0 && (
              <span className="ml-1 w-2 h-2 bg-red-500 rounded-full inline-block"></span>
            )}
          </div>
          <div className="text-sm text-gray-600">Pending Feedback</div>
          <div className="text-xs text-gray-500 mt-1">
            {feedback.length === 0 ? 'All resolved' : `${feedback.length} waiting`}
          </div>
          <a href="/human-feedback" className="text-xs text-blue-600 hover:text-blue-700 mt-1 block">
            Review →
          </a>
        </div>

        {/* Tasks */}
        <div>
          <div className="text-xl font-bold text-gray-900">{totalTasks}</div>
          <div className="text-sm text-gray-600">Total Tasks</div>
          <div className="text-xs text-gray-500 mt-1">{successRate}% success</div>
          <a href={`/projects/${workspaceId}/tasks`} className="text-xs text-blue-600 hover:text-blue-700 mt-1 block">
            View →
          </a>
        </div>
      </div>
    </div>
  )
}

export default MissionControlSection
