'use client'
import React from 'react'

interface Props {
  rationale: string
  onClose: () => void
}

const RationaleModal: React.FC<Props> = ({ rationale, onClose }) => (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-lg max-w-md w-full p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Rationale</h2>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
      </div>
      <pre className="whitespace-pre-wrap text-sm">{rationale || 'Nessuna rationale disponibile'}</pre>
    </div>
  </div>
)

export default RationaleModal
