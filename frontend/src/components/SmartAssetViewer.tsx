// frontend/src/components/SmartAssetViewer.tsx - USER FRIENDLY ASSET VIEWER
'use client';

import React, { useState, useEffect } from 'react';
import type { ActionableAsset } from '@/types';
import StructuredAssetRenderer from './StructuredAssetRenderer';
import GenericArrayViewer from './GenericArrayViewer';
import { useAssetRefinementStatus } from '@/hooks/useAssetRefinementStatus';
import EnhancementTaskMonitorWebSocket from './EnhancementTaskMonitorWebSocket';

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
  const [activeView, setActiveView] = useState<'visual' | 'data' | 'usage' | 'requests'>('visual');
  const [processedMarkup, setProcessedMarkup] = useState<any>(null);
  const [refinementFeedback, setRefinementFeedback] = useState('');
  const [refinementLoading, setRefinementLoading] = useState(false);
  const [showEnhancementDetails, setShowEnhancementDetails] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [showTaskMonitor, setShowTaskMonitor] = useState(false);
  
  // Get workspace ID from URL
  const workspaceId = typeof window !== 'undefined' ? window.location.pathname.split('/')[2] : '';
  
  // Get refinement status for this asset
  const refinementStatus = useAssetRefinementStatus(workspaceId, asset.asset_name || asset.name);
  
  // Check if asset has markup content
  useEffect(() => {
    const assetData = asset.asset_data || asset.content || {};
    if (assetData._processed_markup) {
      setProcessedMarkup(assetData._processed_markup);
    }
  }, [asset]);

  // Load saved draft feedback
  useEffect(() => {
    const draftKey = `asset-refinement-draft-${asset.asset_name || asset.name}`;
    const savedDraft = localStorage.getItem(draftKey);
    if (savedDraft) {
      setRefinementFeedback(savedDraft);
    }
  }, [asset.asset_name, asset.name]);

  // Save draft as user types
  useEffect(() => {
    if (refinementFeedback.trim()) {
      const draftKey = `asset-refinement-draft-${asset.asset_name || asset.name}`;
      localStorage.setItem(draftKey, refinementFeedback);
    }
  }, [refinementFeedback, asset.asset_name, asset.name]);

  // Handle refinement submission
  const handleRefinementSubmit = async () => {
    if (!refinementFeedback.trim()) return;
    
    try {
      setRefinementLoading(true);
      
      const taskId = asset.source_task_id || asset.sourceTaskId || 'unknown-task-id';
      const workspaceId = window.location.pathname.split('/')[2]; // Extract from URL
      
      const refinementPayload = {
        asset_data: asset.asset_data || asset.content,
        asset_name: asset.asset_name || asset.name,
        user_feedback: refinementFeedback,
        refinement_type: 'user_requested_improvement',
        workspace_id: workspaceId
      };

      console.log('📤 [SmartAssetViewer] Sending refinement request:', refinementPayload);
      
      const response = await fetch(`http://localhost:8000/improvement/asset-refinement/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(refinementPayload)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📥 [SmartAssetViewer] Refinement response:', result);
        
        // Clear draft and reset form
        const draftKey = `asset-refinement-draft-${asset.asset_name || asset.name}`;
        localStorage.removeItem(draftKey);
        setRefinementFeedback('');
        
        // Extract task ID from response for monitoring
        if (result.enhancement_task_id) {
          setCurrentTaskId(result.enhancement_task_id);
          setShowTaskMonitor(true);
          console.log('🔍 Starting task monitoring for:', result.enhancement_task_id);
        }
        
        // Refresh the refinement status immediately
        console.log('🔄 Refreshing refinement status after submission');
        await refinementStatus.refresh();
        
        // Show nice success message instead of alert
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        successDiv.innerHTML = `
          <div class="flex items-center space-x-2">
            <span>✅</span>
            <span>Enhancement task created! Monitoring progress...</span>
          </div>
        `;
        document.body.appendChild(successDiv);
        setTimeout(() => document.body.removeChild(successDiv), 4000);
        
      } else {
        throw new Error(`Failed to start refinement: ${response.statusText}`);
      }
    } catch (error) {
      console.error('❌ [Asset Refinement] Error:', error);
      // Show error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      errorDiv.innerHTML = `
        <div class="flex items-center space-x-2">
          <span>❌</span>
          <span>Failed to request refinement</span>
        </div>
      `;
      document.body.appendChild(errorDiv);
      setTimeout(() => document.body.removeChild(errorDiv), 4000);
    } finally {
      setRefinementLoading(false);
    }
  };

  // Handle task completion
  const handleTaskCompleted = async (taskId: string, result: any) => {
    console.log('🎉 Enhancement task completed:', taskId, result);
    
    // Refresh refinement status to show the completed task
    await refinementStatus.refresh();
    
    // Show completion notification
    const successDiv = document.createElement('div');
    successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    successDiv.innerHTML = `
      <div class="flex items-center space-x-2">
        <span>🎉</span>
        <span>Enhancement completed! Asset has been updated.</span>
      </div>
    `;
    document.body.appendChild(successDiv);
    setTimeout(() => document.body.removeChild(successDiv), 5000);
    
    // Hide task monitor after completion
    setTimeout(() => {
      setShowTaskMonitor(false);
      setCurrentTaskId(null);
    }, 10000); // Keep visible for 10 seconds to show final result
  };

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
              { 
                key: 'requests', 
                label: `💬 Requests ${refinementStatus.totalRefinements > 0 ? `(${refinementStatus.totalRefinements})` : ''}`, 
                desc: refinementStatus.pendingRefinements.length > 0 ? `${refinementStatus.pendingRefinements.length} pending` : 'Improve asset'
              },
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
          {activeView === 'requests' && (
            <div className="space-y-6">
              {/* Task Monitor for Active Enhancement */}
              {showTaskMonitor && currentTaskId && (
                <EnhancementTaskMonitorWebSocket
                  workspaceId={workspaceId}
                  taskId={currentTaskId}
                  onTaskCompleted={handleTaskCompleted}
                />
              )}
              
              {/* Enhancement Status - Minimal */}
              {refinementStatus.isLoading ? (
                <div className="text-center py-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400 mx-auto"></div>
                </div>
              ) : refinementStatus.totalRefinements > 0 ? (
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 mb-4">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setShowEnhancementDetails(!showEnhancementDetails)}
                      className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
                    >
                      <span className="text-blue-600">🔄</span>
                      <span className="text-sm font-medium text-blue-800 underline">
                        {refinementStatus.pendingRefinements.length > 0 
                          ? `${refinementStatus.pendingRefinements.length} enhancement${refinementStatus.pendingRefinements.length > 1 ? 's' : ''} in progress`
                          : `${refinementStatus.completedRefinements.length} enhancement${refinementStatus.completedRefinements.length > 1 ? 's' : ''} in history`
                        }
                      </span>
                      <span className="text-blue-600 text-xs">{showEnhancementDetails ? '▼' : '▶'}</span>
                    </button>
                    {refinementStatus.totalRefinements > 0 && (
                      <span className="text-xs text-blue-600">
                        Total: {refinementStatus.totalRefinements}
                      </span>
                    )}
                  </div>
                  
                  {/* Enhancement Details Dropdown */}
                  {showEnhancementDetails && (
                    <div className="mt-3 pt-3 border-t border-blue-200 space-y-2">
                      {refinementStatus.pendingRefinements.length > 0 && (
                        <div>
                          <h6 className="text-xs font-semibold text-blue-700 mb-1">In Progress:</h6>
                          {refinementStatus.pendingRefinements.map((task) => (
                            <div key={task.id} className="bg-white rounded p-2 mb-1 text-xs">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="font-medium text-gray-700">{task.name.replace('🔄 ENHANCE: ', '')}</div>
                                  <div className="text-gray-500 italic mt-1">"{task.metadata?.user_feedback || task.context_data?.user_feedback || 'Nessuna descrizione'}"</div>
                                </div>
                                <div className="text-orange-600 text-xs ml-2">{task.status}</div>
                              </div>
                              <div className="text-gray-400 mt-1">
                                {new Date(task.created_at).toLocaleString()}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {refinementStatus.completedRefinements.length > 0 && (
                        <div>
                          <h6 className="text-xs font-semibold text-gray-700 mb-1">History:</h6>
                          {refinementStatus.completedRefinements.map((task) => (
                            <div key={task.id} className={`rounded p-2 mb-1 text-xs ${
                              task.status === 'completed' ? 'bg-green-50' : 'bg-red-50'
                            }`}>
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="font-medium text-gray-700">{task.name.replace('🔄 ENHANCE: ', '')}</div>
                                  <div className="text-gray-500 italic mt-1">"{task.metadata?.user_feedback || task.context_data?.user_feedback || 'Nessuna descrizione'}"</div>
                                </div>
                                <div className={`text-xs ml-2 ${
                                  task.status === 'completed' ? 'text-green-600' : 'text-red-600'
                                }`}>
                                  {task.status === 'completed' ? '✓' : '❌'} {task.status}
                                </div>
                              </div>
                              <div className="text-gray-400 mt-1">
                                {new Date(task.created_at).toLocaleString()}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : null}

              
              {/* Asset Version Info - Minimal */}
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">📝</span>
                    <span className="text-sm text-gray-700">Version 1.0</span>
                    {asset.source_task_id && asset.source_task_id !== 'unknown-task-id' && (
                      <span className="text-xs text-gray-500">• From task completion</span>
                    )}
                  </div>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Active</span>
                </div>
              </div>

              {/* Request Changes Form */}
              <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4 border border-orange-200">
                <h4 className="font-semibold text-orange-800 mb-3">💬 Request Improvements</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      What would you like to improve or change?
                    </label>
                    <textarea
                      value={refinementFeedback}
                      onChange={(e) => setRefinementFeedback(e.target.value)}
                      disabled={refinementLoading}
                      placeholder="Describe the improvements you'd like to see. Be as specific as possible. For example:&#10;&#10;• Add more detailed information&#10;• Include additional data fields&#10;• Improve content quality&#10;• Expand the scope&#10;• Change the format or structure"
                      className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                      rows={6}
                    />
                    <div className="flex justify-between items-center mt-2">
                      <div className="text-xs text-gray-500">
                        💡 Be specific to get better results
                      </div>
                      <div className="text-xs text-gray-400">
                        {refinementFeedback.length}/1000
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <h5 className="font-medium text-blue-800 mb-2">💡 Tips for better results:</h5>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Be specific about what data or information to add</li>
                      <li>• Mention quality improvements you want to see</li>
                      <li>• Specify if you want more items/entries</li>
                      <li>• Describe the format or structure changes needed</li>
                    </ul>
                  </div>

                  {refinementLoading && (
                    <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                      <div className="flex items-center space-x-3">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-orange-500"></div>
                        <div>
                          <div className="font-medium text-yellow-800">Processing your request...</div>
                          <div className="text-sm text-yellow-600">The AI team is working on your enhancement</div>
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleRefinementSubmit}
                    disabled={refinementLoading || !refinementFeedback.trim()}
                    className="w-full px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-medium hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {refinementLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <span>🚀</span>
                        <span>Submit Improvement Request</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
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
              onClick={() => setActiveView('requests')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition flex items-center justify-center space-x-2 ${
                activeView === 'requests' 
                  ? 'bg-orange-200 text-orange-800 border border-orange-300' 
                  : 'bg-orange-600 text-white hover:bg-orange-700'
              }`}
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