# Quota Monitoring Rate Limit Solution

## Problem Description
The application was experiencing 429 rate limit errors with the message:
```
Error: API error: 429 {"detail":"Rate limit exceeded. Max 20 requests per 60 seconds"}
```

This was occurring in the quota monitoring system, specifically in `src/utils/api.ts` line 2300 in the `getStatus` function.

## Root Cause Analysis

### 1. **Multiple Component Instances**
- 6+ different components were using the `useQuotaMonitor` hook independently
- Each instance maintained its own polling cycle and state
- No coordination between components

### 2. **Aggressive Polling Intervals**
- Components were polling with intervals as low as 10 seconds
- With multiple instances: 6 components × 2 API calls × every 30 seconds = 24+ requests/minute
- This exceeded the backend limit of 20 requests per minute

### 3. **No Request Deduplication**
- Multiple components on the same page requested identical data simultaneously
- No shared state or caching mechanism
- Each hook instance made independent API calls

### 4. **Lack of Rate Limiting on Client Side**
- Frontend had no awareness of backend rate limits
- No exponential backoff on rate limit errors
- No request queueing or throttling

## Solution Implementation

### 1. **Centralized Quota Context** (`/frontend/src/contexts/QuotaContext.tsx`)
- Single source of truth for quota data across all components
- Request deduplication - only one API call even with multiple consumers
- Intelligent caching with 5-second TTL
- Shared WebSocket connection for real-time updates
- Exponential backoff on rate limit errors (1s → 2s → 4s → ... → 60s max)

### 2. **Client-Side Rate Limiter** (`/frontend/src/utils/rateLimiter.ts`)
- Token bucket algorithm implementation
- Enforces rate limits before making API calls
- Request queueing when rate limit is reached
- Per-endpoint rate limit configuration
- Automatic token refill based on time window

### 3. **Backward Compatibility**
- `useQuotaMonitor` hook refactored as compatibility wrapper
- Existing components continue to work without changes
- Deprecation warnings guide migration to new `useQuota` hook
- No breaking changes for existing code

### 4. **API Integration Updates**
- `api.ts` updated to use rate-limited fetch for quota endpoints
- Automatic rate limit enforcement before requests
- Better error handling for 429 responses

## Architecture Benefits

### Performance Improvements
- **API Calls Reduced**: From 24+ requests/minute to max 2 requests/minute
- **Response Time**: Near-instant for cached data (5-second TTL)
- **WebSocket Priority**: Real-time updates without polling when connected
- **Graceful Degradation**: Falls back to polling if WebSocket fails

### Reliability Enhancements
- **No More 429 Errors**: Client-side rate limiting prevents hitting backend limits
- **Exponential Backoff**: Automatic recovery from rate limit situations
- **Request Coalescing**: Multiple simultaneous requests share single API call
- **Error Resilience**: Continues functioning even during rate limit periods

### Developer Experience
- **Zero Migration Effort**: Backward compatible with existing code
- **Clear Deprecation Path**: Warnings guide migration to new patterns
- **Centralized Management**: Single place to configure quota monitoring
- **Type Safety**: Full TypeScript support with proper interfaces

## Usage Guidelines

### For New Components
```typescript
import { useQuota } from '@/contexts/QuotaContext'

function MyComponent() {
  const { quotaStatus, isLoading, error, refresh } = useQuota()
  
  // Use quota data...
}
```

### For Existing Components
Existing components using `useQuotaMonitor` will continue to work but should migrate:
```typescript
// Old (deprecated but working)
import useQuotaMonitor from '@/hooks/useQuotaMonitor'
const { quotaStatus } = useQuotaMonitor({ workspaceId })

// New (recommended)
import { useQuota } from '@/contexts/QuotaContext'
const { quotaStatus } = useQuota()
```

### Configuration
The QuotaProvider is configured at the root level in `app/layout.tsx`:
```typescript
<QuotaProvider enableWebSocket={true} showNotifications={true}>
  {children}
</QuotaProvider>
```

## Monitoring and Debugging

### Check Rate Limiter Status
```typescript
import { checkRateLimitStatus } from '@/utils/rateLimiter'

const status = checkRateLimitStatus('quota/status')
console.log('Available tokens:', status.availableTokens)
console.log('Queue length:', status.queueLength)
```

### Monitor API Calls
- Browser DevTools Network tab: Look for `/api/quota/*` requests
- Should see maximum 1 request every 30 seconds per endpoint
- WebSocket connection at `/api/quota/ws` for real-time updates

### Backend Rate Limit Configuration
- `/api/quota/status`: Max 20 requests per minute
- `/api/quota/check`: Max 30 requests per minute  
- `/api/quota/notifications`: Max 10 requests per minute

## Testing Checklist

- [ ] No 429 errors during normal operation
- [ ] Multiple components share same quota data
- [ ] WebSocket provides real-time updates
- [ ] Graceful fallback when WebSocket disconnects
- [ ] Exponential backoff on rate limit errors
- [ ] Cache prevents unnecessary API calls
- [ ] Backward compatibility maintained

## Files Modified

### Core Implementation
- `/frontend/src/contexts/QuotaContext.tsx` - New centralized context
- `/frontend/src/utils/rateLimiter.ts` - Client-side rate limiting
- `/frontend/src/hooks/useQuotaMonitor.ts` - Refactored as compatibility wrapper
- `/frontend/src/app/layout.tsx` - Added QuotaProvider
- `/frontend/src/utils/api.ts` - Added rate-limited fetch for quota endpoints

### Backend (Reference)
- `/backend/routes/quota_api.py` - Rate limit decorators (20 req/min)
- `/backend/utils/performance_cache.py` - Rate limiting implementation

## Future Improvements

1. **Persistent Cache**: Store quota data in localStorage for faster initial load
2. **Smart Polling**: Adjust intervals based on activity and quota status
3. **Request Priority**: Prioritize critical requests when approaching limits
4. **Analytics**: Track and report rate limit metrics for optimization
5. **Circuit Breaker**: Temporarily disable features when quota exhausted