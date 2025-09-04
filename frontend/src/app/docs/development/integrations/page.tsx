'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Brain,
  Database,
  Settings,
  Code,
  CheckCircle,
  AlertTriangle,
  Copy,
  Play,
  FileText,
  Zap,
  Shield,
  Terminal,
  ExternalLink
} from 'lucide-react'

const integrationSteps = [
  {
    id: 'database',
    title: 'Database Migration',
    description: 'Apply the required database migration to support OpenAI Assistants',
    duration: '2-3 minutes',
    commands: [
      {
        description: 'Run the migration to create workspace_assistants table',
        command: 'psql -U your_user -d your_database -f migrations/018_add_openai_assistants_support.sql'
      }
    ],
    verification: 'Check that workspace_assistants table exists with proper schema',
    icon: Database,
    color: 'bg-blue-50 border-blue-200'
  },
  {
    id: 'configuration',
    title: 'Environment Configuration',
    description: 'Configure environment variables to enable OpenAI Assistants API',
    duration: '1 minute',
    commands: [
      {
        description: 'Add to your .env file',
        command: `# Enable OpenAI Assistants API for RAG
USE_OPENAI_ASSISTANTS=true

# Optional configuration
OPENAI_ASSISTANT_MODEL=gpt-4-turbo-preview
OPENAI_ASSISTANT_TEMPERATURE=0.7
OPENAI_ASSISTANT_MAX_TOKENS=4096
OPENAI_FILE_SEARCH_MAX_RESULTS=10`
      }
    ],
    verification: 'Environment variables loaded correctly on server restart',
    icon: Settings,
    color: 'bg-green-50 border-green-200'
  },
  {
    id: 'code-integration',
    title: 'Code Integration',
    description: 'Update routes to use the new conversational agent factory',
    duration: '5-10 minutes',
    commands: [
      {
        description: 'Update conversational.py imports',
        command: `# Old import
from ai_agents.conversational_simple import SimpleConversationalAgent

# New import
from ai_agents.conversational_factory import create_and_initialize_agent`
      },
      {
        description: 'Update agent creation in routes',
        command: `# Old agent creation
@app.post("/api/conversational/message")
async def process_message(request: ConversationRequest):
    agent = SimpleConversationalAgent(request.workspace_id, request.chat_id)

# New agent creation
@app.post("/api/conversational/message")
async def process_message(request: ConversationRequest):
    agent = await create_and_initialize_agent(request.workspace_id, request.chat_id)`
      }
    ],
    verification: 'API endpoints respond correctly with new agent integration',
    icon: Code,
    color: 'bg-purple-50 border-purple-200'
  },
  {
    id: 'testing',
    title: 'Integration Testing',
    description: 'Verify the integration works correctly with file search capabilities',
    duration: '5-10 minutes',
    commands: [
      {
        description: 'Test file upload and search',
        command: `curl -X POST "http://localhost:8000/api/conversational/message" \\
  -H "Content-Type: application/json" \\
  -d '{"workspace_id": "test", "chat_id": "test", "message": "search uploaded files"}'`
      }
    ],
    verification: 'File search returns relevant results from uploaded documents',
    icon: Play,
    color: 'bg-orange-50 border-orange-200'
  }
]

const configurationOptions = [
  {
    key: 'USE_OPENAI_ASSISTANTS',
    type: 'boolean',
    default: 'false',
    description: 'Enable OpenAI Assistants API for RAG functionality',
    required: true
  },
  {
    key: 'OPENAI_ASSISTANT_MODEL',
    type: 'string',
    default: 'gpt-4-turbo-preview',
    description: 'OpenAI model to use for assistants',
    required: false
  },
  {
    key: 'OPENAI_ASSISTANT_TEMPERATURE',
    type: 'float',
    default: '0.7',
    description: 'Temperature setting for assistant responses',
    required: false
  },
  {
    key: 'OPENAI_ASSISTANT_MAX_TOKENS',
    type: 'integer',
    default: '4096',
    description: 'Maximum tokens for assistant responses',
    required: false
  },
  {
    key: 'OPENAI_FILE_SEARCH_MAX_RESULTS',
    type: 'integer',
    default: '10',
    description: 'Maximum number of search results to return',
    required: false
  }
]

const troubleshootingIssues = [
  {
    issue: 'AssistantNotFoundError',
    cause: 'Assistant not properly created or initialized',
    solutions: [
      'Check that USE_OPENAI_ASSISTANTS=true in environment',
      'Verify OpenAI API key has Assistants API access',
      'Run database migration to create workspace_assistants table'
    ]
  },
  {
    issue: 'FileSearchNotWorking',
    cause: 'File search capability not properly configured',
    solutions: [
      'Ensure files are uploaded to correct vector store',
      'Check OPENAI_FILE_SEARCH_MAX_RESULTS configuration',
      'Verify files are processed and indexed by OpenAI'
    ]
  },
  {
    issue: 'SlowResponseTimes',
    cause: 'Assistant initialization or API calls taking too long',
    solutions: [
      'Enable assistant caching in workspace_assistants table',
      'Reduce OPENAI_ASSISTANT_MAX_TOKENS if responses are too long',
      'Check network connectivity to OpenAI API'
    ]
  }
]

export default function IntegrationsPage() {
  const [selectedStep, setSelectedStep] = useState<string | null>(null)
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)

  const copyToClipboard = (text: string, commandId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCommand(commandId)
    setTimeout(() => setCopiedCommand(null), 2000)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-4">
            <Link 
              href="/docs"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
          </div>
          <div className="mt-4">
            <h1 className="text-3xl font-bold text-gray-900">OpenAI Assistants Integration</h1>
            <p className="text-gray-600 mt-2">
              Complete guide to integrating OpenAI Assistants API for advanced RAG capabilities
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Brain className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Integration Overview</h2>
              <p className="text-gray-600">
                Transform your AI system with semantic file search and advanced conversational capabilities
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Semantic Search</h3>
              <p className="text-blue-700 text-sm">
                Replace basic keyword search with AI-powered semantic understanding of document content
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="font-semibold text-green-900 mb-2">Vector Store Integration</h3>
              <p className="text-green-700 text-sm">
                Leverage OpenAI vector stores for efficient document retrieval and context
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="font-semibold text-purple-900 mb-2">Enhanced Conversations</h3>
              <p className="text-purple-700 text-sm">
                Enable AI agents to reference uploaded documents and provide contextual responses
              </p>
            </div>
          </div>
        </div>

        {/* Integration Steps */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Step-by-Step Integration</h2>
          
          <div className="space-y-6">
            {integrationSteps.map((step, index) => {
              const StepIcon = step.icon
              const isSelected = selectedStep === step.id
              
              return (
                <div key={step.id} className="relative">
                  <div 
                    className={`${step.color} border rounded-xl p-6 transition-all cursor-pointer hover:shadow-md ${
                      isSelected ? 'shadow-lg' : ''
                    }`}
                    onClick={() => setSelectedStep(isSelected ? null : step.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center justify-center w-10 h-10 bg-white rounded-lg border-2 border-gray-300">
                          <span className="text-lg font-bold text-gray-700">{index + 1}</span>
                        </div>
                        <div className="p-3 bg-white rounded-xl">
                          <StepIcon className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
                          <p className="text-gray-600 text-sm">{step.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-500">{step.duration}</span>
                        <CheckCircle className={`w-5 h-5 transition-all ${
                          isSelected ? 'text-green-600 rotate-180' : 'text-gray-400'
                        }`} />
                      </div>
                    </div>
                    
                    {isSelected && (
                      <div className="mt-6 space-y-4">
                        {step.commands.map((cmd, cmdIndex) => (
                          <div key={cmdIndex}>
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900 text-sm">{cmd.description}</h4>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  copyToClipboard(cmd.command, `${step.id}-${cmdIndex}`)
                                }}
                                className="flex items-center text-xs text-gray-500 hover:text-gray-700"
                              >
                                <Copy className="w-3 h-3 mr-1" />
                                {copiedCommand === `${step.id}-${cmdIndex}` ? 'Copied!' : 'Copy'}
                              </button>
                            </div>
                            <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg overflow-x-auto">
                              <code>{cmd.command}</code>
                            </pre>
                          </div>
                        ))}
                        
                        <div className="bg-green-50 rounded-lg p-3 mt-4">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <h4 className="font-medium text-green-900 text-sm">Verification</h4>
                          </div>
                          <p className="text-green-700 text-sm mt-1">{step.verification}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Configuration Reference */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Configuration Reference</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Variable</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Type</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Default</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Description</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Required</th>
                </tr>
              </thead>
              <tbody>
                {configurationOptions.map((option, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">{option.key}</code>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{option.type}</td>
                    <td className="py-3 px-4">
                      <code className="text-sm text-gray-700">{option.default}</code>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{option.description}</td>
                    <td className="py-3 px-4">
                      {option.required ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Required
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Optional
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Troubleshooting */}
        <div className="bg-white rounded-xl border p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Troubleshooting</h2>
          
          <div className="space-y-6">
            {troubleshootingIssues.map((issue, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  <h3 className="font-semibold text-gray-900">{issue.issue}</h3>
                </div>
                
                <p className="text-gray-600 mb-4 text-sm">
                  <strong>Cause:</strong> {issue.cause}
                </p>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Solutions:</h4>
                  <ul className="space-y-2">
                    {issue.solutions.map((solution, solIndex) => (
                      <li key={solIndex} className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{solution}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-3">
              <ExternalLink className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-blue-900">Additional Resources</h3>
            </div>
            <div className="space-y-2">
              <a 
                href="https://platform.openai.com/docs/assistants/overview" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block text-blue-700 hover:text-blue-900 text-sm underline"
              >
                OpenAI Assistants API Documentation
              </a>
              <a 
                href="https://platform.openai.com/docs/assistants/tools/file-search" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block text-blue-700 hover:text-blue-900 text-sm underline"
              >
                File Search Tool Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}