'use client'
import React from 'react'
import type { ProjectOutputExtended } from '@/types'

interface Props {
  output: ProjectOutputExtended
  onViewDetails: () => void
}

const DeliverableCard: React.FC<Props> = ({ output, onViewDetails }) => {
  const title = output.title || output.task_name
  const summary = output.summary || output.output || ''
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm flex flex-col justify-between hover:shadow-md transition">
      <div>
        <h3 className="font-semibold text-gray-800 text-sm mb-1 truncate">{title}</h3>
        {summary && (
          <p className="text-sm text-gray-600 line-clamp-3 overflow-hidden">{summary.length > 160 ? summary.slice(0,160)+'…' : summary}</p>
        )}
      </div>
      <button className="mt-3 text-indigo-600 text-sm hover:underline self-start" onClick={onViewDetails}>Dettagli</button>
    </div>
  )
}

export default DeliverableCard
