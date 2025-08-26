'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  CheckCircle, 
  Clock, 
  User, 
  ChevronDown, 
  ChevronRight,
  Zap,
  Database,
  Bot,
  Network
} from 'lucide-react'
import { format } from 'date-fns'

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

interface RecoveryExplanationCardProps {
  explanation: RecoveryExplanation
  onUserActionClick?: (action: string, taskId: string) => void
  showTechnicalDetails?: boolean
}

const RecoveryExplanationCard: React.FC<RecoveryExplanationCardProps> = ({
  explanation,
  onUserActionClick,
  showTechnicalDetails = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showTechnical, setShowTechnical] = useState(showTechnicalDetails)

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'low':
        return <Info className="w-4 h-4 text-blue-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    const variants = {
      critical: 'destructive',
      high: 'destructive', 
      medium: 'default',
      low: 'secondary'
    } as const
    
    return (
      <Badge variant={variants[severity as keyof typeof variants] || 'default'}>
        {severity.toUpperCase()}
      </Badge>
    )
  }

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'agent response issue':
        return <Bot className="w-4 h-4 text-purple-500" />
      case 'temporary service issue':
        return <Zap className="w-4 h-4 text-yellow-500" />
      case 'system infrastructure':
        return <Database className="w-4 h-4 text-blue-500" />
      case 'resource availability':
        return <Clock className="w-4 h-4 text-orange-500" />
      default:
        return <Network className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-200 bg-red-50'
      case 'high':
        return 'border-orange-200 bg-orange-50'
      case 'medium':
        return 'border-yellow-200 bg-yellow-50'
      case 'low':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const handleUserAction = (action: string) => {
    if (onUserActionClick) {
      onUserActionClick(action, explanation.task_id)
    }
  }

  return (
    <Card className={`mb-4 ${getStatusColor(explanation.severity_level)}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getSeverityIcon(explanation.severity_level)}
            <CardTitle className="text-base font-semibold">
              {explanation.failure_summary}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {getSeverityBadge(explanation.severity_level)}
            <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="p-1">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            {getCategoryIcon(explanation.display_category)}
            <span>{explanation.display_category}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{format(new Date(explanation.failure_time), 'PPp')}</span>
          </div>
          {explanation.task_name && (
            <div className="truncate max-w-xs">
              <strong>Task:</strong> {explanation.task_name}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* Root Cause */}
        <div className="mb-3">
          <p className="text-sm text-gray-700">
            <strong>Root Cause:</strong> {explanation.root_cause}
          </p>
        </div>

        {/* Recovery Decision */}
        <div className="mb-3">
          <p className="text-sm text-gray-700">
            <strong>Recovery Decision:</strong> {explanation.retry_decision}
          </p>
        </div>

        {/* Confidence */}
        <div className="mb-3 flex items-center gap-2">
          <p className="text-sm text-gray-600">
            {explanation.confidence_explanation}
          </p>
          {explanation.ai_analysis_used && (
            <Badge variant="outline" className="text-xs">
              AI Analysis
            </Badge>
          )}
          {explanation.error_pattern_matched && (
            <Badge variant="outline" className="text-xs">
              Known Pattern
            </Badge>
          )}
        </div>

        {/* Estimated Resolution Time */}
        {explanation.estimated_resolution_time && (
          <div className="mb-3">
            <p className="text-sm text-gray-600">
              <strong>Estimated Resolution:</strong> {explanation.estimated_resolution_time}
            </p>
          </div>
        )}

        {/* User Action Required */}
        {explanation.user_action_required && (
          <div className="mb-3 p-3 bg-yellow-100 border border-yellow-300 rounded-md">
            <div className="flex items-start gap-2">
              <User className="w-4 h-4 text-yellow-700 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-yellow-800 mb-2">
                  <strong>Action Required:</strong> {explanation.user_action_required}
                </p>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleUserAction('review_task')}
                    className="bg-white hover:bg-yellow-50"
                  >
                    Review Task
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleUserAction('view_details')}
                    className="bg-white hover:bg-yellow-50"
                  >
                    View Details
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Expandable Sections */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleContent className="space-y-4">
            
            {/* Technical Details Toggle */}
            <div className="border-t pt-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTechnical(!showTechnical)}
                className="mb-2"
              >
                {showTechnical ? 'Hide' : 'Show'} Technical Details
              </Button>

              {showTechnical && (
                <div className="bg-gray-100 p-3 rounded-md text-xs space-y-2">
                  <div>
                    <strong>Task ID:</strong> <code>{explanation.task_id}</code>
                  </div>
                  
                  {explanation.technical_details.failure_category && (
                    <div>
                      <strong>Failure Category:</strong> {explanation.technical_details.failure_category}
                    </div>
                  )}
                  
                  {explanation.technical_details.error_message && (
                    <div>
                      <strong>Error Message:</strong>
                      <pre className="mt-1 p-2 bg-gray-200 rounded text-xs overflow-x-auto">
                        {explanation.technical_details.error_message}
                      </pre>
                    </div>
                  )}
                  
                  {explanation.technical_details.attempt_count && (
                    <div>
                      <strong>Attempt Count:</strong> {explanation.technical_details.attempt_count}
                    </div>
                  )}
                  
                  {explanation.technical_details.recovery_strategy && (
                    <div>
                      <strong>Recovery Strategy:</strong> {explanation.technical_details.recovery_strategy}
                    </div>
                  )}

                  {explanation.error_pattern_matched && (
                    <div>
                      <strong>Pattern Matched:</strong>
                      <code className="block mt-1 p-1 bg-gray-200 rounded text-xs">
                        {explanation.error_pattern_matched}
                      </code>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Timestamps */}
            <div className="text-xs text-gray-500 border-t pt-2">
              <div>Failed: {format(new Date(explanation.failure_time), 'PPpp')}</div>
              <div>Explained: {format(new Date(explanation.explanation_generated_time), 'PPpp')}</div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}

export default RecoveryExplanationCard