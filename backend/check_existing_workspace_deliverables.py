#!/usr/bin/env python3
"""
🔍 CHECK EXISTING WORKSPACE DELIVERABLES

Controlla il workspace 53e4edfc-6dc9-47f6-96b7-35668591ed5d e tutti i suoi deliverable
per vedere il contenuto reale che è stato generato dal sistema AI-driven.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from database import (
    get_workspace, 
    get_deliverables, 
    list_tasks, 
    supabase
)

async def check_workspace_deliverables():
    """Check workspace and show all deliverable content"""
    
    workspace_id = "53e4edfc-6dc9-47f6-96b7-35668591ed5d"
    
    print("🔍 CHECKING EXISTING WORKSPACE DELIVERABLES")
    print("="*80)
    print(f"Workspace ID: {workspace_id}")
    print("="*80)
    
    try:
        # 1. Get workspace info
        print("\n📋 WORKSPACE INFO:")
        workspace = await get_workspace(workspace_id)
        if workspace:
            print(f"   Name: {workspace.get('name', 'N/A')}")
            print(f"   Goal: {workspace.get('goal', 'N/A')}")
            print(f"   Status: {workspace.get('status', 'N/A')}")
            print(f"   Created: {workspace.get('created_at', 'N/A')}")
        else:
            print("   ❌ Workspace not found")
            return
        
        # 2. Get agents
        print("\n👥 AGENTS:")
        try:
            agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
            agents = agents_response.data if agents_response.data else []
            print(f"   Total agents: {len(agents)}")
            if agents:
                for agent in agents:
                    print(f"   - {agent.get('name', 'N/A')} ({agent.get('role', 'N/A')}) - {agent.get('status', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Error getting agents: {e}")
            agents = []
        
        # 3. Get tasks
        print("\n📋 TASKS:")
        tasks = await list_tasks(workspace_id)
        print(f"   Total tasks: {len(tasks) if tasks else 0}")
        
        task_status_counts = {}
        if tasks:
            for task in tasks:
                status = task.get('status', 'unknown')
                task_status_counts[status] = task_status_counts.get(status, 0) + 1
                print(f"   - {task.get('name', 'N/A')[:50]}... [{status}]")
        
        print(f"   Status breakdown: {dict(task_status_counts)}")
        
        # 4. Get deliverables - THIS IS THE KEY PART
        print("\n📦 DELIVERABLES (REAL CONTENT):")
        deliverables = await get_deliverables(workspace_id)
        print(f"   Total deliverables: {len(deliverables) if deliverables else 0}")
        
        if deliverables:
            for i, deliverable in enumerate(deliverables, 1):
                print(f"\n   🎯 DELIVERABLE {i}:")
                print(f"      ID: {deliverable.get('id', 'N/A')}")
                print(f"      Type: {deliverable.get('type', 'N/A')}")
                print(f"      Status: {deliverable.get('status', 'N/A')}")
                print(f"      Created: {deliverable.get('created_at', 'N/A')}")
                
                # THIS IS THE CRITICAL PART - ACTUAL CONTENT
                content = deliverable.get('content', '')
                if content:
                    print(f"      📄 CONTENT LENGTH: {len(content)} characters")
                    print(f"      📄 CONTENT PREVIEW (first 300 chars):")
                    print(f"         {content[:300]}...")
                    
                    # Check if content looks like real data or methodology
                    content_lower = content.lower()
                    has_emails = '@' in content and '.com' in content
                    has_names = any(word in content_lower for word in ['john', 'sarah', 'mike', 'lisa', 'david', 'jane'])
                    has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'you can use', 'how to'])
                    
                    print(f"      🔍 CONTENT ANALYSIS:")
                    print(f"         Has emails: {has_emails}")
                    print(f"         Has names: {has_names}")
                    print(f"         Has methodology language: {has_methodology}")
                    
                    if has_emails and has_names:
                        print(f"         ✅ APPEARS TO BE REAL CONTACT DATA")
                    elif has_methodology:
                        print(f"         ❌ APPEARS TO BE METHODOLOGY/STRATEGY")
                    else:
                        print(f"         ⚠️  CONTENT TYPE UNCLEAR")
                else:
                    print(f"      ❌ NO CONTENT FOUND")
                
                # Check assets if any
                assets = deliverable.get('assets', [])
                if assets:
                    print(f"      📎 ASSETS: {len(assets)} files")
                    for asset in assets:
                        print(f"         - {asset.get('name', 'N/A')} ({asset.get('type', 'N/A')})")
        else:
            print("   ❌ No deliverables found")
        
        # 5. Direct database query for assets/artifacts
        print("\n📎 DIRECT ASSET CHECK:")
        try:
            assets_response = supabase.table("assets").select("*").eq("workspace_id", workspace_id).execute()
            if assets_response.data:
                print(f"   Found {len(assets_response.data)} assets in database")
                for asset in assets_response.data:
                    print(f"   - {asset.get('name', 'N/A')} ({asset.get('type', 'N/A')}) - {len(asset.get('content', ''))} chars")
                    
                    # Show asset content
                    asset_content = asset.get('content', '')
                    if asset_content:
                        print(f"     Content preview: {asset_content[:200]}...")
            else:
                print("   No assets found in database")
        except Exception as e:
            print(f"   ❌ Error checking assets: {e}")
        
        # 6. Summary
        print("\n" + "="*80)
        print("📊 SUMMARY:")
        print(f"   Workspace: {'✅ Found' if workspace else '❌ Not found'}")
        print(f"   Agents: {len(agents) if agents else 0}")
        print(f"   Tasks: {len(tasks) if tasks else 0}")
        print(f"   Deliverables: {len(deliverables) if deliverables else 0}")
        
        if deliverables:
            real_data_count = 0
            methodology_count = 0
            for deliverable in deliverables:
                content = deliverable.get('content', '').lower()
                if '@' in content and any(name in content for name in ['john', 'sarah', 'mike']):
                    real_data_count += 1
                elif any(word in content for word in ['strategy', 'approach', 'how to']):
                    methodology_count += 1
            
            print(f"   Real data deliverables: {real_data_count}")
            print(f"   Methodology deliverables: {methodology_count}")
            
            if real_data_count > 0:
                print("   ✅ SYSTEM APPEARS TO BE PRODUCING REAL BUSINESS DATA")
            else:
                print("   ❌ SYSTEM APPEARS TO BE PRODUCING ONLY METHODOLOGIES")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error checking workspace: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_workspace_deliverables())