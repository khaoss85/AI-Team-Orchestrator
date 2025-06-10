'use client';

import React, { useState, use } from 'react';
import Link from 'next/link';
import { useAssetDependencies } from '@/hooks/useAssetDependencies';
import { AssetHistoryPanel } from '@/components/assets/AssetHistoryPanel';
import { RelatedAssetsModal } from '@/components/assets/RelatedAssetsModal';
import { DependencyGraph } from '@/components/assets/DependencyGraph';
import { AIImpactPredictor } from '@/components/assets/AIImpactPredictor';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectAssetsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const workspaceId = params.id;
  
  const {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    dependencies,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    history,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    loading,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    fetchHistory,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    compareVersions,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyUpdates
  } = useAssetDependencies(workspaceId);

  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'dependencies' | 'history' | 'impact'>('history');
  const [showRelatedModal, setShowRelatedModal] = useState(false);

  // Mock asset list - replace with real data from API
  const assets = [
    { id: 'asset-1', name: 'Marketing Strategy Analysis', type: 'analysis', lastModified: '2024-01-15', versions: 3 },
    { id: 'asset-2', name: 'Competitor Research Report', type: 'report', lastModified: '2024-01-14', versions: 2 },
    { id: 'asset-3', name: 'Financial Projections', type: 'spreadsheet', lastModified: '2024-01-13', versions: 5 },
    { id: 'asset-4', name: 'Brand Guidelines', type: 'document', lastModified: '2024-01-12', versions: 1 },
  ];

  const tabs = [
    { id: 'history', label: 'Version History', icon: '📜', description: 'Cronologia modifiche' },
    { id: 'dependencies', label: 'Dependencies', icon: '🕸️', description: 'Relazioni asset' },
    { id: 'impact', label: 'Impact Analysis', icon: '🎯', description: 'Predizioni AI' }
  ];

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'analysis': return '📊';
      case 'report': return '📄';
      case 'spreadsheet': return '📈';
      case 'document': return '📝';
      default: return '📦';
    }
  };

  const getVersionBadgeColor = (count: number) => {
    if (count >= 5) return 'bg-red-100 text-red-800';
    if (count >= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Simple Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Asset History & Versions</h1>
            <p className="text-gray-600 mt-1">Track changes, manage dependencies, and analyze impact</p>
          </div>
          <Link
            href={`/projects/${workspaceId}/ai-management`}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
          >
            🤖 AI Features
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Asset List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Project Assets</h2>
              <p className="text-sm text-gray-600">Select an asset to view its history</p>
            </div>
            
            <div className="p-6">
              <div className="space-y-3">
                {assets.map((asset) => (
                  <div
                    key={asset.id}
                    onClick={() => setSelectedAssetId(asset.id)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                      selectedAssetId === asset.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl">{getAssetIcon(asset.type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-medium text-gray-900 truncate">
                            {asset.name}
                          </h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getVersionBadgeColor(asset.versions)}`}>
                            v{asset.versions}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 capitalize">
                          {asset.type}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Modified: {asset.lastModified}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {assets.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📦</div>
                  <p>No assets found</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2">
          {selectedAssetId ? (
            <>
              {/* Selected Asset Info */}
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm mb-6 p-6">
                <div className="flex items-center space-x-3 mb-4">
                  {assets.find(a => a.id === selectedAssetId) && (
                    <>
                      <span className="text-3xl">{getAssetIcon(assets.find(a => a.id === selectedAssetId)!.type)}</span>
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          {assets.find(a => a.id === selectedAssetId)!.name}
                        </h2>
                        <p className="text-sm text-gray-600 capitalize">
                          {assets.find(a => a.id === selectedAssetId)!.type} • 
                          {assets.find(a => a.id === selectedAssetId)!.versions} versions available
                        </p>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Tabs */}
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
                <div className="border-b border-gray-200">
                  <div className="flex space-x-8 px-6">
                    {tabs.map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as 'dependencies' | 'history' | 'impact')}
                        className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                          activeTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <span className="text-lg">{tab.icon}</span>
                        <span>{tab.label}</span>
                        <span className="text-xs text-gray-400 hidden md:block">
                          {tab.description}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Tab Content */}
              <div className="space-y-6">
                {activeTab === 'history' && (
                  <AssetHistoryPanel
                    assetId={selectedAssetId}
                    workspaceId={workspaceId}
                    className="shadow-sm"
                  />
                )}

                {activeTab === 'dependencies' && (
                  <div className="space-y-6">
                    <DependencyGraph 
                      workspaceId={workspaceId}
                      centralAssetId={selectedAssetId}
                      className="shadow-sm"
                    />
                    
                    <button
                      onClick={() => setShowRelatedModal(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Manage Related Assets
                    </button>
                  </div>
                )}

                {activeTab === 'impact' && (
                  <AIImpactPredictor
                    assetId={selectedAssetId}
                    workspaceId={workspaceId}
                    changeDescription="Analyze potential impact of upcoming changes"
                    onPredictionReady={(prediction) => {
                      console.log('Impact prediction:', prediction);
                    }}
                    className="shadow-sm"
                  />
                )}
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
              <div className="text-6xl mb-4">📜</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Seleziona un Asset per Visualizzare la Cronologia
              </h3>
              <p className="text-gray-600 mb-6">
                Scegli un asset dalla lista per vedere tutte le versioni, i cambiamenti e le dipendenze
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-md mx-auto">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl mb-2">📜</div>
                  <div className="text-sm font-medium text-blue-900">Version History</div>
                  <div className="text-xs text-blue-600">Track all changes</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl mb-2">🕸️</div>
                  <div className="text-sm font-medium text-green-900">Dependencies</div>
                  <div className="text-xs text-green-600">See relationships</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl mb-2">🎯</div>
                  <div className="text-sm font-medium text-purple-900">AI Impact</div>
                  <div className="text-xs text-purple-600">Predict changes</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Related Assets Modal */}
      {showRelatedModal && selectedAssetId && (
        <RelatedAssetsModal
          assetId={selectedAssetId}
          workspaceId={workspaceId}
          isOpen={showRelatedModal}
          onClose={() => setShowRelatedModal(false)}
        />
      )}
    </div>
  );
}