'use client'
import React from 'react'
import type { Workspace, AssetCompletionStats } from '@/types'

interface Props {
  workspace: Workspace
  assetStats: AssetCompletionStats
  finalDeliverables: number
}

const gradients = [
  'from-indigo-500 to-purple-600',
  'from-teal-500 to-emerald-600',
  'from-pink-500 to-rose-600',
  'from-amber-500 to-orange-600',
  'from-sky-500 to-blue-600'
]

const ActionableHeroSection: React.FC<Props> = ({ workspace, assetStats, finalDeliverables }) => {
  const gradient = React.useMemo(() => {
    const idx = workspace.id
      ? workspace.id.charCodeAt(0) % gradients.length
      : 0
    return gradients[idx]
  }, [workspace.id])

  return (
    <div className={`rounded-lg shadow-lg p-8 text-white bg-gradient-to-br ${gradient}`}>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1">{workspace.name}</h1>
          {workspace.goal && <p className="opacity-90">{workspace.goal}</p>}
        </div>
        <div className="text-sm text-right space-y-1">
          <div>
            <span className="font-medium">Asset:</span> {assetStats.completedAssets}/{assetStats.totalAssets}
          </div>
          <div>
            <span className="font-medium">Deliverable finali:</span> {finalDeliverables}
          </div>
        </div>
      </div>
      <div className="mt-4">
        <div className="w-full bg-white bg-opacity-30 h-2 rounded-full">
          <div
            className="bg-white h-2 rounded-full"
            style={{ width: `${assetStats.completionRate}%` }}
          />
        </div>
        <div className="text-xs mt-1">Progresso asset: {Math.round(assetStats.completionRate)}%</div>
      </div>
      <div className="mt-6 flex gap-3 flex-wrap">
        <a
          href={`/projects/${workspace.id}/deliverables`}
          className="px-4 py-2 bg-black/40 rounded-md text-sm hover:bg-black/60"
        >
          Download &amp; Use Now
        </a>
        <a
          href={`/projects/${workspace.id}/team`}
          className="px-4 py-2 bg-black/40 rounded-md text-sm hover:bg-black/60"
        >
          Talk to AI Team
        </a>
      </div>
    </div>
  )
}

export default ActionableHeroSection
