import { useState, useEffect, useCallback } from 'react'

interface FirstVisitState {
  shouldShowWelcome: boolean
  isFirstVisit: boolean
  hasShownWelcome: boolean
}

const STORAGE_KEY_PREFIX = 'ai-orchestrator-first-visit-'

export default function useFirstVisitWelcome(workspaceId: string) {
  const [firstVisitState, setFirstVisitState] = useState<FirstVisitState>({
    shouldShowWelcome: false,
    isFirstVisit: false,
    hasShownWelcome: false
  })

  const storageKey = `${STORAGE_KEY_PREFIX}${workspaceId}`

  // 🔍 Check if this is the first visit to conversation after configure
  const checkFirstVisit = useCallback(async () => {
    try {
      // Check localStorage for previous visits
      const storedData = localStorage.getItem(storageKey)
      const visitData = storedData ? JSON.parse(storedData) : null

      // For simplicity, show welcome for any recent workspace visit
      // The workspace creation check will be done by WelcomeRecapMessage
      const isFirstVisit = !visitData?.hasVisitedConversation
      const shouldShow = isFirstVisit

      setFirstVisitState({
        shouldShowWelcome: shouldShow,
        isFirstVisit,
        hasShownWelcome: visitData?.hasShownWelcome || false
      })

      // Mark conversation as visited
      if (isFirstVisit) {
        const newVisitData = {
          hasVisitedConversation: true,
          hasShownWelcome: false,
          firstVisitDate: new Date().toISOString()
        }
        localStorage.setItem(storageKey, JSON.stringify(newVisitData))
      }

    } catch (error) {
      console.error('Error checking first visit status:', error)
    }
  }, [workspaceId, storageKey])

  // 🎯 Mark welcome as shown and dismissed
  const markWelcomeShown = useCallback(() => {
    try {
      const storedData = localStorage.getItem(storageKey)
      const visitData = storedData ? JSON.parse(storedData) : {}
      
      const updatedData = {
        ...visitData,
        hasShownWelcome: true,
        welcomeShownDate: new Date().toISOString()
      }
      
      localStorage.setItem(storageKey, JSON.stringify(updatedData))
      
      setFirstVisitState(prev => ({
        ...prev,
        shouldShowWelcome: false,
        hasShownWelcome: true
      }))
    } catch (error) {
      console.error('Error marking welcome as shown:', error)
    }
  }, [storageKey])

  // 🔄 Reset welcome state (for testing or manual trigger)
  const resetWelcomeState = useCallback(() => {
    localStorage.removeItem(storageKey)
    setFirstVisitState({
      shouldShowWelcome: false,
      isFirstVisit: false,
      hasShownWelcome: false
    })
  }, [storageKey])

  // 🚀 Check on mount
  useEffect(() => {
    if (workspaceId) {
      checkFirstVisit()
    }
  }, [workspaceId, checkFirstVisit])

  return {
    ...firstVisitState,
    markWelcomeShown,
    resetWelcomeState,
    checkFirstVisit
  }
}