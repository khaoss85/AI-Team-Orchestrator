# 🔄 Frontend OpenAI Usage API Integration

## Overview

The frontend has been fully integrated with the real OpenAI Usage API to display actual costs and budget tracking instead of the legacy quota system.

## Architecture

### 1. Smart Component Switching (BudgetUsageChatV2)
The system automatically detects whether the real Usage API is available and switches between:
- **Enhanced Version**: Real OpenAI costs when Usage API is configured
- **Legacy Version**: Falls back to quota tracking when Usage API is unavailable

### 2. Component Structure

```
BudgetCardV2.tsx (Entry Point)
  └── BudgetUsageChatV2.tsx (Smart Switcher)
      ├── BudgetUsageChatEnhanced.tsx (Real Costs)
      └── BudgetUsageChat.tsx (Legacy Quota)
```

## New Features

### Real Cost Tracking
- **Monthly Budget**: $100.00 default budget tracking
- **Current Spend**: Real-time cost accumulation
- **Daily Average**: Automatic calculation of daily spending
- **Projected Monthly**: Smart projection based on current usage

### Model Cost Breakdown
- Per-model cost tracking
- Token usage per model
- Request count per model
- Efficiency scoring

### AI Cost Intelligence
- Automatic detection of high GPT-4 usage
- Duplicate call pattern detection
- Cost optimization recommendations
- Potential savings calculations

### Visual Enhancements
- **Three-tab Interface**: Overview, Model Costs, AI Insights
- **Progress Bars**: Visual budget consumption
- **Color-coded Alerts**: Normal (green), Warning (yellow), Critical (red)
- **Live Update Indicators**: Real-time data refresh every 30 seconds

## API Endpoints

### Backend Routes (`/api/usage/`)
- `GET /api/usage/current-month` - Monthly usage data
- `GET /api/usage/today` - Today's usage with hourly breakdown
- `GET /api/usage/budget-status` - Budget tracking and alerts
- `GET /api/usage/model-comparison` - Model cost analysis
- `GET /api/usage/cost-intelligence/{workspace_id}` - AI optimization insights
- `GET /api/usage/dashboard/{workspace_id}` - Comprehensive dashboard

### Frontend API Client
```typescript
// Usage API methods in api.ts
api.usage.getCurrentMonth()
api.usage.getToday()
api.usage.getBudgetStatus()
api.usage.getModelComparison()
api.usage.getCostIntelligence(workspaceId)
api.usage.getDashboard(workspaceId)
```

## Type Definitions

```typescript
// Core types in types/usage.ts
interface UsageData {
  total_cost: number
  total_tokens: number
  total_requests: number
  model_breakdown: ModelCost[]
  daily_breakdown?: DailyUsage[]
}

interface BudgetStatus {
  monthly_budget: number
  current_spend: number
  budget_used_percentage: number
  projected_monthly_spend: number
  days_remaining: number
  daily_average: number
  is_over_budget: boolean
  budget_alert_level: 'normal' | 'warning' | 'critical'
  recommendations: string[]
}
```

## Current Status

### ✅ Completed
- Frontend API integration
- Type definitions
- Enhanced UI components
- Smart fallback system
- Backend route implementation
- Live data fetching

### 📊 Test Results
All endpoints return valid data:
- Budget status: Working (returns $0 due to exhausted quota)
- Today's usage: Working (returns empty data when no usage)
- Monthly usage: Working (accumulates all month data)
- Model comparison: Working (provides recommendations)
- Cost intelligence: Working (generates optimization alerts)

## Usage Instructions

### For Users
1. Navigate to any project conversation
2. Click on "Budget & Usage" in the sidebar
3. View real-time costs across three tabs:
   - **Overview**: Current spending and projections
   - **Model Costs**: Per-model breakdown
   - **AI Insights**: Optimization opportunities

### For Developers
1. Import the V2 component:
   ```tsx
   import BudgetCardV2 from '@/components/conversational/BudgetCardV2'
   ```

2. Use with workspace ID:
   ```tsx
   <BudgetCardV2 workspaceId={workspaceId} />
   ```

3. The component automatically handles:
   - API availability detection
   - Fallback to legacy system
   - Live data updates
   - Error handling

## Configuration

### Environment Variables
```bash
# Backend (.env)
OPENAI_API_KEY=sk-...        # Required for Usage API
MONTHLY_BUDGET=100.00         # Default monthly budget
USAGE_API_CACHE_TTL=300       # Cache duration in seconds

# Frontend
# No additional config needed - auto-detects API availability
```

## Monitoring

### Health Checks
- API endpoint: `GET /api/usage/budget-status`
- Returns budget status even with $0 usage
- Confirms system is operational

### Debugging
```bash
# Check backend endpoints
curl http://localhost:8000/api/usage/budget-status
curl http://localhost:8000/api/usage/today
curl http://localhost:8000/api/usage/current-month

# Monitor frontend console for:
- "Usage API not available, falling back to quota system"
- "✅ Usage API detected, using enhanced version"
```

## Benefits

### For Business Users
- **Real Cost Visibility**: See actual OpenAI spending, not arbitrary quotas
- **Budget Control**: Set and track against real monthly budgets
- **Cost Optimization**: AI-powered recommendations to reduce costs
- **Model Insights**: Understand which models cost the most

### For Development Teams
- **Automatic Fallback**: System works even without Usage API
- **Type Safety**: Full TypeScript support
- **Minimal UI**: Clean, ChatGPT-style interface
- **Production Ready**: Error handling and loading states

## Future Enhancements
- Historical cost charts
- Team-based budget allocation
- Cost alerting via email/Slack
- Export to CSV/PDF reports
- Custom budget periods
- Department cost attribution

## Files Reference
- **Components**: `frontend/src/components/conversational/BudgetUsageChat*.tsx`
- **Types**: `frontend/src/types/usage.ts`
- **API Client**: `frontend/src/utils/api.ts` (usage section)
- **Backend Routes**: `backend/routes/usage.py`
- **Usage Client**: `backend/services/openai_usage_api_client.py`