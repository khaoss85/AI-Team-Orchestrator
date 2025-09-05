# OpenAI Quota Monitoring System Architecture

## Executive Summary
Comprehensive architectural analysis of the OpenAI quota monitoring system, examining API usage tracking, credit consumption calculation, and real-time budget monitoring across the full stack.

## 1. Core Architecture Components

### 1.1 Backend Components

#### **QuotaTrackedOpenAI Client Factory** (`backend/utils/openai_client_factory.py`)
- **Purpose**: Centralized factory ensuring ALL OpenAI API calls are tracked
- **Critical Role**: Wraps OpenAI SDK clients to intercept and monitor usage
- **Key Methods**:
  - `QuotaTrackedOpenAI`: Synchronous client wrapper
  - `QuotaTrackedAsyncOpenAI`: Asynchronous client wrapper
  - Wraps `chat.completions.create()` and `beta.chat.completions.parse()`
- **Tracking Mechanism**: 
  - Records token usage from API response
  - Captures both successful and failed requests
  - Routes metrics to quota_tracker service

#### **OpenAI Quota Tracker Service** (`backend/services/openai_quota_tracker.py`)
- **Purpose**: Multi-tenant quota tracking and status management
- **Key Features**:
  - Per-workspace tracking via `WorkspaceQuotaTracker` class
  - Real-time WebSocket broadcasting
  - Rate limit enforcement
  - Error detection and status escalation
- **Status States**:
  - `NORMAL`: Operating within limits
  - `WARNING`: Approaching limits (>90% usage)
  - `RATE_LIMITED`: Minute/day limits reached
  - `QUOTA_EXCEEDED`: OpenAI account quota exhausted
  - `DEGRADED`: Reduced capacity mode

#### **Quota API Routes** (`backend/routes/quota_api.py`)
- **REST Endpoints**:
  - `GET /api/quota/status`: Current quota status and usage
  - `GET /api/quota/notifications`: User-friendly notifications
  - `GET /api/quota/usage`: Detailed usage statistics
  - `GET /api/quota/availability`: Quick availability check
  - `POST /api/quota/reset`: Admin reset functionality
- **WebSocket Endpoint**:
  - `WS /api/quota/ws`: Real-time status updates
  - Per-workspace connection support
  - Automatic reconnection handling

### 1.2 Frontend Components

#### **useQuotaMonitor Hook** (`frontend/src/hooks/useQuotaMonitor.ts`)
- **Purpose**: React hook for quota monitoring integration
- **Features**:
  - WebSocket connection management
  - Automatic fallback to polling
  - Toast notification system
  - Progressive status updates
- **Configuration Options**:
  - `workspaceId`: Enable workspace-specific tracking
  - `enableWebSocket`: Real-time updates
  - `autoRefresh`: Polling fallback
  - `showNotifications`: Toast display control

#### **BudgetUsageChat Component** (`frontend/src/components/conversational/BudgetUsageChat.tsx`)
- **Purpose**: Visual budget monitoring in conversation interface
- **Display Elements**:
  - Real-time usage percentages
  - Requests per minute/day metrics
  - Countdown timers to reset
  - Color-coded status indicators
  - Progressive loading states

## 2. API Usage Tracking Flow

### 2.1 Request Interception Flow
```
1. Code calls OpenAI API → 
2. QuotaTrackedOpenAI intercepts → 
3. Executes actual API call → 
4. Extracts token usage from response → 
5. Records metrics in quota_tracker → 
6. Returns response to caller
```

### 2.2 Tracking Mechanism Details

#### **Token Usage Extraction**
```python
# From QuotaTrackedOpenAI wrapper
result = self._original_chat_completions_create(*args, **kwargs)
tokens_used = 0
if hasattr(result, 'usage') and result.usage:
    tokens_used = result.usage.total_tokens
quota_tracker.record_request(success=True, tokens_used=tokens_used)
```

#### **Request Recording**
```python
def record_request(self, success: bool = True, tokens_used: int = 0):
    # Track per-minute and per-day counts
    minute_key = now.replace(second=0, microsecond=0)
    day_key = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if success:
        self.request_counts[minute_key] += 1
        self.request_counts[day_key] += 1
        self.usage_stats["tokens_used"] += tokens_used
```

## 3. Credit Consumption Calculation

### 3.1 Rate Limit Tracking
The system tracks consumption against configurable limits:

#### **Rate Limits** (Environment Variables)
- `OPENAI_RATE_LIMIT_PER_MINUTE`: Default 500 requests
- `OPENAI_RATE_LIMIT_PER_DAY`: Default 10,000 requests  
- `OPENAI_TOKEN_LIMIT_PER_MINUTE`: Default 150,000 tokens

### 3.2 Usage Calculation Logic

#### **Percentage Calculations**
```python
"requests_per_minute": {
    "current": requests_this_minute,
    "limit": self.rate_limits["requests_per_minute"],
    "percentage": (requests_this_minute / limit) * 100
}
```

#### **Status Determination**
```python
if requests_this_minute >= limit:
    status = QuotaStatus.RATE_LIMITED
elif requests_this_minute >= limit * 0.9:
    status = QuotaStatus.WARNING
elif requests_today >= daily_limit * 0.9:
    status = QuotaStatus.WARNING
else:
    status = QuotaStatus.NORMAL
```

### 3.3 Cost Tracking (Note)
**Important**: The current system tracks REQUEST COUNTS and TOKEN USAGE but does NOT calculate monetary costs. Cost calculation would require:
- Model pricing tables (GPT-4, GPT-3.5, etc.)
- Token-to-cost conversion logic
- Budget limit configuration

## 4. Complete Flow: API Call to UI Display

### 4.1 End-to-End Data Flow

```mermaid
graph TD
    A[Agent/Service Code] -->|Uses| B[openai_client_factory]
    B -->|Creates| C[QuotaTrackedOpenAI Client]
    C -->|Wraps| D[OpenAI SDK]
    D -->|API Call| E[OpenAI API]
    E -->|Response + Usage| D
    D -->|Response| C
    C -->|Extract Tokens| F[quota_tracker.record_request]
    F -->|Update Stats| G[WorkspaceQuotaTracker]
    G -->|Broadcast| H[WebSocket Connections]
    H -->|Real-time Update| I[useQuotaMonitor Hook]
    I -->|State Update| J[BudgetUsageChat Component]
    G -->|REST API| K[/api/quota/status]
    K -->|Polling Fallback| I
```

### 4.2 WebSocket Real-time Updates

#### **Server-side Broadcasting**
```python
async def broadcast_status_update(self, status_data: Dict):
    message = json.dumps({
        "type": "quota_update",
        "data": status_data,
        "timestamp": datetime.now().isoformat()
    })
    
    for ws in self.connected_websockets:
        await ws.send_text(message)
```

#### **Client-side Reception**
```typescript
// In useQuotaMonitor hook
ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  if (message.type === 'quota_update') {
    const newStatus = mapQuotaDataToStatus(message.data)
    setQuotaStatus(newStatus)
    handleStatusNotification(newStatus)
  }
}
```

### 4.3 Frontend Display Pipeline

```typescript
// Component receives updates via hook
const { quotaStatus } = useQuotaMonitor({ workspaceId })

// Extract metrics
const rpmCurrent = stats.requests_per_minute.current
const rpmLimit = stats.requests_per_minute.limit
const rpmPercentage = stats.requests_per_minute.percentage

// Visual representation
<div className={statusDisplay.bg}>
  <span>{statusDisplay.emoji}</span>
  <span>{rpmCurrent}/{rpmLimit} requests/min</span>
  <ProgressBar percentage={rpmPercentage} />
</div>
```

## 5. Key Integration Points

### 5.1 Service Integration
Services using quota tracking:
- `universal_learning_engine.py`
- `ai_content_display_transformer.py`
- `ai_goal_matcher.py`
- `specialist.py`
- `conversational_simple.py`
- `director.py`

### 5.2 Critical Success Factor
**ALL OpenAI API calls MUST use `openai_client_factory`**
- Direct `OpenAI()` instantiation bypasses tracking
- Previous issue: 0/118,454 requests tracked
- Resolution: Centralized factory enforcement

## 6. System Capabilities

### 6.1 Real-time Monitoring
- WebSocket-based instant updates
- Per-workspace isolation
- Multi-client broadcasting
- Automatic reconnection

### 6.2 Intelligent Status Management
- Automatic status escalation
- Error-based status detection
- Cooldown period management
- Graceful degradation

### 6.3 User Experience Features
- Progressive loading states
- Color-coded visual indicators
- Countdown timers
- Toast notifications
- Suggested actions

## 7. Configuration & Environment

### 7.1 Required Environment Variables
```bash
# Rate Limits
OPENAI_RATE_LIMIT_PER_MINUTE=500
OPENAI_RATE_LIMIT_PER_DAY=10000
OPENAI_TOKEN_LIMIT_PER_MINUTE=150000

# Admin Features
QUOTA_ADMIN_RESET_KEY=<secure-key>
```

### 7.2 Frontend Configuration
```typescript
useQuotaMonitor({
  workspaceId: "workspace-uuid",
  enableWebSocket: true,
  autoRefresh: true,
  refreshInterval: 30000,
  showNotifications: true
})
```

## 8. Testing & Verification

### 8.1 Test Files
- `backend/test_quota_integration_verification.py`
- `backend/test_quota_integration_fix.py`

### 8.2 Key Test Scenarios
1. Token usage tracking accuracy
2. WebSocket connection resilience
3. Status escalation logic
4. Multi-workspace isolation
5. Error handling and recovery

## 9. Future Enhancements

### 9.1 Potential Improvements
1. **Cost Calculation**: Add model pricing and budget limits
2. **Historical Analytics**: Track usage patterns over time
3. **Predictive Warnings**: ML-based usage prediction
4. **Custom Alerts**: Configurable threshold notifications
5. **Usage Reports**: Daily/weekly summaries

### 9.2 Architecture Scalability
- Redis for distributed tracking
- Time-series database for analytics
- Webhook integrations for alerts
- Admin dashboard for monitoring

## 10. Critical Implementation Notes

### 10.1 Mandatory Patterns
```python
# CORRECT - Tracked
from utils.openai_client_factory import get_openai_client
client = get_openai_client()

# INCORRECT - Not tracked
from openai import OpenAI
client = OpenAI()  # Bypasses tracking!
```

### 10.2 WebSocket Lifecycle
```typescript
// Automatic cleanup on unmount
useEffect(() => {
  const ws = new WebSocket(wsUrl)
  // ... setup
  return () => ws.close()
}, [workspaceId])
```

### 10.3 Error Recovery
- Automatic WebSocket reconnection
- Fallback to REST polling
- Graceful degradation on quota exceeded
- User-friendly error messages

## Conclusion

The OpenAI Quota Monitoring System provides comprehensive, real-time tracking of API usage across the application. Through centralized client factories, WebSocket broadcasting, and intelligent status management, it ensures complete visibility and control over OpenAI API consumption. The system's architecture supports multi-tenancy, real-time updates, and graceful degradation, making it production-ready for managing API quotas at scale.

---
*Document Status: Complete Architecture Analysis*
*Last Updated: 2025-09-05*
*Author: AI Team Orchestrator Analysis System*