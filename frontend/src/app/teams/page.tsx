'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Agent, Workspace } from '@/types';

export default function TeamsPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // In una vera implementazione, dovremmo recuperare i progetti e gli agenti dal backend
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Dati fittizi per testing
        setWorkspaces([
          {
            id: '1',
            name: 'Progetto Marketing Digitale',
            description: 'Campagna di marketing sui social media',
            user_id: '123',
            status: 'active',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            name: 'Analisi Dati Utenti',
            description: 'Analisi comportamentale degli utenti sul sito web',
            user_id: '123',
            status: 'created',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
        
        setAgents([
          {
            id: '1',
            workspace_id: '1',
            name: 'Project Manager',
            role: 'Project Management',
            seniority: 'expert',
            description: 'Coordina l\'intero progetto e gestisce gli handoff',
            status: 'active',
            health: { status: 'healthy' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            workspace_id: '1',
            name: 'Content Specialist',
            role: 'Content Creation',
            seniority: 'senior',
            description: 'Crea contenuti di alta qualità',
            status: 'active',
            health: { status: 'healthy' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '3',
            workspace_id: '1',
            name: 'Data Analyst',
            role: 'Data Analysis',
            seniority: 'senior',
            description: 'Analizza e visualizza dati',
            status: 'active',
            health: { status: 'degraded' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '4',
            workspace_id: '2',
            name: 'Data Scientist',
            role: 'Data Science',
            seniority: 'expert',
            description: 'Analisi avanzata dei dati e modelli predittivi',
            status: 'active',
            health: { status: 'healthy' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'processing_tasks': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'auto_recovering': return 'bg-orange-100 text-orange-800';
      case 'degraded_mode': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
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
  
  return (
    <div className="container mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Team di Agenti</h1>
      
      {loading ? (
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento agenti...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="mb-6">
            <h2 className="text-lg font-medium mb-4">Agenti per Progetto</h2>
            
            {workspaces.map((workspace) => {
              const workspaceAgents = agents.filter(a => a.workspace_id === workspace.id);
              
              return (
                <div key={workspace.id} className="mb-8 last:mb-0">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="font-medium">{workspace.name}</h3>
                      <p className="text-sm text-gray-600">{workspace.description}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(workspace.status)}`}>
                      {workspace.status === 'active' ? 'Attivo' : 
                       workspace.status === 'created' ? 'Creato' : 
                       workspace.status === 'processing_tasks' ? 'Elaborazione' :
                       workspace.status === 'paused' ? 'In pausa' : 
                       workspace.status === 'completed' ? 'Completato' : 
                       workspace.status === 'auto_recovering' ? 'Recupero automatico' :
                       workspace.status === 'degraded_mode' ? 'Modalità ridotta' :
                       workspace.status === 'error' ? 'Errore' :
                       workspace.status}
                    </span>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-md">
                    {workspaceAgents.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">Nessun agente in questo progetto</p>
                    ) : (
                      <div className="space-y-4">
                        {workspaceAgents.map((agent) => (
                          <div key={agent.id} className="bg-white p-4 rounded-md border border-gray-100">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="font-medium">{agent.name}</h4>
                                <p className="text-gray-600 text-sm">{agent.role}</p>
                              </div>
                              <div className="flex space-x-2">
                                <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                                  {agent.seniority}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(agent.status)}`}>
                                  {agent.status === 'active' ? 'Attivo' : 
                                   agent.status === 'created' ? 'Creato' : 
                                   agent.status === 'paused' ? 'In pausa' : 
                                   agent.status === 'error' ? 'Errore' : 
                                   agent.status}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded-full ${getHealthColor(agent.health.status)}`}>
                                  {agent.health.status}
                                </span>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
                            <div className="flex space-x-2 mt-2">
                              <button className="text-xs px-3 py-1 bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100 transition">
                                Visualizza Attività
                              </button>
                              <button className="text-xs px-3 py-1 bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition">
                                Modifica
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className="mt-4 text-right">
                      <Link href={`/projects/${workspace.id}`} className="text-indigo-600 text-sm hover:underline">
                        Vai al progetto
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}