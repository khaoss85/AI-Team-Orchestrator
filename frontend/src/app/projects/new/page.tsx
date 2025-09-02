'use client';

import React, { useState, useEffect } from 'react';
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
  
  // Load data from template if present in localStorage
  useEffect(() => {
    const templateData = localStorage.getItem('projectTemplate');
    if (templateData) {
      try {
        const template = JSON.parse(templateData);
        setFormData(prev => ({
          ...prev,
          name: template.name || prev.name,
          description: template.description || prev.description,
          goal: template.goal || prev.goal,
          budget: template.budget || prev.budget
        }));
        
        // Remove template after use
        localStorage.removeItem('projectTemplate');
      } catch (e) {
        console.error('Error parsing template data:', e);
      }
    }
  }, []);
  
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
        throw new Error('Project name is required');
      }
      
      if (!formData.goal?.trim()) {
        throw new Error('Project goal is required');
      }
      
      const createdWorkspace = await api.workspaces.create(formData);
      console.log('Workspace created:', createdWorkspace);
      
      // Redirect to the director configuration page
      router.push(`/projects/${createdWorkspace.id}/configure`);
    } catch (err) {
      console.error('Failed to create project:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while creating the project');
      
      // Don't redirect to fake ID - let user see error and retry
      // If backend is down, user should fix connection and retry
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold mb-6">Create New Project</h1>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
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
              Description
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
              Project Goal *
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
              Clearly describe what you want to achieve with this project. This will help the director plan the team of agents.
            </p>
          </div>
          
          <div className="mb-6">
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-1">
              Maximum Budget (EUR)
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
              The budget will determine the complexity and seniority of the AI agent team.
            </p>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.push('/projects')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                  Creating...
                </>
              ) : (
                'Create Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}