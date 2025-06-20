'use client'

import React, { useState, useRef } from 'react'
import { Upload, File, X, Users, User, Loader } from 'lucide-react'

interface DocumentUploadProps {
  onUpload: (file: File, sharingScope: string, description?: string) => Promise<void>
  disabled?: boolean
  workspaceId: string
}

export function DocumentUpload({ onUpload, disabled = false, workspaceId }: DocumentUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [sharingScope, setSharingScope] = useState<'team' | 'specific'>('team')
  const [specificAgentId, setSpecificAgentId] = useState('')
  const [description, setDescription] = useState('')
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setShowUploadDialog(true)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    try {
      const scope = sharingScope === 'team' ? 'team' : `agent-${specificAgentId}`
      await onUpload(selectedFile, scope, description)
      
      // Reset state
      setSelectedFile(null)
      setShowUploadDialog(false)
      setSharingScope('team')
      setSpecificAgentId('')
      setDescription('')
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
    setSpecificAgentId('')
    setDescription('')
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
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled || isUploading}
        className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
        title="Upload document"
      >
        <Upload className="w-5 h-5" />
      </button>

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
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
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
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                rows={2}
                placeholder="Describe the document contents..."
              />
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
                    <p className="font-medium text-sm">Entire Team</p>
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
                    <p className="text-xs text-gray-500">Only one agent can access this document</p>
                  </div>
                </label>
              </div>

              {sharingScope === 'specific' && (
                <div className="mt-3">
                  <input
                    type="text"
                    value={specificAgentId}
                    onChange={(e) => setSpecificAgentId(e.target.value)}
                    placeholder="Enter agent ID..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
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
                disabled={isUploading || (sharingScope === 'specific' && !specificAgentId)}
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