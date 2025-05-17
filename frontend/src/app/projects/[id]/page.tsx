'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import ConfirmModal from '@/components/ConfirmModal';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';
import { useRouter } from 'next/navigation';

// Sezioni di componenti specifici
import ProjectOverviewSection from '@/components/ProjectOverviewSection';
import ProjectProgressSection from '@/components/ProjectProgressSection';
import ProjectTeamSection from '@/components/ProjectTeamSection';
import ProjectActionsSection from '@/components/ProjectActionsSection';

export default function ProjectDashboard({ params }: { params: { id: string } }) {
  const router = useRouter();
  const workspaceId = params.id;
  
  // Stati per i dati
  const [workspace, setWorkspace] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [feedbackRequests, setFeedbackRequests] = useState<any[]>([]);
  
  // Stati per il controllo dell'UI
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [isStartingTeam, setIsStartingTeam] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  // Fetch dei dati iniziali
  useEffect(() => {
    const fetchData = async () => {
      if (!workspaceId) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Fetch workspace
        const workspaceData = await api.workspaces.get(workspaceId);
        setWorkspace(workspaceData);
        
        // Fetch agents
        try {
          const agentsData = await api.agents.list(workspaceId);
          setAgents(agentsData);
        } catch (agentErr) {
          console.error('Failed to fetch agents:', agentErr);
        }
        
        // Fetch tasks
        try {
          setTasksLoading(true);
          const tasksData = await api.monitoring.getWorkspaceTasks(workspaceId);
          setTasks(tasksData);
        } catch (taskErr) {
          console.error('Failed to fetch tasks:', taskErr);
        } finally {
          setTasksLoading(false);
        }
        
        // Fetch stats
        try {
          const statsData = await api.monitoring.getWorkspaceStatus(workspaceId);
          setStats(statsData);
        } catch (statsErr) {
          console.error('Failed to fetch stats:', statsErr);
        }
        
        // Fetch feedback requests
        try {
          const requests = await api.humanFeedback.getPendingRequests(workspaceId);
          setFeedbackRequests(requests);
        } catch (feedbackErr) {
          console.error('Failed to fetch feedback requests:', feedbackErr);
        }
        
      } catch (err) {
        console.error('Error fetching workspace data:', err);
        setError(err instanceof Error ? err.message : 'Impossibile caricare i dettagli del progetto');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [workspaceId]);
  
  // Funzioni di azione
  const handleStartTeam = async () => {
    try {
      setIsStartingTeam(true);
      await api.monitoring.startTeam(workspaceId);
      // Reload workspace data to get updated status
      const workspaceData = await api.workspaces.get(workspaceId);
      setWorkspace(workspaceData);
    } catch (err) {
      console.error('Error starting team:', err);
    } finally {
      setIsStartingTeam(false);
    }
  };
  
  const handleDeleteProject = async () => {
    try {
      await api.workspaces.delete(workspaceId);
      router.push('/projects');
    } catch (err) {
      console.error('Error deleting project:', err);
    }
  };
  
  // Calcoli per la barra di avanzamento
  const calculateProgress = () => {
    if (!tasks || tasks.length === 0) return 0;
    
    const completed = tasks.filter(t => t.status === 'completed').length;
    return Math.round((completed / tasks.length) * 100);
  };
  
  // Stima del budget utilizzato
  const calculateBudgetUsage = () => {
    if (!stats) return 0;
    
    const budget = workspace?.budget?.max_amount || 0;
    const spent = stats?.budget?.total_cost || 0;
    
    if (budget === 0) return 0;
    return Math.round((spent / budget) * 100);
  };
  
  // Rendering condizionale in base allo stato di caricamento
  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento progetto...</p>
        </div>
      </div>
    );
  }
  
  // Rendering in caso di errore
  if (error) {
    return (
      <div className="container mx-auto">
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => router.push('/projects')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition"
          >
            Torna alla lista progetti
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  // Verifica che workspace esista
  if (!workspace) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-10">
          <div className="text-3xl mb-3">😕</div>
          <h2 className="text-xl font-medium mb-2">Progetto non trovato</h2>
          <p className="text-gray-500 mb-4">Non è stato possibile trovare il progetto richiesto.</p>
          <Link 
            href="/projects"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Torna alla lista progetti
          </Link>
        </div>
      </div>
    );
  }

  // Componente principale
  return (
    <div className="container mx-auto">
      {/* Header con informazioni essenziali e navigazione */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <h1 className="text-2xl font-bold mr-3">{workspace?.name}</h1>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                workspace?.status === 'active' ? 'bg-green-100 text-green-800' :
                workspace?.status === 'created' ? 'bg-blue-100 text-blue-800' :
                workspace?.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                workspace?.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {workspace?.status === 'active' ? 'Attivo' : 
                 workspace?.status === 'created' ? 'Creato' : 
                 workspace?.status === 'paused' ? 'In pausa' : 
                 workspace?.status === 'completed' ? 'Completato' : 
                 workspace?.status}
              </span>
            </div>
            <p className="text-gray-600 mb-2">{workspace?.description}</p>
            
            {/* Obiettivo del progetto - evidenziato */}
            {workspace?.goal && (
              <div className="mt-3 mb-4 p-3 bg-indigo-50 border-l-4 border-indigo-500 rounded-r-md">
                <div className="flex items-start">
                  <span className="text-indigo-600 text-lg mr-2">🎯</span>
                  <div>
                    <p className="text-sm font-medium text-indigo-700">Obiettivo del progetto:</p>
                    <p className="text-sm text-indigo-900">{workspace.goal}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Progress bar e budget */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-700">Progresso</span>
                  <span className="text-sm font-medium text-gray-700">{calculateProgress()}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${calculateProgress()}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-700">Budget utilizzato</span>
                  <span className="text-sm font-medium text-gray-700">{calculateBudgetUsage()}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-green-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${calculateBudgetUsage()}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Team stats rapide */}
          <div className="text-right">
            <div className="bg-gray-50 px-4 py-3 rounded-lg border border-gray-200">
              <div className="text-sm text-gray-500">Team</div>
              <div className="text-3xl font-bold">{agents.length}</div>
              <div className="text-sm text-gray-500">agenti</div>
            </div>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 mt-6">
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'overview' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('overview')}
          >
            📊 Panoramica
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'team' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('team')}
          >
            👥 Team
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'tasks' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('tasks')}
          >
            📋 Attività
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'deliverables' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('deliverables')}
          >
            🎯 Deliverables
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'actions' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('actions')}
          >
            ⚙️ Azioni
          </button>
        </div>
      </div>

      {/* Contenuto dei tab */}
      <div className="mb-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <ProjectOverviewSection 
              workspace={workspace} 
              tasks={tasks} 
              agents={agents} 
              stats={stats} 
            />
            
            {/* Alert per feedback richiesto */}
            {feedbackRequests.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg flex items-start">
                <span className="text-yellow-600 text-lg mr-3">⚠️</span>
                <div>
                  <p className="font-medium text-yellow-700">Feedback richiesto!</p>
                  <p className="text-yellow-600">
                    Ci sono {feedbackRequests.length} richieste di feedback in attesa di risposta.
                  </p>
                  <button 
                    onClick={() => setActiveTab('actions')}
                    className="mt-2 text-sm font-medium text-yellow-700 hover:text-yellow-800"
                  >
                    Vedi dettagli →
                  </button>
                </div>
              </div>
            )}
            
            {/* Project Insights Dashboard */}
            <ProjectInsightsDashboard workspaceId={workspaceId} />
          </div>
        )}
        
        {activeTab === 'team' && (
          <ProjectTeamSection 
            workspace={workspace}
            agents={agents}
            workspaceId={workspaceId}
          />
        )}
        
        {activeTab === 'tasks' && (
          <ProjectProgressSection 
            workspace={workspace}
            tasks={tasks}
            agents={agents}
            tasksLoading={tasksLoading}
            workspaceId={workspaceId}
          />
        )}
        
        {activeTab === 'deliverables' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Deliverables del Progetto</h2>
            <p className="text-gray-600 mb-4">
              Esplora i risultati finali e gli output del progetto, inclusi documenti, analisi e raccomandazioni.
            </p>
            <Link 
              href={`/projects/${workspaceId}/deliverables`}
              className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
            >
              Visualizza Deliverables
            </Link>
          </div>
        )}
        
        {activeTab === 'actions' && (
          <ProjectActionsSection 
            workspace={workspace}
            onStartTeam={handleStartTeam}
            onDeleteClick={() => setIsDeleteModalOpen(true)}
            isStartingTeam={isStartingTeam}
            feedbackRequests={feedbackRequests}
          />
        )}
      </div>
      
      {/* Azioni rapide (sempre visibili) */}
      <div className="fixed bottom-6 right-6 flex space-x-3">
        <Link 
          href={`/projects/${workspaceId}/team`}
          className="flex items-center justify-center w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all"
          title="Gestisci Team"
        >
          <span className="text-xl">👥</span>
        </Link>
        <Link 
          href={`/projects/${workspaceId}/tasks`}
          className="flex items-center justify-center w-12 h-12 bg-green-600 text-white rounded-full shadow-lg hover:bg-green-700 transition-all"
          title="Visualizza Attività"
        >
          <span className="text-xl">📋</span>
        </Link>
        <Link 
          href={`/projects/${workspaceId}/deliverables`}
          className="flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all"
          title="Visualizza Deliverables"
        >
          <span className="text-xl">🎯</span>
        </Link>
      </div>
      
      {/* Modal di conferma eliminazione */}
      <ConfirmModal
        isOpen={isDeleteModalOpen}
        title="Elimina progetto"
        message={`Sei sicuro di voler eliminare il progetto "${workspace?.name}"? Questa azione eliminerà anche tutti gli agenti e i dati associati. Questa azione non può essere annullata.`}
        confirmText="Elimina"
        cancelText="Annulla"
        onConfirm={handleDeleteProject}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </div>
  );
}