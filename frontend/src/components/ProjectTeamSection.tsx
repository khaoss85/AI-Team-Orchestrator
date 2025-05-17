import React from 'react';
import Link from 'next/link';
import { Workspace, Agent } from '@/types';

interface ProjectTeamSectionProps {
  workspace: Workspace;
  agents: Agent[];
  workspaceId: string;
}

export default function ProjectTeamSection({ workspace, agents, workspaceId }: ProjectTeamSectionProps) {
  // Funzioni helper per la visualizzazione
  const getSeniorityColor = (seniority: string) => {
    switch(seniority) {
      case 'junior': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'senior': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'expert': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'created': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getHealthColor = (health: any) => {
    const status = health?.status || 'unknown';
    switch(status) {
      case 'healthy': return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'unhealthy': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Raggruppa agenti per ruolo
  const agentsByRole = React.useMemo(() => {
    const roleGroups: Record<string, Agent[]> = {};
    
    agents.forEach(agent => {
      const role = agent.role;
      if (!roleGroups[role]) {
        roleGroups[role] = [];
      }
      roleGroups[role].push(agent);
    });
    
    return roleGroups;
  }, [agents]);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold">Team di Agenti AI</h2>
          <p className="text-gray-500">
            {agents.length} agenti stanno lavorando su questo progetto
          </p>
        </div>
        
        <Link 
          href={`/projects/${workspaceId}/team`}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition inline-flex items-center"
        >
          <span>Gestisci Team</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </Link>
      </div>
      
      {agents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-5xl mb-3">👥</div>
          <p className="text-gray-600 text-lg mb-2">Nessun agente configurato</p>
          <p className="text-gray-500 text-sm mb-4">Configura il team del progetto per iniziare</p>
          <Link
            href={`/projects/${workspaceId}/configure`}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Configura Team
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Visualizzazione a team con raggruppamento per ruolo */}
          {Object.entries(agentsByRole).map(([role, roleAgents]) => (
            <div key={role} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-lg mb-3 border-b pb-2">{role}</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {roleAgents.map(agent => (
                  <div key={agent.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition">
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium">{agent.name}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                        {agent.seniority}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1 mb-3 line-clamp-2">
                      {agent.description || `Agente specializzato in ${agent.role}`}
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getHealthColor(agent.health)}`}>
                        {agent.health?.status || 'unknown'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          
          {/* Link alla vista dettagliata del team */}
          <div className="text-center pt-4">
            <Link 
              href={`/projects/${workspaceId}/team`}
              className="text-indigo-600 hover:text-indigo-800 text-sm font-medium inline-flex items-center"
            >
              <span>Visualizza dettagli completi del team</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}