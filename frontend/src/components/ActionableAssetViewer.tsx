// frontend/src/components/ActionableAssetViewer.tsx - MODAL FOR VIEWING ASSET DETAILS

'use client';

import React, { useState } from 'react';
import { ActionableAsset } from '@/types';

interface ActionableAssetViewerProps {
  assetName: string;
  asset: ActionableAsset;
  onClose: () => void;
}

// Helper component to render different data types
const DataRenderer: React.FC<{ data: any; level?: number }> = ({ data, level = 0 }) => {
  const maxLevel = 3; // Prevent infinite nesting
  
  if (level > maxLevel) {
    return <span className="text-gray-500 italic">Dati troppo annidati...</span>;
  }

  if (data === null || data === undefined) {
    return <span className="text-gray-400">null</span>;
  }

  if (typeof data === 'boolean') {
    return <span className={data ? 'text-green-600' : 'text-red-600'}>{String(data)}</span>;
  }

  if (typeof data === 'number') {
    return <span className="text-blue-600">{data}</span>;
  }

  if (typeof data === 'string') {
    // Handle URLs
    if (data.startsWith('http')) {
      return (
        <a href={data} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
          {data.length > 50 ? `${data.slice(0, 50)}...` : data}
        </a>
      );
    }
    // Handle long strings
    if (data.length > 100) {
      return (
        <div>
          <p className="text-gray-800">{data.slice(0, 100)}...</p>
          <button 
            onClick={() => navigator.clipboard.writeText(data)}
            className="text-xs text-blue-600 hover:underline mt-1"
          >
            Copia testo completo
          </button>
        </div>
      );
    }
    return <span className="text-gray-800">{data}</span>;
  }

  if (Array.isArray(data)) {
    return (
      <div className="space-y-2">
        <div className="text-sm text-gray-600">Array con {data.length} elementi:</div>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {data.map((item, index) => (
            <div key={index} className="flex">
              <span className="text-gray-400 mr-2 min-w-[2rem]">[{index}]</span>
              <div className="flex-1">
                <DataRenderer data={item} level={level + 1} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data);
    return (
      <div className="space-y-2">
        <div className="text-sm text-gray-600">Oggetto con {entries.length} proprietà:</div>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {entries.map(([key, value]) => (
            <div key={key} className="bg-gray-50 p-2 rounded">
              <div className="flex">
                <span className="font-medium text-gray-700 mr-2 min-w-[100px]">{key}:</span>
                <div className="flex-1">
                  <DataRenderer data={value} level={level + 1} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return <span className="text-gray-500">Tipo sconosciuto</span>;
};

// Format file size helper
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default function ActionableAssetViewer({ assetName, asset, onClose }: ActionableAssetViewerProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'data' | 'technical' | 'usage'>('overview');
  const [searchTerm, setSearchTerm] = useState('');

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
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleDownload = (format: 'json' | 'csv' | 'txt') => {
    try {
      let content: string;
      let filename: string;
      let mimeType: string;

      switch (format) {
        case 'json':
          content = JSON.stringify(asset.asset_data, null, 2);
          filename = `${assetName}_${Date.now()}.json`;
          mimeType = 'application/json';
          break;
        case 'csv':
          // Simple CSV conversion for flat objects/arrays
          if (Array.isArray(asset.asset_data)) {
            const headers = Object.keys(asset.asset_data[0] || {});
            const csvContent = [
              headers.join(','),
              ...asset.asset_data.map((row: any) => 
                headers.map(header => JSON.stringify(row[header] || '')).join(',')
              )
            ].join('\n');
            content = csvContent;
          } else {
            // For objects, create key-value CSV
            content = Object.entries(asset.asset_data)
              .map(([key, value]) => `"${key}","${JSON.stringify(value)}"`)
              .join('\n');
          }
          filename = `${assetName}_${Date.now()}.csv`;
          mimeType = 'text/csv';
          break;
        case 'txt':
          content = JSON.stringify(asset.asset_data, null, 2);
          filename = `${assetName}_${Date.now()}.txt`;
          mimeType = 'text/plain';
          break;
        default:
          return;
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading asset:', error);
      alert('Errore durante il download');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copiato negli appunti!');
    }).catch(err => {
      console.error('Errore nella copia:', err);
    });
  };

  // Filter data based on search term
  const filteredData = React.useMemo(() => {
    if (!searchTerm) return asset.asset_data;
    
    const search = searchTerm.toLowerCase();
    if (Array.isArray(asset.asset_data)) {
      return asset.asset_data.filter((item: any) => 
        JSON.stringify(item).toLowerCase().includes(search)
      );
    } else if (typeof asset.asset_data === 'object') {
      const filtered: any = {};
      Object.entries(asset.asset_data).forEach(([key, value]) => {
        if (key.toLowerCase().includes(search) || 
            JSON.stringify(value).toLowerCase().includes(search)) {
          filtered[key] = value;
        }
      });
      return filtered;
    }
    return asset.asset_data;
  }, [asset.asset_data, searchTerm]);

  const dataSize = new Blob([JSON.stringify(asset.asset_data)]).size;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <div className="flex items-center">
            <span className="text-3xl mr-4">{getAssetIcon(assetName)}</span>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {assetName.replace(/_/g, ' ').toUpperCase()}
              </h2>
              <p className="text-gray-600">Asset azionabile pronto per l'uso</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold p-2"
          >
            ×
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', label: '👀 Panoramica', icon: '👀' },
              { id: 'data', label: '📊 Dati', icon: '📊' },
              { id: 'technical', label: '🔧 Tecnico', icon: '🔧' },
              { id: 'usage', label: '📖 Utilizzo', icon: '📖' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Asset Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-green-800">Azionabilità</h3>
                    <span className="text-2xl">🚀</span>
                  </div>
                  <div className={`text-3xl font-bold ${getActionabilityColor(asset.actionability_score)}`}>
                    {Math.round(asset.actionability_score * 100)}%
                  </div>
                  <p className="text-sm text-green-600 mt-2">
                    {asset.ready_to_use ? 'Pronto all\'uso immediato' : 'Richiede personalizzazione'}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-blue-800">Validazione</h3>
                    <span className="text-2xl">✅</span>
                  </div>
                  <div className="text-3xl font-bold text-blue-600">
                    {Math.round(asset.validation_score * 100)}%
                  </div>
                  <p className="text-sm text-blue-600 mt-2">
                    Qualità e completezza dei dati
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-purple-800">Dimensione</h3>
                    <span className="text-2xl">📦</span>
                  </div>
                  <div className="text-3xl font-bold text-purple-600">
                    {formatFileSize(dataSize)}
                  </div>
                  <p className="text-sm text-purple-600 mt-2">
                    {Object.keys(asset.asset_data).length} campi principali
                  </p>
                </div>
              </div>

              {/* Asset Info */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-4">Informazioni Asset</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm font-medium text-gray-600">Metodo Estrazione:</span>
                    <p className="text-gray-800">{asset.extraction_method}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-600">Task Origine:</span>
                    <p className="text-gray-800 font-mono text-sm">{asset.source_task_id}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-600">Stato:</span>
                    <p className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                      asset.ready_to_use 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {asset.ready_to_use ? '✅ Pronto' : '🔧 In lavorazione'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="space-y-6">
              {/* Search */}
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Cerca nei dati..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(filteredData, null, 2))}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                >
                  📋 Copia
                </button>
              </div>

              {/* Data Display */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <DataRenderer data={filteredData} />
              </div>
            </div>
          )}

          {activeTab === 'technical' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Metrics */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-800 mb-4">Metriche Tecniche</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Score Azionabilità:</span>
                      <span className="font-medium">{asset.actionability_score.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Score Validazione:</span>
                      <span className="font-medium">{asset.validation_score.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Dimensione Dati:</span>
                      <span className="font-medium">{formatFileSize(dataSize)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tipo Dati:</span>
                      <span className="font-medium">
                        {Array.isArray(asset.asset_data) ? 'Array' : 'Object'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Asset Schema */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-800 mb-4">Schema Dati</h3>
                  <div className="space-y-2 text-sm">
                    {Object.keys(asset.asset_data).slice(0, 10).map(key => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span className="font-medium text-xs bg-gray-200 px-2 py-1 rounded">
                          {typeof asset.asset_data[key]}
                        </span>
                      </div>
                    ))}
                    {Object.keys(asset.asset_data).length > 10 && (
                      <p className="text-xs text-gray-500">
                        +{Object.keys(asset.asset_data).length - 10} altri campi...
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* JSON Raw Data */}
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-white">Dati JSON Grezzi</h3>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(asset.asset_data, null, 2))}
                    className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 text-sm"
                  >
                    Copia JSON
                  </button>
                </div>
                <pre className="text-green-400 text-sm overflow-auto max-h-64 bg-gray-800 p-4 rounded">
                  {JSON.stringify(asset.asset_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'usage' && (
            <div className="space-y-6">
              {/* Usage Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-semibold text-blue-800 mb-4">🚀 Come Utilizzare questo Asset</h3>
                <div className="space-y-3 text-blue-700">
                  <p>
                    <strong>Tipo Asset:</strong> {assetName.replace(/_/g, ' ').toLowerCase()}
                  </p>
                  <p>
                    <strong>Stato:</strong> {asset.ready_to_use ? 'Pronto per utilizzo immediato' : 'Richiede personalizzazione'}
                  </p>
                  <p>
                    <strong>Azionabilità:</strong> {Math.round(asset.actionability_score * 100)}% - 
                    {asset.actionability_score >= 0.8 ? ' Può essere utilizzato così com\'è' :
                     asset.actionability_score >= 0.6 ? ' Richiede alcune modifiche' :
                     ' Template di base, personalizzazione necessaria'}
                  </p>
                </div>
              </div>

              {/* Suggested Next Steps */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="font-semibold text-green-800 mb-4">✅ Prossimi Passi Suggeriti</h3>
                <ol className="list-decimal list-inside space-y-2 text-green-700">
                  <li>Scarica l'asset nel formato preferito (JSON, CSV, TXT)</li>
                  <li>Importa i dati nel tuo sistema o strumento di lavoro</li>
                  {!asset.ready_to_use && (
                    <li>Personalizza i dati secondo le tue esigenze specifiche</li>
                  )}
                  <li>Testa l'asset con un piccolo campione prima dell'uso completo</li>
                  <li>Implementa nell'ambiente di produzione</li>
                  <li>Monitora le performance e ottimizza se necessario</li>
                </ol>
              </div>

              {/* Download Options */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-4">📥 Opzioni di Download</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => handleDownload('json')}
                    className="p-4 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition text-center"
                  >
                    <div className="text-2xl mb-2">📄</div>
                    <div className="font-medium">JSON</div>
                    <div className="text-sm text-gray-600">Formato strutturato</div>
                  </button>
                  <button
                    onClick={() => handleDownload('csv')}
                    className="p-4 bg-white border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition text-center"
                  >
                    <div className="text-2xl mb-2">📊</div>
                    <div className="font-medium">CSV</div>
                    <div className="text-sm text-gray-600">Per Excel/fogli di calcolo</div>
                  </button>
                  <button
                    onClick={() => handleDownload('txt')}
                    className="p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition text-center"
                  >
                    <div className="text-2xl mb-2">📝</div>
                    <div className="font-medium">TXT</div>
                    <div className="text-sm text-gray-600">Testo semplice</div>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Asset estratto da task: <span className="font-mono">{asset.source_task_id}</span>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
            >
              Chiudi
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}