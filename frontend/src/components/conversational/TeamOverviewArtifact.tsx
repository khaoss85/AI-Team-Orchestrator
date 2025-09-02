'use client'

import React, { useState } from 'react'
import AgentSkillRadarChart, { calculateTeamDimensions } from '@/components/AgentSkillRadarChart'
import AgentDetailRadarSection from '@/components/AgentDetailRadarSection'
import AgentEditModal from '@/components/AgentEditModal'

// Helper functions from team page
const getStatusColor = (status: string) => {
  switch(status) {
    case 'active': return 'bg-green-100 text-green-800'
    case 'created': return 'bg-blue-100 text-blue-800'
    case 'initializing': return 'bg-yellow-100 text-yellow-800'
    case 'paused': return 'bg-yellow-100 text-yellow-800'
    case 'error': return 'bg-red-100 text-red-800'
    case 'terminated': return 'bg-gray-100 text-gray-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const getSeniorityColor = (seniority: string) => {
  switch(seniority) {
    case 'junior': return 'bg-blue-100 text-blue-800'
    case 'senior': return 'bg-purple-100 text-purple-800'
    case 'expert': return 'bg-indigo-100 text-indigo-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const getHealthColor = (health?: string) => {
  if (!health) return 'bg-gray-100 text-gray-800'
  switch(health) {
    case 'healthy': return 'bg-green-100 text-green-800'
    case 'degraded': return 'bg-yellow-100 text-yellow-800'
    case 'unhealthy': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

interface TeamOverviewArtifactProps {
  team: any[]
  workspaceId: string
  handoffs?: any[]
  onTeamUpdate?: (updatedTeam: any[]) => void
}

export default function TeamOverviewArtifact({ 
  team, 
  workspaceId, 
  handoffs = [],
  onTeamUpdate 
}: TeamOverviewArtifactProps) {
  const [selectedAgent, setSelectedAgent] = useState<any>(null)
  const [editingAgent, setEditingAgent] = useState<any>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [activeView, setActiveView] = useState<'overview' | 'agents' | 'skills'>('overview')

  const handleEditAgent = (agent: any) => {
    console.log('🔧 [TeamOverviewArtifact] Opening edit modal for agent:', agent.id)
    console.log('🔧 [TeamOverviewArtifact] Available handoffs:', handoffs?.length || 0)
    console.log('🔧 [TeamOverviewArtifact] Available team members:', team?.length || 0)
    setEditingAgent(agent)
    setIsEditModalOpen(true)
  }

  const handleAgentUpdate = async (agentId: string, updates: Partial<any>) => {
    try {
      // Find the agent and apply updates
      const updatedAgent = { ...team.find(agent => agent.id === agentId), ...updates }
      
      if (onTeamUpdate) {
        const updatedTeam = team.map(agent => 
          agent.id === agentId ? updatedAgent : agent
        )
        onTeamUpdate(updatedTeam)
      }
      setIsEditModalOpen(false)
      setEditingAgent(null)
    } catch (error) {
      console.error('Error updating agent:', error)
      // Keep modal open on error
    }
  }

  const teamDimensions = calculateTeamDimensions(team)

  if (team.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">👥</div>
          <div className="text-lg font-medium mb-2">No Team Members</div>
          <div className="text-sm">Add team members through the conversation</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with view tabs */}
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          👥 Team Overview ({team.length} members)
        </h3>
        
        <div className="flex space-x-1">
          <ViewTab
            active={activeView === 'overview'}
            onClick={() => setActiveView('overview')}
            label="Overview"
            icon="📊"
          />
          <ViewTab
            active={activeView === 'agents'}
            onClick={() => setActiveView('agents')}
            label="Members"
            icon="👤"
          />
          <ViewTab
            active={activeView === 'skills'}
            onClick={() => setActiveView('skills')}
            label="Skills"
            icon="🎯"
          />
        </div>
      </div>

      {/* Content based on active view */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'overview' && (
          <TeamOverviewTab team={team} teamDimensions={teamDimensions} />
        )}
        
        {activeView === 'agents' && (
          <TeamMembersTab 
            team={team} 
            handoffs={handoffs}
            onSelectAgent={setSelectedAgent}
            onEditAgent={handleEditAgent}
          />
        )}
        
        {activeView === 'skills' && (
          <TeamSkillsTab team={team} teamDimensions={teamDimensions} />
        )}
      </div>

      {/* Agent Edit Modal */}
      {isEditModalOpen && editingAgent && (
        <AgentEditModal
          isOpen={isEditModalOpen}
          agent={editingAgent}
          allAgents={team}
          allHandoffs={handoffs}
          onClose={() => setIsEditModalOpen(false)}
          onSave={handleAgentUpdate}
        />
      )}
    </div>
  )
}

// View Tab Component
interface ViewTabProps {
  active: boolean
  onClick: () => void
  label: string
  icon: string
}

function ViewTab({ active, onClick, label, icon }: ViewTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
        ${active
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }
      `}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  )
}

// Team Overview Tab
function TeamOverviewTab({ team, teamDimensions }: { team: any[], teamDimensions: any }) {
  const activeMembersCount = team.filter(agent => agent.status === 'active').length
  const totalSkills = [...new Set(team.flatMap(agent => agent.skills || []))].length
  
  return (
    <div className="p-4 space-y-4">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{activeMembersCount}</div>
          <div className="text-sm text-blue-700">Active Members</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{totalSkills}</div>
          <div className="text-sm text-green-700">Total Skills</div>
        </div>
      </div>

      {/* Team Skill Radar */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Team Skills Overview</h4>
        <AgentSkillRadarChart
          skills={teamDimensions}
          title="Team Skills"
          size={200}
          colorScheme="team"
        />
      </div>

      {/* Seniority Distribution */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Seniority Distribution</h4>
        <div className="space-y-2">
          {['junior', 'senior', 'expert'].map(level => {
            const count = team.filter(agent => agent.seniority === level).length
            const percentage = team.length > 0 ? (count / team.length) * 100 : 0
            return (
              <div key={level} className="flex items-center space-x-3">
                <div className="w-16 text-sm text-gray-600 capitalize">{level}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <div className="w-8 text-sm text-gray-600">{count}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// Team Members Tab
function TeamMembersTab({ 
  team, 
  handoffs = [],
  onSelectAgent, 
  onEditAgent 
}: { 
  team: any[], 
  handoffs?: any[],
  onSelectAgent: (agent: any) => void,
  onEditAgent: (agent: any) => void
}) {
  
  const getAgentHandoffs = (agentId: string) => {
    if (!handoffs) return [];
    return handoffs.filter(h => h.source_agent_id === agentId || h.target_agent_id === agentId);
  };
  return (
    <div className="p-4 space-y-4">
      {team.map((agent) => (
        <div
          key={agent.id}
          className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
        >
          {/* Agent Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start space-x-3">
              <div className="flex flex-col items-center space-y-1">
                <div className={`w-3 h-3 rounded-full ${
                  agent.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                }`} />
                {agent.health && (
                  <div className={`w-2 h-2 rounded-full ${
                    agent.health === 'healthy' ? 'bg-green-400' : 
                    agent.health === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
                  }`} />
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {typeof agent.name === 'object' 
                    ? JSON.stringify(agent.name) 
                    : agent.name || 'Unknown Agent'
                  }
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  {typeof agent.description === 'object' 
                    ? JSON.stringify(agent.description) 
                    : agent.description || 'AI Agent specialist'
                  }
                </p>
                
                {/* Status Badges */}
                <div className="flex flex-wrap gap-2">
                  <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                    getStatusColor(typeof agent.status === 'object' ? agent.status.status || 'unknown' : agent.status)
                  }`}>
                    {typeof agent.status === 'object' 
                      ? agent.status.status || 'unknown'
                      : agent.status || 'unknown'
                    }
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                    {agent.seniority || 'unknown'}
                  </span>
                  {agent.health && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      getHealthColor(typeof agent.health === 'object' ? agent.health.status || 'unknown' : agent.health)
                    }`}>
                      {typeof agent.health === 'object' 
                        ? agent.health.status || 'unknown'
                        : agent.health || 'unknown'
                      }
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => onEditAgent(agent)}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Edit
            </button>
          </div>

          {/* Skills Section */}
          {((agent.hard_skills && agent.hard_skills.length > 0) || 
            (agent.soft_skills && agent.soft_skills.length > 0)) && (
            <div className="border-t pt-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Skills</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Hard Skills */}
                {agent.hard_skills && agent.hard_skills.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Hard Skills</div>
                    <div className="flex flex-wrap gap-1">
                      {agent.hard_skills.slice(0, 3).map((skill: any, index: number) => (
                        <span
                          key={skill?.name || skill || index}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                        >
                          {typeof skill === 'object' && skill?.name 
                            ? `${skill.name} (${skill.level || 'N/A'})` 
                            : typeof skill === 'string' 
                            ? skill 
                            : typeof skill === 'object'
                            ? JSON.stringify(skill)
                            : 'Unknown skill'
                          }
                        </span>
                      ))}
                      {agent.hard_skills.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{agent.hard_skills.length - 3} più
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Soft Skills */}
                {agent.soft_skills && agent.soft_skills.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Soft Skills</div>
                    <div className="flex flex-wrap gap-1">
                      {agent.soft_skills.slice(0, 3).map((skill: any, index: number) => (
                        <span
                          key={skill?.name || skill || index}
                          className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded"
                        >
                          {typeof skill === 'object' && skill?.name 
                            ? `${skill.name} (${skill.level || 'N/A'})` 
                            : typeof skill === 'string' 
                            ? skill 
                            : typeof skill === 'object'
                            ? JSON.stringify(skill)
                            : 'Unknown skill'
                          }
                        </span>
                      ))}
                      {agent.soft_skills.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{agent.soft_skills.length - 3} più
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Handoffs Information */}
          {(() => {
            const agentHandoffs = getAgentHandoffs(agent.id)
            return agentHandoffs.length > 0 && (
              <div className="border-t pt-3 mt-3">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Handoffs ({agentHandoffs.length})</h4>
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {agentHandoffs.map((handoff) => {
                    const isSource = handoff.source_agent_id === agent.id
                    const otherAgentId = isSource ? handoff.target_agent_id : handoff.source_agent_id
                    const otherAgent = team.find(a => a.id === otherAgentId)
                    
                    return (
                      <div key={handoff.id} className={`p-2 rounded text-xs ${
                        isSource ? 'bg-yellow-50 text-yellow-800' : 'bg-green-50 text-green-800'
                      }`}>
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">
                            {isSource ? '→' : '←'} {otherAgent?.name || 'Unknown Agent'}
                          </span>
                          <span className={`px-1 py-0.5 rounded text-xs ${
                            isSource ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'
                          }`}>
                            {isSource ? 'OUT' : 'IN'}
                          </span>
                        </div>
                        {handoff.description && (
                          <p className="text-xs text-gray-600 mt-1 truncate" title={handoff.description}>
                            {handoff.description}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })()}

          {/* Cost Information */}
          {agent.seniority && (
            <div className="border-t pt-3 mt-3">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Costo stimato</span>
                <span className="font-medium">
                  {agent.seniority === 'expert' ? '18 EUR/giorno' : 
                   agent.seniority === 'senior' ? '10 EUR/giorno' : 
                   '6 EUR/giorno'}
                </span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// Team Skills Tab
function TeamSkillsTab({ team, teamDimensions }: { team: any[], teamDimensions: any }) {
  const allSkills = team.flatMap(agent => agent.skills || [])
  const skillCounts = allSkills.reduce((acc: Record<string, number>, skill) => {
    acc[skill] = (acc[skill] || 0) + 1
    return acc
  }, {})

  const topSkills = Object.entries(skillCounts)
    .sort(([,a], [,b]) => (b as number) - (a as number))
    .slice(0, 10)

  return (
    <div className="p-4 space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Detailed Skills Radar</h4>
        <AgentDetailRadarSection
          agent={null}
          teamDimensions={teamDimensions}
        />
      </div>

      <div className="space-y-3">
        <h4 className="font-medium text-gray-900">Top Skills</h4>
        {topSkills.map(([skill, count]) => (
          <div key={skill} className="flex items-center justify-between">
            <span className="text-sm text-gray-700">{skill}</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${((count as number) / team.length) * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 w-8">{count}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}