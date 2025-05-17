"use client"

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Task } from '@/types';
import ConfirmModal from '@/components/ConfirmModal';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';

// Nuovi componenti specifici
import ProjectOverviewSection from '@/components/ProjectOverviewSection';
import ProjectProgressSection from '@/components/ProjectProgressSection';
import ProjectTeamSection from '@/components/ProjectTeamSection';
import ProjectActionsSection from '@/components/ProjectActionsSection';
import ProjectFeedbackSection from '@/components/ProjectFeedbackSection';

export default function ProjectDashboard({ workspace, agents, loading, error, onStartTeam, onDeleteProject, isStartingTeam, isDeleteModalOpen, setIsDeleteModalOpen }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [feedbackRequests, setFeedbackRequests] = useState([]);
  
  useEffect(() => {
    if (workspace) {
      fetchTasks();
      fetchStats();
      fetchFeedbackRequests();
    }
  }, [workspace?.id]);
  
  const fetchTasks = async () => {
    try {
      setTasksLoading(true);
      const result = await api.monitoring.getWorkspaceTasks(workspace.id);
      setTasks(result);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    } finally {
      setTasksLoading(false);
    }
  };
  
  const fetchStats = async () => {
    try {
      const result = await api.monitoring.getWorkspaceStatus(workspace.id);
      setStats(result);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };
  
  const fetchFeedbackRequests = async () => {
    try {
      const requests = await api.humanFeedback.getPendingRequests(workspace.id);
      setFeedbackRequests(requests);
    } catch (err) {
      console.error('Error fetching feedback requests:', err);
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
  
  // Rendering in caso di errore
  if (error) {
    return (
      <div className="container mx-auto">
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      </div>
    );
  }

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
                 'Stato sconosciuto'}
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
            <ProjectOverviewSection workspace={workspace} tasks={tasks} agents={agents} stats={stats} />
            
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
            <ProjectInsightsDashboard workspaceId={workspace.id} />
          </div>
        )}
        
        {activeTab === 'team' && (
          <ProjectTeamSection 
            workspace={workspace}
            agents={agents}
            workspaceId={workspace.id}
          />
        )}
        
        {activeTab === 'tasks' && (
          <ProjectProgressSection 
            workspace={workspace}
            tasks={tasks}
            tasksLoading={tasksLoading}
            workspaceId={workspace.id}
          />
        )}
        
        {activeTab === 'deliverables' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Deliverables del Progetto</h2>
            <p className="text-gray-600 mb-4">
              Esplora i risultati finali e gli output del progetto, inclusi documenti, analisi e raccomandazioni.
            </p>
            <Link 
              href={`/projects/${workspace.id}/deliverables`}
              className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
            >
              Visualizza Deliverables
            </Link>
          </div>
        )}
        
        {activeTab === 'actions' && (
          <ProjectActionsSection 
            workspace={workspace}
            onStartTeam={onStartTeam}
            onDeleteClick={() => setIsDeleteModalOpen(true)}
            isStartingTeam={isStartingTeam}
            feedbackRequests={feedbackRequests}
          />
        )}
      </div>
      
      {/* Azioni rapide (sempre visibili) */}
      <div className="fixed bottom-6 right-6 flex space-x-3">
        <Link 
          href={`/projects/${workspace.id}/team`}
          className="flex items-center justify-center w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all"
          title="Gestisci Team"
        >
          <span className="text-xl">👥</span>
        </Link>
        <Link 
          href={`/projects/${workspace.id}/tasks`}
          className="flex items-center justify-center w-12 h-12 bg-green-600 text-white rounded-full shadow-lg hover:bg-green-700 transition-all"
          title="Visualizza Attività"
        >
          <span className="text-xl">📋</span>
        </Link>
        <Link 
          href={`/projects/${workspace.id}/deliverables`}
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
        onConfirm={onDeleteProject}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </div>
  );
}