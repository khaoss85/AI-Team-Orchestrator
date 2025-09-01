'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Loader2, TrendingUp, Package, Target, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'

interface Deliverable {
  id: string
  title: string
  status: string
  progress: number
  created_at: string
}

interface MacroDeliverable {
  theme_id: string
  name: string
  description: string
  icon: string
  business_value: string
  confidence_score: number
  goals: string[]
  deliverables: Deliverable[]
  statistics: {
    total_goals: number
    total_deliverables: number
    average_progress: number
    completed_deliverables: number
  }
  reasoning: string
}

interface MacroDeliverableViewProps {
  workspaceId: string
  onDeliverableClick?: (deliverable: Deliverable) => void
}

export function MacroDeliverableView({ workspaceId, onDeliverableClick }: MacroDeliverableViewProps) {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [macroDeliverables, setMacroDeliverables] = useState<MacroDeliverable[]>([])
  const [expandedThemes, setExpandedThemes] = useState<Set<string>>(new Set())
  const [extractionSummary, setExtractionSummary] = useState<any>(null)

  const fetchMacroDeliverables = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      setError(null)

      const response = await fetch(`/api/theme/${workspaceId}/macro-deliverables`)
      if (!response.ok) {
        throw new Error(`Failed to fetch macro deliverables: ${response.statusText}`)
      }

      const data = await response.json()
      setMacroDeliverables(data.macro_deliverables || [])
      setExtractionSummary(data.extraction_summary)

      // Auto-expand first theme if none expanded
      if (data.macro_deliverables?.length > 0 && expandedThemes.size === 0) {
        setExpandedThemes(new Set([data.macro_deliverables[0].theme_id]))
      }
    } catch (err) {
      console.error('Error fetching macro deliverables:', err)
      setError(err instanceof Error ? err.message : 'Failed to load macro deliverables')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const refreshThemes = async () => {
    try {
      setRefreshing(true)
      
      // First extract new themes
      const extractResponse = await fetch(`/api/theme/${workspaceId}/extract`, {
        method: 'GET',
      })
      
      if (!extractResponse.ok) {
        throw new Error(`Failed to extract themes: ${extractResponse.statusText}`)
      }

      // Then fetch updated macro deliverables
      await fetchMacroDeliverables(true)
    } catch (err) {
      console.error('Error refreshing themes:', err)
      setError(err instanceof Error ? err.message : 'Failed to refresh themes')
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (workspaceId) {
      fetchMacroDeliverables()
    }
  }, [workspaceId])

  const toggleThemeExpansion = (themeId: string) => {
    setExpandedThemes((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(themeId)) {
        newSet.delete(themeId)
      } else {
        newSet.add(themeId)
      }
      return newSet
    })
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 85) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-orange-600'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Loading macro deliverables...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={() => fetchMacroDeliverables()} variant="outline">
          Try Again
        </Button>
      </div>
    )
  }

  if (!macroDeliverables || macroDeliverables.length === 0) {
    return (
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="text-center py-8">
          <Package className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">No macro deliverables found</p>
          <Button onClick={refreshThemes} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Extract Themes
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Macro Deliverables</h2>
          {extractionSummary && (
            <p className="text-sm text-gray-600 mt-1">
              {extractionSummary.total_themes} themes • {extractionSummary.total_goals} goals • 
              {' '}{Math.round(extractionSummary.grouping_efficiency)}% grouped
            </p>
          )}
        </div>
        <Button 
          onClick={refreshThemes} 
          variant="outline" 
          size="sm"
          disabled={refreshing}
        >
          {refreshing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Refreshing...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Themes
            </>
          )}
        </Button>
      </div>

      {/* Macro Deliverables Grid */}
      <div className="grid gap-6">
        {macroDeliverables.map((macro) => {
          const isExpanded = expandedThemes.has(macro.theme_id)
          const completionRate = macro.statistics.total_deliverables > 0
            ? (macro.statistics.completed_deliverables / macro.statistics.total_deliverables) * 100
            : 0

          return (
            <Card 
              key={macro.theme_id} 
              className="overflow-hidden hover:shadow-lg transition-shadow duration-200"
            >
              <CardHeader 
                className="cursor-pointer bg-gradient-to-r from-gray-50 to-white"
                onClick={() => toggleThemeExpansion(macro.theme_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{macro.icon}</span>
                      <CardTitle className="text-xl">{macro.name}</CardTitle>
                      <Badge 
                        variant="outline" 
                        className={getConfidenceColor(macro.confidence_score)}
                      >
                        {Math.round(macro.confidence_score)}% confidence
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{macro.description}</p>
                    
                    {/* Business Value */}
                    <div className="flex items-start gap-2 mb-3">
                      <TrendingUp className="w-4 h-4 text-blue-500 mt-0.5" />
                      <p className="text-sm text-gray-700">{macro.business_value}</p>
                    </div>

                    {/* Statistics Bar */}
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Target className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{macro.statistics.total_goals} goals</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Package className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">
                          {macro.statistics.completed_deliverables} deliverables
                        </span>
                      </div>
                      {completionRate > 0 && (
                        <div className="flex items-center gap-2 flex-1 max-w-xs">
                          <Progress value={completionRate} className="h-2" />
                          <span className="text-gray-600">{Math.round(completionRate)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <Button variant="ghost" size="sm">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>

              {isExpanded && (
                <CardContent className="pt-4 bg-white">
                  {/* Reasoning */}
                  {macro.reasoning && (
                    <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>AI Reasoning:</strong> {macro.reasoning}
                      </p>
                    </div>
                  )}

                  {/* Deliverables List */}
                  {macro.deliverables.length > 0 ? (
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Deliverables:</h4>
                      {macro.deliverables.map((deliverable) => (
                        <div
                          key={deliverable.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                          onClick={() => onDeliverableClick?.(deliverable)}
                        >
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">
                              {deliverable.title}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              Created: {new Date(deliverable.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge className={getStatusColor(deliverable.status)}>
                            {deliverable.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-gray-500">
                      <Package className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No deliverables yet for this theme</p>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}

export default MacroDeliverableView