'use client'

import React, { useState, useEffect } from 'react'
import { useAssetRefinementStatus } from '@/hooks/useAssetRefinementStatus'
import { useDeliverableMonitoring } from '@/hooks/useDeliverableMonitoring'

interface EnhancementTrackingProps {
  workspaceId: string
  assetName: string
}

const EnhancementTracking: React.FC<EnhancementTrackingProps> = ({
  workspaceId,
  assetName
}) => {
  const [trackingLogs, setTrackingLogs] = useState<string[]>([])
  const [isExpanded, setIsExpanded] = useState(false)

  const refinementStatus = useAssetRefinementStatus(workspaceId, assetName)
  const deliverableMonitoring = useDeliverableMonitoring(workspaceId, 15000) // Check every 15 seconds

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setTrackingLogs(prev => [`[${timestamp}] ${message}`, ...prev.slice(0, 19)]) // Keep last 20 logs
  }

  // Monitor refinement status changes
  useEffect(() => {
    if (refinementStatus.totalRefinements > 0) {
      addLog(`📋 Found ${refinementStatus.totalRefinements} enhancement tasks`)
      
      if (refinementStatus.pendingRefinements.length > 0) {
        addLog(`⏳ ${refinementStatus.pendingRefinements.length} tasks in progress`)
      }
      
      if (refinementStatus.completedRefinements.length > 0) {
        addLog(`✅ ${refinementStatus.completedRefinements.length} tasks in history`)
      }
    }
  }, [refinementStatus.totalRefinements, refinementStatus.pendingRefinements.length, refinementStatus.completedRefinements.length])

  // Monitor deliverable changes
  useEffect(() => {
    if (deliverableMonitoring.hasChanges) {
      addLog(`🔄 Deliverables updated - ${deliverableMonitoring.deliverables.length} deliverables found`)
    }
  }, [deliverableMonitoring.hasChanges, deliverableMonitoring.deliverables.length])

  // Monitor errors
  useEffect(() => {
    if (refinementStatus.error) {
      addLog(`❌ Enhancement error: ${refinementStatus.error}`)
    }
  }, [refinementStatus.error])

  useEffect(() => {
    if (deliverableMonitoring.error) {
      addLog(`❌ Deliverable monitoring error: ${deliverableMonitoring.error}`)
    }
  }, [deliverableMonitoring.error])

  const getStatusSummary = () => {
    const total = refinementStatus.totalRefinements
    const pending = refinementStatus.pendingRefinements.length
    const completed = refinementStatus.completedRefinements.length
    const deliverables = deliverableMonitoring.deliverables.length

    return `${total} enhancement tasks • ${pending} active • ${completed} history • ${deliverables} deliverables`
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">📊</span>
          <div>
            <h4 className="font-medium text-gray-900">Enhancement Tracking</h4>
            <p className="text-sm text-gray-600">{getStatusSummary()}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {(refinementStatus.isLoading || deliverableMonitoring.isLoading) && (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
          )}
          <span className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Current Status */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold text-blue-700">{refinementStatus.totalRefinements}</div>
              <div className="text-xs text-blue-600">Total Tasks</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-xl font-bold text-orange-700">{refinementStatus.pendingRefinements.length}</div>
              <div className="text-xs text-orange-600">In Progress</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-700">{refinementStatus.completedRefinements.length}</div>
              <div className="text-xs text-green-600">Completed</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-xl font-bold text-purple-700">{deliverableMonitoring.deliverables.length}</div>
              <div className="text-xs text-purple-600">Deliverables</div>
            </div>
          </div>

          {/* Activity Log */}
          {trackingLogs.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-700 mb-2">📋 Activity Log</h5>
              <div className="bg-gray-50 rounded p-3 max-h-32 overflow-y-auto">
                {trackingLogs.map((log, index) => (
                  <div key={index} className="text-xs text-gray-600 font-mono mb-1">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="flex space-x-2">
            <button
              onClick={refinementStatus.refresh}
              className="flex-1 bg-blue-100 text-blue-700 px-3 py-2 rounded text-sm hover:bg-blue-200 transition-colors"
            >
              🔄 Refresh Tasks
            </button>
            <button
              onClick={deliverableMonitoring.refresh}
              className="flex-1 bg-purple-100 text-purple-700 px-3 py-2 rounded text-sm hover:bg-purple-200 transition-colors"
            >
              📦 Refresh Deliverables
            </button>
          </div>

          {/* Last Update Info */}
          <div className="text-xs text-gray-500 text-center">
            Last update: {deliverableMonitoring.lastUpdate ? new Date(deliverableMonitoring.lastUpdate).toLocaleTimeString() : 'Never'}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnhancementTracking