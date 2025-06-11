'use client';

import React, { useState, use } from 'react';
// Using real unified assets API
import { useUnifiedAssets } from '@/hooks/useUnifiedAssets';
import { AssetHistoryPanel } from '@/components/assets/AssetHistoryPanel';
import { RelatedAssetsModal } from '@/components/assets/RelatedAssetsModal';
import { DependencyGraph } from '@/components/assets/DependencyGraph';
import { AIImpactPredictor } from '@/components/assets/AIImpactPredictor';
import HumanFeedbackDashboard from '@/components/HumanFeedbackDashboard';
import GenericArrayViewer from '@/components/GenericArrayViewer';
import StructuredContentRenderer from '@/components/StructuredContentRenderer';
import StructuredAssetRenderer from '@/components/StructuredAssetRenderer';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectAssetsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const workspaceId = params.id;
  
  // Use the new unified assets hook
  const {
    assets,
    assetsMap,
    loading,
    error,
    workspaceGoal,
    assetCount,
    totalVersions,
    refresh
  } = useUnifiedAssets(workspaceId);

  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [assetViewTab, setAssetViewTab] = useState<'content' | 'history' | 'dependencies' | 'impact' | 'feedback'>('content');
  const [showRelatedModal, setShowRelatedModal] = useState(false);
  const [showRawData, setShowRawData] = useState(false);

  // Handle asset selection
  const handleAssetSelect = (assetId: string) => {
    setSelectedAssetId(assetId);
    const asset = assetsMap[assetId];
    setSelectedAsset(asset);
    
    console.log('🔍 [Asset Selection] Selected asset:', {
      assetId,
      assetName: asset?.name,
      assetVersions: asset?.versions,
      hasContent: !!asset?.content,
      contentType: asset?.content?.enhancement_source,
      hasStructuredContent: !!asset?.content?.structured_content,
      hasRenderedHtml: !!asset?.content?.rendered_html
    });
  };

  // HTML sanitization helper
  const sanitizeHTML = (html: string): string => {
    if (!html) return '';
    
    let sanitized = html
      .replace(/<script[^>]*>.*?<\/script>/gis, '')
      .replace(/on\w+="[^"]*"/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\')
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
      .replace(/\\r/g, '\r')
      .replace(/\\{2,}/g, '\\')
      .replace(/\s+\\/g, ' ')
      .replace(/\\\s+/g, ' ')
      .trim();
    
    return sanitized;
  };

  // Render structured content helper
  const renderStructuredContent = (content: any) => {
    if (!content) return null;

    if (typeof content === 'string') {
      if (content.includes('<') && content.includes('>')) {
        return (
          <div 
            className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200"
            dangerouslySetInnerHTML={{ __html: sanitizeHTML(content) }}
          />
        );
      }
      return (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {content}
          </div>
        </div>
      );
    }

    const arrayFields = Object.entries(content).filter(([key, value]) => 
      Array.isArray(value) && value.length > 0 && typeof value[0] === 'object'
    );
    
    if (arrayFields.length > 0) {
      const [fieldName, fieldData] = arrayFields[0];
      const additionalData = Object.fromEntries(
        Object.entries(content).filter(([key, value]) => !Array.isArray(value))
      );
      
      return (
        <GenericArrayViewer 
          items={fieldData} 
          fieldName={fieldName}
          additionalData={additionalData}
          assetName={selectedAsset?.name || 'Content Collection'}
        />
      );
    }

    return (
      <div className="space-y-6">
        {Object.keys(content).map(key => {
          const value = content[key];
          if (typeof value === 'string') {
            return (
              <div key={key} className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-3 capitalize text-lg">
                  {key.replace(/_/g, ' ')}
                </h4>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {value}
                </div>
              </div>
            );
          } else if (typeof value === 'object' && value !== null) {
            const entries = Object.entries(value);
            const isSimpleObject = entries.length <= 10 && entries.every(([k, v]) => 
              typeof k === 'string' && (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
            );
            
            return (
              <div key={key} className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-3 capitalize text-lg">
                  {key.replace(/_/g, ' ')}
                </h4>
                {isSimpleObject ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {entries.map(([k, v], idx) => (
                      <div key={idx} className="flex justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-600 font-medium">{k.replace(/_/g, ' ')}:</span>
                        <span className="text-gray-900">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          }
          return null;
        })}
      </div>
    );
  };

  const assetViewTabs = [
    { id: 'content', label: 'Content', icon: '📄', description: 'AI-enhanced view' },
    { id: 'history', label: 'Version History', icon: '📜', description: 'Cronologia modifiche' },
    { id: 'dependencies', label: 'Dependencies', icon: '🕸️', description: 'Relazioni asset' },
    { id: 'impact', label: 'Impact Analysis', icon: '🎯', description: 'Predizioni AI' },
    { id: 'feedback', label: 'Feedback', icon: '💬', description: 'Asset-specific feedback' }
  ];

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'contact_database': return '👥';
      case 'email_templates': return '📬';
      case 'content_calendar': return '📅';
      case 'content_strategy': return '🎯';
      case 'email_campaign': return '📧';
      case 'analysis_report': return '📊';
      case 'analysis': return '📊';
      case 'report': return '📄';
      case 'spreadsheet': return '📈';
      case 'document': return '📝';
      case 'strategy': return '🎯';
      case 'calendar': return '📅';
      case 'guidelines': return '📋';
      case 'presentation': return '🎤';
      case 'database': return '🗃️';
      default: return '📦';
    }
  };

  const getVersionBadgeColor = (count: number) => {
    if (count >= 5) return 'bg-red-100 text-red-800';
    if (count >= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Project Assets</h1>
              <p className="text-gray-600 mt-1">
                Unified asset management with AI content processing, versioning, and business-ready deliverables
              </p>
              {workspaceGoal && (
                <p className="text-sm text-blue-600 mt-2">
                  🎯 Goal: {workspaceGoal}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{assetCount}</div>
                <div className="text-sm text-gray-500">Assets</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{totalVersions}</div>
                <div className="text-sm text-gray-500">Total Versions</div>
              </div>
              <button
                onClick={refresh}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                disabled={loading}
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>

          <div className="border-b border-gray-200">
            <div className="flex items-center space-x-2 py-4">
              <span className="text-lg">🔧</span>
              <span className="font-medium text-blue-600">Unified Assets</span>
              <span className="text-xs text-gray-400">Powered by ConcreteAssetExtractor</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <span className="text-red-600 text-sm font-medium">Error: {error}</span>
              <button
                onClick={refresh}
                className="ml-4 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Asset List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Project Assets</h2>
                <p className="text-sm text-gray-600">Select an asset to analyze</p>
              </div>
              
              <div className="p-6">
                {loading ? (
                  <div className="animate-pulse space-y-3">
                    {[1, 2, 3, 4].map(i => (
                      <div key={i} className="h-16 bg-gray-100 rounded"></div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {assets.map((asset) => (
                      <div
                        key={asset.id}
                        onClick={() => handleAssetSelect(asset.id)}
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
                              {asset.type.replace('_', ' ')}
                              {asset.ready_to_use && (
                                <span className="ml-2 text-xs text-green-600 font-medium">• Ready to use</span>
                              )}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              Modified: {new Date(asset.lastModified).toLocaleDateString()}
                            </p>
                            {asset.ready_to_use && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                                Ready to use
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {!loading && !error && assets.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    <div className="text-6xl mb-6">🚀</div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-3">No Assets Available Yet</h3>
                    <p className="text-gray-600 mb-6 max-w-md mx-auto">
                      This workspace doesn't have any completed tasks yet. 
                      Start your AI team to begin generating actionable assets.
                    </p>
                    <div className="space-y-4">
                      <button 
                        onClick={() => window.location.href = `/projects/${workspaceId}/team`}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                      >
                        🎯 Launch AI Team
                      </button>
                      <div className="text-sm text-gray-500">
                        <p>Or go to <a href={`/projects/${workspaceId}/tasks`} className="text-blue-600 hover:underline">Tasks</a> to monitor progress</p>
                      </div>
                    </div>
                    {/* Debug info */}
                    <div className="mt-8 text-xs text-gray-400">
                      Workspace ID: {workspaceId} | Asset Count: {assetCount}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Asset Analysis Panel */}
          <div className="lg:col-span-2">
            {selectedAssetId && selectedAsset ? (
              <div className="space-y-6">
                {/* Selected Asset Info */}
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <span className="text-3xl">{getAssetIcon(selectedAsset.type)}</span>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">
                        {selectedAsset.name}
                      </h2>
                      <p className="text-sm text-gray-600">
                        {selectedAsset.type.replace('_', ' ')} • {selectedAsset.versions} versions available
                      </p>
                      {selectedAsset.quality_scores?.overall && (
                        <p className="text-sm text-green-600">
                          Quality Score: {Math.round(selectedAsset.quality_scores.overall * 100)}%
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Asset View Tabs */}
                  <div className="border-b border-gray-200 mb-6">
                    <div className="flex space-x-6">
                      {assetViewTabs.map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setAssetViewTab(tab.id as any)}
                          className={`flex items-center space-x-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                            assetViewTab === tab.id
                              ? 'border-blue-500 text-blue-600'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <span className="text-lg">{tab.icon}</span>
                          <span>{tab.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Asset Analysis Content */}
                <div className="space-y-6">
                  {assetViewTab === 'content' && (
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                      <div className="p-6">
                        {/* Pre-rendered HTML */}
                        {selectedAsset.content?.rendered_html && (
                          <div className="mb-6">
                            <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
                              <h3 className="text-lg font-semibold text-green-800 mb-2">⚡ AI-Enhanced Content</h3>
                              <p className="text-green-700 text-sm">Pre-formatted and ready for immediate use</p>
                            </div>
                            <div 
                              className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200 ai-enhanced-content"
                              dangerouslySetInnerHTML={{ __html: sanitizeHTML(selectedAsset.content.rendered_html) }}
                            />
                          </div>
                        )}

                        {/* Markup Elements */}
                        {selectedAsset.content?.markup_elements && (
                          <div className="mb-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900">📊 Structured Elements</h3>
                            <StructuredContentRenderer 
                              elements={selectedAsset.content.markup_elements}
                              rawData={selectedAsset.content.structured_content}
                            />
                          </div>
                        )}
                        
                        {/* Structured Content */}
                        {!selectedAsset.content?.rendered_html && !selectedAsset.content?.markup_elements && selectedAsset.content?.structured_content && (
                          <div className="mb-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900">📄 Content</h3>
                            {selectedAsset.content.structured_content.tables || 
                             selectedAsset.content.structured_content.cards || 
                             selectedAsset.content.structured_content.metrics || 
                             selectedAsset.content.structured_content.timelines ? (
                              <StructuredAssetRenderer 
                                data={selectedAsset.content.structured_content}
                              />
                            ) : (
                              renderStructuredContent(selectedAsset.content.structured_content)
                            )}
                          </div>
                        )}
                        
                        {/* Raw Data Toggle */}
                        {selectedAsset.content?.structured_content && (
                          <div className="mt-6 pt-6 border-t border-gray-200">
                            <button
                              onClick={() => setShowRawData(!showRawData)}
                              className="flex items-center text-sm text-gray-600 hover:text-gray-800 mb-2"
                            >
                              <svg className={`w-4 h-4 mr-1 transform transition-transform ${showRawData ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              Raw JSON Data
                            </button>
                            {showRawData && (
                              <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto max-h-60 overflow-y-auto">
                                {JSON.stringify(selectedAsset.content.structured_content, null, 2)}
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {assetViewTab === 'history' && (
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                      <div className="p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Version History</h3>
                        <div className="space-y-4">
                          {selectedAsset.version_history?.map((version: any, index: number) => (
                            <div key={version.version} className={`p-4 rounded-lg border ${index === 0 ? 'border-green-200 bg-green-50' : 'border-gray-200'}`}>
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <span className="font-semibold text-gray-900">{version.version}</span>
                                  {index === 0 && (
                                    <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                      Current
                                    </span>
                                  )}
                                </div>
                                <span className="text-sm text-gray-500">
                                  {new Date(version.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mb-1">{version.changes_summary}</p>
                              <p className="text-xs text-gray-500">By {version.created_by}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {assetViewTab === 'dependencies' && (
                    <div className="space-y-6">
                      <DependencyGraph 
                        nodes={[
                          {
                            id: selectedAsset.id,
                            name: selectedAsset.name,
                            type: selectedAsset.type,
                            category: 'strategy',
                            status: 'current',
                            last_updated: selectedAsset.lastModified,
                            size: 'medium',
                            business_value: selectedAsset.quality_scores?.overall ? Math.round(selectedAsset.quality_scores.overall * 100) : 85
                          }
                        ]}
                        edges={[]}
                        centralNodeId={selectedAsset.id}
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

                  {assetViewTab === 'impact' && (
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

                  {assetViewTab === 'feedback' && (
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                      <div className="p-6 border-b border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          Asset Feedback: {selectedAsset.name}
                        </h3>
                        <p className="text-gray-600 text-sm">
                          Provide feedback specific to this asset and its related tasks
                        </p>
                      </div>
                      <div className="p-6">
                        <HumanFeedbackDashboard 
                          workspaceId={workspaceId}
                          assetContext={{
                            assetId: selectedAsset.id,
                            assetName: selectedAsset.name,
                            sourceTaskId: selectedAsset.sourceTaskId
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
                <div className="text-6xl mb-4">🔧</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select an Asset to Analyze
                </h3>
                <p className="text-gray-600 mb-6">
                  Choose an asset to view its AI-enhanced content, version history, dependencies, impact analysis, and provide feedback
                </p>
                
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 max-w-3xl mx-auto">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl mb-2">📄</div>
                    <div className="text-sm font-medium text-blue-900">Content</div>
                    <div className="text-xs text-blue-600">AI-enhanced view</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl mb-2">📜</div>
                    <div className="text-sm font-medium text-green-900">History</div>
                    <div className="text-xs text-green-600">Track changes</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl mb-2">🕸️</div>
                    <div className="text-sm font-medium text-purple-900">Dependencies</div>
                    <div className="text-xs text-purple-600">Relationships</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-2xl mb-2">🎯</div>
                    <div className="text-sm font-medium text-orange-900">Impact</div>
                    <div className="text-xs text-orange-600">AI predictions</div>
                  </div>
                  <div className="text-center p-4 bg-pink-50 rounded-lg">
                    <div className="text-2xl mb-2">💬</div>
                    <div className="text-sm font-medium text-pink-900">Feedback</div>
                    <div className="text-xs text-pink-600">Asset-specific</div>
                  </div>
                </div>
              </div>
            )}
          </div>
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