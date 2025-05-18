import React from 'react';
import { Workspace } from '@/types';

interface ProjectBudgetSectionProps {
  workspace: Workspace;
  stats: any;
}

export default function ProjectBudgetSection({ workspace, stats }: ProjectBudgetSectionProps) {
  // Calcolo delle metriche del budget
  const budget = workspace.budget?.max_amount || 0;
  const currency = workspace.budget?.currency || 'EUR';
  const spent = stats?.budget?.total_cost || 0;
  const budgetPercentage = budget ? Math.round((spent / budget) * 100) : 0;
  
  // Dati agente mock (sostituire con dati reali se disponibili)
  const agentCosts = stats?.budget?.agent_costs || {
    "Agent 1": spent * 0.4,
    "Agent 2": spent * 0.3,
    "Agent 3": spent * 0.2,
    "Altri agenti": spent * 0.1
  };
  
  // Token usage (mock - sostituire con dati reali)
  const tokenUsage = stats?.budget?.total_tokens || {
    input: 1000000,
    output: 500000
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Analisi Budget</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Budget totale e speso */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-5 rounded-lg border border-blue-200 shadow-sm">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-blue-800 font-semibold">Budget Totale</h3>
            <span className="text-blue-700 text-lg font-bold">{budget} {currency}</span>
          </div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-blue-700">Speso</span>
            <span className="text-blue-700 font-medium">{spent.toFixed(2)} {currency}</span>
          </div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-blue-700">Rimanente</span>
            <span className="text-blue-700 font-medium">{(budget - spent).toFixed(2)} {currency}</span>
          </div>
          <div className="mt-3">
            <div className="flex justify-between text-xs mb-1">
              <span>Utilizzo</span>
              <span>{budgetPercentage}%</span>
            </div>
            <div className="w-full bg-white rounded-full h-2.5">
              <div 
                className={`h-2.5 rounded-full ${
                  budgetPercentage > 90 ? 'bg-red-500' :
                  budgetPercentage > 70 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${budgetPercentage}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        {/* Breakdown per agente */}
        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-5 rounded-lg border border-purple-200 shadow-sm">
          <h3 className="text-purple-800 font-semibold mb-3">Distribuzione Costi</h3>
          <div className="space-y-2">
            {Object.entries(agentCosts).map(([agent, cost], index) => (
              <div key={index}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-purple-700">{agent}</span>
                  <span className="text-purple-700">{typeof cost === 'number' ? cost.toFixed(2) : cost} {currency}</span>
                </div>
                <div className="w-full bg-white rounded-full h-1.5">
                  <div 
                    className="h-1.5 rounded-full bg-purple-500"
                    style={{ width: `${(typeof cost === 'number' ? cost : 0) / spent * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Utilizzo token */}
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-5 rounded-lg border border-green-200 shadow-sm">
          <h3 className="text-green-800 font-semibold mb-3">Utilizzo Token</h3>
          <div className="flex flex-col h-40 justify-center">
            <div className="relative h-20 w-full mb-2">
              <div className="absolute bottom-0 left-0 w-2/3 h-16 bg-green-300 rounded"></div>
              <div className="absolute bottom-0 right-0 w-1/3 h-10 bg-green-500 rounded"></div>
              <div className="absolute -bottom-6 left-0 text-xs text-green-700">Input: {tokenUsage.input.toLocaleString()}</div>
              <div className="absolute -bottom-6 right-0 text-xs text-green-700 text-right">Output: {tokenUsage.output.toLocaleString()}</div>
            </div>
            <div className="text-center mt-8 text-sm text-green-700">
              <div>Totale: {(tokenUsage.input + tokenUsage.output).toLocaleString()} token</div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="text-right">
        <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
          Visualizza analisi dettagliata →
        </button>
      </div>
    </div>
  );
}