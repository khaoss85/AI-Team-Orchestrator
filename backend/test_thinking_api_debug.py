#!/usr/bin/env python3
"""
Debug script for thinking API endpoint
Tests the endpoint and provides detailed debugging information
"""

import requests
import json
from uuid import UUID

def test_thinking_api():
    """Test the thinking API endpoint with various scenarios"""
    
    # Test workspace ID
    workspace_id = "550e8400-e29b-41d4-a716-446655440000"
    base_url = "http://localhost:8000"
    endpoint = f"/api/thinking/workspace/{workspace_id}"
    
    print("=" * 60)
    print("THINKING API DEBUG TEST")
    print("=" * 60)
    
    # Test 1: Direct API call
    print("\n1. Testing direct API call:")
    print(f"   URL: {base_url}{endpoint}?limit=10")
    
    try:
        response = requests.get(f"{base_url}{endpoint}", params={"limit": 10})
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: CORS headers check
    print("\n2. Testing CORS headers (simulating browser request):")
    headers = {
        "Origin": "http://localhost:3000",
        "Referer": "http://localhost:3000/",
        "User-Agent": "Mozilla/5.0 (Browser simulation)"
    }
    
    try:
        response = requests.options(f"{base_url}{endpoint}", headers=headers)
        print(f"   Preflight Status: {response.status_code}")
        print(f"   CORS Headers:")
        for header in ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", 
                      "Access-Control-Allow-Headers", "Access-Control-Allow-Credentials"]:
            if header in response.headers:
                print(f"     {header}: {response.headers[header]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Actual request with CORS headers
    print("\n3. Testing actual request with browser-like headers:")
    
    try:
        response = requests.get(f"{base_url}{endpoint}", 
                               params={"limit": 10},
                               headers=headers)
        print(f"   Status: {response.status_code}")
        
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"   CORS Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
        
        if response.status_code == 200:
            print("   ✅ Request successful!")
        else:
            print(f"   ❌ Request failed: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 4: Check if the service is running
    print("\n4. Testing health endpoint:")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Health Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Health Response: {response.json()}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 60)
    print("DEBUGGING SUGGESTIONS:")
    print("=" * 60)
    print("""
1. If CORS headers are missing, check backend/main.py CORS configuration
2. If preflight fails, ensure OPTIONS method is allowed
3. If the endpoint returns 404, check router registration in main.py
4. If connection refused, ensure backend is running on port 8000
5. Check browser console for specific error messages
6. Use browser Network tab to inspect actual requests/responses
    """)

if __name__ == "__main__":
    test_thinking_api()