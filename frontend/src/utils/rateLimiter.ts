/**
 * Client-side Rate Limiter
 * Implements a token bucket algorithm for rate limiting API calls
 */

interface RateLimiterOptions {
  maxRequests: number
  windowMs: number
  name?: string
}

interface RequestQueue {
  resolve: () => void
  reject: (error: Error) => void
  timestamp: number
}

class RateLimiter {
  private tokens: number
  private lastRefill: number
  private readonly maxTokens: number
  private readonly refillRate: number
  private readonly windowMs: number
  private readonly name: string
  private queue: RequestQueue[] = []
  private processing = false

  constructor(options: RateLimiterOptions) {
    this.maxTokens = options.maxRequests
    this.tokens = options.maxRequests
    this.windowMs = options.windowMs
    this.refillRate = options.maxRequests / (options.windowMs / 1000) // tokens per second
    this.lastRefill = Date.now()
    this.name = options.name || 'default'
  }

  private refillTokens() {
    const now = Date.now()
    const timePassed = (now - this.lastRefill) / 1000 // in seconds
    const tokensToAdd = timePassed * this.refillRate
    
    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd)
    this.lastRefill = now
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return
    
    this.processing = true
    
    while (this.queue.length > 0) {
      this.refillTokens()
      
      if (this.tokens >= 1) {
        const request = this.queue.shift()
        if (request) {
          this.tokens -= 1
          request.resolve()
        }
      } else {
        // Calculate wait time until next token is available
        const waitTime = (1 / this.refillRate) * 1000
        await new Promise(resolve => setTimeout(resolve, waitTime))
      }
    }
    
    this.processing = false
  }

  async acquire(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check for stale requests in queue (older than 30 seconds)
      const now = Date.now()
      this.queue = this.queue.filter(req => {
        if (now - req.timestamp > 30000) {
          req.reject(new Error('Rate limit request timeout'))
          return false
        }
        return true
      })

      // Add to queue
      this.queue.push({ resolve, reject, timestamp: now })
      
      // Start processing
      this.processQueue()
    })
  }

  getStatus() {
    this.refillTokens()
    return {
      availableTokens: Math.floor(this.tokens),
      maxTokens: this.maxTokens,
      queueLength: this.queue.length,
      canMakeRequest: this.tokens >= 1
    }
  }

  reset() {
    this.tokens = this.maxTokens
    this.lastRefill = Date.now()
    this.queue.forEach(req => req.reject(new Error('Rate limiter reset')))
    this.queue = []
  }
}

// Create rate limiters for different API endpoints
const rateLimiters = new Map<string, RateLimiter>()

export function getRateLimiter(endpoint: string, options?: RateLimiterOptions): RateLimiter {
  const key = endpoint.toLowerCase()
  
  if (!rateLimiters.has(key)) {
    // Default rate limits based on backend configuration
    const defaultOptions: RateLimiterOptions = {
      maxRequests: 20,
      windowMs: 60000, // 1 minute
      name: endpoint,
      ...options
    }
    
    // Specific limits for known endpoints
    if (key.includes('quota/status')) {
      defaultOptions.maxRequests = 20
      defaultOptions.windowMs = 60000
    } else if (key.includes('quota/check')) {
      defaultOptions.maxRequests = 30
      defaultOptions.windowMs = 60000
    } else if (key.includes('quota/notifications')) {
      defaultOptions.maxRequests = 10
      defaultOptions.windowMs = 60000
    }
    
    rateLimiters.set(key, new RateLimiter(defaultOptions))
  }
  
  return rateLimiters.get(key)!
}

// Middleware function for fetch requests
export async function rateLimitedFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  // Extract endpoint from URL
  const urlObj = new URL(url)
  const endpoint = urlObj.pathname.replace('/api/', '')
  
  // Get rate limiter for this endpoint
  const limiter = getRateLimiter(endpoint)
  
  // Wait for rate limit token
  await limiter.acquire()
  
  // Make the actual request
  try {
    const response = await fetch(url, options)
    
    // Check for rate limit headers from server
    const remaining = response.headers.get('X-RateLimit-Remaining')
    const reset = response.headers.get('X-RateLimit-Reset')
    
    if (remaining && reset) {
      console.log(`Rate limit status for ${endpoint}: ${remaining} remaining, resets at ${new Date(parseInt(reset) * 1000).toLocaleTimeString()}`)
    }
    
    return response
  } catch (error) {
    // On error, return the token
    const status = limiter.getStatus()
    console.error(`Request failed for ${endpoint}. Rate limiter status:`, status)
    throw error
  }
}

// Export utility to check rate limit status
export function checkRateLimitStatus(endpoint: string) {
  const limiter = getRateLimiter(endpoint)
  return limiter.getStatus()
}

// Export utility to reset all rate limiters (for testing)
export function resetAllRateLimiters() {
  rateLimiters.forEach(limiter => limiter.reset())
  rateLimiters.clear()
}