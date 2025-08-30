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
  // 🧠 Real-time props (Claude/o3 style)
  isRealTime?: boolean
  currentDecomposition?: any
  // 🎯 Goal-specific props
  goalContext?: {
    goal: any
    todoList: any[]
    decomposition: any
  }
}

interface ThinkingSession {
  id: string
  steps: ThinkingStep[]
  timestamp?: string
  isExpanded: boolean
  summary: string
  duration?: string
}

export default function ThinkingProcessViewer({ 
  steps, 
  isThinking = false, 
  isRealTime = false, 
  currentDecomposition,
  goalContext 
}: ThinkingProcessViewerProps) {
  const [expandedSessions, setExpandedSessions] = useState<Record<string, boolean>>({})


  if (!steps || steps.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">{goalContext ? '🎯' : '🧠'}</div>
        <p className="text-sm">
          {goalContext 
            ? 'No thinking process for this deliverable' 
            : 'No thinking process to display'
          }
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {goalContext 
            ? 'Goal-specific thinking steps will appear here when available'
            : 'Thinking steps will appear here when the AI processes your message'
          }
        </p>
        {goalContext && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg text-left">
            <p className="text-xs font-medium text-gray-600 mb-1">Goal Summary:</p>
            <p className="text-xs text-gray-700">{goalContext.goal?.description || 'Goal data not available'}</p>
            {goalContext.todoList && goalContext.todoList.length > 0 && (
              <p className="text-xs text-gray-600 mt-2">{goalContext.todoList.length} todo items tracked</p>
            )}
          </div>
        )}
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
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-xl">🧠</span>
          <h3 className="text-lg font-semibold text-gray-900">Thinking Process</h3>
          {isRealTime && (
            <div className="flex items-center gap-2 ml-3">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-sm text-green-600 font-medium">REAL-TIME</span>
            </div>
          )}
        </div>
        
        {/* Goal decomposition progress indicator */}
        {currentDecomposition && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className={`w-2.5 h-2.5 rounded-full ${
              currentDecomposition.status === 'in_progress' ? 'bg-orange-500 animate-pulse' :
              currentDecomposition.status === 'completed' ? 'bg-green-500' : 'bg-gray-400'
            }`}></div>
            <span className="capitalize font-medium">{currentDecomposition.status || 'analyzing'}</span>
          </div>
        )}
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
        <div className="flex items-center justify-center py-6">
          <div className="animate-pulse flex items-center gap-3 text-blue-600">
            <div className="w-2.5 h-2.5 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-2.5 h-2.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2.5 h-2.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="ml-3 text-sm font-medium">AI is thinking...</span>
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
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
      {/* Collapsible Header - Claude Style */}
      <button
        onClick={onToggle}
        className="w-full px-5 py-4 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
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
              <div className="text-sm font-semibold text-gray-900 leading-relaxed">
                {session.summary}
              </div>
              <div className="text-xs text-gray-600 mt-1.5">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {completedSteps}/{totalSteps} steps
                </span>
                {session.id !== 'current' && session.timestamp && (
                  <span className="ml-3 text-gray-500">
                    {new Date(session.timestamp).toLocaleString()}
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
        <div className="px-5 py-4 space-y-3 bg-gray-50 border-t border-gray-100">
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
        return 'text-green-700 bg-green-50 border-green-200'
      case 'in_progress':
        return 'text-blue-700 bg-blue-50 border-blue-200 ring-1 ring-blue-300'
      case 'pending':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      default:
        return 'text-green-700 bg-green-50 border-green-200'
    }
  }

  return (
    <div className={`
      border rounded-lg p-4 transition-all duration-200 text-sm
      ${getStatusColor(step.status)}
      ${isActive ? 'ring-2 ring-blue-300 shadow-sm' : ''}
      ${isFromSavedMessage ? 'opacity-90' : ''}
    `}>
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 mt-0.5 rounded-full bg-white border">
          <span className="text-sm font-semibold">{getStatusIcon(step.status)}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-sm font-semibold text-gray-900 leading-snug">
              {step.title}
            </h4>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700">
              #{index + 1}
            </span>
          </div>
          
          <p className="text-sm text-gray-700 leading-relaxed">
            {step.description}
          </p>
          
          {/* 📋 Todo List Decomposition (Claude/o3 style) */}
          {step.todo_list && Array.isArray(step.todo_list) && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md border">
              <div className="text-xs font-medium text-gray-800 mb-2 flex items-center">
                <span className="mr-1">📋</span>
                Action Plan ({step.todo_list.length} items)
              </div>
              <div className="space-y-2">
                {step.todo_list.map((todo: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      todo.status === 'completed' ? 'bg-green-100 text-green-600' :
                      todo.status === 'in_progress' ? 'bg-blue-100 text-blue-600' :
                      'bg-gray-100 text-gray-500'
                    }`}>
                      {todo.status === 'completed' ? '✓' : 
                       todo.status === 'in_progress' ? '○' : '○'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`font-medium ${
                        todo.status === 'completed' ? 'text-green-700 line-through' :
                        todo.status === 'in_progress' ? 'text-blue-700' :
                        'text-gray-700'
                      }`}>
                        {todo.title}
                      </div>
                      {todo.description && (
                        <div className="text-gray-600 mt-0.5">
                          {todo.description}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
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