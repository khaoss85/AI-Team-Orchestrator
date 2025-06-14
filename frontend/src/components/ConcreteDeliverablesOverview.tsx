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

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'contact_database': return '👥'
      case 'email_templates': return '📬'
      case 'content_calendar': return '📅'
      case 'content_strategy': return '🎯'
      case 'audience_research': return '🔍'
      case 'growth_strategy': return '📈'
      case 'automation_guide': return '⚙️'
      case 'engagement_playbook': return '💬'
      default: return '📦'
    }
  }

  const getAssetTypeLabel = (type: string) => {
    switch (type) {
      case 'contact_database': return 'Database Contatti'
      case 'email_templates': return 'Template Email'
      case 'content_calendar': return 'Calendario Editoriale'
      case 'content_strategy': return 'Strategia Contenuti'
      case 'audience_research': return 'Ricerca Audience'
      case 'growth_strategy': return 'Strategia Crescita'
      case 'automation_guide': return 'Guida Automazione'
      case 'engagement_playbook': return 'Playbook Engagement'
      default: return type.replace('_', ' ')
    }
  }

  const renderAssetCard = (asset: any) => (
    <div
      key={asset.id}
      className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6"
    >
      <div className="flex items-start space-x-4">
        <div className="text-3xl">{getAssetIcon(asset.type)}</div>
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
          
          <p className="text-sm text-gray-600 mb-3">
            {getAssetTypeLabel(asset.type)}
          </p>
          
          {asset.quality_scores?.overall && (
            <div className="mb-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Qualità</span>
                <span className="font-medium text-gray-900">
                  {Math.round(asset.quality_scores.overall * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${asset.quality_scores.overall * 100}%` }}
                />
              </div>
            </div>
          )}
          
          <div className="flex space-x-2">
            <button
              onClick={() => onViewAsset(asset)}
              className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Visualizza
            </button>
            <button
              onClick={() => onDownloadAsset(asset)}
              className="px-3 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              ⬇️
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderDeliverableCard = (deliverable: any) => (
    <div
      key={deliverable.id}
      className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200 shadow-sm p-6"
    >
      <div className="flex items-start space-x-4">
        <div className="text-3xl">🎯</div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Deliverable Finale
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {deliverable.achievement_rate || 'N/A'}
              </div>
              <div className="text-sm text-green-700">Achievement Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {deliverable.concrete_assets?.length || 0}
              </div>
              <div className="text-sm text-blue-700">Asset Concreti</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {deliverable.quality_metrics?.average_task_quality ? 
                  Math.round(deliverable.quality_metrics.average_task_quality * 100) + '%' : 'N/A'}
              </div>
              <div className="text-sm text-purple-700">Qualità Media</div>
            </div>
          </div>
          
          {deliverable.business_impact && (
            <div className="bg-white rounded-lg p-4 mb-4">
              <h4 className="font-medium text-gray-900 mb-2">💼 Impatto Business</h4>
              <p className="text-sm text-gray-700 mb-2">
                <strong>Uso Immediato:</strong> {deliverable.business_impact.immediate_use}
              </p>
              <p className="text-sm text-gray-700 mb-2">
                <strong>Risultati Previsti:</strong> {deliverable.business_impact.projected_results}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Tempo Implementazione:</strong> {deliverable.business_impact.implementation_time}
              </p>
            </div>
          )}
          
          {deliverable.next_actions && deliverable.next_actions.length > 0 && (
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">🚀 Prossimi Passi</h4>
              <ul className="space-y-1">
                {deliverable.next_actions.map((action: string, index: number) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-green-600 mr-2 mt-0.5">•</span>
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Risultati Concreti</h2>
            <p className="text-gray-600">Asset e deliverable pronti per l'uso immediato</p>
          </div>
          <Link
            href={`/projects/${workspaceId}/assets`}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center"
          >
            Gestisci Asset
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      <div className="p-6">
        {activeTab === 'deliverables' && (
          <div className="space-y-6">
            {finalDeliverables.length > 0 ? (
              finalDeliverables.map(deliverable => renderDeliverableCard(deliverable))
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
                  {readyAssets.map(asset => renderAssetCard(asset))}
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

            {inProgressAssets.length > 0 && readyAssets.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  ⏳ In Elaborazione ({inProgressAssets.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {inProgressAssets.slice(0, 4).map(asset => (
                    <div
                      key={asset.id}
                      className="bg-gray-50 rounded-lg border border-gray-200 p-6 opacity-75"
                    >
                      <div className="flex items-start space-x-4">
                        <div className="text-3xl opacity-50">{getAssetIcon(asset.type)}</div>
                        <div className="flex-1">
                          <h4 className="text-lg font-medium text-gray-700 mb-2">
                            {asset.name}
                          </h4>
                          <p className="text-sm text-gray-500 mb-3">
                            {getAssetTypeLabel(asset.type)}
                          </p>
                          <div className="flex items-center text-sm text-blue-600">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                            In elaborazione...
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {inProgressAssets.length > 4 && (
                  <p className="text-center text-sm text-gray-500 mt-4">
                    + altri {inProgressAssets.length - 4} asset in elaborazione
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