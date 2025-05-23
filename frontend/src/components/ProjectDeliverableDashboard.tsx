'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverables, DeliverableFeedback } from '@/types';
import DeliverableInsightCard from './DeliverableInsightCard';

interface ProjectDeliverableDashboardProps {
  workspaceId: string;
}

export default function ProjectDeliverableDashboard({
  workspaceId,
}: ProjectDeliverableDashboardProps) {
  const [deliverables, setDeliverables] = useState<ProjectDeliverables | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackType, setFeedbackType] = useState<
    'approve' | 'request_changes' | 'general_feedback'
  >('general_feedback');
  const [feedback, setFeedback] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const [viewMode, setViewMode] = useState<'cards' | 'detailed'>('cards');
  const [expandedOutput, setExpandedOutput] = useState<string | null>(null);

  /* --------------------------- Fetch deliverables -------------------------- */

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
      console.error(err);
      setError('Impossibile caricare i deliverable');
    } finally {
      setLoading(false);
    }
  };

  /* ------------------------------- Feedback -------------------------------- */

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
        priority,
      };
      await api.monitoring.submitDeliverableFeedback(workspaceId, feedbackData);
      setFeedback('');
      setShowFeedbackForm(false);
      setFeedbackType('general_feedback');
      alert('Feedback inviato con successo!');
      fetchDeliverables();
    } catch (err) {
      console.error(err);
      alert("Errore nell'invio del feedback. Riprova.");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  /* ----------------------------- Helpers UI ------------------------------- */

  const getOutputTypeIcon = (type: string) =>
    ({
      analysis: '📊',
      recommendation: '💡',
      document: '📄',
    }[type] ?? '📋');

  const getOutputTypeColor = (type: string) =>
    ({
      analysis: 'bg-blue-50 border-blue-200 text-blue-700',
      recommendation: 'bg-green-50 border-green-200 text-green-700',
      document: 'bg-purple-50 border-purple-200 text-purple-700',
    }[type] ?? 'bg-gray-50 border-gray-200 text-gray-700');

  const getStatusColor = (status: string) =>
    ({
      completed: 'bg-green-100 text-green-800 border-green-300',
      awaiting_review: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      in_progress: 'bg-blue-100 text-blue-800 border-blue-300',
    }[status] ?? 'bg-gray-100 text-gray-800 border-gray-300');

  const getStatusLabel = (status: string) =>
    ({
      completed: 'Completato',
      awaiting_review: 'In Attesa di Revisione',
      in_progress: 'In Corso',
    }[status] ?? status);

  const formatDate = (d: string) =>
    new Date(d).toLocaleString('it-IT', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  /* ----------------------------- Render states ----------------------------- */

  if (loading)
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-gray-200 rounded" />
        <div className="h-4 w-full bg-gray-200 rounded" />
        <div className="h-4 w-2/3 bg-gray-200 rounded" />
        <div className="h-32 bg-gray-200 rounded" />
      </div>
    );

  if (error)
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center text-red-500">
        <div className="text-4xl mb-2">❌</div>
        {error}
        <button
          onClick={fetchDeliverables}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Riprova
        </button>
      </div>
    );

  if (!deliverables)
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        Nessun deliverable disponibile
      </div>
    );

  /* --------------------------- Filters & slices --------------------------- */

  const finalDeliverables = deliverables.key_outputs.filter(
    (o) => o.type === 'final_deliverable' || o.category === 'final_deliverable',
  );
  const normalDeliverables = deliverables.key_outputs.filter(
    (o) => o.type !== 'final_deliverable' && o.category !== 'final_deliverable',
  );

  /* --------------------------------- JSX ---------------------------------- */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between">
          <div>
            <h1 className="text-2xl font-semibold">📋 Project Deliverables</h1>
            <p className="text-gray-600">Risultati finali e output del progetto</p>
          </div>
          <div className="text-right">
            <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(deliverables.completion_status)}`}>
              {getStatusLabel(deliverables.completion_status)}
            </span>
            <div className="text-xs text-gray-500 mt-1">
              {deliverables.completed_tasks}/{deliverables.total_tasks} task completati
            </div>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
          <div
            className="bg-green-600 h-2 rounded-full transition-all"
            style={{ width: `${(deliverables.completed_tasks / deliverables.total_tasks) * 100}%` }}
          />
        </div>
      </div>

      {/* Executive summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-3">📊 Executive Summary</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">{deliverables.summary}</div>
        <div className="text-xs text-gray-500 mt-2">Generato il {formatDate(deliverables.generated_at)}</div>
      </div>

      {/* Final deliverable spotlight */}
      {finalDeliverables.length > 0 && (
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-indigo-800 text-white rounded-xl shadow-lg p-8 space-y-8">
          <div className="flex justify-between">
            <div>
              <div className="flex items-center mb-2">
                <span className="text-3xl mr-3">🎯</span>
                <h2 className="text-2xl font-bold">Deliverable Finale Completato</h2>
              </div>
              <p className="text-indigo-100">
                Il tuo progetto ha raggiunto un traguardo importante con la produzione del deliverable finale.
              </p>
            </div>
            <div className="bg-white/20 rounded-full p-4">
              <svg className="w-8 h-8" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </div>

          {finalDeliverables.map((d) => (
            <div key={d.task_id} className="bg-white/10 rounded-lg p-6 backdrop-blur">
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Info */}
                <div className="lg:col-span-2">
                  <h3 className="text-xl font-semibold mb-3">{d.title || d.task_name}</h3>
                  <p className="text-indigo-100 mb-4 leading-relaxed">
                    {d.description || `${d.output.slice(0, 200)}...`}
                  </p>
                  {d.key_insights?.length && (
                    <div>
                      <h4 className="text-sm font-medium text-indigo-200 mb-2">Insights Principali</h4>
                      <ul className="space-y-1">
                        {d.key_insights.slice(0, 3).map((i, idx) => (
                          <li key={idx} className="flex">
                            <span className="mr-2 mt-1 text-indigo-300">•</span>
                            <span className="text-sm text-indigo-100">{i}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                {/* Metrics + actions */}
                <div className="space-y-4">
                  {d.metrics && (
                    <div className="bg-white/10 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-indigo-200 mb-3">Metriche Chiave</h4>
                      <ul className="space-y-2">
                        {Object.entries(d.metrics)
                          .slice(0, 3)
                          .map(([k, v]) => (
                            <li key={k} className="flex justify-between text-xs text-indigo-200 capitalize">
                              <span>{k.replace(/_/g, ' ')}</span>
                              <span className="font-semibold text-white">{Array.isArray(v) ? v[0] : v}</span>
                            </li>
                          ))}
                      </ul>
                    </div>
                  )}

                  <button
                    onClick={() => setExpandedOutput(d.task_id)}
                    className="w-full bg-white/20 hover:bg-white/30 py-3 rounded-lg flex justify-center items-center font-medium"
                  >
                    👁️ Visualizza Dettagli
                  </button>
                  <button
                    onClick={() => {
                      const dataUri =
                        'data:application/json;charset=utf-8,' +
                        encodeURIComponent(JSON.stringify(d, null, 2));
                      const a = document.createElement('a');
                      a.href = dataUri;
                      a.download = `deliverable_${d.task_id}.json`;
                      a.click();
                    }}
                    className="w-full bg-white/10 hover:bg-white/20 py-2 rounded-lg flex justify-center items-center font-medium border border-white/30"
                  >
                    📥 Scarica
                  </button>
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-white/20 flex justify-between text-sm text-indigo-200">
                <span>
                  Creato da {d.agent_name} • {formatDate(d.created_at)}
                </span>
                <span className="flex items-center">
                  🎯 <span className="ml-1">Deliverable Finale</span>
                </span>
              </div>
            </div>
          ))}

          <div className="bg-white/10 rounded-lg p-4 flex justify-between items-center">
            <div>
              <p className="font-medium">Pronto per la revisione finale?</p>
              <p className="text-sm text-indigo-200">Approva il deliverable o richiedi modifiche</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setFeedbackType('approve');
                  setShowFeedbackForm(true);
                }}
                className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-lg font-medium"
              >
                ✅ Approva
              </button>
              <button
                onClick={() => {
                  setFeedbackType('request_changes');
                  setShowFeedbackForm(true);
                }}
                className="bg-orange-500 hover:bg-orange-600 px-4 py-2 rounded-lg font-medium"
              >
                📝 Modifiche
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Other deliverables */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold">🎯 Altri Deliverable del Progetto</h2>
            <p className="text-sm text-gray-600">Output e risultati intermedi</p>
          </div>
          {!!deliverables.insight_cards?.length && (
            <button
              onClick={() => setViewMode(viewMode === 'cards' ? 'detailed' : 'cards')}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
            >
              {viewMode === 'cards' ? 'View Details' : 'View Cards'}
            </button>
          )}
        </div>

        {viewMode === 'cards' && !!deliverables.insight_cards?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deliverables.insight_cards.map((c) => (
              <DeliverableInsightCard
                key={c.id}
                card={c}
                onViewDetails={() => {
                  setViewMode('detailed');
                  setExpandedOutput(c.id);
                }}
              />
            ))}
          </div>
        ) : normalDeliverables.length ? (
          <div className="space-y-4">
            {normalDeliverables.map((o) => (
              <div key={o.task_id} className={`border rounded-lg p-4 ${getOutputTypeColor(o.type)}`}>
                <div className="flex justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getOutputTypeIcon(o.type)}</span>
                    <h3 className="font-medium">{o.task_name}</h3>
                    <span className="text-xs px-2 py-0.5 bg-white/60 rounded">{o.type}</span>
                  </div>
                  <button
                    onClick={() => setExpandedOutput(expandedOutput === o.task_id ? null : o.task_id)}
                    className="text-xs text-gray-600 hover:text-gray-800"
                  >
                    {expandedOutput === o.task_id ? 'Riduci' : 'Espandi'}
                  </button>
                </div>

                <div className="bg-white/60 rounded p-3 mb-2 text-sm text-gray-700 leading-relaxed">
                  {expandedOutput === o.task_id
                    ? o.output
                    : o.output.length > 200
                    ? `${o.output.slice(0, 200)}…`
                    : o.output}
                </div>

                <div className="flex justify-between text-xs text-gray-600">
                  <span>
                    <strong>Creato da:</strong> {o.agent_name} ({o.agent_role})
                  </span>
                  <span>{formatDate(o.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📋</div>
            Tutti i deliverable sono stati consolidati nel deliverable finale
          </div>
        )}
      </div>

      {/* Feedback */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">💬 Feedback e Azioni</h2>

        {!showFeedbackForm ? (
          <>
            <p className="text-gray-600 mb-4">
              Cosa ne pensi dei risultati? Puoi approvare il progetto o richiedere modifiche.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => {
                  setFeedbackType('approve');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                ✅ Approva Progetto
              </button>
              <button
                onClick={() => {
                  setFeedbackType('request_changes');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                📝 Richiedi Modifiche
              </button>
              <button
                onClick={() => {
                  setFeedbackType('general_feedback');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                💭 Feedback Generale
              </button>
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between">
              <h3 className="font-medium">
                {feedbackType === 'approve' && '✅ Approva Progetto'}
                {feedbackType === 'request_changes' && '📝 Richiedi Modifiche'}
                {feedbackType === 'general_feedback' && '💭 Feedback Generale'}
              </h3>
              <button onClick={() => setShowFeedbackForm(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <textarea
              rows={4}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              placeholder={
                feedbackType === 'approve'
                  ? 'Es. Ottimo lavoro! Il progetto soddisfa tutti i requisiti…'
                  : feedbackType === 'request_changes'
                  ? 'Es. Vorrei che venissero approfonditi i seguenti aspetti…'
                  : 'Es. Suggerimento per migliorare…'
              }
            />

            <div>
              <label className="block text-sm font-medium mb-1">Priorità</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
                className="px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="low">Bassa</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
              </select>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSubmitFeedback}
                disabled={submittingFeedback}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md disabled:opacity-50 hover:bg-indigo-700"
              >
                {submittingFeedback ? 'Invio…' : 'Invia Feedback'}
              </button>
              <button onClick={() => setShowFeedbackForm(false)} className="px-4 py-2 bg-gray-100 rounded-md">
                Annulla
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}