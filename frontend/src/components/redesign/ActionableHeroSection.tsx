'use client'
import React from 'react'
import type { Workspace, AssetCompletionStats } from '@/types'

interface Props {
  workspace: Workspace
  assetStats: AssetCompletionStats
  finalDeliverables: number
}

const ActionableHeroSection: React.FC<Props> = ({ workspace, assetStats, finalDeliverables }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1">{workspace.name}</h1>
          {workspace.goal && <p className="text-gray-600">{workspace.goal}</p>}
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
        <div className="w-full bg-gray-200 h-2 rounded-full">
          <div
            className="bg-indigo-600 h-2 rounded-full"
            style={{ width: `${assetStats.completionRate}%` }}
          />
        </div>
        <div className="text-xs text-gray-600 mt-1">Progresso asset: {Math.round(assetStats.completionRate)}%</div>
      </div>
    </div>
  )
}

export default ActionableHeroSection
