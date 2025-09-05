'use client'

import React, { useState } from 'react'

interface AgentMetadata {
  id?: string
  name?: string
  role?: string
  seniority?: 'junior' | 'senior' | 'expert'
  skills?: string[]
  status?: string
}

interface ToolMetadata {
  name?: string
  type?: string
  parameters?: Record<string, any>
  execution_time_ms?: number
  success?: boolean
  error?: string
}

interface ToolResults {
  output_type?: string
  output_size?: number
  summary?: string
  artifacts_created?: string[]
}

interface CollaborationMetadata {
  type?: string
  agents?: Array<{
    id?: string
    role?: string
    seniority?: string
    responsibility?: string
  }>
  timestamp?: string
}

interface EnhancedMetadata {
  agent?: AgentMetadata
  tool?: ToolMetadata
  results?: ToolResults
  collaboration?: CollaborationMetadata
  execution_context?: {
    workspace_id?: string
    task_id?: string
    timestamp?: string
  }
}

interface ThinkingStep {
  type: string
  step: string
  title: string
  description: string
  status: 'completed' | 'in_progress' | 'pending'
  timestamp?: string
  fromMessage?: string  // ID of the message this step came from
  messageTimestamp?: string  // Timestamp of the original message
  // Enhanced metadata from backend
  step_type?: string
  content?: string
  confidence?: number
  metadata?: EnhancedMetadata
  todo_list?: any[]
  // New UX enhancement fields
  process_title?: string  // AI-generated concise title
  summary_metadata?: {  // Essential metadata for minimal display
    primary_agent?: string
    tools_used?: string[]
    estimated_tokens?: number
    duration_ms?: number
    total_steps?: number
  }
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
  metadata?: {  // Essential metadata for minimal display
    primary_agent?: string
    tools_used?: string[]
    estimated_tokens?: number
    duration_ms?: number
    total_steps?: number
  }
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
    
    // Use AI-generated title if available, otherwise generate summary
    const summary = firstStep.process_title || generateThinkingSummary(sessionSteps)
    
    // Use metadata duration if available, otherwise calculate
    let duration = ''
    if (firstStep.summary_metadata?.duration_ms) {
      const ms = firstStep.summary_metadata.duration_ms
      duration = ms < 1000 ? '<1s' : `${Math.round(ms / 1000)}s`
    } else if (firstStep.timestamp && lastStep.timestamp) {
      const startTime = new Date(firstStep.timestamp)
      const endTime = new Date(lastStep.timestamp)
      const durationMs = endTime.getTime() - startTime.getTime()
      duration = durationMs < 1000 ? '<1s' : `${Math.round(durationMs / 1000)}s`
    }
    
    return {
      id: sessionId,
      steps: sessionSteps,
      timestamp: firstStep.messageTimestamp || firstStep.timestamp,
      isExpanded: expandedSessions[sessionId] || false, // Default to collapsed, even for current
      summary,
      duration,
      metadata: firstStep.summary_metadata  // Include metadata for display
    }
  })

  const toggleSession = (sessionId: string) => {
    setExpandedSessions(prev => ({
      ...prev,
      [sessionId]: !prev[sessionId]
    }))
  }

  return (
    <div className="space-y-4">
      {/* Clean minimal header if needed */}
      {currentDecomposition && (
        <div className="flex items-center justify-center py-3">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className={`w-2 h-2 rounded-full ${
              currentDecomposition.status === 'in_progress' ? 'bg-blue-500 animate-pulse' :
              currentDecomposition.status === 'completed' ? 'bg-green-500' : 'bg-gray-400'
            }`}></div>
            <span className="capitalize font-medium">{currentDecomposition.status || 'analyzing'}</span>
          </div>
        </div>
      )}

      {/* Thinking Sessions - Clean List */}
      {sessions.map((session) => (
        <ClaudeStyleThinkingSession
          key={session.id}
          session={session}
          onToggle={() => toggleSession(session.id)}
          isThinking={isThinking && session.id === 'current'}
        />
      ))}

      {/* Minimal thinking indicator */}
      {isThinking && (
        <div className="flex items-center justify-center py-4">
          <div className="flex items-center gap-2 text-blue-600">
            <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="ml-2 text-sm text-gray-600">AI is thinking...</span>
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
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white hover:border-gray-300 transition-colors">
      {/* Clean Header with Prominent Title - ChatGPT/Claude Style */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0 pr-4">
            {/* Prominent Title */}
            <div className="text-base font-semibold text-gray-900 leading-tight mb-2 pr-2">
              {session.summary}
            </div>
            
            {/* Small Metadata - Clean and Minimal */}
            <div className="text-xs text-gray-500 flex items-center gap-4 flex-wrap">
              {session.duration && (
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {session.duration}
                </span>
              )}
              
              {session.metadata?.estimated_tokens && (
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {(session.metadata.estimated_tokens / 1000).toFixed(1)}k tokens
                </span>
              )}
              
              {session.metadata?.tools_used && session.metadata.tools_used.length > 0 && (
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {session.metadata.tools_used.slice(0, 2).join(', ')}
                </span>
              )}
              
              {session.metadata?.primary_agent && (
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {session.metadata.primary_agent}
                </span>
              )}
              
              <span className="flex items-center gap-1 text-gray-400">
                {completedSteps}/{totalSteps} steps
              </span>
            </div>
          </div>
          
          {/* Expand/Collapse Icon + Status */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {isThinking && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-blue-600 font-medium">thinking</span>
              </div>
            )}
            
            <div className="flex-shrink-0 ml-2">
              {session.isExpanded ? (
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </div>
          </div>
        </div>
      </button>
      
      {/* Expandable Detailed Content */}
      {session.isExpanded && (
        <div className="px-6 pb-4 space-y-3 bg-gray-50/50 border-t border-gray-100">
          <div className="pt-3">
            <div className="text-xs font-medium text-gray-600 mb-3 flex items-center gap-2">
              <span>🧠</span>
              <span>Detailed Thinking Process ({session.steps.length} steps)</span>
            </div>
            {session.steps.map((step, index) => (
              <CollapsibleThinkingStep 
                key={index}
                step={step} 
                index={index}
                isActive={isThinking && index === session.steps.length - 1 && session.id === 'current'}
                isFromSavedMessage={session.id !== 'current'}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface CollapsibleThinkingStepProps {
  step: ThinkingStep
  index: number
  isActive?: boolean
  isFromSavedMessage?: boolean
}

function CollapsibleThinkingStep({ step, index, isActive = false, isFromSavedMessage = false }: CollapsibleThinkingStepProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'in_progress':
        return '•'
      case 'pending':
        return '○'
      default:
        return '✓'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'in_progress':
        return 'text-blue-600'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className={`
      border rounded-lg text-sm mb-2 last:mb-0 bg-white
      ${isActive ? 'border-blue-200' : 'border-gray-100'}
      ${isFromSavedMessage ? 'opacity-90' : ''}
    `}>
      {/* Collapsed Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 text-left hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
      >
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 mt-0.5">
            <span className={`text-sm ${getStatusColor(step.status)}`}>
              {getStatusIcon(step.status)}
            </span>
          </div>
          
          {/* Title and Mini Metadata */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900 leading-tight">
                  {step.title}
                </h4>
                
                {/* Minimal metadata inline when collapsed */}
                {!isExpanded && (
                  <div className="text-xs text-gray-500 mt-1 flex items-center gap-3 flex-wrap">
                    {step.metadata?.agent?.role && (
                      <span>Agent: {step.metadata.agent.role}</span>
                    )}
                    {step.metadata?.tool?.name && (
                      <span>Tool: {step.metadata.tool.name}</span>
                    )}
                    {step.confidence !== undefined && step.confidence < 0.7 && (
                      <span>Confidence: {Math.round(step.confidence * 100)}%</span>
                    )}
                  </div>
                )}
              </div>
              
              {/* Expand/Collapse Icon */}
              <div className="flex-shrink-0 ml-2">
                {isExpanded ? (
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </div>
            </div>
          </div>
        </div>
      </button>
      
      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-100">
          <div className="pt-3 pl-8">
            {/* Full Description */}
            <p className="text-sm text-gray-600 leading-relaxed mb-3">
              {step.content || step.description}
            </p>
            
            {/* Full Agent Information */}
            {step.metadata?.agent && (
              <AgentInfoDisplay 
                agent={step.metadata.agent} 
                confidence={step.confidence}
              />
            )}
            
            {/* Full Tool Execution Details */}
            {step.metadata?.tool && (
              <ToolExecutionDisplay 
                tool={step.metadata.tool} 
                results={step.metadata.results}
                confidence={step.confidence}
              />
            )}
            
            {/* Multi-Agent Collaboration */}
            {step.metadata?.collaboration && (
              <CollaborationDisplay 
                collaboration={step.metadata.collaboration}
              />
            )}
            
            {/* Todo List if present */}
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
          </div>
        </div>
      )}
    </div>
  )
}

// Original ThinkingStepCard component can be kept for backward compatibility if needed
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
        return '•'
      case 'pending':
        return '○'
      default:
        return '✓'
    }
  }

  const getStatusColor = (status: string) => {
    // Ultra-minimal color scheme
    switch (status) {
      case 'completed':
        return 'text-gray-700 bg-white border-gray-100'
      case 'in_progress':
        return 'text-gray-700 bg-white border-blue-100'
      case 'pending':
        return 'text-gray-500 bg-gray-50 border-gray-100'
      default:
        return 'text-gray-700 bg-white border-gray-100'
    }
  }

  return (
    <div className={`
      border rounded-lg p-4 text-sm mb-3 last:mb-0
      ${getStatusColor(step.status)}
      ${isActive ? 'border-blue-200 bg-blue-50/30' : ''}
      ${isFromSavedMessage ? 'opacity-90' : ''}
    `}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 mt-0.5">
          <span className={`text-sm ${
            step.status === 'completed' ? 'text-green-600' :
            step.status === 'in_progress' ? 'text-blue-600' :
            'text-gray-400'
          }`}>
            {getStatusIcon(step.status)}
          </span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="mb-2">
            <h4 className="text-sm font-medium text-gray-900 leading-tight">
              {step.title}
            </h4>
          </div>
          
          <p className="text-sm text-gray-600 leading-relaxed">
            {step.content || step.description}
          </p>
          
          {/* 🤖 Agent Information Display */}
          {step.metadata?.agent && (
            <AgentInfoDisplay 
              agent={step.metadata.agent} 
              confidence={step.confidence}
            />
          )}
          
          {/* 🔧 Tool Execution Display */}
          {step.metadata?.tool && (
            <ToolExecutionDisplay 
              tool={step.metadata.tool} 
              results={step.metadata.results}
              confidence={step.confidence}
            />
          )}
          
          {/* 🤝 Multi-Agent Collaboration Display */}
          {step.metadata?.collaboration && (
            <CollaborationDisplay 
              collaboration={step.metadata.collaboration}
            />
          )}
          
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
          
          {/* Minimal Performance Info - Only if relevant */}
          {(step.confidence !== undefined && step.confidence < 0.5) && (
            <div className="mt-2 text-xs text-gray-500">
              Low confidence: {Math.round(step.confidence * 100)}%
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 🤖 Agent Information Display Component
interface AgentInfoDisplayProps {
  agent: AgentMetadata
  confidence?: number
}

function AgentInfoDisplay({ agent, confidence }: AgentInfoDisplayProps) {
  return (
    <div className="mt-2 pl-4 border-l-2 border-gray-200">
      <div className="text-xs text-gray-600">
        <span className="font-medium">Agent:</span> {agent.role || 'Unknown'}
        {agent.seniority && ` • ${agent.seniority}`}
        {confidence !== undefined && confidence < 0.7 && (
          <span className="text-gray-500"> ({Math.round(confidence * 100)}% confidence)</span>
        )}
      </div>
      {agent.skills && agent.skills.length > 0 && (
        <div className="text-xs text-gray-500 mt-1">
          Skills: {agent.skills.slice(0, 3).join(', ')}
        </div>
      )}
    </div>
  )
}

// 🔧 Tool Execution Display Component
interface ToolExecutionDisplayProps {
  tool: ToolMetadata
  results?: ToolResults
  confidence?: number
}

function ToolExecutionDisplay({ tool, results, confidence }: ToolExecutionDisplayProps) {
  return (
    <div className="mt-2 pl-4 border-l-2 border-gray-200">
      <div className="text-xs text-gray-600">
        <span className="font-medium">Tool:</span> {tool.name || 'Unknown'}
        {tool.success === false && <span className="text-red-600 ml-2">(failed)</span>}
        {tool.execution_time_ms && tool.execution_time_ms > 1000 && (
          <span className="text-gray-500 ml-2">({Math.round(tool.execution_time_ms / 1000)}s)</span>
        )}
      </div>
      {tool.error && (
        <div className="text-xs text-red-600 mt-1">
          Error: {tool.error.substring(0, 100)}
        </div>
      )}
      {results?.summary && (
        <div className="text-xs text-gray-500 mt-1">
          {results.summary}
        </div>
      )}
    </div>
  )
}

// 🤝 Multi-Agent Collaboration Display Component
interface CollaborationDisplayProps {
  collaboration: CollaborationMetadata
}

function CollaborationDisplay({ collaboration }: CollaborationDisplayProps) {
  return (
    <div className="mt-2 pl-4 border-l-2 border-gray-200">
      <div className="text-xs text-gray-600">
        <span className="font-medium">Collaboration:</span> {collaboration.type || 'multi-agent'}
        {collaboration.agents && collaboration.agents.length > 0 && (
          <span className="text-gray-500"> ({collaboration.agents.length} agents)</span>
        )}
      </div>
      {collaboration.agents && collaboration.agents.length > 0 && (
        <div className="text-xs text-gray-500 mt-1">
          Agents: {collaboration.agents.map(a => a.role).filter(Boolean).join(', ')}
        </div>
      )}
    </div>
  )
}