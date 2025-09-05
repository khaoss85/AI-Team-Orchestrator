#!/usr/bin/env python3
"""
Final test of the fixed API endpoints
"""

import asyncio
from routes.usage import router
from services.openai_usage_api_client import get_usage_client

async def test_endpoints():
    """Test the API endpoints directly"""
    
    print("🧪 Testing endpoints with real data...")
    
    # Test today endpoint
    print("\n1️⃣ Testing today's usage endpoint...")
    try:
        client = get_usage_client()
        usage_data = await client.get_today_usage()
        
        result = {
            "total_cost": usage_data.total_cost,
            "total_tokens": usage_data.total_tokens,
            "total_requests": usage_data.total_requests,
            "model_breakdown": [
                {
                    "model": model_name,
                    "input_cost_per_1k": stats.get('input_cost', 0) / max(stats.get('input_tokens', 1) / 1000, 0.001),
                    "output_cost_per_1k": stats.get('output_cost', 0) / max(stats.get('output_tokens', 1) / 1000, 0.001),
                    "total_input_tokens": stats.get('input_tokens', 0),
                    "total_output_tokens": stats.get('output_tokens', 0),
                    "total_cost": stats.get('total_cost', 0),
                    "request_count": stats.get('requests_count', 0),
                    "error_count": 0  
                } for model_name, stats in usage_data.model_breakdown.items()
            ],
            "hourly_breakdown": [
                {
                    "hour": int(hour_key.split()[1].split(':')[0]) if ' ' in hour_key and ':' in hour_key else idx,
                    "cost": hour_data.get('total_cost', hour_data.get('cost', 0)),
                    "tokens": hour_data.get('total_tokens', hour_data.get('tokens', 0)),
                    "requests": hour_data.get('requests_count', hour_data.get('requests', 0))
                } for idx, (hour_key, hour_data) in enumerate(usage_data.hourly_breakdown.items() if usage_data.hourly_breakdown else {})
            ] if usage_data.hourly_breakdown else [],
            "period_start": getattr(usage_data, 'period_start', None),
            "period_end": getattr(usage_data, 'period_end', None)
        }
        
        print(f"✅ SUCCESS! Today's usage:")
        print(f"   Total cost: ${result['total_cost']:.2f}")
        print(f"   Total tokens: {result['total_tokens']:,}")
        print(f"   Total requests: {result['total_requests']:,}")
        print(f"   Models: {len(result['model_breakdown'])}")
        print(f"   Hourly data points: {len(result['hourly_breakdown'])}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test budget endpoint
    print("\n2️⃣ Testing budget status endpoint...")
    try:
        client = get_usage_client()
        budget_data = await client.check_budget_status()
        print(f"✅ SUCCESS! Budget status:")
        print(f"   Status: {budget_data.get('status')}")
        print(f"   Monthly budget: ${budget_data.get('monthly_budget', 0):.2f}")
        print(f"   Current spend: ${budget_data.get('current_spend', 0):.2f}")
        print(f"   Budget used: {budget_data.get('budget_used_percent', 0):.1f}%")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())