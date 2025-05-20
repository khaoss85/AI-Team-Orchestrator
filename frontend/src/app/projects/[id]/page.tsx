'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import ConfirmModal from '@/components/ConfirmModal';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';
import { useRouter } from 'next/navigation';
import AgentSkillRadarChart, { calculateTeamDimensions } from '@/components/AgentSkillRadarChart';
import AgentDetailRadarSection from '@/components/AgentDetailRadarSection';
import TaskResultDetails from '@/components/TaskResultDetails';
import ProjectActionsSection from '@/components/ProjectActionsSection';


// Mantieni la definizione dei tipi originale
type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectDashboard({ params: paramsPromise }: Props) {
  const router = useRouter();
  
  // Use the React.use hook to "unwrap" the Promise
  const params = use(paramsPromise);
  const workspaceId = params.id;
  
  // Stati per i dati
  const [workspace, setWorkspace] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [feedbackRequests, setFeedbackRequests] = useState<any[]>([]);
  const [recentActivitySummary, setRecentActivitySummary] = useState<string>('');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  
  // Stati per il controllo dell'UI
  const [activeSection, setActiveSection] = useState('results');
  const [activeResultId, setActiveResultId] = useState('');
  const [showTeamRadar, setShowTeamRadar] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [isStartingTeam, setIsStartingTeam] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  // Fetch dei dati iniziali
  useEffect(() => {
    fetchData();
  }, [workspaceId]);
  
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
        const response = await fetch(`${api.getBaseUrl()}/monitoring/workspace/${workspaceId}/tasks`);
        if (!response.ok) {
          throw new Error(`Failed to fetch tasks: ${response.status}`);
        }
        const tasksData = await response.json();
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

  const handleEditAgent = (agent) => {
    // Implementa la funzione per modificare un agente
    // Puoi mantenere la funzionalità esistente
    console.log('Edit agent:', agent);
  };
  
  const handleInteractWithAgent = (agent) => {
    // Implementa la funzione per interagire con un agente
    console.log('Interact with agent:', agent);
  };
    
   const onDeleteClick = () => {
      setIsDeleteModalOpen(true);
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
  
  // Helper functions per la visualizzazione
  const getStatusColor = (status) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusLabel = (status) => {
    switch(status) {
      case 'active': return 'Attivo';
      case 'created': return 'Creato';
      case 'paused': return 'In pausa';
      case 'error': return 'Errore';
      case 'completed': return 'Completato';
      case 'in_progress': return 'In Corso';
      case 'pending': return 'In Attesa';
      case 'failed': return 'Fallito';
      default: return status;
    }
  };
  
  const formatPersonalityTraits = (traits) => {
    if (!traits || !Array.isArray(traits) || traits.length === 0) return "Non specificati";
    return traits.map(trait => 
      typeof trait === 'string' 
        ? trait.replace(/_/g, ' ').replace(/-/g, ' ') 
        : String(trait).replace(/_/g, ' ').replace(/-/g, ' ')
    ).join(', ');
  };
  
  // Funzioni per i risultati
  const getAgentName = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Sistema';
  };
  
  const determineTaskType = (task) => {
    const name = (task.name || '').toLowerCase();
    const description = (task.description || '').toLowerCase();
    
    if (name.includes('analis') || name.includes('ricerca') || description.includes('analis') || description.includes('ricerca')) return 'analysis';
    if (name.includes('piano') || name.includes('strategi') || description.includes('piano') || description.includes('strategi')) return 'strategy';
    if (name.includes('document') || name.includes('report') || description.includes('document') || description.includes('report')) return 'document';
    return 'general';
  };
  
  const getTaskIcon = (task) => {
    const type = determineTaskType(task);
    switch(type) {
      case 'analysis': return '🔍';
      case 'strategy': return '📈';
      case 'document': return '📄';
      default: return '📋';
    }
  };
  
  const formatTaskContent = (task) => {
    if (!task.result) return { 
      summary: 'Nessun risultato disponibile',
      keyPoints: [],
      details: ''
    };
    
    try {
      // Assumendo che result sia un oggetto JSON
      const result = typeof task.result === 'string' ? JSON.parse(task.result) : task.result;
      
      // Tenta di estrarre punti chiave dai dati del risultato
      let keyPoints = [];
      if (result.key_points) {
        keyPoints = result.key_points;
      } else if (result.insights) {
        keyPoints = result.insights;
      } else if (result.points) {
        keyPoints = result.points;
      } else if (result.steps) {
        keyPoints = result.steps;
      } else {
        // Crea punti chiave generici se non ne sono specificati
        keyPoints = [
          'Attività completata con successo',
          'Risultato generato dall\'agente ' + getAgentName(task.agent_id)
        ];
      }
      
      // Tenta di estrarre il sommario dai dati del risultato
      let summary = '';
      if (result.summary) {
        summary = result.summary;
      } else if (result.output) {
        summary = result.output;
      } else if (result.conclusion) {
        summary = result.conclusion;
      } else if (typeof result === 'string') {
        summary = result;
      } else {
        summary = 'Risultato completato con successo';
      }
      
      // Tenta di estrarre i dettagli dai dati del risultato
      let details = '';
      if (result.details) {
        details = result.details;
      } else if (result.full_output) {
        details = result.full_output;
      } else if (result.description) {
        details = result.description;
      } else if (typeof result === 'string') {
        details = result;
      } else {
        details = JSON.stringify(result, null, 2);
      }
      
      return {
        summary,
        keyPoints: Array.isArray(keyPoints) ? keyPoints : [keyPoints],
        details
      };
    } catch (e) {
      return { 
        summary: 'Risultato disponibile ma in formato non standard',
        keyPoints: ['Formato dati non standard', 'Richiede interpretazione'],
        details: typeof task.result === 'string' ? task.result : JSON.stringify(task.result, null, 2)
      };
    }
  };
  
  const getAgentEmoji = (role) => {
    const roleLower = (role || '').toLowerCase();
    if (roleLower.includes('project') || roleLower.includes('manager') || roleLower.includes('strategic')) return '🧠';
    if (roleLower.includes('content') || roleLower.includes('creat')) return '✍️';
    if (roleLower.includes('data') || roleLower.includes('analy')) return '📊';
    if (roleLower.includes('develop') || roleLower.includes('engineer')) return '💻';
    if (roleLower.includes('market') || roleLower.includes('promot')) return '📣';
    if (roleLower.includes('design')) return '🎨';
    if (roleLower.includes('research')) return '🔍';
    if (roleLower.includes('customer') || roleLower.includes('support')) return '🙋';
    return '👤';
  };
  
  const getRecentAgentActivity = (agent) => {
    if (!tasks || !agent) return 'Nessuna attività recente';
    
    const agentTasks = tasks.filter(t => t.agent_id === agent.id);
    if (!agentTasks.length) return 'Nessuna attività recente';
    
    const lastTask = agentTasks.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0];
    return `${lastTask.name} (${getStatusLabel(lastTask.status)})`;
  };
  
  // Costruisci l'elenco dei risultati
  const projectResults = React.useMemo(() => {
    if (!tasks) return [];
    
    return tasks
      .filter(task => task.status === 'completed' && task.result)
      .map(task => ({
        id: task.id,
        title: task.name,
        description: task.description || 'Nessuna descrizione',
        date: new Date(task.updated_at).toLocaleDateString(),
        type: determineTaskType(task),
        icon: getTaskIcon(task),
        creator: getAgentName(task.agent_id),
        content: formatTaskContent(task)
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [tasks, agents]);
  
  // Usa il primo risultato come default se ce ne sono
  useEffect(() => {
    if (projectResults.length > 0 && !activeResultId) {
      setActiveResultId(projectResults[0].id);
    }
  }, [projectResults, activeResultId]);
  
  // Filtra il risultato attivo
  const activeResult = projectResults.find(r => r.id === activeResultId);
  
  // Raggruppa task per una visualizzazione a timeline
  const projectPlan = React.useMemo(() => {
    if (!tasks) return [];
    
    return tasks
      .map(task => ({
        id: task.id,
        name: task.name,
        description: task.description,
        status: task.status,
        dueDate: task.deadline ? new Date(task.deadline).toLocaleDateString() : 'Non specificata',
        agent: getAgentName(task.agent_id),
        agentId: task.agent_id,
        createdAt: new Date(task.created_at).toLocaleDateString(),
        updatedAt: new Date(task.updated_at).toLocaleDateString()
      }))
      .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
  }, [tasks, agents]);
  
  // Calcola le dimensioni del team
  const teamDimensions = calculateTeamDimensions(agents);
  
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
      {/* Header con informazioni essenziali */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
          <div className="mb-4 md:mb-0">
            <div className="flex items-baseline">
              <h1 className="text-2xl font-bold">{workspace.name}</h1>
              <Link href="/projects" className="text-indigo-600 hover:underline text-sm ml-3">
                ← Progetti
              </Link>
            </div>
            <p className="text-gray-600 mt-1">{workspace.description}</p>
            
            {/* Obiettivo del progetto - evidenziato */}
            {workspace.goal && (
              <div className="mt-3 p-3 bg-indigo-50 border-l-4 border-indigo-500 rounded-r-md">
                <div className="flex items-start">
                  <span className="text-indigo-600 text-lg mr-2">🎯</span>
                  <div>
                    <p className="text-sm font-medium text-indigo-700">Obiettivo del progetto:</p>
                    <p className="text-sm text-indigo-900">{workspace.goal}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="flex space-x-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workspace.status)}`}>
              {getStatusLabel(workspace.status)}
            </span>
            <button 
              onClick={handleStartTeam} 
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
              disabled={isStartingTeam || workspace.status !== 'created'}
            >
              {isStartingTeam ? 'Avvio...' : workspace.status === 'created' ? 'Avvia Team' : 'Interagisci con il Team'}
            </button>
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Progresso Progetto</span>
            <span className="text-sm font-medium">{calculateProgress()}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${calculateProgress()}%` }}></div>
          </div>
        </div>
      </div>
      
      {/* Main navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button 
          onClick={() => setActiveSection('results')}
          className={`px-4 py-2 font-medium ${activeSection === 'results' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
        >
          💎 Risultati
        </button>
        <button 
          onClick={() => setActiveSection('plan')}
          className={`px-4 py-2 font-medium ${activeSection === 'plan' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
        >
          📋 Piano Attività
        </button>
        <button 
          onClick={() => setActiveSection('team')}
          className={`px-4 py-2 font-medium ${activeSection === 'team' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
        >
          👥 Team
        </button>
        <button 
          onClick={() => setActiveSection('details')}
          className={`px-4 py-2 font-medium ${activeSection === 'details' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
        >
          📊 Dettagli & Metriche
        </button>
      </div>
      
      {/* Contenuto basato sulla tab selezionata */}
      {activeSection === 'results' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Results list sidebar */}
          <div className="md:col-span-1 bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-lg font-semibold mb-4">Risultati Prodotti</h2>
            
            {projectResults.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <div className="text-5xl mb-3">📋</div>
                <p className="text-gray-600 mb-2">Nessun risultato disponibile</p>
                <p className="text-sm text-gray-500 mb-4">
                  {workspace.status === 'created' 
                    ? 'Avvia il team per iniziare a generare risultati' 
                    : 'Il team è al lavoro ma non ha ancora prodotto risultati'}
                </p>
                {workspace.status === 'created' && (
                  <button 
                    onClick={handleStartTeam}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                    disabled={isStartingTeam}
                  >
                    {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {projectResults.map(result => (
                  <div 
                    key={result.id} 
                    onClick={() => setActiveResultId(result.id)}
                    className={`p-3 rounded-lg cursor-pointer transition border ${
                      result.id === activeResultId 
                        ? 'border-indigo-300 bg-indigo-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start">
                      <div className="text-2xl mr-3">{result.icon}</div>
                      <div>
                        <h3 className="font-medium text-gray-900">{result.title}</h3>
                        <p className="text-sm text-gray-500">{result.description}</p>
                        <div className="flex items-center mt-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(result.type)}`}>
                            {result.type}
                          </span>
                          <span className="text-xs text-gray-500 ml-2">
                            {result.date}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {projectResults.length > 0 && (
              <button onClick={() => console.log('Richiedi nuovo output')} className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition text-sm">
                Richiedi Nuovo Output
              </button>
            )}
          </div>
          
{/* Result details - Versione migliorata */}
<div className="md:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden border border-gray-200">
  {activeResult ? (
    <>
      {/* Header migliorato */}
      <div className="bg-gray-50 border-b border-gray-200">
        <div className="flex justify-between items-center px-6 py-4">
          <div className="flex items-center">
            <span className="text-3xl mr-3">{activeResult.icon}</span>
            <div>
              <h2 className="text-xl font-semibold">{activeResult.title}</h2>
              <div className="flex items-center text-sm text-gray-500 mt-1">
                <span>{activeResult.creator}</span>
                <span className="mx-2">•</span>
                <span>{activeResult.date}</span>
                <span className={`ml-3 px-2 py-0.5 rounded-full text-xs ${getStatusColor(activeResult.type)}`}>
                  {activeResult.type}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            {/* Navigazione tra risultati */}
            {projectResults.length > 1 && (
              <div className="flex border border-gray-200 rounded-md overflow-hidden">
                <button 
                  onClick={() => {
                    const currentIndex = projectResults.findIndex(r => r.id === activeResultId);
                    if (currentIndex > 0) {
                      setActiveResultId(projectResults[currentIndex - 1].id);
                    }
                  }}
                  disabled={projectResults.findIndex(r => r.id === activeResultId) === 0}
                  className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Risultato precedente"
                >
                  ← 
                </button>
                <div className="px-3 py-2 border-l border-r border-gray-200 text-sm">
                  {projectResults.findIndex(r => r.id === activeResultId) + 1} di {projectResults.length}
                </div>
                <button 
                  onClick={() => {
                    const currentIndex = projectResults.findIndex(r => r.id === activeResultId);
                    if (currentIndex < projectResults.length - 1) {
                      setActiveResultId(projectResults[currentIndex + 1].id);
                    }
                  }}
                  disabled={projectResults.findIndex(r => r.id === activeResultId) === projectResults.length - 1}
                  className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Risultato successivo"
                >
                  →
                </button>
              </div>
            )}
            
            <button 
              onClick={() => {
                // Funzione per esportare il risultato come file JSON
                const task = tasks.find(t => t.id === activeResultId);
                if (task && task.result) {
                  const jsonStr = JSON.stringify(task.result, null, 2);
                  const blob = new Blob([jsonStr], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${task.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_result.json`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }
              }} 
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
            >
              <span className="mr-1">↓</span> Esporta
            </button>
          </div>
        </div>
      </div>
      
      {/* Contenuto principale con TaskResultDetails migliorato */}
      <div className="p-6">
        <TaskResultDetails result={tasks.find(t => t.id === activeResultId)?.result} />
        
        {/* Feedback e azioni */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <div className="flex space-x-3">
            <button 
              onClick={() => console.log('Chiedi modifiche', activeResultId)} 
              className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-md text-sm hover:bg-indigo-100 transition flex items-center"
            >
              <span className="mr-1">✏️</span> Chiedi Modifiche
            </button>
            <button 
              onClick={() => console.log('Commenta', activeResultId)} 
              className="px-4 py-2 bg-gray-50 text-gray-700 rounded-md text-sm hover:bg-gray-100 transition flex items-center"
            >
              <span className="mr-1">💬</span> Commenta
            </button>
          </div>
          
          <button 
            onClick={() => console.log('Approva', activeResultId)} 
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center"
          >
            <span className="mr-1">✓</span> Approva
          </button>
        </div>
      </div>
    </>
  ) : (
    <div className="flex flex-col items-center justify-center p-12">
      <div className="text-5xl mb-4">💎</div>
      <h3 className="text-xl font-medium text-gray-700 mb-2">Seleziona un risultato</h3>
      <p className="text-gray-500 text-center max-w-md">
        {projectResults.length > 0
          ? 'Seleziona un risultato dalla lista a sinistra per visualizzarne i dettagli'
          : 'Il team non ha ancora prodotto risultati'}
      </p>
      {/* CTA se nessun risultato disponibile */}
      {projectResults.length === 0 && workspace.status === 'created' && (
        <button 
          onClick={handleStartTeam}
          className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
          disabled={isStartingTeam}
        >
          {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
        </button>
      )}
    </div>
  )}
</div>
        </div>
      )}
      
      {activeSection === 'plan' && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-6">Piano di Esecuzione</h2>
          
          {projectPlan.length === 0 ? (
            <div className="text-center py-10 bg-gray-50 rounded-lg">
              <div className="text-5xl mb-3">📋</div>
              <p className="text-gray-600 mb-2">Nessuna attività pianificata</p>
              <p className="text-sm text-gray-500 mb-4">
                {workspace.status === 'created' 
                  ? 'Avvia il team per iniziare a generare il piano di lavoro' 
                  : 'Il team è al lavoro ma non ha ancora pianificato attività'}
              </p>
              {workspace.status === 'created' && (
                <button 
                  onClick={handleStartTeam}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  disabled={isStartingTeam}
                >
                  {isStartingTeam ? 'Avvio...' : 'Avvia Team'}
                </button>
              )}
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
              
              <div className="space-y-8">
                {projectPlan.map((task) => (
                  <div key={task.id} className="relative pl-12">
                    {/* Timeline circle */}
                    <div className={`absolute left-1.5 w-7 h-7 rounded-full flex items-center justify-center ${
                      task.status === 'completed' ? 'bg-green-500 text-white' :
                      task.status === 'in_progress' ? 'bg-blue-500 text-white' :
                      task.status === 'failed' ? 'bg-red-500 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {task.status === 'completed' ? '✓' : 
                       task.status === 'in_progress' ? '▶' : 
                       task.status === 'failed' ? '✕' : '⌛'}
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{task.name}</h3>
                          {task.description && (
                            <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                          )}
                          {task.agent && (
                            <p className="text-sm text-gray-600 mt-1">
                              Assegnato a: {task.agent}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center">
                          <span className={`text-xs px-3 py-1 rounded-full mr-3 ${getStatusColor(task.status)}`}>
                            {getStatusLabel(task.status)}
                          </span>
                          <span className="text-sm text-gray-500 whitespace-nowrap">
                            {task.dueDate}
                          </span>
                        </div>
                      </div>
                      
                      {task.status === 'in_progress' && (
                        <div className="mt-4 flex space-x-3">
                          <button 
                            onClick={() => console.log('View details', task.id)} 
                            className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
                          >
                            Dettagli
                          </button>
                          <button 
                            onClick={() => console.log('Interact with task', task.id)} 
                            className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                          >
                            Interagisci
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {projectPlan.length > 0 && (
            <div className="mt-8 flex justify-between">
              <button 
                onClick={() => console.log('View complete plan')} 
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
              >
                Visualizza Piano Completo
              </button>
              <button 
                onClick={() => console.log('Add new task')} 
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                Aggiungi Nuova Attività
              </button>
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'team' && (
        <div className="space-y-6">
          {/* Sezione Team Radar */}
          {agents.length > 1 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-lg font-semibold">Team Competency Matrix</h2>
                <button 
                  className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-md text-sm"
                  onClick={() => setShowTeamRadar(!showTeamRadar)}
                >
                  {showTeamRadar ? 'Nascondi grafico' : 'Mostra grafico'}
                </button>
              </div>
              
              {showTeamRadar && (
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg">
                  <div className="flex flex-col items-center">
                    <p className="text-purple-700 mb-4">
                      Questa visualizzazione mostra la competenza media del team su 6 dimensioni chiave
                    </p>
                    <AgentSkillRadarChart 
                      skills={teamDimensions} 
                      title="Team Matrix" 
                      size={450} 
                      colorScheme="team" 
                    />
                    
                    <div className="mt-6 w-full max-w-2xl">
                      <h4 className="text-md font-medium text-gray-800 mb-2">Dimensioni principali del team:</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {teamDimensions.map((dim, index) => (
                          <div key={index} className="bg-white p-2 rounded-md border border-gray-200 flex justify-between items-center">
                            <span className="text-sm font-medium">{dim.name}</span>
                            <div className="flex items-center">
                              <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                                <div 
                                  className="h-2 bg-purple-600 rounded-full"
                                  style={{ width: `${(dim.value / 5) * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs font-semibold">{dim.value}/5</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {agents.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center py-10">
                <div className="text-5xl mb-3">👥</div>
                <h3 className="text-lg font-medium text-gray-600 mb-2">Nessun agente nel team</h3>
                <p className="text-gray-500 mb-4">Configura il team per questo progetto</p>
                <Link 
                  href={`/projects/${workspaceId}/configure`}
                  className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                >
                  Configura Team
                </Link>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {agents.map(agent => (
                <div key={agent.id} className="bg-white rounded-xl shadow-sm p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-2xl">
                      {getAgentEmoji(agent.role)}
                    </div>
                    <div className="ml-3">
                      <h3 className="font-semibold">{agent.name}</h3>
                      <p className="text-gray-500 text-sm">{agent.role}</p>
                    </div>
                  </div>
                  
                  {/* Skill radar per ogni agente */}
                  <div className="mb-4">
                    <AgentDetailRadarSection agent={agent} />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Personalità:</span> {formatPersonalityTraits(agent.personality_traits)}
                      </p>
                    </div>
                    
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm text-blue-700">
                        <span className="font-medium">Attività Recente:</span> {getRecentAgentActivity(agent)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex space-x-3">
                    <button 
                      onClick={() => handleInteractWithAgent(agent)}
                      className="flex-1 px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                    >
                      Interagisci
                    </button>
                    <button 
                      onClick={() => handleEditAgent(agent)}
                      className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition"
                    >
                      Profilo
                    </button>
                  </div>
                </div>
              ))}
              
              {/* Sezione comunicazione di team */}
              {agents.length > 0 && (
                <div className="md:col-span-3 bg-white rounded-xl shadow-sm p-6">
                  <h3 className="font-semibold mb-4">Comunicazione di Team</h3>
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="space-y-4 max-h-64 overflow-y-auto">
                      {/* Mock di comunicazioni del team */}
                      {agents.length >= 2 && (
                        <>
                          <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                            <div className="flex items-start">
                              <div className="text-xl mr-2">{getAgentEmoji(agents[0].role)}</div>
                              <div>
                                <div className="flex items-center">
                                  <span className="font-medium">{agents[0].name}</span>
                                  <span className="ml-2 text-xs text-gray-500">recentemente</span>
                                </div>
                                <p className="text-sm mt-1">Sto lavorando sulle attività assegnate secondo il piano di progetto. Ci sono aspetti specifici su cui vorresti che mi concentrassi?</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                            <div className="flex items-start">
                              <div className="text-xl mr-2">{getAgentEmoji(agents[1].role)}</div>
                              <div>
                                <div className="flex items-center">
                                  <span className="font-medium">{agents[1].name}</span>
                                  <span className="ml-2 text-xs text-gray-500">recentemente</span>
                                </div>
                                <p className="text-sm mt-1">Ho completato l'analisi iniziale e sono pronto a procedere con le fasi successive del progetto. Collaborerò con il resto del team per garantire coerenza nell'approccio.</p>
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                    
                    <div className="mt-4 flex">
                      <input 
                        type="text" 
                        placeholder="Scrivi un messaggio al team..." 
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                      <button 
                        onClick={() => console.log('Send message to team')}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-r-md hover:bg-indigo-700 transition"
                      >
                        Invia
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'details' && (
        <div className="space-y-6">
          {/* Budget info */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Metriche e Dettagli Avanzati</h2>
            <p className="text-gray-500 mb-6">Visualizza statistiche dettagliate, monitoraggio costi e altre metriche del progetto.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                <h3 className="font-medium text-blue-800 mb-2">Budget Utilizzato</h3>
                <p className="text-3xl font-bold text-blue-900">
                  {stats?.budget?.total_cost?.toFixed(2) || '0.00'} {workspace.budget?.currency || 'EUR'}
                </p>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${calculateBudgetUsage()}%` }}></div>
                </div>
                <p className="text-xs text-blue-700 mt-1">
                  {calculateBudgetUsage()}% del budget totale ({workspace.budget?.max_amount || 0} {workspace.budget?.currency || 'EUR'})
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                <h3 className="font-medium text-green-800 mb-2">Task Completati</h3>
                <p className="text-3xl font-bold text-green-900">
                  {tasks.filter(t => t.status === 'completed').length} / {tasks.length}
                </p>
                <div className="mt-2 w-full bg-green-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: `${calculateProgress()}%` }}></div>
                </div>
                <p className="text-xs text-green-700 mt-1">{calculateProgress()}% dei task totali</p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                <h3 className="font-medium text-purple-800 mb-2">Agenti Attivi</h3>
                <p className="text-3xl font-bold text-purple-900">
                  {agents.filter(a => a.status === 'active').length} / {agents.length}
                </p>
                <div className="mt-2 w-full bg-purple-200 rounded-full h-2">
                  <div className="bg-purple-600 h-2 rounded-full" 
                    style={{ width: `${agents.length ? (agents.filter(a => a.status === 'active').length / agents.length) * 100 : 0}%` }}></div>
                </div>
                <p className="text-xs text-purple-700 mt-1">
                  {agents.filter(a => a.status === 'active').length} agenti attivi su {agents.length} totali
                </p>
              </div>
            </div>
            
            {/* Project insights dashboard */}
            <ProjectInsightsDashboard workspaceId={workspaceId} />
              
              <ProjectActionsSection 
  workspace={workspace}
  onStartTeam={handleStartTeam}
  onDeleteClick={onDeleteClick} 
  isStartingTeam={isStartingTeam}
  feedbackRequests={feedbackRequests}
/>
            
            <div className="text-center mt-6">
              <Link 
                href={`/projects/${workspaceId}/monitoring`}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                Visualizza Dashboard Completa
              </Link>
            </div>
          </div>
          
          {/* Feedback section */}
          {feedbackRequests.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Richieste di Feedback</h2>
              <div className="space-y-4">
                {feedbackRequests.map(request => (
                  <div 
                    key={request.id}
                    className={`p-4 rounded-lg border ${
                      request.priority === 'high' ? 'border-red-200 bg-red-50' :
                      request.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                      'border-blue-200 bg-blue-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{request.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        request.priority === 'high' ? 'bg-red-200 text-red-800' :
                        request.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {request.priority.toUpperCase()}
                      </span>
                    </div>
                    <div className="mt-3 flex space-x-3">
                      <Link
                        href={`/human-feedback?id=${request.id}`}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                      >
                        Rispondi
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Quick action buttons */}
      <div className="fixed bottom-8 right-8 flex flex-col space-y-4">
        <button 
          onClick={handleStartTeam}
          className="w-12 h-12 bg-green-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-green-700 transition"
          disabled={isStartingTeam || workspace.status !== 'created'}
          title={workspace.status === 'created' ? 'Avvia Team' : 'Team già attivo'}
        >
          <span className="text-xl">{isStartingTeam ? '⏳' : workspace.status === 'created' ? '▶️' : '✓'}</span>
        </button>
        <button 
          onClick={() => setActiveSection('team')}
          className="w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-indigo-700 transition"
          title="Interagisci con il Team"
        >
          <span className="text-xl">💬</span>
        </button>
      </div>
      
      {/* Mantieni i modali esistenti */}
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