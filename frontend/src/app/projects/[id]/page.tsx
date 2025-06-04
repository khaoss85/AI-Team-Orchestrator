'use client'

import React, { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { api } from '@/utils/api'
import type { Workspace, ProjectOutputExtended } from '@/types'
import { useAssetManagement } from '@/hooks/useAssetManagement'
import ActionableHeroSection from '@/components/redesign/ActionableHeroSection'
import MissionControlSection from '@/components/redesign/MissionControlSection'
import DeliverableCard from '@/components/redesign/DeliverableCard'
import DetailsDrillDown from '@/components/redesign/DetailsDrillDown'
import InteractionPanel from '@/components/redesign/InteractionPanel'

interface Props {
  params: Promise<{ id: string }>
}

export default function ModernProjectPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise)
  const id = params.id

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const {
    finalDeliverables,
    getAssetCompletionStats,
    loading: assetsLoading,
    error: assetError
  } = useAssetManagement(id)

  const [selectedOutput, setSelectedOutput] = useState<ProjectOutputExtended | null>(null)

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoading(true)
        const data = await api.workspaces.get(id)
        setWorkspace(data)
        setError(null)
      } catch (e: any) {
        setError(e.message || 'Impossibile caricare il progetto')
      } finally {
        setLoading(false)
      }
    }

    fetchWorkspace()
  }, [id])

  if (loading || assetsLoading) {
    return (
      <div className="container mx-auto py-20 text-center">Caricamento progetto...</div>
    )
  }

  if (error || assetError || !workspace) {
    return (
      <div className="container mx-auto py-20 text-center text-red-600">
        {error || assetError || 'Progetto non trovato'}
      </div>
    )
  }

  const assetStats = getAssetCompletionStats()

  return (
    <div className="container mx-auto space-y-6">
      <Link href="/projects" className="text-indigo-600 hover:underline text-sm">← Progetti</Link>
      <ActionableHeroSection workspace={workspace} assetStats={assetStats} finalDeliverables={finalDeliverables.length} />
      <MissionControlSection workspace={workspace} />
      <InteractionPanel workspace={workspace} onWorkspaceUpdate={setWorkspace} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {finalDeliverables.map(output => (
          <DeliverableCard key={output.task_id} output={output} onViewDetails={() => setSelectedOutput(output)} />
        ))}
      </div>

      {selectedOutput && (
        <DetailsDrillDown output={selectedOutput} onClose={() => setSelectedOutput(null)} />
      )}
    </div>
  )
}
