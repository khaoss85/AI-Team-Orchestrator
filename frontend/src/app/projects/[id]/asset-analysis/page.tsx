// frontend/src/app/projects/[id]/asset-analysis/page.tsx - ASSET ANALYSIS PAGE

'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { useAssetManagement } from '@/hooks/useAssetManagement';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function AssetAnalysisPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const {
    requirements,
    schemas,
    extractionStatus,
    getAssetCompletionStats,
    loading,
    error,
    refresh
  } = useAssetManagement(id);

  const [triggeringAnalysis, setTriggeringAnalysis] = useState(false);

  const assetStats = getAssetCompletionStats();

  const handleTriggerAnalysis = async () => {
    try {
      setTriggeringAnalysis(true);
      await api.projects.triggerAssetAnalysis(id);
      setTimeout(() => {
        refresh();
      }, 2000);
    } catch (error) {
      console.error('Error triggering analysis:', error);
    } finally {
      setTriggeringAnalysis(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm">
          ← Torna al progetto
        </Link>
        <div className="flex justify-between items-center mt-2">
          <div>
            <h1 className="text-2xl font-semibold">Analisi Asset Avanzata</h1>
            <p className="text-gray-600">Analisi dettagliata di requirements, schemi e produzione asset</p>
          </div>
          <button
            onClick={handleTriggerAnalysis}
            disabled={triggeringAnalysis}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {triggeringAnalysis ? 'Analisi in corso...' : '🔄 Aggiorna Analisi'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      {/* Asset Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Asset Totali</p>
              <p className="text-2xl font-bold text-blue-600">{assetStats.totalAssets}</p>
            </div>
            <div className="text-blue-500 text-2xl">📦</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Completati</p>
              <p className="text-2xl font-bold text-green-600">{assetStats.completedAssets}</p>
            </div>
            <div className="text-green-500 text-2xl">✅</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Tasso Completamento</p>
              <p className="text-2xl font-bold text-purple-600">{Math.round(assetStats.completionRate)}%</p>
            </div>
            <div className="text-purple-500 text-2xl">📈</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Deliverable Ready</p>
              <p className="text-2xl font-bold text-orange-600">
                {assetStats.isDeliverableReady ? 'Sì' : 'No'}
              </p>
            </div>
            <div className="text-orange-500 text-2xl">
              {assetStats.isDeliverableReady ? '🎯' : '⏳'}
            </div>
          </div>
        </div>
      </div>

      {/* Requirements Analysis */}
      {requirements && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8 border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">📋 Analisi Requirements</h2>
          
          <div className="mb-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h3 className="font-medium text-blue-800 mb-2">
                Categoria Deliverable: {requirements.deliverable_category}
              </h3>
              <p className="text-blue-700 text-sm">
                Asset primari richiesti: {requirements.primary_assets_needed.length}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {requirements.primary_assets_needed.map((req, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium capitalize">
                    {req.asset_type.replace(/_/g, ' ')}
                  </h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    req.priority === 1 ? 'bg-red-100 text-red-800' :
                    req.priority === 2 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    P{req.priority}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">Formato:</span>
                    <span className="ml-2">{req.asset_format.replace(/_/g, ' ')}</span>
                  </div>
                  <div>
                    <span className="font-medium">Azionabilità:</span>
                    <span className="ml-2">{req.actionability_level.replace(/_/g, ' ')}</span>
                  </div>
                  <div>
                    <span className="font-medium">Impatto:</span>
                    <span className="ml-2">{req.business_impact}</span>
                  </div>
                </div>

                {req.validation_criteria.length > 0 && (
                  <div className="mt-3">
                    <span className="text-xs font-medium text-gray-600">Criteri validazione:</span>
                    <ul className="mt-1 text-xs text-gray-600">
                      {req.validation_criteria.map((criterion, idx) => (
                        <li key={idx} className="flex items-center">
                          <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                          {criterion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Asset Schemas */}
      {Object.keys(schemas).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8 border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">📐 Schemi Asset Disponibili</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(schemas).map(([name, schema]) => (
              <div key={name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium capitalize">{name.replace(/_/g, ' ')}</h3>
                  {schema.automation_ready && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                      🤖 Auto-ready
                    </span>
                  )}
                </div>

                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Struttura Schema:</h4>
                    <div className="bg-gray-50 p-3 rounded text-xs">
                      <pre className="whitespace-pre-wrap overflow-auto max-h-32">
                        {JSON.stringify(schema.schema_definition, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {schema.validation_rules.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Regole Validazione:</h4>
                      <ul className="text-xs text-gray-600">
                        {schema.validation_rules.map((rule, idx) => (
                          <li key={idx} className="flex items-center">
                            <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                            {rule}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Istruzioni Uso:</h4>
                    <p className="text-xs text-gray-600">{schema.usage_instructions}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extraction Status */}
      {extractionStatus && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">🔬 Stato Estrazione Asset</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800">Task Completati</h3>
              <p className="text-2xl font-bold text-blue-900">
                {extractionStatus.extraction_summary.total_completed_tasks}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="font-medium text-purple-800">Asset Production Tasks</h3>
              <p className="text-2xl font-bold text-purple-900">
                {extractionStatus.extraction_summary.asset_production_tasks}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-800">Pronti per Estrazione</h3>
              <p className="text-2xl font-bold text-green-900">
                {extractionStatus.extraction_summary.extraction_ready_tasks}
              </p>
            </div>
          </div>

          {extractionStatus.extraction_candidates.length > 0 && (
            <div>
              <h3 className="font-medium mb-3">Candidati per Estrazione:</h3>
              <div className="space-y-3">
                {extractionStatus.extraction_candidates.map((candidate, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <h4 className="font-medium">{candidate.task_name}</h4>
                      <p className="text-sm text-gray-600">
                        Task ID: {candidate.task_id.substring(0, 8)}...
                        {candidate.asset_type && ` • Tipo: ${candidate.asset_type}`}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {candidate.has_structured_output && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                          ✅ Strutturato
                        </span>
                      )}
                      {candidate.extraction_ready && (
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                          🚀 Pronto
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {extractionStatus.next_steps.length > 0 && (
            <div className="mt-6">
              <h3 className="font-medium mb-3">Prossimi Passi:</h3>
              <ul className="space-y-2">
                {extractionStatus.next_steps.map((step, index) => (
                  <li key={index} className="flex items-center text-sm">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* No Data State */}
      {!requirements && !Object.keys(schemas).length && !extractionStatus && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
          <div className="text-6xl mb-4">🔬</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nessuna Analisi Asset Disponibile</h3>
          <p className="text-gray-500 mb-6">
            L'analisi degli asset viene generata automaticamente durante l'esecuzione del progetto
          </p>
          <button
            onClick={handleTriggerAnalysis}
            disabled={triggeringAnalysis}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {triggeringAnalysis ? 'Analisi in corso...' : '🔍 Avvia Analisi Asset'}
          </button>
        </div>
      )}
    </div>
  );
}