'use client';

import React, { useState } from 'react';
import { CheckCircle2, Target, Edit2, Trash2, RefreshCw } from 'lucide-react';

interface ExtractedGoal {
  id: string;
  value: number;
  unit: string;
  type: string;
  description: string;
  confidence: number;
  editable: boolean;
  // Strategic deliverable fields
  deliverable_type?: string;
  business_value?: string;
  acceptance_criteria?: string[];
  execution_phase?: string;
  semantic_context?: any;
  // AI Autonomy fields
  autonomy_level?: string;
  autonomy_reason?: string;
  available_tools?: string[];
  human_input_required?: string[];
}

interface GoalConfirmationProps {
  goals: ExtractedGoal[];
  finalMetrics?: ExtractedGoal[];
  strategicDeliverables?: ExtractedGoal[];
  goalSummary?: {
    total_goals: number;
    final_metrics_count: number;
    strategic_deliverables_count: number;
  };
  originalGoal: string;
  onConfirm: (goals: ExtractedGoal[]) => void;
  onEdit: (index: number, goal: ExtractedGoal) => void;
  onRemove: (index: number) => void;
  onReprocess: () => void;
  isLoading?: boolean;
}

export function GoalConfirmation({
  goals,
  finalMetrics = [],
  strategicDeliverables = [],
  goalSummary,
  originalGoal,
  onConfirm,
  onEdit,
  onRemove,
  onReprocess,
  isLoading = false
}: GoalConfirmationProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [editDescription, setEditDescription] = useState<string>('');
  const [editField, setEditField] = useState<'value' | 'description'>('value');

  const handleEditStart = (index: number, field: 'value' | 'description' = 'value') => {
    setEditingIndex(index);
    setEditField(field);
    if (field === 'value') {
      setEditValue(finalMetrics[index].value.toString());
    } else {
      setEditDescription(finalMetrics[index].description);
    }
  };

  const handleEditSave = (index: number) => {
    const goalToUpdate = finalMetrics[index];
    const updatedGoal = {
      ...goalToUpdate,
      value: editField === 'value' ? (parseFloat(editValue) || goalToUpdate.value) : goalToUpdate.value,
      description: editField === 'description' ? editDescription : goalToUpdate.description
    };
    
    // Find the actual index in the main goals array
    const goalIndex = goals.findIndex(g => g.id === goalToUpdate.id);
    if (goalIndex !== -1) {
      onEdit(goalIndex, updatedGoal);
    }
    setEditingIndex(null);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'Alta';
    if (confidence >= 0.7) return 'Media';
    return 'Bassa';
  };

  const getAutonomyInfo = (autonomyLevel?: string) => {
    switch (autonomyLevel) {
      case 'autonomous':
        return { icon: '🤖', label: 'Autonomo', color: 'bg-green-100 text-green-800', description: 'AI può completare autonomamente' };
      case 'assisted':
        return { icon: '🤝', label: 'Assistito', color: 'bg-yellow-100 text-yellow-800', description: 'AI + input umano' };
      case 'human_required':
        return { icon: '👥', label: 'Umano', color: 'bg-red-100 text-red-800', description: 'Richiede lavoro umano' };
      case 'tool_upgradeable':
        return { icon: '🔧', label: 'Upgradabile', color: 'bg-blue-100 text-blue-800', description: 'Diventerà autonomo con nuovi tools' };
      default:
        return { icon: '🤖', label: 'Autonomo', color: 'bg-green-100 text-green-800', description: 'AI può completare autonomamente' };
    }
  };

  return (
    <div className="w-full max-w-2xl bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Target className="h-5 w-5" />
          Conferma Obiettivi
        </h3>
        <p className="text-sm text-gray-600 mt-2">
          L&apos;AI ha analizzato il tuo obiettivo usando decomposizione strategica
        </p>
        {goalSummary && (
          <div className="flex gap-4 text-xs text-gray-500 mt-2">
            <span>{goalSummary.final_metrics_count} metriche finali</span>
            <span>•</span>
            <span>{goalSummary.strategic_deliverables_count} deliverable strategici</span>
          </div>
        )}
      </div>
      
      <div className="p-6 space-y-4">
        {/* Original Goal Display */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <p className="text-sm">
            <strong>Obiettivo originale:</strong> {originalGoal}
          </p>
        </div>

        {/* Final Metrics Section */}
        {finalMetrics && finalMetrics.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-md font-semibold text-blue-600 flex items-center gap-2">
              🎯 Metriche Finali da Raggiungere
            </h4>
            <p className="text-sm text-gray-600 mb-3">
              Questi sono gli obiettivi quantificabili che definiranno il successo del progetto
            </p>
            {finalMetrics.map((goal, index) => (
              <div
                key={goal.id}
                className="p-4 border rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors border-blue-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {editingIndex === index ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="w-20 px-2 py-1 text-xl font-bold text-blue-600 border border-blue-300 rounded focus:ring-2 focus:ring-blue-500"
                            autoFocus
                          />
                          <button
                            onClick={() => handleEditSave(index)}
                            className="text-green-600 hover:text-green-800"
                          >
                            <CheckCircle2 className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => setEditingIndex(null)}
                            className="text-red-600 hover:text-red-800"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <>
                          <span className="text-2xl font-bold text-blue-600">
                            {goal.value}
                          </span>
                          <span className="font-medium">{goal.unit}</span>
                          <button
                            onClick={() => handleEditStart(index)}
                            className="text-gray-500 hover:text-blue-600 transition-colors"
                            title="Modifica valore"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        📊 Metrica
                      </span>
                    </div>
                    
                    {editingIndex === index && editField === 'description' ? (
                      <div className="flex items-center gap-2 mt-2">
                        <input
                          type="text"
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          className="flex-1 px-2 py-1 text-sm text-gray-700 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                          autoFocus
                        />
                        <button
                          onClick={() => handleEditSave(index)}
                          className="text-green-600 hover:text-green-800"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setEditingIndex(null)}
                          className="text-red-600 hover:text-red-800"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <p className="text-sm text-gray-700 font-medium flex-1">{goal.description}</p>
                        <button
                          onClick={() => handleEditStart(index, 'description')}
                          className="text-gray-500 hover:text-blue-600 transition-colors"
                          title="Modifica descrizione"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-gray-500">Confidenza:</span>
                      <span className={`text-xs font-medium ${getConfidenceColor(goal.confidence)}`}>
                        {getConfidenceLabel(goal.confidence)} ({Math.round(goal.confidence * 100)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Strategic Deliverables Section */}
        {strategicDeliverables && strategicDeliverables.length > 0 && (
          <div className="space-y-3 mt-6">
            <h4 className="text-md font-semibold text-green-600 flex items-center gap-2">
              📋 Asset Strategici da Creare
            </h4>
            <p className="text-sm text-gray-600 mb-3">
              Questi deliverable saranno creati dagli agenti AI per raggiungere le metriche finali
            </p>
            {strategicDeliverables.map((goal, index) => {
              const autonomyInfo = getAutonomyInfo(goal.autonomy_level);
              return (
              <div
                key={goal.id}
                className="p-4 border rounded-lg bg-green-50 hover:bg-green-100 transition-colors border-green-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        🔧 {goal.deliverable_type || 'Asset'}
                      </span>
                      
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${autonomyInfo.color}`}>
                        {autonomyInfo.icon} {autonomyInfo.label}
                      </span>
                      
                      {goal.execution_phase && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          📅 {goal.execution_phase}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-700 font-medium mb-2">{goal.description}</p>
                    
                    {goal.business_value && (
                      <p className="text-xs text-gray-600 mb-2">
                        <strong>Valore Business:</strong> {goal.business_value}
                      </p>
                    )}
                    
                    {/* Autonomy Details */}
                    {goal.autonomy_reason && (
                      <p className="text-xs text-gray-600 mb-2">
                        <strong>Modalità di Esecuzione:</strong> {goal.autonomy_reason}
                      </p>
                    )}
                    
                    {goal.human_input_required && goal.human_input_required.length > 0 && (
                      <p className="text-xs text-red-600 mb-2">
                        <strong>Input Umano Richiesto:</strong> {goal.human_input_required.join(', ')}
                      </p>
                    )}
                    
                    {goal.available_tools && goal.available_tools.length > 0 && (
                      <p className="text-xs text-blue-600 mb-2">
                        <strong>Strumenti AI Utilizzati:</strong> {goal.available_tools.join(', ')}
                      </p>
                    )}
                    
                    {goal.autonomy_level === 'tool_upgradeable' && (
                      <p className="text-xs text-blue-600 mb-2">
                        <strong>🔧 Tool Roadmap:</strong> Diventerà autonomo quando svilupperemo l'integrazione diretta con i sistemi esterni
                      </p>
                    )}

                    {goal.acceptance_criteria && goal.acceptance_criteria.length > 0 && (
                      <div className="text-xs text-gray-600">
                        <strong>Criteri di Accettazione:</strong>
                        <ul className="list-disc list-inside mt-1 ml-2">
                          {goal.acceptance_criteria.slice(0, 3).map((criteria, idx) => (
                            <li key={idx}>{criteria}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-gray-500">Confidenza:</span>
                      <span className={`text-xs font-medium ${getConfidenceColor(goal.confidence)}`}>
                        {getConfidenceLabel(goal.confidence)} ({Math.round(goal.confidence * 100)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              );
            })}
          </div>
        )}

        {/* Fallback: All Goals (backward compatibility) */}
        {(!finalMetrics || finalMetrics.length === 0) && (!strategicDeliverables || strategicDeliverables.length === 0) && (
          <div className="space-y-3">
            <h4 className="text-md font-semibold text-gray-600">
              Obiettivi Estratti
            </h4>
            {goals.map((goal, index) => (
            <div
              key={goal.id}
              className="p-4 border rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {editingIndex === index ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="w-20 px-2 py-1 border rounded"
                          autoFocus
                        />
                        <span className="font-medium">{goal.unit}</span>
                        <button
                          className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                          onClick={() => handleEditSave(index)}
                        >
                          ✓
                        </button>
                        <button
                          className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                          onClick={() => setEditingIndex(null)}
                        >
                          ✗
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className="text-2xl font-bold text-indigo-600">
                          {goal.value}
                        </span>
                        <span className="font-medium">{goal.unit}</span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {goal.type}
                        </span>
                      </>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600">{goal.description}</p>
                  
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-500">Confidenza:</span>
                    <span className={`text-xs font-medium ${getConfidenceColor(goal.confidence)}`}>
                      {getConfidenceLabel(goal.confidence)} ({Math.round(goal.confidence * 100)}%)
                    </span>
                  </div>
                </div>
                
                <div className="flex gap-1 ml-4">
                  <button
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-md disabled:opacity-50"
                    onClick={() => handleEditStart(index)}
                    disabled={editingIndex !== null}
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-md disabled:opacity-50"
                    onClick={() => onRemove(index)}
                    disabled={editingIndex !== null}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse"></div>
            <p className="text-sm font-medium text-yellow-800">
              ⚡ Azione Richiesta
            </p>
          </div>
          <p className="text-xs text-yellow-700">
            Gli obiettivi sono stati estratti con successo! Clicca "Conferma e Procedi" per salvarli nel database e avviare il team.
          </p>
        </div>
        
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => {
              console.log('🎯 User clicking Confirm button with goals:', goals);
              onConfirm(goals);
            }}
            disabled={isLoading || goals.length === 0}
            className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            ✅ Conferma e Procedi ({goals.length} obiettivi)
          </button>
          
          <button
            onClick={onReprocess}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50 transition flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Rianalizza
          </button>
        </div>
      </div>
    </div>
  );
}