import { useState, useEffect, useCallback, useRef } from 'react'
import { ThemeExtractionResult, MacroTheme } from '@/components/conversational/types'

// 🚀 Cache configuration
const THEME_CACHE_DURATION = 5 * 60 * 1000 // 5 minutes cache
const THEME_CACHE_KEY_PREFIX = 'theme_extraction_'

interface ThemeCacheEntry {
  data: ThemeExtractionResult
  timestamp: number
  workspaceId: string
}

export function useThemeExtraction(workspaceId: string | null) {
  const [themes, setThemes] = useState<MacroTheme[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [extractionResult, setExtractionResult] = useState<ThemeExtractionResult | null>(null)
  const lastFetchTime = useRef<number>(0)
  const fetchInProgress = useRef<boolean>(false)

  const fetchThemes = useCallback(async (forceRefresh: boolean = false) => {
    if (!workspaceId) {
      console.log('No workspace ID, skipping theme extraction')
      return
    }

    // 🚀 Prevent duplicate fetches
    if (fetchInProgress.current) {
      console.log('⏳ Theme fetch already in progress, skipping duplicate request')
      return
    }

    // 🚀 Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cacheKey = `${THEME_CACHE_KEY_PREFIX}${workspaceId}`
      const cachedData = localStorage.getItem(cacheKey)
      
      if (cachedData) {
        try {
          const cache: ThemeCacheEntry = JSON.parse(cachedData)
          const cacheAge = Date.now() - cache.timestamp
          
          if (cache.workspaceId === workspaceId && cacheAge < THEME_CACHE_DURATION) {
            console.log(`✅ Using cached themes (${Math.round(cacheAge / 1000)}s old)`)
            setExtractionResult(cache.data)
            setThemes(cache.data.macro_deliverables)
            lastFetchTime.current = cache.timestamp
            return
          } else {
            console.log('🔄 Cache expired or workspace changed, fetching fresh themes')
          }
        } catch (e) {
          console.warn('⚠️ Failed to parse cached themes, fetching fresh', e)
        }
      }
    }

    // 🚀 Rate limiting - prevent too frequent API calls
    const timeSinceLastFetch = Date.now() - lastFetchTime.current
    if (!forceRefresh && timeSinceLastFetch < 10000) { // 10 seconds minimum between fetches
      console.log(`⏳ Rate limiting: Last fetch was ${Math.round(timeSinceLastFetch / 1000)}s ago`)
      return
    }

    fetchInProgress.current = true
    setLoading(true)
    setError(null)
    
    try {
      // Detect user locale for AI-driven theme extraction
      const userLocale = navigator.language.split('-')[0] || 'en'
      
      console.log('🎯 Fetching themes from API...')
      
      // Call the AI-driven theme extraction API
      const response = await fetch(
        `http://localhost:8000/api/theme/${workspaceId}/macro-deliverables?include_deliverables=true&user_locale=${userLocale}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch themes: ${response.statusText}`)
      }

      const data: ThemeExtractionResult = await response.json()
      
      // Log extraction result for debugging
      console.log('🎯 AI Theme Extraction Result:', {
        themes_count: data.macro_deliverables.length,
        view_type: data.view_type,
        extraction_summary: data.extraction_summary,
        confidence_scores: data.macro_deliverables.map(t => ({
          name: t.name,
          confidence: t.confidence_score
        }))
      })

      // 🚀 Cache the result
      const cacheEntry: ThemeCacheEntry = {
        data,
        timestamp: Date.now(),
        workspaceId
      }
      localStorage.setItem(`${THEME_CACHE_KEY_PREFIX}${workspaceId}`, JSON.stringify(cacheEntry))
      lastFetchTime.current = Date.now()

      setExtractionResult(data)
      setThemes(data.macro_deliverables)
      
      // If no themes were extracted, log a warning
      if (data.macro_deliverables.length === 0) {
        console.warn('⚠️ No themes extracted. Falling back to individual goals view')
      }
      
    } catch (err) {
      console.error('❌ Theme extraction failed:', err)
      setError(err instanceof Error ? err.message : 'Failed to extract themes')
      
      // Set empty themes on error to fall back to regular goal view
      setThemes([])
    } finally {
      setLoading(false)
      fetchInProgress.current = false
    }
  }, [workspaceId])

  // Fetch themes when workspace changes
  useEffect(() => {
    if (workspaceId) {
      fetchThemes()
    }
  }, [workspaceId, fetchThemes])

  // Function to get theme by ID
  const getThemeById = useCallback((themeId: string): MacroTheme | undefined => {
    return themes.find(theme => theme.theme_id === themeId)
  }, [themes])

  // Function to get goals for a specific theme
  const getThemeGoals = useCallback((themeId: string): string[] => {
    const theme = getThemeById(themeId)
    return theme?.goals || []
  }, [getThemeById])

  // Function to check if a goal belongs to a theme
  const isGoalInTheme = useCallback((goalId: string, themeId: string): boolean => {
    const theme = getThemeById(themeId)
    return theme?.goals.includes(goalId) || false
  }, [getThemeById])

  // Function to find theme for a goal
  const findThemeForGoal = useCallback((goalId: string): MacroTheme | undefined => {
    return themes.find(theme => theme.goals.includes(goalId))
  }, [themes])

  return {
    themes,
    loading,
    error,
    extractionResult,
    refetch: fetchThemes,
    getThemeById,
    getThemeGoals,
    isGoalInTheme,
    findThemeForGoal,
  }
}