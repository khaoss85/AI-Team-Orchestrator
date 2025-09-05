'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Settings, Plus, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'
import KnowledgeInsightManager from '../knowledge/KnowledgeInsightManager'
import ReactMarkdown from 'react-markdown'

interface KnowledgeInsightsArtifactProps {
  knowledgeData: {
    insights?: any[]
    bestPractices?: any[]
    learnings?: any[]
    summary?: {
      recent_discoveries?: string[]
      key_constraints?: string[]
      success_patterns?: string[]
      top_tags?: string[]
    }
  } | null | undefined
  workspaceId: string
  currentUserId?: string
  onInsightAction?: (action: string, insight: any) => void
  onRefreshKnowledge?: () => Promise<void>
}

export default function KnowledgeInsightsArtifact({ 
  knowledgeData, 
  workspaceId,
  currentUserId = 'default_user',
  onInsightAction,
  onRefreshKnowledge
}: KnowledgeInsightsArtifactProps) {
  const [activeSection, setActiveSection] = useState<'insights' | 'practices' | 'learnings' | 'summary' | 'manage'>('insights')
  const [managementMode, setManagementMode] = useState(false)

  // Debug logging
  React.useEffect(() => {
    console.log('🎯 [KnowledgeInsightsArtifact] Component mounted with data:', {
      knowledgeDataReceived: !!knowledgeData,
      insights: knowledgeData?.insights?.length || 0,
      bestPractices: knowledgeData?.bestPractices?.length || 0,
      learnings: knowledgeData?.learnings?.length || 0,
      summary: knowledgeData?.summary,
      workspaceId: workspaceId
    })
  }, [knowledgeData, workspaceId])

  const { insights, bestPractices, learnings, summary } = knowledgeData || {
    insights: [],
    bestPractices: [],
    learnings: [],
    summary: {}
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case 'success_pattern': return '✅'
      case 'failure_lesson': return '⚠️'
      case 'discovery': return '🔍'
      case 'constraint': return '🚧'
      case 'optimization': return '⚡'
      default: return '💡'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  // Handle case where knowledge data is not available
  if (!knowledgeData) {
    console.warn('⚠️ [KnowledgeInsightsArtifact] No knowledge data provided')
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-3xl mb-3">💡</div>
          <div className="text-lg font-medium mb-2">Loading Knowledge Base...</div>
          <div className="text-sm text-gray-600">
            Knowledge insights will appear here once loaded
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with management toggle */}
      <div className="flex items-center justify-between p-4">
        <h2 className="text-lg font-semibold text-gray-900">Knowledge Base</h2>
        <div className="flex items-center space-x-2">
          {onRefreshKnowledge && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefreshKnowledge}
              className="flex items-center space-x-1"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </Button>
          )}
          <Button
            variant={managementMode ? "default" : "outline"}
            size="sm"
            onClick={() => setManagementMode(!managementMode)}
            className="flex items-center space-x-1"
          >
            {managementMode ? (
              <>
                <Settings className="w-4 h-4" />
                <span>Exit Management</span>
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>Manage Insights</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Management Mode */}
      {managementMode ? (
        <div className="border rounded-lg p-6 bg-gray-50 mt-4">
          <KnowledgeInsightManager 
            workspaceId={workspaceId}
            currentUserId={currentUserId}
          />
        </div>
      ) : (
        /* Original Knowledge View */
        <>
          {/* Navigation Tabs */}
          <div className="flex space-x-2 border-b pb-4 px-4">
            <SectionTab 
              active={activeSection === 'insights'} 
              onClick={() => setActiveSection('insights')}
              label="Insights"
              count={insights?.length || 0}
              icon="💡"
            />
            <SectionTab 
              active={activeSection === 'practices'} 
              onClick={() => setActiveSection('practices')}
              label="Best Practices" 
              count={bestPractices?.length || 0}
              icon="⭐"
            />
            <SectionTab 
              active={activeSection === 'learnings'} 
              onClick={() => setActiveSection('learnings')}
              label="Learnings"
              count={learnings?.length || 0}
              icon="📚"
            />
            <SectionTab 
              active={activeSection === 'summary'} 
              onClick={() => setActiveSection('summary')}
              label="Summary"
              icon="📊"
            />
          </div>

          {/* Content Sections */}
          <div className="px-4">
            {activeSection === 'insights' && (
              <InsightSection 
                title="💡 Insights & Discoveries" 
                items={insights || []} 
                onInsightAction={onInsightAction}
              />
            )}

            {activeSection === 'practices' && (
              <InsightSection 
                title="⭐ Best Practices" 
                items={bestPractices || []}
                onInsightAction={onInsightAction}
              />
            )}

            {activeSection === 'learnings' && (
              <InsightSection 
                title="📚 Learnings & Constraints" 
                items={learnings || []}
                onInsightAction={onInsightAction}
              />
            )}

            {activeSection === 'summary' && (
              <SummaryView summary={summary} />
            )}
          </div>
        </>
      )}

      {/* AI Status Indicator */}
      {knowledgeData.ai_enabled && (
        <div className="flex items-center justify-center p-2 bg-blue-50 rounded-lg mx-4">
          <div className="flex items-center space-x-2 text-sm text-blue-700">
            <span>🤖</span>
            <span>AI-driven semantic categorization active</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Section Tab Component
interface SectionTabProps {
  active: boolean
  onClick: () => void
  label: string
  count?: number
  icon: string
}

function SectionTab({ active, onClick, label, count, icon }: SectionTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors
        ${active
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }
      `}
    >
      <span>{icon}</span>
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span className={`
          text-xs px-1.5 py-0.5 rounded-full
          ${active ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-700'}
        `}>
          {count}
        </span>
      )}
    </button>
  )
}

// Insights List Component
interface InsightsListProps {
  items: any[]
  title: string
  emptyMessage: string
  onInsightAction?: (action: string, insight: any) => void
}

function InsightsList({ items, title, emptyMessage, onInsightAction }: InsightsListProps) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📭</div>
        <div className="text-lg font-medium text-gray-600 mb-2">{title}</div>
        <div className="text-sm text-gray-500 max-w-md mx-auto">
          {emptyMessage}
        </div>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case 'success_pattern': return '✅'
      case 'failure_lesson': return '⚠️'
      case 'discovery': return '🔍'
      case 'constraint': return '🚧'
      case 'optimization': return '⚡'
      default: return '💡'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{getInsightTypeIcon(item.type)}</span>
                <div className="text-sm text-gray-600">
                  {item.type?.replace('_', ' ') || 'Insight'}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {item.confidence && (
                  <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(item.confidence)}`}>
                    {Math.round(item.confidence * 100)}% confidence
                  </span>
                )}
                <div className="text-xs text-gray-500">
                  {formatDate(item.created_at)}
                </div>
              </div>
            </div>

            <div className="text-sm text-gray-900 mb-3">
              {item.content}
            </div>

            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {item.tags.slice(0, 5).map((tag: string) => (
                  <span key={tag} className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                    {tag}
                  </span>
                ))}
                {item.tags.length > 5 && (
                  <span className="text-xs text-gray-500">
                    +{item.tags.length - 5} more
                  </span>
                )}
              </div>
            )}

            {onInsightAction && (
              <div className="flex space-x-2 pt-2 border-t">
                <button
                  onClick={() => onInsightAction('apply', item)}
                  className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
                >
                  Apply Learning
                </button>
                <button
                  onClick={() => onInsightAction('similar', item)}
                  className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                >
                  Find Similar
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Insight Section Component
interface InsightSectionProps {
  title: string
  items: any[]
  onInsightAction?: (action: string, insight: any) => void
}

function InsightSection({ title, items, onInsightAction }: InsightSectionProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const [confidenceFilter, setConfidenceFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case 'success_pattern': return '✅'
      case 'failure_lesson': return '⚠️'
      case 'discovery': return '🔍'
      case 'constraint': return '🚧'
      case 'optimization': return '⚡'
      default: return '💡'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }

  const getItemTitle = (item: any) => {
    // Try to extract title from various sources
    if (item.title) {
      return item.title
    }
    
    // Try to parse title from content if it's JSON
    if (typeof item.content === 'string') {
      try {
        const parsed = JSON.parse(item.content)
        if (parsed.title) {
          return parsed.title
        }
      } catch {}
    }
    
    // Fallback: create a title from the first 60 chars of content
    const contentStr = typeof item.content === 'string' ? item.content : JSON.stringify(item.content)
    const firstLine = contentStr.split('\n')[0]
    if (firstLine.length <= 60) {
      return firstLine
    }
    return firstLine.substring(0, 57) + '...'
  }

  const getItemContent = (item: any) => {
    // Extract the full content from various sources
    if (typeof item.content === 'string') {
      try {
        const parsed = JSON.parse(item.content)
        if (parsed.learning) {
          return parsed.learning
        }
        if (parsed.content) {
          return parsed.content
        }
      } catch {}
      return item.content
    }
    return JSON.stringify(item.content, null, 2)
  }

  // Filter items based on confidence level
  const filteredItems = items?.filter((item) => {
    if (confidenceFilter === 'all') return true
    
    const confidence = item.confidence || 0
    if (confidenceFilter === 'high') return confidence >= 0.7
    if (confidenceFilter === 'medium') return confidence >= 0.5 && confidence < 0.7
    if (confidenceFilter === 'low') return confidence < 0.5
    
    return true
  }) || []

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📭</div>
        <div className="text-lg font-medium text-gray-600 mb-2">{title}</div>
        <div className="text-sm text-gray-500">
          No items available yet. Check back as your team makes progress.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        {/* Confidence Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Confidence:</span>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setConfidenceFilter('all')}
              className={`px-2 py-1 text-xs rounded-lg transition-colors ${
                confidenceFilter === 'all'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              📊 All ({items.length})
            </button>
            <button
              onClick={() => setConfidenceFilter('high')}
              className={`px-2 py-1 text-xs rounded-lg transition-colors ${
                confidenceFilter === 'high'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🟢 High (≥70%)
            </button>
            <button
              onClick={() => setConfidenceFilter('medium')}
              className={`px-2 py-1 text-xs rounded-lg transition-colors ${
                confidenceFilter === 'medium'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🟡 Medium (50-69%)
            </button>
            <button
              onClick={() => setConfidenceFilter('low')}
              className={`px-2 py-1 text-xs rounded-lg transition-colors ${
                confidenceFilter === 'low'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🔴 Low (&lt;50%)
            </button>
          </div>
        </div>
      </div>
      
      {filteredItems.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <div className="text-gray-500">
            No insights match the selected confidence filter.
          </div>
          <button
            onClick={() => setConfidenceFilter('all')}
            className="mt-2 text-sm text-blue-600 hover:text-blue-700"
          >
            Show all insights
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const isExpanded = expandedItems.has(item.id)
            const itemTitle = getItemTitle(item)
            const itemContent = getItemContent(item)
            
            return (
              <div key={item.id} className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-2 flex-1">
                    <button
                      onClick={() => toggleExpanded(item.id)}
                      className="mt-0.5 text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                    <span className="text-lg">{getInsightTypeIcon(item.type)}</span>
                    <div className="flex-1">
                      <button
                        onClick={() => toggleExpanded(item.id)}
                        className="text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors text-left"
                      >
                        {itemTitle}
                      </button>
                      <div className="text-xs text-gray-600 mt-1">
                        {item.type?.replace('_', ' ') || 'Insight'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {item.confidence && (
                      <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(item.confidence)}`}>
                        {Math.round(item.confidence * 100)}% confidence
                      </span>
                    )}
                    <div className="text-xs text-gray-500">
                      {formatDate(item.created_at)}
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-3 pl-10">
                    <div className="text-sm text-gray-700 mb-3 prose prose-sm max-w-none">
                      {itemContent.includes('*') || itemContent.includes('#') || itemContent.includes('-') ? (
                        <ReactMarkdown>{itemContent}</ReactMarkdown>
                      ) : (
                        <div className="whitespace-pre-wrap">{itemContent}</div>
                      )}
                    </div>

                    {item.tags && item.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {item.tags.map((tag: string) => (
                          <span key={tag} className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {onInsightAction && (
                      <div className="flex space-x-2 pt-2 border-t">
                        <button
                          onClick={() => onInsightAction('apply', item)}
                          className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
                        >
                          Apply Learning
                        </button>
                        <button
                          onClick={() => onInsightAction('similar', item)}
                          className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                        >
                          Find Similar
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// Summary View Component
interface SummaryViewProps {
  summary?: {
    recent_discoveries: string[]
    key_constraints: string[]
    success_patterns: string[]
    top_tags: string[]
  }
}

function SummaryView({ summary }: SummaryViewProps) {
  if (!summary) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📊</div>
        <div className="text-lg font-medium text-gray-600 mb-2">Knowledge Summary</div>
        <div className="text-sm text-gray-500">
          Summary data will appear as more insights are collected.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Knowledge Summary</h3>

      {/* Recent Discoveries */}
      <div>
        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
          <span className="text-lg mr-2">🔍</span>
          Recent Discoveries
        </h4>
        {summary.recent_discoveries?.length > 0 ? (
          <div className="space-y-2">
            {summary.recent_discoveries.map((discovery, index) => (
              <div key={index} className="p-3 bg-blue-50 rounded-lg text-sm">
                {discovery}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">No recent discoveries</div>
        )}
      </div>

      {/* Key Constraints */}
      <div>
        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
          <span className="text-lg mr-2">🚧</span>
          Key Constraints
        </h4>
        {summary.key_constraints?.length > 0 ? (
          <div className="space-y-2">
            {summary.key_constraints.map((constraint, index) => (
              <div key={index} className="p-3 bg-yellow-50 rounded-lg text-sm">
                {constraint}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">No constraints identified</div>
        )}
      </div>

      {/* Success Patterns */}
      <div>
        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
          <span className="text-lg mr-2">✅</span>
          Success Patterns
        </h4>
        {summary.success_patterns?.length > 0 ? (
          <div className="space-y-2">
            {summary.success_patterns.map((pattern, index) => (
              <div key={index} className="p-3 bg-green-50 rounded-lg text-sm">
                {pattern}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">No success patterns identified</div>
        )}
      </div>

      {/* Top Tags */}
      <div>
        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
          <span className="text-lg mr-2">🏷️</span>
          Top Tags
        </h4>
        {summary.top_tags?.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {summary.top_tags.map((tag, index) => (
              <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">No tags available</div>
        )}
      </div>
    </div>
  )
}