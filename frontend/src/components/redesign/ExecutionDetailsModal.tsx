'use client'
import React from 'react'
import type { ProjectOutputExtended } from '@/types'

interface Props {
  output: ProjectOutputExtended
  onClose: () => void
}

const ExecutionDetailsModal: React.FC<Props> = ({ output, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Execution Details</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div className="space-y-2 text-sm">
          {output.cost_estimated !== undefined && (
            <div className="flex justify-between">
              <span>Costo stimato:</span>
              <span className="font-medium">${output.cost_estimated.toFixed(6)}</span>
            </div>
          )}
          {output.execution_time_seconds !== undefined && (
            <div className="flex justify-between">
              <span>Tempo:</span>
              <span className="font-medium">{output.execution_time_seconds.toFixed(2)}s</span>
            </div>
          )}
          {output.tokens_used && (
            <div className="flex justify-between">
              <span>Token:</span>
              <span className="font-medium">{output.tokens_used.input + output.tokens_used.output}</span>
            </div>
          )}
          {output.model_used && (
            <div className="flex justify-between">
              <span>Modello:</span>
              <span className="font-medium">{output.model_used}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ExecutionDetailsModal
