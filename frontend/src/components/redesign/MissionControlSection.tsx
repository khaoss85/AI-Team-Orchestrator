'use client'
import React from 'react'
import type { Agent, FeedbackRequest, TaskAnalysisResponse } from '@/types'

interface Props {
  agents: Agent[]
  feedback: FeedbackRequest[]
  taskAnalysis: TaskAnalysisResponse | null
  loading: boolean
  error?: string | null
  onRefresh: () => void
}

const MissionControlSection: React.FC<Props> = ({ agents, feedback, taskAnalysis, loading, error, onRefresh }) => {
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

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 space-y-4">
      <div className="flex justify-between">
        <h2 className="text-lg font-semibold">Mission Control</h2>
        <button className="text-sm text-indigo-600" onClick={onRefresh}>Aggiorna</button>
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
