'use client'
import React, { useEffect, useState } from 'react'
import { api } from '@/utils/api'
import type { ProjectOutputExtended } from '@/types'
import TaskResultDetails from '@/components/TaskResultDetails'

interface Props {
  output: ProjectOutputExtended
  workspaceId: string
  onClose: () => void
}

const DetailsDrillDown: React.FC<Props> = ({ output, workspaceId, onClose }) => {
  const [details, setDetails] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true)
        const data = await api.monitoring.getTaskResult(output.task_id)
        setDetails(data)
        setError(null)
      } catch (e: any) {
        setError(e.message || 'Errore nel caricamento dei dettagli')
      } finally {
        setLoading(false)
      }
    }
    fetchDetails()
  }, [output.task_id])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{output.title || output.task_name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        {loading ? (
          <div className="text-center py-10">Caricamento...</div>
        ) : error ? (
          <div className="text-red-600 text-center">{error}</div>
        ) : (
          <>
            <TaskResultDetails result={details} />
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={async () => {
                  try {
                    await api.monitoring.submitDeliverableFeedback(workspaceId, {
                      feedback_type: 'request_changes',
                      message: '',
                      priority: 'medium',
                      specific_tasks: [output.task_id]
                    })
                    alert('Feedback inviato')
                  } catch (e) {
                    console.error(e)
                    alert('Errore nell\'invio del feedback')
                  }
                }}
                className="px-4 py-2 bg-orange-600 text-white rounded-md text-sm"
              >
                Request Modifications
              </button>
              <button
                onClick={() => {
                  const dataStr = 'data:application/json;charset=utf-8,' +
                    encodeURIComponent(JSON.stringify(details, null, 2))
                  const link = document.createElement('a')
                  link.href = dataStr
                  link.download = `asset_${output.task_id}.json`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-md text-sm"
              >
                Download Full Asset
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default DetailsDrillDown
