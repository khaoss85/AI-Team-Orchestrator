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
}

interface GoalConfirmationProps {
  goals: ExtractedGoal[];
  originalGoal: string;
  onConfirm: (goals: ExtractedGoal[]) => void;
  onEdit: (index: number, goal: ExtractedGoal) => void;
  onRemove: (index: number) => void;
  onReprocess: () => void;
  isLoading?: boolean;
}

export function GoalConfirmation({
  goals,
  originalGoal,
  onConfirm,
  onEdit,
  onRemove,
  onReprocess,
  isLoading = false
}: GoalConfirmationProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  const handleEditStart = (index: number) => {
    setEditingIndex(index);
    setEditValue(goals[index].value.toString());
  };

  const handleEditSave = (index: number) => {
    const updatedGoal = {
      ...goals[index],
      value: parseFloat(editValue) || goals[index].value
    };
    onEdit(index, updatedGoal);
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

  return (
    <div className="w-full max-w-2xl bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Target className="h-5 w-5" />
          Conferma Obiettivi
        </h3>
        <p className="text-sm text-gray-600 mt-2">
          L&apos;AI ha analizzato il tuo obiettivo e lo ha suddiviso in metriche misurabili
        </p>
      </div>
      
      <div className="p-6 space-y-4">
        {/* Original Goal Display */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <p className="text-sm">
            <strong>Obiettivo originale:</strong> {originalGoal}
          </p>
        </div>

        {/* Extracted Goals */}
        <div className="space-y-3">
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

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => onConfirm(goals)}
            disabled={isLoading || goals.length === 0}
            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Conferma e Procedi
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