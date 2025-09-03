'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Play,
  Users, 
  Target, 
  Brain, 
  Zap,
  CheckCircle,
  ArrowRight,
  Clock,
  Settings,
  Database,
  FileText,
  BarChart3,
  Lightbulb,
  Shield,
  Cog,
  MessageSquare,
  Package
} from 'lucide-react'

const orchestrationPhases = [
  {
    id: 'user-input',
    title: 'User Project Creation',
    duration: '30 seconds',
    description: 'User creates a new project with business objectives',
    participants: ['User', 'Frontend Interface'],
    inputs: ['Business goal description', 'Domain context', 'Success criteria'],
    outputs: ['Workspace created', 'Initial goal structure'],
    example: 'User: "Lanciare campagna di marketing per prodotto SaaS B2B"',
    icon: MessageSquare,
    color: 'bg-blue-50 border-blue-200',
    iconColor: 'text-blue-600'
  },
  {
    id: 'director-analysis',
    title: 'Director AI Analysis',
    duration: '15-30 seconds',
    description: 'Director Agent analyzes the project and proposes specialized team composition',
    participants: ['Director Agent', 'AI Goal Decomposer'],
    inputs: ['User project description', 'Domain knowledge', 'Historical patterns'],
    outputs: ['Team proposal', 'Goal decomposition', 'Resource estimation'],
    example: 'Director proposes: Marketing Specialist, Content Creator, Analytics Expert',
    icon: Brain,
    color: 'bg-purple-50 border-purple-200',
    iconColor: 'text-purple-600'
  },
  {
    id: 'team-approval',
    title: 'Team Formation & Approval',
    duration: '5-10 seconds',
    description: 'User approves proposed team, agents are instantiated with specialized skills',
    participants: ['User', 'Agent Factory', 'Specialized AI Agents'],
    inputs: ['Team proposal', 'User approval', 'Agent configurations'],
    outputs: ['Active specialized agents', 'Skill matrix', 'Responsibility assignment'],
    example: 'Team activated: 3 specialized agents with marketing, content, and analytics expertise',
    icon: Users,
    color: 'bg-green-50 border-green-200',
    iconColor: 'text-green-600'
  },
  {
    id: 'goal-planning',
    title: 'AI-Driven Goal Planning',
    duration: '20-45 seconds',
    description: 'AI system decomposes business objectives into concrete, measurable goals with tasks',
    participants: ['Goal Planning AI', 'Task Generator', 'Domain Expert Agents'],
    inputs: ['Business objectives', 'Domain expertise', 'Success patterns'],
    outputs: ['Concrete goals', 'Task breakdown', 'Success metrics'],
    example: 'Goal 1: Email campaign (5 tasks), Goal 2: Landing page (7 tasks), Goal 3: Analytics (3 tasks)',
    icon: Target,
    color: 'bg-orange-50 border-orange-200',
    iconColor: 'text-orange-600'
  },
  {
    id: 'task-execution',
    title: 'Autonomous Task Execution',
    duration: '2-30 minutes',
    description: 'Specialized agents execute tasks autonomously using real tools and APIs',
    participants: ['Specialized Agents', 'Tool Registry', 'External APIs'],
    inputs: ['Task specifications', 'Real-world tools', 'Business context'],
    outputs: ['Task completions', 'Intermediate deliverables', 'Progress updates'],
    example: 'Marketing Agent creates email sequence, Content Agent writes copy, Analytics Agent sets tracking',
    icon: Cog,
    color: 'bg-indigo-50 border-indigo-200',
    iconColor: 'text-indigo-600'
  },
  {
    id: 'quality-gates',
    title: 'Quality Assurance Gates',
    duration: '5-15 seconds',
    description: 'Autonomous quality gates validate all deliverables before finalization',
    participants: ['8 Quality Gate Agents', 'Compliance Systems'],
    inputs: ['Completed deliverables', 'Quality standards', 'Compliance rules'],
    outputs: ['Quality validation', 'Compliance confirmation', 'Improvement suggestions'],
    example: 'Placeholder Police ensures no TODOs, Principles Guardian validates architecture',
    icon: Shield,
    color: 'bg-red-50 border-red-200',
    iconColor: 'text-red-600'
  },
  {
    id: 'deliverable-generation',
    title: 'Professional Deliverable Creation',
    duration: '10-30 seconds',
    description: 'AI transforms raw outputs into professional business deliverables',
    participants: ['AI Content Transformer', 'Business Format Engine'],
    inputs: ['Raw task outputs', 'Business templates', 'Professional standards'],
    outputs: ['Professional deliverables', 'Executive summaries', 'Action plans'],
    example: 'Email campaign → Professional marketing brief with metrics and timeline',
    icon: FileText,
    color: 'bg-cyan-50 border-cyan-200',
    iconColor: 'text-cyan-600'
  },
  {
    id: 'learning-integration',
    title: 'Workspace Memory Learning',
    duration: '5-10 seconds',
    description: 'System learns from project outcomes and stores patterns for future reuse',
    participants: ['Learning Engine', 'Pattern Recognition', 'Workspace Memory'],
    inputs: ['Project outcomes', 'Success metrics', 'Failure patterns'],
    outputs: ['Success patterns stored', 'Lessons learned', 'Future optimizations'],
    example: 'Learns: "SaaS B2B campaigns succeed with technical case studies + ROI focus"',
    icon: Lightbulb,
    color: 'bg-yellow-50 border-yellow-200',
    iconColor: 'text-yellow-600'
  }
]

const systemComponents = [
  {
    name: 'Director Agent',
    role: 'Project orchestrator and team composer',
    responsibility: 'Analyzes project requirements and proposes optimal team composition',
    icon: Brain
  },
  {
    name: 'Specialized Agents',
    role: 'Domain experts (marketing, dev, analytics, etc.)',
    responsibility: 'Execute domain-specific tasks using real tools and expertise',
    icon: Users
  },
  {
    name: 'Quality Gates',
    role: '8 autonomous quality assurance agents',
    responsibility: 'Validate code quality, compliance, and production readiness',
    icon: Shield
  },
  {
    name: 'AI Goal Decomposer',
    role: 'Breaks business objectives into concrete tasks',
    responsibility: 'Transform high-level goals into actionable, measurable tasks',
    icon: Target
  },
  {
    name: 'Learning Engine',
    role: 'Workspace memory and pattern recognition',
    responsibility: 'Learn from successes/failures, optimize future performance',
    icon: Lightbulb
  },
  {
    name: 'Tool Registry',
    role: 'Real-world tool and API integration',
    responsibility: 'Provide agents access to external services and tools',
    icon: Cog
  }
]

const realWorldExample = {
  project: "Launch SaaS B2B Marketing Campaign",
  timeline: "45 minutes total",
  phases: [
    {
      phase: "Project Setup",
      time: "0-30s",
      action: "User describes: 'Launch marketing campaign for our project management SaaS targeting engineering teams'",
      result: "Workspace created with domain context"
    },
    {
      phase: "AI Analysis",
      time: "30s-1m",
      action: "Director analyzes project, identifies need for technical marketing approach",
      result: "Proposes team: Marketing Specialist, Technical Content Creator, Developer Relations Expert"
    },
    {
      phase: "Team Formation",
      time: "1m-1m30s", 
      action: "User approves team, agents instantiated with B2B SaaS expertise",
      result: "3 specialized agents active with defined responsibilities"
    },
    {
      phase: "Goal Planning",
      time: "1m30s-3m",
      action: "AI decomposes campaign into: technical content, developer outreach, metrics tracking",
      result: "15 concrete tasks across 3 goals with success metrics"
    },
    {
      phase: "Task Execution",
      time: "3m-35m",
      action: "Agents create technical blog posts, LinkedIn strategy, GitHub integration examples",
      result: "Professional marketing materials tailored for engineering audience"
    },
    {
      phase: "Quality Review",
      time: "35m-40m",
      action: "Quality gates validate technical accuracy, compliance, brand consistency",
      result: "All deliverables pass quality standards, ready for deployment"
    },
    {
      phase: "Final Deliverables",
      time: "40m-45m",
      action: "System generates executive summary, implementation timeline, success metrics",
      result: "Complete marketing campaign ready for immediate execution"
    }
  ]
}

const performanceMetrics = [
  {
    metric: 'End-to-End Speed',
    value: '3-45 min',
    description: 'Complete project from concept to deliverables',
    icon: Clock
  },
  {
    metric: 'Quality Success Rate',
    value: '97%',
    description: 'Deliverables passing all quality gates',
    icon: CheckCircle
  },
  {
    metric: 'Domain Accuracy',
    value: '91%',
    description: 'Contextually appropriate solutions',
    icon: Target
  },
  {
    metric: 'User Satisfaction',
    value: '94%',
    description: 'Users satisfied with final outputs',
    icon: Users
  }
]

export default function CompleteOrchestrationPage() {
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null)
  const [showRealExample, setShowRealExample] = useState(false)

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
            <h1 className="text-3xl font-bold text-gray-900">Complete AI Orchestration Workflow</h1>
            <p className="text-gray-600 mt-2">
              End-to-end journey from user project creation to professional deliverables
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Play className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
              <p className="text-gray-600">
                From business idea to professional deliverables in minutes, not hours
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {performanceMetrics.map((metric) => (
              <div key={metric.metric} className="text-center">
                <div className="flex justify-center mb-2">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <metric.icon className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">{metric.value}</div>
                <div className="font-medium text-gray-900 mb-1">{metric.metric}</div>
                <div className="text-sm text-gray-600">{metric.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Orchestration Flow */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Complete Orchestration Flow</h2>
          
          <div className="space-y-6">
            {orchestrationPhases.map((phase, index) => {
              const PhaseIcon = phase.icon
              const isSelected = selectedPhase === phase.id
              
              return (
                <div key={phase.id} className="relative">
                  <div 
                    className={`${phase.color} border rounded-xl p-6 transition-all cursor-pointer hover:shadow-md ${
                      isSelected ? 'shadow-lg' : ''
                    }`}
                    onClick={() => setSelectedPhase(isSelected ? null : phase.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-white rounded-lg border-2 border-gray-200">
                          <span className="text-lg font-bold text-gray-600">{index + 1}</span>
                        </div>
                        <div className={`p-3 rounded-xl bg-white`}>
                          <PhaseIcon className={`w-6 h-6 ${phase.iconColor}`} />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{phase.title}</h3>
                          <p className="text-gray-600 text-sm">{phase.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-500">{phase.duration}</span>
                        <ArrowRight className={`w-4 h-4 text-gray-400 transition-transform ${
                          isSelected ? 'rotate-90' : ''
                        }`} />
                      </div>
                    </div>
                    
                    {isSelected && (
                      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Participants</h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {phase.participants.map((participant, idx) => (
                              <li key={idx} className="flex items-center">
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2" />
                                {participant}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Key Inputs</h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {phase.inputs.map((input, idx) => (
                              <li key={idx} className="flex items-center">
                                <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mr-2" />
                                {input}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Outputs Generated</h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {phase.outputs.map((output, idx) => (
                              <li key={idx} className="flex items-center">
                                <div className="w-1.5 h-1.5 bg-green-400 rounded-full mr-2" />
                                {output}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-4">
                      <div className="bg-white rounded-lg p-3 border">
                        <h4 className="font-medium text-gray-900 text-sm mb-1">Example</h4>
                        <p className="text-sm text-gray-600 italic">{phase.example}</p>
                      </div>
                    </div>
                  </div>
                  
                  {index < orchestrationPhases.length - 1 && (
                    <div className="flex justify-center py-2">
                      <ArrowRight className="w-5 h-5 text-gray-300" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* System Components */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Core System Components</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {systemComponents.map((component) => {
              const ComponentIcon = component.icon
              
              return (
                <div key={component.name} className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <ComponentIcon className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{component.name}</h3>
                      <p className="text-sm text-gray-600">{component.role}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700">{component.responsibility}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Real World Example */}
        <div className="bg-white rounded-xl border p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Real-World Example</h2>
            <button
              onClick={() => setShowRealExample(!showRealExample)}
              className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
            >
              {showRealExample ? 'Hide' : 'Show'} Complete Example
            </button>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">Project: {realWorldExample.project}</h3>
            <p className="text-gray-600 mb-2">Total Timeline: {realWorldExample.timeline}</p>
            <p className="text-sm text-gray-600">
              Complete walkthrough from user input to final professional deliverables
            </p>
          </div>
          
          {showRealExample && (
            <div className="space-y-4">
              {realWorldExample.phases.map((phase, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{phase.phase}</h4>
                    <span className="text-sm font-medium text-blue-600">{phase.time}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{phase.action}</p>
                  <div className="bg-green-50 rounded p-2">
                    <p className="text-sm text-green-800">
                      <CheckCircle className="w-3 h-3 inline mr-1" />
                      {phase.result}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}