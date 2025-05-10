'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { CustomTool } from '@/types';

export default function ToolsPage() {
  const [tools, setTools] = useState<CustomTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Mock workspace ID for development
  const mockWorkspaceId = '123e4567-e89b-12d3-a456-426614174000';
  
  useEffect(() => {
    const fetchTools = async () => {
      try {
        setLoading(true);
        const data = await api.tools.listCustomTools(mockWorkspaceId);
        setTools(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch tools:', err);
        setError('Impossibile caricare i tool. Riprova più tardi.');
        
        // Per test, mostra dati fittizi
        setTools([
          {
            id: '1',
            workspace_id: mockWorkspaceId,
            name: 'analyze_hashtag_popularity',
            description: 'Analizza la popolarità degli hashtag',
            code: `async def analyze_hashtag_popularity(hashtag: str) -> Dict[str, Any]:\n    # Implementation\n    return {"popularity": 0.8}`,
            created_by: 'user',
            created_at: new Date().toISOString()
          },
          {
            id: '2',
            workspace_id: mockWorkspaceId,
            name: 'find_trending_accounts',
            description: 'Trova account in tendenza nel settore',
            code: `async def find_trending_accounts(sector: str, limit: int = 5) -> List[Dict[str, Any]]:\n    # Implementation\n    return [{"username": "example", "followers": 10000}]`,
            created_by: 'agent',
            created_at: new Date().toISOString()
          }
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTools();
  }, []);
  
  const handleDeleteTool = async (id: string) => {
    try {
      await api.tools.deleteCustomTool(id);
      setTools(tools.filter(tool => tool.id !== id));
    } catch (err) {
      console.error('Failed to delete tool:', err);
      setError('Impossibile eliminare il tool. Riprova più tardi.');
    }
  };
  
  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Tool Manager</h1>
        <Link href="/tools/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
          Nuovo Tool
        </Link>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-medium mb-2">Tool predefiniti per Instagram</h2>
          <p className="text-gray-600 mb-4">
            Tool per l'analisi di contenuti Instagram già disponibili per i tuoi agenti.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-md p-4">
              <h3 className="font-medium">Analisi Hashtag</h3>
              <p className="text-sm text-gray-600 mb-2">Analizza hashtag di Instagram per popolarità e rilevanza</p>
              <Link href="/tools/instagram/hashtags" className="text-indigo-600 text-sm hover:underline">
                Prova il tool
              </Link>
            </div>
            
            <div className="border border-gray-200 rounded-md p-4">
              <h3 className="font-medium">Analisi Account</h3>
              <p className="text-sm text-gray-600 mb-2">Analizza account Instagram per metriche di engagement</p>
              <Link href="/tools/instagram/account" className="text-indigo-600 text-sm hover:underline">
                Prova il tool
              </Link>
            </div>
            
            <div className="border border-gray-200 rounded-md p-4">
              <h3 className="font-medium">Idee Contenuti</h3>
              <p className="text-sm text-gray-600 mb-2">Genera idee per contenuti Instagram basate su topic e audience</p>
              <Link href="/tools/instagram/content" className="text-indigo-600 text-sm hover:underline">
                Prova il tool
              </Link>
            </div>
            
            <div className="border border-gray-200 rounded-md p-4">
              <h3 className="font-medium">Analisi Competitors</h3>
              <p className="text-sm text-gray-600 mb-2">Analizza account dei competitor e le loro strategie</p>
              <Link href="/tools/instagram/competitors" className="text-indigo-600 text-sm hover:underline">
                Prova il tool
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-medium mb-4">Tool Personalizzati</h2>
        
        {loading ? (
          <div className="text-center py-10">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Caricamento tool...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
            {error}
          </div>
        ) : tools.length === 0 ? (
          <div className="text-center py-10">
            <h3 className="text-lg font-medium text-gray-600">Nessun tool personalizzato</h3>
            <p className="text-gray-500 mt-2 mb-4">Crea il tuo primo tool personalizzato</p>
            <Link href="/tools/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
              Crea Tool
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {tools.map((tool) => (
              <div key={tool.id} className="border border-gray-200 rounded-md p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-medium">{tool.name}</h3>
                    <p className="text-sm text-gray-600">{tool.description || 'Nessuna descrizione'}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    tool.created_by === 'user' ? 'bg-indigo-100 text-indigo-800' : 'bg-green-100 text-green-800'
                  }`}>
                    {tool.created_by === 'user' ? 'Creato da utente' : 'Creato da agente'}
                  </span>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md mb-3">
                  <pre className="text-sm text-gray-700 overflow-auto">
                    {tool.code.length > 150 ? `${tool.code.substring(0, 150)}...` : tool.code}
                  </pre>
                </div>
                
                <div className="flex space-x-2">
                  <Link 
                    href={`/tools/${tool.id}`}
                    className="text-xs px-3 py-1 bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100 transition"
                  >
                    Modifica
                  </Link>
                  <button 
                    onClick={() => handleDeleteTool(tool.id)}
                    className="text-xs px-3 py-1 bg-red-50 text-red-700 rounded-md hover:bg-red-100 transition"
                  >
                    Elimina
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}