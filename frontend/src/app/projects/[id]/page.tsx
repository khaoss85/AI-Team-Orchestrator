'use client'

import React, { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/utils/api'
import type { Workspace } from '@/types'

interface Props {
  params: Promise<{ id: string }>
}

export default function SimplifiedProjectPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise)
  const id = params.id
  const router = useRouter()

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Redirect immediately to conversation view
    router.replace(`/projects/${id}/conversation`)
  }, [id, router])

  useEffect(() => {
    fetchWorkspace()
  }, [id])

  const fetchWorkspace = async () => {
    try {
      setLoading(true)
      const data = await api.workspaces.get(id)
      setWorkspace(data)
      setError(null)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Impossibile caricare il progetto'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-20 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-4 text-gray-600">Caricamento progetto...</p>
      </div>
    )
  }

  if (error || !workspace) {
    return (
      <div className="container mx-auto py-20 text-center text-red-600">
        {error || 'Progetto non trovato'}
      </div>
    )
  }

  // 🚀 REDIRECT TO CONVERSATIONAL INTERFACE
  // The new default is the conversational interface
  return (
    <div className="h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-4xl mb-4">🚀</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Redirecting to Conversational Interface
        </h2>
        <p className="text-gray-600 mb-4">
          We&apos;re switching you to the new AI-driven conversational interface...
        </p>
        <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-blue-600 border-r-transparent"></div>
      </div>
    </div>
  )
}