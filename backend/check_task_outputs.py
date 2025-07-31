#!/usr/bin/env python3
"""
Check task outputs to find the actual content
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_task_outputs():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"📋 DETAILED TASK OUTPUTS CHECK")
    print(f"Workspace: {workspace_id}")
    print("="*80)
    
    try:
        response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        tasks = response.data if response.data else []
        
        print(f"Found {len(tasks)} task(s)")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n📋 TASK {i}:")
            print(f"   ID: {task.get('id')}")
            print(f"   Name: {task.get('name')}")
            print(f"   Status: {task.get('status')}")
            print(f"   Agent ID: {task.get('agent_id')}")
            
            # Check task output
            output = task.get('output')
            if output:
                output_str = str(output)
                print(f"   Output length: {len(output_str)} characters")
                
                if len(output_str) > 0:
                    # Show substantial content
                    preview_length = min(1500, len(output_str))
                    print(f"\n   📝 TASK OUTPUT ({preview_length} chars):")
                    print(f"   {output_str[:preview_length]}")
                    if len(output_str) > preview_length:
                        print(f"   ... [output continues for {len(output_str) - preview_length} more chars]")
                    
                    # Analysis of output content
                    output_lower = output_str.lower()
                    has_emails = '@' in output_str and ('.com' in output_str or '.it' in output_str)
                    has_names = any(name in output_lower for name in [
                        'john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco', 'giulia', 'luca',
                        'alessandro', 'francesco', 'matteo', 'lorenzo', 'anna', 'chiara', 'elena'
                    ])
                    has_companies = any(company in output_lower for company in ['srl', 'spa', 'ltd', 'inc', 'gmbh', 'saas'])
                    has_methodology = any(word in output_lower for word in [
                        'strategia', 'approccio', 'come trovare', 'puoi utilizzare', 'considera di usare',
                        'strategy', 'approach', 'how to find', 'you can use', 'consider using',
                        'tool for', 'website for'
                    ])
                    
                    print(f"\n   📊 OUTPUT ANALYSIS:")
                    print(f"      Has emails: {has_emails}")
                    print(f"      Has names: {has_names}")
                    print(f"      Has companies: {has_companies}")
                    print(f"      Has methodology keywords: {has_methodology}")
                    
                    # Determine content type
                    real_data_indicators = sum([has_emails, has_names, has_companies])
                    if real_data_indicators >= 2 and not has_methodology:
                        print(f"      ✅ VERDICT: REAL BUSINESS DATA FOUND!")
                    elif has_methodology and real_data_indicators < 2:
                        print(f"      ❌ VERDICT: METHODOLOGY/STRATEGY CONTENT")
                    elif task.get('status') == 'needs_revision':
                        print(f"      🔄 VERDICT: UNDER AI REVISION (likely rejected methodology)")
                    else:
                        print(f"      ⚠️  VERDICT: MIXED OR OTHER CONTENT")
                else:
                    print(f"   ❌ Output is empty")
            else:
                print(f"   ❌ No output field")
                
            # Check failure reason if failed
            if task.get('status') == 'failed':
                failure_reason = task.get('failure_reason', 'No reason provided')
                print(f"   ❌ Failure reason: {failure_reason}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_task_outputs())