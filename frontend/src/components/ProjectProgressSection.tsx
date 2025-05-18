import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Workspace, Task, Agent } from '@/types';

interface ProjectProgressSectionProps {
  workspace: Workspace;
  tasks: Task[];
  agents: Agent[]; // Aggiungiamo gli agenti per mostrare il responsabile
  tasksLoading: boolean;
  workspaceId: string;
}

export default function ProjectProgressSection({ 
  workspace, 
  tasks, 
  agents,
  tasksLoading, 
  workspaceId 
}: ProjectProgressSectionProps) {
  // Stati esistenti
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // Nuovo stato per le fasi espanse
  const [expandedPhases, setExpandedPhases] = useState<Record<string, boolean>>({});
  
  // Funzione per determinare la fase di un task in base al nome o descrizione
  const getTaskPhase = (task: Task): string => {
    const name = task.name.toLowerCase();
    const description = (task.description || '').toLowerCase();
    const content = name + ' ' + description;
    
    if (content.includes('iniz') || content.includes('pianific') || content.includes('prep')) {
      return 'Pianificazione';
    } else if (content.includes('ricerca') || content.includes('analis') || content.includes('stud')) {
      return 'Analisi';
    } else if (content.includes('svilupp') || content.includes('crea') || content.includes('implement')) {
      return 'Sviluppo';
    } else if (content.includes('test') || content.includes('verif') || content.includes('valid')) {
      return 'Testing';
    } else if (content.includes('ottimiz') || content.includes('miglior') || content.includes('refin')) {
      return 'Ottimizzazione';
    } else if (content.includes('presenta') || content.includes('review') || content.includes('finalizz')) {
      return 'Finalizzazione';
    }
    
    return 'Altro';
  };
  
  // Raggruppamento dei task per fase
  const tasksByPhase = React.useMemo(() => {
    const grouped: Record<string, Task[]> = {};
    
    let filtered = tasks;
    
    // Applica filtri
    if (filterStatus !== 'all') {
      filtered = filtered.filter(task => task.status === filterStatus);
    }
    
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(task => 
        task.name.toLowerCase().includes(term) || 
        (task.description || '').toLowerCase().includes(term)
      );
    }
    
    // Ordina
    filtered = filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    // Raggruppa per fase
    filtered.forEach(task => {
      const phase = getTaskPhase(task);
      if (!grouped[phase]) {
        grouped[phase] = [];
      }
      grouped[phase].push(task);
    });
    
    return grouped;
  }, [tasks, filterStatus, searchTerm, sortBy, sortOrder]);
  
  // Calcolo statistiche per fase
  const phaseStats = React.useMemo(() => {
    const stats: Record<string, { total: number, completed: number, percentage: number }> = {};
    
    Object.entries(tasksByPhase).forEach(([phase, phaseTasks]) => {
      const total = phaseTasks.length;
      const completed = phaseTasks.filter(t => t.status === 'completed').length;
      const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
      
      stats[phase] = { total, completed, percentage };
    });
    
    return stats;
  }, [tasksByPhase]);
  
  // Toggle di espansione/collasso di una fase
  const togglePhase = (phase: string) => {
    setExpandedPhases(prev => ({
      ...prev,
      [phase]: !prev[phase]
    }));
  };
  
  // Inizializza le fasi espanse
  useEffect(() => {
    const phases = Object.keys(tasksByPhase);
    // Espandi di default solo la prima fase o la fase con task in corso
    const initialExpanded: Record<string, boolean> = {};
    
    if (phases.length > 0) {
      // Cerca una fase che ha task in corso
      const phaseWithInProgress = phases.find(phase => 
        tasksByPhase[phase].some(task => task.status === 'in_progress')
      );
      
      if (phaseWithInProgress) {
        initialExpanded[phaseWithInProgress] = true;
      } else if (phases[0]) {
        initialExpanded[phases[0]] = true;
      }
    }
    
    setExpandedPhases(initialExpanded);
  }, [tasksByPhase]);
  
  // Helper per le icone e i colori
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };
  
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'completed': return 'Completato';
      case 'in_progress': return 'In Corso';
      case 'pending': return 'In Attesa';
      case 'failed': return 'Fallito';
      default: return status;
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'completed': return '✅';
      case 'in_progress': return '🔄';
      case 'pending': return '⏳';
      case 'failed': return '❌';
      default: return '❓';
    }
  };
  
  const getPhaseIcon = (phase: string) => {
    switch(phase) {
      case 'Pianificazione': return '📝';
      case 'Analisi': return '🔍';
      case 'Sviluppo': return '⚙️';
      case 'Testing': return '🧪';
      case 'Ottimizzazione': return '📈';
      case 'Finalizzazione': return '🎯';
      default: return '📋';
    }
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Trova il nome dell'agente responsabile
  const getAgentName = (agentId?: string) => {
    if (!agentId) return 'Non assegnato';
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Agente sconosciuto';
  };
  
  // Estrai il risultato principale da un task completato
  const getTaskResult = (task: Task) => {
    if (task.status !== 'completed' || !task.result) return null;
    
    if (typeof task.result === 'object') {
      return task.result.summary || task.result.output || 'Task completato';
    }
    
    return 'Task completato';
  };
  
  if (tasksLoading && tasks.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento attività...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold">
            Piano di Lavoro
            <span className="ml-2 text-sm text-gray-500">({tasks.length} task totali)</span>
          </h2>
          <p className="text-gray-500">Visualizzazione per fasi del progetto</p>
        </div>
        
        <Link 
          href={`/projects/${workspaceId}/tasks`}
          className="mt-3 md:mt-0 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition inline-flex items-center"
        >
          <span>Vista Dettagliata</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </Link>
      </div>
      
      {/* Filtri e ricerca */}
      <div className="bg-gray-50 p-4 rounded-lg mb-5 border border-gray-200">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Cerca Task</label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Cerca per nome o descrizione..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>
          
          <div>
            <label htmlFor="filter" className="block text-sm font-medium text-gray-700 mb-1">Filtra per stato</label>
            <select
              id="filter"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="all">Tutti</option>
              <option value="pending">In Attesa</option>
              <option value="in_progress">In Corso</option>
              <option value="completed">Completati</option>
              <option value="failed">Falliti</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-1">Ordina per</label>
            <select
              id="sort"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="updated_at">Ultimo aggiornamento</option>
              <option value="created_at">Data creazione</option>
              <option value="name">Nome</option>
              <option value="status">Stato</option>
            </select>
          </div>
          
          <div className="hidden md:flex items-end">
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
      
        {/* Timeline migliorata */}
        <div className="mb-6 overflow-x-auto">
          <div className="relative flex items-center justify-between min-w-max py-6">
            {Object.entries(phaseStats).map(([phase, stats], index, array) => (
              <div key={phase} className="flex flex-col items-center px-8 relative">
                {/* Nodo della fase */}
                <div 
                  className={`w-14 h-14 rounded-full flex items-center justify-center shadow-md ${
                    stats.percentage === 100 ? 'bg-green-500 text-white' : 
                    stats.percentage > 0 ? 'bg-blue-500 text-white' : 
                    'bg-gray-200 text-gray-700'
                  }`}
                >
                  <span className="text-2xl">{getPhaseIcon(phase)}</span>
                </div>

                {/* Nome fase e progresso */}
                <div className="text-sm font-medium mt-2 text-center">{phase}</div>
                <div className="flex items-center mt-1">
                  <div className="w-16 bg-gray-200 rounded-full h-1.5 mr-2">
                    <div
                      className={`h-1.5 rounded-full ${stats.percentage === 100 ? 'bg-green-500' : 'bg-blue-500'}`}
                      style={{ width: `${stats.percentage}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600">{stats.percentage}%</span>
                </div>

                {/* Linea di connessione */}
                {index < array.length - 1 && (
                  <div className="absolute h-0.5 bg-gray-300 w-16 left-full top-1/2 transform -translate-y-1/2 -translate-x-4">
                    <div 
                      className="absolute h-0.5 bg-green-500" 
                      style={{ width: `${stats.percentage}%`, maxWidth: '100%' }}
                    ></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      
      {/* Sezioni per fase */}
      <div className="space-y-4">
        {Object.keys(tasksByPhase).length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-5xl mb-3">📋</div>
            <p className="text-gray-600 text-lg mb-1">Nessun task trovato</p>
            <p className="text-gray-500 text-sm">Modifica i filtri di ricerca o crea nuovi task</p>
          </div>
        ) : (
          Object.entries(tasksByPhase).map(([phase, phaseTasks]) => {
            const stats = phaseStats[phase];
            
            return (
              <div key={phase} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Intestazione della fase */}
                <div 
                  className="bg-gray-50 p-4 flex justify-between items-center cursor-pointer"
                  onClick={() => togglePhase(phase)}
                >
                  <div className="flex items-center">
                    <span className="text-xl mr-3">{getPhaseIcon(phase)}</span>
                    <div>
                      <h3 className="font-medium text-gray-800">{phase}</h3>
                      <p className="text-sm text-gray-500">
                        {stats.completed} di {stats.total} task completati ({stats.percentage}%)
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {/* Barra di progresso */}
                    <div className="hidden md:flex items-center w-32">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div 
                          className="bg-green-600 h-2.5 rounded-full"
                          style={{ width: `${stats.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    {/* Icona espandi/collassa */}
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className={`h-5 w-5 transform transition-transform ${expandedPhases[phase] ? 'rotate-180' : 'rotate-0'}`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                
                {/* Task della fase (collassabili) */}
                {expandedPhases[phase] && (
                  <div className="p-4 border-t border-gray-200 divide-y divide-gray-100">
                    {phaseTasks.map((task) => {
                      const taskResult = getTaskResult(task);
                      
                      return (
                        <div key={task.id} className="py-4 first:pt-0 last:pb-0 hover:bg-gray-50 p-2 rounded-md transition-colors">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-lg">{getStatusIcon(task.status)}</span>
                                <h3 className="font-medium">{task.name}</h3>
                                <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(task.status)}`}>
                                  {getStatusLabel(task.status)}
                                </span>
                              </div>
                              
                              {task.description && (
                                <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                                  {task.description}
                                </p>
                              )}
                              
                              {/* Informazioni aggiuntive */}
                              <div className="text-sm text-gray-500 mt-2">
                                <div className="flex flex-wrap gap-y-1 gap-x-4">
                                  <span>👤 {getAgentName(task.agent_id)}</span>
                                  <span>📅 Creato: {formatDate(task.created_at)}</span>
                                  <span>🔄 Aggiornato: {formatDate(task.updated_at)}</span>
                                </div>
                              </div>
                              
                              {/* Risultato del task se completato */}
                              {taskResult && (
                                <div className="mt-3 bg-green-50 p-2 rounded border border-green-100">
                                  <p className="text-sm text-green-700 font-medium">Risultato:</p>
                                  <p className="text-sm text-green-800">{taskResult}</p>
                                </div>
                              )}
                              
                              {/* Error se fallito */}
                              {task.status === 'failed' && task.result && (
                                <div className="mt-3 bg-red-50 p-2 rounded border border-red-100">
                                  <p className="text-sm text-red-700">
                                    {typeof task.result === 'object' && task.result.error 
                                      ? task.result.error 
                                      : 'Task fallito'}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
      
      {/* Link alla vista completa */}
      <div className="mt-6 text-center">
        <Link 
          href={`/projects/${workspaceId}/tasks`}
          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium inline-flex items-center"
        >
          <span>Visualizza tutti i task</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </Link>
      </div>
    </div>
  );
}