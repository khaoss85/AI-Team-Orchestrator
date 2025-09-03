'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, CheckCircle, AlertCircle, Copy, Terminal, Download, Key } from 'lucide-react'

export default function InstallationPage() {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Installation Guide</h1>
            <p className="text-gray-600">Set up the AI Team Orchestrator in less than 5 minutes</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Prerequisites */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                Prerequisites
              </h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span>Python 3.11+ installed</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span>Node.js 18+ and npm installed</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span>Git installed</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span>OpenAI API key</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span>Supabase account (free tier works)</span>
                </div>
              </div>
            </section>

            {/* Step 1: Clone Repository */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full mr-3">1</span>
                Clone the Repository
              </h2>
              <div className="bg-gray-900 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-400 text-sm">Terminal</span>
                  </div>
                  <button 
                    onClick={() => copyToClipboard('git clone https://github.com/yourusername/ai-team-orchestrator.git\ncd ai-team-orchestrator')}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <pre className="text-green-400 text-sm overflow-x-auto">
                  <code>{`git clone https://github.com/yourusername/ai-team-orchestrator.git
cd ai-team-orchestrator`}</code>
                </pre>
              </div>
            </section>

            {/* Step 2: Backend Setup */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full mr-3">2</span>
                Backend Setup (FastAPI)
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Install Python Dependencies</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Terminal className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 text-sm">Terminal</span>
                      </div>
                      <button 
                        onClick={() => copyToClipboard('cd backend\npython -m venv venv\nsource venv/bin/activate  # On Windows: venv\\Scripts\\activate\npip install -r requirements.txt')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt`}</code>
                    </pre>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Environment Configuration</h3>
                  <p className="text-gray-600 mb-4">Create a <code className="bg-gray-100 px-2 py-1 rounded">.env</code> file in the backend directory:</p>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Key className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 text-sm">backend/.env</span>
                      </div>
                      <button 
                        onClick={() => copyToClipboard(`# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# System Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100

# AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true

# Auto-Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30`)}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-yellow-400 text-sm overflow-x-auto">
                      <code>{`# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# System Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100

# AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true

# Auto-Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30`}</code>
                    </pre>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Start the Backend Server</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Terminal className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 text-sm">Terminal (backend directory)</span>
                      </div>
                      <button 
                        onClick={() => copyToClipboard('python main.py')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>python main.py</code>
                    </pre>
                  </div>
                  <p className="text-gray-600 mt-2">The backend will start on <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:8000</code></p>
                </div>
              </div>
            </section>

            {/* Step 3: Frontend Setup */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full mr-3">3</span>
                Frontend Setup (Next.js)
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Install Node Dependencies</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Terminal className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 text-sm">Terminal (new terminal)</span>
                      </div>
                      <button 
                        onClick={() => copyToClipboard('cd frontend\nnpm install')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`cd frontend
npm install`}</code>
                    </pre>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Start the Development Server</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Terminal className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 text-sm">Terminal (frontend directory)</span>
                      </div>
                      <button 
                        onClick={() => copyToClipboard('npm run dev')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>npm run dev</code>
                    </pre>
                  </div>
                  <p className="text-gray-600 mt-2">The frontend will start on <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:3000</code></p>
                </div>
              </div>
            </section>

            {/* Step 4: Verification */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-green-600 text-white text-sm font-semibold rounded-full mr-3">4</span>
                Verify Installation
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-4 bg-green-50 rounded-lg border border-green-200">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <div>
                    <p className="font-medium text-green-900">Frontend is running</p>
                    <p className="text-green-700 text-sm">Visit <a href="http://localhost:3000" className="underline">http://localhost:3000</a> in your browser</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3 p-4 bg-green-50 rounded-lg border border-green-200">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <div>
                    <p className="font-medium text-green-900">Backend API is responding</p>
                    <p className="text-green-700 text-sm">Check <a href="http://localhost:8000/health" className="underline">http://localhost:8000/health</a> for API status</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <AlertCircle className="w-6 h-6 text-blue-600" />
                  <div>
                    <p className="font-medium text-blue-900">Ready to create your first project!</p>
                    <p className="text-blue-700 text-sm">Follow the "Your First Project" guide to get started</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Next Steps</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/getting-started/first-project"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Download className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Your First Project</h3>
                    <p className="text-gray-600 text-sm">Create and run your first AI team project</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/getting-started/environment"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Key className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Advanced Configuration</h3>
                    <p className="text-gray-600 text-sm">Fine-tune your environment settings</p>
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