'use client'

import React, { useState, useRef, useEffect } from 'react'
import { ConversationMessage, Chat, TeamActivity } from './types'
import ConversationBubble from './ConversationBubble'
import ConversationInput from './ConversationInput'
import ThinkingProcessViewer from './ThinkingProcessViewer'
import ActionButtonsPanel from './ActionButtonsPanel'
import WelcomeRecapMessage from './WelcomeRecapMessage'
import useFirstVisitWelcome from '../../hooks/useFirstVisitWelcome'

interface ConversationPanelProps {
  activeChat: Chat | null
  messages: ConversationMessage[]
  teamActivities: TeamActivity[]
  thinkingSteps: any[]
  suggestedActions: any[]
  onSendMessage: (message: string) => Promise<void>
  onRefreshMessages?: () => Promise<void>
  loading: boolean
  workspaceId: string
  // 🧠 Real-time thinking props (Claude/o3 style)
  isWebSocketConnected?: boolean
  currentGoalDecomposition?: any
}

export default function ConversationPanel({
  activeChat,
  messages,
  teamActivities,
  thinkingSteps,
  suggestedActions,
  onSendMessage,
  onRefreshMessages,
  loading,
  workspaceId,
  isWebSocketConnected,
  currentGoalDecomposition
}: ConversationPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [activeTab, setActiveTab] = useState<'conversation' | 'thinking'>('conversation')
  
  // 🎉 Welcome message system
  const {
    shouldShowWelcome,
    isFirstVisit,
    markWelcomeShown
  } = useFirstVisitWelcome(workspaceId)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isAtBottom && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isAtBottom])

  // Handle scroll to detect if user is at bottom
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement
    const isBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 100
    setIsAtBottom(isBottom)
  }

  if (!activeChat) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <div className="text-lg font-medium mb-2">Welcome to your AI Team</div>
          <div className="text-sm">
            Select a chat from the sidebar to start collaborating with your team
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <div className="border-b bg-white px-6 py-4 flex-shrink-0">
        <div className="flex items-center space-x-3">
          <span className="text-xl">{activeChat.icon || '💬'}</span>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{activeChat.title}</h2>
            {activeChat.type === 'dynamic' && activeChat.objective && (
              <div className="text-sm text-gray-600">
                {activeChat.objective.description}
              </div>
            )}
          </div>
        </div>
        
        {/* Team Activity Indicator */}
        {teamActivities.length > 0 && (
          <div className="mt-3 flex items-center space-x-2 text-sm text-gray-600">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span>
              Team is working on {teamActivities.length} task{teamActivities.length > 1 ? 's' : ''}...
            </span>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b bg-white">
        <button
          onClick={() => setActiveTab('conversation')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'conversation'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          💬 Conversation
          {messages.length > 0 && (
            <span className="ml-2 bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
              {messages.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('thinking')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'thinking'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          🧠 Thinking
          {/* Real-time connection indicator */}
          {isWebSocketConnected && (
            <span className="ml-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Real-time connected"></span>
          )}
          {thinkingSteps.length > 0 && (
            <span className="ml-2 bg-blue-100 text-blue-600 text-xs px-2 py-0.5 rounded-full">
              {thinkingSteps.length}
            </span>
          )}
          {/* Show decomposition status */}
          {currentGoalDecomposition?.status === 'in_progress' && (
            <span className="ml-1 text-xs text-orange-600 font-medium">LIVE</span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'conversation' ? (
          <div 
            className="h-full overflow-y-auto p-6 space-y-4"
            onScroll={handleScroll}
          >
            {/* 🎉 First visit welcome message */}
            {shouldShowWelcome && activeChat.type === 'fixed' && (
              <WelcomeRecapMessage
                workspaceId={workspaceId}
                onDismiss={markWelcomeShown}
              />
            )}
            
            {messages.length === 0 && !loading && !shouldShowWelcome && (
              <div className="text-center text-gray-500 mt-12">
                <div className="text-2xl mb-2">
                  {activeChat.type === 'fixed' ? '⚙️' : '🎯'}
                </div>
                <div className="text-lg font-medium mb-2">
                  {activeChat.type === 'fixed' ? 'System Chat' : 'Let\'s work on your objective'}
                </div>
                <div className="text-sm">
                  {activeChat.type === 'fixed' 
                    ? 'Configure and manage your team settings'
                    : 'Describe what you\'d like to achieve and I\'ll help you get there'
                  }
                </div>
              </div>
            )}

            {messages.map((message) => (
              <ConversationBubble key={message.id} message={message} />
            ))}

            {/* Team Activity Stream */}
            {teamActivities.length > 0 && (
              <div className="border-l-4 border-blue-200 pl-4 py-2 bg-blue-50 rounded-r-lg">
                <div className="text-sm font-medium text-blue-800 mb-2">
                  🧠 Team is thinking...
                </div>
                <div className="space-y-2">
                  {teamActivities.map((activity) => (
                    <div key={activity.agentId} className="text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-blue-700">
                          {activity.agentName}
                        </span>
                        {activity.eta && (
                          <span className="text-xs text-blue-600">
                            ETA: {activity.eta}
                          </span>
                        )}
                      </div>
                      <div className="text-blue-600">{activity.activity}</div>
                      <div className="w-full bg-blue-200 rounded-full h-1.5 mt-1">
                        <div 
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${activity.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="h-full overflow-y-auto">
            {/* 🧠 Real-time Goal Decomposition Status (Claude/o3 style) */}
            {currentGoalDecomposition && (
              <div className="sticky top-0 z-10 bg-white border-b p-4 mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    currentGoalDecomposition.status === 'in_progress' 
                      ? 'bg-orange-500 animate-pulse' 
                      : currentGoalDecomposition.status === 'completed'
                      ? 'bg-green-500'
                      : 'bg-gray-400'
                  }`}></div>
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {currentGoalDecomposition.status === 'in_progress' ? '🎯 Decomposing Goal...' :
                       currentGoalDecomposition.status === 'completed' ? '✅ Goal Decomposition Complete' :
                       '🎯 Goal Analysis'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {currentGoalDecomposition.goal_name || currentGoalDecomposition.objective || 'Processing objective'}
                    </p>
                  </div>
                  {/* Real-time connection status */}
                  {isWebSocketConnected && (
                    <div className="ml-auto flex items-center text-xs text-green-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                      LIVE
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* WebSocket Connection Status */}
            {!isWebSocketConnected && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mx-4 mb-4">
                <div className="flex items-center space-x-2 text-sm text-yellow-800">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Real-time thinking updates are currently disconnected</span>
                </div>
              </div>
            )}

            {/* Show thinking steps from current conversation + any saved steps from messages */}
            {(() => {
              const allThinkingSteps = [...thinkingSteps];
              
              // Add thinking steps from saved messages
              messages.forEach(message => {
                if (message.metadata?.thinking_steps && Array.isArray(message.metadata.thinking_steps)) {
                  message.metadata.thinking_steps.forEach((step: any) => {
                    allThinkingSteps.push({
                      ...step,
                      fromMessage: message.id,
                      messageTimestamp: message.timestamp
                    });
                  });
                }
              });
              
              return <ThinkingProcessViewer 
                steps={allThinkingSteps} 
                isThinking={loading} 
                isRealTime={isWebSocketConnected}
                currentDecomposition={currentGoalDecomposition}
              />;
            })()}
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      {!isAtBottom && (
        <div className="absolute bottom-24 right-8">
          <button
            onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })}
            className="bg-white border border-gray-300 rounded-full p-2 shadow-lg hover:shadow-xl transition-shadow"
            title="Scroll to bottom"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>
        </div>
      )}

      {/* Suggested Actions */}
      {suggestedActions.length > 0 && (
        <div className="flex-shrink-0">
          <ActionButtonsPanel
            actions={suggestedActions}
            workspaceId={workspaceId}
            onActionExecuted={async (result) => {
              console.log('Action executed:', result)
              // Refresh messages to show the action result
              if (onRefreshMessages) {
                await onRefreshMessages()
              }
            }}
          />
        </div>
      )}

      {/* Input */}
      <div className="flex-shrink-0">
        <ConversationInput
          activeChat={activeChat}
          onSendMessage={onSendMessage}
          loading={loading}
          workspaceId={workspaceId}
        />
      </div>
    </div>
  )
}