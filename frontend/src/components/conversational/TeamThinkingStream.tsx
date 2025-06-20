'use client'

import React from 'react'
import { TeamActivity } from './types'

interface TeamThinkingStreamProps {
  activities: TeamActivity[]
}

export default function TeamThinkingStream({ activities }: TeamThinkingStreamProps) {
  if (activities.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">🧠</div>
          <div className="text-lg font-medium mb-2">Team is ready</div>
          <div className="text-sm">
            When you send a message, you'll see the team thinking process here
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      <div className="text-sm font-medium text-gray-700 mb-4">
        🧠 Team Thinking Process
      </div>

      {activities.map((activity) => (
        <ActivityCard key={activity.agentId} activity={activity} />
      ))}

      {/* Overall Progress */}
      <div className="mt-6 p-3 bg-blue-50 rounded-lg">
        <div className="text-sm font-medium text-blue-800 mb-2">
          Overall Progress
        </div>
        <div className="w-full bg-blue-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ 
              width: `${activities.reduce((acc, a) => acc + a.progress, 0) / activities.length}%` 
            }}
          />
        </div>
        <div className="text-xs text-blue-600 mt-1">
          {Math.round(activities.reduce((acc, a) => acc + a.progress, 0) / activities.length)}% complete
        </div>
      </div>
    </div>
  )
}

// Activity Card Component
interface ActivityCardProps {
  activity: TeamActivity
}

function ActivityCard({ activity }: ActivityCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'thinking': return '🤔'
      case 'working': return '⚡'
      case 'completed': return '✅'
      case 'waiting': return '⏳'
      default: return '🔄'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'thinking': return 'border-yellow-200 bg-yellow-50'
      case 'working': return 'border-blue-200 bg-blue-50'
      case 'completed': return 'border-green-200 bg-green-50'
      case 'waiting': return 'border-gray-200 bg-gray-50'
      default: return 'border-gray-200 bg-gray-50'
    }
  }

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'thinking': return 'bg-yellow-500'
      case 'working': return 'bg-blue-500'
      case 'completed': return 'bg-green-500'
      case 'waiting': return 'bg-gray-400'
      default: return 'bg-gray-400'
    }
  }

  return (
    <div className={`p-3 rounded-lg border-2 ${getStatusColor(activity.status)}`}>
      {/* Agent Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getStatusIcon(activity.status)}</span>
          <span className="font-medium text-sm text-gray-900">
            {activity.agentName}
          </span>
        </div>
        {activity.eta && (
          <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded-full">
            ETA: {activity.eta}
          </span>
        )}
      </div>

      {/* Activity Description */}
      <div className="text-sm text-gray-700 mb-3">
        {activity.activity}
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-600">
          <span>Progress</span>
          <span>{activity.progress}%</span>
        </div>
        <div className="w-full bg-white rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(activity.status)}`}
            style={{ width: `${activity.progress}%` }}
          />
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-2 flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${
          activity.status === 'working' ? 'animate-pulse' : ''
        } ${getProgressColor(activity.status)}`} />
        <span className="text-xs text-gray-600 capitalize">
          {activity.status.replace('_', ' ')}
        </span>
      </div>
    </div>
  )
}