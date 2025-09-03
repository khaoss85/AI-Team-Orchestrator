'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, RefreshCw, Shield, AlertTriangle, CheckCircle, Clock, Brain, Zap, TrendingUp, Settings } from 'lucide-react'

export default function RecoveryPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Autonomous Recovery System</h1>
            <p className="text-gray-600">Zero-intervention failure recovery with AI-driven strategies</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-green-50 rounded-lg p-6 border border-green-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Shield className="w-6 h-6 text-green-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-green-900">Zero Human Intervention</h3>
                    <p className="text-green-700 mt-1">
                      The system automatically detects, analyzes, and recovers from task failures using 
                      AI-driven strategies, ensuring continuous operation without manual intervention.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The Autonomous Recovery System represents a paradigm shift from traditional error handling. 
                  Instead of stopping and waiting for human intervention, the system intelligently analyzes 
                  failures and applies contextual recovery strategies to maintain operational continuity.
                </p>
              </div>
            </section>

            {/* Recovery Strategies */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Brain className="w-6 h-6 mr-3 text-indigo-600" />
                AI-Driven Recovery Strategies
              </h2>

              <div className="space-y-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <RefreshCw className="w-6 h-6 text-blue-600" />
                    <h3 className="font-semibold text-blue-900">Retry with Different Agent</h3>
                    <span className="px-2 py-1 bg-blue-200 text-blue-800 text-xs rounded">High Success Rate</span>
                  </div>
                  <p className="text-blue-800 text-sm mb-3">
                    Reassigns the task to a different specialized agent with complementary skills or higher seniority.
                  </p>
                  <div className="bg-white rounded p-3 border border-blue-300">
                    <p className="text-xs text-blue-700">
                      <strong>Example:</strong> Content task fails with Junior → automatically reassigned to Senior Content Specialist with domain expertise
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Zap className="w-6 h-6 text-green-600" />
                    <h3 className="font-semibold text-green-900">Decompose into Subtasks</h3>
                    <span className="px-2 py-1 bg-green-200 text-green-800 text-xs rounded">Complex Tasks</span>
                  </div>
                  <p className="text-green-800 text-sm mb-3">
                    Breaks complex failed tasks into smaller, more manageable subtasks that can be executed independently.
                  </p>
                  <div className="bg-white rounded p-3 border border-green-300">
                    <p className="text-xs text-green-700">
                      <strong>Example:</strong> "Create marketing campaign" fails → splits into "research target audience", "write copy", "design assets"
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Settings className="w-6 h-6 text-purple-600" />
                    <h3 className="font-semibold text-purple-900">Alternative Approach</h3>
                    <span className="px-2 py-1 bg-purple-200 text-purple-800 text-xs rounded">Methodology Change</span>
                  </div>
                  <p className="text-purple-800 text-sm mb-3">
                    Changes the implementation strategy or methodology while maintaining the same objective.
                  </p>
                  <div className="bg-white rounded p-3 border border-purple-300">
                    <p className="text-xs text-purple-700">
                      <strong>Example:</strong> API integration fails → switches from REST to GraphQL approach, or uses different authentication method
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Brain className="w-6 h-6 text-orange-600" />
                    <h3 className="font-semibold text-orange-900">Context Reconstruction</h3>
                    <span className="px-2 py-1 bg-orange-200 text-orange-800 text-xs rounded">Memory-Based</span>
                  </div>
                  <p className="text-orange-800 text-sm mb-3">
                    Rebuilds lost execution context from workspace memory and previous successful patterns.
                  </p>
                  <div className="bg-white rounded p-3 border border-orange-300">
                    <p className="text-xs text-orange-700">
                      <strong>Example:</strong> Agent loses context mid-task → reconstructs from previous similar successful executions in workspace memory
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-6 border border-yellow-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <CheckCircle className="w-6 h-6 text-yellow-600" />
                    <h3 className="font-semibold text-yellow-900">Skip with Fallback</h3>
                    <span className="px-2 py-1 bg-yellow-200 text-yellow-800 text-xs rounded">80% Completion</span>
                  </div>
                  <p className="text-yellow-800 text-sm mb-3">
                    Completes the task with a fallback deliverable when the primary approach repeatedly fails.
                  </p>
                  <div className="bg-white rounded p-3 border border-yellow-300">
                    <p className="text-xs text-yellow-700">
                      <strong>Example:</strong> Complex technical implementation fails → provides documented architecture plan instead of full code
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Recovery Flow */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Clock className="w-6 h-6 mr-3 text-indigo-600" />
                Recovery Flow & Timeline
              </h2>

              <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Immediate Recovery (Real-time)</h3>
                <div className="flex items-center justify-between text-sm mb-4">
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <AlertTriangle className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">Task Failure Detected</p>
                    <p className="text-xs text-red-600 font-semibold">0s</p>
                  </div>
                  <div className="w-8 h-0.5 bg-gray-300"></div>
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <Brain className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">AI Strategy Analysis</p>
                    <p className="text-xs text-blue-600 font-semibold">1-3s</p>
                  </div>
                  <div className="w-8 h-0.5 bg-gray-300"></div>
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <RefreshCw className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">Recovery Executed</p>
                    <p className="text-xs text-green-600 font-semibold">&lt; 60s</p>
                  </div>
                </div>
                <p className="text-xs text-gray-600">
                  Immediate recovery handles timeouts, connection issues, and transient failures automatically.
                </p>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                <h3 className="font-semibold text-blue-900 mb-4">Batch Recovery (Scheduled)</h3>
                <div className="flex items-center justify-between text-sm mb-4">
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <Clock className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">Periodic Scan</p>
                    <p className="text-xs text-purple-600 font-semibold">Every 60s</p>
                  </div>
                  <div className="w-8 h-0.5 bg-gray-300"></div>
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <Shield className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">Batch Processing</p>
                    <p className="text-xs text-orange-600 font-semibold">5 tasks max</p>
                  </div>
                  <div className="w-8 h-0.5 bg-gray-300"></div>
                  <div className="text-center flex-1">
                    <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center mb-2 mx-auto">
                      <TrendingUp className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-gray-600">Status Update</p>
                    <p className="text-xs text-green-600 font-semibold">Real-time</p>
                  </div>
                </div>
                <p className="text-xs text-gray-600">
                  Background scheduler finds and recovers complex failures that require deeper analysis.
                </p>
              </div>
            </section>

            {/* Workspace Status Management */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Workspace Status Management</h2>

              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200 mb-6">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-yellow-900">Eliminated Manual States</h3>
                    <p className="text-yellow-700 mt-1">
                      The deprecated "needs_intervention" state has been completely eliminated. All failures 
                      are handled autonomously through "auto_recovering" and "degraded_mode" states.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Autonomous States</h4>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-blue-900">auto_recovering</div>
                        <p className="text-xs text-blue-700">AI-driven recovery in progress</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-orange-900">degraded_mode</div>
                        <p className="text-xs text-orange-700">Operating with reduced functionality but autonomous</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-green-900">active</div>
                        <p className="text-xs text-green-700">Full operational status</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">State Transitions</h4>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">active</span>
                      <span className="text-gray-500">→</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">auto_recovering</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">auto_recovering</span>
                      <span className="text-gray-500">→</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">active</span>
                      <span className="text-xs text-gray-600">(success)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">auto_recovering</span>
                      <span className="text-gray-500">→</span>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">degraded_mode</span>
                      <span className="text-xs text-gray-600">(partial)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">degraded_mode</span>
                      <span className="text-gray-500">→</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">active</span>
                      <span className="text-xs text-gray-600">(recovery)</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance Metrics */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance & Reliability</h2>

              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-6 text-center border border-green-200">
                  <div className="text-3xl font-bold text-green-900 mb-2">85%+</div>
                  <div className="text-sm text-green-700">Recovery success rate</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center border border-blue-200">
                  <div className="text-3xl font-bold text-blue-900 mb-2">&lt; 60s</div>
                  <div className="text-sm text-blue-700">Average recovery time</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center border border-purple-200">
                  <div className="text-3xl font-bold text-purple-900 mb-2">100%</div>
                  <div className="text-sm text-purple-700">Zero-intervention operations</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-6 text-center border border-orange-200">
                  <div className="text-3xl font-bold text-orange-900 mb-2">5</div>
                  <div className="text-sm text-orange-700">Max recovery attempts</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4">System Continuity Benefits</h4>
                <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Operational Excellence</h5>
                    <ul className="space-y-1">
                      <li>• Never blocks on failed tasks</li>
                      <li>• Maintains goal and deliverable relationships</li>
                      <li>• Preserves execution context</li>
                      <li>• Fast recovery times minimize downtime</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Business Impact</h5>
                    <ul className="space-y-1">
                      <li>• 24/7 autonomous operation</li>
                      <li>• Reduced operational overhead</li>
                      <li>• Higher system reliability</li>
                      <li>• Continuous project progress</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Technical Implementation */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Technical Implementation</h2>

              <div className="bg-gray-900 rounded-lg p-6 text-white mb-6">
                <h3 className="text-lg font-semibold mb-4 text-green-400">Core Recovery Engine</h3>
                <pre className="text-sm overflow-x-auto">
                  <code>{`# Autonomous recovery services
backend/services/autonomous_task_recovery.py
backend/services/failed_task_resolver.py

# Main recovery functions
async def autonomous_task_recovery(
    workspace_id: str,
    max_attempts: int = 5
) -> RecoveryResult

async def auto_recover_workspace_tasks(
    workspace_id: str
) -> BatchRecoveryResult

# Recovery strategies
RETRY_WITH_DIFFERENT_AGENT
DECOMPOSE_INTO_SUBTASKS  
ALTERNATIVE_APPROACH
CONTEXT_RECONSTRUCTION
SKIP_WITH_FALLBACK`}</code>
                </pre>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">Integration Points</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Executor failure detection</li>
                    <li>• WebSocket status updates</li>
                    <li>• Background scheduler</li>
                    <li>• Workspace memory integration</li>
                  </ul>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-3">API Endpoints</h4>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>• <code>POST /api/recovery/workspace/{id}/recover</code></li>
                    <li>• <code>GET /api/recovery/{workspace_id}/status</code></li>
                    <li>• <code>GET /api/monitoring/recovery-metrics</code></li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Configuration</h2>

              <div className="bg-gray-100 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Environment Variables</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_AUTO_TASK_RECOVERY=true</code>
                    <span className="text-gray-600 text-xs">Enable autonomous recovery system</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">MAX_AUTO_RECOVERY_ATTEMPTS=5</code>
                    <span className="text-gray-600 text-xs">Maximum recovery attempts per task</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">RECOVERY_DELAY_SECONDS=30</code>
                    <span className="text-gray-600 text-xs">Base delay with exponential backoff</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7</code>
                    <span className="text-gray-600 text-xs">Minimum AI confidence for strategy selection</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">RECOVERY_CHECK_INTERVAL_SECONDS=60</code>
                    <span className="text-gray-600 text-xs">Background scheduler check interval</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Related Concepts */}
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/tasks"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <CheckCircle className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Tasks</h3>
                  <p className="text-sm text-gray-600">Task execution lifecycle</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/memory"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Brain className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Memory</h3>
                  <p className="text-sm text-gray-600">Learning from recovery patterns</p>
                </Link>

                <Link 
                  href="/docs/operations/monitoring"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <TrendingUp className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Monitoring</h3>
                  <p className="text-sm text-gray-600">System health and metrics</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}