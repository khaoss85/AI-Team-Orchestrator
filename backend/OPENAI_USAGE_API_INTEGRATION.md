# OpenAI Usage API v1 Integration

## Overview

This document describes the integration of OpenAI's Usage API v1 into the AI Team Orchestrator system, providing real-time cost tracking, budget monitoring, and intelligent cost optimization recommendations.

## Architecture

### Core Components

1. **OpenAI Usage API Client** (`services/openai_usage_api_client.py`)
   - Direct integration with OpenAI's `/v1/usage` endpoint
   - Fetches real usage data including costs, tokens, and request counts
   - Supports daily, hourly, and minute-level aggregation
   - Includes intelligent caching to minimize API calls

2. **Enhanced AI Cost Intelligence** (`services/ai_cost_intelligence.py`)
   - Now calibrated with real usage data instead of estimates
   - Compares estimated vs actual costs for accuracy improvements
   - Generates optimization alerts based on real spending patterns
   - Detects duplicate calls, model waste, and prompt inefficiencies

3. **Enhanced Quota Tracker** (`services/openai_quota_tracker.py`)
   - Integrates real usage data with rate limiting
   - Provides real-time budget status and projections
   - Broadcasts usage updates via WebSocket
   - Calibrates estimates using actual costs

4. **Usage Analytics API** (`routes/usage_analytics.py`)
   - RESTful endpoints for usage data access
   - Dashboard endpoint with comprehensive metrics
   - Budget monitoring and projections
   - Model comparison and cost trends

5. **Historical Data Storage** (`migrations/017_add_openai_usage_history.sql`)
   - Persistent storage of usage history
   - Cost optimization alert tracking
   - Budget configuration per workspace
   - Optimized views for reporting

## Key Features

### Real-Time Cost Tracking
- **Actual costs** from OpenAI instead of estimates
- **Token-level granularity** for precise tracking
- **Model-specific costs** for optimization decisions
- **Hourly/daily/monthly** aggregation options

### Intelligent Cost Optimization
- **Duplicate call detection** with potential savings calculation
- **Model efficiency analysis** suggesting cheaper alternatives
- **Prompt optimization** detecting bloated prompts
- **Pattern analysis** identifying cost inefficiencies

### Budget Management
- **Monthly budget tracking** with real spend data
- **Projections** based on current usage patterns
- **Automatic alerts** at configurable thresholds
- **Daily limits** calculated from remaining budget

### Accuracy Calibration
- **Real vs Estimated comparison** for system accuracy
- **Automatic calibration** of cost estimates
- **Confidence scoring** for optimization recommendations
- **Historical accuracy tracking**

## API Endpoints

### Usage Data Endpoints

#### GET `/api/usage/current-month`
Returns current month's usage with model breakdown and daily details.

#### GET `/api/usage/today`
Returns today's usage with hourly breakdown.

#### GET `/api/usage/budget-status`
Returns budget status with spending projections and alerts.

#### GET `/api/usage/model-comparison`
Compares costs and efficiency across different models.

#### GET `/api/usage/cost-trend`
Returns cost trends over time with daily and cumulative data.

#### GET `/api/usage/real-vs-estimated/{workspace_id}`
Compares real usage data with system estimates for accuracy.

#### GET `/api/usage/cost-intelligence/{workspace_id}`
Returns AI-generated cost optimization alerts and recommendations.

#### GET `/api/usage/dashboard/{workspace_id}`
Comprehensive dashboard data with all metrics for frontend display.

## Configuration

### Environment Variables

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-...                    # Required for Usage API access

# Cache Settings
USAGE_CACHE_TTL_SECONDS=300              # Cache duration (default: 5 minutes)
USAGE_API_MIN_INTERVAL_SECONDS=10        # Min time between API calls

# Budget Configuration
OPENAI_MONTHLY_BUDGET_USD=100            # Monthly budget limit
OPENAI_WARNING_THRESHOLD_PERCENT=80      # Warning threshold
OPENAI_CRITICAL_THRESHOLD_PERCENT=95     # Critical threshold

# Cost Intelligence Settings
AI_COST_DUPLICATE_THRESHOLD=3            # Duplicate calls threshold
AI_COST_PROMPT_BLOAT_THRESHOLD=2000      # Prompt size threshold
AI_COST_MODEL_WASTE_THRESHOLD=5.0        # Model waste threshold USD
```

## Usage Examples

### Fetching Real Usage Data

```python
from services.openai_usage_api_client import get_usage_client

# Get usage client
client = get_usage_client()

# Fetch current month usage
month_usage = await client.get_current_month_usage()
print(f"Current month spend: ${month_usage.total_cost:.2f}")

# Check budget status
budget_status = await client.check_budget_status()
if budget_status['status'] == 'warning':
    print(f"⚠️ Budget warning: {budget_status['budget_used_percent']:.1f}% used")

# Compare models
comparison = await client.get_model_comparison(days=7)
for model, data in comparison.items():
    print(f"{model}: ${data['total_cost']:.2f} ({data['cost_percentage']:.1f}%)")
```

### Cost Intelligence Integration

```python
from services.ai_cost_intelligence import get_cost_intelligence

# Get cost intelligence for workspace
cost_intel = get_cost_intelligence(workspace_id)

# Update with real costs
await cost_intel.update_real_costs()

# Analyze API call for inefficiencies
alerts = await cost_intel.analyze_api_call(call_data)
for alert in alerts:
    if alert.severity == AlertSeverity.HIGH:
        print(f"🚨 {alert.title}: ${alert.potential_savings:.2f}/day savings possible")

# Get cost summary with real data calibration
summary = cost_intel.get_cost_summary()
print(f"Efficiency Score: {summary['efficiency_score']}/100")
```

### Dashboard Integration

```python
# Fetch comprehensive dashboard data
response = await client.get(f"/api/usage/dashboard/{workspace_id}")
dashboard_data = response.json()

# Display key metrics
print(f"Today: ${dashboard_data['today']['cost']:.2f}")
print(f"Month: ${dashboard_data['month']['cost']:.2f}")
print(f"Budget: {dashboard_data['budget']['percentage_used']:.1f}% used")
print(f"Efficiency: {dashboard_data['intelligence']['efficiency_score']}/100")

# Show alerts
for alert in dashboard_data['intelligence']['alerts']:
    print(f"{alert['severity']}: {alert['title']} (Save ${alert['savings']:.2f}/day)")
```

## Database Schema

### openai_usage_history
Stores historical usage data with:
- Daily/hourly aggregation
- Model-specific breakdown
- Cost and token tracking
- API method distribution

### cost_optimization_alerts
Tracks AI-generated optimization opportunities:
- Alert type and severity
- Potential savings calculation
- Evidence and recommendations
- Status tracking

### openai_budget_tracking
Manages budget configuration and tracking:
- Monthly budget limits
- Current spend tracking
- Projections and overages
- Historical spending data

## Benefits

### 1. **Accurate Cost Tracking**
- Real costs from OpenAI, not estimates
- Precise model and token-level tracking
- Historical trend analysis

### 2. **Proactive Cost Management**
- Early warning for budget overruns
- Daily spending recommendations
- Projected monthly costs

### 3. **Intelligent Optimization**
- AI-driven waste detection
- Model efficiency recommendations
- Prompt optimization suggestions

### 4. **Real-Time Monitoring**
- WebSocket updates for live tracking
- Dashboard with comprehensive metrics
- Instant alerts for critical events

### 5. **Data-Driven Decisions**
- Model comparison for cost/quality trade-offs
- Usage pattern analysis
- ROI tracking for AI investments

## Migration Guide

### Running the Migration

```bash
# Apply the migration to add usage tracking tables
psql -U your_user -d your_database -f migrations/017_add_openai_usage_history.sql

# If needed, rollback the migration
psql -U your_user -d your_database -f migrations/017_add_openai_usage_history_ROLLBACK.sql
```

### Initial Setup

1. Ensure `OPENAI_API_KEY` is set in environment
2. Run the database migration
3. Restart the backend service
4. Access the dashboard at `/api/usage/dashboard/{workspace_id}`

## Testing

### Test Usage API Connection

```bash
# Test the usage API client
cd backend
python3 services/openai_usage_api_client.py

# Expected output:
# 📊 Testing OpenAI Usage API Client
# Today's Usage:
#   Total Cost: $X.XXXX
#   Total Tokens: X,XXX
# Current Month Usage:
#   Total Cost: $XX.XX
# Budget Status:
#   Status: NORMAL
#   Current Spend: $XX.XX / $100.00
```

### Test Cost Intelligence

```bash
# Test cost intelligence with real data
cd backend
python3 services/ai_cost_intelligence.py

# Expected output:
# 🚨 HIGH: Duplicate API Calls Detected
#    💰 Potential savings: $X.XXXX/day
#    💡 Consider caching results
```

### Test API Endpoints

```bash
# Test usage endpoints
curl -X GET "http://localhost:8000/api/usage/current-month" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X GET "http://localhost:8000/api/usage/budget-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X GET "http://localhost:8000/api/usage/dashboard/WORKSPACE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring

### Key Metrics to Track
- **Daily spend rate** - Monitor for anomalies
- **Model distribution** - Ensure optimal model usage
- **Duplicate rate** - Target < 5%
- **Efficiency score** - Target > 80
- **Budget utilization** - Stay under limits

### Alert Thresholds
- **Budget 80%**: Warning notifications
- **Budget 95%**: Critical alerts
- **Duplicate calls > 10/hour**: Optimization alert
- **Model waste > $5/day**: Efficiency alert

## Troubleshooting

### Common Issues

1. **"No API key" error**
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Check key has usage permissions

2. **"Rate limited" on Usage API**
   - Increase `USAGE_API_MIN_INTERVAL_SECONDS`
   - Check cache is working (`USAGE_CACHE_TTL_SECONDS`)

3. **Cost discrepancies**
   - Run calibration: `await cost_intel.update_real_costs()`
   - Check time zones in usage data

4. **Missing historical data**
   - Run migration: `017_add_openai_usage_history.sql`
   - Check database permissions

## Future Enhancements

### Planned Features
- [ ] Automated budget adjustment recommendations
- [ ] Multi-workspace cost allocation
- [ ] Custom alert rules and thresholds
- [ ] Export usage reports (CSV/PDF)
- [ ] Cost prediction using ML models
- [ ] Integration with billing systems
- [ ] Team-based cost tracking
- [ ] Automated model switching based on cost/performance

### API Improvements
- [ ] Batch usage data fetching
- [ ] Webhook support for real-time updates
- [ ] GraphQL endpoint for flexible queries
- [ ] Cost simulator for "what-if" scenarios

## Security Considerations

- **API Key Protection**: Never expose keys in logs or responses
- **Rate Limiting**: Respect OpenAI's API limits
- **Data Privacy**: Usage data contains no PII
- **Access Control**: Workspace-isolated data access
- **Audit Trail**: All budget changes logged

## Support

For issues or questions about the Usage API integration:
1. Check this documentation
2. Review logs in `backend/logs/`
3. Test with provided diagnostic scripts
4. Check OpenAI API status at status.openai.com

## Conclusion

The OpenAI Usage API v1 integration transforms cost tracking from estimates to real data, enabling precise budget management and intelligent optimization. With AI-driven insights and real-time monitoring, teams can maximize their OpenAI investment while staying within budget.