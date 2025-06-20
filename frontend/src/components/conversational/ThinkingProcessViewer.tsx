'use client'

import React, { useState } from 'react'

interface ThinkingStep {
  type: string
  step: string
  title: string
  description: string
  status: 'completed' | 'in_progress' | 'pending'
  timestamp?: string
  fromMessage?: string  // ID of the message this step came from
  messageTimestamp?: string  // Timestamp of the original message
}

interface ThinkingProcessViewerProps {
  steps: ThinkingStep[]
  isThinking?: boolean
}

interface ThinkingSession {
  id: string
  steps: ThinkingStep[]
  timestamp?: string
  isExpanded: boolean
  summary: string
  duration?: string
}

export default function ThinkingProcessViewer({ steps, isThinking = false }: ThinkingProcessViewerProps) {
  const [expandedSessions, setExpandedSessions] = useState<Record<string, boolean>>({})

  if (!steps || steps.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">🧠</div>
        <p className="text-sm">No thinking process to display</p>
        <p className="text-xs text-gray-400 mt-1">
          Thinking steps will appear here when the AI processes your message
        </p>
      </div>
    )
  }

  // Group steps by message/session and create summaries
  const sessions: ThinkingSession[] = Object.entries(
    steps.reduce((groups, step) => {
      const key = step.fromMessage || 'current';
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(step);
      return groups;
    }, {} as Record<string, ThinkingStep[]>)
  ).map(([sessionId, sessionSteps]) => {
    const firstStep = sessionSteps[0]
    const lastStep = sessionSteps[sessionSteps.length - 1]
    
    // Generate Claude-style summary
    const completedSteps = sessionSteps.filter(s => s.status === 'completed')
    const summary = generateThinkingSummary(sessionSteps)
    
    // Calculate duration
    let duration = ''
    if (firstStep.timestamp && lastStep.timestamp) {
      const startTime = new Date(firstStep.timestamp)
      const endTime = new Date(lastStep.timestamp)
      const durationMs = endTime.getTime() - startTime.getTime()
      duration = durationMs < 1000 ? '<1s' : `${Math.round(durationMs / 1000)}s`
    }
    
    return {
      id: sessionId,
      steps: sessionSteps,
      timestamp: firstStep.messageTimestamp || firstStep.timestamp,
      isExpanded: expandedSessions[sessionId] || sessionId === 'current',
      summary,
      duration
    }
  })

  const toggleSession = (sessionId: string) => {
    setExpandedSessions(prev => ({
      ...prev,
      [sessionId]: !prev[sessionId]
    }))
  }

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🧠</span>
        <h3 className="font-semibold text-gray-900">Thinking</h3>
        <span className="text-xs text-gray-500">({steps.length} steps)</span>
      </div>

      {sessions.map((session) => (
        <ClaudeStyleThinkingSession
          key={session.id}
          session={session}
          onToggle={() => toggleSession(session.id)}
          isThinking={isThinking && session.id === 'current'}
        />
      ))}

      {isThinking && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-pulse flex items-center gap-2 text-blue-600">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="ml-2 text-sm">AI is thinking...</span>
          </div>
        </div>
      )}
    </div>
  )
}

function generateThinkingSummary(steps: ThinkingStep[]): string {
  if (steps.length === 0) return 'No thinking steps'
  
  // Extract key actions and insights
  const keyActions = steps
    .filter(step => step.status === 'completed')
    .map(step => step.title.toLowerCase())
  
  const actionTypes = {
    analysis: ['analyze', 'analysis', 'examine', 'review'],
    planning: ['plan', 'strategy', 'approach', 'structure'],
    synthesis: ['synthesize', 'combine', 'integrate', 'merge'],
    evaluation: ['evaluate', 'assess', 'validate', 'check'],
    reasoning: ['reason', 'logic', 'deduce', 'infer']
  }
  
  const detectedActions = new Set<string>()
  keyActions.forEach(action => {
    Object.entries(actionTypes).forEach(([type, keywords]) => {
      if (keywords.some(keyword => action.includes(keyword))) {
        detectedActions.add(type)
      }
    })
  })
  
  if (detectedActions.size === 0) {
    return `Processed ${steps.length} thinking step${steps.length > 1 ? 's' : ''}`
  }
  
  const actionList = Array.from(detectedActions).join(', ')
  return `Completed ${actionList} and strategic reasoning`
}

interface ClaudeStyleThinkingSessionProps {
  session: ThinkingSession
  onToggle: () => void
  isThinking?: boolean
}

function ClaudeStyleThinkingSession({ session, onToggle, isThinking = false }: ClaudeStyleThinkingSessionProps) {
  const completedSteps = session.steps.filter(s => s.status === 'completed').length
  const totalSteps = session.steps.length
  
  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      {/* Collapsible Header - Claude Style */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0">
              {session.isExpanded ? (
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              )}
            </div>
            
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">
                {session.summary}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {completedSteps}/{totalSteps} steps completed
                {session.id !== 'current' && session.timestamp && (
                  <span className="ml-2">
                    • {new Date(session.timestamp).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {session.duration && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {session.duration}
              </span>
            )}
            {isThinking && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-blue-600">thinking...</span>
              </div>
            )}
          </div>
        </div>
      </button>
      
      {/* Expandable Content */}
      {session.isExpanded && (
        <div className="p-4 space-y-3 bg-gray-50">
          {session.steps.map((step, index) => (
            <ThinkingStepCard 
              key={index}
              step={step} 
              index={index}
              isActive={isThinking && index === session.steps.length - 1 && session.id === 'current'}
              isFromSavedMessage={session.id !== 'current'}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface ThinkingStepCardProps {
  step: ThinkingStep
  index: number
  isActive?: boolean
  isFromSavedMessage?: boolean
}

function ThinkingStepCard({ step, index, isActive = false, isFromSavedMessage = false }: ThinkingStepCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'in_progress':
        return '○'
      case 'pending':
        return '○'
      default:
        return '✓'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-white border-green-200'
      case 'in_progress':
        return 'text-blue-600 bg-blue-50 border-blue-200 ring-1 ring-blue-300'
      case 'pending':
        return 'text-gray-500 bg-white border-gray-200'
      default:
        return 'text-green-600 bg-white border-green-200'
    }
  }

  return (
    <div className={`
      border rounded-md p-3 transition-all duration-200 text-sm
      ${getStatusColor(step.status)}
      ${isActive ? 'ring-2 ring-blue-300 shadow-sm' : ''}
      ${isFromSavedMessage ? 'opacity-80' : ''}
    `}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 mt-0.5">
          <span className="text-xs font-mono">{getStatusIcon(step.status)}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-medium text-gray-900">
              {step.title}
            </h4>
            <span className="text-xs text-gray-400">#{index + 1}</span>
          </div>
          
          <p className="text-xs text-gray-700 leading-relaxed">
            {step.description}
          </p>
          
          {step.timestamp && (
            <div className="text-xs text-gray-400 mt-2">
              {new Date(step.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}