#!/usr/bin/env python3
"""Test unified assets API directly."""

import requests
import json
import sys

WORKSPACE_ID = "2d8d4059-aaee-4980-80c8-aa11269aa85d"
API_BASE = "http://localhost:8000"

def test_unified_assets_api():
    """Test the unified assets API endpoint."""
    
    url = f"{API_BASE}/unified-assets/workspace/{WORKSPACE_ID}"
    
    print(f"Testing unified assets API: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse data:")
            print(f"- workspace_id: {data.get('workspace_id')}")
            print(f"- asset_count: {data.get('asset_count')}")
            print(f"- total_versions: {data.get('total_versions')}")
            print(f"- data_source: {data.get('data_source')}")
            
            if 'assets' in data:
                print(f"- assets: {list(data['assets'].keys())}")
                for asset_key, asset_data in list(data['assets'].items())[:3]:  # Show first 3
                    print(f"  - {asset_key}: {asset_data.get('type', 'unknown')} - ready: {asset_data.get('ready_to_use', False)}")
            else:
                print("- No 'assets' key in response")
                
            return data
        else:
            print(f"Error response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API. Is the backend running on localhost:8000?")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_monitoring_asset_tracking():
    """Test the old monitoring asset tracking endpoint for comparison."""
    
    url = f"{API_BASE}/monitoring/workspace/{WORKSPACE_ID}/asset-tracking"
    
    print(f"\nTesting monitoring asset tracking: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data:")
            print(f"- total_assets_found: {data.get('asset_summary', {}).get('total_assets_found', 0)}")
            print(f"- completed_asset_tasks: {data.get('asset_summary', {}).get('completed_asset_tasks', 0)}")
            print(f"- extracted_assets: {len(data.get('extracted_assets', {}))}")
            
            if 'extracted_assets' in data:
                print(f"- asset keys: {list(data['extracted_assets'].keys())[:5]}")  # Show first 5
                
            return data
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    print(f"Testing APIs for workspace: {WORKSPACE_ID}\n")
    
    # Test unified assets API
    unified_result = test_unified_assets_api()
    
    # Test old monitoring API for comparison
    monitoring_result = test_monitoring_asset_tracking()
    
    print(f"\n=== Summary ===")
    if unified_result:
        print(f"Unified API: {unified_result.get('asset_count', 0)} assets")
    else:
        print("Unified API: FAILED")
        
    if monitoring_result:
        print(f"Monitoring API: {monitoring_result.get('asset_summary', {}).get('total_assets_found', 0)} assets")
    else:
        print("Monitoring API: FAILED")