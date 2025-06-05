'use client'
import React from 'react'
import type { ProjectOutputExtended } from '@/types'

import { api } from '@/utils/api'

interface Props {
  output: ProjectOutputExtended
  workspaceId: string
  onViewDetails: () => void
  onViewExecution?: () => void
  onViewRationale?: () => void
}

const getCategoryColors = (category?: string) => {
  switch (category) {
    case 'research':
      return 'from-blue-600 via-indigo-600 to-purple-600'
    case 'planning':
      return 'from-violet-600 via-purple-600 to-pink-600'
    case 'execution':
      return 'from-emerald-500 via-green-500 to-teal-500'
    case 'analysis':
      return 'from-amber-500 via-orange-500 to-red-500'
    case 'review':
      return 'from-rose-500 via-pink-500 to-purple-500'
    default:
      return 'from-slate-600 via-gray-600 to-zinc-600'
  }
}

const DeliverableCard: React.FC<Props> = ({
  output,
  workspaceId,
  onViewDetails,
  onViewExecution,
  onViewRationale
}) => {
  const title = output.title || output.task_name
  const summary = output.summary || output.output || ''

  const firstAsset = React.useMemo(() => {
    if (output.actionable_assets && Object.keys(output.actionable_assets).length > 0) {
      const key = Object.keys(output.actionable_assets)[0]
      return output.actionable_assets[key]
    }

    if (
      output.content?.actionableAssets &&
      Object.keys(output.content.actionableAssets).length > 0
    ) {
      const key = Object.keys(output.content.actionableAssets)[0]
      return output.content.actionableAssets[key]
    }

    if (output.result?.actionable_assets && Object.keys(output.result.actionable_assets).length > 0) {
      const key = Object.keys(output.result.actionable_assets)[0]
      return output.result.actionable_assets[key]
    }

    return null
  }, [output])

  // Generate business-friendly preview from asset data
  const getBusinessPreview = () => {
    if (!firstAsset?.asset_data) return null

    const data = firstAsset.asset_data
    
    // Content Calendar Preview
    if (Array.isArray(data.posts)) {
      return {
        icon: "📅",
        title: "Content Calendar Ready",
        metrics: `${data.posts.length} posts planned`,
        value: `€${(data.posts.length * 150).toLocaleString()}`,
        details: data.posts.slice(0, 2).map(p => p.caption?.slice(0, 40) + "...").join(", ")
      }
    }

    // Contact Database Preview
    if (Array.isArray(data.contacts)) {
      return {
        icon: "📊",
        title: "Lead Database Ready",
        metrics: `${data.contacts.length} qualified leads`,
        value: `€${(data.contacts.length * 50).toLocaleString()}`,
        details: `${data.contacts.filter(c => c.qualification_score > 70).length} high-value prospects`
      }
    }

    // Strategy Document Preview
    if (data.strategy || data.recommendations) {
      return {
        icon: "🎯",
        title: "Strategy Document",
        metrics: "Business plan ready",
        value: "€5,000",
        details: "Implementation roadmap included"
      }
    }

    // Analysis Report Preview
    if (data.insights || data.analysis) {
      return {
        icon: "📈",
        title: "Analysis Report",
        metrics: "Data insights ready",
        value: "€3,500", 
        details: "Actionable recommendations included"
      }
    }

    // Generic asset preview
    const keys = Object.keys(data)
    return {
      icon: "📄",
      title: "Asset Ready",
      metrics: `${keys.length} data points`,
      value: "€2,500",
      details: "Download to explore"
    }
  }

  const businessPreview = getBusinessPreview()

  const handleDownload = () => {
    if (!firstAsset) return
    const dataStr =
      'data:application/json;charset=utf-8,' +
      encodeURIComponent(JSON.stringify(firstAsset.asset_data, null, 2))
    const link = document.createElement('a')
    link.href = dataStr
    link.download = `${firstAsset.asset_name || 'asset'}_${output.task_id}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleRequestChanges = async () => {
    try {
      await api.monitoring.submitDeliverableFeedback(workspaceId, {
        feedback_type: 'request_changes',
        message: '',
        priority: 'medium',
        specific_tasks: [output.task_id],
      })
      alert('Feedback inviato')
    } catch (e) {
      console.error(e)
      alert('Errore invio feedback')
    }
  }

  const gradient = getCategoryColors(output.category)

  return (
    <div
      className={`relative bg-gradient-to-br ${gradient} text-white rounded-xl p-6 shadow-lg hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 overflow-hidden group`}
    >
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-10 group-hover:opacity-20 transition-opacity">
        <div className="absolute top-0 right-0 w-20 h-20 bg-white rounded-full -translate-y-10 translate-x-10"></div>
        <div className="absolute bottom-0 left-0 w-16 h-16 bg-white rounded-full translate-y-8 -translate-x-8"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header with business preview */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              {businessPreview && (
                <span className="text-2xl mr-2">{businessPreview.icon}</span>
              )}
              <h3 className="font-bold text-lg leading-tight">{title}</h3>
            </div>
            {businessPreview && (
              <div className="space-y-1">
                <div className="text-sm font-medium opacity-95">{businessPreview.title}</div>
                <div className="text-xs opacity-80">{businessPreview.details}</div>
              </div>
            )}
          </div>
          
          {/* Value indicator */}
          {businessPreview && (
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-2 text-right">
              <div className="text-xs opacity-80">Value</div>
              <div className="font-bold text-lg">{businessPreview.value}</div>
            </div>
          )}
        </div>

        {/* Business metrics showcase */}
        {businessPreview && (
          <div className="mb-4 p-3 bg-white bg-opacity-15 backdrop-blur-sm rounded-lg border border-white/20">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{businessPreview.metrics}</span>
              {firstAsset?.ready_to_use && (
                <span className="px-2 py-1 bg-green-400 text-green-900 text-xs font-bold rounded-full">
                  ✅ READY
                </span>
              )}
            </div>
          </div>
        )}

        {/* Quality indicators */}
        {firstAsset && (
          <div className="mb-4 flex gap-2">
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              firstAsset.validation_score >= 0.8
                ? 'bg-green-100 text-green-800'
                : firstAsset.validation_score >= 0.6
                  ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {Math.round(firstAsset.validation_score * 100)}% validated
            </div>
            {firstAsset.automation_ready && (
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                🤖 Auto-ready
              </div>
            )}
          </div>
        )}

        {/* Action buttons - streamlined and prominent */}
        <div className="space-y-2">
          {/* Primary action */}
          {firstAsset && (
            <button
              className="w-full bg-white text-black font-semibold py-3 px-4 rounded-lg hover:bg-gray-100 transform hover:scale-105 transition-all duration-200 flex items-center justify-center shadow-lg"
              onClick={handleDownload}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download & Use Now
            </button>
          )}
          
          {/* Secondary actions */}
          <div className="grid grid-cols-2 gap-2">
            <button
              className="bg-black/30 backdrop-blur-sm border border-white/20 text-white font-medium py-2 px-3 rounded-lg hover:bg-black/50 transition-all duration-200 text-sm"
              onClick={onViewDetails}
            >
              View Details
            </button>
            <button
              className="bg-black/30 backdrop-blur-sm border border-white/20 text-white font-medium py-2 px-3 rounded-lg hover:bg-black/50 transition-all duration-200 text-sm"
              onClick={() => (window.location.href = `/projects/${workspaceId}/team`)}
            >
              Talk to AI Team
            </button>
          </div>
          
          {/* Drill-down options */}
          <details className="group/details">
            <summary className="cursor-pointer text-xs opacity-75 hover:opacity-100 transition-opacity list-none flex items-center justify-center">
              <span>More options</span>
              <svg className="w-4 h-4 ml-1 group-open/details:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="mt-2 grid grid-cols-2 gap-1">
              {onViewExecution && (
                <button
                  className="bg-teal-600/80 text-white text-xs py-1.5 px-2 rounded hover:bg-teal-600 transition-colors"
                  onClick={onViewExecution}
                >
                  Execution
                </button>
              )}
              {onViewRationale && (
                <button
                  className="bg-sky-600/80 text-white text-xs py-1.5 px-2 rounded hover:bg-sky-600 transition-colors"
                  onClick={onViewRationale}
                >
                  Rationale
                </button>
              )}
              <button
                className="bg-orange-500/80 text-white text-xs py-1.5 px-2 rounded hover:bg-orange-500 transition-colors col-span-2"
                onClick={handleRequestChanges}
              >
                Request Changes
              </button>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}

export default DeliverableCard
