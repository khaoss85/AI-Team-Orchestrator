'use client';

import React, { useState } from 'react';
import { useAssetDependencies } from '@/hooks/useAssetDependencies';
import { useRealTimeAssets } from '@/hooks/useRealTimeAssets';
import { RelatedAssetsModal } from './RelatedAssetsModal';
import { AssetHistoryPanel } from './AssetHistoryPanel';
import { DependencyGraph } from './DependencyGraph';
import { AIImpactPredictor } from './AIImpactPredictor';
import { SmartNotificationCenter } from './SmartNotificationCenter';
import { WorkflowAutomationEngine } from './WorkflowAutomationEngine';
import { AssetPerformanceAnalytics } from './AssetPerformanceAnalytics';

interface Props {
  workspaceId: string;
  className?: string;
}

/**
 * AssetManagementShowcase - Complete demonstration of the AI-powered asset management system
 * 
 * This component showcases the full "wow factor" experience by integrating:
 * - Real-time WebSocket updates
 * - AI impact prediction
 * - Smart notifications and batching
 * - Workflow automation
 * - Performance analytics
 * - Dependency visualization
 */
export const AssetManagementShowcase: React.FC<Props> = ({
  workspaceId,
  className = ''
}) => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'automation' | 'analytics' | 'dependencies'>('overview');
  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [changeDescription, setChangeDescription] = useState('');
  const [showImpactPredictor, setShowImpactPredictor] = useState(false);

  // Hook integrations
  const { dependencies, loading: depsLoading } = useAssetDependencies(workspaceId);
  const { isConnected, updates, activeStreams, liveMetrics } = useRealTimeAssets(workspaceId);

  const handlePredictionReady = (prediction: any) => {
    console.log('Impact prediction ready:', prediction);
    // Integrate with notification system
  };

  const tabs = [
    { id: 'overview', label: 'Live Overview', icon: '👁️', description: 'Real-time asset activity' },
    { id: 'automation', label: 'Automation', icon: '🤖', description: 'Workflow rules & batching' },
    { id: 'analytics', label: 'Analytics', icon: '📊', description: 'Performance insights' },
    { id: 'dependencies', label: 'Dependencies', icon: '🕸️', description: 'Asset relationships' }
  ];

  return (
    <div className={`bg-gradient-to-br from-gray-50 to-blue-50 min-h-screen ${className}`}>
      {/* Smart Notification Center - Floating */}
      <SmartNotificationCenter 
        workspaceId={workspaceId} 
        position="top-right"
        maxVisible={3}
      />

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  🚀 AI Asset Management Platform
                </h1>
                <p className="mt-2 text-lg text-gray-600">
                  Intelligent, automated, and real-time asset orchestration
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                  isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  <div className={`w-3 h-3 rounded-full ${
                    isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`}></div>
                  <span className="text-sm font-medium">
                    {isConnected ? 'Live Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>

            {/* Live Stats Banner */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
                <div className="text-2xl font-bold">{activeStreams.length}</div>
                <div className="text-sm opacity-90">Processing Now</div>
              </div>
              <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
                <div className="text-2xl font-bold">{liveMetrics.autoApplicableUpdates}</div>
                <div className="text-sm opacity-90">Auto-Applicable</div>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
                <div className="text-2xl font-bold">{Math.round(liveMetrics.avgImpactScore * 100)}%</div>
                <div className="text-sm opacity-90">Avg Impact</div>
              </div>
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
                <div className="text-2xl font-bold">{updates.length}</div>
                <div className="text-sm opacity-90">Recent Updates</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  selectedTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="text-lg">{tab.icon}</span>
                <span>{tab.label}</span>
                <span className="text-xs text-gray-400 hidden md:block">{tab.description}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedTab === 'overview' && (
          <div className="space-y-8">
            {/* Real-time Activity Stream */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">⚡ Live Activity Stream</h2>
                <p className="text-sm text-gray-600">Real-time updates from your asset ecosystem</p>
              </div>
              
              <div className="p-6">
                {activeStreams.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">🔄 Active Processing</h3>
                    <div className="space-y-3">
                      {activeStreams.map((stream) => (
                        <div key={stream.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-blue-900">{stream.name}</span>
                            <span className="text-sm text-blue-600">{stream.progress}%</span>
                          </div>
                          <div className="w-full bg-blue-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${stream.progress}%` }}
                            ></div>
                          </div>
                          {stream.eta_seconds && (
                            <div className="mt-2 text-xs text-blue-600">
                              ETA: {Math.round(stream.eta_seconds / 60)}m {stream.eta_seconds % 60}s
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Recent Updates */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">📋 Recent Updates</h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {updates.slice(0, 10).map((update, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {update.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              update.impact_score > 0.7 ? 'bg-red-100 text-red-800' :
                              update.impact_score > 0.4 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {Math.round(update.impact_score * 100)}% impact
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{update.data.name || update.asset_id}</p>
                          <div className="text-xs text-gray-500 mt-1">
                            {new Date(update.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* AI Impact Predictor */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">🤖 AI Impact Predictor</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Asset ID
                        </label>
                        <input
                          type="text"
                          value={selectedAssetId}
                          onChange={(e) => setSelectedAssetId(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          placeholder="Enter asset ID to analyze..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Change Description
                        </label>
                        <textarea
                          value={changeDescription}
                          onChange={(e) => setChangeDescription(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          rows={3}
                          placeholder="Describe the planned changes..."
                        />
                      </div>
                      <button
                        onClick={() => setShowImpactPredictor(true)}
                        disabled={!selectedAssetId || changeDescription.length < 10}
                        className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                      >
                        Predict Impact with AI
                      </button>
                    </div>

                    {showImpactPredictor && selectedAssetId && changeDescription && (
                      <div className="mt-4">
                        <AIImpactPredictor
                          assetId={selectedAssetId}
                          workspaceId={workspaceId}
                          changeDescription={changeDescription}
                          onPredictionReady={handlePredictionReady}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'automation' && (
          <WorkflowAutomationEngine 
            workspaceId={workspaceId}
            className="shadow-lg"
          />
        )}

        {selectedTab === 'analytics' && (
          <AssetPerformanceAnalytics 
            workspaceId={workspaceId}
            className="shadow-lg"
          />
        )}

        {selectedTab === 'dependencies' && (
          <div className="space-y-8">
            <DependencyGraph 
              workspaceId={workspaceId}
              className="shadow-lg"
            />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <RelatedAssetsModal
                assetId={selectedAssetId || 'demo-asset'}
                workspaceId={workspaceId}
                isOpen={true}
                onClose={() => {}}
              />
              
              <AssetHistoryPanel
                assetId={selectedAssetId || 'demo-asset'}
                workspaceId={workspaceId}
                className="shadow-lg"
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer with Integration Status */}
      <div className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              ✨ Complete AI-Powered Asset Management Platform
            </h3>
            <p className="text-gray-600 mb-4">
              Real-time updates • AI predictions • Smart automation • Performance analytics
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <span className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                WebSocket Connected
              </span>
              <span className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                AI Models Active
              </span>
              <span className="flex items-center">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                Automation Running
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};