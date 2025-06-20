'use client'

import React, { useState } from 'react'

interface ConfigurationArtifactProps {
  configuration: any
  workspaceId: string
  onConfigUpdate?: (updatedConfig: any) => void
}

export default function ConfigurationArtifact({ 
  configuration, 
  workspaceId, 
  onConfigUpdate 
}: ConfigurationArtifactProps) {
  const [activeView, setActiveView] = useState<'general' | 'goals' | 'budget' | 'advanced'>('general')

  if (!configuration) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-3xl mb-3">⚙️</div>
          <div className="text-lg font-medium mb-2">No Configuration</div>
          <div className="text-sm">Configuration data not available</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with view tabs */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            ⚙️ Workspace Configuration
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.open(`/projects/${workspaceId}/configure`, '_blank')}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
              title="Open configuration editor in new tab"
            >
              ⚙️ Edit Settings
            </button>
            <button
              onClick={() => {
                if (onConfigUpdate) {
                  onConfigUpdate({ 
                    action: 'send_message', 
                    message: `I need help with my workspace configuration. Can you explain the current settings and suggest any optimizations?\n\nCurrent configuration summary:\n- Budget: $${configuration.budget?.max_budget || 10}\n- Max iterations: ${configuration.budget?.max_iterations || 3}\n- Quality threshold: ${configuration.budget?.settings?.quality_threshold || 85}%\n\nPlease provide guidance on these settings and any recommended adjustments.`
                  })
                }
              }}
              className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors"
              title="Get AI help with configuration via chat"
            >
              💬 Ask AI
            </button>
          </div>
        </div>
        
        <div className="flex space-x-1 overflow-x-auto">
          <ViewTab
            active={activeView === 'general'}
            onClick={() => setActiveView('general')}
            label="General"
            icon="🏠"
          />
          <ViewTab
            active={activeView === 'goals'}
            onClick={() => setActiveView('goals')}
            label="Goals"
            icon="🎯"
          />
          <ViewTab
            active={activeView === 'budget'}
            onClick={() => setActiveView('budget')}
            label="Budget"
            icon="💰"
          />
          <ViewTab
            active={activeView === 'advanced'}
            onClick={() => setActiveView('advanced')}
            label="Advanced"
            icon="🔧"
          />
        </div>
      </div>

      {/* Content based on active view */}
      <div className="flex-1 overflow-y-auto">
        {activeView === 'general' && (
          <GeneralConfigTab configuration={configuration} />
        )}
        
        {activeView === 'goals' && (
          <GoalsConfigTab configuration={configuration} />
        )}
        
        {activeView === 'budget' && (
          <BudgetConfigTab configuration={configuration} />
        )}
        
        {activeView === 'advanced' && (
          <AdvancedConfigTab configuration={configuration} />
        )}
      </div>
    </div>
  )
}

// View Tab Component
interface ViewTabProps {
  active: boolean
  onClick: () => void
  label: string
  icon: string
}

function ViewTab({ active, onClick, label, icon }: ViewTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap
        ${active
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }
      `}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  )
}

// General Configuration Tab
function GeneralConfigTab({ configuration }: { configuration: any }) {
  return (
    <div className="p-4 space-y-6">
      {/* Basic Information */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
            <div className="text-sm text-gray-900 p-2 bg-gray-50 rounded border">
              {configuration.name || 'Untitled Project'}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <div className="text-sm text-gray-900 p-2 bg-gray-50 rounded border min-h-[60px]">
              {configuration.description || 'No description provided'}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Goal</label>
            <div className="text-sm text-gray-900 p-2 bg-gray-50 rounded border min-h-[60px]">
              {configuration.goal || 'No goal specified'}
            </div>
          </div>
        </div>
      </div>

      {/* Project Status Overview */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Project Status</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-sm text-blue-700 mb-1">Status</div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                configuration.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
              }`} />
              <span className="text-lg font-semibold text-blue-800 capitalize">
                {configuration.status || 'Unknown'}
              </span>
            </div>
          </div>
          
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-sm text-green-700 mb-1">Created</div>
            <div className="text-lg font-semibold text-green-800">
              {configuration.created_at ? new Date(configuration.created_at).toLocaleDateString() : 'Unknown'}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {configuration.budget?.max_budget || 10}
          </div>
          <div className="text-sm text-gray-600">Budget ($)</div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {configuration.budget?.max_iterations || 3}
          </div>
          <div className="text-sm text-gray-600">Max Iterations</div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">
            {configuration.budget?.settings?.quality_threshold || 85}%
          </div>
          <div className="text-sm text-gray-600">Quality Threshold</div>
        </div>
      </div>
    </div>
  )
}

// Goals Configuration Tab
function GoalsConfigTab({ configuration }: { configuration: any }) {
  return (
    <div className="p-4 space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Primary Goal</h4>
        <div className="text-sm text-gray-700 whitespace-pre-wrap">
          {configuration.goal || 'No goal specified'}
        </div>
      </div>

      {configuration.success_criteria && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Success Criteria</h4>
          <div className="text-sm text-gray-700">
            {configuration.success_criteria}
          </div>
        </div>
      )}

      {configuration.timeline_months && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Timeline</h4>
          <div className="flex items-center space-x-2">
            <div className="text-2xl font-bold text-blue-600">
              {configuration.timeline_months}
            </div>
            <div className="text-sm text-gray-700">months</div>
          </div>
        </div>
      )}
    </div>
  )
}

// Budget Configuration Tab
function BudgetConfigTab({ configuration }: { configuration: any }) {
  const budget = configuration.budget || {}
  const settings = budget.settings || {}
  
  return (
    <div className="p-4 space-y-6">
      {/* Budget & Basic Limits */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Budget & Basic Limits</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Budget ($)</label>
            <div className="text-2xl font-bold text-blue-600 p-2 bg-blue-50 rounded border text-center">
              ${budget.max_budget || 10}
            </div>
            <p className="text-xs text-gray-500 mt-1">AI usage cost limit for this project</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Iterations per Task</label>
            <div className="text-2xl font-bold text-purple-600 p-2 bg-purple-50 rounded border text-center">
              {budget.max_iterations || 3}
            </div>
            <p className="text-xs text-gray-500 mt-1">Maximum improvement loops per task</p>
          </div>
        </div>
      </div>

      {/* Budget Usage */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Budget Usage</h4>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Used</span>
            <span className="font-medium">${configuration.budget_used || 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Remaining</span>
            <span className="font-medium text-green-600">
              ${(budget.max_budget || 10) - (configuration.budget_used || 0)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full" 
              style={{ 
                width: `${((configuration.budget_used || 0) / (budget.max_budget || 10)) * 100}%` 
              }}
            />
          </div>
          <div className="text-xs text-gray-500 text-center">
            {(((configuration.budget_used || 0) / (budget.max_budget || 10)) * 100).toFixed(1)}% used
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-lg font-bold text-green-600">
            {settings.max_concurrent_tasks || 3}
          </div>
          <div className="text-sm text-gray-600">Concurrent Tasks</div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-lg font-bold text-orange-600">
            {settings.task_timeout || 150}s
          </div>
          <div className="text-sm text-gray-600">Task Timeout</div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
          <div className="text-lg font-bold text-indigo-600">
            {settings.max_deliverables || 3}
          </div>
          <div className="text-sm text-gray-600">Max Deliverables</div>
        </div>
      </div>
    </div>
  )
}

// Advanced Configuration Tab
function AdvancedConfigTab({ configuration }: { configuration: any }) {
  const advancedFields = [
    'auto_mode',
    'max_agents',
    'task_timeout',
    'retry_limit',
    'notification_settings',
    'api_limits',
    'security_level'
  ]

  return (
    <div className="p-4 space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Advanced Settings</h4>
        <div className="space-y-3">
          {advancedFields.map(field => {
            const value = configuration[field]
            if (value === undefined || value === null) return null
            
            return (
              <ConfigField 
                key={field}
                label={field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                value={typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : String(value)}
              />
            )
          })}
        </div>
      </div>

      {/* Raw Configuration */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Raw Configuration</h4>
        <pre className="text-xs text-gray-600 overflow-x-auto bg-white p-3 rounded border">
          {JSON.stringify(configuration, null, 2)}
        </pre>
      </div>
    </div>
  )
}

// Config Field Component
function ConfigField({ 
  label, 
  value, 
  multiline = false 
}: { 
  label: string
  value: any
  multiline?: boolean 
}) {
  const displayValue = value || 'Not set'
  
  return (
    <div className="flex flex-col space-y-1">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </div>
      <div className={`text-sm text-gray-900 ${multiline ? 'whitespace-pre-wrap' : ''}`}>
        {displayValue}
      </div>
    </div>
  )
}