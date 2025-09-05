#!/usr/bin/env python3
"""
Test script to directly call OpenAI Usage API and see if it returns data
"""

import asyncio
import os
from datetime import datetime, timedelta
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

async def test_openai_usage_api():
    """Test direct OpenAI Usage API call"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return
        
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # OpenAI Usage API endpoint
    usage_endpoint = "https://api.openai.com/v1/usage"
    
    # Get dates for today and this month
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    print(f"\n📅 Testing usage for: {today}")
    
    # Test 1: Today's usage
    print("\n1️⃣ Testing today's usage...")
    params = {
        'date': today.isoformat(),
        'bucket_width': 'day'
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                usage_endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                params=params,
                timeout=30.0
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response structure: {list(data.keys())}")
                if 'data' in data:
                    print(f"   Data points: {len(data['data'])}")
                    if data['data']:
                        # Show first data point structure
                        first_point = data['data'][0]
                        print(f"   First data point keys: {list(first_point.keys())}")
                        print(f"   Sample data: {json.dumps(first_point, indent=2)[:500]}...")
                    else:
                        print("   ⚠️ No usage data points returned (might mean no usage today)")
                elif 'buckets' in data:
                    print(f"   Buckets: {len(data['buckets'])}")
                else:
                    print(f"   Raw response: {json.dumps(data, indent=2)[:500]}...")
            else:
                error_text = response.text[:500]
                print(f"   ❌ Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Current month usage
    print("\n2️⃣ Testing current month usage...")
    params = {
        'start_date': month_start.isoformat(),
        'end_date': today.isoformat(),
        'bucket_width': 'day'
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                usage_endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                params=params,
                timeout=30.0
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response structure: {list(data.keys())}")
                if 'data' in data:
                    print(f"   Data points: {len(data['data'])}")
                    total_cost = sum(point.get('total_cost', 0) for point in data['data'])
                    total_requests = sum(point.get('n_requests', 0) for point in data['data'])
                    print(f"   Total cost this month: ${total_cost:.4f}")
                    print(f"   Total requests: {total_requests}")
                elif 'buckets' in data:
                    print(f"   Buckets: {len(data['buckets'])}")
                else:
                    print(f"   Raw response: {json.dumps(data, indent=2)[:500]}...")
            else:
                error_text = response.text[:500]
                print(f"   ❌ Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Check what models we've been using
    print("\n3️⃣ Checking models used...")
    params = {
        'start_date': (today - timedelta(days=7)).isoformat(),
        'end_date': today.isoformat(),
        'bucket_width': 'day'
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                usage_endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                params=params,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    models = set()
                    for point in data['data']:
                        if 'model' in point:
                            models.add(point['model'])
                    if models:
                        print(f"   Models used: {', '.join(sorted(models))}")
                    else:
                        print("   No model information in data")
            else:
                print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    print("🧪 Testing OpenAI Usage API directly...")
    asyncio.run(test_openai_usage_api())