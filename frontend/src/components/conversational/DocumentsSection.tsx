'use client'

import React, { useState, useEffect } from 'react'
import { FileText, Download, Trash2, Users, User, Search } from 'lucide-react'
import { api } from '@/utils/api'

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

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading documents...
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="px-4 pt-4">
        <div className="flex gap-2">
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
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Search className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Documents List */}
      {documents.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">No documents uploaded yet</p>
          <p className="text-xs mt-1">Upload files from the Knowledge Base chat</p>
        </div>
      ) : (
        <div className="px-4 space-y-2">
          {documents.map((doc) => (
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
                
                <button
                  onClick={() => handleDelete(doc.id, doc.filename)}
                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}