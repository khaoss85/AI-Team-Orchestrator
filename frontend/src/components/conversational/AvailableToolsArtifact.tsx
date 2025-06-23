'use client'

import React, { useState } from 'react'

interface ToolData {
  name: string
  label: string
  description: string
  parameters: Record<string, any>
}

interface ToolCategory {
  title: string
  icon: string
  tools: ToolData[]
}

interface SlashCommand {
  command: string
  description: string
}

interface Integration {
  name: string
  status: string
  features: string[]
}

interface AvailableToolsData {
  tools: ToolData[]
  categories: Record<string, ToolCategory>
  slash_commands: SlashCommand[]
  integrations: Integration[]
  capabilities: string[]
}

interface AvailableToolsArtifactProps {
  toolsData: AvailableToolsData
  workspaceId: string
  onToolExecute?: (toolName: string, parameters?: Record<string, any>) => void
}

export default function AvailableToolsArtifact({ 
  toolsData, 
  workspaceId, 
  onToolExecute 
}: AvailableToolsArtifactProps) {
  const [activeTab, setActiveTab] = useState<'tools' | 'integrations'>('tools')
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)


  const handleToolExecute = (toolName: string, parameters?: Record<string, any>) => {
    if (onToolExecute) {
      onToolExecute(toolName, parameters)
    }
  }

  return (
    <div className="">
      {/* Minimal Header */}
      <div className="border-b border-gray-100 pb-4 mb-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Available Tools</h1>
        <p className="text-gray-600 text-sm">
          <span className="font-medium">{toolsData?.tools?.length || 0}</span> native tools available
        </p>
      </div>

      {/* Simplified Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <TabButton 
          active={activeTab === 'tools'} 
          onClick={() => setActiveTab('tools')}
          label="Native Tools"
        />
        <TabButton 
          active={activeTab === 'integrations'} 
          onClick={() => setActiveTab('integrations')}
          label="Integrations"
        />
      </div>

      {/* Content */}
      <div className="px-4 pb-4">
        {activeTab === 'tools' && (
          <ToolsTab 
            categories={toolsData.categories || {}} 
            expandedCategory={expandedCategory}
            onToggleCategory={setExpandedCategory}
            onToolExecute={handleToolExecute}
            slashCommands={toolsData.slash_commands || []}
          />
        )}
        
        {activeTab === 'integrations' && (
          <IntegrationsTab 
            integrations={toolsData.integrations || []} 
            capabilities={toolsData.capabilities || []}
          />
        )}
      </div>
    </div>
  )
}

// Tab Button Component
interface TabButtonProps {
  active: boolean
  onClick: () => void
  label: string
}

function TabButton({ active, onClick, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        px-4 py-2 text-sm font-medium border-b-2 transition-colors
        ${active
          ? 'text-blue-600 border-blue-600'
          : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
        }
      `}
    >
      {label}
    </button>
  )
}

// Tools Tab Component
interface ToolsTabProps {
  categories: Record<string, ToolCategory>
  expandedCategory: string | null
  onToggleCategory: (category: string | null) => void
  onToolExecute: (toolName: string, parameters?: Record<string, any>) => void
}

function ToolsTab({ categories, expandedCategory, onToggleCategory, onToolExecute }: ToolsTabProps) {
  if (!categories || Object.keys(categories).length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-2xl mb-2">🔧</div>
        <div>No tool categories available</div>
      </div>
    )
  }
  
  return (
    <div className="space-y-3">
      {Object.entries(categories).map(([categoryKey, category]) => (
        <div key={categoryKey} className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => onToggleCategory(
              expandedCategory === categoryKey ? null : categoryKey
            )}
            className="w-full p-4 text-left bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-xl">{category.icon}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{category.title}</h3>
                  <p className="text-sm text-gray-600">
                    {category.tools?.length || 0} tools available
                  </p>
                </div>
              </div>
              <svg 
                className={`w-5 h-5 transition-transform ${
                  expandedCategory === categoryKey ? 'rotate-180' : ''
                }`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>
          
          {expandedCategory === categoryKey && (
            <div className="border-t border-gray-200 bg-white">
              <div className="p-4 space-y-3">
                {(category.tools || []).map((tool, index) => (
                  <div key={index} className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{tool.label}</h4>
                        <p className="text-sm text-gray-600 mt-1">{tool.description}</p>
                        {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Parameters:</p>
                            <div className="text-xs text-gray-600">
                              {Object.entries(tool.parameters).map(([param, desc]) => (
                                <div key={param} className="ml-2">
                                  <span className="font-mono text-blue-600">{param}</span>: {desc}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => onToolExecute(tool.name)}
                        className="ml-3 px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors"
                      >
                        Execute
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// Commands Tab Component
interface CommandsTabProps {
  commands: SlashCommand[]
}

function CommandsTab({ commands }: CommandsTabProps) {
  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600 mb-4">
        Type any of these commands in the chat to quickly access features:
      </div>
      {commands.map((command, index) => (
        <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
          <code className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-sm font-mono">
            {command.command}
          </code>
          <span className="text-gray-700">{command.description}</span>
        </div>
      ))}
    </div>
  )
}

// Integrations Tab Component
interface IntegrationsTabProps {
  integrations: Integration[]
}

function IntegrationsTab({ integrations }: IntegrationsTabProps) {
  return (
    <div className="space-y-3">
      {integrations.map((integration, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">{integration.name}</h3>
            <span className={`px-2 py-1 rounded-full text-xs ${
              integration.status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {integration.status}
            </span>
          </div>
          <div className="space-y-1">
            {integration.features.map((feature, featureIndex) => (
              <div key={featureIndex} className="flex items-center space-x-2 text-sm text-gray-600">
                <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// Capabilities Tab Component
interface CapabilitiesTabProps {
  capabilities: string[]
}

function CapabilitiesTab({ capabilities }: CapabilitiesTabProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {capabilities.map((capability, index) => (
        <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
          <span className="text-green-500 mt-0.5">✓</span>
          <span className="text-gray-700">{capability}</span>
        </div>
      ))}
    </div>
  )
}