'use client'

import React, { useState, useEffect } from 'react'
import { FileText, Download, Trash2, Users, User, Search, Upload, Eye, ExternalLink } from 'lucide-react'
import { api } from '@/utils/api'
import { DocumentUploadEnhanced } from './DocumentUploadEnhanced'

interface Document {
  id: string
  filename: string
  file_size: number
  mime_type: string
  upload_date: string
  uploaded_by: string
  sharing_scope: string
  description?: string
  tags: string[]
}

interface DocumentsSectionProps {
  workspaceId: string
  onSendMessage: (message: string) => Promise<void>
}

export function DocumentsSection({ workspaceId, onSendMessage }: DocumentsSectionProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterTag, setFilterTag] = useState<string | null>(null)

  // Load documents
  useEffect(() => {
    loadDocuments()
  }, [workspaceId])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await api.documents.list(workspaceId)
      if (response.documents) {
        setDocuments(response.documents)
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File, sharingScope: string, description?: string, tags?: string[]) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('sharing_scope', sharingScope)
      if (description) formData.append('description', description)
      if (tags && tags.length > 0) {
        formData.append('tags', tags.join(','))
      }

      const response = await fetch(`${api.getBaseUrl()}/api/documents/${workspaceId}/upload-file`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`)
      }

      // Reload documents after successful upload
      await loadDocuments()
    } catch (error) {
      console.error('Upload error:', error)
      throw error
    }
  }

  const handleView = (documentId: string, filename: string) => {
    // Open document in new tab
    const viewUrl = api.documents.getViewUrl(workspaceId, documentId)
    window.open(viewUrl, '_blank')
  }

  const handleDelete = async (documentId: string, filename: string) => {
    if (confirm(`Delete "${filename}"?`)) {
      try {
        await api.documents.delete(workspaceId, documentId)
        await loadDocuments()
      } catch (error) {
        console.error('Failed to delete document:', error)
      }
    }
  }

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      const message = `EXECUTE_TOOL: search_documents {"query": "${searchQuery}"}`
      await onSendMessage(message)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return '📄'
    if (mimeType.includes('word') || mimeType.includes('doc')) return '📝'
    if (mimeType.includes('sheet') || mimeType.includes('excel')) return '📊'
    if (mimeType.includes('image')) return '🖼️'
    if (mimeType.includes('text')) return '📋'
    return '📎'
  }

  // Get all unique tags from documents
  const allTags = Array.from(new Set(documents.flatMap(doc => doc.tags)))

  // Filter documents based on search and tag filter
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = !searchQuery || 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesTag = !filterTag || doc.tags.includes(filterTag)
    return matchesSearch && matchesTag
  })

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading documents...
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with Search and Upload */}
      <div className="px-4 pt-4">
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search documents..."
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim()}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Search className="w-4 h-4" />
          </button>
          <DocumentUploadEnhanced 
            workspaceId={workspaceId}
            onUpload={handleUpload}
            buttonVariant="button"
          />
        </div>

        {/* Tag Filter */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-500">Filter by tag:</span>
            <button
              onClick={() => setFilterTag(null)}
              className={`px-2 py-1 text-xs rounded-full transition-colors ${
                !filterTag 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setFilterTag(tag === filterTag ? null : tag)}
                className={`px-2 py-1 text-xs rounded-full transition-colors ${
                  filterTag === tag 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Documents List */}
      {documents.length === 0 ? (
        <div className="p-8 text-center">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm text-gray-600 font-medium">No documents uploaded yet</p>
          <p className="text-xs text-gray-500 mt-1 mb-4">Share knowledge with your AI team</p>
          <DocumentUploadEnhanced 
            workspaceId={workspaceId}
            onUpload={handleUpload}
            buttonVariant="button"
            className="mx-auto"
          />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">No documents match your filters</p>
          <p className="text-xs mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="px-4 space-y-2">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="text-2xl">{getFileIcon(doc.mime_type)}</div>
                
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm truncate">{doc.filename}</h4>
                  
                  {doc.description && (
                    <p className="text-xs text-gray-600 mt-1">{doc.description}</p>
                  )}
                  
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      {doc.sharing_scope === 'team' ? (
                        <Users className="w-3 h-3" />
                      ) : (
                        <User className="w-3 h-3" />
                      )}
                      {doc.sharing_scope === 'team' ? 'Team' : doc.sharing_scope.replace('agent-', '')}
                    </span>
                    <span>{formatFileSize(doc.file_size)}</span>
                    <span>{formatDate(doc.upload_date)}</span>
                  </div>
                  
                  {doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {doc.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleView(doc.id, doc.filename)}
                    className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors"
                    title="View document"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}