'use client'

import React, { useState } from 'react'

interface SuggestedAction {
  tool: string
  label: string
  description: string
  parameters?: Record<string, any>
  type: 'info' | 'action' | 'warning'
}

interface ActionButtonsPanelProps {
  actions: SuggestedAction[]
  workspaceId: string
  onActionExecuted?: (result: any) => void
}

export default function ActionButtonsPanel({ 
  actions, 
  workspaceId, 
  onActionExecuted 
}: ActionButtonsPanelProps) {
  const [executingAction, setExecutingAction] = useState<string | null>(null)
  const [executedActions, setExecutedActions] = useState<Set<string>>(new Set())
  const [actionResults, setActionResults] = useState<Record<string, any>>({})

  // Filter out executed actions
  const availableActions = actions.filter(action => !executedActions.has(action.tool))
  const hasResults = Object.keys(actionResults).length > 0
  
  if (availableActions.length === 0 && !hasResults) {
    return null
  }

  const executeAction = async (action: SuggestedAction) => {
    if (executingAction) return // Prevent multiple simultaneous executions

    setExecutingAction(action.tool)

    try {
      console.log('🔧 [ActionButtonsPanel] Executing action:', action.tool)
      
      const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/execute-action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool: action.tool,
          parameters: action.parameters || {},
          chat_id: 'general'
        })
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('✅ [ActionButtonsPanel] Action executed successfully:', result)
        
        // Mark action as executed and store result
        setExecutedActions(prev => new Set([...prev, action.tool]))
        setActionResults(prev => ({ ...prev, [action.tool]: result }))
        
        onActionExecuted?.(result)
      } else {
        console.error('❌ [ActionButtonsPanel] Action failed:', result.error)
        alert(`Action failed: ${result.error}`)
      }
    } catch (error) {
      console.error('❌ [ActionButtonsPanel] Error executing action:', error)
      alert(`Error executing action: ${error.message}`)
    } finally {
      setExecutingAction(null)
    }
  }

  const getButtonStyle = (type: string) => {
    switch (type) {
      case 'info':
        return 'bg-blue-500 hover:bg-blue-600 text-white border-blue-500'
      case 'action':
        return 'bg-green-500 hover:bg-green-600 text-white border-green-500'
      case 'warning':
        return 'bg-orange-500 hover:bg-orange-600 text-white border-orange-500'
      default:
        return 'bg-gray-500 hover:bg-gray-600 text-white border-gray-500'
    }
  }

  return (
    <div className="border-t border-gray-200 p-4 bg-gray-50">
      {/* Available Actions */}
      {availableActions.length > 0 && (
        <>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-medium text-gray-700">Suggested Actions:</span>
            <span className="text-xs text-gray-500">({availableActions.length})</span>
          </div>
          
          <div className="flex flex-wrap gap-2 mb-3">
            {availableActions.map((action, index) => (
              <ActionButton
                key={index}
                action={action}
                isExecuting={executingAction === action.tool}
                onClick={() => executeAction(action)}
                style={getButtonStyle(action.type)}
              />
            ))}
          </div>
        </>
      )}
      
      {/* Execution Status */}
      {executingAction && (
        <div className="mb-3 text-xs text-blue-600 flex items-center gap-1">
          <div className="animate-spin w-3 h-3 border border-blue-600 border-t-transparent rounded-full"></div>
          Executing {actions.find(a => a.tool === executingAction)?.label}...
        </div>
      )}
      
      {/* Action Results */}
      {hasResults && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700 mb-2">Action Results:</div>
          {Object.entries(actionResults).map(([tool, result]) => {
            const action = actions.find(a => a.tool === tool)
            return (
              <div key={tool} className="bg-white border border-green-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm font-medium text-gray-900">
                    {action?.label || tool}
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  {result.message || 'Action completed successfully'}
                </div>
                {result.data && (
                  <div className="mt-2 text-xs text-gray-500 bg-gray-50 p-2 rounded">
                    <pre>{JSON.stringify(result.data, null, 2)}</pre>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface ActionButtonProps {
  action: SuggestedAction
  isExecuting: boolean
  onClick: () => void
  style: string
}

function ActionButton({ action, isExecuting, onClick, style }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isExecuting}
      className={`
        px-3 py-2 rounded-lg text-sm font-medium border transition-all duration-200
        ${style}
        ${isExecuting ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md'}
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
      title={action.description}
    >
      <div className="flex items-center gap-2">
        {isExecuting ? (
          <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin"></div>
        ) : (
          <span>{action.label}</span>
        )}
      </div>
    </button>
  )
}