#!/usr/bin/env python3

import asyncio
import json
import uuid
import aiohttp

async def test_endpoints():
    """Test the newly added endpoints to verify they respond correctly"""
    
    # Use a random UUID to test empty workspace behavior
    test_workspace_id = str(uuid.uuid4())
    base_url = "http://localhost:8002"
    
    endpoints_to_test = [
        f"{base_url}/unified-assets/workspace/{test_workspace_id}",
        f"{base_url}/projects/{test_workspace_id}/deliverables",
        f"{base_url}/projects/{test_workspace_id}/insights",
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                print(f"\n🧪 Testing: {endpoint}")
                
                async with session.get(endpoint) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ SUCCESS: Got valid response")
                        print(f"Response type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())}")
                    elif response.status == 404:
                        text = await response.text()
                        print(f"❌ 404 ERROR: {text}")
                    else:
                        text = await response.text()
                        print(f"⚠️  Status {response.status}: {text}")
                        
            except Exception as e:
                print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())