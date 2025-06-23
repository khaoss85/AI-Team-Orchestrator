#!/usr/bin/env python3
"""
Test script to verify asset versioning display in the frontend
Creates a workspace with mock unified assets data to test the UI
"""

import asyncio
import json
from uuid import uuid4
from datetime import datetime, timedelta
from database import create_workspace, create_task, update_task_fields, supabase
from models import TaskStatus, WorkspaceStatus

async def test_asset_versioning_display():
    """Test asset versioning display with mock data"""
    
    # Create test workspace
    workspace_data = {
        "name": "Asset Versioning UI Test",
        "description": "Testing asset versioning display in frontend",
        "user_id": str(uuid4()),
        "goal": "Develop comprehensive Instagram growth strategy for fitness influencers"
    }
    
    print(f"🚀 Creating test workspace...")
    workspace = await create_workspace(**workspace_data)
    workspace_id = workspace['id']
    print(f"✅ Created workspace: {workspace_id}")
    
    # Create multiple tasks that represent different versions
    tasks = []
    
    # Task 1: Initial content strategy
    task1 = await create_task(
        workspace_id=workspace_id,
        name="Create Initial Content Strategy",
        description="Develop initial content strategy for Instagram",
        status=TaskStatus.PENDING.value,
        assigned_to_role="Content Strategist"
    )
    await update_task_fields(task1['id'], {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Initial content strategy document created",
            "data": {
                "type": "content_strategy",
                "content": "Basic content strategy outline"
            }
        }
    })
    tasks.append(task1)
    
    # Task 2: Enhanced version
    task2 = await create_task(
        workspace_id=workspace_id,
        name="Enhance Content Strategy - Asset 2",
        description="Enhanced version with competitor analysis",
        status=TaskStatus.PENDING.value,
        assigned_to_role="Senior Strategist"
    )
    await update_task_fields(task2['id'], {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Enhanced content strategy with competitor insights",
            "data": {
                "type": "content_strategy",
                "content": "Enhanced strategy with detailed analysis"
            }
        },
        "iteration_count": 2
    })
    tasks.append(task2)
    
    # Task 3: Final version
    task3 = await create_task(
        workspace_id=workspace_id,
        name="Finalize Content Strategy - Asset 3",
        description="Final comprehensive version",
        status=TaskStatus.PENDING.value,
        assigned_to_role="Expert Consultant"
    )
    await update_task_fields(task3['id'], {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Comprehensive content strategy with full implementation plan",
            "data": {
                "type": "content_strategy",
                "content": "Complete strategy with 90-day roadmap"
            }
        },
        "iteration_count": 3
    })
    tasks.append(task3)
    
    # Also create a contact database asset with versions
    contact1 = await create_task(
        workspace_id=workspace_id,
        name="Build Initial Contact Database",
        description="Create initial ICP contact list",
        status=TaskStatus.PENDING.value,
        assigned_to_role="Research Analyst"
    )
    await update_task_fields(contact1['id'], {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Initial contact database with 50 leads",
            "data": {
                "type": "contact_database",
                "contacts": [
                    {"name": "John Doe", "role": "Fitness Coach", "followers": "125K"},
                    {"name": "Jane Smith", "role": "Nutritionist", "followers": "89K"}
                ]
            }
        }
    })
    tasks.append(contact1)
    
    # Enhanced contact database
    contact2 = await create_task(
        workspace_id=workspace_id,
        name="Expand Contact Database - Enhanced Asset",
        description="Expand database with more qualified leads",
        status=TaskStatus.PENDING.value,
        assigned_to_role="Senior Research Lead"
    )
    await update_task_fields(contact2['id'], {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Expanded contact database with 150 qualified leads",
            "data": {
                "type": "contact_database",
                "contacts": [
                    {"name": "Mike Johnson", "role": "Bodybuilding Coach", "followers": "250K"},
                    {"name": "Sarah Williams", "role": "Fitness Influencer", "followers": "500K"},
                    {"name": "Chris Brown", "role": "Gym Owner", "followers": "75K"}
                ]
            }
        },
        "iteration_count": 2
    })
    tasks.append(contact2)
    
    print(f"\n✅ Created {len(tasks)} tasks representing different asset versions")
    print(f"\n📊 Summary:")
    print(f"   - Content Strategy: 3 versions")
    print(f"   - Contact Database: 2 versions")
    
    # Optionally, directly insert mock unified assets response for testing
    print(f"\n💡 Testing unified assets endpoint...")
    
    # Make a request to the unified assets endpoint
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8000/unified-assets/workspace/{workspace_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Unified assets response:")
                print(f"   - Total assets: {data.get('asset_count', 0)}")
                print(f"   - Total versions: {data.get('total_versions', 0)}")
                
                # Display asset details
                for asset_id, asset in data.get('assets', {}).items():
                    print(f"\n   📦 {asset.get('name', 'Unknown Asset')}")
                    print(f"      Type: {asset.get('type', 'unknown')}")
                    print(f"      Versions: {asset.get('versions', 1)}")
                    print(f"      Ready: {asset.get('ready_to_use', False)}")
                    
                    # Check version history
                    if 'version_history' in asset:
                        print(f"      History: {len(asset['version_history'])} entries")
                    
                    # Check related tasks
                    if 'related_tasks' in asset:
                        print(f"      Related Tasks: {len(asset['related_tasks'])}")
                        for task in asset['related_tasks'][:3]:
                            print(f"         - v{task.get('version', 1)}: {task.get('name', 'Unknown')}")
            else:
                print(f"\n❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"\n❌ Error calling API: {e}")
    
    return workspace_id

if __name__ == "__main__":
    workspace_id = asyncio.run(test_asset_versioning_display())
    
    print(f"\n🎉 Test complete!")
    print(f"📌 Workspace ID: {workspace_id}")
    print(f"🌐 View in browser: http://localhost:3000/projects/{workspace_id}/assets")
    print(f"\n🔍 Expected behavior:")
    print(f"   1. Assets page should show 2 assets (Content Strategy, Contact Database)")
    print(f"   2. Content Strategy should show 'v3' badge")
    print(f"   3. Contact Database should show 'v2' badge")
    print(f"   4. Clicking 'Version History' tab should show AssetHistoryPanel")
    print(f"   5. History should display all versions with comparison capability")