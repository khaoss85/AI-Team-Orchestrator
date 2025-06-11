#!/usr/bin/env python3
"""
Test script for unified asset management system
Uses real workspace data from the database
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment manually if needed
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from database import supabase, list_tasks

# Real workspace ID found from the database
TEST_WORKSPACE_ID = "2d8d4059-aaee-4980-80c8-aa11269aa85d"

async def test_project_deliverables_endpoint():
    """Test the /projects/{workspace_id}/deliverables endpoint"""
    print("🧪 Testing Project Deliverables API Endpoint")
    print("=" * 60)
    
    try:
        # Import the endpoint function
        from routes.project_insights import get_project_deliverables
        
        # Test the endpoint with our real workspace
        print(f"📡 Testing with workspace: {TEST_WORKSPACE_ID}")
        
        # Call the endpoint function directly
        result = await get_project_deliverables(TEST_WORKSPACE_ID)
        
        print(f"✅ API Response received")
        print(f"📊 Response type: {type(result)}")
        
        if hasattr(result, 'status_code'):
            print(f"📈 Status code: {result.status_code}")
        
        # Try to get the response data
        if hasattr(result, 'body'):
            response_data = json.loads(result.body.decode())
        elif isinstance(result, dict):
            response_data = result
        else:
            response_data = str(result)
        
        print(f"📋 Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
        
        if isinstance(response_data, dict):
            # Check for deliverables
            deliverables = response_data.get('deliverables', [])
            print(f"🎯 Deliverables found: {len(deliverables)}")
            
            for i, deliverable in enumerate(deliverables[:3], 1):  # Show first 3
                print(f"\n📦 Deliverable {i}:")
                print(f"   Title: {deliverable.get('title', 'No title')}")
                print(f"   Summary: {deliverable.get('summary', 'No summary')[:100]}...")
                print(f"   Status: {deliverable.get('status', 'Unknown')}")
                print(f"   Assets: {len(deliverable.get('assets', []))}")
                
                # Check for rich content
                if 'rich_content' in deliverable:
                    rich_content = deliverable['rich_content']
                    print(f"   Rich content available:")
                    print(f"     - Tables: {len(rich_content.get('tables', []))}")
                    print(f"     - Cards: {len(rich_content.get('cards', []))}")
                    print(f"     - Metrics: {len(rich_content.get('metrics', []))}")
                    print(f"     - Visual summary: {'Yes' if rich_content.get('visual_summary') else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_asset_management_api():
    """Test the asset management API"""
    print("\n🧪 Testing Asset Management API")
    print("=" * 60)
    
    try:
        # Import the asset management functions
        from routes.asset_management import get_workspace_assets, get_asset_details
        
        print(f"📡 Testing get_workspace_assets with workspace: {TEST_WORKSPACE_ID}")
        
        # Test getting workspace assets
        assets_result = await get_workspace_assets(TEST_WORKSPACE_ID)
        print(f"✅ Workspace assets response received")
        
        # Parse the response
        if hasattr(assets_result, 'body'):
            assets_data = json.loads(assets_result.body.decode())
        elif isinstance(assets_result, dict):
            assets_data = assets_result
        else:
            assets_data = {"assets": []}
        
        assets = assets_data.get('assets', [])
        print(f"🎯 Assets found: {len(assets)}")
        
        if assets:
            # Test getting details for the first asset
            first_asset = assets[0]
            asset_id = first_asset.get('id')
            
            if asset_id:
                print(f"\n📋 Testing get_asset_details for asset: {asset_id}")
                
                asset_details = await get_asset_details(asset_id)
                print(f"✅ Asset details response received")
                
                # Parse asset details
                if hasattr(asset_details, 'body'):
                    details_data = json.loads(asset_details.body.decode())
                elif isinstance(asset_details, dict):
                    details_data = asset_details
                else:
                    details_data = {}
                
                print(f"📊 Asset details keys: {list(details_data.keys()) if isinstance(details_data, dict) else 'Not a dict'}")
                
                if isinstance(details_data, dict):
                    asset_info = details_data.get('asset', {})
                    print(f"   Name: {asset_info.get('name', 'Unknown')}")
                    print(f"   Type: {asset_info.get('type', 'Unknown')}")
                    print(f"   Ready to use: {asset_info.get('ready_to_use', False)}")
                    print(f"   Actionability score: {asset_info.get('actionability_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Asset management API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_queries():
    """Test direct database queries for deliverables"""
    print("\n🧪 Testing Database Queries")
    print("=" * 60)
    
    try:
        # Get all tasks for the workspace
        all_tasks = await list_tasks(TEST_WORKSPACE_ID)
        print(f"📊 Total tasks in workspace: {len(all_tasks)}")
        
        # Find intelligent AI deliverable tasks
        intelligent_deliverable_tasks = [
            task for task in all_tasks 
            if task.get('creation_type') == 'intelligent_ai_deliverable'
        ]
        
        print(f"🤖 Intelligent AI deliverable tasks: {len(intelligent_deliverable_tasks)}")
        
        for task in intelligent_deliverable_tasks:
            print(f"\n📋 Task: {task.get('name', 'Unnamed')}")
            print(f"   ID: {task.get('id')}")
            print(f"   Status: {task.get('status')}")
            print(f"   Created: {task.get('created_at')}")
            
            # Check result payload
            result = task.get('result', {})
            if isinstance(result, dict):
                print(f"   Has result payload: Yes")
                print(f"   Result keys: {list(result.keys())}")
                
                # Check for detailed results
                if 'detailed_results_json' in result:
                    detailed_results = result['detailed_results_json']
                    if isinstance(detailed_results, dict):
                        print(f"   Detailed results keys: {list(detailed_results.keys())}")
                        
                        # Look for rich content indicators
                        for key, value in detailed_results.items():
                            if isinstance(value, list) and len(value) > 0:
                                print(f"     - {key}: {len(value)} items")
                            elif isinstance(value, dict):
                                print(f"     - {key}: dict with {len(value)} keys")
            else:
                print(f"   Has result payload: No")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_markup_processing():
    """Test markup processing with sample data"""
    print("\n🧪 Testing Markup Processing")
    print("=" * 60)
    
    try:
        from deliverable_system.markup_processor import DeliverableMarkupProcessor
        
        # Sample data that should contain rich content
        sample_data = {
            "email_sequences": [
                {
                    "sequence_name": "Welcome Series",
                    "total_emails": 5,
                    "open_rate_target": "30%",
                    "click_rate_target": "10%"
                },
                {
                    "sequence_name": "Product Demo",
                    "total_emails": 3,
                    "open_rate_target": "35%", 
                    "click_rate_target": "12%"
                }
            ],
            "target_metrics": {
                "contacts_to_collect": 50,
                "target_open_rate": "≥30%",
                "target_click_rate": "≥10%",
                "timeline": "6 weeks"
            },
            "key_insights": [
                "Focus on CMO/CTO personas for European SaaS companies",
                "Optimize subject lines for higher open rates",
                "Implement A/B testing for email content"
            ]
        }
        
        processor = DeliverableMarkupProcessor()
        processed = processor.process_deliverable_content(sample_data)
        
        print(f"✅ Markup processing completed")
        print(f"📊 Processing results:")
        print(f"   Has structured content: {processed.get('has_structured_content', False)}")
        print(f"   Tables detected: {len(processed.get('tables', []))}")
        print(f"   Cards detected: {len(processed.get('cards', []))}")
        print(f"   Metrics detected: {len(processed.get('metrics', []))}")
        print(f"   Has visual summary: {'Yes' if processed.get('visual_summary') else 'No'}")
        
        if processed.get('visual_summary'):
            print(f"\n✨ Visual Summary:")
            print(f"   {processed['visual_summary']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Markup processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all unified asset management tests"""
    print("🚀 UNIFIED ASSET MANAGEMENT SYSTEM TEST")
    print("=" * 80)
    print(f"📍 Test workspace: {TEST_WORKSPACE_ID}")
    print(f"📅 Test date: {os.popen('date').read().strip()}")
    print()
    
    tests = [
        ("Database Queries", test_database_queries),
        ("Markup Processing", test_markup_processing),
        ("Project Deliverables API", test_project_deliverables_endpoint),
        ("Asset Management API", test_asset_management_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}\n")
    
    # Final summary
    print("=" * 80)
    print(f"📊 TEST SUMMARY")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Unified asset management system is working.")
        print("\n📋 You can now use this workspace for testing:")
        print(f"   Workspace ID: {TEST_WORKSPACE_ID}")
        print(f"   API URL: http://localhost:8000/projects/{TEST_WORKSPACE_ID}/deliverables")
        print(f"   Frontend URL: http://localhost:3000/projects/{TEST_WORKSPACE_ID}/deliverables")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)