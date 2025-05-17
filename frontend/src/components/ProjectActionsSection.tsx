import React from 'react';
import Link from 'next/link';
import { Workspace } from '@/types';

interface ProjectActionsSectionProps {
  workspace: Workspace;
  onStartTeam: () => void;
  onDeleteClick: () => void;
  isStartingTeam: boolean;
  feedbackRequests: any[];
}

export default function ProjectActionsSection({ 
  workspace, 
  onStartTeam, 
  onDeleteClick, 
  isStartingTeam,
  feedbackRequests
}: ProjectActionsSectionProps) {
  return (
    <div className="space-y-6">
      {/* Human Feedback Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">🤝 Richieste di Feedback</h2>
        
        {feedbackRequests.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <p className="text-lg text-gray-600 mb-2">Nessuna richiesta di feedback in attesa</p>
            <p className="text-sm text-gray-500">
              Verrai notificato quando un agente richiede la tua approvazione o input
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {feedbackRequests.map((request) => (
              <div 
                key={request.id} 
                className={`border rounded-lg p-4 ${
                  request.priority === 'high' 
                    ? 'border-red-300 bg-red-50' 
                    : request.priority === 'medium'
                    ? 'border-yellow-300 bg-yellow-50'
                    : 'border-blue-300 bg-blue-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{request.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    request.priority === 'high' 
                      ? 'bg-red-200 text-red-800' 
                      : request.priority === 'medium'
                      ? 'bg-yellow-200 text-yellow-800'
                      : 'bg-blue-200 text-blue-800'
                  }`}>
                    {request.priority.toUpperCase()}
                  </span>
                </div>
                
                <div className="mt-3 space-y-2">
                  <p className="text-sm font-medium">Azioni proposte:</p>
                  {request.proposed_actions.map((action, index) => (
                    <div key={index} className="bg-white bg-opacity-60 p-2 rounded border border-gray-200">
                      <p className="text-sm">
                        <span className="font-medium">{action.type}:</span> {action.description}
                      </p>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 flex space-x-3">
                  <Link 
                    href={`/human-feedback?id=${request.id}`}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  >
                    Rispondi
                  </Link>
                </div>
              </div>
            ))}
            
            <Link 
              href="/human-feedback"
              className="block text-center text-indigo-600 hover:text-indigo-800 text-sm"
            >
              Visualizza tutte le richieste →
            </Link>
          </div>
        )}
      </div>
      
      {/* Project Control Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">⚙️ Azioni di Controllo</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Avvio Team / Stato */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="font-medium mb-2">Stato Team</h3>
            
            {workspace.status === 'created' ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Il team è configurato ma non è ancora stato avviato. Avvia il team per iniziare a lavorare sul progetto.
                </p>
                <button 
                  onClick={onStartTeam}
                  disabled={isStartingTeam}
                  className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center disabled:opacity-50"
                >
                  {isStartingTeam ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                      Avvio in corso...
                    </>
                  ) : (
                    <>
                      <span className="mr-2">🚀</span>
                      Avvia Team
                    </>
                  )}
                </button>
              </div>
            ) : workspace.status === 'active' ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Il team è attivo e sta lavorando sul progetto. Puoi visualizzare i dettagli delle attività nella sezione "Attività".
                </p>
                <div className="flex">
                  <Link 
                    href={`/projects/${workspace.id}/tasks`}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition mr-2"
                  >
                    Visualizza Attività
                  </Link>
                  <Link 
                    href={`/projects/${workspace.id}/team`}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  >
                    Gestisci Team
                  </Link>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Stato attuale del progetto: <span className="font-medium">{workspace.status}</span>
                </p>
                <Link 
                  href={`/projects/${workspace.id}/configure`}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                >
                  Configura Team
                </Link>
              </div>
            )}
          </div>

          {/* Gestione Deliverables */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 className="font-medium mb-2">Deliverables e Risultati</h3>
            <p className="text-sm text-gray-600 mb-3">
              Visualizza e gestisci i risultati finali del progetto, inclusi documenti, analisi e raccomandazioni.
            </p>
            <Link 
              href={`/projects/${workspace.id}/deliverables`}
              className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition"
            >
              Visualizza Deliverables
            </Link>
          </div>
          
          {/* Tools Configuration */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <h3 className="font-medium mb-2">Strumenti e Tool</h3>
            <p className="text-sm text-gray-600 mb-3">
              Configura e gestisci gli strumenti disponibili per gli agenti del progetto.
            </p>
            <Link 
              href="/tools"
              className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition"
            >
              Gestisci Tool
            </Link>
          </div>
          
          {/* Project Removal */}
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <h3 className="font-medium mb-2">Eliminazione Progetto</h3>
            <p className="text-sm text-gray-600 mb-3">
              Attenzione: questa azione eliminerà permanentemente il progetto e tutti i dati associati.
            </p>
            <button 
              onClick={onDeleteClick}
              className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 transition"
            >
              Elimina Progetto
            </button>
          </div>
        </div>
      </div>
      
      {/* Advanced Options */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">🔧 Opzioni Avanzate</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Monitoraggio Avanzato</h3>
            <p className="text-sm text-gray-600 mb-3">
              Accedi alle funzionalità avanzate di monitoraggio e statistiche del progetto.
            </p>
            <Link 
              href={`/projects/${workspace.id}/monitoring`}
              className="px-4 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
            >
              Monitoraggio Avanzato
            </Link>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Gestione Budget</h3>
            <p className="text-sm text-gray-600 mb-3">
              Visualizza e modifica le impostazioni di budget del progetto.
            </p>
            <Link 
              href={`/projects/${workspace.id}/budget`}
              className="px-4 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
            >
              Gestione Budget
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}