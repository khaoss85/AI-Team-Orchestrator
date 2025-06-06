// frontend/src/components/SmartAssetViewer.tsx - USER FRIENDLY ASSET VIEWER
'use client';

import React, { useState, useEffect } from 'react';
import type { ActionableAsset } from '@/types';
import StructuredAssetRenderer from './StructuredAssetRenderer';

interface SmartAssetViewerProps {
  asset: ActionableAsset;
  onClose: () => void;
  onDownload?: (asset: ActionableAsset) => void;
  onRefine?: (asset: ActionableAsset) => void;
}

const SmartAssetViewer: React.FC<SmartAssetViewerProps> = ({
  asset,
  onClose,
  onDownload,
  onRefine
}) => {
  const [activeView, setActiveView] = useState<'visual' | 'data' | 'usage'>('visual');
  const [processedMarkup, setProcessedMarkup] = useState<any>(null);
  
  // Check if asset has markup content
  useEffect(() => {
    if (asset.asset_data?._processed_markup) {
      setProcessedMarkup(asset.asset_data._processed_markup);
    }
  }, [asset]);

  const getAssetTypeInfo = (assetName: string, assetData: any) => {
    // Simple universal approach - clean up the name and use generic icon
    const cleanName = assetName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
    
    return {
      type: 'universal',
      icon: '📋',
      title: cleanName,
      description: 'Business-ready deliverable'
    };
  };

  const typeInfo = getAssetTypeInfo(asset.asset_name, asset.asset_data);

  // Universal smart content renderer 
  const renderAssetContent = () => {
    // 🧪 TEST: Check for test asset injection
    const testAsset = localStorage.getItem('test_instagram_calendar');
    if (testAsset && asset.asset_name.toLowerCase().includes('calendar')) {
      try {
        const testData = JSON.parse(testAsset);
        return (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
              <h3 className="text-lg font-semibold text-green-800 mb-2">🧪 TEST MODE: Enhanced Content</h3>
              <p className="text-green-700 text-sm">This is how the content should look with proper dual output format</p>
            </div>
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: testData.rendered_html }} 
            />
          </div>
        );
      } catch (e) {
        console.error('Error parsing test asset:', e);
      }
    }

    // ✅ PRIORITY 1: Check for pre-rendered HTML from dual output format
    if (asset.asset_data?.rendered_html) {
      return (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
            <h3 className="text-lg font-semibold text-green-800 mb-2">⚡ Ready-to-View Content</h3>
            <p className="text-green-700 text-sm">Pre-formatted by AI during creation - zero delay</p>
          </div>
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: asset.asset_data.rendered_html }} 
          />
        </div>
      );
    }

    // ✅ PRIORITY 2: Check for calendar array format (current backend format)
    if (asset.asset_data?.calendar && Array.isArray(asset.asset_data.calendar)) {
      const calendar = asset.asset_data.calendar;
      const executiveSummary = asset.asset_data.executive_summary;
      
      return (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg mb-4">
            <h3 className="text-lg font-semibold text-purple-800 mb-2">📅 Instagram Editorial Calendar</h3>
            <p className="text-purple-700 text-sm">Complete 3-month content strategy with {calendar.length} specific posts</p>
          </div>

          {/* Executive Summary */}
          {executiveSummary && (
            <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
              <h4 className="font-semibold text-gray-800 mb-2">📋 Overview</h4>
              <p className="text-gray-700 text-sm">{executiveSummary}</p>
            </div>
          )}

          {/* Calendar Posts */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-800 mb-3">📱 Content Calendar ({calendar.length} Posts)</h4>
            <div className="grid gap-4">
              {calendar.map((post: any, index: number) => {
                // Debug logging for each post
                if (process.env.NODE_ENV === 'development') {
                  console.log(`Rendering post ${index + 1}:`, post);
                }
                
                return (
                <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{post.type}</div>
                        <div className="text-xs text-gray-500">{post.date}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {post.type === 'Carousel' && <span className="text-blue-500">🖼️</span>}
                      {post.type === 'Reel' && <span className="text-purple-500">🎬</span>}
                      {post.type === 'Photo' && <span className="text-green-500">📸</span>}
                      {post.type === 'Video' && <span className="text-red-500">🎥</span>}
                      {post.type === 'Motivational Post' && <span className="text-yellow-500">💪</span>}
                      {post.type === 'Transformation Post' && <span className="text-orange-500">🔥</span>}
                    </div>
                  </div>
                  
                  {/* Caption */}
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-800 mb-1">Caption:</h5>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded border-l-4 border-blue-400">
                      {post.caption}
                    </p>
                  </div>
                  
                  {/* Hashtags */}
                  {post.hashtags && (
                    <div className="mb-3">
                      <h5 className="font-medium text-gray-800 mb-1">Hashtags:</h5>
                      <div className="flex flex-wrap gap-1">
                        {Array.isArray(post.hashtags) ? post.hashtags.map((hashtag: string, idx: number) => (
                          <span key={idx} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                            {hashtag}
                          </span>
                        )) : (
                          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                            {post.hashtags}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Engagement Strategy */}
                  {post.engagement && (
                    <div className="bg-green-50 border border-green-200 rounded p-2">
                      <h5 className="font-medium text-green-800 text-xs mb-1">🎯 Engagement Strategy:</h5>
                      <p className="text-green-700 text-xs">{post.engagement}</p>
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>

          {/* Content Statistics */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-3">📊 Content Statistics</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600">{calendar.length}</div>
                <div className="text-xs text-gray-600">Total Posts</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-purple-600">
                  {calendar.filter((p: any) => p.type === 'Reel').length}
                </div>
                <div className="text-xs text-gray-600">Reels</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-green-600">
                  {calendar.filter((p: any) => p.type === 'Carousel').length}
                </div>
                <div className="text-xs text-gray-600">Carousels</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-orange-600">
                  {calendar.filter((p: any) => p.type && (p.type.includes('Motivational') || p.type.includes('Transformation'))).length}
                </div>
                <div className="text-xs text-gray-600">Special Posts</div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // ✅ PRIORITY 3: Check for structured_content from dual output
    if (asset.asset_data?.structured_content) {
      const structuredContent = asset.asset_data.structured_content;
      
      return (
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-3">📋 Structured Business Content</h4>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <SmartValueRenderer value={structuredContent} />
            </div>
          </div>
        </div>
      );
    }

    // ✅ PRIORITY 3: If we have processed markup, use the structured renderer
    if (processedMarkup && processedMarkup.has_structured_content) {
      return (
        <StructuredAssetRenderer 
          data={processedMarkup}
          onExport={(format) => {
            // Handle export
            console.log('Export in format:', format);
            onDownload?.(asset);
          }}
        />
      );
    }
    
    const data = asset.asset_data;
    
    if (!data || typeof data !== 'object') {
      return <div className="text-gray-500">No data available for this asset</div>;
    }

    // Check if data has markup strings
    const hasMarkupStrings = Object.values(data).some(value => 
      typeof value === 'string' && value.includes('## TABLE:')
    );
    
    if (hasMarkupStrings) {
      // Process markup on the fly
      return <div className="text-center py-8 text-gray-600">
        <p>Structured content detected. Processing...</p>
      </div>;
    }

    // ✅ FALLBACK: Universal approach for legacy data
    const entries = Object.entries(data).filter(([key]) => 
      key !== '_processed_markup' && 
      key !== 'rendered_html' && 
      key !== 'structured_content'
    );
    
    if (entries.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>Asset extraction in progress...</p>
          <p className="text-sm mt-2">Please check back in a few moments.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-semibold text-blue-800 mb-3">📋 Deliverable Content</h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {entries.map(([key, value]) => (
              <div key={key} className="bg-white rounded-lg p-4 border border-blue-100">
                <div className="font-medium text-blue-700 mb-2">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div className="text-gray-700">
                  <SmartValueRenderer value={value} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Universal usage instructions
  const renderUsageInstructions = () => {
    const instructions = [
      "Review the deliverable content in the Visual View tab",
      "Adapt the content to fit your specific business context", 
      "Implement the recommendations systematically",
      "Download the asset for integration with your existing tools",
      "Monitor results and request refinements if needed"
    ];

    return (
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-3">💡 How to Use This Deliverable</h4>
        <ol className="space-y-2">
          {instructions.map((instruction, index) => (
            <li key={index} className="flex items-start">
              <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">
                {index + 1}
              </div>
              <span className="text-blue-900">{instruction}</span>
            </li>
          ))}
        </ol>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">{typeInfo.icon}</div>
              <div>
                <h2 className="text-2xl font-bold">{typeInfo.title}</h2>
                <p className="opacity-90">{typeInfo.description}</p>
              </div>
            </div>
            <button 
              onClick={onClose} 
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <div className="flex">
            {[
              { key: 'visual', label: '👁️ Visual View', desc: 'Formatted view' },
              { key: 'usage', label: '💡 Usage Guide', desc: 'How to use' },
              { key: 'data', label: '🔧 Raw Data', desc: 'Technical view' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveView(tab.key as any)}
                className={`flex-1 px-6 py-4 text-center border-b-2 transition ${
                  activeView === tab.key
                    ? 'border-green-500 text-green-600 bg-green-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="font-medium">{tab.label}</div>
                <div className="text-xs text-gray-500">{tab.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeView === 'visual' && renderAssetContent()}
          {activeView === 'usage' && renderUsageInstructions()}
          {activeView === 'data' && (
            <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
              <h3 className="text-white font-medium mb-3">Raw Asset Data</h3>
              <pre className="text-green-400 text-sm overflow-auto max-h-96">
                {JSON.stringify(asset.asset_data, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="flex space-x-4">
            <button
              onClick={() => onDownload?.(asset)}
              className="flex-1 bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center justify-center space-x-2"
            >
              <span>📥</span>
              <span>Download Asset</span>
            </button>
            <button
              onClick={() => onRefine?.(asset)}
              className="flex-1 bg-orange-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-orange-700 transition flex items-center justify-center space-x-2"
            >
              <span>💬</span>
              <span>Request Changes</span>
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Universal smart value renderer component
const SmartValueRenderer: React.FC<{ value: any }> = ({ value }) => {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }

  if (typeof value === 'string') {
    if (value.length > 200) {
      return (
        <div>
          <div className="mb-2">{value.substring(0, 200)}...</div>
          <div className="text-xs text-gray-500">({value.length} characters total)</div>
        </div>
      );
    }
    return <span>{value}</span>;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return <span className="font-medium">{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-gray-400 italic">Empty list</span>;
    }
    
    return (
      <div>
        <div className="font-medium text-sm mb-2">{value.length} items:</div>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {value.slice(0, 5).map((item, index) => (
            <div key={index} className="bg-gray-50 rounded p-2 text-sm">
              <div className="text-xs text-gray-500 mb-1">Item {index + 1}</div>
              <SmartValueRenderer value={item} />
            </div>
          ))}
          {value.length > 5 && (
            <div className="text-xs text-gray-500 text-center">
              + {value.length - 5} more items
            </div>
          )}
        </div>
      </div>
    );
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value);
    if (entries.length === 0) {
      return <span className="text-gray-400 italic">Empty object</span>;
    }

    return (
      <div className="space-y-2">
        {entries.slice(0, 3).map(([key, val]) => (
          <div key={key} className="bg-gray-50 rounded p-2">
            <div className="text-xs font-medium text-gray-600 mb-1">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
            <div className="text-sm">
              <SmartValueRenderer value={val} />
            </div>
          </div>
        ))}
        {entries.length > 3 && (
          <div className="text-xs text-gray-500 text-center">
            + {entries.length - 3} more properties
          </div>
        )}
      </div>
    );
  }

  return <span>{String(value)}</span>;
};

export default SmartAssetViewer;