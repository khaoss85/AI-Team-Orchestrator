'use client';

import React, { useState, useEffect } from 'react';
import { Agent, AgentSeniority } from '@/types';
import CodeEditor from './CodeEditor';

interface AgentEditModalProps {
  isOpen: boolean;
  agent: Agent | null;
  onClose: () => void;
  onSave: (agentId: string, updates: Partial<Agent>) => Promise<void>;
}

export default function AgentEditModal({
  isOpen,
  agent,
  onClose,
  onSave
}: AgentEditModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    seniority: 'junior' as AgentSeniority,
    description: '',
    system_prompt: '',
    llm_config: {
      model: 'gpt-4.1-mini',
      temperature: 0.3
    },
    tools: [] as any[]
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolsJson, setToolsJson] = useState('');

  useEffect(() => {
    if (agent && isOpen) {
      setFormData({
        name: agent.name,
        role: agent.role,
        seniority: agent.seniority,
        description: agent.description || '',
        system_prompt: agent.system_prompt || '',
        llm_config: agent.llm_config || { model: 'gpt-4.1-mini', temperature: 0.3 },
        tools: agent.tools || []
      });
      setToolsJson(JSON.stringify(agent.tools || [], null, 2));
    }
  }, [agent, isOpen]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    if (name === 'model' || name === 'temperature') {
      setFormData(prev => ({
        ...prev,
        llm_config: {
          ...prev.llm_config,
          [name]: name === 'temperature' ? parseFloat(value) : value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSystemPromptChange = (value: string) =>
    setFormData(prev => ({ ...prev, system_prompt: value }));

  const handleToolsChange = (value: string) => setToolsJson(value);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agent) return;

    setLoading(true);
    setError(null);

    try {
      let parsedTools: any[] = [];

      if (toolsJson.trim()) {
        parsedTools = JSON.parse(toolsJson);
        if (!Array.isArray(parsedTools)) throw new Error('Tools must be an array');
      }

      const updates: Partial<Agent> = {
        name: formData.name,
        role: formData.role,
        seniority: formData.seniority,
        description: formData.description,
        system_prompt: formData.system_prompt,
        llm_config: formData.llm_config,
        tools: parsedTools
      };

      await onSave(agent.id, updates);
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'Impossibile salvare');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !agent) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Modifica Agente</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-md">{error}</div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* nome */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Nome *
              </label>
              <input
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>
            {/* ruolo */}
            <div>
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Ruolo *
              </label>
              <input
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>
            {/* seniority */}
            <div>
              <label
                htmlFor="seniority"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Seniority *
              </label>
              <select
                id="seniority"
                name="seniority"
                value={formData.seniority}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              >
                <option value="junior">Junior</option>
                <option value="senior">Senior</option>
                <option value="expert">Expert</option>
              </select>
            </div>
            {/* modello */}
            <div>
              <label
                htmlFor="model"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Modello LLM
              </label>
              <select
                id="model"
                name="model"
                value={formData.llm_config.model}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="gpt-4.1-nano">GPT-4.1 Nano</option>
                <option value="gpt-4.1-mini">GPT-4.1 Mini</option>
                <option value="gpt-4.1">GPT-4.1</option>
              </select>
            </div>
            {/* temperature */}
            <div className="md:col-span-2">
              <label
                htmlFor="temperature"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Temperature: {formData.llm_config.temperature}
              </label>
              <input
                type="range"
                id="temperature"
                name="temperature"
                min="0"
                max="1"
                step="0.1"
                value={formData.llm_config.temperature}
                onChange={handleChange}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Conservativo (0)</span>
                <span>Creativo (1)</span>
              </div>
            </div>
          </div>

          {/* descrizione */}
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Descrizione
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              value={formData.description}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* system prompt */}
          <div>
            <label
              htmlFor="system_prompt"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              System Prompt *
            </label>
            <CodeEditor
              value={formData.system_prompt}
              onChange={handleSystemPromptChange}
              language="text"
              height="200px"
            />
          </div>

          {/* tools */}
          <div>
            <label
              htmlFor="tools"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tools (JSON)
            </label>
            <CodeEditor
              value={toolsJson}
              onChange={handleToolsChange}
              language="json"
              height="150px"
            />
            <p className="mt-1 text-xs text-gray-500">
              Esempio: [
              {`{"name": "web_search", "type": "function", "description": "Search the web"}`}
              ]
            </p>
          </div>

          {/* actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
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
                  Salvataggio...
                </>
              ) : (
                'Salva Modifiche'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
