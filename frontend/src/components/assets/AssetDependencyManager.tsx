'use client';

import React, { useState } from 'react';
import { useAssetDependencies } from '@/hooks/useAssetDependencies';
import { RelatedAssetsModal } from './RelatedAssetsModal';
import { AssetHistoryPanel } from './AssetHistoryPanel';
import { DependencyGraph, AssetNode, AssetEdge } from './DependencyGraph';

interface Props {
  workspaceId: string;
  assetId?: string;
  triggerMode?: 'manual' | 'auto';
  className?: string;
}

export const AssetDependencyManager: React.FC<Props> = ({
  workspaceId,
  assetId,
  triggerMode = 'manual',
  className = ''
}) => {
  const {
    suggestions,
    history,
    loading,
    error,
    checkDependencies,
    applySelectedUpdates,
    fetchAssetHistory,
    compareVersions,
    clearSuggestions,
    clearHistory
  } = useAssetDependencies();

  const [activeView, setActiveView] = useState<'suggestions' | 'history' | 'graph' | null>(null);
  const [dependencyGraph, setDependencyGraph] = useState<{nodes: AssetNode[], edges: AssetEdge[]} | null>(null);
  const [selectedAssetForHistory, setSelectedAssetForHistory] = useState<string>('');

  // Funzione per controllare dipendenze di un asset
  const handleCheckDependencies = async (targetAssetId: string) => {
    const result = await checkDependencies(targetAssetId);
    if (result?.affected_assets?.length > 0) {
      setActiveView('suggestions');
    }
  };

  // Funzione per visualizzare history di un asset
  const handleViewHistory = async (targetAssetId: string) => {
    setSelectedAssetForHistory(targetAssetId);
    await fetchAssetHistory(targetAssetId);
    setActiveView('history');
  };

  // Funzione per visualizzare dependency graph
  const handleViewDependencyGraph = async () => {
    try {
      // Chiama API per ottenere dependency graph
      const graphData = await fetch(`/api/workspaces/${workspaceId}/dependency-graph${assetId ? `?central_asset=${assetId}` : ''}`);
      const result = await graphData.json();
      setDependencyGraph(result);
      setActiveView('graph');
    } catch (error) {
      console.error('Failed to load dependency graph:', error);
    }
  };

  // Funzione per applicare aggiornamenti
  const handleApplyUpdates = async (selectedIds: string[], options: any) => {
    if (!assetId) return;
    
    await applySelectedUpdates(assetId, selectedIds, options);
    clearSuggestions();
    setActiveView(null);
    
    // Ricarica il dependency graph se era aperto
    if (activeView === 'graph') {
      handleViewDependencyGraph();
    }
  };

  // Funzione per confrontare versioni
  const handleCompareVersions = async (targetAssetId: string, fromVersion: string, toVersion: string) => {
    return await compareVersions(targetAssetId, fromVersion, toVersion);
  };

  // Chiude le viste attive
  const closeActiveView = () => {
    setActiveView(null);
    clearSuggestions();
    clearHistory();
    setDependencyGraph(null);
    setSelectedAssetForHistory('');
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="text-red-600 mr-3">⚠️</div>
          <div>
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Control Panel */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Asset Dependency Management</h2>
          <div className="text-xs text-gray-500">
            Workspace: {workspaceId.slice(0, 8)}...
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Check Dependencies Button */}
          <button
            onClick={() => assetId && handleCheckDependencies(assetId)}
            disabled={!assetId || loading}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
            <span className="text-sm font-medium">
              {loading ? 'Checking...' : 'Check Dependencies'}
            </span>
          </button>

          {/* View History Button */}
          <button
            onClick={() => assetId && handleViewHistory(assetId)}
            disabled={!assetId || loading}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-purple-50 border border-purple-200 text-purple-700 rounded-lg hover:bg-purple-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm font-medium">View History</span>
          </button>

          {/* Dependency Graph Button */}
          <button
            onClick={handleViewDependencyGraph}
            disabled={loading}
            className="flex items-center justify-center space-x-2 px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-lg hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
            </svg>
            <span className="text-sm font-medium">Dependency Graph</span>
          </button>
        </div>

        {/* Quick Stats */}
        {assetId && (
          <div className="mt-4 p-3 bg-gray-50 rounded border grid grid-cols-3 gap-4 text-center text-sm">
            <div>
              <div className="font-medium text-gray-900">Current Asset</div>
              <div className="text-gray-600">{assetId.slice(0, 12)}...</div>
            </div>
            <div>
              <div className="font-medium text-gray-900">Mode</div>
              <div className="text-gray-600 capitalize">{triggerMode}</div>
            </div>
            <div>
              <div className="font-medium text-gray-900">Status</div>
              <div className="text-gray-600">
                {loading ? 'Processing...' : 'Ready'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Active View Content */}
      {activeView === 'suggestions' && suggestions && (
        <RelatedAssetsModal
          isOpen={true}
          onClose={closeActiveView}
          suggestion={suggestions}
          onApplyUpdates={handleApplyUpdates}
          loading={loading}
        />
      )}

      {activeView === 'history' && (
        <AssetHistoryPanel
          assetId={selectedAssetForHistory}
          history={history}
          onFetchHistory={fetchAssetHistory}
          onCompareVersions={handleCompareVersions}
          loading={loading}
          className="mt-4"
        />
      )}

      {activeView === 'graph' && dependencyGraph && (
        <DependencyGraph
          nodes={dependencyGraph.nodes}
          edges={dependencyGraph.edges}
          centralNodeId={assetId}
          onNodeClick={(node) => {
            // Permette di controllare dipendenze del nodo cliccato
            handleCheckDependencies(node.id);
          }}
          onEdgeClick={(edge) => {
            console.log('Edge clicked:', edge);
            // Possibilità di mostrare dettagli della relazione
          }}
          className="mt-4"
          interactive={true}
          showLabels={true}
          layout="circular"
        />
      )}

      {/* Auto-trigger per feedback */}
      {triggerMode === 'auto' && assetId && (
        <div className="text-xs text-gray-500 text-center">
          ⚡ Auto-dependency checking enabled for asset updates
        </div>
      )}
    </div>
  );
};