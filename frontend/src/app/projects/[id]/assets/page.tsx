'use client';

import React, { useState, useEffect, use } from 'react';
import { useAssetDependencies } from '@/hooks/useAssetDependencies';
import { useAssetManagement } from '@/hooks/useAssetManagement';
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

// Simplified - only components now

export default function ProjectAssetsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const workspaceId = params.id;
  
  // No longer needed - only components tab
  // const [activeTab, setActiveTab] = useState<TabType>('components');
  
  const {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    dependencies,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    history,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    loading: dependenciesLoading,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    fetchHistory,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    compareVersions,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyUpdates
  } = useAssetDependencies(workspaceId);

  // Load real assets from the workspace
  const {
    assets: realAssets,
    loading: assetsLoading
  } = useAssetManagement(workspaceId);

  // Load tasks to get iteration counts and proper versioning
  const [tasks, setTasks] = useState<any[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setTasksLoading(true);
        const response = await fetch(`http://localhost:8000/monitoring/workspace/${workspaceId}/tasks`);
        if (response.ok) {
          const data = await response.json();
          setTasks(Array.isArray(data) ? data : data.tasks || []);
        }
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      } finally {
        setTasksLoading(false);
      }
    };

    if (workspaceId) {
      fetchTasks();
    }
  }, [workspaceId]);

  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [selectedAsset, setSelectedAsset] = useState<{
    id: string;
    name: string;
    type: string;
    lastModified: string;
    versions: number;
    sourceTaskId: string;
  } | null>(null);
  const [assetViewTab, setAssetViewTab] = useState<'content' | 'history' | 'dependencies' | 'impact' | 'feedback'>('content');
  const [showRelatedModal, setShowRelatedModal] = useState(false);
  
  // Enhanced content state for AI visualization in asset tabs
  const [enhancedContent, setEnhancedContent] = useState<any>(null);
  const [loadingEnhanced, setLoadingEnhanced] = useState(false);
  const [aiProcessedContent, setAiProcessedContent] = useState<string | null>(null);
  const [loadingAiContent, setLoadingAiContent] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  
  // No longer needed - deliverables functionality moved to content tab
  // const { allResults, readyToUse, finalDeliverables, loading: resultsLoading, error: resultsError } = useProjectResults(workspaceId);

  // Helper function to determine asset type from name
  const getAssetTypeFromName = (assetName: string): string => {
    const name = assetName.toLowerCase();
    if (name.includes('strategy') || name.includes('analysis')) return 'analysis';
    if (name.includes('report') || name.includes('research')) return 'report';
    if (name.includes('projection') || name.includes('budget') || name.includes('financial')) return 'spreadsheet';
    if (name.includes('guideline') || name.includes('brand') || name.includes('document')) return 'document';
    return 'document';
  };

  // Convert real assets to display format with proper versioning and deduplication
  const processedAssets = new Map();
  
  Object.entries(realAssets).forEach(([key, asset]) => {
    // Use task name as the primary identifier to group versions
    const taskName = tasks?.find(t => t.id === asset.source_task_id)?.name || asset.asset_name;
    const cleanName = taskName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    // Find the source task to get more info
    const sourceTask = tasks?.find(t => t.id === asset.source_task_id);
    
    // Try to determine version number from various sources
    let versionNumber = 1;
    
    // 1. Check if the task name contains version info
    if (taskName.includes('Asset 1')) versionNumber = 1;
    else if (taskName.includes('Asset 2')) versionNumber = 2;
    else if (taskName.includes('Asset 3')) versionNumber = 3;
    
    // 2. Check iteration_count if available
    if (sourceTask?.iteration_count && sourceTask.iteration_count > 1) {
      versionNumber = sourceTask.iteration_count;
    }
    
    // 3. Check if it's an enhancement task (usually means v2+)
    if (taskName.toLowerCase().includes('enhance') && versionNumber === 1) {
      versionNumber = 2;
    }
    
    // 4. Look at creation timestamp to infer versions for same asset type
    const updatedAt = sourceTask?.updated_at || new Date().toISOString();
    
    // Create a unique identifier based on the clean name
    const assetKey = cleanName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    
    if (processedAssets.has(assetKey)) {
      // If we already have this asset, update with higher version number if applicable
      const existing = processedAssets.get(assetKey);
      if (versionNumber > existing.versions) {
        processedAssets.set(assetKey, {
          ...existing,
          versions: versionNumber,
          lastModified: new Date(updatedAt).toISOString().split('T')[0],
          sourceTaskId: asset.source_task_id,
          id: asset.source_task_id // Use latest task ID
        });
      }
    } else {
      // Add new asset
      processedAssets.set(assetKey, {
        id: asset.source_task_id,
        name: cleanName,
        type: getAssetTypeFromName(asset.asset_name || taskName),
        lastModified: new Date(updatedAt).toISOString().split('T')[0],
        versions: versionNumber,
        sourceTaskId: asset.source_task_id
      });
    }
  });

  const assets = Array.from(processedAssets.values());

  // Handle asset selection
  const handleAssetSelect = async (assetId: string) => {
    setSelectedAssetId(assetId);
    const asset = assets.find(a => a.id === assetId);
    setSelectedAsset(asset);
    
    // Load asset content for the content tab
    if (asset) {
      setLoadingEnhanced(true);
      setEnhancedContent(null);
      setAiProcessedContent(null);
      
      try {
        const tasksResponse = await fetch(`http://localhost:8000/monitoring/workspace/${workspaceId}/tasks`);
        if (tasksResponse.ok) {
          const tasksData = await tasksResponse.json();
          const task = tasksData.tasks?.find((t: any) => t.id === asset.sourceTaskId);
          if (task?.result?.detailed_results_json) {
            try {
              const detailedResults = JSON.parse(task.result.detailed_results_json);
              const content = {
                visual_summary: task.result?.summary || `📋 ${asset.name}`,
                content: task.result?.summary || asset.name,
                structured_content: detailedResults,
                key_insights: detailedResults.actionable_insights || detailedResults.key_insights || []
              };
              setEnhancedContent(content);
              
              if (!detailedResults.rendered_html) {
                const aiContent = await processWithAI(detailedResults, asset.name);
                if (aiContent && aiContent.length > 100) {
                  setAiProcessedContent(aiContent);
                }
              }
            } catch (e) {
              console.warn('Failed to parse detailed results:', e);
            }
          }
        }
      } catch (error) {
        console.error('Error fetching enhanced content:', error);
      } finally {
        setLoadingEnhanced(false);
      }
    }
  };
  
  // AI content processing (from Results page)
  const processWithAI = async (structuredContent: any, taskTitle: string) => {
    if (!structuredContent) return null;
    
    setLoadingAiContent(true);
    try {
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('AI processing timeout')), 45000);
      });
      
      const fetchPromise = fetch(`http://localhost:8000/ai/process-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: structuredContent,
          title: taskTitle,
          format: 'structured',
          instructions: `First, try to identify if this content contains structured data that can be organized as:
                        - Tables (data with rows/columns)
                        - Cards (individual items with title/content)
                        - Metrics (numerical values with units)
                        - Timelines (date-ordered events)
                        
                        If structured data is found, return JSON in this format:
                        {
                          "has_structured_content": true,
                          "tables": [{"type": "table", "name": "...", "display_name": "...", "headers": [...], "rows": [...], "row_count": N, "metadata": {"sortable": true, "filterable": true}}],
                          "cards": [{"type": "card", "card_type": "...", "fields": {"title": "...", "content": "..."}, "style": "default", "icon": "📊"}],
                          "metrics": [{"type": "metric", "name": "...", "display_name": "...", "value": "...", "unit": "...", "trend_icon": "📈"}],
                          "timelines": [{"type": "timeline", "name": "...", "display_name": "...", "entries": [{"date": "...", "event": "...", "status": "..."}]}]
                        }
                        
                        If no clear structure is found, return HTML instead:
                        {
                          "has_structured_content": false,
                          "rendered_html": "<div>...beautiful HTML here...</div>"
                        }
                        
                        Focus on actionability and business value. Use emojis for visual appeal.`
        })
      });

      const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

      if (response.ok) {
        const data = await response.json();
        const processedContent = data.processed_content || data.content;
        
        // Try to parse as JSON first (structured content)
        try {
          const parsed = typeof processedContent === 'string' ? JSON.parse(processedContent) : processedContent;
          if (parsed && typeof parsed === 'object') {
            return parsed; // Return structured data object
          }
        } catch (e) {
          // Not JSON, check if it's HTML
          if (processedContent && processedContent.includes('<') && processedContent.includes('>')) {
            return processedContent; // Return HTML string
          }
        }
        
        console.warn('AI did not return valid structured data or HTML, falling back to default rendering');
        return null;
      } else {
        throw new Error(`AI endpoint returned status ${response.status}`);
      }
    } catch (error) {
      console.error('Error processing content with AI:', error);
      return null;
    } finally {
      setLoadingAiContent(false);
    }
  };
  
  // Removed - deliverables functionality now in content tab
  
  // Render structured content in a user-friendly way with better formatting
  const renderStructuredContent = (content: any) => {
    if (!content) return null;

    // Check if this is a string that might be HTML or markdown
    if (typeof content === 'string') {
      // If it looks like HTML, render it as HTML
      if (content.includes('<') && content.includes('>')) {
        return (
          <div 
            className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        );
      }
      // Otherwise render as formatted text
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

    // Enhanced rendering for object content
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
            return (
              <div key={key} className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-3 capitalize text-lg">
                  {key.replace(/_/g, ' ')}
                </h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              </div>
            );
          }
          return null;
        })}
      </div>
    );
  };

  // Simplified - no tabs needed anymore
  // const mainTabs = [{ id: 'components', label: 'Components', icon: '🔧', description: 'Asset management & analysis' }];
  
  const assetViewTabs = [
    { id: 'content', label: 'Content', icon: '📄', description: 'AI-enhanced view' },
    { id: 'history', label: 'Version History', icon: '📜', description: 'Cronologia modifiche' },
    { id: 'dependencies', label: 'Dependencies', icon: '🕸️', description: 'Relazioni asset' },
    { id: 'impact', label: 'Impact Analysis', icon: '🎯', description: 'Predizioni AI' },
    { id: 'feedback', label: 'Feedback', icon: '💬', description: 'Asset-specific feedback' }
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

  // Unified loading and error handling is now handled within each tab

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Project Assets</h1>
              <p className="text-gray-600 mt-1">
                Complete asset management with AI content, versioning, dependencies, impact analysis, and feedback workflow
              </p>
            </div>
          </div>

          {/* Simplified - no tabs needed */}
          <div className="border-b border-gray-200">
            <div className="flex items-center space-x-2 py-4">
              <span className="text-lg">🔧</span>
              <span className="font-medium text-blue-600">Components</span>
              <span className="text-xs text-gray-400">Asset management & analysis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Asset Management Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Components - Asset Management */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Asset List */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">Project Assets</h2>
                  <p className="text-sm text-gray-600">Select an asset to analyze</p>
                </div>
                
                <div className="p-6">
                  {assetsLoading || tasksLoading ? (
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
                  )}

                  {assets.length === 0 && !assetsLoading && !tasksLoading && (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-4">📦</div>
                      <p>No assets found</p>
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
                        <p className="text-sm text-gray-600 capitalize">
                          {selectedAsset.type} • {selectedAsset.versions} versions available
                        </p>
                      </div>
                    </div>

                    {/* Asset View Tabs */}
                    <div className="border-b border-gray-200 mb-6">
                      <div className="flex space-x-6">
                        {assetViewTabs.map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setAssetViewTab(tab.id as 'content' | 'history' | 'dependencies' | 'impact' | 'feedback')}
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
                        {loadingEnhanced ? (
                          <div className="flex flex-col items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                            <span className="text-gray-600 font-medium">Loading asset content...</span>
                          </div>
                        ) : enhancedContent ? (
                          <div className="p-6">
                            {/* Enhanced Summary with better rendering */}
                            {enhancedContent.visual_summary && (
                              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                                <h3 className="text-lg font-semibold mb-2 text-blue-800">📋 Summary</h3>
                                <div className="text-blue-700 leading-relaxed whitespace-pre-wrap">
                                  {enhancedContent.visual_summary}
                                </div>
                              </div>
                            )}

                            {/* Enhanced Content Rendering */}
                            {enhancedContent.content && enhancedContent.content !== enhancedContent.visual_summary && (
                              <div className="mb-6">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900">📄 Full Content</h3>
                                <div className="bg-white p-6 rounded-lg border border-gray-200">
                                  <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                    {enhancedContent.content}
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* Pre-rendered HTML */}
                            {enhancedContent.structured_content?.rendered_html && (
                              <div className="mb-6">
                                <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
                                  <h3 className="text-lg font-semibold text-green-800 mb-2">⚡ Ready-to-View Content</h3>
                                  <p className="text-green-700 text-sm">Pre-formatted by AI during creation</p>
                                </div>
                                <div 
                                  className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200 ai-enhanced-content"
                                  dangerouslySetInnerHTML={{ __html: enhancedContent.structured_content.rendered_html }}
                                  style={{
                                    '--tw-prose-headings': '#1f2937',
                                    '--tw-prose-body': '#374151',
                                    '--tw-prose-bold': '#111827',
                                    '--tw-prose-links': '#2563eb',
                                    '--tw-prose-pre-bg': '#f3f4f6',
                                    '--tw-prose-th-borders': '#d1d5db',
                                    '--tw-prose-td-borders': '#e5e7eb',
                                  } as React.CSSProperties}
                                />
                              </div>
                            )}

                            {/* AI-Generated Content */}
                            {!enhancedContent.structured_content?.rendered_html && loadingAiContent && (
                              <div className="mb-6 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                                <div className="flex items-center">
                                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                                  <span className="text-blue-700 font-medium">🤖 AI is generating beautiful content...</span>
                                </div>
                              </div>
                            )}
                            
                            {!enhancedContent.structured_content?.rendered_html && aiProcessedContent && (
                              <div className="mb-6">
                                <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg mb-4">
                                  <h3 className="text-lg font-semibold text-purple-800 mb-2">🤖 AI-Enhanced Presentation</h3>
                                  <p className="text-purple-700 text-sm">Content processed and beautifully formatted by AI</p>
                                </div>
                                
                                {/* Check if aiProcessedContent is structured data or HTML */}
                                {typeof aiProcessedContent === 'object' && aiProcessedContent.has_structured_content ? (
                                  <StructuredAssetRenderer 
                                    data={aiProcessedContent}
                                  />
                                ) : typeof aiProcessedContent === 'object' && aiProcessedContent.rendered_html ? (
                                  <div 
                                    className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200 ai-enhanced-content"
                                    dangerouslySetInnerHTML={{ __html: aiProcessedContent.rendered_html }}
                                    style={{
                                      '--tw-prose-headings': '#1f2937',
                                      '--tw-prose-body': '#374151',
                                      '--tw-prose-bold': '#111827',
                                      '--tw-prose-links': '#2563eb',
                                      '--tw-prose-pre-bg': '#f3f4f6',
                                      '--tw-prose-th-borders': '#d1d5db',
                                      '--tw-prose-td-borders': '#e5e7eb',
                                    } as React.CSSProperties}
                                  />
                                ) : typeof aiProcessedContent === 'string' ? (
                                  <div 
                                    className="prose prose-lg max-w-none bg-white p-6 rounded-lg border border-gray-200 ai-enhanced-content"
                                    dangerouslySetInnerHTML={{ __html: aiProcessedContent }}
                                    style={{
                                      '--tw-prose-headings': '#1f2937',
                                      '--tw-prose-body': '#374151',
                                      '--tw-prose-bold': '#111827',
                                      '--tw-prose-links': '#2563eb',
                                      '--tw-prose-pre-bg': '#f3f4f6',
                                      '--tw-prose-th-borders': '#d1d5db',
                                      '--tw-prose-td-borders': '#e5e7eb',
                                    } as React.CSSProperties}
                                  />
                                ) : (
                                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                                      {JSON.stringify(aiProcessedContent, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}
                            
                            {/* Structured Content with Advanced Rendering */}
                            {!enhancedContent.structured_content?.rendered_html && !aiProcessedContent && !loadingAiContent && enhancedContent.structured_content && (
                              <div className="mb-6">
                                <h3 className="text-lg font-semibold mb-4">📊 Analysis Results</h3>
                                {enhancedContent.structured_content.tables || enhancedContent.structured_content.cards || 
                                 enhancedContent.structured_content.metrics || enhancedContent.structured_content.timelines ? (
                                  <StructuredContentRenderer 
                                    elements={enhancedContent.structured_content}
                                    rawData={enhancedContent.structured_content}
                                  />
                                ) : enhancedContent.structured_content.has_structured_content ? (
                                  <StructuredAssetRenderer 
                                    data={enhancedContent.structured_content}
                                  />
                                ) : (
                                  renderStructuredContent(enhancedContent.structured_content)
                                )}
                              </div>
                            )}
                            
                            {/* Key Insights */}
                            {enhancedContent.key_insights && enhancedContent.key_insights.length > 0 && (
                              <div className="mb-6">
                                <h3 className="text-lg font-semibold mb-4">💡 Key Insights</h3>
                                <ul className="list-disc list-inside space-y-2">
                                  {enhancedContent.key_insights.map((insight: string, index: number) => (
                                    <li key={index} className="text-gray-700">{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {/* Raw Data Toggle */}
                            {enhancedContent.structured_content && (
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
                                    {JSON.stringify(enhancedContent.structured_content, null, 2)}
                                  </pre>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="p-12 text-center">
                            <div className="text-gray-400 text-4xl mb-4">📄</div>
                            <p className="text-gray-600">No content available for this asset</p>
                          </div>
                        )}
                      </div>
                    )}

                    {assetViewTab === 'history' && (
                      <AssetHistoryPanel
                        assetId={selectedAsset.sourceTaskId || selectedAssetId}
                        workspaceId={workspaceId}
                        className="shadow-sm"
                      />
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
                              business_value: 85
                            },
                            {
                              id: 'related-1',
                              name: 'Market Research Data',
                              type: 'data',
                              category: 'research',
                              status: 'updated',
                              last_updated: '2024-01-14',
                              size: 'large',
                              business_value: 75
                            },
                            {
                              id: 'related-2',
                              name: 'Customer Feedback',
                              type: 'feedback',
                              category: 'research',
                              status: 'stale',
                              last_updated: '2024-01-10',
                              size: 'small',
                              business_value: 60
                            }
                          ]}
                          edges={[
                            {
                              source: selectedAsset.id,
                              target: 'related-1',
                              impact: 'high',
                              relationship_type: 'depends_on',
                              strength: 0.8
                            },
                            {
                              source: selectedAsset.id,
                              target: 'related-2',
                              impact: 'medium',
                              relationship_type: 'influences',
                              strength: 0.6
                            }
                          ]}
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