'use client';

import React, { useState, useEffect } from 'react';
import { Agent, AgentSeniority, Handoff } from '@/types';
import CodeEditor from './CodeEditor';

// Definizione delle enum necessarie
enum SkillLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  EXPERT = "expert"
}

enum PersonalityTrait {
  ANALYTICAL = "analytical",
  CREATIVE = "creative",
  DETAIL_ORIENTED = "detail-oriented",
  PROACTIVE = "proactive",
  COLLABORATIVE = "collaborative",
  DECISIVE = "decisive",
  INNOVATIVE = "innovative",
  METHODICAL = "methodical",
  ADAPTABLE = "adaptable",
  DIPLOMATIC = "diplomatic"
}

enum CommunicationStyle {
  FORMAL = "formal",
  CASUAL = "casual",
  TECHNICAL = "technical",
  CONCISE = "concise",
  DETAILED = "detailed",
  EMPATHETIC = "empathetic",
  ASSERTIVE = "assertive"
}

interface Skill {
  name: string;
  level: SkillLevel;
  description?: string;
}

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
    tools: [] as any[],
    // Nuovi campi per personalità
    first_name: '',
    last_name: '',
    personality_traits: [] as PersonalityTrait[],
    communication_style: CommunicationStyle.CASUAL,
    hard_skills: [] as Skill[],
    soft_skills: [] as Skill[],
    background_story: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolsJson, setToolsJson] = useState('');
  const [toolsPreview, setToolsPreview] = useState<any[]>([]);
  const [agentHandoffs, setAgentHandoffs] = useState<Handoff[]>([]);
  
  // Nuovo stato per la gestione delle skills
  const [newHardSkill, setNewHardSkill] = useState<Skill>({
    name: '',
    level: SkillLevel.INTERMEDIATE,
    description: ''
  });
  
  const [newSoftSkill, setNewSoftSkill] = useState<Skill>({
    name: '',
    level: SkillLevel.INTERMEDIATE,
    description: ''
  });

  useEffect(() => {
    if (agent && isOpen) {
      setFormData({
        name: agent.name,
        role: agent.role,
        seniority: agent.seniority,
        description: agent.description || '',
        system_prompt: agent.system_prompt || '',
        llm_config: agent.llm_config || { model: 'gpt-4.1-mini', temperature: 0.3 },
        tools: agent.tools || [],
        // Inizializzazione campi di personalità
        first_name: agent.first_name || '',
        last_name: agent.last_name || '',
        personality_traits: agent.personality_traits || [],
        communication_style: agent.communication_style || CommunicationStyle.CASUAL,
        hard_skills: agent.hard_skills || [],
        soft_skills: agent.soft_skills || [],
        background_story: agent.background_story || ''
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

  // Gestione dei personality traits
  const handlePersonalityTraitChange = (trait: PersonalityTrait) => {
    setFormData(prev => {
      const traits = [...prev.personality_traits];
      if (traits.includes(trait)) {
        return {...prev, personality_traits: traits.filter(t => t !== trait)};
      } else {
        return {...prev, personality_traits: [...traits, trait]};
      }
    });
  };

  // Aggiunta di una hard skill
  const handleAddHardSkill = () => {
    if (newHardSkill.name.trim()) {
      setFormData(prev => ({
        ...prev,
        hard_skills: [...prev.hard_skills, { ...newHardSkill }]
      }));
      setNewHardSkill({
        name: '',
        level: SkillLevel.INTERMEDIATE,
        description: ''
      });
    }
  };

  // Rimozione di una hard skill
  const handleRemoveHardSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      hard_skills: prev.hard_skills.filter((_, i) => i !== index)
    }));
  };

  // Aggiunta di una soft skill
  const handleAddSoftSkill = () => {
    if (newSoftSkill.name.trim()) {
      setFormData(prev => ({
        ...prev,
        soft_skills: [...prev.soft_skills, { ...newSoftSkill }]
      }));
      setNewSoftSkill({
        name: '',
        level: SkillLevel.INTERMEDIATE,
        description: ''
      });
    }
  };

  // Rimozione di una soft skill
  const handleRemoveSoftSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      soft_skills: prev.soft_skills.filter((_, i) => i !== index)
    }));
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

  // Funzione helper per ottenere lo stile del badge di skill level
  const getSkillLevelBadge = (level: SkillLevel) => {
    switch (level) {
      case SkillLevel.BEGINNER:
        return 'bg-blue-100 text-blue-800';
      case SkillLevel.INTERMEDIATE:
        return 'bg-purple-100 text-purple-800';
      case SkillLevel.EXPERT:
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Modifica Agente: {agent.name}</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && <div className="bg-red-50 text-red-700 p-4 rounded-md">{error}</div>}

          {/* Sezione 1: Campi principali */}
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
          </div>

          {/* Sezione 2: Identità Personale */}
          <div className="border-t pt-6 mt-6">
            <h3 className="text-lg font-medium mb-4">Identità Personale</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* first_name */}
              <div>
                <label className="block text-sm font-medium mb-1">Nome</label>
                <input
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Alex"
                />
              </div>
              {/* last_name */}
              <div>
                <label className="block text-sm font-medium mb-1">Cognome</label>
                <input
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Chen"
                />
              </div>
              {/* background_story */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Background</label>
                <textarea
                  name="background_story"
                  value={formData.background_story}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Breve storia di background dell'agente..."
                />
              </div>
            </div>
          </div>

          {/* Sezione 3: Personalità */}
          <div className="border-t pt-6 mt-6">
            <h3 className="text-lg font-medium mb-4">Personalità e Comunicazione</h3>
            
            {/* communication_style */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Stile di Comunicazione</label>
              <select
                name="communication_style"
                value={formData.communication_style}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="formal">Formale</option>
                <option value="casual">Informale</option>
                <option value="technical">Tecnico</option>
                <option value="concise">Conciso</option>
                <option value="detailed">Dettagliato</option>
                <option value="empathetic">Empatico</option>
                <option value="assertive">Assertivo</option>
              </select>
            </div>
            
            {/* personality_traits */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Tratti di Personalità</label>
              <div className="flex flex-wrap gap-2">
                {Object.values(PersonalityTrait).map(trait => (
                  <div
                    key={trait}
                    onClick={() => handlePersonalityTraitChange(trait)}
                    className={`px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
                      formData.personality_traits.includes(trait)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {trait.replace(/_/g, ' ').replace(/-/g, ' ')}
                  </div>
                ))}
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Seleziona i tratti che definiscono la personalità dell'agente
              </p>
            </div>
          </div>

          {/* Sezione 4: Skills */}
          <div className="border-t pt-6 mt-6">
            <h3 className="text-lg font-medium mb-4">Competenze</h3>
            
            {/* Hard Skills */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Hard Skills</label>
              
              {formData.hard_skills.length > 0 && (
                <div className="mb-3 space-y-2">
                  {formData.hard_skills.map((skill, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                      <div>
                        <span className="font-medium">{skill.name}</span>
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${getSkillLevelBadge(skill.level)}`}>
                          {skill.level}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveHardSkill(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newHardSkill.name}
                  onChange={(e) => setNewHardSkill({...newHardSkill, name: e.target.value})}
                  placeholder="Nome della skill"
                  className="flex-grow px-3 py-2 border rounded-md"
                />
                <select
                  value={newHardSkill.level}
                  onChange={(e) => setNewHardSkill({...newHardSkill, level: e.target.value as SkillLevel})}
                  className="w-40 px-3 py-2 border rounded-md"
                >
                  <option value={SkillLevel.BEGINNER}>Principiante</option>
                  <option value={SkillLevel.INTERMEDIATE}>Intermedio</option>
                  <option value={SkillLevel.EXPERT}>Esperto</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddHardSkill}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
                >
                  Aggiungi
                </button>
              </div>
            </div>
            
            {/* Soft Skills */}
            <div>
              <label className="block text-sm font-medium mb-2">Soft Skills</label>
              
              {formData.soft_skills.length > 0 && (
                <div className="mb-3 space-y-2">
                  {formData.soft_skills.map((skill, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                      <div>
                        <span className="font-medium">{skill.name}</span>
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${getSkillLevelBadge(skill.level)}`}>
                          {skill.level}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveSoftSkill(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSoftSkill.name}
                  onChange={(e) => setNewSoftSkill({...newSoftSkill, name: e.target.value})}
                  placeholder="Nome della skill"
                  className="flex-grow px-3 py-2 border rounded-md"
                />
                <select
                  value={newSoftSkill.level}
                  onChange={(e) => setNewSoftSkill({...newSoftSkill, level: e.target.value as SkillLevel})}
                  className="w-40 px-3 py-2 border rounded-md"
                >
                  <option value={SkillLevel.BEGINNER}>Principiante</option>
                  <option value={SkillLevel.INTERMEDIATE}>Intermedio</option>
                  <option value={SkillLevel.EXPERT}>Esperto</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddSoftSkill}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
                >
                  Aggiungi
                </button>
              </div>
            </div>
          </div>

          {/* description */}
          <div className="border-t pt-6">
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