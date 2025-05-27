// frontend/src/components/AssetDashboard.tsx - ENHANCED & UNIFIED VERSION

'use client';

import React, { useState } from 'react';
import { useAssetManagement } from '@/hooks/useAssetManagement';
import ActionableAssetViewer from './ActionableAssetViewer';
import type { ActionableAsset } from '@/types';

interface AssetDashboardProps {
  workspaceId: string;
}

// Asset Viewer Component per singolo asset
const AssetViewer: React.FC<{
  asset: ActionableAsset;
  onDownload?: () => void;
  onUse?: () => void;
  onViewDetails?: () => void;
  showActions?: boolean;
}> = ({ asset, onDownload, onUse, onViewDetails, showActions = true }) => {
  const getActionabilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getAssetTypeIcon = (assetName: string) => {
    const name = assetName.toLowerCase();
    if (name.includes('calendar')) return '📅';
    if (name.includes('contact') || name.includes('database')) return '📊';
    if (name.includes('content')) return '📝';
    if (name.includes('strategy')) return '🎯';
    if (name.includes('analysis')) return '📈';
    return '📄';
  };

  const renderAssetData = () => {
    if (!asset.asset_data || typeof asset.asset_data !== 'object') {
      return <p className="text-gray-500">Nessun dato disponibile</p>;
    }

    // If asset_data has specific structure, render it nicely
    if (Array.isArray(asset.asset_data.posts)) {
      // Content Calendar
      return (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-800">📅 Calendario Contenuti</h4>
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <div className="text-sm text-gray-600 mb-2">
              {asset.asset_data.posts.length} post programmati
            </div>
            {asset.asset_data.posts.slice(0, 3).map((post, idx) => (
              <div key={idx} className="bg-white p-3 rounded border border-gray-200 mb-2">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{post.date} {post.time}</span>
                  <span className="capitalize">{post.platform}</span>
                </div>
                <p className="text-sm text-gray-800 truncate">{post.caption}</p>
                {post.hashtags && (
                  <div className="mt-1">
                    {post.hashtags.slice(0, 3).map((tag, i) => (
                      <span key={i} className="text-xs bg-blue-100 text-blue-700 px-1 rounded mr-1">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {asset.asset_data.posts.length > 3 && (
              <div className="text-center text-sm text-gray-500 mt-2">
                ...e altri {asset.asset_data.posts.length - 3} post
              </div>
            )}
          </div>
        </div>
      );
    }

    if (Array.isArray(asset.asset_data.contacts)) {
      // Contact Database
      return (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-800">📊 Database Contatti</h4>
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <div className="text-sm text-gray-600 mb-2">
              {asset.asset_data.contacts.length} contatti qualificati
            </div>
            {asset.asset_data.contacts.slice(0, 3).map((contact, idx) => (
              <div key={idx} className="bg-white p-3 rounded border border-gray-200 mb-2">
                <div className="flex justify-between">
                  <span className="font-medium">{contact.name || contact.company}</span>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                    Score: {contact.qualification_score || 'N/A'}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {contact.email} • {contact.industry || contact.role}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Generic object display
    return (
      <div className="space-y-4">
        <h4 className="font-medium text-gray-800">📄 Dati Asset</h4>
        <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(asset.asset_data, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Asset Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">{getAssetTypeIcon(asset.asset_name)}</div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 capitalize">
                {asset.asset_name.replace(/_/g, ' ')}
              </h3>
              <p className="text-sm text-gray-500">
                Estratto da task {asset.source_task_id.substring(0, 8)}...
              </p>
            </div>
          </div>
          
          {/* Ready to Use Badge */}
          {asset.ready_to_use && (
            <div className="flex items-center space-x-2">
              <span className="bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full font-medium">
                ✅ Pronto all'uso
              </span>
              {asset.automation_ready && (
                <span className="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium">
                  🤖 Automazione
                </span>
              )}
            </div>
          )}
        </div>

        {/* Actionability Score */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">Punteggio Azionabilità</span>
            <span className="font-medium">{Math.round(asset.actionability_score * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-500 ${
                asset.actionability_score >= 0.8 ? 'bg-green-500' :
                asset.actionability_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${asset.actionability_score * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Asset Data Preview */}
        {renderAssetData()}

        {/* Usage Instructions */}
        {asset.usage_instructions && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-800 mb-2">💡 Istruzioni per l'uso</h4>
            <p className="text-sm text-blue-700">{asset.usage_instructions}</p>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="mt-6 flex space-x-3">
            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                Visualizza Dettagli
              </button>
            )}

            {onDownload && (
              <button
                onClick={onDownload}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Scarica Asset
              </button>
            )}
            
            {asset.ready_to_use && onUse && (
              <button
                onClick={onUse}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Usa Subito
              </button>
            )}
            
            <button
              onClick={() => {
                const dataStr = JSON.stringify(asset.asset_data, null, 2);
                navigator.clipboard.writeText(dataStr);
                // Could add a toast notification here
              }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copia
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Main Asset Dashboard Component
export default function AssetDashboard({ workspaceId }: AssetDashboardProps) {
  // 🆕 FIXED: Use enhanced hook properly
  const {
    tracking,
    requirements,
    schemas,
    assets,
    assetDisplayData,
    getAssetCompletionStats,
    triggerAssetAnalysis,
    loading,
    error,
    refresh
  } = useAssetManagement(workspaceId);

  const [activeTab, setActiveTab] = useState<'overview' | 'assets' | 'requirements'>('overview');
  const [selectedAsset, setSelectedAsset] = useState<ActionableAsset | null>(null);

  const assetStats = getAssetCompletionStats();

  const handleDownloadAsset = (asset: ActionableAsset) => {
    const dataStr = JSON.stringify(asset.asset_data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${asset.asset_name}_${asset.source_task_id.substring(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleUseAsset = (asset: ActionableAsset) => {
    // Open asset in a new window/tab or copy to clipboard
    const dataStr = JSON.stringify(asset.asset_data, null, 2);
    navigator.clipboard.writeText(dataStr);
    alert('Asset copiato negli appunti! Puoi ora incollarlo nel tuo strumento preferito.');
  };

  const handleViewAssetDetails = (asset: ActionableAsset) => {
    setSelectedAsset(asset);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Errore nel caricamento</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button 
            onClick={refresh}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">🎯 Asset Azionabili</h1>
            <p className="text-gray-600">Risultati business-ready pronti per l'implementazione</p>
          </div>
          <button 
            onClick={refresh}
            className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md text-sm hover:bg-indigo-100 transition"
          >
            Aggiorna
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', label: '📊 Panoramica', count: assetStats.totalAssets },
              { id: 'assets', label: '🎯 Asset Pronti', count: assets.length },
              { id: 'requirements', label: '📋 Requisiti', count: requirements?.primary_assets_needed?.length || 0 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                    activeTab === tab.id ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-600 text-sm font-medium">Asset Totali</p>
                      <p className="text-2xl font-bold text-blue-900">{assetStats.totalAssets}</p>
                    </div>
                    <div className="text-blue-500 text-2xl">📄</div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-600 text-sm font-medium">Completati</p>
                      <p className="text-2xl font-bold text-green-900">{assetStats.completedAssets}</p>
                    </div>
                    <div className="text-green-500 text-2xl">✅</div>
                  </div>
                </div>

                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-yellow-600 text-sm font-medium">In Corso</p>
                      <p className="text-2xl font-bold text-yellow-900">{assetStats.pendingAssets}</p>
                    </div>
                    <div className="text-yellow-500 text-2xl">⏳</div>
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-600 text-sm font-medium">Tasso Completamento</p>
                      <p className="text-2xl font-bold text-purple-900">{Math.round(assetStats.completionRate)}%</p>
                    </div>
                    <div className="text-purple-500 text-2xl">📈</div>
                  </div>
                </div>
              </div>

              {/* Asset Types Breakdown */}
              {tracking?.asset_types_breakdown && Object.keys(tracking.asset_types_breakdown).length > 0 && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="font-medium text-gray-900 mb-4">📊 Distribuzione per Tipo di Asset</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(tracking.asset_types_breakdown).map(([type, data]) => (
                      <div key={type} className="bg-white p-4 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-medium text-gray-800 capitalize">{type.replace(/_/g, ' ')}</h4>
                          <span className="text-sm text-gray-500">{data.completed}/{data.total}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${(data.completed / data.total) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Deliverable Ready Status */}
              {assetStats.isDeliverableReady && (
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
                  <div className="flex items-center">
                    <div className="text-4xl mr-4">🎯</div>
                    <div>
                      <h3 className="text-lg font-semibold text-green-800">Deliverable Pronto!</h3>
                      <p className="text-green-700">
                        Gli asset hanno raggiunto la soglia di completamento necessaria per creare il deliverable finale.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'assets' && (
            <div className="space-y-6">
              {assets.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📄</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun Asset Disponibile</h3>
                  <p className="text-gray-500">
                    Gli asset verranno visualizzati qui una volta completati i task di produzione.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {assetDisplayData.map((assetData, index) => (
                    <AssetViewer
                      key={index}
                      asset={assetData.asset}
                      onDownload={() => handleDownloadAsset(assetData.asset)}
                      onUse={() => handleUseAsset(assetData.asset)}
                      onViewDetails={() => handleViewAssetDetails(assetData.asset)}
                      showActions={true}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'requirements' && (
            <div className="space-y-6">
              {requirements ? (
                <div>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      📋 Requisiti Asset per categoria: {requirements.deliverable_category}
                    </h3>
                    <p className="text-gray-600">
                      Asset richiesti per completare con successo questo progetto
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {requirements.primary_assets_needed.map((req, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium text-gray-900 capitalize">
                            {req.asset_type.replace(/_/g, ' ')}
                          </h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            req.priority === 1 ? 'bg-red-100 text-red-800' :
                            req.priority === 2 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            Priorità {req.priority}
                          </span>
                        </div>

                        <div className="space-y-3">
                          <div>
                            <span className="text-sm font-medium text-gray-600">Formato:</span>
                            <span className="ml-2 text-sm text-gray-800 capitalize">
                              {req.asset_format.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <div>
                            <span className="text-sm font-medium text-gray-600">Livello:</span>
                            <span className="ml-2 text-sm text-gray-800 capitalize">
                              {req.actionability_level.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <div>
                            <span className="text-sm font-medium text-gray-600">Impatto:</span>
                            <span className="ml-2 text-sm text-gray-800 capitalize">
                              {req.business_impact.replace(/_/g, ' ')}
                            </span>
                          </div>

                          {req.validation_criteria.length > 0 && (
                            <div>
                              <span className="text-sm font-medium text-gray-600">Criteri di validazione:</span>
                              <ul className="mt-1 space-y-1">
                                {req.validation_criteria.map((criterion, idx) => (
                                  <li key={idx} className="text-sm text-gray-700 flex items-center">
                                    <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                                    {criterion}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📋</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Requisiti Non Disponibili</h3>
                  <p className="text-gray-500">
                    I requisiti degli asset verranno generati automaticamente durante l'analisi del progetto.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Asset Viewer Modal */}
      {selectedAsset && (
        <ActionableAssetViewer
          assetName={selectedAsset.asset_name}
          asset={selectedAsset}
          onClose={() => setSelectedAsset(null)}
        />
      )}
    </div>
  );
}