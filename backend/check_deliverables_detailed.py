#!/usr/bin/env python3
"""
Check deliverables content in detail
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_deliverables():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"📦 DETAILED DELIVERABLES CHECK")
    print(f"Workspace: {workspace_id}")
    print("="*80)
    
    try:
        response = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
        deliverables = response.data if response.data else []
        
        print(f"Found {len(deliverables)} deliverable(s)")
        
        for i, deliverable in enumerate(deliverables, 1):
            print(f"\n📄 DELIVERABLE {i}:")
            print(f"   ID: {deliverable.get('id')}")
            print(f"   Title: {deliverable.get('title')}")
            print(f"   Description: {deliverable.get('description')}")
            print(f"   Type: {deliverable.get('type')}")
            print(f"   Status: {deliverable.get('status')}")
            print(f"   Business Value Score: {deliverable.get('business_value_score')}")
            print(f"   Completion %: {deliverable.get('completion_percentage')}")
            print(f"   Quality Level: {deliverable.get('quality_level')}")
            
            content = deliverable.get('content')
            if content:
                content_str = str(content)
                print(f"   Content length: {len(content_str)} characters")
                
                if len(content_str) > 0:
                    # Show more content since we want to see what's actually there
                    preview_length = min(1000, len(content_str))
                    print(f"\n   📝 CONTENT ({preview_length} chars):")
                    print(f"   {content_str[:preview_length]}")
                    if len(content_str) > preview_length:
                        print(f"   ... [content continues for {len(content_str) - preview_length} more chars]")
                    
                    # Analysis
                    content_lower = content_str.lower()
                    has_emails = '@' in content_str and ('.com' in content_str or '.it' in content_str)
                    has_names = any(name in content_lower for name in [
                        'john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco', 'giulia', 'luca',
                        'alessandro', 'francesco', 'matteo', 'lorenzo', 'anna', 'chiara', 'elena'
                    ])
                    has_companies = any(company in content_lower for company in ['srl', 'spa', 'ltd', 'inc', 'gmbh', 'saas'])
                    has_methodology = any(word in content_lower for word in [
                        'strategia', 'approccio', 'come trovare', 'puoi utilizzare', 'considera di usare',
                        'strategy', 'approach', 'how to find', 'you can use', 'consider using'
                    ])
                    
                    print(f"\n   📊 CONTENT ANALYSIS:")
                    print(f"      Has emails: {has_emails}")
                    print(f"      Has names: {has_names}")
                    print(f"      Has companies: {has_companies}")
                    print(f"      Has methodology keywords: {has_methodology}")
                    
                    # Verdict
                    real_data_indicators = sum([has_emails, has_names, has_companies])
                    if real_data_indicators >= 2 and not has_methodology:
                        print(f"      ✅ VERDICT: APPEARS TO BE REAL BUSINESS DATA")
                    elif has_methodology and real_data_indicators < 2:
                        print(f"      ❌ VERDICT: APPEARS TO BE METHODOLOGY/STRATEGY")
                    else:
                        print(f"      ⚠️  VERDICT: MIXED OR UNCLEAR CONTENT")
                else:
                    print(f"   ❌ Content is empty")
            else:
                print(f"   ❌ No content field")
                
            # Check metadata
            metadata = deliverable.get('metadata')
            if metadata:
                print(f"   Metadata: {metadata}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        
    # Also check tasks to see what's happening
    print(f"\n📋 RELATED TASKS:")
    try:
        tasks_response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        tasks = tasks_response.data if tasks_response.data else []
        
        for task in tasks:
            status = task.get('status')
            name = task.get('name', 'No name')[:50]
            output = task.get('output', '')
            print(f"   - {name}... [{status}]")
            if output and len(output) > 100:
                print(f"     Output: {len(output)} chars - {output[:100]}...")
    
    except Exception as e:
        print(f"❌ Error checking tasks: {e}")

if __name__ == "__main__":
    asyncio.run(check_deliverables())