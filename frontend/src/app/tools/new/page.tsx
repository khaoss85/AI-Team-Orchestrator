'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import CodeEditor from '@/components/CodeEditor';
import { api } from '@/utils/api';
import { CustomToolCreate } from '@/types';

export default function NewToolPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Mock workspace ID for development
  const mockWorkspaceId = '123e4567-e89b-12d3-a456-426614174000';
  
  const [formData, setFormData] = useState<Partial<CustomToolCreate>>({
    name: '',
    description: '',
    code: `async def my_custom_tool(param1: str, param2: int = 5) -> Dict[str, Any]:
    """
    Description of what your tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2, defaults to 5
    
    Returns:
        Dictionary with results
    """
    # Your implementation here
    result = {
        "success": True,
        "data": {
            "param1": param1,
            "param2": param2
        }
    }
    return result
`,
    workspace_id: mockWorkspaceId,
    created_by: 'user'
  });
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  const handleCodeChange = (code: string) => {
    setFormData({
      ...formData,
      code
    });
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      // Validate form data
      if (!formData.name?.trim()) {
        throw new Error('Il nome del tool è obbligatorio');
      }
      
      if (!formData.code?.trim()) {
        throw new Error('Il codice del tool è obbligatorio');
      }
      
      // Ensure all required fields are present
      const toolData: CustomToolCreate = {
        name: formData.name!,
        description: formData.description || '',
        code: formData.code!,
        workspace_id: mockWorkspaceId,
        created_by: 'user'
      };
      
      const createdTool = await api.tools.createCustomTool(toolData);
      console.log('Tool created:', createdTool);
      
      // Redirect to tools page
      router.push('/tools');
    } catch (err) {
      console.error('Failed to create tool:', err);
      setError(err instanceof Error ? err.message : 'Si è verificato un errore durante la creazione del tool');
      
      // For testing without backend, simulate success
      setTimeout(() => {
        router.push('/tools');
      }, 1000);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold mb-6">Crea Nuovo Tool</h1>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Nome del Tool *
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
            <p className="mt-1 text-xs text-gray-500">
              Il nome del tool deve essere unico e descrivere la sua funzione (es. analyze_instagram_hashtags)
            </p>
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
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            ></textarea>
          </div>
          
          <div className="mb-6">
            <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">
              Codice Python *
            </label>
            <CodeEditor 
              value={formData.code || ''} 
              onChange={handleCodeChange} 
              language="python"
              height="300px"
            />
            <p className="mt-1 text-xs text-gray-500">
              Scrivi il codice Python per il tuo tool. Deve essere una funzione async con tipizzazione.
            </p>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.push('/tools')}
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
                'Crea Tool'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}