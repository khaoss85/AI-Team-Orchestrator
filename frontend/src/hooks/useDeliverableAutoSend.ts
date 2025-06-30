import { useCallback, useEffect, useState } from 'react'

interface Deliverable {
  id: string
  title: string
  content: any
  businessValueScore?: number
  goalDescription?: string
  created_at: string
}

interface AutoSendConfig {
  enabled: boolean
  businessValueThreshold: number // Only send deliverables above this score
  cooldownMinutes: number // Prevent spam
}

const DEFAULT_CONFIG: AutoSendConfig = {
  enabled: true,
  businessValueThreshold: 40, // Only high-value deliverables
  cooldownMinutes: 5
}

export default function useDeliverableAutoSend(
  workspaceId: string,
  onDeliverableSent?: (deliverable: Deliverable) => void
) {
  const [config, setConfig] = useState<AutoSendConfig>(DEFAULT_CONFIG)
  const [lastSentTimes, setLastSentTimes] = useState<Record<string, number>>({})
  const [pendingDeliverables, setPendingDeliverables] = useState<Deliverable[]>([])

  // 🤖 AI-DRIVEN: Smart deliverable qualification
  const qualifiesForAutoSend = useCallback((deliverable: Deliverable): boolean => {
    if (!config.enabled) return false

    // 📊 Business value threshold
    const businessScore = deliverable.businessValueScore || 0
    if (businessScore < config.businessValueThreshold) {
      console.log(`📊 Deliverable "${deliverable.title}" below threshold: ${businessScore} < ${config.businessValueThreshold}`)
      return false
    }

    // ⏰ Cooldown check
    const goalKey = deliverable.goalDescription || 'default'
    const lastSent = lastSentTimes[goalKey] || 0
    const cooldownMs = config.cooldownMinutes * 60 * 1000
    const now = Date.now()

    if (now - lastSent < cooldownMs) {
      console.log(`⏰ Deliverable cooldown active for goal: ${goalKey}`)
      return false
    }

    // ✅ Content quality check
    if (!deliverable.content || 
        (typeof deliverable.content === 'object' && Object.keys(deliverable.content).length === 0)) {
      console.log(`📄 Deliverable "${deliverable.title}" has no substantial content`)
      return false
    }

    return true
  }, [config, lastSentTimes])

  // 🚀 Send deliverable to chat
  const sendDeliverableToChat = useCallback(async (deliverable: Deliverable): Promise<boolean> => {
    try {
      // 📨 Call API to add deliverable message to chat
      const response = await fetch(`/api/workspaces/${workspaceId}/chat/deliverable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deliverable_id: deliverable.id,
          deliverable_title: deliverable.title,
          deliverable_content: deliverable.content,
          goal_description: deliverable.goalDescription,
          business_value_score: deliverable.businessValueScore,
          auto_sent: true
        })
      })

      if (response.ok) {
        // Update cooldown
        const goalKey = deliverable.goalDescription || 'default'
        setLastSentTimes(prev => ({
          ...prev,
          [goalKey]: Date.now()
        }))

        // Notify callback
        onDeliverableSent?.(deliverable)
        
        console.log(`✅ Auto-sent deliverable: ${deliverable.title}`)
        return true
      } else {
        console.error(`❌ Failed to send deliverable: ${response.statusText}`)
        return false
      }
    } catch (error) {
      console.error(`❌ Error sending deliverable:`, error)
      return false
    }
  }, [workspaceId, onDeliverableSent])

  // 🔄 Process pending deliverables
  const processPendingDeliverables = useCallback(async () => {
    const qualified = pendingDeliverables.filter(qualifiesForAutoSend)
    
    if (qualified.length === 0) return

    console.log(`🤖 Processing ${qualified.length} qualified deliverables for auto-send`)

    for (const deliverable of qualified) {
      const sent = await sendDeliverableToChat(deliverable)
      if (sent) {
        // Remove from pending
        setPendingDeliverables(prev => 
          prev.filter(d => d.id !== deliverable.id)
        )
      }
    }
  }, [pendingDeliverables, qualifiesForAutoSend, sendDeliverableToChat])

  // ⏰ Auto-process every 30 seconds
  useEffect(() => {
    const interval = setInterval(processPendingDeliverables, 30000)
    return () => clearInterval(interval)
  }, [processPendingDeliverables])

  // 📥 Add deliverable to queue
  const queueDeliverable = useCallback((deliverable: Deliverable) => {
    setPendingDeliverables(prev => {
      // Prevent duplicates
      if (prev.some(d => d.id === deliverable.id)) return prev
      
      console.log(`📥 Queued deliverable for auto-send: ${deliverable.title}`)
      return [...prev, deliverable]
    })
  }, [])

  // 🎯 Manual send (bypass cooldown and threshold)
  const manualSendDeliverable = useCallback(async (deliverable: Deliverable): Promise<boolean> => {
    return await sendDeliverableToChat(deliverable)
  }, [sendDeliverableToChat])

  // 🛠️ Configuration management
  const updateConfig = useCallback((newConfig: Partial<AutoSendConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }))
  }, [])

  return {
    // State
    config,
    pendingCount: pendingDeliverables.length,
    
    // Actions
    queueDeliverable,
    manualSendDeliverable,
    updateConfig,
    
    // Utils
    qualifiesForAutoSend
  }
}