#!/usr/bin/env python3
"""
Quick check of real workspace status
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase, list_tasks, get_deliverables

async def check_now():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"🔍 REAL WORKSPACE STATUS CHECK")
    print(f"Workspace: {workspace_id}")
    print("="*60)
    
    # Check agents
    agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
    agents = agents_response.data if agents_response.data else []
    print(f"👥 AGENTS: {len(agents)}")
    for agent in agents:
        print(f"   - {agent.get('name')} ({agent.get('role')}) - {agent.get('status')}")
    
    # Check tasks
    tasks = await list_tasks(workspace_id)
    print(f"\n📋 TASKS: {len(tasks) if tasks else 0}")
    
    task_statuses = {}
    if tasks:
        for task in tasks:
            status = task.get('status', 'unknown')
            task_statuses[status] = task_statuses.get(status, 0) + 1
            name = task.get('name', 'No name')[:60]
            print(f"   - {name}... [{status}]")
    
    print(f"   Status breakdown: {dict(task_statuses) if task_statuses else 'None'}")
    
    # Check deliverables with content analysis
    deliverables = await get_deliverables(workspace_id)
    print(f"\n📦 DELIVERABLES: {len(deliverables) if deliverables else 0}")
    
    if deliverables:
        for i, deliverable in enumerate(deliverables, 1):
            content = deliverable.get('content', '')
            content_length = len(content)
            deliverable_type = deliverable.get('type', 'Unknown')
            status = deliverable.get('status', 'Unknown')
            
            print(f"\n   📄 DELIVERABLE {i}:")
            print(f"      Type: {deliverable_type}")
            print(f"      Status: {status}")
            print(f"      Content: {content_length} characters")
            
            if content:
                print(f"      Preview: {content[:200]}...")
                
                # CRITICAL: Analyze content type
                content_lower = content.lower()
                has_emails = '@' in content and ('.com' in content or '.org' in content)
                has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco', 'giulia', 'luca'])
                has_phone = any(phone in content for phone in ['+', 'phone:', 'tel:', '39', '33', '34'])
                has_companies = any(company in content_lower for company in ['srl', 'spa', 'ltd', 'inc', 'gmbh'])
                has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'how to', 'you can', 'consider using', 'tool for'])
                
                print(f"      📊 CONTENT ANALYSIS:")
                print(f"         Has emails: {has_emails}")
                print(f"         Has names: {has_names}")
                print(f"         Has phones: {has_phone}")
                print(f"         Has companies: {has_companies}")
                print(f"         Has methodology: {has_methodology}")
                
                # Determine content type
                real_data_indicators = sum([has_emails, has_names, has_phone, has_companies])
                
                if real_data_indicators >= 2 and not has_methodology:
                    print(f"         ✅ VERDICT: APPEARS TO BE REAL CONTACT DATA")
                elif has_methodology and real_data_indicators < 2:
                    print(f"         ❌ VERDICT: APPEARS TO BE METHODOLOGY/STRATEGY")
                else:
                    print(f"         ⚠️  VERDICT: MIXED OR UNCLEAR CONTENT")
    
    # Check team proposals
    proposals_response = supabase.table("team_proposals").select("*").eq("workspace_id", workspace_id).execute()
    proposals = proposals_response.data if proposals_response.data else []
    print(f"\n📝 TEAM PROPOSALS: {len(proposals)}")
    for proposal in proposals:
        print(f"   - {proposal.get('id')} - {proposal.get('status')}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    has_agents = len(agents) > 0
    has_tasks = len(tasks) > 0 if tasks else False
    has_deliverables = len(deliverables) > 0 if deliverables else False
    needs_revision = task_statuses.get('needs_revision', 0) > 0
    
    print(f"   Agents created: {'✅' if has_agents else '❌'}")
    print(f"   Tasks generated: {'✅' if has_tasks else '❌'}")
    print(f"   Deliverables created: {'✅' if has_deliverables else '❌'}")
    print(f"   AI validation active: {'✅' if needs_revision else '❓'}")
    
    if has_deliverables:
        # Check if any deliverable has real data
        real_data_found = False
        for deliverable in deliverables:
            content = deliverable.get('content', '').lower()
            if '@' in content and any(name in content for name in ['john', 'sarah', 'mike']):
                real_data_found = True
                break
        
        print(f"   Real data detected: {'✅' if real_data_found else '❌'}")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(check_now())