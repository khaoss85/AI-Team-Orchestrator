'use client'

import React from 'react'

interface ThinkingStatusIndicatorProps {
  isConnected: boolean
  hasActiveThinking?: boolean
  recentThinkingCount?: number
}

export default function ThinkingStatusIndicator({ 
  isConnected, 
  hasActiveThinking = false,
  recentThinkingCount = 0
}: ThinkingStatusIndicatorProps) {
  // Don't show anything if not connected and no recent activity
  if (!isConnected && !hasActiveThinking && recentThinkingCount === 0) {
    return null
  }

  return (
    <div className="flex items-center space-x-2 text-xs">
      {/* Connection Status */}
      <div className="flex items-center space-x-1">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
        <span className="text-gray-600">
          {isConnected ? 'Real-time thinking enabled' : 'Thinking updates offline'}
        </span>
      </div>

      {/* Active Thinking Indicator */}
      {hasActiveThinking && (
        <div className="flex items-center space-x-1 text-blue-600">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <span>AI is thinking...</span>
        </div>
      )}

      {/* Recent Activity Count */}
      {recentThinkingCount > 0 && !hasActiveThinking && (
        <span className="text-gray-500">
          {recentThinkingCount} recent thinking session{recentThinkingCount > 1 ? 's' : ''}
        </span>
      )}
    </div>
  )
}