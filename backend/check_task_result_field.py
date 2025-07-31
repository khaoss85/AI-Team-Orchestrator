#!/usr/bin/env python3
"""
Check task result field to find actual content
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_task_results():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"📋 CHECKING TASK RESULT FIELD")
    print(f"Workspace: {workspace_id}")
    print("="*80)
    
    try:
        # Get all tasks for the workspace
        response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        tasks = response.data if response.data else []
        
        print(f"Found {len(tasks)} task(s)")
        
        # Show all field names for first task
        if tasks:
            print(f"\n📋 AVAILABLE FIELDS IN TASKS TABLE:")
            field_names = list(tasks[0].keys())
            print(f"   {field_names}")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n📋 TASK {i}:")
            print(f"   ID: {task.get('id')}")
            print(f"   Name: {task.get('name')}")
            print(f"   Status: {task.get('status')}")
            
            # Check different potential content fields
            for field_name in ['result', 'output', 'content', 'description', 'context_data']:
                field_value = task.get(field_name)
                if field_value:
                    field_str = str(field_value)
                    if len(field_str) > 100:  # Only show substantial content
                        print(f"\n   📝 FIELD '{field_name}' ({len(field_str)} chars):")
                        preview = min(1000, len(field_str))
                        print(f"   {field_str[:preview]}")
                        if len(field_str) > preview:
                            print(f"   ... [continues for {len(field_str) - preview} more chars]")
                        
                        # Analysis for business content
                        field_lower = field_str.lower()
                        has_emails = '@' in field_str and '.com' in field_str
                        has_names = any(name in field_lower for name in [
                            'john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco', 'giulia'
                        ])
                        has_companies = any(company in field_lower for company in ['srl', 'spa', 'ltd', 'inc', 'saas'])
                        has_methodology = any(word in field_lower for word in [
                            'strategia', 'approccio', 'come', 'puoi', 'considera',
                            'strategy', 'approach', 'how to', 'you can', 'consider'
                        ])
                        
                        print(f"\n   📊 CONTENT ANALYSIS:")
                        print(f"      Has emails: {has_emails}")
                        print(f"      Has names: {has_names}")
                        print(f"      Has companies: {has_companies}")
                        print(f"      Has methodology: {has_methodology}")
                        
                        real_data_score = sum([has_emails, has_names, has_companies])
                        if real_data_score >= 2 and not has_methodology:
                            print(f"      ✅ VERDICT: REAL BUSINESS DATA!")
                        elif has_methodology:
                            print(f"      ❌ VERDICT: METHODOLOGY/INSTRUCTIONS")
                        else:
                            print(f"      ⚠️  VERDICT: OTHER CONTENT")
                    elif field_value:
                        print(f"   - {field_name}: {field_str[:100]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_task_results())