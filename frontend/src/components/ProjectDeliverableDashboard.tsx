'use client';

import React, { useState } from 'react';
import { api } from '@/utils/api';
import { DeliverableFeedback, ActionableAsset, ProjectOutputExtended } from '@/types';
import { useProjectDeliverables } from '@/hooks/useProjectDeliverables';
import DeliverableInsightCard from './DeliverableInsightCard';
import ActionableOutputCard from './ActionableOutputCard';
import TaskResultDetails from './TaskResultDetails';
import DeliverableCard from './redesign/DeliverableCard';

interface ProjectDeliverableDashboardProps {
  workspaceId: string;
}

// Using the redesigned DeliverableCard component instead of the old ActionableAssetCard

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
  const {
    deliverables,
    loading,
    error,
    refetch,
    submitFeedback,
  } = useProjectDeliverables(workspaceId);

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
  // Loading and error handling are managed by the useProjectDeliverables hook

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
      await submitFeedback(feedbackData);
      setFeedback('');
      setShowFeedbackForm(false);
      setFeedbackType('general_feedback');
      setFeedbackTaskId(null);
      alert('Feedback inviato con successo!');
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
      const details = await api.monitoring.getTaskResult(workspaceId, output.task_id);
      setOutputDetails(details);
    } catch (err) {
      console.error('Error fetching output', err);
      setOutputDetails(null);
    } finally {
      setLoadingOutput(false);
    }
  };

  const handleQuickFeedback = async (
    type: 'approve' | 'request_changes',
    taskId: string,
  ) => {
    try {
      await submitFeedback({
        feedback_type: type,
        message: '',
        priority: 'medium',
        specific_tasks: [taskId],
      });
    } catch (err) {
      console.error('Error sending feedback', err);
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
          onClick={refetch}
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
      {/* Clean Header - Content Focused */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Deliverables</h1>
            <p className="text-gray-600 mt-1">
              {hasActionableAssets ? `${Object.keys(actionableAssets).length} business-ready assets` : 'Project deliverables and assets'}
            </p>
          </div>
          {/* Auto-completion status indicator */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Auto-completing missing deliverables</span>
            </div>
          </div>
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
            {Object.entries(actionableAssets).map(([assetName, asset]) => {
              // Convert asset to ProjectOutputExtended format for DeliverableCard
              const assetAsOutput: ProjectOutputExtended = {
                task_id: asset.source_task_id,
                task_name: assetName.replace(/_/g, ' ').toUpperCase(),
                title: assetName.replace(/_/g, ' ').toUpperCase(),
                output: `Business-ready ${assetName} asset with ${Object.keys(asset.asset_data).length} data points`,
                summary: `Ready-to-use ${assetName} asset for immediate implementation`,
                type: 'final_deliverable',
                category: 'execution',
                agent_name: 'Asset Packager',
                agent_role: 'specialist',
                created_at: new Date().toISOString(),
                actionable_assets: {
                  [assetName]: asset
                },
                result: {
                  actionable_assets: {
                    [assetName]: asset
                  }
                },
                metrics: {
                  validation_score: Math.round(asset.validation_score * 100),
                  actionability_score: Math.round(asset.actionability_score * 100),
                  ready_to_use: asset.ready_to_use
                },
                key_insights: [
                  `Asset quality: ${Math.round(asset.validation_score * 100)}%`,
                  `Actionability: ${Math.round(asset.actionability_score * 100)}%`,
                  asset.ready_to_use ? 'Ready for immediate use' : 'Requires customization'
                ]
              };

              return (
                <DeliverableCard
                  key={assetName}
                  output={assetAsOutput}
                  workspaceId={workspaceId}
                  onViewDetails={() => handleViewAssetDetails(assetName, asset)}
                />
              );
            })}
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

      {/* Removed executive summary - status overview moved to Overview tab */}

      {/* Actionable outputs */}
      {actionableOutputs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">🎯 Altri Output Azionabili</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {actionableOutputs.map(o => (
              <DeliverableCard 
                key={o.task_id} 
                output={o} 
                workspaceId={workspaceId}
                onViewDetails={() => openOutputModal(o)} 
              />
            ))}
          </div>
        </div>
      )}

      {/* Clean Final Deliverables Section */}
      {showMore && finalDeliverables.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Final Deliverables</h2>
            <span className="text-sm text-gray-500">{finalDeliverables.length} completed</span>
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

        </div>
      )}

      {/* Simplified Additional Deliverables */}
      {normalDeliverables.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Additional Outputs</h2>
            <span className="text-sm text-gray-500">{normalDeliverables.length} items</span>
          </div>
        </div>
        
        <div className="space-y-3">
          {normalDeliverables.map((output) => (
            <div key={output.task_id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-2">{output.task_name}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">
                    {output.output.length > 200 ? `${output.output.slice(0, 200)}...` : output.output}
                  </p>
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-gray-500">
                      {output.agent_name} • {formatDate(output.created_at)}
                    </span>
                    <button
                      onClick={() => openOutputModal(output)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        </div>
      )}

      {/* Removed feedback section - moved to dedicated feedback tab/area */}

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
              <TaskResultDetails 
                result={outputDetails} 
                workspaceId={workspaceId}
                taskId={selectedOutput.task_id}
              />
            )}
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => handleQuickFeedback('request_changes', selectedOutput.task_id)}
                className="px-4 py-2 bg-orange-600 text-white rounded-md text-sm"
              >
                Request changes
              </button>
              <button
                onClick={() => handleQuickFeedback('approve', selectedOutput.task_id)}
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