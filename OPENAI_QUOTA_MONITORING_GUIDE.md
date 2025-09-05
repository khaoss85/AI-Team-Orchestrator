# OpenAI Quota Monitoring System - Complete Guide

## Overview
The enhanced OpenAI Quota Monitoring System provides comprehensive tracking of all OpenAI API usage with model-specific breakdown, real-time updates, and budget management capabilities.

## Key Features

### 1. Complete API Coverage
- **Chat Completions**: All chat models (GPT-4, GPT-3.5, etc.)
- **Embeddings**: All embedding models
- **Assistants API**: Full assistant operations tracking
- **Threads & Runs**: Conversation thread management
- **Images**: DALL-E and image generation
- **Files**: File upload and management
- **Models**: Model listing (no quota impact)

### 2. Enhanced Tracking Capabilities
- **Model-Specific Breakdown**: Track usage per model (gpt-4, gpt-3.5-turbo, etc.)
- **API Method Breakdown**: Track usage per API method (chat.completions, embeddings.create, etc.)
- **Token Tracking**: Precise token usage per request and cumulative
- **Cost Estimation**: Real-time cost calculation based on token usage
- **Error Tracking**: Track failed requests and error patterns
- **Recent Activity Log**: Last 10 API calls with full details

### 3. Real-Time Updates
- **WebSocket Support**: Live updates to connected clients
- **Auto-Refresh**: Configurable refresh intervals
- **Progressive UI Updates**: Non-blocking UI with real-time data

### 4. Configurable Limits
All limits are configurable via environment variables:

```bash
# OpenAI Quota Monitoring Configuration
OPENAI_RATE_LIMIT_PER_MINUTE=500          # Max requests per minute
OPENAI_RATE_LIMIT_PER_DAY=10000           # Max requests per day  
OPENAI_TOKEN_LIMIT_PER_MINUTE=150000      # Max tokens per minute
OPENAI_DAILY_TOKEN_LIMIT=2000000          # Max tokens per day (2M tokens)
OPENAI_MONTHLY_BUDGET_USD=100             # Monthly budget in USD
OPENAI_WARNING_THRESHOLD_PERCENT=80       # Trigger warning at 80% usage
OPENAI_CRITICAL_THRESHOLD_PERCENT=95      # Trigger critical alert at 95% usage
```

## Implementation Architecture

### Core Components

#### 1. Enhanced Factory (`openai_client_factory_enhanced.py`)
```python
from utils.openai_client_factory_enhanced import get_enhanced_openai_client

# Create a tracked client
client = get_enhanced_openai_client(workspace_id="your-workspace")

# Use normally - all calls are automatically tracked
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
```

#### 2. Quota Tracker (`openai_quota_tracker.py`)
- Maintains per-workspace usage statistics
- Tracks requests, tokens, and costs
- Manages WebSocket connections for real-time updates
- Provides status data with enhanced metrics

#### 3. UI Component (`BudgetUsageChat.tsx`)
- Real-time budget monitoring display
- Model usage breakdown visualization
- API method usage statistics
- Recent activity log
- Progressive loading for performance

## Migration Guide

### Step 1: Update Imports
Replace direct OpenAI client instantiation:

**Before:**
```python
from openai import OpenAI
client = OpenAI()
```

**After:**
```python
from utils.openai_client_factory_enhanced import get_enhanced_openai_client
client = get_enhanced_openai_client(workspace_id=workspace_id)
```

### Step 2: Update Async Clients
For async operations:

**Before:**
```python
from openai import AsyncOpenAI
client = AsyncOpenAI()
```

**After:**
```python
from utils.openai_client_factory_enhanced import get_enhanced_async_openai_client
client = get_enhanced_async_openai_client(workspace_id=workspace_id)
```

### Step 3: Files to Update
Priority files that need migration:
1. `backend/utils/context_manager.py` ✅ (Updated)
2. `backend/ai_agents/conversational.py` ✅ (Updated)
3. `backend/services/document_manager.py`
4. `backend/services/unified_progress_manager.py`
5. `backend/services/universal_ai_content_extractor.py`
6. `backend/services/ai_domain_classifier.py`
7. `backend/services/semantic_domain_memory.py`
8. `backend/services/workspace_cleanup_service.py`
9. `backend/tools/openai_sdk_tools.py`
10. `backend/tools/enhanced_document_search.py`

## API Endpoints

### Get Quota Status
```bash
GET /api/quota/status/{workspace_id}
```

Response:
```json
{
  "status": "normal",
  "requests_per_minute": {
    "current": 10,
    "limit": 500,
    "percentage": 2.0
  },
  "requests_per_day": {
    "current": 150,
    "limit": 10000,
    "percentage": 1.5
  },
  "tokens_per_minute": {
    "current": 1500,
    "limit": 150000,
    "percentage": 1.0
  },
  "enhanced_tracking": {
    "models_breakdown": {
      "gpt-3.5-turbo": {
        "request_count": 100,
        "tokens_used": 5000
      },
      "gpt-4": {
        "request_count": 50,
        "tokens_used": 10000
      }
    },
    "api_methods_breakdown": {
      "chat.completions": {
        "request_count": 140,
        "error_count": 2
      },
      "embeddings.create": {
        "request_count": 10,
        "error_count": 0
      }
    },
    "recent_activity": [
      {
        "timestamp": "2025-09-05T09:31:27Z",
        "model": "gpt-3.5-turbo",
        "api_method": "chat.completions",
        "tokens_used": 24,
        "success": true
      }
    ]
  }
}
```

### WebSocket Connection
```javascript
// Connect to quota updates WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/quota/ws/${workspaceId}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'quota_update') {
    // Handle quota update
    console.log('Quota update:', data.data)
  }
}
```

## UI Integration

### React Hook Usage
```typescript
import { useQuotaMonitor } from '@/hooks/useQuotaMonitor'

function MyComponent() {
  const { quotaStatus, isLoading, error } = useQuotaMonitor({
    workspaceId: 'your-workspace',
    enableWebSocket: true,
    showNotifications: true,
    autoRefresh: true,
    refreshInterval: 10000
  })
  
  // Use quotaStatus data
  return (
    <div>
      <p>Status: {quotaStatus.status}</p>
      <p>Requests today: {quotaStatus.statistics.requests_per_day.current}</p>
    </div>
  )
}
```

### Budget Usage Component
```typescript
import BudgetUsageChat from '@/components/conversational/BudgetUsageChat'

function ConversationView() {
  return (
    <BudgetUsageChat workspaceId="your-workspace" />
  )
}
```

## Testing

### Run Test Suite
```bash
cd backend
python3 test_enhanced_quota_tracking.py
```

### Manual Testing
```python
# Test the enhanced tracking
from utils.openai_client_factory_enhanced import get_enhanced_openai_client

client = get_enhanced_openai_client(workspace_id="test")
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Test"}],
    max_tokens=10
)

# Check tracking
from services.openai_quota_tracker import quota_manager
tracker = quota_manager.get_tracker("test")
print(tracker.get_status_data())
print(tracker.get_enhanced_status_data())
```

## Monitoring & Alerts

### Status Levels
1. **NORMAL**: Everything operating within limits
2. **WARNING**: Approaching limits (>80% usage)
3. **RATE_LIMITED**: Hit rate limits, requests throttled
4. **QUOTA_EXCEEDED**: Monthly quota exceeded
5. **DEGRADED**: System operating with limitations

### Alert Triggers
- **Warning Alert**: At 80% of any limit
- **Critical Alert**: At 95% of any limit
- **Rate Limit Alert**: When 429 errors received
- **Quota Exceeded Alert**: When monthly budget exhausted

## Best Practices

### 1. Always Use the Factory
Never instantiate OpenAI clients directly. Always use the factory:
```python
# ❌ Don't do this
client = OpenAI()

# ✅ Do this
client = get_enhanced_openai_client(workspace_id=workspace_id)
```

### 2. Pass Workspace IDs
Always pass workspace IDs for proper multi-tenant tracking:
```python
client = get_enhanced_openai_client(workspace_id=workspace_id)
```

### 3. Handle Quota Errors
Check quota status before making expensive operations:
```python
tracker = quota_manager.get_tracker(workspace_id)
status = tracker.get_status_data()

if status['status'] in ['quota_exceeded', 'rate_limited']:
    # Handle gracefully - wait, use cache, or inform user
    return cached_response
```

### 4. Monitor Cost Trends
Use the enhanced data to monitor cost trends:
```python
enhanced = tracker.get_enhanced_status_data()
models = enhanced['enhanced_tracking']['models_breakdown']

# Find most expensive model usage
for model, data in models.items():
    cost = estimate_cost(model, data['tokens_used'])
    print(f"{model}: ${cost:.2f}")
```

## Troubleshooting

### Issue: Tracking Not Working
1. Verify factory is imported correctly
2. Check that workspace_id is passed
3. Ensure quota_manager is initialized
4. Check logs for wrapping errors

### Issue: WebSocket Not Connecting
1. Verify WebSocket endpoint is running
2. Check CORS configuration
3. Ensure workspace_id matches
4. Check network/firewall settings

### Issue: Limits Not Respected
1. Verify environment variables are set
2. Restart backend after config changes
3. Check that all clients use the factory
4. Review error logs for bypass paths

## Future Enhancements

### Planned Features
1. **Cost Prediction**: ML-based cost forecasting
2. **Auto-Throttling**: Automatic request throttling near limits
3. **Budget Alerts**: Email/Slack notifications for budget thresholds
4. **Historical Analytics**: Long-term usage trends and analysis
5. **Model Optimization**: Suggestions for cheaper model alternatives
6. **Team Quotas**: Per-team or per-user quota management

### Integration Opportunities
1. **Billing System**: Direct integration with payment systems
2. **Analytics Dashboard**: Comprehensive usage analytics
3. **Cost Allocation**: Department/project cost allocation
4. **Compliance Reporting**: Usage reports for compliance
5. **API Gateway**: Central API management layer

## Support

For issues or questions:
1. Check the test suite: `test_enhanced_quota_tracking.py`
2. Review logs in `backend/logs/`
3. Check environment configuration in `.env`
4. Verify all clients use the enhanced factory

## Conclusion

The Enhanced OpenAI Quota Monitoring System provides enterprise-grade tracking and management of OpenAI API usage. By following this guide and migrating all OpenAI client instantiations to use the enhanced factory, you'll have complete visibility and control over your AI infrastructure costs and usage patterns.