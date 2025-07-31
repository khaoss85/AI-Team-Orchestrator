'use client'

import React, { useState } from 'react'
import DeliverableActionBar from './DeliverableActionBar'

interface DeliverableMessageProps {
  deliverable: {
    id: string
    title: string
    content: any
    contentType?: 'HTML' | 'Structured' | 'Basic'
    type?: string
    businessValueScore?: number
    goalDescription?: string
  }
  timestamp?: string
  compact?: boolean
}

export default function DeliverableMessage({ 
  deliverable, 
  timestamp = new Date().toISOString(),
  compact = false 
}: DeliverableMessageProps) {
  const [isExpanded, setIsExpanded] = useState(!compact)

  // 🤖 AI-DRIVEN: Smart content preview generation
  const generatePreview = () => {
    // Handle direct string content (new backend format)
    if (typeof deliverable.content === 'string' && deliverable.content.trim()) {
      // Remove markdown formatting for preview
      const cleanContent = deliverable.content
        .replace(/^#+ /gm, '') // Remove headers
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
        .replace(/\*(.*?)\*/g, '$1') // Remove italic
        .replace(/\n\n+/g, ' ') // Replace multiple newlines
        .trim()
      return cleanContent.substring(0, 200) + (cleanContent.length > 200 ? '...' : '')
    }
    
    // Handle legacy structured content
    if (deliverable.content?.summary) {
      return deliverable.content.summary.substring(0, 150) + '...'
    }
    
    if (deliverable.content?.sections && deliverable.content.sections.length > 0) {
      const firstSection = deliverable.content.sections[0]
      const preview = firstSection.content || firstSection.title || ''
      return preview.substring(0, 150) + '...'
    }
    
    return `${deliverable.title} has been completed and is ready for use.`
  }

  // 🧠 Smart content type detection
  const getDeliverableIcon = () => {
    if (deliverable.type?.includes('website') || deliverable.title.toLowerCase().includes('website')) {
      return '🌐'
    }
    if (deliverable.type?.includes('content') || deliverable.title.toLowerCase().includes('content')) {
      return '📝'
    }
    if (deliverable.type?.includes('strategy') || deliverable.title.toLowerCase().includes('strategy')) {
      return '🎯'
    }
    if (deliverable.type?.includes('analysis') || deliverable.title.toLowerCase().includes('analysis')) {
      return '📊'
    }
    if (deliverable.type?.includes('campaign') || deliverable.title.toLowerCase().includes('campaign')) {
      return '🚀'
    }
    return '📦' // Generic deliverable
  }

  // 📊 Business value indicator
  const getValueIndicator = () => {
    const score = deliverable.businessValueScore || 0
    if (score >= 70) return { color: 'text-green-600', label: 'High Value', icon: '🟢' }
    if (score >= 40) return { color: 'text-blue-600', label: 'Good Value', icon: '🔵' }
    if (score >= 20) return { color: 'text-yellow-600', label: 'Thinking', icon: '🟡' }
    return { color: 'text-gray-600', label: 'Meta', icon: '⚪' }
  }

  const valueIndicator = getValueIndicator()
  const preview = generatePreview()

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm max-w-2xl">
      {/* 🎉 Header with celebration */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-t-lg border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-xl shadow-sm">
                {getDeliverableIcon()}
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-lg">🎉</span>
                <h3 className="text-sm font-medium text-gray-900">
                  Deliverable Ready
                </h3>
                {deliverable.goalDescription && (
                  <span className="text-xs text-gray-500">
                    for {deliverable.goalDescription}
                  </span>
                )}
              </div>
              <h4 className="text-base font-semibold text-gray-900 mt-1">
                {deliverable.title}
              </h4>
            </div>
          </div>
          
          {/* Value indicator */}
          <div className="flex items-center space-x-2">
            <span className={`text-xs font-medium ${valueIndicator.color}`}>
              {valueIndicator.icon} {valueIndicator.label}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* 📋 Content Preview */}
      <div className="p-4">
        <div className="text-sm text-gray-700 leading-relaxed">
          {preview}
        </div>
        
        {!isExpanded && (deliverable.content?.sections || (typeof deliverable.content === 'string' && deliverable.content.trim())) && (
          <button
            onClick={() => setIsExpanded(true)}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
          >
            <span>View full content</span>
            <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* 📄 Expanded Content */}
      {isExpanded && (deliverable.content?.sections || (typeof deliverable.content === 'string' && deliverable.content.trim())) && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <div className="bg-white rounded border p-4 max-h-64 overflow-y-auto">
            {/* Handle direct string content (new backend format) */}
            {typeof deliverable.content === 'string' && deliverable.content.trim() && (
              <div className="prose prose-sm max-w-none">
                <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {deliverable.content}
                </div>
              </div>
            )}
            
            {/* Handle legacy structured content */}
            {deliverable.content?.sections && deliverable.content.sections.map((section: any, index: number) => (
              <div key={index} className="mb-4 last:mb-0">
                {section.title && (
                  <h5 className="font-medium text-gray-900 mb-2">{section.title}</h5>
                )}
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {section.content}
                </div>
              </div>
            ))}
          </div>
          
          {!compact && (
            <button
              onClick={() => setIsExpanded(false)}
              className="mt-3 text-sm text-gray-600 hover:text-gray-800 flex items-center"
            >
              <svg className="mr-1 w-4 h-4 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              <span>Show less</span>
            </button>
          )}
        </div>
      )}

      {/* 🎯 Actions */}
      <DeliverableActionBar 
        deliverable={deliverable}
        compact={true}
      />
      
      {/* 🔄 Auto-send context */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            🤖 Automatically sent when goal completed
          </span>
          <button className="text-xs text-blue-600 hover:text-blue-800 font-medium">
            Send to chat manually
          </button>
        </div>
      </div>
    </div>
  )
}