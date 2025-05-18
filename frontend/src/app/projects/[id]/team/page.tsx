'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Handoff, SkillLevel, PersonalityTrait, CommunicationStyle } from '@/types'; 
import AgentEditModal from '@/components/AgentEditModal';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectTeamPage({ params: paramsPromise, searchParams }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [handoffs, setHandoffs] = useState<Handoff[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      
      const workspaceData = await api.workspaces.get(id);
      setWorkspace(workspaceData);
      
      const agentsData = await api.agents.list(id);
      setAgents(agentsData);
      
      const handoffsData = await api.handoffs.list(id);
      setHandoffs(handoffsData);
      
    } catch (err: any) {
      console.error('Failed to fetch project team:', err);
      setError(err.message || 'Impossibile caricare il team del progetto. Riprova più tardi.');
    } finally {
      setLoading(false);
    }
  };
  
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
      case 'initializing': return 'Inizializzazione';
      case 'paused': return 'In pausa';
      case 'error': return 'Errore';
      case 'terminated': return 'Terminato';
      default: return status;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'initializing': return 'bg-yellow-100 text-yellow-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'terminated': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getHealthColor = (health?: string) => {
    if (!health) return 'bg-gray-100 text-gray-800';
    switch(health) {
      case 'healthy': return 'bg-green-100 text-green-800';
      case 'degraded': return 'bg-yellow-100 text-yellow-800';
      case 'unhealthy': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getSeniorityColor = (seniority: string) => {
    switch(seniority) {
      case 'junior': return 'bg-blue-100 text-blue-800';
      case 'senior': return 'bg-purple-100 text-purple-800';
      case 'expert': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getSeniorityLabel = (seniority: string) => {
    switch(seniority) {
      case 'junior': return 'Junior';
      case 'senior': return 'Senior';
      case 'expert': return 'Expert';
      default: return seniority;
    }
  };
  
  const getCostPerDay = (seniority: string) => {
    switch(seniority) {
      case 'junior': return 5;
      case 'senior': return 10;
      case 'expert': return 18;
      default: return 5;
    }
  };
  
  const getSkillLevelBadge = (level?: string) => {
    if (!level) return "";
    switch(level.toLowerCase()) {
      case 'beginner': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'intermediate': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'expert': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };
  
  const formatPersonalityTraits = (traits: PersonalityTrait[] | undefined) => {
    if (!traits || !Array.isArray(traits) || traits.length === 0) return "Non specificati";
    return traits.map(trait => 
      typeof trait === 'string' 
        ? trait.replace(/_/g, ' ').replace(/-/g, ' ') 
        : String(trait).replace(/_/g, ' ').replace(/-/g, ' ')
    ).join(', ');
  };
  
  const getAgentHandoffs = (agentId: string): Handoff[] => {
    if (!handoffs) return [];
    return handoffs.filter(h => h.source_agent_id === agentId || h.target_agent_id === agentId);
  };
  
  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setIsEditModalOpen(true);
  };
  
  const handleSaveAgent = async (agentId: string, updates: Partial<Agent>) => {
    if (!id) return;
    try {
      const updatedAgent = await api.agents.update(id, agentId, updates);
      setAgents(agents.map(agent => 
        agent.id === agentId ? { ...agent, ...updatedAgent } : agent
      ));
      setIsEditModalOpen(false);
      setEditingAgent(null);
    } catch (err) {
      console.error('Failed to update agent:', err);
      throw err; 
    }
  };
  
  if (loading && !workspace) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento team...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto">
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}
      
      {workspace && (
        <>
          <div className="flex items-center justify-between mb-6">
            <div>
              <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm mb-2 block">
                ← Torna al progetto
              </Link>
              <h1 className="text-2xl font-semibold">Team di Agenti</h1>
              <p className="text-gray-600">{workspace.name}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Agenti nel team</p>
              <p className="text-2xl font-bold">{agents.length}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 gap-6">
            {agents.map((agent) => {
              const agentHandoffs = getAgentHandoffs(agent.id);
              const costPerDay = getCostPerDay(agent.seniority);
              const monthlyCost = costPerDay * 30;
              
              return (
                <div key={agent.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-xl font-semibold">{agent.name}</h2>
                      <p className="text-gray-600 font-medium">{agent.role}</p>
                      
                      {/* Nome completo se disponibile */}
                      {(agent.first_name || agent.last_name) && (
                        <p className="text-sm text-gray-600 mt-1">
                          {`${agent.first_name || ''} ${agent.last_name || ''}`.trim()}
                        </p>
                      )}
                    </div>
                    <div className="flex space-x-2 items-center">
                      <button
                        onClick={() => handleEditAgent(agent)}
                        className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-md text-sm hover:bg-indigo-100 transition"
                      >
                        Modifica
                      </button>
                      <span className={`text-xs px-3 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                        {getSeniorityLabel(agent.seniority)}
                      </span>
                      <span className={`text-xs px-3 py-1 rounded-full ${getStatusColor(agent.status)}`}>
                        {getStatusLabel(agent.status)}
                      </span>
                      <span className={`text-xs px-3 py-1 rounded-full ${getHealthColor(agent.health?.status)}`}>
                        {agent.health?.status || 'unknown'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      {/* Descrizione e system prompt */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Descrizione</h3>
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                          {agent.description || 'Nessuna descrizione disponibile'}
                        </p>
                      </div>
                      
                      {/* Nuova sezione: Personalità e Caratteristiche */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Personalità e Caratteristiche</h3>
                        <div className="bg-blue-50 p-3 rounded-md space-y-2">
                          {/* Stile di comunicazione */}
                          {agent.communication_style && (
                            <div className="text-sm">
                              <span className="font-medium text-blue-700">Stile di Comunicazione:</span>
                              <span className="ml-2">{agent.communication_style}</span>
                            </div>
                          )}
                          
                          {/* Tratti di personalità */}
                          {agent.personality_traits && agent.personality_traits.length > 0 && (
                            <div className="text-sm">
                              <span className="font-medium text-blue-700">Tratti di Personalità:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {agent.personality_traits.map((trait, i) => (
                                  <span key={i} className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                                    {typeof trait === 'string' 
                                      ? trait.replace(/_/g, ' ').replace(/-/g, ' ') 
                                      : String(trait).replace(/_/g, ' ').replace(/-/g, ' ')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Background story */}
                          {agent.background_story && (
                            <div className="text-sm">
                              <span className="font-medium text-blue-700">Background:</span>
                              <p className="mt-1 text-sm">{agent.background_story}</p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Hard Skills */}
                      {agent.hard_skills && agent.hard_skills.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-gray-900 mb-1">Hard Skills</h3>
                          <div className="bg-gray-50 p-3 rounded-md">
                            <div className="space-y-2">
                              {agent.hard_skills.map((skill, index) => (
                                <div key={index} className="flex justify-between items-center bg-white p-2 rounded border border-gray-100">
                                  <span className="font-medium">{skill.name}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${getSkillLevelBadge(skill.level as string)}`}>
                                    {skill.level}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Soft Skills */}
                      {agent.soft_skills && agent.soft_skills.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-gray-900 mb-1">Soft Skills</h3>
                          <div className="bg-gray-50 p-3 rounded-md">
                            <div className="space-y-2">
                              {agent.soft_skills.map((skill, index) => (
                                <div key={index} className="flex justify-between items-center bg-white p-2 rounded border border-gray-100">
                                  <span className="font-medium">{skill.name}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${getSkillLevelBadge(skill.level as string)}`}>
                                    {skill.level}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">System Prompt</h3>
                        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md max-h-32 overflow-y-auto">
                          <pre className="whitespace-pre-wrap">
                            {agent.system_prompt || 'Nessun prompt di sistema definito'}
                          </pre>
                        </div>
                      </div>
                      
                      {agent.llm_config && (
                        <div>
                          <h3 className="text-sm font-medium text-gray-900 mb-1">Configurazione LLM</h3>
                          <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                            <div className="grid grid-cols-2 gap-2">
                              {agent.llm_config.model && (
                                <div>
                                  <span className="font-medium">Modello:</span> {agent.llm_config.model}
                                </div>
                              )}
                              {typeof agent.llm_config.temperature === 'number' && (
                                <div>
                                  <span className="font-medium">Temperature:</span> {agent.llm_config.temperature}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-4">
                      {/* Tools, handoffs, costi */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Strumenti Disponibili</h3>
                        <div className="space-y-2">
                          {agent.tools && agent.tools.length > 0 ? (
                            agent.tools.map((tool, index) => (
                              <div key={index} className="bg-indigo-50 p-3 rounded-md">
                                <div className="flex justify-between items-start mb-1">
                                  <span className="font-medium text-indigo-900">{tool.name}</span>
                                  <span className="text-xs text-indigo-600">{typeof tool === 'object' && tool.type ? tool.type : 'N/D'}</span>
                                </div>
                                <p className="text-sm text-indigo-700">{typeof tool === 'object' && tool.description ? tool.description : ''}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-gray-500 italic">Nessuno strumento configurato</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Handoffs ({agentHandoffs.length})</h3>
                        <div className="space-y-2 max-h-40 overflow-y-auto bg-gray-50 p-3 rounded-md">
                          {agentHandoffs.length > 0 ? (
                            agentHandoffs.map((handoff) => {
                              const isSource = handoff.source_agent_id === agent.id;
                              const otherAgentId = isSource ? handoff.target_agent_id : handoff.source_agent_id;
                              const otherAgent = agents.find(a => a.id === otherAgentId);
                              
                              return (
                                <div key={handoff.id} className={`p-2 rounded-md border ${isSource ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${isSource ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'}`}>
                                      {isSource ? 'IN USCITA' : 'IN ENTRATA'}
                                    </span>
                                    <span className="text-sm font-medium text-gray-700">
                                      {isSource ? '→' : '←'} {otherAgent?.name || 'Agente Sconosciuto'}
                                    </span>
                                  </div>
                                  <p className="text-xs text-gray-600">{handoff.description || "Nessuna descrizione per l'handoff"}</p>
                                </div>
                              );
                            })
                          ) : (
                            <p className="text-sm text-gray-500 italic">Nessun handoff configurato per questo agente.</p>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Costo Stimato</h3>
                        <div className="bg-green-50 p-3 rounded-md">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-green-700 font-medium">Giornaliero:</span> {costPerDay} EUR
                            </div>
                            <div>
                              <span className="text-green-700 font-medium">Mensile:</span> {monthlyCost} EUR
                            </div>
                          </div>
                          <p className="text-xs text-green-600 mt-1">
                            Basato su seniority {agent.seniority}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {agents.length === 0 && !loading && (
            <div className="text-center py-10 bg-white rounded-lg shadow-sm">
              <h3 className="text-lg font-medium text-gray-600 mb-2">Nessun agente nel team</h3>
              <p className="text-gray-500 mb-4">Configura il team per questo progetto</p>
              <Link 
                href={`/projects/${id}/configure`}
                className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                Configura Team
              </Link>
            </div>
          )}
        </>
      )}
      
      <AgentEditModal
        isOpen={isEditModalOpen}
        agent={editingAgent}
        allAgents={agents}
        allHandoffs={handoffs}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingAgent(null);
        }}
        onSave={handleSaveAgent}
      />
    </div>
  );
}