import React from 'react';
import AgentSkillRadarChart, { calculateAgentDimensions } from './AgentSkillRadarChart';

interface AgentDetailRadarSectionProps {
  agent: any;
}

const AgentDetailRadarSection: React.FC<AgentDetailRadarSectionProps> = ({ agent }) => {
  if (!agent) return null;
  
  // Calcola le dimensioni dell'agente per il radar chart
  const agentDimensions = calculateAgentDimensions(agent);
  
  return (
    <div className="border border-gray-200 rounded-lg p-5">
      <h3 className="text-md font-medium text-gray-900 mb-4">Profilo di Competenza</h3>
      
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-4 rounded-lg">
        <div className="flex flex-col items-center">
          <AgentSkillRadarChart 
            skills={agentDimensions} 
            title={`Competency Matrix - ${agent.name}`}
            size={400}
          />
          
          <div className="mt-5 w-full">
            <h4 className="text-sm font-medium text-gray-800 mb-2">Dimensioni rappresentate:</h4>
            <div className="grid grid-cols-2 gap-3">
              {agentDimensions.map((dim, index) => (
                <div key={index} className="bg-white p-2 rounded-md border border-gray-200 flex justify-between items-center">
                  <span className="text-sm font-medium">{dim.name}</span>
                  <div className="flex items-center">
                    <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                      <div 
                        className="h-2 bg-indigo-600 rounded-full"
                        style={{ width: `${(dim.value / 5) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-semibold">{dim.value}/5</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              <p>I valori sono calcolati in base al livello di skill e ai tratti di personalità dell'agente.</p>
              <p>Le 6 dimensioni più rilevanti sono state selezionate automaticamente in base ai punteggi.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDetailRadarSection;