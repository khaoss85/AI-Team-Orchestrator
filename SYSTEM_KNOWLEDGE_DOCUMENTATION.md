# AI Team Orchestrator - Critical System Knowledge Documentation

**Generated from Troubleshooting Session** - Essential knowledge for future development work on this AI team orchestrator system.

## 🏗️ System Architecture - Essential Concepts

### Core Data Flow
**Critical Path:** `Goals → Tasks → Deliverables → Asset_Artifacts → Frontend`

This is the fundamental data flow that drives the entire system. Understanding this flow is essential:

1. **Workspaces** contain multiple **Goals** (specific business objectives)
2. **Goals** generate **Tasks** (AI-driven decomposition of work)  
3. **Tasks** produce **Deliverables** (organized business outputs)
4. **Deliverables** contain **Asset_Artifacts** (concrete deliverable content)
5. **Frontend** displays this chain through various UI components

### Database Schema Relationships
```
workspaces (1:n) workspace_goals (1:n) tasks (1:n) asset_artifacts
                              ↓
                        deliverables (aggregates tasks into business outputs)
```

**Key Tables:**
- `workspaces` - Project containers
- `workspace_goals` - Specific measurable objectives  
- `tasks` - Individual work units (AI-generated)
- `asset_artifacts` - Actual deliverable content
- `deliverables` - Business-focused aggregations of completed work

## 🔧 Critical Technical Patterns

### 1. Backend API URL Structure
**CRITICAL RULE:** All API endpoints use `/api` prefix consistently

```typescript
// Correct patterns:
`${API_BASE_URL}/api/workspaces/${id}`
`${API_BASE_URL}/api/unified-assets/workspace/${workspaceId}`  
`${API_BASE_URL}/api/deliverables/workspace/${workspaceId}`

// Legacy patterns (avoid):
`${API_BASE_URL}/workspaces/${id}`  
`${API_BASE_URL}/assets/${id}`
```

### 2. Frontend API Integration Patterns
**File:** `/frontend/src/utils/api.ts` - Central API client

```typescript
// Standard API call pattern:
const response = await fetch(`${API_BASE_URL}/api/endpoint`, {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
});
if (!response.ok) throw new Error(`API error: ${response.status}`);
return await response.json();
```

### 3. Goal Progress Calculation Logic
**CRITICAL:** Backend and frontend must use identical calculation logic

```typescript
// Correct calculation (both frontend and backend):
const progress = targetValue > 0 ? Math.min((currentValue / targetValue) * 100, 100) : 0;

// Common mistake: 
const progress = (currentValue / targetValue) * 100; // No bounds checking
```

### 4. Status Value Mapping
**CRITICAL:** Enum string values must match between frontend/backend

```typescript
// Backend (models.py):
class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed" 
    PAUSED = "paused"

// Frontend must use exact same string values:
status === 'active' // NOT status === 'ACTIVE'
```

## 🚨 Common Issues and Solutions

### Issue #1: OpenAI Quota Exhaustion
**Symptoms:** API timeouts, 429 errors, system slowdown
**Solution:** 
```python
# Implement graceful degradation in AI-driven components
try:
    ai_result = await openai_call()
except openai.RateLimitError:
    return fallback_logic()
```

### Issue #2: Frontend-Backend Data Format Mismatches  
**Symptoms:** Data not displaying, calculation errors
**Root Cause:** Backend returns different field names/types than frontend expects

**Solution Pattern:**
```typescript
// Transform backend data to expected frontend format
const transformedData: ProjectDeliverablesExtended = {
  workspace_id: workspaceId,
  completion_percentage: data.completion_percentage || 0,
  key_outputs: (data.key_outputs || []).map((output: any) => ({
    ...output,
    created_at: typeof output.created_at === 'string' 
      ? output.created_at 
      : new Date(output.created_at).toISOString(),
  }))
};
```

### Issue #3: Deliverables Not Showing Despite Backend Success
**Symptoms:** Empty deliverables in frontend, backend logs show successful creation
**Root Cause:** API endpoint URL mismatch or data transformation errors

**Debugging Steps:**
1. Check browser Network tab for actual API requests
2. Verify API endpoint URLs match backend route definitions
3. Compare raw API response with frontend expected format
4. Validate data transformation logic

### Issue #4: Goal Progress Calculation Inconsistencies
**Symptoms:** Different progress percentages in different UI components
**Root Cause:** Multiple calculation methods across codebase

**Solution:** Centralize calculation logic:
```typescript
// utils/goalProgress.ts
export const calculateGoalProgress = (current: number, target: number): number => {
  if (!target || target <= 0) return 0;
  return Math.min((current / target) * 100, 100);
};
```

## 📚 Development Best Practices

### Debugging Workflow
1. **Check API Contract:** Verify frontend API calls match backend route definitions
2. **Inspect Network Traffic:** Use browser dev tools to see actual requests/responses
3. **Validate Data Flow:** Trace data from database → backend API → frontend display
4. **Use Sub-Agents:** Leverage specialized debugging sub-agents (db-steward, api-contract-guardian)

### API Development Pattern
1. **Define Backend Route:** Add to appropriate router in `/backend/routes/`
2. **Update Frontend API Client:** Add method to `/frontend/src/utils/api.ts`
3. **Create Frontend Hook:** Add custom hook in `/frontend/src/hooks/`
4. **Implement UI Component:** Connect hook to component
5. **Test Integration:** Verify end-to-end functionality

### Error Handling Standards
```typescript
// Backend (FastAPI):
try:
    result = await operation()
    return {"success": True, "data": result}
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))

// Frontend:
try {
    const response = await api.method();
    setData(response);
} catch (error) {
    console.error('Operation failed:', error);
    setError(error.message);
}
```

## ⚠️ Critical Gotchas

### 1. OpenAI API Rate Limits
- **Impact:** Sudden system failure during heavy usage
- **Prevention:** Implement rate limiting and fallback mechanisms
- **Recovery:** Monitor usage patterns, implement graceful degradation

### 2. Database Query Optimization
- **Issue:** N+1 query problems in goal/task/deliverable relationships
- **Solution:** Use database joins and proper indexing
- **Monitor:** Watch query execution times in logs

### 3. WebSocket Connection Management
- **Issue:** Memory leaks from unclosed connections  
- **Solution:** Proper cleanup in `useEffect` cleanup functions
- **Pattern:** Always call `websocket.close()` in cleanup

### 4. Frontend State Synchronization
- **Issue:** Stale data when multiple components track same resource
- **Solution:** Use centralized state management or React Query
- **Pattern:** Single source of truth for shared data

## 🔍 Effective Debugging Strategies

### 1. API Contract Verification
```bash
# Test backend endpoints directly:
curl -X GET "http://localhost:8000/api/deliverables/workspace/{id}"
curl -X GET "http://localhost:8000/api/unified-assets/workspace/{id}"
```

### 2. Database State Inspection
```python
# Quick database inspection script:
from database import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
print(f"Goals: {len(result.data)}")
```

### 3. Frontend Data Flow Tracing
```typescript
// Add temporary logging to trace data flow:
console.log('API Response:', rawResponse);
console.log('Transformed Data:', transformedData);
console.log('Component State:', componentData);
```

### 4. Component Hierarchy Analysis
Use React Developer Tools to inspect:
- Component props and state
- Hook values and dependencies  
- Re-render triggers
- Performance bottlenecks

## 📁 Key File Locations

### Backend Critical Files
- `/backend/main.py` - FastAPI application entry point and routing
- `/backend/models.py` - Pydantic models and enums (source of truth)
- `/backend/database.py` - Supabase integration and database operations
- `/backend/routes/` - API endpoint definitions (organized by feature)
- `/backend/executor.py` - Task execution engine

### Frontend Critical Files  
- `/frontend/src/utils/api.ts` - Central API client (ALL API calls)
- `/frontend/src/types/index.ts` - TypeScript type definitions
- `/frontend/src/hooks/` - Custom React hooks for data fetching
- `/frontend/src/components/conversational/` - Main user interface components

### Configuration Files
- `/backend/.env` - Environment variables and feature flags
- `/CLAUDE.md` - Development commands and system overview
- `/frontend/package.json` - Frontend dependencies and scripts

## 🛠️ Recovery Procedures

### When System Appears "Stuck"
1. **Check OpenAI Quota:** Verify API limits haven't been exceeded
2. **Restart Backend:** `cd backend && python main.py`
3. **Clear Frontend Cache:** Hard refresh browser, clear localStorage
4. **Verify Database State:** Check recent tasks/goals in Supabase dashboard
5. **Check Logs:** Examine backend console output for errors

### When Data Isn't Flowing
1. **API Health Check:** `curl http://localhost:8000/health`  
2. **Network Inspection:** Check browser Network tab for failed requests
3. **URL Verification:** Ensure API URLs match backend routes
4. **Data Format Validation:** Compare API response to expected format

### When Frontend Shows Empty Data
1. **Backend Data Verification:** Confirm data exists in database
2. **API Response Validation:** Check raw API responses in browser
3. **Transformation Logic:** Verify data transformation in api.ts
4. **Component State:** Check if data reaches component via React DevTools

---

## 🎯 Success Patterns

**This troubleshooting session successfully resolved:**
- OpenAI quota exhaustion handling
- Frontend-backend goal progress calculation alignment  
- API endpoint URL pattern inconsistencies
- Deliverables pipeline frontend integration
- Data flow optimization from database to UI

**Key Success Factors:**
1. **Systematic API Contract Verification** - Test each endpoint independently
2. **Data Flow Tracing** - Follow data from database through all transformation layers
3. **Sub-Agent Utilization** - Leverage specialized debugging agents for focused tasks
4. **Consistent URL Patterns** - Maintain `/api` prefix across all endpoints  
5. **Graceful Degradation** - Implement fallbacks for external API failures

This documentation should significantly reduce debugging time and prevent repeated issues in future development sessions.