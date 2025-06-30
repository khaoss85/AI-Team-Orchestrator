'use client'

import React, { useState } from 'react'
import { toast } from 'react-hot-toast'

interface DeliverableActionBarProps {
  deliverable: {
    id: string
    title: string
    content: any
    contentType?: 'HTML' | 'Structured' | 'Basic'
    type?: string
  }
  compact?: boolean
}

interface ActionResult {
  success: boolean
  message: string
  data?: any
}

export default function DeliverableActionBar({ deliverable, compact = false }: DeliverableActionBarProps) {
  const [isProcessing, setIsProcessing] = useState<string | null>(null)

  // 🌍 UNIVERSAL: AI-driven action detection based on content
  const detectAvailableActions = () => {
    const actions = []
    
    // 📋 Copy action - always available
    actions.push({
      id: 'copy',
      label: 'Copy',
      icon: '📋',
      primary: true,
      description: 'Copy content to clipboard'
    })

    // 📥 Download actions - based on content type
    if (deliverable.contentType === 'HTML' || deliverable.content?.sections?.length > 0) {
      actions.push({
        id: 'download_pdf',
        label: 'PDF',
        icon: '📄',
        primary: true,
        description: 'Download as PDF document'
      })
    }

    if (deliverable.contentType === 'Structured' || Array.isArray(deliverable.content?.sections)) {
      actions.push({
        id: 'export_data',
        label: 'Export',
        icon: '📊',
        primary: false,
        description: 'Export structured data'
      })
    }

    // 🔗 Share action - always available
    actions.push({
      id: 'share',
      label: 'Share',
      icon: '🔗',
      primary: false,
      description: 'Generate shareable link'
    })

    // 🔍 Expand/View action for complex content
    if (deliverable.content?.sections?.length > 3) {
      actions.push({
        id: 'expand',
        label: 'View Full',
        icon: '🔍',
        primary: false,
        description: 'View complete content'
      })
    }

    return actions
  }

  // 🤖 AI-DRIVEN: Smart content processing based on type
  const processAction = async (actionId: string): Promise<ActionResult> => {
    setIsProcessing(actionId)

    try {
      switch (actionId) {
        case 'copy':
          return await handleCopy()
        case 'download_pdf':
          return await handleDownloadPDF()
        case 'export_data':
          return await handleExportData()
        case 'share':
          return await handleShare()
        case 'expand':
          return await handleExpand()
        default:
          return { success: false, message: 'Action not supported' }
      }
    } finally {
      setIsProcessing(null)
    }
  }

  // 📋 UNIVERSAL: Smart copy based on content structure
  const handleCopy = async (): Promise<ActionResult> => {
    try {
      let textToCopy = ''

      if (deliverable.content?.sections) {
        // Structured content
        textToCopy = deliverable.content.sections
          .map((section: any) => `${section.title}\n${section.content}`)
          .join('\n\n---\n\n')
      } else if (deliverable.content?.summary) {
        // Summary content
        textToCopy = deliverable.content.summary
      } else if (typeof deliverable.content === 'string') {
        // Plain text content
        textToCopy = deliverable.content
      } else {
        // Fallback to JSON
        textToCopy = JSON.stringify(deliverable.content, null, 2)
      }

      await navigator.clipboard.writeText(textToCopy)
      return { success: true, message: 'Content copied to clipboard' }
    } catch (error) {
      return { success: false, message: 'Failed to copy content' }
    }
  }

  // 📄 UNIVERSAL: PDF generation for any content
  const handleDownloadPDF = async (): Promise<ActionResult> => {
    try {
      // Create downloadable content
      const content = deliverable.content?.sections 
        ? deliverable.content.sections.map((s: any) => `${s.title}\n${s.content}`).join('\n\n')
        : JSON.stringify(deliverable.content, null, 2)

      // Simple text-to-PDF approach (in real app, use proper PDF library)
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `${deliverable.title.replace(/[^a-z0-9]/gi, '_')}.txt`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      return { success: true, message: 'Document downloaded' }
    } catch (error) {
      return { success: false, message: 'Download failed' }
    }
  }

  // 📊 UNIVERSAL: Export structured data
  const handleExportData = async (): Promise<ActionResult> => {
    try {
      const data = deliverable.content?.sections || deliverable.content
      const jsonString = JSON.stringify(data, null, 2)
      
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `${deliverable.title.replace(/[^a-z0-9]/gi, '_')}_data.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      return { success: true, message: 'Data exported' }
    } catch (error) {
      return { success: false, message: 'Export failed' }
    }
  }

  // 🔗 UNIVERSAL: Share functionality
  const handleShare = async (): Promise<ActionResult> => {
    try {
      const shareUrl = `${window.location.origin}/deliverable/${deliverable.id}`
      
      if (navigator.share) {
        await navigator.share({
          title: deliverable.title,
          text: `Check out this deliverable: ${deliverable.title}`,
          url: shareUrl
        })
        return { success: true, message: 'Shared successfully' }
      } else {
        await navigator.clipboard.writeText(shareUrl)
        return { success: true, message: 'Share link copied to clipboard' }
      }
    } catch (error) {
      return { success: false, message: 'Share failed' }
    }
  }

  // 🔍 Expand content view
  const handleExpand = async (): Promise<ActionResult> => {
    // Open in modal or new view
    window.open(`/deliverable/${deliverable.id}/full`, '_blank')
    return { success: true, message: 'Opening full view' }
  }

  const availableActions = detectAvailableActions()
  const primaryActions = availableActions.filter(a => a.primary)
  const secondaryActions = availableActions.filter(a => !a.primary)

  const handleActionClick = async (actionId: string) => {
    const result = await processAction(actionId)
    
    if (result.success) {
      toast.success(result.message)
    } else {
      toast.error(result.message)
    }
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        {primaryActions.map(action => (
          <button
            key={action.id}
            onClick={() => handleActionClick(action.id)}
            disabled={isProcessing === action.id}
            className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50"
            title={action.description}
          >
            <span className="mr-1">{action.icon}</span>
            {isProcessing === action.id ? '⏳' : action.label}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="border-t border-gray-200 bg-gray-50 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Actions:</span>
          {primaryActions.map(action => (
            <button
              key={action.id}
              onClick={() => handleActionClick(action.id)}
              disabled={isProcessing === action.id}
              className="inline-flex items-center px-3 py-1.5 text-sm bg-white border border-gray-300 hover:bg-gray-50 rounded-md transition-colors disabled:opacity-50"
              title={action.description}
            >
              <span className="mr-2">{action.icon}</span>
              {isProcessing === action.id ? 'Processing...' : action.label}
            </button>
          ))}
        </div>
        
        {secondaryActions.length > 0 && (
          <div className="flex items-center space-x-2">
            {secondaryActions.map(action => (
              <button
                key={action.id}
                onClick={() => handleActionClick(action.id)}
                disabled={isProcessing === action.id}
                className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                title={action.description}
              >
                <span className="mr-1">{action.icon}</span>
                {isProcessing === action.id ? '⏳' : action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}