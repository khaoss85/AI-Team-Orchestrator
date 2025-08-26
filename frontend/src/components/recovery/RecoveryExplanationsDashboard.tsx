'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  AlertCircle, 
  TrendingUp, 
  Filter, 
  Refresh, 
  Download,
  BarChart3,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react'
import RecoveryExplanationCard from './RecoveryExplanationCard'

interface RecoveryExplanation {
  task_id: string
  task_name: string | null
  failure_summary: string
  root_cause: string
  retry_decision: string
  confidence_explanation: string
  user_action_required: string | null
  estimated_resolution_time: string | null
  severity_level: string
  display_category: string
  failure_time: string
  explanation_generated_time: string
  technical_details: Record<string, any>
  error_pattern_matched: string | null
  ai_analysis_used: boolean
}

interface ExplanationStats {
  total_explanations: number
  pattern_matches: number
  ai_analyses_used: number
  pattern_match_rate: number
  ai_analysis_rate: number
  top_failure_categories: Array<{
    category: string
    count: number
    percentage: number
  }>
}

interface RecoveryExplanationsDashboardProps {
  workspaceId: string
}

const RecoveryExplanationsDashboard: React.FC<RecoveryExplanationsDashboardProps> = ({
  workspaceId
}) => {
  const [explanations, setExplanations] = useState<RecoveryExplanation[]>([])
  const [stats, setStats] = useState<ExplanationStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    severity: '',
    category: '',
    searchTerm: ''
  })
  const [autoRefresh, setAutoRefresh] = useState(false)

  // Load explanations
  const loadExplanations = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.severity) params.append('severity_filter', filters.severity)
      if (filters.category) params.append('category_filter', filters.category)
      
      const response = await fetch(`/api/recovery-explanations/workspace/${workspaceId}?${params}`)
      if (response.ok) {
        const data = await response.json()
        setExplanations(data)
      }
    } catch (error) {
      console.error('Failed to load recovery explanations:', error)
    }
    setLoading(false)
  }

  // Load statistics
  const loadStats = async () => {
    try {
      const response = await fetch('/api/recovery-explanations/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to load explanation statistics:', error)
    }
  }

  // Initial load
  useEffect(() => {
    loadExplanations()
    loadStats()
  }, [workspaceId, filters])

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(() => {
      loadExplanations()
      loadStats()
    }, 30000) // Refresh every 30 seconds
    
    return () => clearInterval(interval)
  }, [autoRefresh, workspaceId, filters])

  // Filter explanations based on search term
  const filteredExplanations = explanations.filter(exp => 
    !filters.searchTerm || 
    exp.task_name?.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
    exp.failure_summary.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
    exp.root_cause.toLowerCase().includes(filters.searchTerm.toLowerCase())
  )

  const handleUserAction = (action: string, taskId: string) => {
    switch (action) {
      case 'review_task':
        // Navigate to task detail page
        window.open(`/tasks/${taskId}`, '_blank')
        break
      case 'view_details':
        // Show detailed technical information
        const explanation = explanations.find(e => e.task_id === taskId)
        if (explanation) {
          alert(`Technical Details:\n${JSON.stringify(explanation.technical_details, null, 2)}`)
        }
        break
    }
  }

  const handleExportData = () => {
    const exportData = filteredExplanations.map(exp => ({
      task_id: exp.task_id,
      task_name: exp.task_name,
      failure_time: exp.failure_time,
      severity: exp.severity_level,
      category: exp.display_category,
      summary: exp.failure_summary,
      root_cause: exp.root_cause,
      recovery_decision: exp.retry_decision,
      user_action_required: exp.user_action_required
    }))
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `recovery-explanations-${workspaceId}-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getSeverityCount = (severity: string) => 
    explanations.filter(exp => exp.severity_level === severity).length

  const getCategoryCount = (category: string) =>
    explanations.filter(exp => exp.display_category === category).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Recovery Explanations</h2>
          <p className="text-gray-600">
            Transparent insights into task failure recovery decisions
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
          >
            <Refresh className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          
          <Button variant="outline" size="sm" onClick={loadExplanations} disabled={loading}>
            <Refresh className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleExportData}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Statistics Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Explanations</p>
                  <p className="text-2xl font-bold">{stats.total_explanations}</p>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pattern Recognition</p>
                  <p className="text-2xl font-bold">{(stats.pattern_match_rate * 100).toFixed(0)}%</p>
                </div>
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">AI Analysis Used</p>
                  <p className="text-2xl font-bold">{(stats.ai_analysis_rate * 100).toFixed(0)}%</p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Critical Issues</p>
                  <p className="text-2xl font-bold text-red-600">{getSeverityCount('critical')}</p>
                </div>
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="explanations" className="w-full">
        <TabsList>
          <TabsTrigger value="explanations">Recent Explanations</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="explanations" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Filters
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Input
                  placeholder="Search explanations..."
                  value={filters.searchTerm}
                  onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
                />
                
                <Select value={filters.severity} onValueChange={(value) => setFilters(prev => ({ ...prev, severity: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Severities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Severities</SelectItem>
                    <SelectItem value="critical">Critical ({getSeverityCount('critical')})</SelectItem>
                    <SelectItem value="high">High ({getSeverityCount('high')})</SelectItem>
                    <SelectItem value="medium">Medium ({getSeverityCount('medium')})</SelectItem>
                    <SelectItem value="low">Low ({getSeverityCount('low')})</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={filters.category} onValueChange={(value) => setFilters(prev => ({ ...prev, category: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Categories</SelectItem>
                    <SelectItem value="Agent Response Issue">Agent Response ({getCategoryCount('Agent Response Issue')})</SelectItem>
                    <SelectItem value="Temporary Service Issue">Service Issue ({getCategoryCount('Temporary Service Issue')})</SelectItem>
                    <SelectItem value="System Infrastructure">Infrastructure ({getCategoryCount('System Infrastructure')})</SelectItem>
                    <SelectItem value="Resource Availability">Resources ({getCategoryCount('Resource Availability')})</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button 
                  variant="outline" 
                  onClick={() => setFilters({ severity: '', category: '', searchTerm: '' })}
                >
                  Clear Filters
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Explanations List */}
          <div className="space-y-4">
            {loading && (
              <div className="text-center py-8">
                <Refresh className="w-8 h-8 animate-spin mx-auto mb-2" />
                <p>Loading explanations...</p>
              </div>
            )}
            
            {!loading && filteredExplanations.length === 0 && (
              <Card>
                <CardContent className="text-center py-8">
                  <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <p className="text-lg font-medium">No recent failures</p>
                  <p className="text-gray-600">All tasks are running smoothly!</p>
                </CardContent>
              </Card>
            )}
            
            {filteredExplanations.map((explanation) => (
              <RecoveryExplanationCard
                key={`${explanation.task_id}-${explanation.failure_time}`}
                explanation={explanation}
                onUserActionClick={handleUserAction}
              />
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="analytics" className="space-y-4">
          {/* Category Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Failure Categories</CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.top_failure_categories.map((category, index) => (
                <div key={index} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-blue-500 rounded" />
                    <span>{category.category}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant="secondary">{category.count}</Badge>
                    <span className="text-sm text-gray-600">{category.percentage.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          
          {/* Severity Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Severity Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {['critical', 'high', 'medium', 'low'].map((severity) => {
                  const count = getSeverityCount(severity)
                  const percentage = explanations.length > 0 ? (count / explanations.length) * 100 : 0
                  
                  return (
                    <div key={severity} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {severity === 'critical' && <XCircle className="w-4 h-4 text-red-500" />}
                        {severity === 'high' && <AlertTriangle className="w-4 h-4 text-orange-500" />}
                        {severity === 'medium' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                        {severity === 'low' && <Clock className="w-4 h-4 text-blue-500" />}
                        <span className="capitalize">{severity}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <Badge variant="outline">{count}</Badge>
                        <span className="text-sm text-gray-600 w-12">{percentage.toFixed(0)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default RecoveryExplanationsDashboard