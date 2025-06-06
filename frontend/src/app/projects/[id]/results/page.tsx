'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useProjectResults, UnifiedResultItem } from '@/hooks/useProjectResults';
import { UnifiedResultCard } from '@/components/UnifiedResultCard';

type FilterType = 'all' | 'readyToUse' | 'inProgress' | 'final';
type SortType = 'impact' | 'actionability' | 'recent' | 'alphabetical';

export default function ProjectResultsPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  // Get filter from URL params
  const searchParams = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
  const urlFilter = searchParams.get('filter') as FilterType;
  
  const {
    allResults,
    readyToUse,
    inProgress,
    finalDeliverables,
    totalResults,
    completionRate,
    qualityScore,
    loading,
    error,
    lastUpdated,
    refresh: refreshResults
  } = useProjectResults(projectId);

  const [activeFilter, setActiveFilter] = useState<FilterType>(urlFilter || 'all');
  const [sortBy, setSortBy] = useState<SortType>('impact');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResult, setSelectedResult] = useState<UnifiedResultItem | null>(null);
  const [enhancedContent, setEnhancedContent] = useState<any>(null);
  const [loadingEnhanced, setLoadingEnhanced] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  const [aiProcessedContent, setAiProcessedContent] = useState<string | null>(null);
  const [loadingAiContent, setLoadingAiContent] = useState(false);

  // Function to process structured content with AI for rich rendering
  const processWithAI = async (structuredContent: any, taskTitle: string) => {
    if (!structuredContent) return null;
    
    setLoadingAiContent(true);
    try {
      // First try the real AI endpoint
      const response = await fetch(`http://localhost:8000/ai/process-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: structuredContent,
          title: taskTitle,
          format: 'html',
          instructions: `Transform this structured data into a beautiful, user-friendly HTML presentation. 
                        Use appropriate headings, lists, tables, cards, and visual elements. 
                        Make it engaging and easy to read. Include proper styling classes for a professional look.
                        Focus on actionability and business value.`
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.processed_content || data.content;
      } else {
        // Fallback to preview endpoint if main endpoint fails
        console.log('Main AI endpoint failed, trying preview...');
        const previewResponse = await fetch(`http://localhost:8000/ai/process-content/preview`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: structuredContent,
            title: taskTitle,
            format: 'html'
          })
        });

        if (previewResponse.ok) {
          const previewData = await previewResponse.json();
          return previewData.processed_content;
        }
      }
    } catch (error) {
      console.error('Error processing content with AI:', error);
      
      // Final fallback - generate basic HTML client-side
      return generateBasicHTML(structuredContent, taskTitle);
    } finally {
      setLoadingAiContent(false);
    }
    return null;
  };

  // Client-side fallback for basic HTML generation
  const generateBasicHTML = (content: any, title: string) => {
    let html = `<div class="space-y-6">`;
    html += `<div class="bg-blue-50 p-6 rounded-lg border border-blue-200">`;
    html += `<h1 class="text-2xl font-bold text-blue-900 mb-3">📊 ${title}</h1>`;
    html += `<p class="text-blue-700">AI-processed content (using fallback formatting)</p>`;
    html += `</div>`;
    
    // Generate basic cards for each major content section
    Object.keys(content).forEach(key => {
      const value = content[key];
      if (typeof value === 'object' && value !== null) {
        html += `<div class="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">`;
        html += `<h2 class="text-lg font-bold text-gray-900 mb-3">${key.replace(/_/g, ' ').toUpperCase()}</h2>`;
        
        if (Array.isArray(value)) {
          html += `<ul class="space-y-2">`;
          value.slice(0, 3).forEach(item => {
            if (typeof item === 'string') {
              html += `<li class="text-gray-700">• ${item}</li>`;
            } else if (typeof item === 'object') {
              html += `<li class="text-gray-700">• ${JSON.stringify(item).substring(0, 100)}...</li>`;
            }
          });
          html += `</ul>`;
        } else {
          html += `<p class="text-gray-700">${JSON.stringify(value).substring(0, 200)}...</p>`;
        }
        
        html += `</div>`;
      }
    });
    
    html += `</div>`;
    return html;
  };

  // Function to fetch enhanced content when viewing details
  const handleViewDetails = async (result: UnifiedResultItem) => {
    setSelectedResult(result);
    setLoadingEnhanced(true);
    setEnhancedContent(null);
    setAiProcessedContent(null);

    try {
      // Get all workspace tasks to find the one with detailed results
      const tasksResponse = await fetch(`http://localhost:8000/monitoring/workspace/${projectId}/tasks`);
      if (tasksResponse.ok) {
        const tasksData = await tasksResponse.json();
        console.log('📋 All workspace tasks:', tasksData);
        
        // Find the specific task
        const task = tasksData.tasks?.find((t: any) => t.id === result.sourceTaskId);
        if (task) {
          console.log('🎯 Found specific task:', task);
          
          // Try to extract detailed_results_json from the task
          let detailedResults = null;
          if (task.result?.detailed_results_json) {
            try {
              detailedResults = JSON.parse(task.result.detailed_results_json);
              console.log('✅ Parsed detailed_results_json from task:', detailedResults);
            } catch (e) {
              console.warn('Failed to parse detailed_results_json from task:', e);
            }
          }
          
          if (detailedResults) {
            const enhancedContent = {
              visual_summary: task.result?.summary || `📋 ${result.title}`,
              content: task.result?.summary || result.description,
              structured_content: detailedResults,
              key_insights: detailedResults.actionable_insights || detailedResults.key_insights || result.keyInsights || [],
              business_impact: result.businessImpact,
              actionability_score: result.actionabilityScore,
              agent_details: {
                name: result.agentName,
                role: result.agentRole
              },
              task_metadata: {
                source_task_id: result.sourceTaskId,
                last_updated: result.lastUpdated
              }
            };
            setEnhancedContent(enhancedContent);
            
            // Check if we already have pre-rendered HTML
            if (detailedResults.rendered_html) {
              console.log('✅ Found pre-rendered HTML, using directly');
              // HTML is already included in enhancedContent.structured_content
              return;
            }
            
            // Fallback: Process the structured content with AI for rich rendering
            const aiContent = await processWithAI(detailedResults, result.title);
            if (aiContent) {
              setAiProcessedContent(aiContent);
            }
            return;
          }
        }
      }
      
      // Fallback to enhanced endpoint
      const enhancedResponse = await fetch(`http://localhost:8000/projects/${projectId}/task/${result.sourceTaskId}/enhanced-result`);
      if (enhancedResponse.ok) {
        const enhanced = await enhancedResponse.json();
        setEnhancedContent(enhanced);
      } else {
        console.log('No detailed data available, using basic fallback');
        
        // Create basic fallback content
        const fallbackContent = {
          visual_summary: `📋 ${result.title}`,
          content: result.description,
          structured_content: result.structuredContent,
          key_insights: result.keyInsights || [],
          business_impact: result.businessImpact,
          actionability_score: result.actionabilityScore,
          agent_details: {
            name: result.agentName,
            role: result.agentRole
          }
        };
        
        setEnhancedContent(fallbackContent);
      }
    } catch (error) {
      console.error('Error fetching enhanced content:', error);
      // Create rich fallback content even on error
      const fallbackContent = {
        visual_summary: `📋 ${result.title}`,
        content: result.description,
        structured_content: result.structuredContent,
        key_insights: result.keyInsights || [],
        business_impact: result.businessImpact,
        actionability_score: result.actionabilityScore
      };
      setEnhancedContent(fallbackContent);
    } finally {
      setLoadingEnhanced(false);
    }
  };

  // Export functions
  const exportSingleResult = (result: UnifiedResultItem, format: 'json' | 'txt' | 'md') => {
    let content = '';
    let filename = '';
    let mimeType = '';

    switch (format) {
      case 'json':
        content = JSON.stringify({
          title: result.title,
          description: result.description,
          type: result.type,
          businessImpact: result.businessImpact,
          actionabilityScore: result.actionabilityScore,
          keyInsights: result.keyInsights,
          nextActions: result.nextActions,
          structuredContent: result.structuredContent,
          sourceTaskId: result.sourceTaskId,
          agentName: result.agentName,
          lastUpdated: result.lastUpdated
        }, null, 2);
        filename = `${result.title.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
        mimeType = 'application/json';
        break;
      
      case 'md':
        content = `# ${result.title}\n\n`;
        content += `**Type:** ${result.type}\n`;
        content += `**Business Impact:** ${result.businessImpact}\n`;
        content += `**Actionability:** ${result.actionabilityScore}%\n\n`;
        content += `## Description\n${result.description}\n\n`;
        
        if (result.keyInsights && result.keyInsights.length > 0) {
          content += `## Key Insights\n`;
          result.keyInsights.forEach(insight => content += `- ${insight}\n`);
          content += '\n';
        }
        
        if (result.nextActions && result.nextActions.length > 0) {
          content += `## Next Actions\n`;
          result.nextActions.forEach(action => content += `- ${action}\n`);
          content += '\n';
        }
        
        filename = `${result.title.replace(/[^a-zA-Z0-9]/g, '_')}.md`;
        mimeType = 'text/markdown';
        break;
      
      case 'txt':
        content = `${result.title}\n${'='.repeat(result.title.length)}\n\n`;
        content += `Type: ${result.type}\n`;
        content += `Business Impact: ${result.businessImpact}\n`;
        content += `Actionability: ${result.actionabilityScore}%\n\n`;
        content += `Description:\n${result.description}\n\n`;
        
        if (result.keyInsights && result.keyInsights.length > 0) {
          content += `Key Insights:\n`;
          result.keyInsights.forEach(insight => content += `• ${insight}\n`);
          content += '\n';
        }
        
        filename = `${result.title.replace(/[^a-zA-Z0-9]/g, '_')}.txt`;
        mimeType = 'text/plain';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportBulkResults = (results: UnifiedResultItem[], format: 'json') => {
    const content = JSON.stringify({
      exportDate: new Date().toISOString(),
      projectId: projectId,
      totalResults: results.length,
      results: results.map(result => ({
        title: result.title,
        description: result.description,
        type: result.type,
        businessImpact: result.businessImpact,
        actionabilityScore: result.actionabilityScore,
        keyInsights: result.keyInsights,
        nextActions: result.nextActions,
        structuredContent: result.structuredContent,
        sourceTaskId: result.sourceTaskId,
        agentName: result.agentName,
        lastUpdated: result.lastUpdated
      }))
    }, null, 2);
    
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `project_${projectId}_results_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Selection handlers
  const toggleItemSelection = (itemId: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const selectAllVisible = () => {
    const visibleIds = new Set(filteredResults.map(r => r.id));
    setSelectedItems(visibleIds);
    setShowBulkActions(visibleIds.size > 0);
  };

  const clearSelection = () => {
    setSelectedItems(new Set());
    setShowBulkActions(false);
  };

  // Render structured content in a user-friendly way
  const renderStructuredContent = (content: any) => {
    if (!content) return null;

    return (
      <div className="space-y-6">
        {/* Executive Summary */}
        {content.executive_summary && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">📋 Executive Summary</h4>
            <p className="text-blue-700">{content.executive_summary}</p>
          </div>
        )}

        {/* Competitor Analysis */}
        {content.competitor_analysis && Array.isArray(content.competitor_analysis) && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">🏆 Competitor Analysis</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {content.competitor_analysis.map((competitor: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <h5 className="font-semibold text-lg">{competitor.name}</h5>
                    <span className="ml-2 text-sm text-gray-500">{competitor.instagram_handle}</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <p><strong>Followers:</strong> {competitor.followers}</p>
                    <p><strong>Engagement:</strong> {competitor.engagement_rate}</p>
                    <p><strong>Focus:</strong> {competitor.content_focus}</p>
                    {competitor.notable_achievements && (
                      <p><strong>Achievements:</strong> {competitor.notable_achievements}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Audience Profile */}
        {content.audience_profile && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">👥 Audience Profile</h4>
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              {content.audience_profile.demographics && (
                <div>
                  <h5 className="font-medium text-gray-700">Demographics</h5>
                  <ul className="text-sm text-gray-600 mt-1">
                    {content.audience_profile.demographics.gender_distribution && (
                      <li>• Gender: {content.audience_profile.demographics.gender_distribution}</li>
                    )}
                    {content.audience_profile.demographics.age_range && (
                      <li>• Age: {content.audience_profile.demographics.age_range}</li>
                    )}
                  </ul>
                </div>
              )}
              
              {content.audience_profile.interests && (
                <div>
                  <h5 className="font-medium text-gray-700">Interests</h5>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {content.audience_profile.interests.map((interest: string, index: number) => (
                      <span key={index} className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Content Calendar/Posts */}
        {content.posts && Array.isArray(content.posts) && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">📅 Content Calendar</h4>
            <div className="space-y-3">
              {content.posts.slice(0, 5).map((post: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-2">
                    <h5 className="font-medium">{post.title || post.content_theme || `Post ${index + 1}`}</h5>
                    <span className="text-xs text-gray-500">{post.date || post.posting_date}</span>
                  </div>
                  {post.caption && (
                    <p className="text-sm text-gray-600 mb-2">{post.caption.substring(0, 100)}...</p>
                  )}
                  {post.hashtags && (
                    <div className="text-xs text-blue-600">
                      {post.hashtags.slice(0, 5).join(' ')}
                    </div>
                  )}
                </div>
              ))}
              {content.posts.length > 5 && (
                <p className="text-sm text-gray-500 text-center">
                  ...and {content.posts.length - 5} more posts
                </p>
              )}
            </div>
          </div>
        )}

        {/* Generic structured data rendering for other content types */}
        {Object.keys(content).filter(key => 
          !['executive_summary', 'competitor_analysis', 'audience_profile', 'posts', 'actionable_insights', 'key_insights'].includes(key)
        ).map(key => {
          const value = content[key];
          if (typeof value === 'object' && value !== null) {
            return (
              <div key={key}>
                <h4 className="font-semibold text-gray-800 mb-3 capitalize">
                  {key.replace(/_/g, ' ')}
                </h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
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

  const getFilteredResults = () => {
    let filtered = allResults;

    // Apply category filter
    switch (activeFilter) {
      case 'readyToUse':
        filtered = readyToUse;
        break;
      case 'inProgress':
        filtered = inProgress;
        break;
      case 'final':
        filtered = finalDeliverables;
        break;
      default:
        filtered = allResults;
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(result =>
        result.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        result.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'impact':
          const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          return impactOrder[b.businessImpact] - impactOrder[a.businessImpact];
        case 'actionability':
          return b.actionabilityScore - a.actionabilityScore;
        case 'recent':
          return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
        case 'alphabetical':
          return a.title.localeCompare(b.title);
        default:
          return 0;
      }
    });
  };

  const filteredResults = getFilteredResults();

  const getBusinessImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-48 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Results</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={refreshResults}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Custom CSS for AI-generated content */}
      <style jsx global>{`
        .ai-generated-content {
          line-height: 1.7;
        }
        .ai-generated-content h1, .ai-generated-content h2, .ai-generated-content h3 {
          color: #1f2937;
          font-weight: 600;
          margin-top: 2rem;
          margin-bottom: 1rem;
        }
        .ai-generated-content h1 {
          font-size: 1.875rem;
          border-bottom: 2px solid #e5e7eb;
          padding-bottom: 0.5rem;
        }
        .ai-generated-content h2 {
          font-size: 1.5rem;
        }
        .ai-generated-content h3 {
          font-size: 1.25rem;
        }
        .ai-generated-content ul, .ai-generated-content ol {
          margin: 1rem 0;
          padding-left: 1.5rem;
        }
        .ai-generated-content li {
          margin: 0.5rem 0;
        }
        .ai-generated-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5rem 0;
          background: white;
          border-radius: 0.5rem;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .ai-generated-content th, .ai-generated-content td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        .ai-generated-content th {
          background-color: #f9fafb;
          font-weight: 600;
          color: #374151;
        }
        .ai-generated-content .card {
          background: white;
          border-radius: 0.5rem;
          padding: 1.5rem;
          margin: 1rem 0;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          border-left: 4px solid #3b82f6;
        }
        .ai-generated-content .highlight {
          background: linear-gradient(120deg, #a7f3d0 0%, #a7f3d0 100%);
          background-repeat: no-repeat;
          background-size: 100% 0.2em;
          background-position: 0 88%;
          padding: 0.1em 0.3em;
        }
        .ai-generated-content blockquote {
          border-left: 4px solid #3b82f6;
          padding-left: 1rem;
          margin: 1.5rem 0;
          font-style: italic;
          color: #6b7280;
        }
      `}</style>
      
      <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* Navigation */}
          <div className="mb-6">
            <Link href={`/projects/${projectId}`} className="text-indigo-600 hover:underline text-sm">
              ← Back to Project
            </Link>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <Link
                href={`/projects/${projectId}`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Overview
              </Link>
              <Link
                href={`/projects/${projectId}/results`}
                className="py-2 px-1 border-b-2 border-indigo-500 font-medium text-sm text-indigo-600"
              >
                📊 Unified Results
              </Link>
              <Link
                href={`/projects/${projectId}/tasks`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Tasks
              </Link>
              <Link
                href={`/projects/${projectId}/team`}
                className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Team
              </Link>
            </nav>
          </div>

          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Project Results</h1>
              <p className="text-gray-600 mt-1">
                Unified view of all deliverables, assets, and actionable outputs
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={refreshResults}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh Results
              </button>
              
              <button
                onClick={() => exportBulkResults(filteredResults, 'json')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export All
              </button>
            </div>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{readyToUse.length}</div>
              <div className="text-sm text-green-700">Ready to Use</div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">{inProgress.length}</div>
              <div className="text-sm text-blue-700">In Progress</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600">{finalDeliverables.length}</div>
              <div className="text-sm text-purple-700">Final Deliverables</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-600">{totalResults}</div>
              <div className="text-sm text-gray-700">Total Results</div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search results..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filter */}
            <div className="flex gap-2">
              {[
                { key: 'all', label: 'All Results' },
                { key: 'readyToUse', label: 'Ready to Use' },
                { key: 'inProgress', label: 'In Progress' },
                { key: 'final', label: 'Final' }
              ].map(filter => (
                <button
                  key={filter.key}
                  onClick={() => setActiveFilter(filter.key as FilterType)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    activeFilter === filter.key
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortType)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="impact">Business Impact</option>
              <option value="actionability">Actionability</option>
              <option value="recent">Most Recent</option>
              <option value="alphabetical">Alphabetical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {showBulkActions && (
        <div className="bg-indigo-50 border-y border-indigo-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-indigo-700 font-medium">
                  {selectedItems.size} items selected
                </span>
                <button
                  onClick={clearSelection}
                  className="ml-4 text-indigo-600 hover:text-indigo-800 text-sm underline"
                >
                  Clear selection
                </button>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const selectedResults = filteredResults.filter(r => selectedItems.has(r.id));
                    exportBulkResults(selectedResults, 'json');
                  }}
                  className="px-3 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export Selected
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selection Controls */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        {filteredResults.length > 0 && (
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={selectAllVisible}
                className="text-sm text-gray-600 hover:text-gray-800 flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Select All ({filteredResults.length})
              </button>
              
              {selectedItems.size > 0 && (
                <span className="text-sm text-indigo-600">
                  {selectedItems.size} selected
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Results Grid */}
      <div className="max-w-7xl mx-auto px-6 pb-6">
        {filteredResults.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
            <p className="text-gray-600">
              {searchQuery
                ? 'Try adjusting your search terms or filters.'
                : 'No results match the current filter.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResults.map((result) => (
              <UnifiedResultCard
                key={result.id}
                result={result}
                onViewDetails={handleViewDetails}
                isSelected={selectedItems.has(result.id)}
                onToggleSelection={toggleItemSelection}
                onExport={exportSingleResult}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedResult.title}
                  </h2>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded-full ${getBusinessImpactColor(selectedResult.businessImpact)}`}>
                      {selectedResult.businessImpact.toUpperCase()} Impact
                    </span>
                    <span className="text-gray-600">
                      Actionability: {selectedResult.actionabilityScore}%
                    </span>
                    <span className="text-gray-600">
                      Validation: {selectedResult.validationScore}%
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSelectedResult(null);
                    setEnhancedContent(null);
                    setLoadingEnhanced(false);
                  }}
                  className="ml-4 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {loadingEnhanced ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Loading detailed content...</span>
                </div>
              ) : (
                <div className="prose max-w-none">
                  {enhancedContent ? (
                    <div>
                      {/* Enhanced Rich Content */}
                      {enhancedContent.visual_summary && (
                        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                          <h3 className="text-lg font-semibold mb-2 text-blue-800">📋 Summary</h3>
                          <p className="text-blue-700">{enhancedContent.visual_summary}</p>
                        </div>
                      )}
                      
                      {/* Pre-rendered HTML (NEW: Direct from backend) */}
                      {enhancedContent.structured_content?.rendered_html && (
                        <div className="mb-6">
                          <div className="bg-gradient-to-r from-green-100 to-blue-100 p-4 rounded-lg mb-4">
                            <div className="flex justify-between items-center">
                              <div>
                                <h3 className="text-lg font-semibold text-green-800 mb-2">⚡ Ready-to-View Content</h3>
                                <p className="text-green-700 text-sm">Pre-formatted by AI during creation - zero delay</p>
                              </div>
                              <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">Instant</span>
                            </div>
                          </div>
                          <div 
                            className="prose prose-lg max-w-none ai-generated-content"
                            dangerouslySetInnerHTML={{ __html: enhancedContent.structured_content.rendered_html }}
                            style={{
                              '--tw-prose-headings': '#1f2937',
                              '--tw-prose-lead': '#4b5563',
                              '--tw-prose-links': '#3b82f6',
                              '--tw-prose-bold': '#1f2937',
                              '--tw-prose-counters': '#6b7280',
                              '--tw-prose-bullets': '#d1d5db',
                              '--tw-prose-hr': '#e5e7eb',
                              '--tw-prose-quotes': '#6b7280',
                              '--tw-prose-quote-borders': '#e5e7eb',
                              '--tw-prose-captions': '#6b7280',
                              '--tw-prose-code': '#1f2937',
                              '--tw-prose-pre-code': '#e5e7eb',
                              '--tw-prose-pre-bg': '#1f2937',
                              '--tw-prose-th-borders': '#d1d5db',
                              '--tw-prose-td-borders': '#e5e7eb'
                            } as React.CSSProperties}
                          />
                        </div>
                      )}

                      {/* AI-Generated Rich Content (Fallback for older content) */}
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
                            <div className="flex justify-between items-center">
                              <div>
                                <h3 className="text-lg font-semibold text-purple-800 mb-2">🤖 AI-Enhanced Presentation</h3>
                                <p className="text-purple-700 text-sm">Content processed and beautifully formatted by AI</p>
                              </div>
                              <button
                                onClick={async () => {
                                  const newContent = await processWithAI(enhancedContent.structured_content, selectedResult.title);
                                  if (newContent) setAiProcessedContent(newContent);
                                }}
                                disabled={loadingAiContent}
                                className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm flex items-center"
                              >
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Regenerate
                              </button>
                            </div>
                          </div>
                          <div 
                            className="prose prose-lg max-w-none ai-generated-content"
                            dangerouslySetInnerHTML={{ __html: aiProcessedContent }}
                            style={{
                              '--tw-prose-headings': '#1f2937',
                              '--tw-prose-lead': '#4b5563',
                              '--tw-prose-links': '#3b82f6',
                              '--tw-prose-bold': '#1f2937',
                              '--tw-prose-counters': '#6b7280',
                              '--tw-prose-bullets': '#d1d5db',
                              '--tw-prose-hr': '#e5e7eb',
                              '--tw-prose-quotes': '#6b7280',
                              '--tw-prose-quote-borders': '#e5e7eb',
                              '--tw-prose-captions': '#6b7280',
                              '--tw-prose-code': '#1f2937',
                              '--tw-prose-pre-code': '#e5e7eb',
                              '--tw-prose-pre-bg': '#1f2937',
                              '--tw-prose-th-borders': '#d1d5db',
                              '--tw-prose-td-borders': '#e5e7eb'
                            } as React.CSSProperties}
                          />
                        </div>
                      )}
                      
                      {/* Fallback: Manual Structured Content Rendering (only if no pre-rendered HTML and AI processing fails) */}
                      {!enhancedContent.structured_content?.rendered_html && !aiProcessedContent && !loadingAiContent && enhancedContent.structured_content && (
                        <div className="mb-6">
                          <h3 className="text-lg font-semibold mb-4">📊 Analysis Results</h3>
                          {renderStructuredContent(enhancedContent.structured_content)}
                        </div>
                      )}
                      
                      {/* Raw Structured Data (Collapsible) */}
                      {enhancedContent.structured_content && (
                        <div className="mb-6">
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
                      
                      {/* Key Insights from enhanced content */}
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
                    </div>
                  ) : (
                    /* Fallback to basic content */
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Description</h3>
                      <p className="text-gray-700 mb-6">{selectedResult.description}</p>
                      
                      {selectedResult.keyInsights && selectedResult.keyInsights.length > 0 && (
                        <>
                          <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
                          <ul className="list-disc list-inside space-y-2 mb-6">
                            {selectedResult.keyInsights.map((insight, index) => (
                              <li key={index} className="text-gray-700">{insight}</li>
                            ))}
                          </ul>
                        </>
                      )}
                      
                      {selectedResult.nextActions && selectedResult.nextActions.length > 0 && (
                        <>
                          <h3 className="text-lg font-semibold mb-4">Recommended Actions</h3>
                          <ul className="list-disc list-inside space-y-2 mb-6">
                            {selectedResult.nextActions.map((action, index) => (
                              <li key={index} className="text-gray-700">{action}</li>
                            ))}
                          </ul>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              <div className="flex justify-between items-center mt-6 pt-6 border-t border-gray-200">
                <div className="flex gap-2">
                  {enhancedContent && (
                    <>
                      <button
                        onClick={() => {
                          const content = JSON.stringify(enhancedContent, null, 2);
                          const blob = new Blob([content], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `${selectedResult.title.replace(/[^a-zA-Z0-9]/g, '_')}_enhanced.json`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          URL.revokeObjectURL(url);
                        }}
                        className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                      >
                        📄 Export Enhanced
                      </button>
                      
                      <button
                        onClick={() => {
                          const contentStr = enhancedContent.content || enhancedContent.visual_summary || selectedResult.description;
                          navigator.clipboard.writeText(contentStr);
                        }}
                        className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                      >
                        📋 Copy
                      </button>
                    </>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setSelectedResult(null);
                      setEnhancedContent(null);
                      setLoadingEnhanced(false);
                    }}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Close
                  </button>
                  {selectedResult.readyToUse && (
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                      Use This Result
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}