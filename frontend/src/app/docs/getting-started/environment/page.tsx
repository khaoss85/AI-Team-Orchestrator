'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Key, Database, Zap, Shield, Copy, AlertTriangle, CheckCircle } from 'lucide-react'

export default function EnvironmentPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Environment Configuration</h1>
            <p className="text-gray-600">Complete guide to configuring your AI Team Orchestrator environment</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Key className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Configuration Categories</h3>
                    <p className="text-blue-700 text-sm mt-1">API keys, database settings, AI features, and system optimization</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <h4 className="font-medium text-green-900">Required Settings</h4>
                  </div>
                  <p className="text-green-700 text-sm">Essential configurations needed for the system to function</p>
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Zap className="w-5 h-5 text-blue-600" />
                    <h4 className="font-medium text-blue-900">Optional Optimizations</h4>
                  </div>
                  <p className="text-blue-700 text-sm">Advanced settings for performance and feature tuning</p>
                </div>
              </div>
            </section>

            {/* Required Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                Required Configuration
              </h2>

              {/* API Keys */}
              <div className="space-y-8">
                <div className="bg-red-50 rounded-lg p-6 border border-red-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Key className="w-6 h-6 text-red-600" />
                    <h3 className="text-lg font-semibold text-red-900">OpenAI API Configuration</h3>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Required Environment Variable</span>
                      <button 
                        onClick={() => copyToClipboard('OPENAI_API_KEY=sk-your-openai-api-key-here')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-yellow-400 text-sm">
                      <code>OPENAI_API_KEY=sk-your-openai-api-key-here</code>
                    </pre>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">How to get your OpenAI API key:</h4>
                      <ol className="list-decimal list-inside space-y-1 text-red-700 text-sm">
                        <li>Visit <a href="https://platform.openai.com/api-keys" className="underline" target="_blank">platform.openai.com/api-keys</a></li>
                        <li>Sign in or create an OpenAI account</li>
                        <li>Click "Create new secret key"</li>
                        <li>Copy the key (starts with sk-...)</li>
                        <li>Add billing information to your OpenAI account</li>
                      </ol>
                    </div>
                    
                    <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-orange-600" />
                        <span className="font-medium text-orange-900">Cost Estimation</span>
                      </div>
                      <p className="text-orange-700 text-sm">
                        A typical project costs €2-15 in OpenAI API usage depending on complexity. 
                        The system is optimized to minimize costs through smart agent selection and caching.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Supabase Configuration */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Database className="w-6 h-6 text-blue-600" />
                    <h3 className="text-lg font-semibold text-blue-900">Supabase Database Configuration</h3>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Required Environment Variables</span>
                      <button 
                        onClick={() => copyToClipboard(`SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here`)}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-yellow-400 text-sm">
                      <code>{`SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here`}</code>
                    </pre>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">How to setup Supabase:</h4>
                    <ol className="list-decimal list-inside space-y-1 text-blue-700 text-sm">
                      <li>Visit <a href="https://supabase.com" className="underline" target="_blank">supabase.com</a> and create a free account</li>
                      <li>Click "New project" and choose a name</li>
                      <li>Wait for database setup (2-3 minutes)</li>
                      <li>Go to Settings → API to find your keys</li>
                      <li>Copy the "Project URL" and "anon/public" key</li>
                    </ol>
                  </div>
                </div>
              </div>
            </section>

            {/* AI-Driven Features */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                <Zap className="w-6 h-6 text-blue-600 mr-3" />
                AI-Driven Features Configuration
              </h2>

              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200 mb-6">
                <h3 className="font-medium text-purple-900 mb-3">Core AI Features (Recommended: All Enabled)</h3>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400 text-sm">AI System Configuration</span>
                    <button 
                      onClick={() => copyToClipboard(`# Core AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true
ENABLE_AI_AGENT_MATCHING=true
ENABLE_AI_PERSONALITY_GENERATION=true

# Advanced AI Features
ENABLE_AI_ADAPTIVE_THRESHOLDS=true
ENABLE_AI_ADAPTIVE_ENHANCEMENT=true
ENABLE_AI_FAKE_DETECTION=true`)}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                  <pre className="text-green-400 text-sm overflow-x-auto">
                    <code>{`# Core AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true
ENABLE_AI_AGENT_MATCHING=true
ENABLE_AI_PERSONALITY_GENERATION=true

# Advanced AI Features
ENABLE_AI_ADAPTIVE_THRESHOLDS=true
ENABLE_AI_ADAPTIVE_ENHANCEMENT=true
ENABLE_AI_FAKE_DETECTION=true`}</code>
                  </pre>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Core Features Explained:</h4>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Task Similarity:</strong> AI semantic matching instead of keywords</li>
                    <li>• <strong>Task Priority:</strong> Context-aware priority calculation</li>
                    <li>• <strong>Quality Assurance:</strong> AI-driven enhancement loops</li>
                    <li>• <strong>Goal-Driven System:</strong> Automatic goal decomposition</li>
                  </ul>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Advanced Features:</h4>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Adaptive Thresholds:</strong> Context-aware quality thresholds</li>
                    <li>• <strong>Fake Detection:</strong> Prevents placeholder content</li>
                    <li>• <strong>Agent Matching:</strong> Semantic agent-task assignment</li>
                    <li>• <strong>Personality Generation:</strong> Dynamic agent traits</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* System Optimization */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                <Shield className="w-6 h-6 text-green-600 mr-3" />
                System Optimization Settings
              </h2>

              <div className="space-y-6">
                {/* Asset & Deliverable Settings */}
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-3">Asset & Deliverable Configuration</h3>
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Deliverable System Settings</span>
                      <button 
                        onClick={() => copyToClipboard(`# Asset & Deliverable Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100
MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2
DELIVERABLE_CHECK_COOLDOWN_SECONDS=30`)}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-blue-400 text-sm overflow-x-auto">
                      <code>{`# Asset & Deliverable Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100
MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2
DELIVERABLE_CHECK_COOLDOWN_SECONDS=30`}</code>
                    </pre>
                  </div>
                  <p className="text-green-700 text-sm">
                    These settings control deliverable creation and prevent duplicate or low-quality outputs.
                  </p>
                </div>

                {/* Recovery System */}
                <div className="bg-orange-50 rounded-lg p-6 border border-orange-200">
                  <h3 className="font-medium text-orange-900 mb-3">Autonomous Recovery System</h3>
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Auto-Recovery Configuration</span>
                      <button 
                        onClick={() => copyToClipboard(`# Autonomous Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
RECOVERY_BATCH_SIZE=5
RECOVERY_CHECK_INTERVAL_SECONDS=60
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30
AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7`)}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-orange-400 text-sm overflow-x-auto">
                      <code>{`# Autonomous Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
RECOVERY_BATCH_SIZE=5
RECOVERY_CHECK_INTERVAL_SECONDS=60
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30
AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7`}</code>
                    </pre>
                  </div>
                  <p className="text-orange-700 text-sm">
                    Enables automatic recovery from task failures without human intervention.
                  </p>
                </div>

                {/* Goal System */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-3">Goal-Driven System Settings</h3>
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Goal Management Configuration</span>
                      <button 
                        onClick={() => copyToClipboard(`# Goal-Driven System
AUTO_CREATE_GOALS_FROM_WORKSPACE=true
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
GOAL_COMPLETION_THRESHOLD=80
GOAL_VALIDATION_INTERVAL_MINUTES=20
GOAL_VALIDATION_GRACE_PERIOD_HOURS=2`)}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-blue-400 text-sm overflow-x-auto">
                      <code>{`# Goal-Driven System
AUTO_CREATE_GOALS_FROM_WORKSPACE=true
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
GOAL_COMPLETION_THRESHOLD=80
GOAL_VALIDATION_INTERVAL_MINUTES=20
GOAL_VALIDATION_GRACE_PERIOD_HOURS=2`}</code>
                    </pre>
                  </div>
                  <p className="text-blue-700 text-sm">
                    Controls automatic goal creation and validation from workspace descriptions.
                  </p>
                </div>
              </div>
            </section>

            {/* Complete .env Template */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Complete .env Template</h2>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-gray-400">Complete backend/.env file</span>
                  <button 
                    onClick={() => copyToClipboard(`# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Core AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true
ENABLE_AI_AGENT_MATCHING=true
ENABLE_AI_PERSONALITY_GENERATION=true

# Asset & Deliverable Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100
MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2
DELIVERABLE_CHECK_COOLDOWN_SECONDS=30

# Autonomous Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
RECOVERY_BATCH_SIZE=5
RECOVERY_CHECK_INTERVAL_SECONDS=60
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30
AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7

# Goal-Driven System
AUTO_CREATE_GOALS_FROM_WORKSPACE=true
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
GOAL_COMPLETION_THRESHOLD=80
GOAL_VALIDATION_INTERVAL_MINUTES=20
GOAL_VALIDATION_GRACE_PERIOD_HOURS=2

# Quality Assurance
ENABLE_AI_ADAPTIVE_THRESHOLDS=true
ENABLE_AI_ADAPTIVE_ENHANCEMENT=true
ENABLE_AI_FAKE_DETECTION=true

# Performance Settings
PHASE_PLANNING_COOLDOWN_MINUTES=5
MAX_PENDING_TASKS_FOR_TRANSITION=8
AUTO_COMPLETION_RATE_LIMIT_PER_MINUTE=5
GOAL_UNBLOCK_RATE_LIMIT_PER_MINUTE=10`)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <pre className="text-green-400 text-sm overflow-x-auto">
                  <code>{`# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Core AI-Driven Features
ENABLE_AI_TASK_SIMILARITY=true
ENABLE_AI_TASK_PRIORITY=true  
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_GOAL_DRIVEN_SYSTEM=true
ENABLE_AI_AGENT_MATCHING=true
ENABLE_AI_PERSONALITY_GENERATION=true

# Asset & Deliverable Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100
MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2
DELIVERABLE_CHECK_COOLDOWN_SECONDS=30

# Autonomous Recovery System
ENABLE_AUTO_TASK_RECOVERY=true
RECOVERY_BATCH_SIZE=5
RECOVERY_CHECK_INTERVAL_SECONDS=60
MAX_AUTO_RECOVERY_ATTEMPTS=5
RECOVERY_DELAY_SECONDS=30
AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7

# Goal-Driven System
AUTO_CREATE_GOALS_FROM_WORKSPACE=true
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
GOAL_COMPLETION_THRESHOLD=80
GOAL_VALIDATION_INTERVAL_MINUTES=20
GOAL_VALIDATION_GRACE_PERIOD_HOURS=2

# Quality Assurance
ENABLE_AI_ADAPTIVE_THRESHOLDS=true
ENABLE_AI_ADAPTIVE_ENHANCEMENT=true
ENABLE_AI_FAKE_DETECTION=true

# Performance Settings
PHASE_PLANNING_COOLDOWN_MINUTES=5
MAX_PENDING_TASKS_FOR_TRANSITION=8
AUTO_COMPLETION_RATE_LIMIT_PER_MINUTE=5
GOAL_UNBLOCK_RATE_LIMIT_PER_MINUTE=10`}</code>
                </pre>
              </div>
            </section>

            {/* Troubleshooting */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Common Configuration Issues</h2>
              
              <div className="space-y-4">
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <h4 className="font-medium text-red-900 mb-2">OpenAI API Key Issues</h4>
                  <ul className="space-y-1 text-red-700 text-sm">
                    <li>• Check that your key starts with "sk-" and is fully copied</li>
                    <li>• Ensure billing is set up on your OpenAI account</li>
                    <li>• Verify the key has sufficient usage limits</li>
                    <li>• Check for any whitespace or quotes around the key</li>
                  </ul>
                </div>

                <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                  <h4 className="font-medium text-orange-900 mb-2">Supabase Connection Issues</h4>
                  <ul className="space-y-1 text-orange-700 text-sm">
                    <li>• Verify the URL format: https://project-id.supabase.co</li>
                    <li>• Use the "anon/public" key, not the service role key</li>
                    <li>• Check that RLS policies allow your operations</li>
                    <li>• Ensure the database schema is properly migrated</li>
                  </ul>
                </div>

                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2">Performance Issues</h4>
                  <ul className="space-y-1 text-blue-700 text-sm">
                    <li>• Reduce MAX_DELIVERABLES_PER_WORKSPACE if memory is limited</li>
                    <li>• Increase cooldown times if hitting rate limits</li>
                    <li>• Disable some AI features if OpenAI costs are too high</li>
                    <li>• Check backend logs for specific error messages</li>
                  </ul>
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
                    <Zap className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Create Your First Project</h3>
                    <p className="text-gray-600 text-sm">Test your configuration with a real project</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/operations/monitoring"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Shield className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Monitoring & Logging</h3>
                    <p className="text-gray-600 text-sm">Learn how to monitor system health</p>
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