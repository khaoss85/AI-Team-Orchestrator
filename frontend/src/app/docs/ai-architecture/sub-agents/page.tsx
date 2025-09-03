'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Users, Shield, Database } from 'lucide-react'

export default function SubAgentsPage() {
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
            <h1 className="text-3xl font-bold text-gray-900">Sub-Agent Orchestration</h1>
            <p className="text-gray-600 mt-2">
              Specialized AI agents working in coordinated quality gates for autonomous code review
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-purple-50 rounded-xl">
              <Users className="w-8 h-8 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
              <p className="text-gray-600">
                8 specialized AI agents working as coordinated quality gates
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Autonomous Quality Control</h3>
              <p className="text-blue-700 text-sm">
                Sub-agents automatically trigger on file changes, providing comprehensive code review
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="font-semibold text-green-900 mb-2">Cost Optimized</h3>
              <p className="text-green-700 text-sm">
                Smart conditional triggering reduces API costs by 94% while maintaining quality
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="font-semibold text-purple-900 mb-2">Production Ready</h3>
              <p className="text-purple-700 text-sm">
                Prevents placeholder code, enforces best practices, ensures documentation consistency
              </p>
            </div>
          </div>
        </div>

        {/* Sub-Agents */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Core Sub-Agents</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Director */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-purple-100 text-purple-800">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Director</h3>
                  <p className="text-sm text-gray-600">Main orchestrator and quality gate trigger</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Analyzes projects, proposes specialized teams, and triggers other sub-agents as quality gates
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Functions</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Project analysis & decomposition</li>
                  <li>• Team composition planning</li>
                  <li>• Quality gate orchestration</li>
                </ul>
              </div>
            </div>

            {/* System Architect */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-blue-100 text-blue-800">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">System Architect</h3>
                  <p className="text-sm text-gray-600">Architectural consistency guardian</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Ensures architectural consistency, component reuse, and prevents anti-patterns
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Functions</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Architecture pattern enforcement</li>
                  <li>• Component reuse optimization</li>
                  <li>• Anti-pattern detection</li>
                </ul>
              </div>
            </div>

            {/* DB Steward */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-green-100 text-green-800">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">DB Steward</h3>
                  <p className="text-sm text-gray-600">Database schema guardian</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Proactively manages Supabase schema changes, prevents duplicates, ensures migration safety
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Functions</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Schema migration validation</li>
                  <li>• Duplicate detection & prevention</li>
                  <li>• Data integrity checks</li>
                </ul>
              </div>
            </div>

            {/* Principles Guardian */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-red-100 text-red-800">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Principles Guardian</h3>
                  <p className="text-sm text-gray-600">15 Pillars compliance enforcer</p>
                </div>
              </div>
              <p className="text-gray-700 text-sm mb-4">
                Enforces architectural pillars, blocks critical violations, ensures SDK compliance
              </p>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-1">Key Functions</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• 15 Pillars compliance validation</li>
                  <li>• Critical violation detection</li>
                  <li>• SDK compliance verification</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-xl border p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Performance Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">94%</div>
              <div className="font-medium text-gray-900 mb-1">Cost Optimization</div>
              <div className="text-sm text-gray-600">Reduction through smart conditional triggering</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">97%</div>
              <div className="font-medium text-gray-900 mb-1">Quality Gate Success</div>
              <div className="text-sm text-gray-600">Issues caught before production</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">8.3s</div>
              <div className="font-medium text-gray-900 mb-1">Average Response Time</div>
              <div className="text-sm text-gray-600">Complete quality gate cycle</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">2.1%</div>
              <div className="font-medium text-gray-900 mb-1">False Positive Rate</div>
              <div className="text-sm text-gray-600">Incorrect issue detections</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}