'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { MessageSquare, FolderOpen, Play, ArrowRight, Clock, Euro, Users, Lightbulb, Target, Sparkles, BookOpen, FileText, ExternalLink } from 'lucide-react'

// Real suggested projects from /projects page - updated and expanded
const suggestedProjects = [
  {
    id: 'social-growth',
    name: 'Social Growth',
    description: 'Develop growth strategies for Instagram account dedicated to bodybuilders',
    goal: 'Complete Instagram content calendar with 30 posts/reels, growth strategy document with hashtag lists, templates for 5 high-performing post types, competitor analysis report, and weekly tracking dashboard',
    budget: { max_amount: 1200, currency: 'EUR' },
    icon: '📱',
    category: 'Marketing',
    color: 'from-purple-500 to-indigo-600'
  },
  {
    id: 'smart-investing',
    name: 'Smart Investing Guide',
    description: 'Stock analysis and recommendation system based on fundamentals, market trends and sentiment',
    goal: 'Personalized investment portfolio allocation, Excel portfolio tracker with automated P&L calculation, monthly stock screening reports, risk assessment questionnaire, 12-month investment calendar, and emergency exit strategy playbook',
    budget: { max_amount: 1500, currency: 'EUR' },
    icon: '📊',
    category: 'Finance',
    color: 'from-green-500 to-emerald-600'
  },
  {
    id: 'coding-upskill',
    name: 'Coding Upskill Sprint',
    description: 'Intensive JavaScript/React path with hands-on projects and code reviews',
    goal: 'Three complete full-stack applications (E-commerce, Social dashboard, Task management), GitHub repository with clean code, technical portfolio website, code review checklist, open-source contribution strategy, and mock interview preparation',
    budget: { max_amount: 900, currency: 'EUR' },
    icon: '💻',
    category: 'Tech',
    color: 'from-blue-500 to-indigo-600'
  },
  {
    id: 'outbound-mailup',
    name: 'B2B Outbound Sales Lists',
    description: 'Creation and qualification of prospect lists for MailUp outbound campaigns',
    goal: 'Qualified database of 500+ ICP contacts, three complete email sequences with A/B test variants, HubSpot import-ready CSV, competitor analysis, performance tracking dashboard, and sales script templates',
    budget: { max_amount: 1000, currency: 'EUR' },
    icon: '📧',
    category: 'Sales',
    color: 'from-rose-500 to-pink-600'
  },
  {
    id: 'sport-performance',
    name: 'Sport Performance Boost',
    description: 'Integrated training program (strength, cardio, mobility, recovery) designed for those who want to sustainably elevate their athletic level',
    goal: 'Personalized 12-week training program, nutrition plan with macro calculations, injury prevention assessment, performance tracking spreadsheet, video exercise library, and weekly check-in protocols',
    budget: { max_amount: 800, currency: 'EUR' },
    icon: '💪',
    category: 'Health',
    color: 'from-blue-500 to-blue-700'
  },
  {
    id: 'abm-target-accounts',
    name: 'ABM Target Accounts',
    description: 'Identification and engagement of 100 ideal enterprise accounts with multi-channel outreach',
    goal: 'Target account database of 100 enterprise companies, account-specific outreach strategies, multi-channel engagement playbook, sales collateral package, account scoring model, and pipeline tracking dashboard',
    budget: { max_amount: 1200, currency: 'EUR' },
    icon: '🎯',
    category: 'Sales',
    color: 'from-indigo-500 to-violet-600'
  }
]

// Interactive learning steps
const learningSteps = [
  {
    title: 'Describe Your Goal',
    description: 'Simply tell us what you want to accomplish in natural language',
    example: '"Create a marketing plan for our new eco-friendly product line"',
    icon: MessageSquare,
    color: 'blue'
  },
  {
    title: 'AI Team Assembles',
    description: 'Specialized agents deploy automatically based on your needs',
    example: 'Marketing Strategist + Content Creator + Market Researcher',
    icon: Users,
    color: 'green'
  },
  {
    title: 'Collaborative Execution',
    description: 'Watch your AI team work together in real-time',
    example: 'Live updates, thinking processes, and deliverable creation',
    icon: Sparkles,
    color: 'purple'
  }
]

export default function Home() {
  const [currentStep, setCurrentStep] = useState(0)

  // Auto-rotate learning steps every 4 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % learningSteps.length)
    }, 4000)
    return () => clearInterval(timer)
  }, [])
  const handleTemplateClick = (project: typeof suggestedProjects[0]) => {
    // Store project template for new project page (client-side only)
    if (typeof window !== 'undefined') {
      localStorage.setItem('projectTemplate', JSON.stringify(project))
      window.location.href = '/projects/new'
    }
  }

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-6xl mx-auto">
        
        {/* App Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Workspace
          </h1>
          <p className="text-gray-600">
            Start a new project or continue with your existing ones.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <Link 
            href="/projects/new"
            className="group p-6 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                <MessageSquare className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 group-hover:text-blue-900 mb-1">
                  New Project
                </h3>
                <p className="text-sm text-gray-600 group-hover:text-blue-700">
                  Describe your goal and let the AI team handle the rest
                </p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
            </div>
          </Link>

          <Link 
            href="/projects"
            className="group p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gray-50 rounded-xl group-hover:bg-gray-100 transition-colors">
                <FolderOpen className="w-6 h-6 text-gray-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">
                  My Projects
                </h3>
                <p className="text-sm text-gray-600">
                  Continue working on existing projects or explore completed ones
                </p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        </div>

        {/* Project Templates */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Project Templates</h2>
              <p className="text-sm text-gray-600">Get started quickly with these predefined projects</p>
            </div>
          </div>

          <div className="overflow-x-auto pb-4">
            <div className="flex gap-6 w-max">
              {suggestedProjects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => handleTemplateClick(project)}
                  className="p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all text-left group w-80 flex-shrink-0"
                >
                <div className="flex items-start space-x-4">
                  <div className="text-2xl">{project.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-semibold text-gray-900 group-hover:text-gray-800">
                        {project.name}
                      </h3>
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-lg">
                        {project.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      {project.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Euro className="w-3 h-3" />
                        <span>{project.budget.max_amount.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-blue-600 font-medium group-hover:text-blue-700">
                        <Play className="w-3 h-3" />
                        <span>Use template</span>
                      </div>
                    </div>
                  </div>
                </div>
              </button>
              ))}
            </div>
          </div>
        </div>

        {/* Interactive How It Works */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">How it works in practice</h2>
            <p className="text-gray-600">Follow the interactive journey to understand the process</p>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            {/* Step Indicator */}
            <div className="flex justify-center mb-8">
              {learningSteps.map((step, index) => (
                <div key={index} className="flex items-center">
                  <div className={`
                    w-3 h-3 rounded-full transition-all duration-300
                    ${currentStep === index ? 'bg-blue-600' : 'bg-gray-300'}
                  `} />
                  {index < learningSteps.length - 1 && (
                    <div className="w-16 h-px bg-gray-300 mx-2" />
                  )}
                </div>
              ))}
            </div>

            {/* Current Step Content */}
            <div className="text-center max-w-2xl mx-auto">
              <div className={`
                inline-flex items-center justify-center w-16 h-16 rounded-full mb-4
                ${learningSteps[currentStep].color === 'blue' ? 'bg-blue-50' :
                  learningSteps[currentStep].color === 'green' ? 'bg-green-50' : 'bg-purple-50'}
              `}>
                {React.createElement(learningSteps[currentStep].icon, {
                  className: `w-8 h-8 ${
                    learningSteps[currentStep].color === 'blue' ? 'text-blue-600' :
                    learningSteps[currentStep].color === 'green' ? 'text-green-600' : 'text-purple-600'
                  }`
                })}
              </div>
              
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {learningSteps[currentStep].title}
              </h3>
              <p className="text-gray-600 mb-4">
                {learningSteps[currentStep].description}
              </p>
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 font-mono">
                {learningSteps[currentStep].example}
              </div>
            </div>

            {/* Manual Navigation */}
            <div className="flex justify-center space-x-2 mt-6">
              {learningSteps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`
                    w-2 h-2 rounded-full transition-colors
                    ${currentStep === index ? 'bg-blue-600' : 'bg-gray-300 hover:bg-gray-400'}
                  `}
                  aria-label={`Go to step ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Learn More Links */}
        <div className="mb-12">
          <div className="text-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Learn More</h2>
            <p className="text-sm text-gray-600">Discover how this system was built and explore the documentation</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <a
              href="https://books.danielepelleri.com"
              target="_blank"
              rel="noopener noreferrer"
              className="group p-6 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-blue-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                  <BookOpen className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-900 mb-1">
                    Read the Paper
                  </h3>
                  <p className="text-sm text-gray-600 group-hover:text-blue-700">
                    How this AI team orchestration system was built
                  </p>
                </div>
                <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
              </div>
            </a>

            <a
              href="/docs"
              className="group p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gray-50 rounded-xl group-hover:bg-gray-100 transition-colors">
                  <FileText className="w-6 h-6 text-gray-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Documentation
                  </h3>
                  <p className="text-sm text-gray-600">
                    Technical guides and API reference
                  </p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" />
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}