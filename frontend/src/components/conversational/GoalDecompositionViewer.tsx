'use client'

import React, { useState, useEffect } from 'react'

interface AssetTodo {
  id: string
  type: 'asset'
  name: string
  description: string
  value_proposition: string
  completion_criteria: string
  priority: 'high' | 'medium' | 'low'
  estimated_effort: 'low' | 'medium' | 'high'
  user_impact: 'immediate' | 'short-term' | 'long-term'
  deliverable_type: 'concrete_asset'
  completed?: boolean
}

interface ThinkingTodo {
  id: string
  type: 'thinking'
  name: string
  description: string
  supports_assets: string[]
  complexity: 'simple' | 'medium' | 'complex'
  priority: 'medium'
  deliverable_type: 'strategic_thinking'
  completed?: boolean
}

interface GoalDecomposition {
  goal_id: string
  asset_todos: AssetTodo[]
  thinking_todos: ThinkingTodo[]
  completion_flow: {
    asset_dependency_chain: string[]
    thinking_support_map: Record<string, string[]>
    final_deliverable: {
      name: string
      components: string[]
      thinking_support: string[]
      user_value_score: number
    }
  }
  expected_user_value: number
}

interface GoalDecompositionViewerProps {
  goalId: string
  goalDescription: string
  goalProgress: number
  onTodoComplete?: (todoId: string, todoType: 'asset' | 'thinking') => void
}

export default function GoalDecompositionViewer({
  goalId,
  goalDescription,
  goalProgress,
  onTodoComplete
}: GoalDecompositionViewerProps) {
  const [decomposition, setDecomposition] = useState<GoalDecomposition | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'assets' | 'thinking' | 'overview'>('assets')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadGoalDecomposition()
  }, [goalId])

  const loadGoalDecomposition = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // In real implementation, this would call the backend API
      // For now, simulate the decomposition based on goal description
      const simulatedDecomposition = generateSimulatedDecomposition(goalDescription)
      setDecomposition(simulatedDecomposition)
      
    } catch (err: any) {
      setError(err.message || 'Failed to load goal decomposition')
    } finally {
      setLoading(false)
    }
  }

  const generateSimulatedDecomposition = (description: string): GoalDecomposition => {
    const isContent = description.toLowerCase().includes('content') || 
                     description.toLowerCase().includes('post') ||
                     description.toLowerCase().includes('social')
    
    const isResearch = description.toLowerCase().includes('research') ||
                      description.toLowerCase().includes('analysis') ||
                      description.toLowerCase().includes('study')
    
    const isPlan = description.toLowerCase().includes('plan') ||
                  description.toLowerCase().includes('strategy') ||
                  description.toLowerCase().includes('roadmap')

    let assetTodos: AssetTodo[] = []
    let thinkingTodos: ThinkingTodo[] = []

    if (isContent) {
      assetTodos = [
        {
          id: 'asset_1',
          type: 'asset',
          name: 'Content Library',
          description: 'Ready-to-publish content pieces with engaging copy and visuals',
          value_proposition: 'Immediate publishing capability across social channels',
          completion_criteria: 'Each piece tested and optimized for target platform',
          priority: 'high',
          estimated_effort: 'medium',
          user_impact: 'immediate',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 50
        },
        {
          id: 'asset_2', 
          type: 'asset',
          name: 'Content Calendar',
          description: 'Publishing schedule with optimal timing and distribution channels',
          value_proposition: 'Organized content deployment for maximum reach',
          completion_criteria: 'Calendar with specific dates, times, and platform assignments',
          priority: 'high',
          estimated_effort: 'low',
          user_impact: 'immediate',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 70
        }
      ]
      
      thinkingTodos = [
        {
          id: 'thinking_1',
          type: 'thinking',
          name: 'Content Strategy Analysis',
          description: 'Research target audience preferences and content performance patterns',
          supports_assets: ['Content Library', 'Content Calendar'],
          complexity: 'medium',
          priority: 'medium',
          deliverable_type: 'strategic_thinking',
          completed: goalProgress >= 30
        }
      ]
    } else if (isResearch) {
      assetTodos = [
        {
          id: 'asset_1',
          type: 'asset',
          name: 'Research Report',
          description: 'Comprehensive analysis document with findings and recommendations',
          value_proposition: 'Actionable insights for strategic decision making',
          completion_criteria: 'Report with executive summary and clear action items',
          priority: 'high',
          estimated_effort: 'high',
          user_impact: 'long-term',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 80
        },
        {
          id: 'asset_2',
          type: 'asset',
          name: 'Executive Summary',
          description: 'One-page summary with key findings and recommendations',
          value_proposition: 'Quick reference for leadership decisions',
          completion_criteria: 'Summary with clear next steps and priorities',
          priority: 'high',
          estimated_effort: 'low',
          user_impact: 'immediate',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 90
        }
      ]
      
      thinkingTodos = [
        {
          id: 'thinking_1',
          type: 'thinking',
          name: 'Data Collection Strategy',
          description: 'Plan for gathering and validating research information',
          supports_assets: ['Research Report'],
          complexity: 'medium',
          priority: 'medium',
          deliverable_type: 'strategic_thinking',
          completed: goalProgress >= 40
        }
      ]
    } else if (isPlan) {
      assetTodos = [
        {
          id: 'asset_1',
          type: 'asset',
          name: 'Strategic Plan Document',
          description: 'Complete planning document with timelines and milestones',
          value_proposition: 'Clear execution roadmap for goal achievement',
          completion_criteria: 'Plan with specific milestones and resource allocation',
          priority: 'high',
          estimated_effort: 'high',
          user_impact: 'long-term',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 85
        }
      ]
      
      thinkingTodos = [
        {
          id: 'thinking_1',
          type: 'thinking',
          name: 'Strategic Analysis',
          description: 'Environmental scan and capability assessment',
          supports_assets: ['Strategic Plan Document'],
          complexity: 'complex',
          priority: 'medium',
          deliverable_type: 'strategic_thinking',
          completed: goalProgress >= 60
        }
      ]
    } else {
      // Universal fallback
      assetTodos = [
        {
          id: 'asset_1',
          type: 'asset',
          name: 'Goal Achievement Package',
          description: 'Complete deliverable package for goal completion',
          value_proposition: 'Concrete results aligned with stated objectives',
          completion_criteria: 'All goal requirements met with documentation',
          priority: 'high',
          estimated_effort: 'medium',
          user_impact: 'immediate',
          deliverable_type: 'concrete_asset',
          completed: goalProgress >= 90
        }
      ]
      
      thinkingTodos = [
        {
          id: 'thinking_1',
          type: 'thinking',
          name: 'Goal Planning Process',
          description: 'Strategic approach to goal achievement',
          supports_assets: ['Goal Achievement Package'],
          complexity: 'simple',
          priority: 'medium',
          deliverable_type: 'strategic_thinking',
          completed: goalProgress >= 50
        }
      ]
    }

    return {
      goal_id: goalId,
      asset_todos: assetTodos,
      thinking_todos: thinkingTodos,
      completion_flow: {
        asset_dependency_chain: assetTodos.map(a => a.id),
        thinking_support_map: {
          [thinkingTodos[0]?.id || 'thinking_1']: assetTodos.map(a => a.name)
        },
        final_deliverable: {
          name: `Complete Goal Package: ${description}`,
          components: assetTodos.map(a => a.name),
          thinking_support: thinkingTodos.map(t => t.name),
          user_value_score: 85
        }
      },
      expected_user_value: 85
    }
  }

  const handleTodoComplete = (todoId: string, todoType: 'asset' | 'thinking') => {
    if (onTodoComplete) {
      onTodoComplete(todoId, todoType)
    }
    
    // Update local state
    setDecomposition(prev => {
      if (!prev) return prev
      
      if (todoType === 'asset') {
        return {
          ...prev,
          asset_todos: prev.asset_todos.map(todo =>
            todo.id === todoId ? { ...todo, completed: true } : todo
          )
        }
      } else {
        return {
          ...prev,
          thinking_todos: prev.thinking_todos.map(todo =>
            todo.id === todoId ? { ...todo, completed: true } : todo
          )
        }
      }
    })
  }

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'immediate': return 'bg-blue-100 text-blue-800'
      case 'short-term': return 'bg-purple-100 text-purple-800'
      case 'long-term': return 'bg-indigo-100 text-indigo-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'complex': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading goal decomposition...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-red-500 text-sm">{error}</div>
        <button 
          onClick={loadGoalDecomposition}
          className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!decomposition) {
    return (
      <div className="p-6 text-center text-gray-500">
        No decomposition available for this goal
      </div>
    )
  }

  const completedAssets = decomposition.asset_todos.filter(t => t.completed).length
  const completedThinking = decomposition.thinking_todos.filter(t => t.completed).length
  const totalAssets = decomposition.asset_todos.length
  const totalThinking = decomposition.thinking_todos.length

  return (
    <div className="space-y-6">
      {/* Header with Goal Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Goal Decomposition</h2>
        <p className="text-sm text-gray-700 mb-3">{goalDescription}</p>
        
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{completedAssets}/{totalAssets}</div>
            <div className="text-gray-600">Assets Ready</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{completedThinking}/{totalThinking}</div>
            <div className="text-gray-600">Thinking Complete</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{decomposition.expected_user_value}</div>
            <div className="text-gray-600">Expected Value</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('assets')}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'assets'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          📦 Assets ({totalAssets})
        </button>
        <button
          onClick={() => setActiveTab('thinking')}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'thinking'
              ? 'bg-white text-purple-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          🧠 Thinking ({totalThinking})
        </button>
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'overview'
              ? 'bg-white text-green-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          🎯 Overview
        </button>
      </div>

      {/* Content */}
      {activeTab === 'assets' && (
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900 flex items-center">
            <span className="text-blue-500 mr-2">📦</span>
            Concrete Deliverables for User
          </h3>
          {decomposition.asset_todos.map((asset) => (
            <div
              key={asset.id}
              className={`border rounded-lg p-4 ${
                asset.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 flex items-center">
                    {asset.completed && <span className="text-green-500 mr-2">✅</span>}
                    {asset.name}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">{asset.description}</p>
                </div>
                
                <div className="flex flex-col space-y-1 ml-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getEffortColor(asset.estimated_effort)}`}>
                    {asset.estimated_effort} effort
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getImpactColor(asset.user_impact)}`}>
                    {asset.user_impact}
                  </span>
                </div>
              </div>
              
              <div className="bg-blue-50 rounded p-3 mb-3">
                <div className="text-sm font-medium text-blue-800 mb-1">💎 Value Proposition</div>
                <div className="text-sm text-blue-700">{asset.value_proposition}</div>
              </div>
              
              <div className="text-xs text-gray-500">
                <span className="font-medium">Completion Criteria:</span> {asset.completion_criteria}
              </div>
              
              {!asset.completed && (
                <button
                  onClick={() => handleTodoComplete(asset.id, 'asset')}
                  className="mt-3 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                >
                  Mark Complete
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'thinking' && (
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900 flex items-center">
            <span className="text-purple-500 mr-2">🧠</span>
            Strategic Thinking & Planning
          </h3>
          {decomposition.thinking_todos.map((thinking) => (
            <div
              key={thinking.id}
              className={`border rounded-lg p-4 ${
                thinking.completed ? 'bg-purple-50 border-purple-200' : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 flex items-center">
                    {thinking.completed && <span className="text-purple-500 mr-2">✅</span>}
                    {thinking.name}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">{thinking.description}</p>
                </div>
                
                <span className={`px-2 py-1 text-xs rounded-full ${getComplexityColor(thinking.complexity)}`}>
                  {thinking.complexity}
                </span>
              </div>
              
              <div className="bg-purple-50 rounded p-3 mb-3">
                <div className="text-sm font-medium text-purple-800 mb-1">🔗 Supports Assets</div>
                <div className="text-sm text-purple-700">
                  {thinking.supports_assets.join(', ')}
                </div>
              </div>
              
              {!thinking.completed && (
                <button
                  onClick={() => handleTodoComplete(thinking.id, 'thinking')}
                  className="mt-3 px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition-colors"
                >
                  Mark Complete
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'overview' && (
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900 flex items-center">
            <span className="text-green-500 mr-2">🎯</span>
            Goal Completion Overview
          </h3>
          
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">
              {decomposition.completion_flow.final_deliverable.name}
            </h4>
            <div className="text-sm text-gray-700 mb-4">
              User Value Score: <span className="font-medium text-green-600">
                {decomposition.completion_flow.final_deliverable.user_value_score}/100
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-800 mb-2">📦 Asset Components</div>
                <ul className="space-y-1">
                  {decomposition.completion_flow.final_deliverable.components.map((component, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-center">
                      <span className="text-blue-500 mr-2">•</span>
                      {component}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <div className="text-sm font-medium text-gray-800 mb-2">🧠 Thinking Support</div>
                <ul className="space-y-1">
                  {decomposition.completion_flow.final_deliverable.thinking_support.map((support, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-center">
                      <span className="text-purple-500 mr-2">•</span>
                      {support}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="text-sm text-amber-700">
              <span className="font-medium">🔒 Completion Guarantee:</span> This goal will receive deliverables 
              regardless of business score once it reaches 90% progress, ensuring no work is lost.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}