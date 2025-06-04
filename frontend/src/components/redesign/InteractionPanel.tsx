'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace } from '@/types'

interface Props {
  workspace: Workspace
  onWorkspaceUpdate: (w: Workspace) => void
}

const InteractionPanel: React.FC<Props> = ({ workspace, onWorkspaceUpdate }) => {
  const [starting, setStarting] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleStart = async () => {
    try {
      setStarting(true)
      await api.monitoring.startTeam(workspace.id)
      const updated = await api.workspaces.get(workspace.id)
      onWorkspaceUpdate(updated)
    } catch (e) {
      console.error(e)
    } finally {
      setStarting(false)
    }
  }

  const handleDelete = async () => {
    const confirmDelete = window.confirm('Sei sicuro di voler eliminare il progetto?')
    if (!confirmDelete) return
    try {
      setDeleting(true)
      await api.workspaces.delete(workspace.id)
      window.location.href = '/projects'
    } catch (e) {
      console.error(e)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 space-y-4">
      {workspace.status === 'created' && (
        <button onClick={handleStart} disabled={starting} className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 disabled:opacity-50">
          {starting ? 'Avvio…' : '🚀 Avvia Team'}
        </button>
      )}
      <div className="flex gap-3 text-sm">
        <Link href={`/projects/${workspace.id}/deliverables`} className="text-indigo-600 hover:underline">Deliverable</Link>
        <Link href={`/projects/${workspace.id}/assets`} className="text-indigo-600 hover:underline">Asset</Link>
      </div>
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 disabled:opacity-50"
      >
        {deleting ? 'Eliminazione…' : '🗑️ Elimina Progetto'}
      </button>
    </div>
  )
}

export default InteractionPanel
