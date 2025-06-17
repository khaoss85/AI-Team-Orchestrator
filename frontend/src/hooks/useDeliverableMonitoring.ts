import { useState, useEffect, useCallback } from 'react'

interface DeliverableStatus {
  id: string
  name: string
  created_at: string
  updated_at: string
  generation_status: string
  concrete_assets: any[]
  quality_metrics: any
  business_impact: any
}

interface DeliverableMonitoring {
  deliverables: DeliverableStatus[]
  isLoading: boolean
  error: string | null
  lastUpdate: string | null
  hasChanges: boolean
  refresh: () => Promise<void>
}

export const useDeliverableMonitoring = (workspaceId: string, refreshInterval: number = 30000) => {
  const [monitoring, setMonitoring] = useState<DeliverableMonitoring>({
    deliverables: [],
    isLoading: true,
    error: null,
    lastUpdate: null,
    hasChanges: false,
    refresh: async () => {}
  })

  const [previousDeliverables, setPreviousDeliverables] = useState<string>('')

  const fetchDeliverables = useCallback(async () => {
    if (!workspaceId) return

    try {
      console.log('🔍 [DeliverableMonitoring] Fetching deliverables for workspace:', workspaceId)
      
      const response = await fetch(`http://localhost:8000/deliverables/workspace/${workspaceId}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const deliverables = await response.json()
      console.log('📦 [DeliverableMonitoring] Fetched deliverables:', deliverables)

      // Check for changes
      const currentDeliverablesString = JSON.stringify(deliverables)
      const hasChanges = previousDeliverables !== '' && previousDeliverables !== currentDeliverablesString
      
      if (hasChanges) {
        console.log('🔄 [DeliverableMonitoring] Deliverables have changed!')
        
        // Show notification for changes
        const changeDiv = document.createElement('div')
        changeDiv.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50'
        changeDiv.innerHTML = `
          <div class="flex items-center space-x-2">
            <span>📦</span>
            <span>Deliverables updated! Check the latest changes.</span>
          </div>
        `
        document.body.appendChild(changeDiv)
        setTimeout(() => {
          try {
            document.body.removeChild(changeDiv)
          } catch (e) {
            // Element might already be removed
          }
        }, 5000)
      }

      setPreviousDeliverables(currentDeliverablesString)

      setMonitoring(prev => ({
        ...prev,
        deliverables,
        isLoading: false,
        error: null,
        lastUpdate: new Date().toISOString(),
        hasChanges
      }))

    } catch (error) {
      console.error('❌ [DeliverableMonitoring] Error fetching deliverables:', error)
      setMonitoring(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch deliverables'
      }))
    }
  }, [workspaceId, previousDeliverables])

  const refresh = useCallback(async () => {
    setMonitoring(prev => ({ ...prev, isLoading: true }))
    await fetchDeliverables()
  }, [fetchDeliverables])

  useEffect(() => {
    setMonitoring(prev => ({ ...prev, refresh }))
  }, [refresh])

  useEffect(() => {
    if (!workspaceId) return

    // Initial fetch
    fetchDeliverables()

    // Set up polling
    const interval = setInterval(fetchDeliverables, refreshInterval)

    return () => clearInterval(interval)
  }, [workspaceId, fetchDeliverables, refreshInterval])

  return monitoring
}