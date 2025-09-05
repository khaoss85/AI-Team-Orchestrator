#!/usr/bin/env python3
"""
Test the OpenAI Usage API Client to see what's happening
"""

import asyncio
import os
from datetime import datetime
import logging
from services.openai_usage_api_client import OpenAIUsageAPIClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def test_usage_client():
    """Test the usage client with different queries"""
    
    client = OpenAIUsageAPIClient()
    
    print("\n1️⃣ Testing today's usage through the client...")
    try:
        today_usage = await client.get_today_usage()
        print(f"   Total cost: ${today_usage.total_cost:.4f}")
        print(f"   Total tokens: {today_usage.total_tokens}")
        print(f"   Total requests: {today_usage.total_requests}")
        print(f"   Model breakdown: {list(today_usage.model_breakdown.keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2️⃣ Testing current month usage through the client...")
    try:
        month_usage = await client.get_current_month_usage()
        print(f"   Total cost: ${month_usage.total_cost:.4f}")
        print(f"   Total tokens: {month_usage.total_tokens}")
        print(f"   Total requests: {month_usage.total_requests}")
        print(f"   Models used: {list(month_usage.model_breakdown.keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3️⃣ Testing raw fetch_usage method...")
    try:
        today = datetime.now()
        raw_usage = await client.fetch_usage(
            start_date=today.replace(hour=0, minute=0, second=0),
            end_date=today,
            use_cache=False
        )
        print(f"   Total cost: ${raw_usage.total_cost:.4f}")
        print(f"   Total tokens: {raw_usage.total_tokens}")
        print(f"   Total requests: {raw_usage.total_requests}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4️⃣ Testing budget status...")
    try:
        budget = await client.check_budget_status()
        print(f"   Status: {budget.get('status')}")
        print(f"   Monthly budget: ${budget.get('monthly_budget', 0):.2f}")
        print(f"   Current spend: ${budget.get('current_spend', 0):.2f}")
        print(f"   Budget used: {budget.get('budget_used_percent', 0):.1f}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing OpenAI Usage API Client...")
    asyncio.run(test_usage_client())