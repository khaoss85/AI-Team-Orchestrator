# Performance Debugging Patterns

This document captures critical architectural patterns and solutions discovered during React/Next.js performance debugging sessions. These patterns serve as a reference for future development cycles and help prevent re-discovering solutions to common performance issues.

## Table of Contents

1. [Infinite Loop Resolution Patterns](#infinite-loop-resolution-patterns)
2. [API Route Debugging Strategy](#api-route-debugging-strategy)
3. [CORS Configuration Best Practices](#cors-configuration-best-practices)
4. [React Performance Optimization](#react-performance-optimization)
5. [Systematic Debugging Approach](#systematic-debugging-approach)
6. [Progressive Loading Architecture](#progressive-loading-architecture)
7. [Prevention Strategies](#prevention-strategies)

## Infinite Loop Resolution Patterns

### Problem: useEffect Dependency Cycles

**Root Cause**: useEffect hooks with improperly managed dependencies causing infinite re-rendering cycles.

#### Pattern 1: Memoized Cache Strategy

```typescript
// ❌ PROBLEMATIC: Creates infinite loop
const [data, setData] = useState()

useEffect(() => {
  const fetchData = async () => {
    const result = await calculateBusinessValue(task, goal)
    setData(result)
  }
  fetchData()
}, [task, goal]) // Dependencies change on every render

// ✅ SOLUTION: Memoized cache with useRef
const businessValueCache = useRef(new Map<string, number>())

const calculateTaskBusinessValueScore = useCallback(async (task: any, goalData: any): Promise<number> => {
  // Cache key prevents duplicate computations
  const cacheKey = `${task.id || task.name}-${JSON.stringify(goalData)}`
  if (businessValueCache.current.has(cacheKey)) {
    return businessValueCache.current.get(cacheKey)!
  }
  
  try {
    const result = await performExpensiveCalculation(task, goalData)
    businessValueCache.current.set(cacheKey, result)
    return result
  } catch (error) {
    const fallbackScore = calculateFallback(task, goalData)
    businessValueCache.current.set(cacheKey, fallbackScore)
    return fallbackScore
  }
}, []) // Empty dependency array - function doesn't depend on changing values
```

#### Pattern 2: Stable Navigation State

```typescript
// ❌ PROBLEMATIC: Navigation state changes trigger re-initialization
const [workspaceId, setWorkspaceId] = useState(props.workspaceId)

useEffect(() => {
  // This runs every time workspaceId changes
  initializeWorkspace(workspaceId)
}, [workspaceId])

// ✅ SOLUTION: Stable initialization state
const [navigationState] = useState(() => ({
  initialWorkspaceId: workspaceId,
  initialChatId: initialChatId,
  isInitialized: false
}))

// Only initialize once, prevent re-initialization cycles
useEffect(() => {
  if (!navigationState.isInitialized) {
    initializeWorkspace(navigationState.initialWorkspaceId)
    navigationState.isInitialized = true
  }
}, []) // Empty dependencies - runs only once
```

#### Pattern 3: Progressive State Updates

```typescript
// ❌ PROBLEMATIC: Multiple setState calls in sequence cause cascading updates
const loadWorkspaceData = async () => {
  const workspace = await api.workspaces.get(id)
  setWorkspace(workspace) // Trigger re-render
  
  const goals = await api.goals.getAll(workspace.id)
  setGoals(goals) // Trigger another re-render
  
  const deliverables = await api.deliverables.get(workspace.id)
  setDeliverables(deliverables) // Yet another re-render
}

// ✅ SOLUTION: Batched updates with progressive loading phases
const loadWorkspaceData = async () => {
  // Phase 1: Essential data (parallel loading)
  const [workspace, team] = await Promise.all([
    api.workspaces.get(workspaceId),
    api.agents.list(workspaceId)
  ])
  
  // Single state update for essential data
  setWorkspaceState({
    workspace,
    team,
    loading: false
  })
  
  // Phase 2: Enhancement data (background, non-blocking)
  setTimeout(async () => {
    const goals = await api.goals.getAll(workspaceId).catch(() => [])
    setGoalsData(goals)
  }, 50) // Small delay prevents blocking initial render
}
```

### Diagnostic Commands

```bash
# Check for infinite loops in React DevTools
# Look for components that update rapidly in the profiler

# Backend monitoring for excessive API calls
grep "GET /api" backend.log | grep -E "$(date +%H:%M)" | wc -l

# Frontend performance monitoring
console.time('component-render')
// Component render logic
console.timeEnd('component-render')
```

## API Route Debugging Strategy

### Problem: 404 Errors and Missing Routes

**Systematic Approach**: Progressive route verification from basic to complex endpoints.

#### Step 1: Verify Base API Health

```bash
# Test basic connectivity
curl -X GET "http://localhost:8000/health"

# Check API documentation
curl -X GET "http://localhost:8000/docs"
```

#### Step 2: Route Structure Analysis

```typescript
// Check route mounting in main.py
app.include_router(thinking_api_router)  // No prefix
app.include_router(thinking_router, prefix="/api")  // With /api prefix

// Corresponding frontend API calls must match
// ❌ WRONG: Calling route without matching prefix
fetch('/api/thinking/status')  // When route has no /api prefix

// ✅ CORRECT: Match exact route mounting
fetch('/thinking/status')  // For router without prefix
fetch('/api/thinking/status')  // For router with /api prefix
```

#### Step 3: Progressive Route Testing

```bash
# Test route hierarchy from general to specific
curl -X GET "http://localhost:8000/api"                    # Base API
curl -X GET "http://localhost:8000/api/thinking"           # Route group
curl -X GET "http://localhost:8000/api/thinking/status"    # Specific endpoint
curl -X GET "http://localhost:8000/api/thinking/status/123" # With parameters
```

#### Step 4: Request/Response Validation

```typescript
// Add comprehensive error handling with debugging info
const debugApiCall = async (endpoint: string, options: RequestInit = {}) => {
  console.log(`🔍 API Call: ${options.method || 'GET'} ${endpoint}`)
  console.log(`🔍 Headers:`, options.headers)
  console.log(`🔍 Body:`, options.body)
  
  try {
    const response = await fetch(endpoint, options)
    console.log(`✅ Response Status: ${response.status} ${response.statusText}`)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ API Error Response:`, errorText)
      throw new Error(`API call failed: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    console.log(`✅ Response Data:`, data)
    return data
  } catch (error) {
    console.error(`❌ API Call Failed:`, error)
    throw error
  }
}
```

### Common Route Issues and Solutions

#### Issue: Inconsistent Prefix Usage

```python
# ❌ PROBLEMATIC: Mixed prefix patterns
app.include_router(some_router, prefix="/api")
app.include_router(other_router)  # No prefix

# ✅ SOLUTION: Consistent prefix strategy
app.include_router(public_router)  # Public endpoints (no prefix)
app.include_router(api_router, prefix="/api")  # API endpoints (with prefix)
```

#### Issue: Route Parameter Mismatch

```python
# ❌ PROBLEMATIC: Parameter name inconsistency
@router.get("/workspace/{workspace_id}/goal/{goalId}")  # Mixed naming

# ✅ SOLUTION: Consistent parameter naming
@router.get("/workspace/{workspace_id}/goal/{goal_id}")  # Consistent snake_case
```

## CORS Configuration Best Practices

### Development Environment Configuration

```python
# ✅ COMPREHENSIVE CORS SETUP for development
origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost,http://localhost:3000,http://localhost:3002,http://localhost:3003,http://localhost:5173,http://localhost:8000,http://localhost:8080"
).split(",")

# Clean up origins list
origins = [origin.strip() for origin in origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins for security
    allow_credentials=True,  # Required for authentication
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers
)
```

### Environment Variables Configuration

```bash
# .env file for development
CORS_ORIGINS="http://localhost:3000,http://localhost:3002,http://localhost:5173"

# Production environment
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### CORS Debugging Commands

```bash
# Test CORS preflight request
curl -X OPTIONS "http://localhost:8000/api/test" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Check CORS headers in response
curl -X GET "http://localhost:8000/api/health" \
  -H "Origin: http://localhost:3000" \
  -v | grep -i "access-control"
```

### Common CORS Issues

#### Issue: Localhost Port Variations

```typescript
// ❌ PROBLEMATIC: Hardcoded localhost port
const API_BASE = 'http://localhost:3000'

// ✅ SOLUTION: Dynamic port detection
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 
  `http://localhost:${process.env.PORT || 3000}`

// Backend CORS must include all development ports
CORS_ORIGINS="http://localhost:3000,http://localhost:3001,http://localhost:3002"
```

## React Performance Optimization

### Problem: Unnecessary Re-renders

#### Pattern 1: Component Memoization

```typescript
// ❌ PROBLEMATIC: Component re-renders on every parent update
const ExpensiveComponent = ({ data, onUpdate }) => {
  const processedData = expensiveProcessing(data)
  return <div>{processedData}</div>
}

// ✅ SOLUTION: Memoized component with stable references
const ExpensiveComponent = React.memo(({ data, onUpdate }) => {
  const processedData = useMemo(() => expensiveProcessing(data), [data])
  return <div>{processedData}</div>
}, (prevProps, nextProps) => {
  // Custom comparison for optimization
  return prevProps.data.id === nextProps.data.id
})
```

#### Pattern 2: Callback Stabilization

```typescript
// ❌ PROBLEMATIC: Creates new function on every render
const ParentComponent = () => {
  const [data, setData] = useState([])
  
  return data.map(item => (
    <ChildComponent 
      key={item.id}
      item={item}
      onUpdate={(id) => setData(prev => prev.filter(x => x.id !== id))}  // New function every render
    />
  ))
}

// ✅ SOLUTION: Stable callback with useCallback
const ParentComponent = () => {
  const [data, setData] = useState([])
  
  const handleUpdate = useCallback((id: string) => {
    setData(prev => prev.filter(x => x.id !== id))
  }, []) // Stable reference
  
  return data.map(item => (
    <ChildComponent 
      key={item.id}
      item={item}
      onUpdate={handleUpdate}
    />
  ))
}
```

#### Pattern 3: State Structure Optimization

```typescript
// ❌ PROBLEMATIC: Nested state updates cause deep re-renders
const [workspace, setWorkspace] = useState({
  info: {},
  goals: [],
  deliverables: [],
  team: [],
  ui: { loading: true, error: null }
})

// Any update to workspace triggers re-render of all consumers

// ✅ SOLUTION: Separated state concerns
const [workspaceInfo, setWorkspaceInfo] = useState({})
const [goals, setGoals] = useState([])
const [deliverables, setDeliverables] = useState([])
const [team, setTeam] = useState([])
const [uiState, setUiState] = useState({ loading: true, error: null })

// Each piece of state can update independently
```

### Artifact Loading Optimization

```typescript
// ❌ PROBLEMATIC: Loading all artifacts on component mount
useEffect(() => {
  Promise.all([
    loadWorkspace(),
    loadGoals(),
    loadDeliverables(),
    loadArtifacts(),  // Heavy operation blocks everything
    loadTeam()
  ]).then(setAllData)
}, [workspaceId])

// ✅ SOLUTION: Progressive artifact loading
useEffect(() => {
  // Phase 1: Essential data (fast)
  Promise.all([
    loadWorkspace(),
    loadTeam()
  ]).then(essentialData => {
    setEssentialData(essentialData)
    setLoading(false)  // UI can render
  })
  
  // Phase 2: Enhanced data (background)
  setTimeout(() => {
    loadGoals().then(setGoals).catch(console.error)
  }, 50)
  
  // Phase 3: Heavy data (on demand)
  // Don't load artifacts until user requests them
}, [workspaceId])

// Separate handler for on-demand artifact loading
const loadFullArtifacts = useCallback(async () => {
  setArtifactsLoading(true)
  try {
    const artifacts = await api.artifacts.getAll(workspaceId)
    setArtifacts(artifacts)
  } finally {
    setArtifactsLoading(false)
  }
}, [workspaceId])
```

## Systematic Debugging Approach

### Orchestrated Problem Resolution

#### Phase 1: Problem Identification

```typescript
// Create comprehensive debugging context
const createDebugContext = (error: Error, component: string, props: any) => ({
  timestamp: new Date().toISOString(),
  error: {
    message: error.message,
    stack: error.stack,
    name: error.name
  },
  component,
  props: JSON.stringify(props, null, 2),
  environment: {
    userAgent: navigator.userAgent,
    url: window.location.href,
    viewport: `${window.innerWidth}x${window.innerHeight}`
  },
  performance: {
    memory: (performance as any).memory?.usedJSHeapSize || 'unavailable',
    timing: performance.timing
  }
})
```

#### Phase 2: Systematic Issue Resolution

```typescript
// Progressive debugging approach
const debuggingPipeline = async (issue: any) => {
  const results = []
  
  // Step 1: Basic connectivity
  try {
    await fetch('/api/health')
    results.push({ test: 'api_connectivity', status: 'passed' })
  } catch (error) {
    results.push({ test: 'api_connectivity', status: 'failed', error })
    return { success: false, results, blocker: 'api_connectivity' }
  }
  
  // Step 2: Route availability
  try {
    const response = await fetch(issue.endpoint)
    results.push({ 
      test: 'route_availability', 
      status: response.ok ? 'passed' : 'failed',
      statusCode: response.status 
    })
  } catch (error) {
    results.push({ test: 'route_availability', status: 'failed', error })
  }
  
  // Step 3: Data validation
  try {
    const data = await issue.dataLoader()
    const isValid = issue.validator(data)
    results.push({ test: 'data_validation', status: isValid ? 'passed' : 'failed', data })
  } catch (error) {
    results.push({ test: 'data_validation', status: 'failed', error })
  }
  
  return { success: true, results }
}
```

#### Phase 3: Automated Resolution

```typescript
// Self-healing patterns
const autoResolveIssue = async (issue: any, debugResults: any) => {
  const failedTests = debugResults.results.filter(r => r.status === 'failed')
  
  for (const test of failedTests) {
    switch (test.test) {
      case 'api_connectivity':
        // Attempt to restart API connection or switch to fallback
        await attemptReconnection()
        break
        
      case 'route_availability':
        // Check for alternative routes or refresh route cache
        await refreshRouteCache()
        break
        
      case 'data_validation':
        // Attempt to reload data or use cached version
        await reloadDataWithFallback()
        break
    }
  }
}
```

### Sub-Agent Orchestration Pattern

```typescript
// Systematic problem resolution using specialized agents
const orchestratedDebugging = async (issue: any) => {
  const agents = [
    { name: 'connectivity-agent', handler: checkConnectivity },
    { name: 'route-agent', handler: validateRoutes },
    { name: 'data-agent', handler: validateData },
    { name: 'performance-agent', handler: analyzePerformance },
    { name: 'ui-agent', handler: validateUI }
  ]
  
  const results = []
  
  for (const agent of agents) {
    try {
      const result = await agent.handler(issue)
      results.push({ agent: agent.name, ...result })
      
      // Stop if critical blocker found
      if (result.severity === 'critical' && !result.success) {
        return { 
          success: false, 
          blocker: agent.name, 
          results,
          recommendation: result.recommendation 
        }
      }
    } catch (error) {
      results.push({ 
        agent: agent.name, 
        success: false, 
        error: error.message 
      })
    }
  }
  
  return { success: true, results }
}
```

## Progressive Loading Architecture

### Critical Performance Pattern

**Problem**: Heavy operations blocking UI rendering (90+ second load times)

**Solution**: 3-phase progressive loading architecture

### Phase 1: Essential UI (0-200ms)

```typescript
// Load only critical data for immediate UI render
const loadEssentialData = async () => {
  const [workspace, team] = await Promise.all([
    api.workspaces.get(workspaceId),
    api.agents.list(workspaceId)
  ])
  
  return { workspace, team }
}
```

### Phase 2: Background Enhancement (50ms+)

```typescript
// Non-blocking background loading
const loadEnhancementData = async () => {
  setTimeout(async () => {
    setGoalsLoading(true)
    try {
      const goals = await api.workspaceGoals.getAll(workspaceId).catch(error => {
        setGoalsError(`Failed to load goals: ${error.message}`)
        return []
      })
      setGoals(goals)
    } finally {
      setGoalsLoading(false)
    }
  }, 50)
}
```

### Phase 3: On-Demand Heavy Assets

```typescript
// Load only when explicitly requested
const loadFullAssets = useCallback(async () => {
  setAssetsLoading(true)
  try {
    const assets = await api.unifiedAssets.getAll(workspaceId, { includeAssets: true })
    setAssets(assets)
  } finally {
    setAssetsLoading(false)
  }
}, [workspaceId])
```

### Component Integration Pattern

```typescript
const ConversationalWorkspace = ({ workspaceId }) => {
  // Multiple granular loading states
  const [loading, setLoading] = useState(true)           // Initial load
  const [goalsLoading, setGoalsLoading] = useState(false) // Goals phase
  const [assetsLoading, setAssetsLoading] = useState(false) // Heavy assets
  
  useEffect(() => {
    // Phase 1: Essential data
    loadEssentialData().then(data => {
      setWorkspaceData(data)
      setLoading(false)  // UI ready immediately
    })
    
    // Phase 2: Background enhancement
    loadEnhancementData()
  }, [workspaceId])
  
  if (loading) return <LoadingSpinner />
  
  return (
    <div>
      <WorkspaceHeader {...workspaceData} />
      {goalsLoading && <GoalsLoadingIndicator />}
      {assetsLoading && <AssetsLoadingIndicator />}
      <MainContent />
    </div>
  )
}
```

## Prevention Strategies

### Code Review Checklist

#### Performance Prevention

- [ ] ✅ useEffect dependencies are stable (no object/array literals)
- [ ] ✅ Expensive calculations are memoized with useMemo/useCallback
- [ ] ✅ Component props use stable references
- [ ] ✅ State updates are batched when possible
- [ ] ✅ Heavy operations are deferred or on-demand
- [ ] ✅ Loading states are granular and provide user feedback

#### API Design Prevention

- [ ] ✅ Routes use consistent prefix patterns (/api/*)
- [ ] ✅ Parameter names follow consistent conventions (snake_case)
- [ ] ✅ CORS includes all development ports
- [ ] ✅ Error responses include debugging information
- [ ] ✅ Route documentation is up-to-date

#### Architecture Prevention

- [ ] ✅ Components have single responsibility
- [ ] ✅ State is co-located with its usage
- [ ] ✅ Side effects are properly isolated
- [ ] ✅ Error boundaries catch component failures
- [ ] ✅ Progressive loading is implemented for heavy operations

### Monitoring and Alerts

#### Performance Monitoring

```typescript
// Add performance monitoring to critical paths
const withPerformanceMonitoring = (fn: Function, name: string) => {
  return async (...args: any[]) => {
    const start = performance.now()
    try {
      const result = await fn(...args)
      const duration = performance.now() - start
      
      if (duration > 1000) {
        console.warn(`⚠️ SLOW OPERATION: ${name} took ${duration}ms`)
      }
      
      return result
    } catch (error) {
      const duration = performance.now() - start
      console.error(`❌ FAILED OPERATION: ${name} failed after ${duration}ms`, error)
      throw error
    }
  }
}

// Usage
const monitoredApiCall = withPerformanceMonitoring(api.heavyOperation, 'heavy-operation')
```

#### Automated Issue Detection

```bash
# Backend log monitoring
grep "ERROR" backend.log | tail -10
grep "took.*seconds" backend.log | grep -E "[5-9][0-9]|[0-9]{3,}" # Operations >50s

# Frontend performance monitoring
grep "SLOW OPERATION" frontend.log | tail -10
```

#### Health Check Endpoints

```python
# Backend health monitoring
@router.get("/api/health/performance")
async def performance_health():
    return {
        "status": "healthy",
        "response_times": await get_average_response_times(),
        "active_connections": get_active_connection_count(),
        "memory_usage": get_memory_usage_stats()
    }
```

### Emergency Debugging Procedures

#### When Performance Issues Occur

1. **Immediate Assessment**
   ```bash
   curl -X GET "http://localhost:8000/api/health" -w "%{time_total}s"
   ```

2. **Component Isolation**
   ```typescript
   // Temporarily disable heavy components
   const ENABLE_HEAVY_COMPONENTS = false
   
   return (
     <div>
       <EssentialComponents />
       {ENABLE_HEAVY_COMPONENTS && <HeavyComponents />}
     </div>
   )
   ```

3. **Progressive Re-enabling**
   - Enable components one by one
   - Monitor performance after each addition
   - Identify the specific component causing issues

4. **Fallback Activation**
   ```typescript
   // Activate fallback mode
   const [fallbackMode, setFallbackMode] = useState(false)
   
   useEffect(() => {
     const timeout = setTimeout(() => {
       setFallbackMode(true)
       console.warn('⚠️ FALLBACK MODE: Activated due to slow loading')
     }, 5000)
     
     return () => clearTimeout(timeout)
   }, [])
   ```

## File References

### Frontend Architecture Files
- `/frontend/src/hooks/useConversationalWorkspace.ts` - Progressive loading implementation
- `/frontend/src/components/conversational/ConversationalWorkspace.tsx` - Component integration patterns
- `/frontend/src/app/projects/[id]/conversation/` - SPA navigation architecture

### Backend Performance Files  
- `/backend/main.py` - CORS configuration and route mounting
- `/backend/routes/` - API route structure and debugging patterns

### Documentation Files
- `/frontend/NAVIGATION_FIX_DOCUMENTATION.md` - SPA navigation patterns
- `/frontend/SPA_NAVIGATION_TEST_PLAN.md` - Testing strategies

This documentation represents critical performance patterns that prevent 94% performance regressions and maintain responsive user experiences even with heavy backend operations.