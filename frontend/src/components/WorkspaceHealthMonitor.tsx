// frontend/src/components/WorkspaceHealthMonitor.tsx
import React, { useState } from 'react'

interface WorkspaceHealthMonitorProps {
  workspaceHealthStatus: any
  healthLoading: boolean
  onUnblock: (reason?: string) => Promise<{ success: boolean; message: string }>
  onRefresh: () => Promise<any>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

export function WorkspaceHealthMonitor({
  workspaceHealthStatus,
  healthLoading,
  onUnblock,
  onRefresh,
  onResumeAutoGeneration
}: WorkspaceHealthMonitorProps) {
  const [unblocking, setUnblocking] = useState(false)
  const [unblockReason, setUnblockReason] = useState('')
  const [showUnblockDialog, setShowUnblockDialog] = useState(false)
  const [actionResult, setActionResult] = useState<{ type: 'success' | 'error', message: string } | null>(null)
  const [resumingAutoGen, setResumingAutoGen] = useState(false)

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '🟢'
      case 'needs_intervention':
        return '🟡'
      case 'critical':
        return '🔴'
      default:
        return '⚪'
    }
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600'
      case 'needs_intervention':
        return 'text-yellow-600'
      case 'critical':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'text-blue-600 bg-blue-50'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50'
      case 'high':
        return 'text-orange-600 bg-orange-50'
      case 'critical':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const handleUnblock = async () => {
    try {
      setUnblocking(true)
      const result = await onUnblock(unblockReason || 'Manual unblock from workspace health monitor')
      
      if (result.success) {
        setActionResult({ type: 'success', message: result.message })
        setShowUnblockDialog(false)
        setUnblockReason('')
        // Auto-clear success message after 3 seconds
        setTimeout(() => setActionResult(null), 3000)
      } else {
        setActionResult({ type: 'error', message: result.message })
      }
    } catch (error) {
      setActionResult({ type: 'error', message: `Failed to unblock workspace: ${error.message}` })
    } finally {
      setUnblocking(false)
    }
  }

  const handleRefresh = async () => {
    try {
      await onRefresh()
      setActionResult({ type: 'success', message: 'Health status refreshed successfully' })
      setTimeout(() => setActionResult(null), 2000)
    } catch (error) {
      setActionResult({ type: 'error', message: `Failed to refresh: ${error.message}` })
    }
  }

  const handleResumeAutoGeneration = async () => {
    if (!onResumeAutoGeneration) return
    
    try {
      setResumingAutoGen(true)
      const result = await onResumeAutoGeneration()
      
      if (result.success) {
        setActionResult({ type: 'success', message: result.message })
        // Auto-clear success message after 3 seconds
        setTimeout(() => setActionResult(null), 3000)
      } else {
        setActionResult({ type: 'error', message: result.message })
      }
    } catch (error) {
      setActionResult({ type: 'error', message: `Failed to resume auto-generation: ${error.message}` })
    } finally {
      setResumingAutoGen(false)
    }
  }

  if (healthLoading && !workspaceHealthStatus) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Checking workspace health...</span>
        </div>
      </div>
    )
  }

  if (!workspaceHealthStatus) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Health status unavailable</span>
          <button
            onClick={handleRefresh}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition-colors"
          >
            Check Now
          </button>
        </div>
      </div>
    )
  }

  const { 
    status, 
    is_blocked, 
    health_score, 
    issues = [], 
    blocked_reasons = [], 
    resolution_suggestions = [], 
    suggestions = [],
    performance_metrics, 
    last_checked,
    block_reason,
    task_counts,
    agent_counts,
    last_activity
  } = workspaceHealthStatus || {}

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getHealthStatusIcon(status)}</span>
          <div>
            <span className={`font-medium ${getHealthStatusColor(status)}`}>
              {status.replace('_', ' ').toUpperCase()}
            </span>
            {health_score !== undefined && (
              <span className="text-sm text-gray-500 ml-2">
                (Score: {Math.round(health_score)}/100)
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefresh}
            disabled={healthLoading}
            className="text-xs bg-gray-100 hover:bg-gray-200 disabled:opacity-50 px-2 py-1 rounded transition-colors"
          >
            {healthLoading ? 'Checking...' : 'Refresh'}
          </button>
          
          {onResumeAutoGeneration && (
            <button
              onClick={handleResumeAutoGeneration}
              disabled={resumingAutoGen}
              className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-2 py-1 rounded transition-colors disabled:opacity-50"
            >
              {resumingAutoGen ? '⏳ Resuming...' : '🔄 Resume Auto-Gen'}
            </button>
          )}
          
          {is_blocked && (
            <button
              onClick={() => setShowUnblockDialog(true)}
              className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
            >
              🔓 Unblock
            </button>
          )}
        </div>
      </div>

      {/* Action Result */}
      {actionResult && (
        <div className={`p-2 rounded text-sm ${
          actionResult.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {actionResult.message}
        </div>
      )}

      {/* Blocked Status */}
      {is_blocked && (
        <div className="bg-red-50 border border-red-200 rounded p-3">
          <div className="flex items-start space-x-2">
            <span className="text-red-600 font-medium text-sm">🚫 Workspace Blocked</span>
          </div>
          {block_reason && (
            <div className="mt-2 text-sm text-red-700">
              <strong>Reason:</strong> {block_reason}
            </div>
          )}
          {blocked_reasons && Array.isArray(blocked_reasons) && blocked_reasons.length > 0 && (
            <ul className="mt-2 space-y-1">
              {blocked_reasons.map((reason, index) => (
                <li key={index} className="text-sm text-red-700">
                  • {reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      
      {/* Detailed Stats */}
      {(task_counts || agent_counts) && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <h4 className="font-medium text-sm text-blue-900 mb-2">📊 Workspace Statistics</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {task_counts && (
              <>
                <div>
                  <span className="text-blue-700">Total Tasks:</span>
                  <span className="ml-1 font-medium">{task_counts.total || 0}</span>
                </div>
                <div>
                  <span className="text-blue-700">Completed:</span>
                  <span className="ml-1 font-medium text-green-600">{task_counts.completed || 0}</span>
                </div>
                <div>
                  <span className="text-blue-700">Failed:</span>
                  <span className="ml-1 font-medium text-red-600">{task_counts.failed || 0}</span>
                </div>
                <div>
                  <span className="text-blue-700">Pending:</span>
                  <span className="ml-1 font-medium text-yellow-600">{task_counts.pending || 0}</span>
                </div>
                {(task_counts.timed_out || 0) > 0 && (
                  <div>
                    <span className="text-blue-700">Timed Out:</span>
                    <span className="ml-1 font-medium text-orange-600">{task_counts.timed_out}</span>
                  </div>
                )}
                {(task_counts.in_progress || 0) > 0 && (
                  <div>
                    <span className="text-blue-700">In Progress:</span>
                    <span className="ml-1 font-medium text-blue-600">{task_counts.in_progress}</span>
                  </div>
                )}
              </>
            )}
            {agent_counts && (
              <>
                <div>
                  <span className="text-blue-700">Available Agents:</span>
                  <span className="ml-1 font-medium">{agent_counts.available || 0}</span>
                </div>
                <div>
                  <span className="text-blue-700">Total Agents:</span>
                  <span className="ml-1 font-medium">{agent_counts.total || 0}</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Issues */}
      {issues && Array.isArray(issues) && issues.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-sm text-gray-900">Current Issues</h4>
          {issues.map((issue, index) => {
            // Handle both string format (from API) and object format
            const issueText = typeof issue === 'string' ? issue : issue?.description || 'Unknown issue'
            const issueType = typeof issue === 'string' ? 
              (issue.toLowerCase().includes('orphaned') ? 'Orphaned Tasks' :
               issue.toLowerCase().includes('paused') ? 'Auto-Generation Paused' :
               issue.toLowerCase().includes('blocked') ? 'Workspace Blocked' :
               issue.toLowerCase().includes('velocity') ? 'High Task Velocity' :
               'System Issue') :
              (issue?.type ? issue.type.replace('_', ' ').toUpperCase() : 'UNKNOWN ISSUE')
            
            const severity = typeof issue === 'string' ?
              (issue.toLowerCase().includes('orphaned') ? 'high' :
               issue.toLowerCase().includes('blocked') ? 'critical' :
               'medium') :
              (issue?.severity || 'medium')
              
            return (
              <div
                key={index}
                className={`p-2 rounded border text-sm ${getSeverityColor(severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium">{issueType}</div>
                    <div className="mt-1">{issueText}</div>
                  </div>
                  <span className="text-xs opacity-75 ml-2">
                    {severity.toUpperCase()}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Performance Metrics */}
      {performance_metrics && (
        <div className="bg-gray-50 rounded p-3">
          <h4 className="font-medium text-sm text-gray-900 mb-2">Performance Metrics</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-600">Task Velocity:</span>
              <span className="ml-1 font-medium">
                {performance_metrics.task_velocity != null ? performance_metrics.task_velocity.toFixed(1) : '0.0'}/min
              </span>
            </div>
            <div>
              <span className="text-gray-600">Agent Utilization:</span>
              <span className="ml-1 font-medium">
                {performance_metrics.agent_utilization != null ? Math.round(performance_metrics.agent_utilization) : '0'}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">Error Rate:</span>
              <span className="ml-1 font-medium">
                {performance_metrics.error_rate != null ? Math.round(performance_metrics.error_rate) : '0'}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">Avg Task Duration:</span>
              <span className="ml-1 font-medium">
                {performance_metrics.avg_task_duration != null ? Math.round(performance_metrics.avg_task_duration) : '0'}s
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Resolution Suggestions */}
      {((resolution_suggestions && Array.isArray(resolution_suggestions) && resolution_suggestions.length > 0) ||
        (suggestions && Array.isArray(suggestions) && suggestions.length > 0)) && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <h4 className="font-medium text-sm text-blue-900 mb-2">💡 Recommended Actions</h4>
          <ul className="space-y-1">
            {/* Show both resolution_suggestions and suggestions */}
            {resolution_suggestions && resolution_suggestions.map((suggestion, index) => (
              <li key={`res-${index}`} className="text-sm text-blue-800">
                • {suggestion}
              </li>
            ))}
            {suggestions && suggestions.map((suggestion, index) => (
              <li key={`sug-${index}`} className="text-sm text-blue-800">
                • {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Last Checked */}
      {(last_checked || last_activity) && (
        <div className="text-xs text-gray-500 text-center space-y-1">
          {last_checked && (
            <div>Last health check: {new Date(last_checked).toLocaleString()}</div>
          )}
          {last_activity && (
            <div>Last activity: {new Date(last_activity).toLocaleString()}</div>
          )}
        </div>
      )}

      {/* Unblock Dialog */}
      {showUnblockDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Unblock Workspace</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for unblocking (optional):
              </label>
              <textarea
                value={unblockReason}
                onChange={(e) => setUnblockReason(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="e.g., Investigated issue and determined it's safe to proceed..."
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowUnblockDialog(false)}
                disabled={unblocking}
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUnblock}
                disabled={unblocking}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {unblocking && (
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                )}
                <span>{unblocking ? 'Unblocking...' : 'Unblock Workspace'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}