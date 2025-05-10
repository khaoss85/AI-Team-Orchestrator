'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Task } from '@/types';

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchProjectData = async () => {
      try {
        setLoading(true);
        
        // Fetch workspace details
        const workspaceData = await api.workspaces.get(params.id);
        setWorkspace(workspaceData);
        
        // Fetch agents
        const agentsData = await api.agents.list(params.id);
        setAgents(agentsData);
        
        // In a real implementation, we would fetch tasks too
        // const tasksData = await api.tasks.list(params.id);
        // setTasks(tasksData);
        
        setError(null);
      } catch (err) {
        console.error('Failed to fetch project data:', err);
        setError('Impossibile caricare i dati del progetto. Riprova più tardi.');
        
        // Per test, mostra dati fittizi
        setWorkspace({
          id: params.id,
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
            workspace_id: params.id,
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
            workspace_id: params.id,
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
            workspace_id: params.id,
            name: 'Data Analyst',
            role: 'Data Analysis',
            seniority: 'senior',
            description: 'Analizza e visualizza dati',
            status: 'active',
            health: { status: 'healthy' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
        
        setTasks([
          {
            id: '1',
            workspace_id: params.id,
            agent_id: '1',
            name: 'Pianificazione campagna',
            description: 'Creare un piano per la campagna di marketing',
            status: 'completed',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            workspace_id: params.id,
            agent_id: '2',
            name: 'Creazione contenuti social',
            description: 'Creare contenuti per i social media',
            status: 'in_progress',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '3',
            workspace_id: params.id,
            agent_id: '3',
            name: 'Analisi dati utenti',
            description: 'Analizzare i dati degli utenti per identificare target',
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProjectData();
  }, [params.id]);
  
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
      case 'paused': return 'In pausa';
      case 'completed': return 'Completato';
      case 'in_progress': return 'In corso';
      case 'pending': return 'In attesa';
      case 'failed': return 'Fallito';
      default: return status;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'in_progress': return 'bg-indigo-100 text-indigo-800';
      case 'pending': return 'bg-orange-100 text-orange-800';
      case 'failed': return 'bg-red-100 text-red-800';
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
  
  if (loading && !workspace) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento progetto...</p>
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
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-semibold">{workspace.name}</h1>
              <p className="text-gray-600">{workspace.description}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(workspace.status)}`}>
              {getStatusLabel(workspace.status)}
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-medium mb-4">Dettagli Progetto</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Obiettivo</p>
                  <p className="font-medium">{workspace.goal || 'Non specificato'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Budget</p>
                  <p className="font-medium">
                    {workspace.budget 
                      ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                      : 'Non specificato'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Data creazione</p>
                  <p className="font-medium">
                    {new Date(workspace.created_at).toLocaleDateString('it-IT')}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-medium mb-4">Statistiche</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-indigo-50 p-3 rounded-md text-center">
                  <p className="text-indigo-700 text-sm mb-1">Agenti</p>
                  <p className="text-xl font-bold">{agents.length}</p>
                </div>
                <div className="bg-emerald-50 p-3 rounded-md text-center">
                  <p className="text-emerald-700 text-sm mb-1">Attività</p>
                  <p className="text-xl font-bold">{tasks.length}</p>
                </div>
                <div className="bg-amber-50 p-3 rounded-md text-center">
                  <p className="text-amber-700 text-sm mb-1">Completate</p>
                  <p className="text-xl font-bold">
                    {tasks.filter(t => t.status === 'completed').length}
                  </p>
                </div>
                <div className="bg-blue-50 p-3 rounded-md text-center">
                  <p className="text-blue-700 text-sm mb-1">In corso</p>
                  <p className="text-xl font-bold">
                    {tasks.filter(t => t.status === 'in_progress').length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-medium mb-4">Azioni</h2>
              <div className="space-y-3">
                <button className="w-full py-2 px-4 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition">
                  Aggiungi Attività
                </button>
                <button className="w-full py-2 px-4 bg-white border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 transition">
                  Gestisci Agenti
                </button>
                <button className="w-full py-2 px-4 bg-white border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 transition">
                  Visualizza Logs
                </button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium">Team di Agenti</h2>
                <Link 
                  href={`/projects/${workspace.id}/team`}
                  className="text-indigo-600 text-sm hover:underline"
                >
                  Visualizza tutti
                </Link>
              </div>
              
              <div className="space-y-4">
                {agents.slice(0, 3).map((agent) => (
                  <div key={agent.id} className="border-b pb-4 last:border-0 last:pb-0">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-medium">{agent.name}</h3>
                        <p className="text-gray-600 text-sm">{agent.role}</p>
                      </div>
                      <div className="flex space-x-2">
                        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(agent.status)}`}>
                          {getStatusLabel(agent.status)}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${getHealthColor(agent.health.status)}`}>
                          {agent.health.status}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium">Attività Recenti</h2>
                <Link 
                  href={`/projects/${workspace.id}/tasks`}
                  className="text-indigo-600 text-sm hover:underline"
                >
                  Visualizza tutte
                </Link>
              </div>
              
              <div className="space-y-4">
                {tasks.slice(0, 3).map((task) => (
                  <div key={task.id} className="border-b pb-4 last:border-0 last:pb-0">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-medium">{task.name}</h3>
                        <p className="text-gray-600 text-sm">
                          Agente: {agents.find(a => a.id === task.agent_id)?.name || 'Sconosciuto'}
                        </p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(task.status)}`}>
                        {getStatusLabel(task.status)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{task.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}