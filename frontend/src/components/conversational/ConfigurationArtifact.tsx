'use client'

import React, { useState } from 'react'
import { api } from '@/utils/api'
import { WorkspaceHealthMonitor } from '../WorkspaceHealthMonitor'

interface ConfigurationArtifactProps {
  configuration: any
  workspaceId: string
  onConfigUpdate?: (updatedConfig: any) => void
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onCheckWorkspaceHealth?: () => Promise<any>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

export default function ConfigurationArtifact({ 
  configuration, 
  workspaceId, 
  onConfigUpdate,
  workspaceHealthStatus,
  healthLoading,
  onUnblockWorkspace,
  onCheckWorkspaceHealth,
  onResumeAutoGeneration
}: ConfigurationArtifactProps) {
  const [activeView, setActiveView] = useState<'general' | 'goals' | 'health' | 'advanced' | 'danger'>('general')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

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
                    message: `I need help with my workspace configuration. Can you explain the current settings and suggest any optimizations?\n\nCurrent configuration summary:\n- Max iterations: ${configuration.budget?.max_iterations || 3}\n- Quality threshold: ${configuration.budget?.settings?.quality_threshold || 85}%\n\nPlease provide guidance on these settings and any recommended adjustments. For budget information, please check the Budget & Usage chat.`
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
            active={activeView === 'health'}
            onClick={() => setActiveView('health')}
            label="Health"
            icon="🏥"
          />
          <ViewTab
            active={activeView === 'advanced'}
            onClick={() => setActiveView('advanced')}
            label="Advanced"
            icon="🔧"
          />
          <ViewTab
            active={activeView === 'danger'}
            onClick={() => setActiveView('danger')}
            label="Danger"
            icon="⚠️"
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
        
        
        {activeView === 'health' && (
          <HealthConfigTab 
            workspaceHealthStatus={workspaceHealthStatus}
            healthLoading={healthLoading}
            onUnblockWorkspace={onUnblockWorkspace}
            onCheckWorkspaceHealth={onCheckWorkspaceHealth}
            onResumeAutoGeneration={onResumeAutoGeneration}
          />
        )}
        
        {activeView === 'advanced' && (
          <AdvancedConfigTab configuration={configuration} />
        )}
        
        {activeView === 'danger' && (
          <DangerZoneTab 
            configuration={configuration} 
            workspaceId={workspaceId}
            showDeleteConfirm={showDeleteConfirm}
            setShowDeleteConfirm={setShowDeleteConfirm}
          />
        )}
      </div>
      
      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-red-600 mb-4">Delete Workspace</h3>
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete "{configuration.name || 'this workspace'}"? 
              This will permanently delete all tasks, agents, goals, and deliverables associated with this project.
              <br /><br />
              <strong>This action cannot be undone.</strong>
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  try {
                    // Use the same API call as the working Settings page
                    const success = await api.workspaces.delete(workspaceId)
                    
                    if (success) {
                      // Redirect to projects page
                      window.location.href = '/projects'
                    } else {
                      alert('Failed to delete workspace. Please try again.')
                    }
                  } catch (error) {
                    console.error('Error deleting workspace:', error)
                    alert('Error deleting workspace. Please try again.')
                  }
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete Workspace
              </button>
            </div>
          </div>
        </div>
      )}
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

      {/* Budget Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center space-x-2">
          <span className="text-blue-600">💰</span>
          <p className="text-sm text-blue-800">
            For budget and usage information, please check the <strong>Budget & Usage</strong> chat in the conversation panel.
          </p>
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

// Danger Zone Tab
function DangerZoneTab({ 
  configuration, 
  workspaceId,
  showDeleteConfirm,
  setShowDeleteConfirm
}: { 
  configuration: any
  workspaceId: string
  showDeleteConfirm: boolean
  setShowDeleteConfirm: (show: boolean) => void
}) {
  return (
    <div className="p-4 space-y-6">
      {/* Warning Header */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-red-600 text-lg">⚠️</span>
          <h4 className="text-lg font-semibold text-red-600">Danger Zone</h4>
        </div>
        <p className="text-red-700 text-sm">
          Actions in this section are permanent and cannot be undone. Please proceed with extreme caution.
        </p>
      </div>

      {/* Delete Workspace Section */}
      <div className="bg-white border border-red-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Delete Workspace</h4>
            <p className="text-sm text-gray-600 mb-3">
              Permanently delete this workspace and all associated data including:
            </p>
            <ul className="text-xs text-gray-500 space-y-1 mb-4">
              <li>• All tasks and their execution history</li>
              <li>• All team members and their configurations</li>
              <li>• All goals and progress tracking</li>
              <li>• All deliverables and project assets</li>
              <li>• All conversation history and artifacts</li>
              <li>• All feedback requests and quality assessments</li>
            </ul>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
              <div className="flex items-center space-x-2">
                <span className="text-yellow-600">⚠️</span>
                <span className="text-yellow-800 text-sm font-medium">
                  This action cannot be undone and will affect all team members.
                </span>
              </div>
            </div>
          </div>
          <div className="ml-4">
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Delete Workspace
            </button>
          </div>
        </div>
      </div>

      {/* Workspace Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Workspace Information</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Name:</span>
            <span className="ml-2 font-medium">{configuration.name || 'Untitled'}</span>
          </div>
          <div>
            <span className="text-gray-600">ID:</span>
            <span className="ml-2 font-mono text-xs">{workspaceId}</span>
          </div>
          <div>
            <span className="text-gray-600">Created:</span>
            <span className="ml-2">
              {configuration.created_at ? new Date(configuration.created_at).toLocaleDateString() : 'Unknown'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Status:</span>
            <span className="ml-2 capitalize">{configuration.status || 'Unknown'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Health Configuration Tab
function HealthConfigTab({ 
  workspaceHealthStatus,
  healthLoading,
  onUnblockWorkspace,
  onCheckWorkspaceHealth,
  onResumeAutoGeneration
}: {
  workspaceHealthStatus?: any
  healthLoading?: boolean
  onUnblockWorkspace?: (reason?: string) => Promise<{ success: boolean; message: string }>
  onCheckWorkspaceHealth?: () => Promise<any>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}) {
  return (
    <div className="p-4">
      <div className="mb-4">
        <h4 className="text-lg font-semibold text-gray-900 mb-2">Workspace Health Monitoring</h4>
        <p className="text-sm text-gray-600">
          Monitor your workspace health, identify issues, and take corrective actions to ensure smooth operation.
        </p>
      </div>
      
      <WorkspaceHealthMonitor
        workspaceHealthStatus={workspaceHealthStatus}
        healthLoading={healthLoading || false}
        onUnblock={onUnblockWorkspace || (async () => ({ success: false, message: 'Not available' }))}
        onRefresh={onCheckWorkspaceHealth || (async () => null)}
        onResumeAutoGeneration={onResumeAutoGeneration}
      />
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