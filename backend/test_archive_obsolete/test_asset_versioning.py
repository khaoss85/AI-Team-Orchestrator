#!/usr/bin/env python3
"""
Test script to verify asset versioning/history system
"""

import asyncio
import json
from uuid import uuid4
from datetime import datetime
from database import create_workspace, create_task, get_workspace
from models import TaskStatus, WorkspaceStatus
from routes.unified_assets import unified_asset_manager

async def test_asset_versioning():
    """Test asset versioning functionality"""
    
    # Create test workspace
    workspace_data = {
        "name": "Test Asset Versioning Workspace",
        "description": "Testing asset versioning and history system",
        "user_id": str(uuid4()),  # Valid UUID for user_id
        "goal": "Test asset versioning and history system"
    }
    
    print(f"🚀 Creating test workspace...")
    workspace = await create_workspace(**workspace_data)
    workspace_id = workspace['id']
    print(f"✅ Created workspace: {workspace_id}")
    
    # Import update_task function
    from database import update_task_fields
    
    # Create tasks that simulate asset versions
    # Version 1: Initial asset
    task1_data = {
        "workspace_id": workspace_id,
        "name": "Create Content Strategy Document",
        "description": "Initial content strategy for Instagram growth",
        "status": TaskStatus.PENDING.value,
        "assigned_to_role": "Content Strategist",
        "priority": "high"
    }
    
    print("📝 Creating version 1 task...")
    task1 = await create_task(**task1_data)
    task1_id = task1['id']
    
    # Update task to completed with result
    await update_task_fields(task1_id, {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Initial content strategy covering audience analysis, content pillars, and posting schedule",
            "data": {
                "type": "content_strategy",
                "content": {
                    "audience_analysis": "Target audience: Male bodybuilders aged 25-40",
                    "content_pillars": ["Workout tips", "Nutrition advice", "Transformation stories"],
                    "posting_schedule": "3x daily at peak engagement hours"
                }
            }
        },
        "iteration_count": 1
    })
    
    # Version 2: Enhanced version
    task2_data = {
        "workspace_id": workspace_id,
        "name": "Enhanced Content Strategy - Asset 2",
        "description": "Enhanced version with competitive analysis and engagement tactics",
        "status": TaskStatus.PENDING.value,
        "assigned_to_role": "Senior Strategy Analyst",
        "priority": "high"
    }
    
    print("📝 Creating version 2 task...")
    task2 = await create_task(**task2_data)
    task2_id = task2['id']
    
    # Update task to completed with result
    await update_task_fields(task2_id, {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Enhanced content strategy with competitor insights and advanced growth tactics",
            "data": {
                "type": "content_strategy",
                "content": {
                    "audience_analysis": "Refined target: Male bodybuilders 25-40, focusing on intermediate to advanced",
                    "content_pillars": ["Advanced techniques", "Science-based nutrition", "Mental training", "Community stories"],
                    "posting_schedule": "4x daily with story updates",
                    "competitor_analysis": "Analysis of top 10 fitness influencers",
                    "engagement_tactics": "Comment pods, strategic hashtags, user-generated content"
                }
            }
        },
        "iteration_count": 2
    })
    
    # Version 3: Final comprehensive version
    task3_data = {
        "workspace_id": workspace_id,
        "name": "Final Comprehensive Strategy - Asset 3",
        "description": "Final version with full implementation roadmap",
        "status": TaskStatus.PENDING.value,
        "assigned_to_role": "Expert Strategy Consultant",
        "priority": "high"
    }
    
    print("📝 Creating version 3 task...")
    task3 = await create_task(**task3_data)
    task3_id = task3['id']
    
    # Update task to completed with result
    await update_task_fields(task3_id, {
        "status": TaskStatus.COMPLETED.value,
        "result": {
            "summary": "Comprehensive content strategy with 90-day implementation roadmap and KPIs",
            "data": {
                "type": "content_strategy",
                "content": {
                    "executive_summary": "Data-driven strategy to achieve 200+ weekly followers",
                    "audience_analysis": "Detailed psychographic and demographic analysis",
                    "content_pillars": ["Educational content", "Inspirational stories", "Community features", "Product reviews", "Live Q&A"],
                    "content_calendar": "30-day detailed calendar with themes and hooks",
                    "posting_schedule": "Optimized schedule based on analytics: 7am, 12pm, 5pm, 8pm",
                    "competitor_analysis": "SWOT analysis of 15 competitors with gap opportunities",
                    "engagement_tactics": "Multi-channel engagement strategy",
                    "kpis": ["Follower growth rate", "Engagement rate", "Story views", "Link clicks"],
                    "implementation_roadmap": "Week-by-week action plan for first 90 days"
                }
            }
        },
        "iteration_count": 3
    })
    
    # Test the unified assets endpoint
    print("\n🔍 Testing unified assets extraction...")
    assets_response = await unified_asset_manager.get_workspace_assets(workspace_id)
    
    print(f"\n✅ Asset extraction complete!")
    print(f"📊 Total assets: {assets_response['asset_count']}")
    print(f"📈 Total versions: {assets_response['total_versions']}")
    
    # Display asset details
    for asset_id, asset in assets_response['assets'].items():
        print(f"\n🎯 Asset: {asset['name']}")
        print(f"   Type: {asset['type']}")
        print(f"   Versions: {asset['versions']}")
        print(f"   Ready to use: {asset.get('ready_to_use', False)}")
        
        # Show version history
        if 'version_history' in asset:
            print(f"   📜 Version History:")
            for version in asset['version_history']:
                print(f"      - {version['version']} by {version['created_by']}")
                print(f"        {version['changes_summary']}")
        
        # Show related tasks
        if 'related_tasks' in asset:
            print(f"   🔗 Related Tasks: {len(asset['related_tasks'])}")
            for task in asset['related_tasks']:
                print(f"      - v{task['version']}: {task['name']}")
    
    return workspace_id, assets_response

if __name__ == "__main__":
    workspace_id, result = asyncio.run(test_asset_versioning())
    
    print(f"\n🎉 Test complete!")
    print(f"📌 Workspace ID: {workspace_id}")
    print(f"🌐 View in browser: http://localhost:3000/projects/{workspace_id}/assets")
    print(f"\n💡 The asset versioning system should show:")
    print(f"   - Single grouped asset (Content Strategy)")
    print(f"   - 3 versions (v1.0, v2.0, v3.0)")
    print(f"   - Version comparison capability")
    print(f"   - Quality score improvements across versions")