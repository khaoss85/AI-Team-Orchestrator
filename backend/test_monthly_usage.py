#!/usr/bin/env python3
"""
Test the fixed monthly usage aggregation
"""

import asyncio
import logging
from services.openai_usage_api_client import OpenAIUsageAPIClient

# Enable info logging to see progress
logging.basicConfig(level=logging.INFO)

async def test_monthly_usage():
    """Test the monthly usage aggregation"""
    
    client = OpenAIUsageAPIClient()
    
    print("\n🧪 Testing monthly usage aggregation (this may take a moment)...")
    try:
        month_usage = await client.get_current_month_usage()
        print(f"✅ Total cost this month: ${month_usage.total_cost:.4f}")
        print(f"   Total tokens: {month_usage.total_tokens:,}")
        print(f"   Total requests: {month_usage.total_requests:,}")
        print(f"   Models used: {list(month_usage.model_breakdown.keys())}")
        print(f"   Days with usage: {len(month_usage.daily_breakdown)}")
        
        # Show daily breakdown
        if month_usage.daily_breakdown:
            print("\n   Daily breakdown:")
            for date in sorted(month_usage.daily_breakdown.keys())[:5]:  # Show first 5 days
                day_data = month_usage.daily_breakdown[date]
                print(f"     {date}: ${day_data.get('cost', 0):.2f} ({day_data.get('requests', 0)} requests)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🧪 Testing budget status with real monthly data...")
    try:
        budget = await client.check_budget_status()
        print(f"✅ Budget status: {budget.get('status')}")
        print(f"   Monthly budget: ${budget.get('monthly_budget', 0):.2f}")
        print(f"   Current spend: ${budget.get('current_spend', 0):.2f}")
        print(f"   Budget used: {budget.get('budget_used_percent', 0):.1f}%")
        print(f"   Daily average: ${budget.get('daily_average', 0):.2f}")
        print(f"   Projected monthly: ${budget.get('projected_monthly', 0):.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_monthly_usage())