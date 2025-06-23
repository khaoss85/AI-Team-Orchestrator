'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Chat } from './types'
import { DocumentUpload } from './DocumentUpload'

interface ConversationInputProps {
  activeChat: Chat | null
  onSendMessage: (message: string) => Promise<void>
  loading: boolean
  workspaceId: string
}

export default function ConversationInput({ 
  activeChat, 
  onSendMessage, 
  loading,
  workspaceId
}: ConversationInputProps) {
  const [input, setInput] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const [showSlashCommands, setShowSlashCommands] = useState(false)
  const [filteredCommands, setFilteredCommands] = useState<any[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Quick actions based on chat type
  const getQuickActions = () => {
    if (!activeChat) return []

    if (activeChat.type === 'fixed') {
      switch (activeChat.systemType) {
        case 'team':
          return [
            'Add team member',
            'Update skills',
            'Show team performance',
            'Change seniority levels'
          ]
        case 'configuration':
          return [
            'Change budget',
            'Update timeline',
            'Modify goals',
            'Adjust priorities'
          ]
        case 'knowledge':
          return [
            'Best practices',
            'Lessons learned',
            'Industry insights',
            'Search knowledge'
          ]
        case 'tools':
          return [
            'Available tools',
            'Integrations',
            'Tool training',
            'Capabilities check'
          ]
        default:
          return ['Help', 'Status', 'Settings']
      }
    } else {
      // Dynamic chat actions
      return [
        'Show progress',
        'Modify approach',
        'Add requirements',
        'Export results'
      ]
    }
  }

  const quickActions = getQuickActions()

  // Available slash commands/tools
  const slashCommands = [
    {
      command: '/show_project_status',
      title: '📊 View Project Status',
      description: 'Get comprehensive project overview',
      example: 'Shows current project metrics and status'
    },
    {
      command: '/show_team_status',
      title: '👥 View Team Status',
      description: 'See current team composition and activities',
      example: 'Displays team members and their current tasks'
    },
    {
      command: '/show_goal_progress',
      title: '🎯 View Goal Progress',
      description: 'Check progress on objectives',
      example: 'Shows completion percentage for all goals'
    },
    {
      command: '/show_deliverables',
      title: '📦 View Deliverables',
      description: 'See completed deliverables and assets',
      example: 'Lists all project deliverables and their status'
    },
    {
      command: '/approve_all_feedback',
      title: '✅ Approve All Feedback',
      description: 'Approve all pending feedback requests',
      example: 'Bulk approves all waiting feedback items'
    },
    {
      command: '/add_team_member',
      title: '➕ Add Team Member',
      description: 'Add a new member to the team',
      example: 'Add team member with specific role and skills'
    },
    {
      command: '/create_goal',
      title: '🎯 Create Goal',
      description: 'Create a new project goal',
      example: 'Define new objectives for the project'
    },
    {
      command: '/fix_workspace_issues',
      title: '🔧 Fix Workspace Issues',
      description: 'Restart failed tasks and resolve issues',
      example: 'Automatically diagnose and fix common problems'
    }
  ]

  // Handle slash command detection
  useEffect(() => {
    const trimmedInput = input.trim()
    
    if (trimmedInput.startsWith('/')) {
      const commandQuery = trimmedInput.slice(1).toLowerCase()
      
      // If just "/", show all commands
      if (commandQuery === '') {
        setFilteredCommands(slashCommands)
      } else {
        // Filter commands based on query
        const filtered = slashCommands.filter(cmd => 
          cmd.command.toLowerCase().includes(`/${commandQuery}`) ||
          cmd.title.toLowerCase().includes(commandQuery) ||
          cmd.description.toLowerCase().includes(commandQuery)
        )
        setFilteredCommands(filtered)
      }
      setShowSlashCommands(true)
    } else {
      setShowSlashCommands(false)
      setFilteredCommands([])
    }
  }, [input])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const message = input.trim()
    setInput('')
    setIsExpanded(false)
    
    try {
      await onSendMessage(message)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore input on error
      setInput(message)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    
    // Handle escape to close slash commands
    if (e.key === 'Escape' && showSlashCommands) {
      setShowSlashCommands(false)
      setFilteredCommands([])
    }
  }

  const handleSlashCommandSelect = (command: any) => {
    // Convert slash command to natural language request
    const naturalRequest = command.title.replace(/^[📊👥🎯📦✅➕🔧]\s*/, '')
    setInput(naturalRequest)
    setShowSlashCommands(false)
    setFilteredCommands([])
    textareaRef.current?.focus()
  }

  const handleQuickAction = (action: string) => {
    setInput(action)
    setIsExpanded(true)
    textareaRef.current?.focus()
  }

  const handleFileUpload = async (file: File, sharingScope: string, description?: string) => {
    // Convert file to base64
    const reader = new FileReader()
    reader.onload = async (e) => {
      const base64 = e.target?.result?.toString().split(',')[1] // Remove data:type/subtype;base64, prefix
      if (base64) {
        const uploadMessage = `EXECUTE_TOOL: upload_document {"file_data": "${base64}", "filename": "${file.name}", "sharing_scope": "${sharingScope}"${description ? `, "description": "${description}"` : ''}}`
        await onSendMessage(uploadMessage)
      }
    }
    reader.readAsDataURL(file)
  }

  const getPlaceholder = () => {
    if (!activeChat) return 'Select a chat to start...'
    
    if (activeChat.type === 'fixed') {
      switch (activeChat.systemType) {
        case 'team': return 'Ask about team management... (type / for tools)'
        case 'configuration': return 'Request configuration changes... (type / for tools)'
        case 'knowledge': return 'Search knowledge base... (type / for tools)'
        case 'tools': return 'Ask about tools and capabilities... (type / for tools)'
        default: return 'Type your message... (type / for tools)'
      }
    } else {
      return 'Describe what you need or ask for updates... (type / for tools)'
    }
  }

  if (!activeChat) {
    return (
      <div className="border-t bg-gray-50 p-4">
        <div className="text-center text-gray-500 text-sm">
          Select a chat to start collaborating
        </div>
      </div>
    )
  }

  return (
    <div className="border-t bg-white">
      {/* Quick Actions */}
      {!isExpanded && quickActions.length > 0 && (
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action) => (
              <button
                key={action}
                onClick={() => handleQuickAction(action)}
                className="px-3 py-1 text-xs bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 rounded-full transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-6">
        <div className="flex items-end space-x-3">
          {/* Document Upload - Only for Knowledge Base chat */}
          {activeChat.type === 'fixed' && activeChat.systemType === 'knowledge' && (
            <DocumentUpload
              onUpload={handleFileUpload}
              disabled={loading}
              workspaceId={workspaceId}
            />
          )}

          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                setIsExpanded(e.target.value.length > 0)
              }}
              onKeyDown={handleKeyDown}
              placeholder={getPlaceholder()}
              disabled={loading}
              rows={1}
              className={`
                w-full px-4 py-3 border border-gray-300 rounded-xl 
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                resize-none transition-all duration-200
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
                ${isExpanded ? 'min-h-[100px]' : 'max-h-[120px]'}
              `}
              style={{ maxHeight: '120px' }}
            />
            
            {/* Character Counter for long messages */}
            {input.length > 500 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}/2000
              </div>
            )}

            {/* Slash Commands Dropdown */}
            {showSlashCommands && filteredCommands.length > 0 && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto z-10">
                <div className="p-2 border-b border-gray-100 bg-gray-50">
                  <div className="text-xs font-medium text-gray-600">Available Tools</div>
                  <div className="text-xs text-gray-500">Click to select or continue typing</div>
                </div>
                {filteredCommands.map((command, index) => (
                  <button
                    key={command.command}
                    onClick={() => handleSlashCommandSelect(command)}
                    className="w-full text-left p-3 hover:bg-blue-50 border-b border-gray-100 last:border-b-0 transition-colors"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="text-lg flex-shrink-0">
                        {command.title.match(/^[📊👥🎯📦✅➕🔧]/)?.[0] || '🔧'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">
                          {command.title}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          {command.description}
                        </div>
                        <div className="text-xs text-blue-600 mt-1 font-mono">
                          {command.command}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
                {filteredCommands.length === 0 && input.trim().startsWith('/') && (
                  <div className="p-3 text-sm text-gray-500 text-center">
                    No matching tools found
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className={`
              p-3 rounded-xl transition-all duration-200
              ${input.trim() && !loading
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }
            `}
            title={loading ? 'Sending...' : 'Send message (Enter)'}
          >
            {loading ? (
              <div className="w-5 h-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {/* Formatting Hint */}
        {isExpanded && (
          <div className="mt-2 text-xs text-gray-500">
            <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Shift + Enter</kbd> for new line, 
            <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs ml-1">Enter</kbd> to send
          </div>
        )}
      </div>
    </div>
  )
}