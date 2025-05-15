'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverables, ProjectOutput, DeliverableFeedback } from '@/types';
import DeliverableInsightCard from './DeliverableInsightCard';
import ConfirmModal from './ConfirmModal';

interface ProjectDeliverableDashboardProps {
  workspaceId: string;
}

export default function ProjectDeliverableDashboard({ workspaceId }: ProjectDeliverableDashboardProps) {
  const [deliverables, setDeliverables] = useState<ProjectDeliverables | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'approve' | 'request_changes' | 'general_feedback'>('general_feedback');
  const [feedback, setFeedback] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [expandedOutput, setExpandedOutput] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<'cards' | 'detailed'>('cards');
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  useEffect(() => {
    fetchDeliverables();
  }, [workspaceId]);

  const fetchDeliverables = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.monitoring.getProjectDeliverables(workspaceId);
      setDeliverables(data);
    } catch (err) {
      console.error('Error fetching deliverables:', err);
      setError(err instanceof Error ? err.message : 'Impossibile caricare i deliverable');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) {
      alert('Inserisci un messaggio di feedback');
      return;
    }

    try {
      setSubmittingFeedback(true);
      
      const feedbackData: DeliverableFeedback = {
        feedback_type: feedbackType,
        message: feedback,
        priority
      };
      
      await api.monitoring.submitDeliverableFeedback(workspaceId, feedbackData);
      
      // Reset form
      setFeedback('');
      setShowFeedbackForm(false);
      setFeedbackType('general_feedback');
      
      // Show success message
      alert('Feedback inviato con successo! Un agente processerà la tua richiesta.');
      
      // Refresh deliverables
      await fetchDeliverables();
      
    } catch (err) {
      console.error('Error submitting feedback:', err);
      alert('Errore nell\'invio del feedback. Riprova.');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const getOutputTypeIcon = (type: string) => {
    switch (type) {
      case 'analysis': return '📊';
      case 'recommendation': return '💡';
      case 'document': return '📄';
      default: return '📋';
    }
  };

  const getOutputTypeColor = (type: string) => {
    switch (type) {
      case 'analysis': return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'recommendation': return 'bg-green-50 border-green-200 text-green-700';
      case 'document': return 'bg-purple-50 border-purple-200 text-purple-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-300';
      case 'awaiting_review': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Completato';
      case 'awaiting_review': return 'In Attesa di Revisione';
      case 'in_progress': return 'In Corso';
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('it-IT', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-500 text-center">
          <div className="text-4xl mb-2">❌</div>
          <p>{error}</p>
          <button 
            onClick={fetchDeliverables}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!deliverables) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">📋</div>
          <p>Nessun deliverable disponibile</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-semibold">📋 Project Deliverables</h1>
            <p className="text-gray-600">Risultati finali e output del progetto</p>
          </div>
          <div className="text-right">
            <span className={`inline-block px-3 py-1 rounded-full text-sm border ${getStatusColor(deliverables.completion_status)}`}>
              {getStatusLabel(deliverables.completion_status)}
            </span>
            <div className="text-xs text-gray-500 mt-1">
              {deliverables.completed_tasks}/{deliverables.total_tasks} task completati
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div 
            className="bg-green-600 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: `${(deliverables.completed_tasks / deliverables.total_tasks) * 100}%` 
            }}
          ></div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-3">📊 Executive Summary</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-gray-700 leading-relaxed">{deliverables.summary}</p>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Generato il {formatDate(deliverables.generated_at)}
        </div>
      </div>

        {/* Key Deliverables - Visual Cards */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-semibold">🎯 Key Deliverables</h2>
              <p className="text-sm text-gray-600">Highlights and insights from completed work</p>
            </div>
            {deliverables.insight_cards && deliverables.insight_cards.length > 0 && (
              <button
                onClick={() => setViewMode(viewMode === 'cards' ? 'detailed' : 'cards')}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition"
              >
                {viewMode === 'cards' ? 'View Details' : 'View Cards'}
              </button>
            )}
          </div>

          {deliverables.insight_cards && deliverables.insight_cards.length > 0 && viewMode === 'cards' ? (
            // Visual Cards View
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {deliverables.insight_cards.map((card) => (
                <DeliverableInsightCard 
                  key={card.id} 
                  card={card}
                  onViewDetails={() => {
                    setExpandedCard(card.id);
                    setViewMode('detailed');
                  }}
                />
              ))}
            </div>
          ) : deliverables.key_outputs.length > 0 ? (
            // Detailed List View (fallback o quando richiesto)
            <div className="space-y-4">
              {deliverables.key_outputs.map((output) => (
                <div key={output.task_id} className={`border rounded-lg p-4 ${getOutputTypeColor(output.type)}`}>
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getOutputTypeIcon(output.type)}</span>
                      <h3 className="font-medium">{output.task_name}</h3>
                      <span className="text-xs px-2 py-1 rounded-full bg-white bg-opacity-60">
                        {output.type}
                      </span>
                    </div>
                    <button
                      onClick={() => setExpandedOutput(expandedOutput === output.task_id ? null : output.task_id)}
                      className="text-xs text-gray-600 hover:text-gray-800"
                    >
                      {expandedOutput === output.task_id ? 'Riduci' : 'Espandi'}
                    </button>
                  </div>

                  <div className="bg-white bg-opacity-60 rounded-md p-3 mb-2">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {expandedOutput === output.task_id ? output.output : 
                       (output.output.length > 200 ? output.output.substring(0, 200) + '...' : output.output)}
                    </p>
                  </div>

                  <div className="flex justify-between items-center text-xs text-gray-600">
                    <span>
                      <strong>Creato da:</strong> {output.agent_name} ({output.agent_role})
                    </span>
                    <span>{formatDate(output.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-3">🎯</div>
              <h3 className="text-lg font-medium mb-2">No deliverables yet</h3>
              <p className="text-sm">Insights will appear here as your team completes tasks</p>
            </div>
          )}
        </div>

      {/* Recommendations & Next Steps */}
      {(deliverables.final_recommendations.length > 0 || deliverables.next_steps.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Recommendations */}
          {deliverables.final_recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-3">💡 Raccomandazioni</h2>
              <ul className="space-y-2">
                {deliverables.final_recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span className="text-sm text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Next Steps */}
          {deliverables.next_steps.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-3">🎯 Prossimi Passi</h2>
              <ul className="space-y-2">
                {deliverables.next_steps.map((step, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-blue-600 mt-1">→</span>
                    <span className="text-sm text-gray-700">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Feedback Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">💬 Feedback e Azioni</h2>
        
        {!showFeedbackForm ? (
          <div className="space-y-3">
            <p className="text-gray-600 mb-4">
              Cosa ne pensi dei risultati? Puoi approvare il progetto o richiedere modifiche.
            </p>
            
            <div className="flex flex-wrap gap-3">
              <button 
                onClick={() => {
                  setFeedbackType('approve');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
              >
                <span className="mr-2">✅</span>
                Approva Progetto
              </button>
              
              <button 
                onClick={() => {
                  setFeedbackType('request_changes');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              >
                <span className="mr-2">📝</span>
                Richiedi Modifiche
              </button>
              
              <button 
                onClick={() => {
                  setFeedbackType('general_feedback');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition"
              >
                <span className="mr-2">💭</span>
                Feedback Generale
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-medium">
                {feedbackType === 'approve' && '✅ Approva Progetto'}
                {feedbackType === 'request_changes' && '📝 Richiedi Modifiche'}
                {feedbackType === 'general_feedback' && '💭 Feedback Generale'}
              </h3>
              <button 
                onClick={() => setShowFeedbackForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {feedbackType === 'approve' && 'Commenti sull\'approvazione (opzionale)'}
                {feedbackType === 'request_changes' && 'Descrivi le modifiche richieste'}
                {feedbackType === 'general_feedback' && 'Il tuo feedback'}
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder={
                  feedbackType === 'approve' 
                    ? 'Es. Ottimo lavoro! Il progetto soddisfa tutti i requisiti...'
                    : feedbackType === 'request_changes'
                    ? 'Es. Vorrei che venissero approfonditi i seguenti aspetti...'
                    : 'Es. Suggerimento per migliorare...'
                }
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priorità</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="low">Bassa</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
              </select>
            </div>
            
            <div className="flex space-x-3">
              <button 
                onClick={handleSubmitFeedback}
                disabled={submittingFeedback}
                className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition disabled:opacity-50"
              >
                {submittingFeedback ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                    Invio...
                  </>
                ) : (
                  'Invia Feedback'
                )}
              </button>
              <button 
                onClick={() => setShowFeedbackForm(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition"
              >
                Annulla
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}