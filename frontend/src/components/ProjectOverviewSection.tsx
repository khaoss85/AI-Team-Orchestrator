import React, { useState } from 'react';
import { Workspace, Agent, Task } from '@/types';

interface ProjectOverviewSectionProps {
  workspace: Workspace;
  tasks: Task[];
  agents: Agent[];
  stats: any;
}

export default function ProjectOverviewSection({ workspace, tasks, agents, stats }: ProjectOverviewSectionProps) {
  // Calcoli per metriche e statistiche
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length;
  const pendingTasks = tasks.filter(t => t.status === 'pending').length;
  const failedTasks = tasks.filter(t => t.status === 'failed').length;
  
  const completionPercentage = tasks.length ? Math.round((completedTasks / tasks.length) * 100) : 0;
  
  // Raggruppamento task per categoria/tipo
  const groupTasksByPhase = () => {
    const phases: Record<string, number> = {};
    
    tasks.forEach(task => {
      // Logica semplificata per determinare la fase dal nome del task
      let phase = 'Altro';
      const name = task.name.toLowerCase();
      
      if (name.includes('analis') || name.includes('ricerca') || name.includes('studio')) {
        phase = 'Analisi';
      } else if (name.includes('pianifica') || name.includes('strategi') || name.includes('progetta')) {
        phase = 'Pianificazione';
      } else if (name.includes('svilupp') || name.includes('crea') || name.includes('implementa')) {
        phase = 'Sviluppo';
      } else if (name.includes('test') || name.includes('verifica') || name.includes('valida')) {
        phase = 'Testing';
      } else if (name.includes('ottimizza') || name.includes('migliora') || name.includes('refine')) {
        phase = 'Ottimizzazione';
      }
      
      phases[phase] = (phases[phase] || 0) + 1;
    });
    
    return phases;
  };
  
  const phases = groupTasksByPhase();
  
  // Calcolo delle statistiche del budget
  const budget = workspace.budget?.max_amount || 0;
  const currency = workspace.budget?.currency || 'EUR';
  const spent = stats?.budget?.total_cost || 0;
  const budgetPercentage = budget ? Math.round((spent / budget) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Informazioni principali a colpo d'occhio */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg mr-4">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Completamento</p>
              <p className="text-2xl font-bold text-gray-800">{completionPercentage}%</p>
              <p className="text-xs text-gray-500">{completedTasks} di {tasks.length} task completati</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg mr-4">
              <span className="text-2xl">💰</span>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Budget Utilizzato</p>
              <p className="text-2xl font-bold text-gray-800">{spent.toFixed(2)} {currency}</p>
              <p className="text-xs text-gray-500">{budgetPercentage}% del budget totale</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg mr-4">
              <span className="text-2xl">⏳</span>
            </div>
            <div>
              <p className="text-gray-500 text-sm">In Attesa</p>
              <p className="text-2xl font-bold text-gray-800">{pendingTasks}</p>
              <p className="text-xs text-gray-500">task in coda</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg mr-4">
              <span className="text-2xl">👥</span>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Team</p>
              <p className="text-2xl font-bold text-gray-800">{agents.length}</p>
              <p className="text-xs text-gray-500">agenti nel progetto</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Distribuzione task per fase */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Distribuzione Task per Fase</h2>
        
        <div className="space-y-3">
          {Object.entries(phases).map(([phase, count]) => (
            <div key={phase} className="bg-gray-50 p-3 rounded-lg">
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium text-gray-800">{phase}</span>
                <span className="text-sm text-gray-600">{count} task</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-indigo-500 h-2 rounded-full"
                  style={{ width: `${Math.round((count / tasks.length) * 100)}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Stato attuale del progetto */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Metriche Chiave</h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-white p-5 rounded-lg border border-blue-200 shadow-sm hover:shadow-md transition">
            <p className="text-3xl font-bold text-blue-700">{inProgressTasks}</p>
            <div className="flex items-center justify-center">
              <span className="text-blue-500 mr-1">🔄</span>
              <p className="text-sm text-blue-600">In Corso</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-green-200 shadow-sm hover:shadow-md transition">
            <p className="text-3xl font-bold text-green-700">{completedTasks}</p>
            <div className="flex items-center justify-center">
              <span className="text-green-500 mr-1">✅</span>
              <p className="text-sm text-green-600">Completati</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-yellow-200 shadow-sm hover:shadow-md transition">
            <p className="text-3xl font-bold text-yellow-700">{pendingTasks}</p>
            <div className="flex items-center justify-center">
              <span className="text-yellow-500 mr-1">⏳</span>
              <p className="text-sm text-yellow-600">In Attesa</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-red-200 shadow-sm hover:shadow-md transition">
            <p className="text-3xl font-bold text-red-700">{failedTasks}</p>
            <div className="flex items-center justify-center">
              <span className="text-red-500 mr-1">❌</span>
              <p className="text-sm text-red-600">Falliti</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}