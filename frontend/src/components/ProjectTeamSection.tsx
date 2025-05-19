import React, { useState } from 'react';
import Link from 'next/link';
import { Workspace, Agent } from '@/types';
import AgentSkillRadarChart, { calculateAgentDimensions, calculateTeamDimensions } from './AgentSkillRadarChart';

interface ProjectTeamSectionProps {
  workspace: Workspace;
  agents: Agent[];
  workspaceId: string;
}

export default function ProjectTeamSection({ workspace, agents, workspaceId }: ProjectTeamSectionProps) {
  // Stato per visualizzare/nascondere il radar chart del team
  const [showTeamRadar, setShowTeamRadar] = useState(true);
  
  // Funzioni helper per la visualizzazione
  const getSeniorityColor = (seniority: string) => {
    switch(seniority) {
      case 'junior': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'senior': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'expert': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getHealthColor = (health: any) => {
    const status = health?.status || 'unknown';
    switch(status) {
      case 'healthy': return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'unhealthy': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Utility per ottenere il colore di skill level
  const getSkillLevelColor = (level: string) => {
    switch(level?.toLowerCase()) {
      case 'beginner': return 'text-blue-600';
      case 'intermediate': return 'text-purple-600';
      case 'expert': return 'text-indigo-600';
      default: return 'text-gray-600';
    }
  };

  // Raggruppa agenti per ruolo
  const agentsByRole = React.useMemo(() => {
    const roleGroups: Record<string, Agent[]> = {};
    
    agents.forEach(agent => {
      const role = agent.role;
      if (!roleGroups[role]) {
        roleGroups[role] = [];
      }
      roleGroups[role].push(agent);
    });
    
    return roleGroups;
  }, [agents]);

  // Formatta i tratti di personalità come una stringa leggibile
  const formatPersonalityTraits = (traits: string[] | null | undefined) => {
    if (!traits || !Array.isArray(traits) || traits.length === 0) return "Non specificati";
    return traits.map(trait => trait.replace(/_/g, ' ').replace(/-/g, ' ')).join(', ');
  };

  // Funzione per formattare skills
  const renderSkills = (skills: any[] | null | undefined) => {
    if (!skills || !Array.isArray(skills) || skills.length === 0) return null;
    
    return (
      <div className="mt-2">
        <div className="flex flex-wrap gap-1">
          {skills.slice(0, 3).map((skill, index) => (
            <div key={index} 
                className="text-xs px-2 py-1 rounded-full bg-gray-50 border border-gray-200 flex items-center">
              <span>{skill.name}</span>
              {skill.level && (
                <span className={`ml-1 text-xs ${getSkillLevelColor(skill.level)}`}>
                  ({skill.level})
                </span>
              )}
            </div>
          ))}
          {skills.length > 3 && (
            <div className="text-xs px-2 py-1 rounded-full bg-gray-50 border border-gray-200">
              +{skills.length - 3}
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Calcola le dimensioni del team 
  const teamDimensions = calculateTeamDimensions(agents);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold">Team di Agenti AI</h2>
          <p className="text-gray-500">
            {agents.length} agenti stanno lavorando su questo progetto
          </p>
        </div>
        
        <Link 
          href={`/projects/${workspaceId}/team`}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition inline-flex items-center"
        >
          <span>Gestisci Team</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </Link>
      </div>
      
      {/* Team Radar Chart */}
      {agents.length > 0 && (
        <div className="mb-6 bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-lg border border-purple-100">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-md font-semibold text-purple-900">Team Competency Matrix</h3>
            <button 
              className="text-xs px-3 py-1 bg-purple-100 text-purple-800 rounded-md"
              onClick={() => setShowTeamRadar(!showTeamRadar)}
            >
              {showTeamRadar ? 'Nascondi' : 'Mostra'}
            </button>
          </div>
          
          {showTeamRadar && (
            <div className="flex flex-col items-center">
              <p className="text-sm text-purple-700 mb-3">
                Questa matrice mostra le competenze medie del team sulle 6 dimensioni più rilevanti
              </p>
              <AgentSkillRadarChart 
                skills={teamDimensions} 
                title="Team Matrix" 
                size={350} 
                colorScheme="team" 
              />
              <div className="text-xs text-purple-600 mt-2">
                Valori da 0 a 5 basati sulle competenze individuali degli agenti
              </div>
            </div>
          )}
        </div>
      )}
      
      {agents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-5xl mb-3">👥</div>
          <p className="text-gray-600 text-lg mb-2">Nessun agente configurato</p>
          <p className="text-gray-500 text-sm mb-4">Configura il team del progetto per iniziare</p>
          <Link
            href={`/projects/${workspaceId}/configure`}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Configura Team
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Visualizzazione a team con raggruppamento per ruolo */}
          {Object.entries(agentsByRole).map(([role, roleAgents]) => (
            <div key={role} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-lg mb-3 border-b pb-2">{role}</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {roleAgents.map(agent => {
                  // Calcola le dimensioni dell'agente per il radar chart
                  const agentDimensions = calculateAgentDimensions(agent);
                  
                  return (
                    <div key={agent.id} className="bg-gray-50 rounded-lg overflow-hidden border border-gray-200 hover:shadow-md transition">
                      <div className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">{agent.name}</h4>
                            {/* Nome completo se disponibile */}
                            {(agent.first_name || agent.last_name) && (
                              <p className="text-sm text-gray-600">
                                {`${agent.first_name || ''} ${agent.last_name || ''}`.trim()}
                              </p>
                            )}
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                            {agent.seniority}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mt-1 mb-2 line-clamp-2">
                          {agent.description || `Agente specializzato in ${agent.role}`}
                        </p>
                        
                        {/* Agent Radar Chart */}
                        <div className="bg-white rounded-md border border-gray-100 mt-2 mb-3">
                          <AgentSkillRadarChart 
                            skills={agentDimensions} 
                            title="Competency Profile"
                            size={200}
                            className="py-2" 
                          />
                        </div>
                        
                        {/* Nuova sezione per personalità e caratteristiche */}
                        <div className="mt-3 mb-3 bg-white p-2 rounded-md border border-gray-100">
                          {agent.communication_style && (
                            <div className="text-xs text-gray-600 flex items-center mb-1">
                              <span className="font-medium mr-1">Comunicazione:</span> 
                              <span className="italic">{agent.communication_style}</span>
                            </div>
                          )}
                          
                          {agent.personality_traits && agent.personality_traits.length > 0 && (
                            <div className="text-xs text-gray-600 mb-1">
                              <span className="font-medium">Personalità:</span> {formatPersonalityTraits(agent.personality_traits)}
                            </div>
                          )}
                        </div>
                        
                        {/* Skills section */}
                        <div className="space-y-2">
                          {agent.hard_skills && agent.hard_skills.length > 0 && (
                            <div>
                              <div className="text-xs text-gray-500 mb-1">Hard Skills:</div>
                              {renderSkills(agent.hard_skills)}
                            </div>
                          )}
                          
                          {agent.soft_skills && agent.soft_skills.length > 0 && (
                            <div>
                              <div className="text-xs text-gray-500 mb-1">Soft Skills:</div>
                              {renderSkills(agent.soft_skills)}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-200">
                          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(agent.status)}`}>
                            {agent.status}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded-full ${getHealthColor(agent.health)}`}>
                            {agent.health?.status || 'unknown'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
          
          {/* Link alla vista dettagliata del team */}
          <div className="text-center pt-4">
            <Link 
              href={`/projects/${workspaceId}/team`}
              className="text-indigo-600 hover:text-indigo-800 text-sm font-medium inline-flex items-center"
            >
              <span>Visualizza dettagli completi del team</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}