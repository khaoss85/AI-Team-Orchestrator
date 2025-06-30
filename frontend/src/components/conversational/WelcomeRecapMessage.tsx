'use client'

import React, { useState, useEffect } from 'react'

interface WelcomeRecapMessageProps {
  workspaceId: string
  onDismiss?: () => void
}

interface WorkspaceData {
  id: string
  name: string
  description: string
  created_at: string
}

interface Goal {
  id: string
  description: string
  target_value: number
  metric_type: string
  priority: number
}

interface TeamMember {
  name: string
  role: string
  seniority: string
}

export default function WelcomeRecapMessage({ 
  workspaceId, 
  onDismiss 
}: WelcomeRecapMessageProps) {
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null)
  const [goals, setGoals] = useState<Goal[]>([])
  const [team, setTeam] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)

  // 🔄 Fetch workspace data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Fetch workspace info
        const workspaceResponse = await fetch(`/api/workspaces/${workspaceId}`)
        if (workspaceResponse.ok) {
          const workspaceData = await workspaceResponse.json()
          setWorkspace(workspaceData)
        }

        // Fetch goals
        const goalsResponse = await fetch(`/api/workspaces/${workspaceId}/goals`)
        if (goalsResponse.ok) {
          const goalsData = await goalsResponse.json()
          setGoals(goalsData || [])
        }

        // Fetch team (agents)
        const teamResponse = await fetch(`/agents/workspace/${workspaceId}`)
        if (teamResponse.ok) {
          const teamData = await teamResponse.json()
          const formattedTeam = teamData.map((agent: any) => ({
            name: agent.name || 'Unknown Agent',
            role: agent.role || 'Specialist',
            seniority: agent.seniority || 'junior'
          }))
          setTeam(formattedTeam)
        }

      } catch (error) {
        console.error('Error fetching welcome data:', error)
      } finally {
        setLoading(false)
      }
    }

    if (workspaceId) {
      fetchData()
    }
  }, [workspaceId])

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Loading workspace recap...</span>
        </div>
      </div>
    )
  }
  
  if (!workspace) {
    return null
  }
  
  // 🤖 AI-DRIVEN: Smart project development phase detection
  const detectDevelopmentPhase = () => {
    const goalCount = goals.length
    const teamSize = team.length
    
    if (goalCount === 0) {
      return { phase: 'initialization', icon: '🚀', description: 'Setting up project foundation' }
    } else if (goalCount <= 3) {
      return { phase: 'planning', icon: '📋', description: 'Defining objectives and strategy' }
    } else if (goalCount <= 6) {
      return { phase: 'development', icon: '🔨', description: 'Active development and implementation' }
    } else {
      return { phase: 'scaling', icon: '📈', description: 'Expanding and optimizing' }
    }
  }

  // 🎯 Prioritize most important goals to show
  const getTopGoals = () => {
    return goals
      .sort((a, b) => b.priority - a.priority)
      .slice(0, 3)
  }

  // 👥 Organize team by seniority for better display
  const organizeTeam = () => {
    const seniorityOrder = { 'expert': 3, 'senior': 2, 'junior': 1 }
    return team
      .sort((a, b) => (seniorityOrder[a.seniority as keyof typeof seniorityOrder] || 0) - 
                     (seniorityOrder[b.seniority as keyof typeof seniorityOrder] || 0))
      .slice(0, 4) // Show max 4 team members
  }

  const developmentPhase = detectDevelopmentPhase()
  const topGoals = getTopGoals()
  const organizedTeam = organizeTeam()

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6 relative">
      {/* Dismiss button */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss welcome message"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* 🎉 Welcome Header */}
      <div className="flex items-start space-x-4 mb-6">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-2xl shadow-sm">
            🎉
          </div>
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome to {workspace.name}!
          </h2>
          <p className="text-gray-700 leading-relaxed">
            Your AI-driven project is ready. Here's what we've set up for you:
          </p>
        </div>
      </div>

      {/* 📊 Project Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        
        {/* 🎯 Objectives */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center mb-3">
            <span className="text-lg mr-2">🎯</span>
            <h3 className="font-medium text-gray-900">Objectives</h3>
          </div>
          <div className="space-y-2">
            {topGoals.length > 0 ? (
              <>
                {topGoals.map((goal, index) => (
                  <div key={goal.id} className="text-sm">
                    <div className="font-medium text-gray-800 truncate">
                      {index + 1}. {goal.description}
                    </div>
                    <div className="text-gray-600">
                      Target: {goal.target_value} {goal.metric_type}
                    </div>
                  </div>
                ))}
                {goals.length > 3 && (
                  <div className="text-xs text-gray-500 mt-2">
                    +{goals.length - 3} more objectives
                  </div>
                )}
              </>
            ) : (
              <div className="text-sm text-gray-600">
                Goals will be extracted automatically from your project description
              </div>
            )}
          </div>
        </div>

        {/* 👥 Team */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center mb-3">
            <span className="text-lg mr-2">👥</span>
            <h3 className="font-medium text-gray-900">Team</h3>
          </div>
          <div className="space-y-2">
            {organizedTeam.length > 0 ? (
              <>
                {organizedTeam.map((member, index) => (
                  <div key={index} className="text-sm">
                    <div className="font-medium text-gray-800">
                      {member.name}
                    </div>
                    <div className="text-gray-600">
                      {member.seniority} {member.role}
                    </div>
                  </div>
                ))}
                {team.length > 4 && (
                  <div className="text-xs text-gray-500 mt-2">
                    +{team.length - 4} more members
                  </div>
                )}
              </>
            ) : (
              <div className="text-sm text-gray-600">
                AI Director will propose a specialized team for your project
              </div>
            )}
          </div>
        </div>

        {/* 📈 Development Phase */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center mb-3">
            <span className="text-lg mr-2">{developmentPhase.icon}</span>
            <h3 className="font-medium text-gray-900">Development</h3>
          </div>
          <div className="space-y-2">
            <div className="text-sm">
              <div className="font-medium text-gray-800 capitalize">
                {developmentPhase.phase} Phase
              </div>
              <div className="text-gray-600">
                {developmentPhase.description}
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Project created {new Date(workspace.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>

      {/* 🚀 Next Steps */}
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center">
          <span className="text-lg mr-2">🚀</span>
          What happens next?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-start">
              <span className="text-green-500 mr-2 mt-0.5">✓</span>
              <span className="text-gray-700">AI agents will start working on your objectives</span>
            </div>
            <div className="flex items-start">
              <span className="text-green-500 mr-2 mt-0.5">✓</span>
              <span className="text-gray-700">Tasks will be generated and executed automatically</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-start">
              <span className="text-blue-500 mr-2 mt-0.5">→</span>
              <span className="text-gray-700">Deliverables will appear as goals are completed</span>
            </div>
            <div className="flex items-start">
              <span className="text-blue-500 mr-2 mt-0.5">→</span>
              <span className="text-gray-700">Use this chat to monitor progress and give feedback</span>
            </div>
          </div>
        </div>
      </div>

      {/* 💬 CTA */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 mb-3">
          Your AI-driven project is now active. Ask me anything or let the system work autonomously!
        </p>
        <div className="flex justify-center space-x-3">
          <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors">
            View Team Dashboard
          </button>
          <button className="px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 transition-colors">
            Check Progress
          </button>
        </div>
      </div>
    </div>
  )
}