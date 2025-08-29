/**
 * Environment detection utilities for the AI Team Orchestrator
 */

export const environment = {
  /**
   * Check if we're running in development mode
   */
  isDevelopment: (): boolean => {
    // Check multiple conditions for development
    return (
      process.env.NODE_ENV === 'development' ||
      (typeof window !== 'undefined' && (
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname.includes('localhost')
      )) ||
      process.env.NEXT_PUBLIC_ENVIRONMENT === 'development'
    )
  },

  /**
   * Check if we're running in production mode
   */
  isProduction: (): boolean => {
    return !environment.isDevelopment()
  },

  /**
   * Get current environment string
   */
  getEnvironment: (): 'development' | 'production' => {
    return environment.isDevelopment() ? 'development' : 'production'
  },

  /**
   * Check if debug features should be enabled
   */
  isDebugEnabled: (): boolean => {
    return environment.isDevelopment() || process.env.NEXT_PUBLIC_DEBUG === 'true'
  },

  /**
   * Get API base URL based on environment
   */
  getApiUrl: (): string => {
    if (typeof window !== 'undefined') {
      // Client-side detection
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000'
      }
    }
    
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
}

export default environment