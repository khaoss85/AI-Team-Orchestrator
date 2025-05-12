'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Handoff } from '@/types';
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
    const fetchProjectTeam = async () => {
      try {
        setLoading(true);
        
        // Fetch workspace details
        const workspaceData = await api.workspaces.get(id);
        setWorkspace(workspaceData);
        
        // Fetch agents
        const agentsData = await api.agents.list(id);
        setAgents(agentsData);
        
        // In una vera implementazione, dovremmo anche fetchare gli handoffs
        // const handoffsData = await api.handoffs.list(id);
        // setHandoffs(handoffsData);
        
        setError(null);
      } catch (err) {
        console.error('Failed to fetch project team:', err);
        setError('Impossibile caricare il team del progetto. Riprova più tardi.');
        
        // Dati fittizi per test
        setWorkspace({
          id: id,
          name: 'Progetto Marketing Digitale',
          description: 'Campagna di marketing sui social media',
          user_id: '123e4567-e89b-12d3-a456-426614174000',
          status: 'active',
          goal: 'Aumentare la visibilità del brand',
          budget: { max_amount: 1000, currency: 'EUR' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
        
        setAgents([
          {
            id: '1',
            workspace_id: id,
            name: 'ValutazioneCriticaDiProgrammiDiAllenamentoSpecialistAgent',
            role: 'Valutazione Critica Di Programmi Di Allenamento Specialization',
            seniority: 'senior',
            description: 'Gestisce tutte le attività relative alla valutazione critica di programmi di allenamento, applicando conoscenze specialistiche e strumenti dedicati.',
            system_prompt: 'Sei uno specialista AI nella valutazione critica di programmi di allenamento. Analizza e valuta i PED più rilevanti dell\'anno per personal trainer, considerando efficacia, innovazione e adattabilità. Collabora con gli altri agenti e fornisci report dettagliati.',
            status: 'active',
            health: { status: 'healthy' },
            llm_config: { model: 'gpt-4.1-mini', temperature: 0.3 },
            tools: [
              { name: 'web_search', type: 'function', description: 'Cerca informazioni aggiornate su programmi di allenamento e recensioni.' }
            ],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            workspace_id: id,
            name: 'RicercaEAnalisiDiLetteraturaScientificaInAmbitoFitnessSpecialistAgent',
            role: 'Ricerca E Analisi Di Letteratura Scientifica In Ambito Fitness Specialization',
            seniority: 'senior',
            description: 'Gestisce tutte le attività di ricerca e analisi della letteratura scientifica nel fitness, garantendo l\'integrazione di evidenze aggiornate.',
            system_prompt: 'Sei uno specialista AI nella ricerca e analisi della letteratura scientifica in ambito fitness. Identifica, valuta e sintetizza studi recenti sui PED più efficaci per personal trainer. Collabora con gli altri agenti e fornisci sintesi chiare e basate su evidenze.',
            status: 'active',
            health: { status: 'healthy' },
            llm_config: { model: 'gpt-4.1-mini', temperature: 0.3 },
            tools: [
              { name: 'academic_search', type: 'function', description: 'Ricerca articoli scientifici e pubblicazioni accademiche.' }
            ],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '3',
            workspace_id: id,
            name: 'ConoscenzaDelleTendenzeAttualiNelSettoreDelFitnessSpecialistAgent',
            role: 'Conoscenza Delle Tendenze Attuali Nel Settore Del Fitness Specialization',
            seniority: 'senior',
            description: 'Gestisce tutte le attività relative all\'analisi delle tendenze attuali nel settore fitness, individuando i PED più popolari e innovativi.',
            system_prompt: 'Sei uno specialista AI nell\'analisi delle tendenze attuali nel settore del fitness. Raccogli e valuta i trend emergenti sui PED, considerando popolarità, innovazione e feedback dei professionisti. Collabora con gli altri agenti e fornisci insight di mercato.',
            status: 'active',
            health: { status: 'healthy' },
            llm_config: { model: 'gpt-4.1-mini', temperature: 0.3 },
            tools: [
              { name: 'social_media_analysis', type: 'function', description: 'Analizza trend e discussioni sui social media riguardo i PED.' },
              { name: 'market_analysis', type: 'function', description: 'Analizza dati di mercato e report di settore.' }
            ],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
        
        // Simula alcuni handoffs
        setHandoffs([
          {
            id: '1',
            source_agent_id: '2',
            target_agent_id: '1',
            description: 'Trasferimento delle sintesi delle evidenze scientifiche sui PED per supportare la valutazione critica dei programmi.',
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            source_agent_id: '3',
            target_agent_id: '1',
            description: 'Condivisione dei trend di mercato e delle preferenze attuali per integrare la valutazione dei PED più rilevanti.',
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProjectTeam();
  }, [id]);
  
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
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
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'terminated': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getHealthColor = (health: string) => {
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
  
  const getAgentHandoffs = (agentId: string) => {
    return handoffs.filter(h => h.source_agent_id === agentId || h.target_agent_id === agentId);
  };
  
  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setIsEditModalOpen(true);
  };
  
  const handleSaveAgent = async (agentId: string, updates: Partial<Agent>) => {
    try {
      const updatedAgent = await api.agents.update(id, agentId, updates);
      setAgents(agents.map(agent => 
        agent.id === agentId ? updatedAgent : agent
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
                    </div>
                    <div className="flex space-x-2">
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
                      <span className={`text-xs px-3 py-1 rounded-full ${getHealthColor(agent.health.status)}`}>
                        {agent.health.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">Descrizione</h3>
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                          {agent.description || 'Nessuna descrizione disponibile'}
                        </p>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">System Prompt</h3>
                        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md max-h-32 overflow-y-auto">
                          <pre className="whitespace-pre-wrap">
                            {agent.system_prompt || 'Nessun prompt di sistema definito'}
                          </pre>
                        </div>
                      </div>
                      
                      {agent.llm_config && (
                        <div>
                          <h3 className="text-sm font-medium text-gray-900 mb-2">Configurazione LLM</h3>
                          <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                            <div className="grid grid-cols-2 gap-2">
                              {agent.llm_config.model && (
                                <div>
                                  <span className="font-medium">Modello:</span> {agent.llm_config.model}
                                </div>
                              )}
                              {agent.llm_config.temperature && (
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
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">Strumenti Disponibili</h3>
                        <div className="space-y-2">
                          {agent.tools && agent.tools.length > 0 ? (
                            agent.tools.map((tool, index) => (
                              <div key={index} className="bg-indigo-50 p-3 rounded-md">
                                <div className="flex justify-between items-start mb-1">
                                  <span className="font-medium text-indigo-900">{tool.name}</span>
                                  <span className="text-xs text-indigo-600">{tool.type}</span>
                                </div>
                                <p className="text-sm text-indigo-700">{tool.description}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-gray-500 italic">Nessuno strumento configurato</p>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">Handoffs</h3>
                        <div className="space-y-2">
                          {agentHandoffs.length > 0 ? (
                            agentHandoffs.map((handoff) => {
                              const isSource = handoff.source_agent_id === agent.id;
                              const targetAgent = agents.find(a => a.id === (isSource ? handoff.target_agent_id : handoff.source_agent_id));
                              
                              return (
                                <div key={handoff.id} className="bg-yellow-50 p-3 rounded-md">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className={`text-xs px-2 py-1 rounded-full ${isSource ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'}`}>
                                      {isSource ? 'Outgoing' : 'Incoming'}
                                    </span>
                                    <span className="text-sm font-medium">
                                      {isSource ? '→' : '←'} {targetAgent?.name || 'Agente sconosciuto'}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600">{handoff.description}</p>
                                </div>
                              );
                            })
                          ) : (
                            <p className="text-sm text-gray-500 italic">Nessun handoff configurato</p>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-2">Costo Stimato</h3>
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
          
          {agents.length === 0 && (
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
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingAgent(null);
        }}
        onSave={handleSaveAgent}
      />
    </div>
  );
}