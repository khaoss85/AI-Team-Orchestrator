'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { Workspace } from '@/types';

export default function ProjectsPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Mock user ID for development
  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
  
  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setLoading(true);
        const data = await api.workspaces.list(mockUserId);
        setWorkspaces(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch workspaces:', err);
        setError('Impossibile caricare i progetti. Riprova più tardi.');
        // Per test, mostra dati fittizi
        setWorkspaces([
          {
            id: '1',
            name: 'Progetto Marketing Digitale',
            description: 'Campagna di marketing sui social media',
            user_id: mockUserId,
            status: 'active',
            goal: 'Aumentare la visibilità del brand',
            budget: { max_amount: 1000, currency: 'EUR' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            name: 'Analisi Dati Utenti',
            description: 'Analisi comportamentale degli utenti sul sito web',
            user_id: mockUserId,
            status: 'created',
            goal: 'Identificare pattern di comportamento',
            budget: { max_amount: 500, currency: 'EUR' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchWorkspaces();
  }, []);
  
  const handleProjectClick = (id: string) => {
    // Use the router to navigate programmatically
    router.push(`/projects/${id}`);
  };
  
  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">I Tuoi Progetti</h1>
        <Link href="/projects/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
          Nuovo Progetto
        </Link>
      </div>
      
      {loading ? (
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento progetti...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-10 bg-white rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-600">Nessun progetto trovato</h3>
          <p className="text-gray-500 mt-2">Inizia creando il tuo primo progetto</p>
          <Link href="/projects/new" className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
            Crea Progetto
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workspaces.map((workspace) => (
            <div 
              key={workspace.id}
              onClick={() => handleProjectClick(workspace.id)}
              className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-lg font-medium text-gray-800">{workspace.name}</h2>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  workspace.status === 'active' ? 'bg-green-100 text-green-800' :
                  workspace.status === 'created' ? 'bg-blue-100 text-blue-800' :
                  workspace.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                  workspace.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {workspace.status === 'active' ? 'Attivo' :
                   workspace.status === 'created' ? 'Creato' :
                   workspace.status === 'paused' ? 'In pausa' :
                   workspace.status === 'completed' ? 'Completato' :
                   'Errore'}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                {workspace.description || 'Nessuna descrizione'}
              </p>
              
              <div className="border-t pt-4 mt-4">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Obiettivo</p>
                    <p className="font-medium text-gray-800 truncate">
                      {workspace.goal || 'Non specificato'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Budget</p>
                    <p className="font-medium text-gray-800">
                      {workspace.budget 
                        ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                        : 'Non specificato'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}