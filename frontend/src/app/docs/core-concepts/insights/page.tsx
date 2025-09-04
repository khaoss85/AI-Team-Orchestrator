'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Brain, Search, Edit } from 'lucide-react'

export default function InsightsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">User Insights Management</h1>
            <p className="text-gray-600">Hybrid AI+Human knowledge management with intelligent categorization</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            <section className="mb-12">
              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Brain className="w-6 h-6 text-purple-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-purple-900">Hybrid AI+Human Knowledge System</h3>
                    <p className="text-purple-700 mt-1">
                      Complete user control over workspace knowledge insights, enhanced by AI-driven semantic 
                      categorization, with full CRUD operations, audit trails, and intelligent organization.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The User Insights Management System empowers users to create, organize, and manage knowledge 
                  insights within their workspace. Unlike pure AI systems, this provides complete human control 
                  while leveraging AI for intelligent categorization and content enhancement.
                </p>
              </div>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Edit className="w-6 h-6 mr-3 text-indigo-600" />
                Core Features
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Edit className="w-6 h-6 text-green-600" />
                    <h3 className="font-semibold text-green-900">Complete CRUD Operations</h3>
                  </div>
                  <ul className="text-sm text-green-800 space-y-2">
                    <li>• Create: Add insights with rich metadata</li>
                    <li>• Read: Search, filter, and browse knowledge</li>
                    <li>• Update: Edit content and categorization</li>
                    <li>• Delete: Soft delete with recovery options</li>
                  </ul>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Brain className="w-6 h-6 text-blue-600" />
                    <h3 className="font-semibold text-blue-900">AI-Powered Categorization</h3>
                  </div>
                  <ul className="text-sm text-blue-800 space-y-2">
                    <li>• Semantic Analysis: Content understanding and classification</li>
                    <li>• Confidence Scoring: AI certainty metrics (0.0-1.0)</li>
                    <li>• Smart Suggestions: Category and domain recommendations</li>
                    <li>• Context Awareness: Workspace-specific intelligence</li>
                  </ul>
                </div>
              </div>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Search className="w-6 h-6 mr-3 text-indigo-600" />
                Key Benefits
              </h2>

              <div className="space-y-4">
                <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                  <h3 className="font-semibold text-yellow-900 mb-3">Human-Centric Design</h3>
                  <p className="text-yellow-800">
                    Every feature prioritizes human control and understanding. AI provides assistance and suggestions, 
                    but all final decisions remain with the user. No automated actions occur without explicit consent.
                  </p>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-semibold text-blue-900 mb-3">Intelligent Organization</h3>
                  <p className="text-blue-800">
                    AI-driven categorization learns from workspace patterns and user preferences to suggest 
                    relevant categories and improve knowledge discoverability over time.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/memory"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Brain className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Memory</h3>
                  <p className="text-sm text-gray-600">Workspace memory and learning</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/workspaces"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Edit className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Workspaces</h3>
                  <p className="text-sm text-gray-600">Multi-tenant workspace system</p>
                </Link>

                <Link 
                  href="/docs/ai-architecture/rag"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Search className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">RAG System</h3>
                  <p className="text-sm text-gray-600">Document intelligence and search</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}