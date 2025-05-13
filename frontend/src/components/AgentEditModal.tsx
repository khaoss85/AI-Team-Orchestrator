'use client';

import React, { useState, useEffect } from 'react';
import { Agent, AgentSeniority, Handoff } from '@/types';
import CodeEditor from './CodeEditor';

interface AgentEditModalProps {
  isOpen: boolean;
  agent: Agent | null;
  allAgents: Agent[];
  allHandoffs: Handoff[];
  onClose: () => void;
  onSave: (agentId: string, updates: Partial<Agent>) => Promise<void>;
}

export default function AgentEditModal({
  isOpen,
  agent,
  allAgents,
  allHandoffs,
  onClose,
  onSave
}: AgentEditModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    seniority: 'junior' as AgentSeniority,
    description: '',
    system_prompt: '',
    llm_config: { model: 'gpt-4.1-mini', temperature: 0.3 },
    tools: [] as any[]
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolsJson, setToolsJson] = useState('');
  const [toolsPreview, setToolsPreview] = useState<any[]>([]);
  const [agentHandoffs, setAgentHandoffs] = useState<Handoff[]>([]);

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
      const json = JSON.stringify(agent.tools || [], null, 2);
      setToolsJson(json);
      setToolsPreview(Array.isArray(agent.tools) ? agent.tools : []);

      setAgentHandoffs(
        (allHandoffs || []).filter(
          h => h.source_agent_id === agent.id || h.target_agent_id === agent.id
        )
      );
    } else {
      setAgentHandoffs([]);
    }
  }, [agent, isOpen, allHandoffs]);

  useEffect(() => {
    try {
      const parsed = JSON.parse(toolsJson);
      setToolsPreview(Array.isArray(parsed) ? parsed : []);
    } catch {
      setToolsPreview([]);
    }
  }, [toolsJson]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    if (name === 'model' || name === 'temperature') {
      setFormData(p => ({
        ...p,
        llm_config: { ...p.llm_config, [name]: name === 'temperature' ? parseFloat(value) : value }
      }));
    } else {
      setFormData(p => ({ ...p, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agent) return;

    setLoading(true);
    setError(null);
    try {
      const parsedTools = toolsJson.trim() ? JSON.parse(toolsJson) : [];
      if (!Array.isArray(parsedTools)) throw new Error('Tools must be an array');

      await onSave(agent.id, { ...formData, tools: parsedTools });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Errore di salvataggio.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !agent) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Modifica Agente: {agent.name}</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && <div className="bg-red-50 text-red-700 p-4 rounded-md">{error}</div>}

          {/* campi principali */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* name */}
            <div>
              <label className="block text-sm font-medium mb-1">Nome *</label>
              <input
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>
            {/* role */}
            <div>
              <label className="block text-sm font-medium mb-1">Ruolo *</label>
              <input
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>
            {/* seniority */}
            <div>
              <label className="block text-sm font-medium mb-1">Seniority *</label>
              <select
                name="seniority"
                value={formData.seniority}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="junior">Junior</option>
                <option value="senior">Senior</option>
                <option value="expert">Expert</option>
              </select>
            </div>
            {/* model */}
            <div>
              <label className="block text-sm font-medium mb-1">Modello LLM</label>
              <select
                name="model"
                value={formData.llm_config.model}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="gpt-4.1-nano">GPT-4.1 Nano</option>
                <option value="gpt-4.1-mini">GPT-4.1 Mini</option>
                <option value="gpt-4.1">GPT-4.1</option>
              </select>
            </div>
            {/* temperature */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                Temperature: {formData.llm_config.temperature}
              </label>
              <input
                type="range"
                name="temperature"
                min="0"
                max="1"
                step="0.1"
                value={formData.llm_config.temperature}
                onChange={handleChange}
                className="w-full"
              />
            </div>
          </div>

          {/* description */}
          <div>
            <label className="block text-sm font-medium mb-1">Descrizione</label>
            <textarea
              name="description"
              rows={3}
              value={formData.description}
              onChange={handleChange}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* system prompt */}
          <div>
            <label className="block text-sm font-medium mb-1">System Prompt *</label>
            <CodeEditor
              value={formData.system_prompt}
              onChange={v => setFormData(p => ({ ...p, system_prompt: v }))}
              language="text"
              height="200px"
            />
          </div>

          {/* tools JSON + preview */}
          <div>
            <label className="block text-sm font-medium mb-1">Tools (JSON)</label>
            <CodeEditor value={toolsJson} onChange={setToolsJson} language="json" height="150px" />
            <p className="mt-1 text-xs text-gray-500">
              Esempio: [{'{'}`"name":"web_search","type":"function"`{'}'}]
            </p>

            {toolsPreview.length > 0 && (
              <div className="mt-4 space-y-3">
                {toolsPreview.map((t, i) => (
                  <div key={i} className="bg-gray-50 p-3 rounded-md">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">{t.name || 'Unnamed Tool'}</span>
                      <span className="text-xs text-gray-600">
                        {t.type === 'web_search'
                          ? '🔍 Web Search'
                          : t.type === 'file_search'
                          ? '📁 File Search'
                          : t.type === 'function'
                          ? '⚙️ Function'
                          : t.type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {t.description || 'No description available'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* handoffs readonly */}
          <div>
            <h3 className="text-md font-medium mb-2 border-t pt-4 mt-4">
              Handoffs Associati ({agentHandoffs.length})
            </h3>
            {agentHandoffs.length > 0 ? (
              <div className="space-y-3 max-h-60 overflow-y-auto bg-gray-50 p-4 rounded-md">
                {agentHandoffs.map(h => {
                  const isSource = h.source_agent_id === agent.id;
                  const otherId = isSource ? h.target_agent_id : h.source_agent_id;
                  const other = allAgents.find(a => a.id === otherId);
                  return (
                    <div
                      key={h.id}
                      className={`p-3 rounded-md border ${
                        isSource ? 'border-yellow-300 bg-yellow-50' : 'border-green-300 bg-green-50'
                      }`}
                    >
                      <p className="text-sm font-semibold">
                        {isSource ? 'Da questo agente a' : 'A questo agente da'}{' '}
                        {other ? other.name : 'Sconosciuto'}
                      </p>
                      <p className="text-xs mt-1">{h.description || 'Nessuna descrizione.'}</p>
                      <p className="text-xs text-gray-400 mt-1">ID: {h.id}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">
                Nessun handoff associato a questo agente.
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              La modifica degli handoff non è attualmente supportata.
            </p>
          </div>

          {/* actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 rounded-md text-sm"
              disabled={loading}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2" />
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
