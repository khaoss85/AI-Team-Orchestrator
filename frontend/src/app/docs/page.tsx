'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Book, Code, Settings, Zap, Users, Database, Shield, FileText, ExternalLink, ChevronRight } from 'lucide-react'

const docsSections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: Zap,
    description: 'Quick setup and first project',
    articles: [
      { title: 'Installation Guide', slug: 'installation', description: 'Set up the AI Team Orchestrator in < 5 minutes' },
      { title: 'Your First Project', slug: 'first-project', description: 'Create and run your first AI team project' },
      { title: 'Environment Configuration', slug: 'environment', description: 'Configure API keys and environment variables' }
    ]
  },
  {
    id: 'core-concepts',
    title: 'Core Concepts',
    icon: Book,
    description: 'Understanding the AI orchestration system',
    articles: [
      { title: 'AI Agent System', slug: 'agents', description: 'Director, specialists, and quality gates' },
      { title: 'Goal-Driven Planning', slug: 'goals', description: 'How AI decomposes objectives into tasks' },
      { title: 'Task Execution System', slug: 'tasks', description: 'Atomic units of work with autonomous recovery' },
      { title: 'Deliverables & Assets', slug: 'deliverables', description: 'AI-transformed professional outputs' },
      { title: 'Sub-Agent Orchestration', slug: 'orchestration', description: 'Director-led team coordination' },
      { title: 'Autonomous Recovery', slug: 'recovery', description: 'Zero-intervention failure recovery' },
      { title: 'Tools & Registry', slug: 'tools', description: 'Extensible tools with slash commands' },
      { title: 'Workspace Management', slug: 'workspaces', description: 'Multi-tenant architecture with health monitoring' },
      { title: 'User Insights', slug: 'insights', description: 'Hybrid AI+Human knowledge management' },
      { title: 'Real-Time Thinking', slug: 'thinking', description: 'Claude/o3-style reasoning processes' },
      { title: 'Workspace Memory', slug: 'memory', description: 'Learning from successes and failures' }
    ]
  },
  {
    id: 'development',
    title: 'Development Guide',
    icon: Code,
    description: 'Technical implementation details',
    articles: [
      { title: 'API Reference', slug: 'api', description: 'Complete REST API documentation' },
      { title: 'Frontend Components', slug: 'components', description: 'React/Next.js component library' },
      { title: 'Database Schema', slug: 'database', description: 'Supabase tables and relationships' },
      { title: 'WebSocket Events', slug: 'websockets', description: 'Real-time communication patterns' },
      { title: 'OpenAI Assistants Integration', slug: 'integrations', description: 'Complete guide to integrating OpenAI Assistants API' },
      { title: 'Advanced Setup', slug: 'advanced-setup', description: 'Expert-level configuration patterns and optimization strategies' }
    ]
  },
  {
    id: 'ai-architecture',
    title: 'AI Architecture',
    icon: Users,
    description: 'Deep dive into the AI system',
    articles: [
      { title: '15 Pillars System', slug: 'pillars', description: 'Core architectural principles' },
      { title: 'Quality Gates', slug: 'quality-gates', description: 'Autonomous code review system' },
      { title: 'Sub-Agent Orchestration', slug: 'sub-agents', description: 'Specialized agent coordination' },
      { title: 'Content-Aware Learning', slug: 'learning', description: 'AI-driven improvement loops' }
    ]
  },
  {
    id: 'workflows',
    title: 'Workflows',
    icon: Zap,
    description: 'End-to-end process flows',
    articles: [
      { title: 'Complete AI Orchestration', slug: 'complete-orchestration', description: 'Full end-to-end workflow from concept to deliverables' },
      { title: 'Task Execution Flow', slug: 'task-execution', description: 'Detailed task processing and recovery workflow' }
    ]
  },
  {
    id: 'operations',
    title: 'Operations',
    icon: Settings,
    description: 'Running in production',
    articles: [
      { title: 'Deployment Guide', slug: 'deployment', description: 'Production deployment strategies' },
      { title: 'Monitoring & Logging', slug: 'monitoring', description: 'System health and debugging' },
      { title: 'Performance Optimization', slug: 'performance', description: 'Scaling and optimization tips' },
      { title: 'Troubleshooting', slug: 'troubleshooting', description: 'Common issues and solutions' }
    ]
  },
  {
    id: 'security',
    title: 'Security',
    icon: Shield,
    description: 'Security best practices',
    articles: [
      { title: 'Security Guidelines', slug: 'security', description: 'Critical security principles' },
      { title: 'Rate Limiting', slug: 'rate-limiting', description: 'API protection strategies' },
      { title: 'Human-in-the-Loop', slug: 'hitl', description: 'Safety validation patterns' },
      { title: 'SDK Compliance', slug: 'sdk-compliance', description: 'Using official SDKs properly' }
    ]
  }
]

const externalResources = [
  {
    title: 'Technical Paper',
    description: 'How the AI Team Orchestrator was built',
    url: 'https://books.danielepelleri.com',
    icon: FileText
  },
  {
    title: 'OpenAI Agents SDK',
    description: 'Official OpenAI Agents SDK documentation',
    url: 'https://openai.github.io/openai-agents-python/',
    icon: ExternalLink
  },
  {
    title: 'FastAPI Docs',
    description: 'Backend API framework documentation',
    url: 'https://fastapi.tiangolo.com/',
    icon: ExternalLink
  },
  {
    title: 'Supabase Docs',
    description: 'Database and authentication platform',
    url: 'https://supabase.com/docs',
    icon: ExternalLink
  }
]

export default function DocsPage() {
  const [selectedSection, setSelectedSection] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-4">
            <Link 
              href="/"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
          </div>
          <div className="mt-4">
            <h1 className="text-3xl font-bold text-gray-900">Documentation</h1>
            <p className="text-gray-600 mt-2">
              Complete guide to the AI Team Orchestrator platform
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border p-6 sticky top-8">
              <h2 className="font-semibold text-gray-900 mb-4">Sections</h2>
              <nav className="space-y-2">
                {docsSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setSelectedSection(selectedSection === section.id ? null : section.id)}
                    className={`w-full text-left flex items-center space-x-3 p-3 rounded-lg transition-all ${
                      selectedSection === section.id
                        ? 'bg-blue-50 text-blue-900 border-blue-200'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <section.icon className="w-5 h-5" />
                    <span className="font-medium">{section.title}</span>
                    <ChevronRight className={`w-4 h-4 ml-auto transition-transform ${
                      selectedSection === section.id ? 'rotate-90' : ''
                    }`} />
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {selectedSection ? (
              // Section Detail View
              <div className="bg-white rounded-xl border p-8">
                {(() => {
                  const section = docsSections.find(s => s.id === selectedSection)!
                  return (
                    <>
                      <div className="flex items-center space-x-4 mb-6">
                        <div className="p-3 bg-blue-50 rounded-xl">
                          <section.icon className="w-8 h-8 text-blue-600" />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">{section.title}</h2>
                          <p className="text-gray-600">{section.description}</p>
                        </div>
                      </div>

                      <div className="grid gap-4">
                        {section.articles.map((article) => (
                          <Link
                            key={article.slug}
                            href={`/docs/${section.id}/${article.slug}`}
                            className="group p-6 border rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <h3 className="font-semibold text-gray-900 group-hover:text-blue-900 mb-2">
                                  {article.title}
                                </h3>
                                <p className="text-gray-600 group-hover:text-blue-700">
                                  {article.description}
                                </p>
                              </div>
                              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                            </div>
                          </Link>
                        ))}
                      </div>
                    </>
                  )
                })()}
              </div>
            ) : (
              // Overview Grid
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                  {docsSections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => setSelectedSection(section.id)}
                      className="group text-left p-6 bg-white rounded-xl border hover:border-blue-300 hover:bg-blue-50 transition-all"
                    >
                      <div className="flex items-center space-x-4 mb-4">
                        <div className="p-3 bg-gray-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                          <section.icon className="w-6 h-6 text-gray-600 group-hover:text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 group-hover:text-blue-900">
                            {section.title}
                          </h3>
                          <p className="text-sm text-gray-600 group-hover:text-blue-700 mt-1">
                            {section.articles.length} articles
                          </p>
                        </div>
                      </div>
                      <p className="text-gray-600 group-hover:text-blue-700">
                        {section.description}
                      </p>
                    </button>
                  ))}
                </div>

                {/* External Resources */}
                <div className="bg-white rounded-xl border p-8">
                  <h2 className="text-xl font-bold text-gray-900 mb-6">External Resources</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {externalResources.map((resource, index) => (
                      <a
                        key={index}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group flex items-center space-x-4 p-4 border rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all"
                      >
                        <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                          <resource.icon className="w-5 h-5 text-gray-600 group-hover:text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900 group-hover:text-blue-900">
                            {resource.title}
                          </h3>
                          <p className="text-sm text-gray-600 group-hover:text-blue-700">
                            {resource.description}
                          </p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                      </a>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}