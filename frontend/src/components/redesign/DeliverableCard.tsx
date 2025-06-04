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
      return 'from-blue-500 to-blue-600'
    case 'planning':
      return 'from-purple-500 to-purple-600'
    case 'execution':
      return 'from-green-500 to-green-600'
    case 'analysis':
      return 'from-orange-500 to-orange-600'
    case 'review':
      return 'from-red-500 to-red-600'
    default:
      return 'from-gray-500 to-gray-600'
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
      className={`bg-gradient-to-br ${gradient} text-white rounded-lg p-4 shadow-sm flex flex-col justify-between hover:shadow-md transition`}
    >
      <div>
        <h3 className="font-semibold text-white text-sm mb-1 truncate">{title}</h3>
        {summary && (
          <p className="text-sm opacity-90 line-clamp-3 overflow-hidden">
            {summary.length > 160 ? summary.slice(0, 160) + '…' : summary}
          </p>
        )}
        {firstAsset && (
          <div className="mt-2 flex items-center text-xs gap-2">
            <span
              className={`px-2 py-1 rounded-full font-medium ${
                firstAsset.validation_score >= 0.8
                  ? 'bg-green-100 text-green-800'
                  : firstAsset.validation_score >= 0.6
                    ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {Math.round(firstAsset.validation_score * 100)}% valido
            </span>
            <span
              className={`px-2 py-1 rounded-full font-medium ${
                firstAsset.ready_to_use
                  ? 'bg-green-100 text-green-800'
                  : 'bg-orange-100 text-orange-800'
              }`}
            >
              {firstAsset.ready_to_use ? 'Ready' : 'Needs Work'}
            </span>
          </div>
        )}
        {output.metrics && (
          <div className="mt-2 flex flex-wrap gap-1 text-xs">
            {Object.entries(output.metrics).map(([k, v]) => (
              <span key={k} className="bg-white bg-opacity-20 px-2 py-1 rounded-full">
                {k}: {String(v)}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="mt-3 flex gap-2 flex-wrap">
        <button
          className="flex-1 bg-indigo-600 text-white text-sm px-3 py-1.5 rounded-md hover:bg-indigo-700"
          onClick={onViewDetails}
        >
          Dettagli
        </button>
        {firstAsset && (
          <button
            className="flex-1 bg-green-600 text-white text-sm px-3 py-1.5 rounded-md hover:bg-green-700"
            onClick={handleDownload}
          >
            Download &amp; Use Now
          </button>
        )}
        {onViewExecution && (
          <button
            className="flex-1 bg-teal-600 text-white text-sm px-3 py-1.5 rounded-md hover:bg-teal-700"
            onClick={onViewExecution}
          >
            Execution
          </button>
        )}
        {onViewRationale && (
          <button
            className="flex-1 bg-sky-600 text-white text-sm px-3 py-1.5 rounded-md hover:bg-sky-700"
            onClick={onViewRationale}
          >
            Rationale
          </button>
        )}
        <button
          className="flex-1 bg-orange-500 text-white text-sm px-3 py-1.5 rounded-md hover:bg-orange-600"
          onClick={handleRequestChanges}
        >
          Request Changes
        </button>
        <button
          className="flex-1 bg-black/40 text-white text-sm px-3 py-1.5 rounded-md hover:bg-black/60"
          onClick={() => (window.location.href = `/projects/${workspaceId}/team`)}
        >
          Talk to AI Team
        </button>
      </div>
    </div>
  )
}

export default DeliverableCard
