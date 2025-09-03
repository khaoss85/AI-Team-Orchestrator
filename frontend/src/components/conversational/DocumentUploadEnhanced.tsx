'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Upload, File, X, Users, User, Loader, Plus, Tag } from 'lucide-react'
import { api } from '@/utils/api'

interface Agent {
  id: string
  name: string
  role: string
  status: string
}

interface DocumentUploadEnhancedProps {
  onUpload: (file: File, sharingScope: string, description?: string, tags?: string[]) => Promise<void>
  disabled?: boolean
  workspaceId: string
  className?: string
  buttonVariant?: 'icon' | 'button'
}

export function DocumentUploadEnhanced({ 
  onUpload, 
  disabled = false, 
  workspaceId,
  className = '',
  buttonVariant = 'icon'
}: DocumentUploadEnhancedProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [sharingScope, setSharingScope] = useState<'team' | 'specific'>('team')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [description, setDescription] = useState('')
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load agents when dialog opens
  useEffect(() => {
    if (showUploadDialog && agents.length === 0) {
      loadAgents()
    }
  }, [showUploadDialog])

  const loadAgents = async () => {
    setLoadingAgents(true)
    try {
      const data = await api.agents.list(workspaceId)
      setAgents(data)
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      setLoadingAgents(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setShowUploadDialog(true)
    }
  }

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()])
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    try {
      const scope = sharingScope === 'team' ? 'team' : `agent-${selectedAgent?.id}`
      await onUpload(selectedFile, scope, description, tags)
      
      // Reset state
      setSelectedFile(null)
      setShowUploadDialog(false)
      setSharingScope('team')
      setSelectedAgent(null)
      setDescription('')
      setTags([])
      setTagInput('')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleCancel = () => {
    setSelectedFile(null)
    setShowUploadDialog(false)
    setSharingScope('team')
    setSelectedAgent(null)
    setDescription('')
    setTags([])
    setTagInput('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <>
      {/* Upload Button */}
      {buttonVariant === 'icon' ? (
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
          className={`p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50 ${className}`}
          title="Upload document"
        >
          <Upload className="w-5 h-5" />
        </button>
      ) : (
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
          className={`flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        >
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        className="hidden"
        accept=".pdf,.doc,.docx,.txt,.md,.csv,.xls,.xlsx,.json,.xml"
      />

      {/* Upload Dialog */}
      {showUploadDialog && selectedFile && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Upload Document</h3>
            
            {/* File Info */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg flex items-center gap-3">
              <File className="w-8 h-8 text-gray-400" />
              <div className="flex-1">
                <p className="font-medium text-sm">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>

            {/* Description */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="Describe the document contents..."
              />
            </div>

            {/* Tags */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (optional)
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddTag()
                    }
                  }}
                  placeholder="Add tags for better organization..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleAddTag}
                  disabled={!tagInput.trim()}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-blue-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Sharing Scope */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Who can access this document?
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="scope"
                    value="team"
                    checked={sharingScope === 'team'}
                    onChange={() => setSharingScope('team')}
                    className="text-blue-600"
                  />
                  <Users className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="font-medium text-sm">All Team Members</p>
                    <p className="text-xs text-gray-500">All agents can search and use this document</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="scope"
                    value="specific"
                    checked={sharingScope === 'specific'}
                    onChange={() => setSharingScope('specific')}
                    className="text-blue-600"
                  />
                  <User className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="font-medium text-sm">Specific Agent</p>
                    <p className="text-xs text-gray-500">Only selected agent can access this document</p>
                  </div>
                </label>
              </div>

              {sharingScope === 'specific' && (
                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Agent
                  </label>
                  {loadingAgents ? (
                    <div className="flex items-center justify-center py-3">
                      <Loader className="w-5 h-5 animate-spin text-gray-400" />
                    </div>
                  ) : (
                    <select
                      value={selectedAgent?.id || ''}
                      onChange={(e) => {
                        const agent = agents.find(a => a.id === e.target.value)
                        setSelectedAgent(agent || null)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Choose an agent...</option>
                      {agents.map(agent => (
                        <option key={agent.id} value={agent.id}>
                          {agent.name} - {agent.role}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <button
                onClick={handleCancel}
                disabled={isUploading}
                className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={isUploading || (sharingScope === 'specific' && !selectedAgent)}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}