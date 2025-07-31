#!/usr/bin/env python3
"""
Approve team and monitor real workspace progress
"""

import requests
import asyncio
import time
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase, list_tasks, get_deliverables

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def approve_team():
    workspace_id = "35241c49-6b11-487a-80d8-4583ea50f60c"
    proposal_id = "f4e52559-77fb-4227-9b6e-d311fb9ea991"
    
    print("✅ Approving team proposal...")
    response = requests.post(f"{API_BASE}/director/approve/{workspace_id}?proposal_id={proposal_id}")
    print(f"Approval response: {response.status_code}")
    if response.status_code not in [200, 204]:
        print(f"❌ Approval failed: {response.text}")
        return False
    
    print("✅ Team approved! Autonomous system should start working...")
    return True

async def monitor_workspace_progress():
    workspace_id = "35241c49-6b11-487a-80d8-4583ea50f60c"
    
    print("\n🔍 MONITORING REAL WORKSPACE PROGRESS")
    print("="*80)
    print(f"Workspace: {workspace_id}")
    print("Focus: AI-driven system producing real contact data vs methodologies")
    print("="*80)
    
    start_time = time.time()
    max_wait_time = 600  # 10 minutes
    
    last_task_count = 0
    last_deliverable_count = 0
    
    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)
        
        # Check agents
        agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
        agents = agents_response.data if agents_response.data else []
        
        # Check tasks
        tasks = await list_tasks(workspace_id)
        task_count = len(tasks) if tasks else 0
        
        # Check deliverables
        deliverables = await get_deliverables(workspace_id)
        deliverable_count = len(deliverables) if deliverables else 0
        
        # Check task status breakdown
        task_statuses = {}
        if tasks:
            for task in tasks:
                status = task.get('status', 'unknown')
                task_statuses[status] = task_statuses.get(status, 0) + 1
        
        # Print progress update
        if task_count != last_task_count or deliverable_count != last_deliverable_count:
            print(f"\n⏰ {elapsed}s - PROGRESS UPDATE:")
            print(f"   👥 Agents: {len(agents)}")
            print(f"   📋 Tasks: {task_count} {dict(task_statuses) if task_statuses else ''}")
            print(f"   📦 Deliverables: {deliverable_count}")
            
            # Show task details
            if tasks:
                for task in tasks[:3]:  # Show first 3 tasks
                    status = task.get('status', 'unknown')
                    name = task.get('name', 'No name')[:50]
                    print(f"      - {name}... [{status}]")
            
            last_task_count = task_count
            last_deliverable_count = deliverable_count
        
        # Check for deliverables with substantial content
        if deliverables:
            for deliverable in deliverables:
                content = deliverable.get('content', '')
                if content and len(content) > 200:
                    print(f"\n🎯 DELIVERABLE WITH CONTENT FOUND!")
                    print(f"   Type: {deliverable.get('type', 'Unknown')}")
                    print(f"   Content length: {len(content)} characters")
                    print(f"   Preview: {content[:300]}...")
                    
                    # Analyze content for real vs methodology
                    content_lower = content.lower()
                    has_emails = '@' in content and '.com' in content
                    has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco'])
                    has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'how to', 'you can use'])
                    
                    print(f"   📊 CONTENT ANALYSIS:")
                    print(f"      Has emails: {has_emails}")
                    print(f"      Has names: {has_names}")
                    print(f"      Has methodology: {has_methodology}")
                    
                    if has_emails and has_names and not has_methodology:
                        print(f"   ✅ APPEARS TO BE REAL CONTACT DATA!")
                        return {
                            'success': True,
                            'real_data_found': True,
                            'deliverable': deliverable,
                            'elapsed_time': elapsed
                        }
                    elif has_methodology:
                        print(f"   ❌ APPEARS TO BE METHODOLOGY/STRATEGY")
                        # Continue monitoring for better results
        
        # Check for needs_revision tasks (AI validation working)
        needs_revision_count = task_statuses.get('needs_revision', 0)
        if needs_revision_count > 0:
            print(f"   🧠 AI VALIDATION: {needs_revision_count} tasks need revision (AI detected methodology vs data)")
        
        await asyncio.sleep(15)  # Check every 15 seconds
    
    print(f"\n⏰ MONITORING COMPLETED ({max_wait_time}s)")
    
    # Final analysis
    final_tasks = await list_tasks(workspace_id)
    final_deliverables = await get_deliverables(workspace_id)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Tasks: {len(final_tasks) if final_tasks else 0}")
    print(f"   Deliverables: {len(final_deliverables) if final_deliverables else 0}")
    
    # Analyze final state
    real_data_found = False
    ai_validation_working = False
    
    if final_tasks:
        status_counts = {}
        for task in final_tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"   Task statuses: {dict(status_counts)}")
        
        if status_counts.get('needs_revision', 0) > 0:
            ai_validation_working = True
            print(f"   ✅ AI validation is working (tasks marked for revision)")
    
    if final_deliverables:
        for deliverable in final_deliverables:
            content = deliverable.get('content', '')
            if content:
                content_lower = content.lower()
                has_emails = '@' in content and '.com' in content
                has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa'])
                has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'how to'])
                
                if has_emails and has_names and not has_methodology:
                    real_data_found = True
                    break
    
    return {
        'success': len(final_tasks) > 0 or len(final_deliverables) > 0,
        'real_data_found': real_data_found,
        'ai_validation_working': ai_validation_working,
        'task_count': len(final_tasks) if final_tasks else 0,
        'deliverable_count': len(final_deliverables) if final_deliverables else 0
    }

async def main():
    print("🎯 REAL PRODUCTION WORKSPACE TEST")
    print("="*80)
    print("Testing AI-driven system with actual user-created workspace")
    print("Focus: Verify system produces real contact data, not methodologies")
    print("="*80)
    
    # Step 1: Approve team
    if not approve_team():
        print("❌ Team approval failed")
        return
    
    # Step 2: Monitor progress
    results = await monitor_workspace_progress()
    
    # Step 3: Final verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT: REAL PRODUCTION TEST")
    print("="*80)
    
    success = results.get('success', False)
    real_data = results.get('real_data_found', False)
    ai_validation = results.get('ai_validation_working', False)
    
    print(f"✅ System activated: {'YES' if success else 'NO'}")
    print(f"✅ Real contact data found: {'YES' if real_data else 'NO'}")
    print(f"✅ AI validation working: {'YES' if ai_validation else 'NO'}")
    print(f"📊 Tasks created: {results.get('task_count', 0)}")
    print(f"📦 Deliverables created: {results.get('deliverable_count', 0)}")
    
    if success and real_data and ai_validation:
        print(f"\n🎉 OVERALL RESULT: ✅ SUCCESS")
        print("   The AI-driven system is working correctly in real production!")
        print("   System produces actual contact data instead of methodologies")
        print("   AI validation prevents methodology content from being accepted")
    elif success and ai_validation:
        print(f"\n🔄 OVERALL RESULT: ⚡ SYSTEM WORKING")
        print("   The AI-driven system is actively working and validating content")
        print("   Quality control is functioning (tasks being revised)")
        print("   Real data may be generated in next iterations")
    else:
        print(f"\n❌ OVERALL RESULT: NEEDS INVESTIGATION")
        print("   System may need further configuration or debugging")

if __name__ == "__main__":
    asyncio.run(main())