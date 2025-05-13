'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Task } from '@/types';
import ConfirmModal from '@/components/ConfirmModal';
import MonitoringDashboard from '@/components/MonitoringDashboard';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';

import { useRouter } from 'next/navigation';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectDetailPage({ params: paramsPromise, searchParams }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isStartingTeam, setIsStartingTeam] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    const fetchProjectData = async () => {
      try {
        setLoading(true);
        
        // Fetch workspace details
        const workspaceData = await api.workspaces.get(id);
        setWorkspace(workspaceData);
        
        // Fetch agents
        const agentsData = await api.agents.list(id);
        setAgents(agentsData);
        
        setError(null);
      } catch (err) {
        console.error('Failed to fetch project data:', err);
        setError('Impossibile caricare i dati del progetto. Riprova più tardi.');
        
        // Mock data for testing
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
            name: 'Project Manager',
            role: 'Project Management',
            seniority: 'expert',
            description: 'Coordina l\'intero progetto',
            status: 'active',
            health: { status: 'healthy' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            workspace_id: id,
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
            workspace_id: id,
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
      } finally {
        setLoading(false);
      }
    };
    
    fetchProjectData();
  }, [id]);
  
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
      case 'paused': return 'In pausa';
      case 'completed': return 'Completato';
      default: return status;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const handleStartTeam = async () => {
    if (!workspace) return;
    
    try {
      setIsStartingTeam(true);
      await api.monitoring.startTeam(workspace.id);
      
      setWorkspace(prev => prev ? { ...prev, status: 'active' } : null);
      setError(null);
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);
      
    } catch (err) {
      console.error('Failed to start team:', err);
      setError('Impossibile avviare il team. Riprova più tardi.');
    } finally {
      setIsStartingTeam(false);
    }
  };
    
  const handleDeleteProject = async () => {
    if (!workspace) return;
    
    try {
      setIsDeleting(true);
      const success = await api.workspaces.delete(workspace.id);
      
      if (success) {
        router.push('/projects');
      } else {
        setError('Impossibile eliminare il progetto. Riprova più tardi.');
        setIsDeleteModalOpen(false);
      }
    } catch (err) {
      console.error('Failed to delete project:', err);
      setError(err instanceof Error ? err.message : 'Si è verificato un errore durante l\'eliminazione del progetto');
    } finally {
      setIsDeleting(false);
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
          {/* Header semplificato */}
          <div className="flex justify-between items-start mb-6">
            <div className="flex-1 mr-6">
              <h1 className="text-2xl font-semibold">{workspace.name}</h1>
              <p className="text-gray-600">{workspace.description}</p>
              
              {/* Obiettivo del progetto - più compatto */}
              {workspace.goal && (
                <div className="mt-2 p-2 bg-indigo-50 border border-indigo-200 rounded-md max-w-3xl">
                  <div className="flex items-start">
                    <span className="text-sm text-indigo-700 font-medium mr-2 flex-shrink-0">🎯 Obiettivo:</span>
                    <p className="text-sm text-indigo-800 leading-relaxed">{workspace.goal}</p>
                  </div>
                </div>
              )}
              
              <div className="mt-3">
                <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(workspace.status)}`}>
                  {getStatusLabel(workspace.status)}
                </span>
              </div>
            </div>
            
            {/* Actions compatte */}
            <div className="flex space-x-3">
              {workspace.status === 'created' && (
                <button 
                  onClick={handleStartTeam}
                  disabled={isStartingTeam}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition disabled:opacity-50"
                >
                  {isStartingTeam ? 'Avvio...' : '🚀 Avvia Team'}
                </button>
              )}
              
              <Link 
                href={`/projects/${workspace.id}/team`}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
              >
                👥 Gestisci Team
              </Link>
              
              <button 
                onClick={() => setIsDeleteModalOpen(true)}
                className="px-4 py-2 bg-red-50 border border-red-300 text-red-700 rounded-md hover:bg-red-100 transition"
              >
                🗑️ Elimina
              </button>
            </div>
          </div>
          
          {/* Project Insights - Dashboard compatto */}
          <div className="mb-8">
            <ProjectInsightsDashboard workspaceId={id} />
          </div>
          
          {/* Quick Actions */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <Link 
              href={`/projects/${id}/tasks`}
              className="block p-4 bg-white rounded-lg shadow-sm border hover:shadow-md transition"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3">📋</span>
                <div>
                  <h3 className="font-medium">Tutte le Attività</h3>
                  <p className="text-sm text-gray-600">Gestisci e monitora le attività</p>
                </div>
              </div>
            </Link>
            
            <Link 
              href={`/projects/${id}/team`}
              className="block p-4 bg-white rounded-lg shadow-sm border hover:shadow-md transition"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3">👥</span>
                <div>
                  <h3 className="font-medium">Team di Agenti</h3>
                  <p className="text-sm text-gray-600">Visualizza e modifica agenti</p>
                </div>
              </div>
            </Link>
            
            <Link 
              href="/tools"
              className="block p-4 bg-white rounded-lg shadow-sm border hover:shadow-md transition"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3">🛠️</span>
                <div>
                  <h3 className="font-medium">Strumenti</h3>
                  <p className="text-sm text-gray-600">Gestisci tool personalizzati</p>
                </div>
              </div>
            </Link>
          </div>

          {/* Monitoring Dashboard - Solo se ci sono agenti attivi */}
          {workspace && agents.length > 0 && (
            <MonitoringDashboard workspaceId={id} agentsInWorkspace={agents} />
          )}
        </>
      )}
      
      <ConfirmModal
        isOpen={isDeleteModalOpen}
        title="Elimina progetto"
        message={`Sei sicuro di voler eliminare il progetto "${workspace?.name}"? Questa azione eliminerà anche tutti gli agenti e i dati associati. Questa azione non può essere annullata.`}
        confirmText={isDeleting ? "Eliminazione..." : "Elimina"}
        cancelText="Annulla"
        onConfirm={handleDeleteProject}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </div>
  );
}