'use client'

import React from 'react'
import { FileText, Upload, Search, BookOpen } from 'lucide-react'

export default function LibraryPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Library</h1>
          <p className="text-gray-600">
            Your knowledge base, documents, and workspace memory
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Upload className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="font-medium text-gray-900">Upload Documents</h3>
            </div>
            <p className="text-sm text-gray-600">
              Add new documents to your workspace knowledge base
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-50 rounded-lg">
                <Search className="w-5 h-5 text-green-600" />
              </div>
              <h3 className="font-medium text-gray-900">Search Knowledge</h3>
            </div>
            <p className="text-sm text-gray-600">
              Find information across all your documents and conversations
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-purple-50 rounded-lg">
                <BookOpen className="w-5 h-5 text-purple-600" />
              </div>
              <h3 className="font-medium text-gray-900">Workspace Memory</h3>
            </div>
            <p className="text-sm text-gray-600">
              Browse patterns learned and insights discovered
            </p>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Recent Documents</h2>
            <button className="text-sm text-blue-600 hover:text-blue-700">
              View all
            </button>
          </div>

          <div className="space-y-3">
            {/* Placeholder for when documents are loaded */}
            <div className="flex items-center space-x-4 p-4 border border-gray-100 rounded-lg hover:bg-gray-50">
              <FileText className="w-8 h-8 text-gray-400" />
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">No documents yet</h3>
                <p className="text-sm text-gray-600">
                  Upload your first document to get started
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Integration Notice */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="p-1 bg-blue-100 rounded-full">
              <FileText className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-blue-900 mb-1">Integration with Conversations</h3>
              <p className="text-sm text-blue-700">
                Documents uploaded here are automatically available to all your AI agents 
                in conversations. You can also access library features directly from 
                any project using slash commands like <code className="bg-blue-100 px-1 rounded">/search_knowledge</code>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}