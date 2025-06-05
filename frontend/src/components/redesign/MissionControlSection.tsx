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
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 space-y-4">
      <div className="flex justify-between">
        <h2 className="text-lg font-semibold">Mission Control</h2>
        <div className="flex items-center space-x-2">
          {loading && initialized && (
            <span className="text-sm text-gray-500">Updating...</span>
          )}
          <button className="text-sm text-indigo-600" onClick={onRefresh}>Aggiorna</button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
        {/* Team Panel */}
        <div className="group relative rounded-xl p-5 text-white bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-600 shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 overflow-hidden">
          {/* Glassmorphism background decorations */}
          <div className="absolute inset-0 opacity-20 group-hover:opacity-30 transition-opacity">
            <div className="absolute top-0 right-0 w-16 h-16 bg-white rounded-full -translate-y-8 translate-x-8 group-hover:scale-110 transition-transform"></div>
            <div className="absolute bottom-0 left-0 w-12 h-12 bg-white rounded-full translate-y-6 -translate-x-6 group-hover:scale-125 transition-transform"></div>
          </div>
          
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="text-xs uppercase opacity-80 tracking-wide font-medium">👥 Team Control</div>
                <div className="text-2xl font-bold mt-1">{totalAgents}</div>
                <div className="text-xs opacity-90 mt-1">
                  {activeAgents} active · {healthyAgents} healthy
                </div>
              </div>
              <div className="flex -space-x-2">
                {agents.slice(0, 4).map(agent => (
                  <div
                    key={agent.id}
                    className="w-9 h-9 rounded-full bg-white bg-opacity-25 backdrop-blur-sm border border-white/30 flex items-center justify-center text-xs font-bold hover:scale-110 transition-transform cursor-pointer"
                    title={agent.name}
                  >
                    {getInitials(agent.name)}
                  </div>
                ))}
                {agents.length > 4 && (
                  <div className="w-9 h-9 rounded-full bg-white bg-opacity-25 backdrop-blur-sm border border-white/30 flex items-center justify-center text-xs font-bold hover:scale-110 transition-transform">
                    +{agents.length - 4}
                  </div>
                )}
              </div>
            </div>
            <a
              href={`/projects/${workspaceId}/configure`}
              className="inline-flex items-center text-xs bg-white bg-opacity-20 backdrop-blur-sm px-3 py-1.5 rounded-full hover:bg-opacity-30 transition-all duration-200 font-medium"
            >
              Manage Team
              <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>

        {/* Human Feedback Panel */}
        <div className="group relative rounded-xl p-5 text-white bg-gradient-to-br from-pink-500 via-rose-500 to-red-500 shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 overflow-hidden">
          {/* Glassmorphism background decorations */}
          <div className="absolute inset-0 opacity-20 group-hover:opacity-30 transition-opacity">
            <div className="absolute top-0 left-0 w-20 h-20 bg-white rounded-full -translate-y-10 -translate-x-10 group-hover:scale-110 transition-transform"></div>
            <div className="absolute bottom-0 right-0 w-14 h-14 bg-white rounded-full translate-y-7 translate-x-7 group-hover:scale-125 transition-transform"></div>
          </div>
          
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="text-xs uppercase opacity-80 tracking-wide font-medium">💬 Human Feedback</div>
                <div className="text-2xl font-bold mt-1">
                  {feedback.length}
                  {feedback.length > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-red-400 text-red-900 text-xs font-bold rounded-full animate-pulse">
                      PENDING
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="mb-3 space-y-2">
              {feedback.length === 0 ? (
                <div className="text-xs opacity-75 bg-white bg-opacity-15 backdrop-blur-sm rounded-lg p-2 border border-white/20">
                  ✅ All feedback resolved
                </div>
              ) : (
                feedback.slice(0, 2).map(req => (
                  <div key={req.id} className="flex justify-between items-center text-xs bg-white bg-opacity-15 backdrop-blur-sm rounded-lg p-2 border border-white/20">
                    <span className="truncate mr-2 font-medium">{req.title}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getPriorityColor(req.priority)}`}>
                      {req.priority}
                    </span>
                  </div>
                ))
              )}
            </div>
            
            <a 
              href="/human-feedback" 
              className="inline-flex items-center text-xs bg-white bg-opacity-20 backdrop-blur-sm px-3 py-1.5 rounded-full hover:bg-opacity-30 transition-all duration-200 font-medium"
            >
              Review All
              <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>

        {/* Logbook Panel */}
        <div className="group relative rounded-xl p-5 text-white bg-gradient-to-br from-emerald-500 via-teal-500 to-green-500 shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 overflow-hidden">
          {/* Glassmorphism background decorations */}
          <div className="absolute inset-0 opacity-20 group-hover:opacity-30 transition-opacity">
            <div className="absolute top-0 right-0 w-18 h-18 bg-white rounded-full -translate-y-9 translate-x-9 group-hover:scale-110 transition-transform"></div>
            <div className="absolute bottom-0 left-0 w-16 h-16 bg-white rounded-full translate-y-8 -translate-x-8 group-hover:scale-125 transition-transform"></div>
          </div>
          
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="text-xs uppercase opacity-80 tracking-wide font-medium">📋 Task Logbook</div>
                <div className="text-2xl font-bold mt-1">{totalTasks}</div>
                <div className="text-xs opacity-90 mt-1">
                  {completedTasks} completed · {failedTasks} failed
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs opacity-80">Success Rate</div>
                <div className="text-lg font-bold">{successRate}%</div>
              </div>
            </div>
            
            <div className="mb-3">
              <div className="w-full bg-white bg-opacity-25 backdrop-blur-sm rounded-full h-2.5 border border-white/30">
                <div
                  className="bg-white h-2.5 rounded-full shadow-lg transition-all duration-1000 ease-out"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>
            
            <a
              href={`/projects/${workspaceId}/tasks`}
              className="inline-flex items-center text-xs bg-white bg-opacity-20 backdrop-blur-sm px-3 py-1.5 rounded-full hover:bg-opacity-30 transition-all duration-200 font-medium"
            >
              View Details
              <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MissionControlSection
