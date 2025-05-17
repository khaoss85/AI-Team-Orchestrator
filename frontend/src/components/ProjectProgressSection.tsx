import React, { useState } from 'react';
import Link from 'next/link';
import { Workspace, Task } from '@/types';

interface ProjectProgressSectionProps {
  workspace: Workspace;
  tasks: Task[];
  tasksLoading: boolean;
  workspaceId: string;
}

export default function ProjectProgressSection({ workspace, tasks, tasksLoading, workspaceId }: ProjectProgressSectionProps) {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // Filtro e ordinamento dei task
  const filteredAndSortedTasks = React.useMemo(() => {
    let filtered = tasks;
    
    // Filtra per stato
    if (filterStatus !== 'all') {
      filtered = filtered.filter(task => task.status === filterStatus);
    }
    
    // Filtra per testo di ricerca
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(task => 
        task.name.toLowerCase().includes(term) || 
        (task.description || '').toLowerCase().includes(term)
      );
    }
    
    // Ordinamento
    return filtered.sort((a, b) => {
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
  }, [tasks, filterStatus, searchTerm, sortBy, sortOrder]);
  
  // Funzioni helper per stilizzazione
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
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
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
            Task del Progetto 
            <span className="ml-2 text-sm text-gray-500">({tasks.length} totali)</span>
          </h2>
          <p className="text-gray-500">Gestisci e monitora le attività del progetto</p>
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
      
      {/* Lista tasks */}
      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
        {filteredAndSortedTasks.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-5xl mb-3">📋</div>
            <p className="text-gray-600 text-lg mb-1">Nessun task trovato</p>
            <p className="text-gray-500 text-sm">Modifica i filtri di ricerca o crea nuovi task</p>
          </div>
        ) : (
          filteredAndSortedTasks.map((task) => (
            <div key={task.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
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
                  
                  {task.result && task.status === 'completed' && (
                    <div className="mt-2 bg-green-50 p-2 rounded border border-green-100">
                      <p className="text-sm text-green-700">
                        {typeof task.result === 'object' && task.result.summary 
                          ? task.result.summary 
                          : 'Task completato con successo'}
                      </p>
                    </div>
                  )}
                  
                  {task.result && task.status === 'failed' && (
                    <div className="mt-2 bg-red-50 p-2 rounded border border-red-100">
                      <p className="text-sm text-red-700">
                        {typeof task.result === 'object' && task.result.error 
                          ? task.result.error 
                          : 'Task fallito'}
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="text-right text-xs text-gray-500">
                  <div>Aggiornato: {formatDate(task.updated_at)}</div>
                  <div>Creato: {formatDate(task.created_at)}</div>
                </div>
              </div>
            </div>
          ))
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