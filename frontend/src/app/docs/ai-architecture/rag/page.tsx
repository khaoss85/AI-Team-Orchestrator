'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, FileText, Search, Database, Brain, Upload, CheckCircle, Zap, Eye, Code } from 'lucide-react'

export default function RAGPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-centers text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG & Document Intelligence</h1>
            <p className="text-gray-600">Advanced document processing and retrieval-augmented generation system</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">OpenAI Assistants API Integration</h3>
                    <p className="text-blue-700 text-sm mt-1">Native RAG functionality with vector search and file processing</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The RAG & Document Intelligence system provides advanced document processing capabilities using OpenAI's Assistants API. 
                Agents can upload, process, and intelligently query documents to provide contextual, source-backed responses with automatic 
                citation and reference extraction.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">Native Vector Search</h4>
                  <p className="text-green-700 text-sm">OpenAI's built-in vector stores and semantic search capabilities</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Multi-Modal Processing</h4>
                  <p className="text-blue-700 text-sm">PDFs, documents, images, and structured data within agent workflows</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Agent-Specific Knowledge</h4>
                  <p className="text-purple-700 text-sm">Domain documents assigned to specialized agents for expert reasoning</p>
                </div>
              </div>
            </section>

            {/* Architecture Overview */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">RAG Architecture</h2>
              
              <div className="space-y-8">
                {/* Document Upload Flow */}
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <Upload className="w-8 h-8 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-green-900">Document Upload & Processing</h3>
                      <p className="text-green-700">Multi-format document ingestion with automatic processing</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-green-200 mb-4">
                    <h4 className="font-medium text-green-900 mb-3">Supported Formats:</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-green-50 rounded p-2 text-center">
                        <FileText className="w-6 h-6 text-green-600 mx-auto mb-1" />
                        <span className="text-xs text-green-700">PDF</span>
                      </div>
                      <div className="bg-green-50 rounded p-2 text-center">
                        <FileText className="w-6 h-6 text-green-600 mx-auto mb-1" />
                        <span className="text-xs text-green-700">DOCX</span>
                      </div>
                      <div className="bg-green-50 rounded p-2 text-center">
                        <FileText className="w-6 h-6 text-green-600 mx-auto mb-1" />
                        <span className="text-xs text-green-700">TXT</span>
                      </div>
                      <div className="bg-green-50 rounded p-2 text-center">
                        <FileText className="w-6 h-6 text-green-600 mx-auto mb-1" />
                        <span className="text-xs text-green-700">MD</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-green-100 rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-2">Processing Pipeline:</h4>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-800 text-sm">Content extraction and chunking</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-800 text-sm">Vector embedding generation</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-800 text-sm">Workspace-specific vector store creation</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-800 text-sm">Agent-document association</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Vector Search */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Search className="w-8 h-8 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Semantic Vector Search</h3>
                      <p className="text-blue-700">OpenAI's native vector search with citation extraction</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-blue-200 mb-4">
                    <h4 className="font-medium text-blue-900 mb-3">Search Capabilities:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-blue-800 mb-2">Semantic Understanding:</h5>
                        <ul className="space-y-1 text-blue-700 text-sm">
                          <li>• Concept-based search beyond keywords</li>
                          <li>• Contextual relevance scoring</li>
                          <li>• Cross-document relationship detection</li>
                          <li>• Multi-language support</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-blue-800 mb-2">Citation & References:</h5>
                        <ul className="space-y-1 text-blue-700 text-sm">
                          <li>• Automatic source attribution</li>
                          <li>• Page number and section references</li>
                          <li>• Direct quote extraction</li>
                          <li>• Confidence scoring</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-100 rounded-lg p-4 border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">Example Query Response:</h4>
                    <div className="bg-white rounded p-3 border border-blue-200">
                      <p className="text-blue-800 text-sm italic">
                        <strong>Question:</strong> "What are the key performance indicators for marketing campaigns?"<br/>
                        <strong>Response:</strong> "Based on the uploaded marketing strategy document, key performance indicators include 
                        conversion rate (target: 3-5%), customer acquisition cost (&lt;$50), and return on ad spend (minimum 4:1 ratio). 
                        Additionally, brand awareness metrics such as reach and engagement rate are crucial for long-term success."<br/>
                        <strong>Sources:</strong> [Marketing_Strategy_2024.pdf, p. 23-24] [Campaign_Metrics_Guide.docx, Section 3.2]
                      </p>
                    </div>
                  </div>
                </div>

                {/* Agent Integration */}
                <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Brain className="w-8 h-8 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-purple-900">Agent-Document Specialization</h3>
                      <p className="text-purple-700">Domain-specific document assignment for expert reasoning</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-purple-200">
                    <h4 className="font-medium text-purple-900 mb-3">Specialization Examples:</h4>
                    <div className="space-y-3">
                      <div className="border-l-4 border-purple-400 pl-4">
                        <h5 className="font-medium text-purple-800 mb-1">Marketing Strategist</h5>
                        <p className="text-purple-700 text-sm">
                          Access to brand guidelines, competitor analysis reports, market research data, and campaign performance documents.
                        </p>
                      </div>
                      <div className="border-l-4 border-purple-400 pl-4">
                        <h5 className="font-medium text-purple-800 mb-1">Financial Analyst</h5>
                        <p className="text-purple-700 text-sm">
                          Financial statements, investment policies, regulatory documents, and economic analysis reports.
                        </p>
                      </div>
                      <div className="border-l-4 border-purple-400 pl-4">
                        <h5 className="font-medium text-purple-800 mb-1">Technical Writer</h5>
                        <p className="text-purple-700 text-sm">
                          API documentation, technical specifications, code standards, and style guides.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Technical Implementation */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Technical Implementation</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-6 border">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    Core Services Architecture
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border">
                      <h4 className="font-medium text-gray-900 mb-3">OpenAI Assistant Manager</h4>
                      <div className="bg-gray-900 rounded p-3 mb-3">
                        <code className="text-green-400 text-sm">
                          backend/services/openai_assistant_manager.py
                        </code>
                      </div>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Manages OpenAI Assistants lifecycle per workspace</li>
                        <li>• Handles assistant-vector store associations</li>
                        <li>• Processes thread creation and message handling</li>
                        <li>• Executes tools through Assistants API</li>
                      </ul>
                    </div>

                    <div className="bg-white rounded-lg p-4 border">
                      <h4 className="font-medium text-gray-900 mb-3">Document Manager</h4>
                      <div className="bg-gray-900 rounded p-3 mb-3">
                        <code className="text-green-400 text-sm">
                          backend/services/document_manager.py
                        </code>
                      </div>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Document upload and content extraction</li>
                        <li>• Vector store creation and management</li>
                        <li>• PDF and multi-format processing</li>
                        <li>• Workspace-specific document organization</li>
                      </ul>
                    </div>

                    <div className="bg-white rounded-lg p-4 border">
                      <h4 className="font-medium text-gray-900 mb-3">Assistant Registry</h4>
                      <div className="bg-gray-900 rounded p-3 mb-3">
                        <code className="text-green-400 text-sm">
                          backend/services/assistant_registry.py
                        </code>
                      </div>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Agent-specific assistant configuration</li>
                        <li>• Tool and capability management</li>
                        <li>• Domain specialization settings</li>
                        <li>• Assistant versioning and updates</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Database Schema */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <Code className="w-5 h-5 mr-2" />
                    Database Integration
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-3">Document Storage Schema:</h4>
                      <div className="bg-gray-900 rounded p-3">
                        <pre className="text-blue-400 text-sm overflow-x-auto">
                          <code>{`-- Document management tables
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  filename VARCHAR(255),
  content_type VARCHAR(100),
  file_size BIGINT,
  openai_file_id VARCHAR(100),
  vector_store_id VARCHAR(100),
  content_hash SHA256,
  page_count INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE document_agent_access (
  document_id UUID REFERENCES documents(id),
  agent_type VARCHAR(100),
  access_level VARCHAR(50),
  assigned_at TIMESTAMP DEFAULT NOW()
);`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-3">Vector Store Management:</h4>
                      <div className="bg-gray-900 rounded p-3">
                        <pre className="text-blue-400 text-sm overflow-x-auto">
                          <code>{`-- Vector store tracking
CREATE TABLE vector_stores (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  openai_vector_store_id VARCHAR(100),
  name VARCHAR(255),
  document_count INTEGER DEFAULT 0,
  last_updated TIMESTAMP DEFAULT NOW()
);`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Advanced Features */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Advanced RAG Features</h2>
              
              <div className="space-y-6">
                <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                  <h3 className="font-medium text-yellow-900 mb-4 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Thread Persistence & Context
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-yellow-200">
                      <h4 className="font-medium text-yellow-900 mb-2">Conversation Context Maintenance:</h4>
                      <ul className="space-y-1 text-yellow-700 text-sm">
                        <li>• Conversation history preserved across sessions</li>
                        <li>• Document context maintained in threads</li>
                        <li>• Agent memory of previous document interactions</li>
                        <li>• Cross-session knowledge continuity</li>
                      </ul>
                    </div>

                    <div className="bg-yellow-100 rounded-lg p-4 border border-yellow-200">
                      <h4 className="font-medium text-yellow-900 mb-2">Context Example:</h4>
                      <div className="bg-white rounded p-3 border border-yellow-200">
                        <p className="text-yellow-800 text-sm italic">
                          "Earlier in our conversation, I referenced the Q3 marketing budget from the strategy document. 
                          Based on that same document and the current campaign performance data you just uploaded, 
                          I recommend reallocating 15% of the social media budget to content marketing for Q4."
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-4 flex items-center">
                    <Eye className="w-5 h-5 mr-2" />
                    MCP Integration Ready
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Model Context Protocol Support:</h4>
                      <ul className="space-y-1 text-green-700 text-sm">
                        <li>• Advanced tool and knowledge connectivity</li>
                        <li>• Multi-modal understanding and processing</li>
                        <li>• Enhanced document analysis capabilities</li>
                        <li>• Future-ready architecture for MCP features</li>
                      </ul>
                    </div>

                    <div className="bg-green-100 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Integration Benefits:</h4>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-green-800 text-sm">Seamless tool integration with external systems</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-green-800 text-sm">Enhanced context understanding across modalities</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-green-800 text-sm">Advanced knowledge graph capabilities</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Usage Examples */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Usage Examples</h2>
              
              <div className="space-y-6">
                <div className="bg-white rounded-lg p-6 border">
                  <h3 className="font-medium text-gray-900 mb-4">Workspace Document Upload</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`# Upload documents to workspace
POST /api/documents/upload/{workspace_id}
Content-Type: multipart/form-data

Files: 
- marketing_strategy_2024.pdf
- competitor_analysis.docx
- brand_guidelines.pdf

Response:
{
  "uploaded": 3,
  "vector_store_id": "vs_abc123",
  "documents": [
    {
      "id": "doc_123",
      "filename": "marketing_strategy_2024.pdf",
      "pages": 45,
      "status": "processed"
    }
  ]
}`}</code>
                    </pre>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-6 border">
                  <h3 className="font-medium text-gray-900 mb-4">Agent Document Query</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`# Agent queries documents through conversation
POST /api/conversational/chat/{workspace_id}

{
  "message": "Based on our uploaded brand guidelines, what colors should we use for the new campaign?",
  "agent_type": "marketing_strategist"
}

Response includes:
- Relevant document excerpts
- Source citations with page numbers
- Agent reasoning with document context`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Learn More</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/core-concepts/agents"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Brain className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">AI Agent System</h3>
                    <p className="text-gray-600 text-sm">How agents use RAG for domain expertise</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/development/api"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Code className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">API Reference</h3>
                    <p className="text-gray-600 text-sm">Document upload and RAG query endpoints</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/getting-started/first-project"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Upload className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Try Document Upload</h3>
                    <p className="text-gray-600 text-sm">Create a project and upload domain documents</p>
                  </div>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}