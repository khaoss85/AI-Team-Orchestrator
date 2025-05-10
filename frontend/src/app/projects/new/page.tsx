'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { WorkspaceCreateData } from '@/types';

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Mock user ID for development
  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
  
  const [formData, setFormData] = useState<WorkspaceCreateData>({
    name: '',
    description: '',
    user_id: mockUserId,
    goal: '',
    budget: {
      max_amount: 1000,
      currency: 'EUR'
    }
  });
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'budget') {
      setFormData({
        ...formData,
        budget: {
          ...formData.budget!,
          max_amount: parseInt(value, 10)
        }
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      // Validate form data
      if (!formData.name.trim()) {
        throw new Error('Il nome del progetto è obbligatorio');
      }
      
      if (!formData.goal?.trim()) {
        throw new Error('L\'obiettivo del progetto è obbligatorio');
      }
      
      const createdWorkspace = await api.workspaces.create(formData);
      console.log('Workspace created:', createdWorkspace);
      
      // Redirect to the director configuration page
      router.push(`/projects/${createdWorkspace.id}/configure`);
    } catch (err) {
      console.error('Failed to create project:', err);
      setError(err instanceof Error ? err.message : 'Si è verificato un errore durante la creazione del progetto');
      
      // For testing without backend, simulate success
      setTimeout(() => {
        const fakeId = 'fake-id-123';
        router.push(`/projects/${fakeId}/configure`);
      }, 1000);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold mb-6">Crea Nuovo Progetto</h1>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Nome del Progetto *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Descrizione
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description || ''}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            ></textarea>
          </div>
          
          <div className="mb-4">
            <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-1">
              Obiettivo del Progetto *
            </label>
            <textarea
              id="goal"
              name="goal"
              value={formData.goal || ''}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            ></textarea>
            <p className="mt-1 text-sm text-gray-500">
              Descrivi chiaramente cosa vuoi ottenere con questo progetto. Questo aiuterà il direttore a pianificare il team di agenti.
            </p>
          </div>
          
          <div className="mb-6">
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-1">
              Budget Massimo (EUR)
            </label>
            <input
              type="number"
              id="budget"
              name="budget"
              value={formData.budget?.max_amount || 1000}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Il budget determinerà la complessità e la seniority del team di agenti AI.
            </p>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.push('/projects')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition"
              disabled={loading}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                  Creazione...
                </>
              ) : (
                'Crea Progetto'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}