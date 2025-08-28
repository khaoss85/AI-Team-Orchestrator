'use client'

import React, { useState } from 'react'
import Link from 'next/link'

interface ConcreteDeliverablesOverviewProps {
  workspaceId: string
  finalDeliverables: any[]
  assets: any[]
  onViewAsset: (asset: any) => void
  onDownloadAsset: (asset: any) => void
}

const ConcreteDeliverablesOverview: React.FC<ConcreteDeliverablesOverviewProps> = ({
  workspaceId,
  finalDeliverables,
  assets,
  onViewAsset,
  onDownloadAsset
}) => {
  const [activeTab, setActiveTab] = useState<'deliverables' | 'assets'>('deliverables')

  // Get ready-to-use assets
  const readyAssets = assets.filter(asset => asset.ready_to_use)
  const inProgressAssets = assets.filter(asset => !asset.ready_to_use)

  return (
    <div className="relative">
      {/* Eye-catching Banner */}
      <div className="bg-gradient-to-r from-green-500 to-blue-600 p-1 rounded-t-lg">
        <div className="bg-white rounded-t-lg">
          {/* Header */}
          <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-t-lg">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-4xl animate-pulse">🎯</span>
                  <h2 className="text-3xl font-bold text-gray-900">Risultati Concreti</h2>
                </div>
                <p className="text-lg text-gray-700 font-medium">
                  {readyAssets.length} asset pronti • {finalDeliverables.length} deliverable finali
                </p>
              </div>
              <Link
                href={`/projects/${workspaceId}/conversation`}
                className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-blue-800 transition-all transform hover:scale-105 flex items-center shadow-lg"
              >
                Chat AI
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="text-xl font-bold text-green-700">{readyAssets.length}</div>
                <div className="text-sm text-green-600">Pronti all'Uso</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-xl font-bold text-blue-700">{inProgressAssets.length}</div>
                <div className="text-sm text-blue-600">In Elaborazione</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg border border-purple-200">
                <div className="text-xl font-bold text-purple-700">{finalDeliverables.length}</div>
                <div className="text-sm text-purple-600">Deliverable Finali</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-xl font-bold text-gray-700">{assets.length}</div>
                <div className="text-sm text-gray-600">Asset Totali</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('deliverables')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'deliverables'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🎯 Deliverable Finali ({finalDeliverables.length})
          </button>
          <button
            onClick={() => setActiveTab('assets')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'assets'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            📦 Asset Pronti ({readyAssets.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 bg-white rounded-b-lg">
        {activeTab === 'deliverables' && (
          <div className="space-y-6">
            {finalDeliverables.length > 0 ? (
              finalDeliverables.map(deliverable => (
                <div key={deliverable.id} className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200 shadow-sm p-6">
                  <div className="flex items-start space-x-4">
                    <div className="text-3xl">🎯</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Deliverable Finale</h3>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Nessun deliverable finale ancora disponibile
                </h3>
                <p className="text-gray-600 mb-6">
                  I deliverable finali vengono generati quando il progetto raggiunge una soglia di completamento sufficientemente alta.
                </p>
                {readyAssets.length > 0 && (
                  <button
                    onClick={() => setActiveTab('assets')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Visualizza Asset Pronti ({readyAssets.length})
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'assets' && (
          <div className="space-y-6">
            {readyAssets.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  ✅ Asset Pronti all'Uso ({readyAssets.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {readyAssets.map(asset => (
                    <div
                      key={asset.id}
                      className="relative bg-white rounded-lg border-2 border-green-200 shadow-md hover:shadow-xl transition-all transform hover:scale-105 p-6 hover:border-green-400"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="text-3xl">📦</div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {asset.name}
                            </h3>
                            {asset.ready_to_use && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                ✅ Pronto all'uso
                              </span>
                            )}
                          </div>
                          
                          <div className="flex space-x-2">
                            <button
                              onClick={() => onViewAsset(asset)}
                              className="flex-1 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2.5 rounded-lg font-medium hover:from-green-600 hover:to-green-700 transition-all transform hover:scale-105 shadow-md"
                            >
                              👁️ Visualizza
                            </button>
                            <button
                              onClick={() => onDownloadAsset(asset)}
                              className="px-3 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm"
                            >
                              ⬇️
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Nessun asset pronto all'uso
                </h3>
                <p className="text-gray-600 mb-6">
                  Gli asset vengono elaborati dal team AI e diventano disponibili quando completati e validati.
                </p>
                {inProgressAssets.length > 0 && (
                  <p className="text-sm text-blue-600">
                    {inProgressAssets.length} asset in elaborazione...
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConcreteDeliverablesOverview