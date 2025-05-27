// frontend/src/components/ProjectActionsSection.tsx - ENHANCED WITH ASSET SUPPORT

"use client"
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Workspace } from '@/types';
import { api } from '@/utils/api';
import { useAssetManagement } from '@/hooks/useAssetManagement';

interface ProjectActionsSectionProps {
  workspace: Workspace;
  onStartTeam: () => void;
  onDeleteClick: () => void;
  isStartingTeam: boolean;
  feedbackRequests: any[];
}

// NEW: Asset Action Card Component
const AssetActionCard: React.FC<{
  title: string;
  description: string;
  action: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon: string;
  variant?: 'primary' | 'secondary' | 'warning';
}> = ({ 
  title, 
  description, 
  action, 
  onClick, 
  disabled = false, 
  loading = false, 
  icon, 
  variant = 'primary' 
}) => {
  const variantClasses = {
    primary: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
    secondary: 'from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700',
    warning: 'from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700'
  };

  return (
    <div className={`bg-gradient-to-r ${variantClasses[variant]} text-white rounded-lg p-4 border border-opacity-20 border-white shadow-lg`}>
      <div className="flex items-start mb-3">
        <span className="text-2xl mr-3">{icon}</span>
        <div>
          <h3 className="font-medium">{title}</h3>
          <p className="text-sm text-white text-opacity-90 mt-1">{description}</p>
        </div>
      </div>
      <button
        onClick={onClick}
        disabled={disabled || loading}
        className="w-full bg-white bg-opacity-20 hover:bg-opacity-30 py-2 px-4 rounded-md text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {loading ? (
          <>
            <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
            Caricamento...
          </>
        ) : (
          action
        )}
      </button>
    </div>
  );
};

// NEW: Asset Dashboard Widget
const AssetDashboardWidget: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const [assetData, setAssetData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const {
    getAssetCompletionStats,
    triggerAssetAnalysis,
    checkDeliverableReadiness
  } = useAssetManagement(workspaceId);

  const assetStats = getAssetCompletionStats();

  useEffect(() => {
    const fetchAssetData = async () => {
      try {
        const [trackingData, readinessData] = await Promise.all([
          api.assetManagement.getAssetTracking(workspaceId),
          api.assetManagement.getDeliverableReadiness(workspaceId)
        ]);
        setAssetData({ tracking: trackingData, readiness: readinessData });
      } catch (error) {
        console.error('Error fetching asset data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAssetData();
    const interval = setInterval(fetchAssetData, 30000);
    return () => clearInterval(interval);
  }, [workspaceId]);

  const handleTriggerAnalysis = async () => {
    try {
      setTriggering(true);
      await triggerAssetAnalysis();
      // Refresh data
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error('Error triggering analysis:', error);
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const isDeliverableReady = assetData?.readiness?.is_ready_for_deliverable || false;
  const hasExistingDeliverable = assetData?.readiness?.has_existing_deliverable || false;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">📦 Asset Management</h2>
      
      {assetStats.totalAssets === 0 ? (
        <div className="bg-gray-50 rounded-lg p-6 text-center">
          <div className="text-4xl mb-3">📦</div>
          <p className="text-gray-600 mb-2">Nessun asset in produzione</p>
          <p className="text-sm text-gray-500 mb-4">
            Gli asset verranno generati automaticamente durante l'esecuzione del progetto
          </p>
          <button
            onClick={handleTriggerAnalysis}
            disabled={triggering}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition disabled:opacity-50"
          >
            {triggering ? 'Analisi in corso...' : '🔍 Analizza Requirements Asset'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Asset Progress Summary */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-blue-800">Progresso Asset</h3>
              <span className="text-sm text-blue-700">
                {assetStats.completedAssets}/{assetStats.totalAssets} completati
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${assetStats.completionRate}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-blue-600 mt-2">
              <span>{Math.round(assetStats.completionRate)}% completato</span>
              {assetStats.isDeliverableReady && (
                <span className="font-medium animate-pulse">🎯 Deliverable Ready!</span>
              )}
            </div>
          </div>

          {/* Asset Actions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* View Assets Action */}
            <AssetActionCard
              icon="👁️"
              title="Visualizza Asset"
              description="Esplora gli asset prodotti e il loro stato"
              action="Visualizza Asset"
              onClick={() => window.open(`/projects/${workspaceId}/assets`, '_blank')}
              variant="primary"
            />

            {/* Download Assets Action */}
            {assetStats.completedAssets > 0 && (
              <AssetActionCard
                icon="📥"
                title="Scarica Asset"
                description="Scarica tutti gli asset completati"
                action="Scarica Tutto"
                onClick={async () => {
                  try {
                    const data = await api.assetManagement.getAssetTracking(workspaceId);
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `assets_${workspaceId}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch (error) {
                    console.error('Error downloading assets:', error);
                  }
                }}
                variant="secondary"
              />
            )}

            {/* Create Deliverable Action */}
            {isDeliverableReady && !hasExistingDeliverable && (
              <AssetActionCard
                icon="🎯"
                title="Crea Deliverable"
                description="Genera il deliverable finale con tutti gli asset"
                action="Crea Deliverable Finale"
                onClick={async () => {
                  try {
                    await api.monitoring.triggerFinalDeliverable(workspaceId);
                    setTimeout(() => window.location.reload(), 3000);
                  } catch (error) {
                    console.error('Error creating deliverable:', error);
                  }
                }}
                variant="primary"
              />
            )}

            {/* View Deliverable Action */}
            {hasExistingDeliverable && (
              <AssetActionCard
                icon="📋"
                title="Visualizza Deliverable"
                description="Vedi il deliverable finale con asset azionabili"
                action="Apri Deliverable"
                onClick={() => window.open(`/projects/${workspaceId}/deliverables`, '_blank')}
                variant="primary"
              />
            )}

            {/* Trigger Analysis Action */}
            <AssetActionCard
              icon="🔄"
              title="Aggiorna Analisi"
              description="Rigenera l'analisi dei requirements asset"
              action="Aggiorna Analisi"
              onClick={handleTriggerAnalysis}
              loading={triggering}
              variant="secondary"
            />

            {/* Force Completion Action - Emergency */}
            {assetStats.totalAssets > 0 && assetStats.completionRate < 70 && (
              <AssetActionCard
                icon="⚡"
                title="Forza Completamento"
                description="Forza la creazione del deliverable (emergenza)"
                action="Forza Completamento"
                onClick={async () => {
                  if (confirm('Sei sicuro di voler forzare il completamento? Questo può generare un deliverable incompleto.')) {
                    try {
                      await api.monitoring.forceFinalization(workspaceId);
                      setTimeout(() => window.location.reload(), 3000);
                    } catch (error) {
                      console.error('Error forcing completion:', error);
                    }
                  }
                }}
                variant="warning"
              />
            )}
          </div>

          {/* Asset Types Breakdown */}
          {assetData?.tracking?.asset_types_breakdown && Object.keys(assetData.tracking.asset_types_breakdown).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-medium text-gray-800 mb-3">Asset per Tipologia</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(assetData.tracking.asset_types_breakdown).map(([type, data]: [string, any]) => (
                  <div key={type} className="bg-white p-3 rounded-md border border-gray-100">
                    <div className="text-sm font-medium text-gray-700 capitalize">
                      {type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {data.completed}/{data.total} completati
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div 
                        className="bg-blue-600 h-1 rounded-full"
                        style={{ width: `${data.total > 0 ? (data.completed / data.total) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function ProjectActionsSection({ 
  workspace, 
  onStartTeam, 
  onDeleteClick, 
  isStartingTeam,
  feedbackRequests
}: ProjectActionsSectionProps) {
  return (
    <div className="space-y-6">
      {/* Human Feedback Section - Enhanced with Asset Context */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">🤝 Richieste di Feedback</h2>
        
        {feedbackRequests.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <p className="text-lg text-gray-600 mb-2">Nessuna richiesta di feedback in attesa</p>
            <p className="text-sm text-gray-500">
              Verrai notificato quando un agente richiede la tua approvazione o input
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {feedbackRequests.map((request) => (
              <div 
                key={request.id} 
                className={`border rounded-lg p-4 ${
                  request.priority === 'high' 
                    ? 'border-red-300 bg-red-50' 
                    : request.priority === 'medium'
                    ? 'border-yellow-300 bg-yellow-50'
                    : 'border-blue-300 bg-blue-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{request.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    request.priority === 'high' 
                      ? 'bg-red-200 text-red-800' 
                      : request.priority === 'medium'
                      ? 'bg-yellow-200 text-yellow-800'
                      : 'bg-blue-200 text-blue-800'
                  }`}>
                    {request.priority.toUpperCase()}
                  </span>
                </div>
                
                <div className="mt-3 space-y-2">
                  <p className="text-sm font-medium">Azioni proposte:</p>
                  {request.proposed_actions.map((action, index) => (
                    <div key={index} className="bg-white bg-opacity-60 p-2 rounded border border-gray-200">
                      <p className="text-sm">
                        <span className="font-medium">{action.type}:</span> {action.description}
                      </p>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 flex space-x-3">
                  <Link 
                    href={`/human-feedback?id=${request.id}`}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  >
                    Rispondi
                  </Link>
                </div>
              </div>
            ))}
            
            <Link 
              href="/human-feedback"
              className="block text-center text-indigo-600 hover:text-indigo-800 text-sm"
            >
              Visualizza tutte le richieste →
            </Link>
          </div>
        )}
      </div>

      {/* NEW: Asset Management Section */}
      <AssetDashboardWidget workspaceId={workspace.id} />
      
      {/* Project Control Actions - Enhanced */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">⚙️ Azioni di Controllo</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Team Status - Enhanced with Asset Info */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="font-medium mb-2">Stato Team & Asset</h3>
            
            {workspace.status === 'created' ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Il team è configurato ma non è ancora stato avviato. Avvia il team per iniziare a lavorare sul progetto e produrre asset.
                </p>
                <button 
                  onClick={onStartTeam}
                  disabled={isStartingTeam}
                  className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center disabled:opacity-50"
                >
                  {isStartingTeam ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                      Avvio in corso...
                    </>
                  ) : (
                    <>
                      <span className="mr-2">🚀</span>
                      Avvia Team
                    </>
                  )}
                </button>
              </div>
            ) : workspace.status === 'active' ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Il team è attivo e sta lavorando sul progetto producendo asset azionabili. Monitora il progresso nella sezione Asset.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Link 
                    href={`/projects/${workspace.id}/tasks`}
                    className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition"
                  >
                    📋 Attività
                  </Link>
                  <Link 
                    href={`/projects/${workspace.id}/team`}
                    className="px-3 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                  >
                    👥 Team
                  </Link>
                  <Link 
                    href={`/projects/${workspace.id}/assets`}
                    className="px-3 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition"
                  >
                    📦 Asset
                  </Link>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Stato attuale del progetto: <span className="font-medium">{workspace.status}</span>
                </p>
                <Link 
                  href={`/projects/${workspace.id}/configure`}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
                >
                  Configura Team
                </Link>
              </div>
            )}
          </div>

          {/* Enhanced Deliverables & Results */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 className="font-medium mb-2">Deliverable e Asset</h3>
            <p className="text-sm text-gray-600 mb-3">
              Visualizza deliverable finali con asset azionabili pronti per l'uso immediato.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link 
                href={`/projects/${workspace.id}/deliverables`}
                className="px-3 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition"
              >
                📋 Deliverable
              </Link>
              <Link 
                href={`/projects/${workspace.id}/assets`}
                className="px-3 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition"
              >
                📦 Asset
              </Link>
            </div>
          </div>
          
          {/* Tools Configuration - Enhanced */}
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <h3 className="font-medium mb-2">Strumenti e Schemi</h3>
            <p className="text-sm text-gray-600 mb-3">
              Configura tool e visualizza schemi per la produzione di asset azionabili.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link 
                href="/tools"
                className="px-3 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition"
              >
                🔧 Tool
              </Link>
              <Link 
                href={`/projects/${workspace.id}/schemas`}
                className="px-3 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              >
                📐 Schemi Asset
              </Link>
            </div>
          </div>
          
          {/* Project Removal */}
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <h3 className="font-medium mb-2">Eliminazione Progetto</h3>
            <p className="text-sm text-gray-600 mb-3">
              Attenzione: eliminerà permanentemente il progetto, tutti gli asset e i dati associati.
            </p>
            <button 
              onClick={onDeleteClick}
              className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 transition"
            >
              Elimina Progetto
            </button>
          </div>
        </div>
      </div>
      
      {/* Advanced Options - Enhanced with Asset Features */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">🔧 Opzioni Avanzate</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Monitoraggio Avanzato</h3>
            <p className="text-sm text-gray-600 mb-3">
              Dashboard completa con tracking asset e statistiche produzione.
            </p>
            <Link 
              href={`/projects/${workspace.id}/monitoring`}
              className="px-4 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
            >
              📊 Dashboard Completa
            </Link>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Gestione Budget & Asset</h3>
            <p className="text-sm text-gray-600 mb-3">
              Monitora costi e ROI degli asset prodotti dal progetto.
            </p>
            <Link 
              href={`/projects/${workspace.id}/budget`}
              className="px-4 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
            >
              💰 Gestione Budget
            </Link>
          </div>

          {/* NEW: Asset Analysis */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Analisi Asset Avanzata</h3>
            <p className="text-sm text-gray-600 mb-3">
              Analisi dettagliata di requirements, schemi e produzione asset.
            </p>
            <Link 
              href={`/projects/${workspace.id}/asset-analysis`}
              className="px-4 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
            >
              🔬 Analisi Asset
            </Link>
          </div>

          {/* NEW: Export/Import Assets */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-medium mb-2">Export/Import Asset</h3>
            <p className="text-sm text-gray-600 mb-3">
              Esporta asset per uso esterno o importa template esistenti.
            </p>
            <div className="flex space-x-2">
              <button
                onClick={async () => {
                  try {
                    const data = await api.assetManagement.getAssetTracking(workspace.id);
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `assets_export_${workspace.id}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch (error) {
                    console.error('Error exporting assets:', error);
                  }
                }}
                className="px-3 py-2 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-800 transition"
              >
                📤 Export
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}