'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverables, DeliverableFeedback, ActionableAsset, ProjectOutputExtended } from '@/types';
import DeliverableInsightCard from './DeliverableInsightCard';
import ActionableOutputCard from './ActionableOutputCard';
import TaskResultDetails from './TaskResultDetails';

interface ProjectDeliverableDashboardProps {
  workspaceId: string;
}

// NEW: Enhanced ActionableAsset display component
const ActionableAssetCard: React.FC<{
  assetName: string;
  asset: ActionableAsset;
  onDownload: () => void;
  onViewDetails: () => void;
}> = ({ assetName, asset, onDownload, onViewDetails }) => {
  const getAssetIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('calendar')) return '📅';
    if (lowerName.includes('contact') || lowerName.includes('database')) return '📊';
    if (lowerName.includes('strategy')) return '🎯';
    if (lowerName.includes('content')) return '📝';
    if (lowerName.includes('analysis')) return '📈';
    return '📦';
  };

  const getActionabilityColor = (score: number) => {
    if (score >= 0.8) return 'from-green-500 to-emerald-600';
    if (score >= 0.6) return 'from-yellow-500 to-orange-600';
    return 'from-red-500 to-pink-600';
  };

  const getActionabilityLabel = (score: number) => {
    if (score >= 0.8) return 'Pronto all\'uso';
    if (score >= 0.6) return 'Richiede personalizzazione';
    return 'Template di base';
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300">
      {/* Header with actionability score */}
      <div className={`bg-gradient-to-r ${getActionabilityColor(asset.actionability_score)} p-4 text-white`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{getAssetIcon(assetName)}</span>
            <div>
              <h3 className="font-bold text-lg">{assetName.replace(/_/g, ' ').toUpperCase()}</h3>
              <p className="text-sm opacity-90">{getActionabilityLabel(asset.actionability_score)}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{Math.round(asset.actionability_score * 100)}%</div>
            <div className="text-xs opacity-90">Azionabilità</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Asset validation and ready status */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              asset.validation_score >= 0.8 
                ? 'bg-green-100 text-green-800' 
                : asset.validation_score >= 0.6
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
            }`}>
              {asset.validation_score >= 0.8 ? '✅' : asset.validation_score >= 0.6 ? '⚠️' : '❌'}
              <span className="ml-1">Validazione: {Math.round(asset.validation_score * 100)}%</span>
            </div>
          </div>
          
          <div className="text-center">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              asset.ready_to_use 
                ? 'bg-green-100 text-green-800' 
                : 'bg-orange-100 text-orange-800'
            }`}>
              {asset.ready_to_use ? '🚀' : '🔧'}
              <span className="ml-1">{asset.ready_to_use ? 'Pronto' : 'In lavorazione'}</span>
            </div>
          </div>
        </div>

        {/* Asset data preview */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-gray-800 mb-2">Anteprima Dati:</h4>
          <div className="space-y-2">
            {Object.entries(asset.asset_data).slice(0, 3).map(([key, value], index) => (
              <div key={index} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-medium text-gray-800 truncate ml-2">
                  {Array.isArray(value) 
                    ? `${value.length} elementi`
                    : typeof value === 'object'
                      ? 'Dati strutturati'
                      : String(value).length > 30
                        ? `${String(value).slice(0, 30)}...`
                        : String(value)
                  }
                </span>
              </div>
            ))}
            {Object.keys(asset.asset_data).length > 3 && (
              <div className="text-xs text-gray-500 text-center pt-2">
                +{Object.keys(asset.asset_data).length - 3} altri campi...
              </div>
            )}
          </div>
        </div>

        {/* Extraction info */}
        <div className="bg-blue-50 rounded-lg p-3 mb-4 text-sm">
          <div className="flex items-center text-blue-800">
            <span className="mr-2">🔬</span>
            <span className="font-medium">Metodo estrazione:</span>
            <span className="ml-1">{asset.extraction_method}</span>
          </div>
          <div className="flex items-center text-blue-700 mt-1">
            <span className="mr-2">📋</span>
            <span>Task origine: {asset.source_task_id.slice(0, 8)}...</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onViewDetails}
            className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition flex items-center justify-center"
          >
            <span className="mr-2">👁️</span>
            Visualizza Dettagli
          </button>
          <button
            onClick={onDownload}
            className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center justify-center"
          >
            <span className="mr-2">📥</span>
            Scarica Asset
          </button>
        </div>
      </div>
    </div>
  );
};

// NEW: Simple Asset Viewer Modal (you can create a separate component later)
const SimpleAssetViewer: React.FC<{
  assetName: string;
  asset: ActionableAsset;
  onClose: () => void;
}> = ({ assetName, asset, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold">{assetName.replace(/_/g, ' ').toUpperCase()}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ✕
          </button>
        </div>
        <div className="p-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">Dati Asset</h3>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(asset.asset_data, null, 2)}
              </pre>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700">Score Validazione</h4>
                <p className="text-2xl font-bold text-green-600">{Math.round(asset.validation_score * 100)}%</p>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">Score Azionabilità</h4>
                <p className="text-2xl font-bold text-blue-600">{Math.round(asset.actionability_score * 100)}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

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
  const [feedbackTaskId, setFeedbackTaskId] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<'cards' | 'detailed'>('cards');
  const [expandedOutput, setExpandedOutput] = useState<string | null>(null);

  // NEW: Asset states
  const [selectedAsset, setSelectedAsset] = useState<{name: string, asset: ActionableAsset} | null>(null);

  // Selected output state
  const [selectedOutput, setSelectedOutput] = useState<ProjectOutputExtended | null>(null);
  const [outputDetails, setOutputDetails] = useState<any | null>(null);
  const [loadingOutput, setLoadingOutput] = useState(false);

  const [showMore, setShowMore] = useState(false);

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

  const handleSubmitFeedback = async (taskIds?: string[]) => {
    if (!feedback.trim()) {
      alert('Inserisci un messaggio di feedback');
      return;
    }
    try {
      setSubmittingFeedback(true);
      const ids = taskIds || finalDeliverables.map(d => d.task_id);
      const feedbackData: DeliverableFeedback = {
        feedback_type: feedbackType,
        message: feedback,
        priority,
        specific_tasks: ids,
      };
      await api.monitoring.submitDeliverableFeedback(workspaceId, feedbackData);
      setFeedback('');
      setShowFeedbackForm(false);
      setFeedbackType('general_feedback');
      setFeedbackTaskId(null);
      alert('Feedback inviato con successo!');
      fetchDeliverables();
    } catch (err) {
      console.error(err);
      alert("Errore nell'invio del feedback. Riprova.");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  /* ----------------------------- NEW: Asset Actions ----------------------------- */

  const handleDownloadAsset = (assetName: string, asset: ActionableAsset) => {
    try {
      const dataUri = 'data:application/json;charset=utf-8,' + 
        encodeURIComponent(JSON.stringify(asset.asset_data, null, 2));
      const link = document.createElement('a');
      link.href = dataUri;
      link.download = `${assetName}_${new Date().getTime()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading asset:', error);
      alert('Errore durante il download dell\'asset');
    }
  };

  const handleViewAssetDetails = (assetName: string, asset: ActionableAsset) => {
    setSelectedAsset({ name: assetName, asset });
  };

  const openOutputModal = async (output: ProjectOutputExtended) => {
    setSelectedOutput(output);
    setLoadingOutput(true);
    try {
      const details = await api.monitoring.getTaskResult(output.task_id);
      setOutputDetails(details);
    } catch (err) {
      console.error('Error fetching output', err);
      setOutputDetails(null);
    } finally {
      setLoadingOutput(false);
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

  /* --------------------------- NEW: Extract actionable assets --------------------------- */

  // Extract actionable assets from final deliverables
  const actionableAssets: Record<string, ActionableAsset> = {};
  
  deliverables.key_outputs
    .filter(output => output.type === 'final_deliverable')
    .forEach(output => {
      // Check different possible locations for actionable assets
      if (output.result?.actionable_assets) {
        Object.assign(actionableAssets, output.result.actionable_assets);
      }
      // Also check if the result itself has actionable structure
      if (output.result && typeof output.result === 'object') {
        const result = output.result;
        if (result.detailed_results_json) {
          try {
            const detailed = JSON.parse(result.detailed_results_json);
            if (detailed.actionable_assets) {
              Object.assign(actionableAssets, detailed.actionable_assets);
            }
          } catch (e) {
            console.debug('Could not parse detailed_results_json for assets');
          }
        }
      }
    });

  /* --------------------------- Filters & slices --------------------------- */

  const finalDeliverables = deliverables.key_outputs.filter(
    (o) => o.type === 'final_deliverable' || o.category === 'final_deliverable',
  );
  const normalDeliverables = deliverables.key_outputs.filter(
    (o) => o.type !== 'final_deliverable' && o.category !== 'final_deliverable',
  );

  const actionableOutputs = deliverables.key_outputs.filter(
    (o) =>
      o.type === 'final_deliverable' ||
      (o.actionable_assets && Object.keys(o.actionable_assets).length > 0)
  );

  const hasActionableAssets = Object.keys(actionableAssets).length > 0;

  /* --------------------------------- JSX ---------------------------------- */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between">
          <div>
            <h1 className="text-2xl font-semibold">📋 Project Deliverables</h1>
            <p className="text-gray-600">
              Risultati finali{hasActionableAssets ? ' e asset azionabili' : ''} del progetto
            </p>
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

      {/* NEW: Actionable Assets Section */}
      {hasActionableAssets && (
        <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-xl p-8 border border-indigo-200 shadow-lg">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mb-4">
              <span className="text-2xl">🎯</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Asset Azionabili Pronti!</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Il tuo progetto ha prodotto <strong>{Object.keys(actionableAssets).length} asset business-ready</strong> che puoi utilizzare immediatamente.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(actionableAssets).map(([assetName, asset]) => (
              <ActionableAssetCard
                key={assetName}
                assetName={assetName}
                asset={asset}
                onDownload={() => handleDownloadAsset(assetName, asset)}
                onViewDetails={() => handleViewAssetDetails(assetName, asset)}
              />
            ))}
          </div>

          {/* Quick actions for all assets */}
          <div className="mt-8 text-center">
            <div className="inline-flex space-x-4">
              <button
                onClick={() => {
                  // Download all assets
                  Object.entries(actionableAssets).forEach(([name, asset]) => {
                    setTimeout(() => handleDownloadAsset(name, asset), 100);
                  });
                }}
                className="bg-white text-indigo-700 px-6 py-3 rounded-lg font-medium hover:bg-indigo-50 transition border border-indigo-200 shadow-sm"
              >
                📦 Scarica Tutti gli Asset
              </button>
              <button
                onClick={() => {
                  setFeedbackTaskId(null);
                  setShowFeedbackForm(true);
                }}
                className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition shadow-sm"
              >
                💬 Fornisci Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Executive summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-3">📊 Executive Summary</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">{deliverables.summary}</div>
        <div className="text-xs text-gray-500 mt-2">Generato il {formatDate(deliverables.generated_at)}</div>
      </div>

      {/* Actionable outputs */}
      {actionableOutputs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {actionableOutputs.map(o => (
            <ActionableOutputCard key={o.task_id} output={o} onClick={() => openOutputModal(o)} />
          ))}
        </div>
      )}

      {/* Final deliverable spotlight */}
      {showMore && finalDeliverables.length > 0 && (
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-indigo-800 text-white rounded-xl shadow-lg p-8 space-y-8">
          <div className="flex justify-between">
            <div>
              <div className="flex items-center mb-2">
                <span className="text-3xl mr-3">🎯</span>
                <h2 className="text-2xl font-bold">Deliverable Finale Completato</h2>
              </div>
              <p className="text-indigo-100">
                Il tuo progetto ha raggiunto un traguardo importante con la produzione del deliverable finale
                {hasActionableAssets && <span className="font-semibold"> contenente {Object.keys(actionableAssets).length} asset azionabili</span>}.
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

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleQuickFeedback('approve', d.task_id)}
                      className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700"
                    >
                      ✅ Approva
                    </button>
                    <button
                      onClick={() => handleQuickFeedback('request_changes', d.task_id)}
                      className="flex-1 bg-orange-500 text-white py-2 rounded-lg text-sm hover:bg-orange-600"
                    >
                      📝 Rework
                    </button>
                  </div>
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
              <p className="text-sm text-indigo-200">
                Approva il deliverable{hasActionableAssets ? ' e gli asset' : ''} o richiedi modifiche
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setFeedbackType('approve');
                  setFeedbackTaskId(finalDeliverables[0]?.task_id || null);
                  setShowFeedbackForm(true);
                }}
                className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-lg font-medium"
              >
                ✅ Approva
              </button>
              <button
                onClick={() => {
                  setFeedbackType('request_changes');
                  setFeedbackTaskId(finalDeliverables[0]?.task_id || null);
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
      <button
        onClick={() => setShowMore(!showMore)}
        className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
      >
        {showMore ? 'Hide details' : 'More details'}
      </button>
      {showMore && (
      <div className="bg-white rounded-lg shadow-sm p-6 mt-4">
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
            {hasActionableAssets 
              ? 'Tutti i deliverable sono stati consolidati negli asset azionabili' 
              : 'Nessun deliverable intermedio disponibile'}
          </div>
        )}
      </div>
      )}

      {/* Enhanced Feedback section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">💬 Feedback e Azioni</h2>

        {!showFeedbackForm ? (
          <>
            <p className="text-gray-600 mb-4">
              Cosa ne pensi dei risultati{hasActionableAssets ? ' e degli asset prodotti' : ''}? 
              Puoi approvare il progetto o richiedere modifiche.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => {
                  setFeedbackType('approve');
                  setShowFeedbackForm(true);
                }}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                ✅ Approva {hasActionableAssets ? 'Asset e ' : ''}Progetto
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
                  setFeedbackTaskId(null);
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
                {feedbackType === 'approve' && `✅ Approva ${hasActionableAssets ? 'Asset e ' : ''}Progetto`}
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
                  ? `Es. Ottimo lavoro! ${hasActionableAssets ? 'Gli asset sono perfetti e pronti all\'uso. ' : ''}Il progetto soddisfa tutti i requisiti…`
                  : feedbackType === 'request_changes'
                  ? `Es. ${hasActionableAssets ? 'Gli asset sono buoni ma vorrei modifiche su... ' : ''}Vorrei che venissero approfonditi i seguenti aspetti…`
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
                onClick={() => handleSubmitFeedback(feedbackTaskId ? [feedbackTaskId] : undefined)}
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

      {/* NEW: Asset Viewer Modal */}
      {selectedAsset && (
        <SimpleAssetViewer
          assetName={selectedAsset.name}
          asset={selectedAsset.asset}
          onClose={() => setSelectedAsset(null)}
        />
      )}

      {selectedOutput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">{selectedOutput.title || selectedOutput.task_name}</h2>
              <button onClick={() => { setSelectedOutput(null); setOutputDetails(null); }} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            {loadingOutput ? (
              <div className="text-center py-10">Caricamento...</div>
            ) : (
              <TaskResultDetails result={outputDetails} />
            )}
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => api.monitoring.submitDeliverableFeedback(workspaceId, { feedback_type: 'request_changes', message: '', specific_tasks: [selectedOutput.task_id], priority: 'medium' })}
                className="px-4 py-2 bg-orange-600 text-white rounded-md text-sm"
              >
                Request changes
              </button>
              <button
                onClick={() => api.monitoring.submitDeliverableFeedback(workspaceId, { feedback_type: 'approve', message: 'generate new deliverable', specific_tasks: [selectedOutput.task_id], priority: 'medium' })}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm"
              >
                Generate new deliverable
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}