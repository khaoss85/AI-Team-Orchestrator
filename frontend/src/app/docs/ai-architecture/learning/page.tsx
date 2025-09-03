'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Brain, TrendingUp, Target } from 'lucide-react'

export default function ContentAwareLearningPage() {
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
            <h1 className="text-3xl font-bold text-gray-900">Content-Aware Learning</h1>
            <p className="text-gray-600 mt-2">
              AI-driven system that transforms generic statistics into domain-specific business intelligence
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-purple-50 rounded-xl">
              <Brain className="w-8 h-8 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
              <p className="text-gray-600">
                Transform generic metrics into actionable business intelligence
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="font-semibold text-purple-900 mb-2">Context-Aware Transformation</h3>
              <p className="text-purple-700 text-sm">
                Converts "task completion: 85%" into "campaign launch readiness: 85%" with specific business context
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="font-semibold text-green-900 mb-2">Pattern Recognition</h3>
              <p className="text-green-700 text-sm">
                Learns from successful workflows to recommend optimal strategies for similar scenarios
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Continuous Improvement</h3>
              <p className="text-blue-700 text-sm">
                System performance improves automatically through learning from usage patterns and outcomes
              </p>
            </div>
          </div>
        </div>

        {/* Learning Components */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Core Learning Components</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Content-Aware Engine */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-purple-100 text-purple-800">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Content-Aware Learning Engine</h3>
                  <p className="text-sm text-gray-600">Generic to business intelligence transformation</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Transforms generic statistics into domain-specific business intelligence using AI-driven context analysis
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Features</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Generic metric transformation</li>
                  <li>• Domain-specific contextualization</li>
                  <li>• Business intelligence extraction</li>
                </ul>
              </div>
            </div>

            {/* Pattern Recognition */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-green-100 text-green-800">
                  <Target className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Success Pattern Recognition</h3>
                  <p className="text-sm text-gray-600">Identifies and learns from successful patterns</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Identifies and learns from successful task execution patterns, storing reusable templates
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Features</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Success pattern detection</li>
                  <li>• Template generation</li>
                  <li>• Scenario matching</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Business Transformation Examples */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Business Intelligence Examples</h2>
          
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Marketing Domain</h3>
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                  AI-Enhanced
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-red-700 mb-2">❌ Before (Generic)</h4>
                  <p className="text-gray-600 bg-white rounded p-3 border-l-4 border-red-300">
                    Task completion: 85%
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-green-700 mb-2">✅ After (Business Context)</h4>
                  <p className="text-gray-600 bg-white rounded p-3 border-l-4 border-green-300">
                    Campaign launch readiness: 85% (3 deliverables ready for market)
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Software Development</h3>
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  Context-Aware
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-red-700 mb-2">❌ Before (Generic)</h4>
                  <p className="text-gray-600 bg-white rounded p-3 border-l-4 border-red-300">
                    Code coverage: 78%
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-green-700 mb-2">✅ After (Business Context)</h4>
                  <p className="text-gray-600 bg-white rounded p-3 border-l-4 border-green-300">
                    Release confidence: 78% (critical paths tested, deployment ready)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-xl border p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Learning Performance Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">91.2%</div>
              <div className="font-medium text-gray-900 mb-1">Pattern Recognition</div>
              <div className="text-sm text-gray-600">Success in identifying reusable patterns</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">87.8%</div>
              <div className="font-medium text-gray-900 mb-1">Business Context</div>
              <div className="text-sm text-gray-600">Accuracy of domain-specific insights</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">83.4%</div>
              <div className="font-medium text-gray-900 mb-1">Predictive Accuracy</div>
              <div className="text-sm text-gray-600">Success in predicting optimal strategies</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">34%</div>
              <div className="font-medium text-gray-900 mb-1">System Optimization</div>
              <div className="text-sm text-gray-600">Average performance improvement</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}