// frontend/src/components/SmartAssetViewer.tsx - USER FRIENDLY ASSET VIEWER
'use client';

import React, { useState, useEffect } from 'react';
import type { ActionableAsset } from '@/types';
import StructuredAssetRenderer from './StructuredAssetRenderer';
import GenericArrayViewer from './GenericArrayViewer';

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
    const assetData = asset.asset_data || asset.content || {};
    if (assetData._processed_markup) {
      setProcessedMarkup(assetData._processed_markup);
    }
  }, [asset]);

  const getAssetTypeInfo = (assetName: string, assetData: any) => {
    // Smart icon detection based on content - handle undefined/null assetName
    const nameLower = (assetName || '').toLowerCase();
    let icon = '📋'; // default
    
    if (nameLower.includes('calendar') || nameLower.includes('schedule')) icon = '📅';
    else if (nameLower.includes('contact') || nameLower.includes('people')) icon = '👤';
    else if (nameLower.includes('product') || nameLower.includes('catalog')) icon = '📦';
    else if (nameLower.includes('task') || nameLower.includes('workflow')) icon = '✅';
    else if (nameLower.includes('report') || nameLower.includes('analysis')) icon = '📊';
    else if (nameLower.includes('strategy') || nameLower.includes('plan')) icon = '🎯';
    else if (nameLower.includes('content') || nameLower.includes('social')) icon = '📱';
    
    // Clean up the name
    const cleanName = assetName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
    
    return {
      type: 'universal',
      icon: icon,
      title: cleanName,
      description: 'Business-ready deliverable'
    };
  };

  const typeInfo = getAssetTypeInfo(asset.asset_name || asset.name || 'Asset', asset.asset_data || asset.content);

  // Universal smart content renderer 
  const renderAssetContent = () => {
    // ✅ COMPATIBILITY: Handle both backend structures
    // Backend returns: asset.content, Frontend expects: asset.asset_data
    const assetData = asset.asset_data || asset.content || {};
    
    console.log('🔍 [SmartAssetViewer] Asset data debug:', {
      hasAssetData: !!asset.asset_data,
      hasContent: !!asset.content,
      assetDataKeys: Object.keys(asset.asset_data || {}),
      contentKeys: Object.keys(asset.content || {}),
      finalAssetData: assetData,
      finalAssetDataSize: Object.keys(assetData).length,
      assetDataType: typeof assetData,
      fullAssetStructure: asset
    });

    // ✅ PRIORITY 1: Check for pre-rendered HTML from dual output format
    if (assetData?.rendered_html) {
      return (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
            <h3 className="text-lg font-semibold text-green-800 mb-2">⚡ Ready-to-View Content</h3>
            <p className="text-green-700 text-sm">Pre-formatted by AI during creation - zero delay</p>
          </div>
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: assetData.rendered_html }} 
          />
        </div>
      );
    }

    // ✅ PRIORITY 2: Smart detection of array-based content (generic approach)
    const arrayFields = Object.entries(assetData || {}).filter(([key, value]) => 
      Array.isArray(value) && value.length > 0 && typeof value[0] === 'object'
    );
    
    if (arrayFields.length > 0) {
      const [fieldName, fieldData] = arrayFields[0]; // Use the first array field
      const additionalData = Object.fromEntries(
        Object.entries(assetData || {}).filter(([key, value]) => !Array.isArray(value))
      );
      
      console.log(`🔍 SmartAssetViewer: Using GenericArrayViewer for ${fieldName} with ${fieldData.length} items`);
      
      return (
        <GenericArrayViewer 
          items={fieldData} 
          fieldName={fieldName}
          additionalData={additionalData}
          assetName={asset.asset_name || asset.name || 'Asset'}
        />
      );
    }

    // ✅ PRIORITY 2: Check for rendered_html from rich deliverables
    if (assetData?.rendered_html) {
      const renderedHtml = assetData.rendered_html;
      const visualSummary = assetData?.visual_summary;
      const actionableInsights = assetData?.actionable_insights || [];
      
      return (
        <div className="space-y-4">
          {visualSummary && (
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <h4 className="font-semibold text-green-800 mb-2">🎯 Executive Summary</h4>
              <p className="text-green-700">{visualSummary}</p>
            </div>
          )}
          
          <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-4">📄 Business-Ready Content</h4>
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: renderedHtml }}
            />
          </div>
          
          {actionableInsights.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-3">💡 Actionable Insights</h4>
              <ul className="space-y-2">
                {actionableInsights.map((insight: string, idx: number) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span className="text-blue-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }

    // ✅ PRIORITY 3: Check for structured_content from dual output
    if (assetData?.structured_content) {
      const structuredContent = assetData.structured_content;
      
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
    
    // ✅ FINAL FALLBACK: Use the compatible assetData we defined above
    if (!assetData || typeof assetData !== 'object') {
      console.log('❌ [SmartAssetViewer] No data available - Debug:', {
        assetData,
        assetDataType: typeof assetData,
        assetDataKeys: assetData ? Object.keys(assetData) : 'null/undefined',
        condition1: !assetData,
        condition2: typeof assetData !== 'object'
      });
      return <div className="text-gray-500">No data available for this asset</div>;
    }

    // Check if data has markup strings
    const hasMarkupStrings = Object.values(assetData).some(value => 
      typeof value === 'string' && value.includes('## TABLE:')
    );
    
    if (hasMarkupStrings) {
      // Process markup on the fly
      return <div className="text-center py-8 text-gray-600">
        <p>Structured content detected. Processing...</p>
      </div>;
    }

    // ✅ FALLBACK: Universal approach for legacy data
    const entries = Object.entries(assetData).filter(([key]) => 
      key !== '_processed_markup' && 
      key !== 'rendered_html' && 
      key !== 'structured_content' &&
      key !== '_original'
    );
    
    if (entries.length === 0) {
      console.log('⚠️ [SmartAssetViewer] No entries found, showing fallback with asset info');
      return (
        <div className="text-center py-8 text-gray-500">
          <p>Asset extraction in progress...</p>
          <p className="text-sm mt-2">Please check back in a few moments.</p>
          <div className="mt-4 p-4 bg-gray-100 rounded-lg text-left">
            <h4 className="font-medium mb-2">Debug Info:</h4>
            <p className="text-xs">Asset Name: {asset.asset_name || asset.name || 'Unknown'}</p>
            <p className="text-xs">Has asset_data: {!!asset.asset_data ? 'Yes' : 'No'}</p>
            <p className="text-xs">Has content: {!!asset.content ? 'Yes' : 'No'}</p>
            <p className="text-xs">Ready to use: {asset.ready_to_use ? 'Yes' : 'No'}</p>
          </div>
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
                {JSON.stringify(asset.asset_data || asset.content, null, 2)}
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