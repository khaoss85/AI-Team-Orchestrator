#!/usr/bin/env python3
"""Force deliverable creation for workspace"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase, trigger_deliverable_aggregation, should_trigger_deliverable_aggregation
from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable


async def main():
    """Force deliverable creation"""
    workspace_id = "12e63f24-1cda-44aa-b5b1-caef243bb18c"
    
    print("🚀 FORCING DELIVERABLE CREATION")
    print("=" * 60)
    
    # First check current state
    workspace = supabase.table('workspaces').select('*').eq('id', workspace_id).single().execute()
    print(f"\n📁 Workspace: {workspace.data['name']}")
    print(f"   Status: {workspace.data['status']}")
    
    # Check existing deliverables
    existing = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    print(f"\n📦 Existing deliverables: {len(existing.data)}")
    
    # Check completed tasks
    tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
    print(f"\n✅ Completed tasks: {len(tasks.data)}")
    
    # Check if should trigger
    print(f"\n🔍 Checking trigger conditions...")
    should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
    print(f"   Should trigger: {should_trigger}")
    
    # Force creation regardless
    print(f"\n💪 Forcing deliverable creation...")
    
    try:
        # Method 1: Using trigger_deliverable_aggregation (which forces)
        await trigger_deliverable_aggregation(workspace_id)
        print("   ✅ Triggered via trigger_deliverable_aggregation")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check if created
        new_deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        new_count = len(new_deliverables.data)
        
        if new_count > len(existing.data):
            print(f"\n🎉 SUCCESS! Created {new_count - len(existing.data)} new deliverable(s)")
            
            # Show new deliverables
            for d in new_deliverables.data[len(existing.data):]:
                print(f"\n📦 New Deliverable:")
                print(f"   ID: {d['id']}")
                print(f"   Type: {d.get('type', 'Unknown')}")
                print(f"   Title: {d.get('title', 'No title')}")
                print(f"   Created: {d['created_at']}")
        else:
            print(f"\n⚠️  No new deliverables created")
            
            # Try method 2: Direct call
            print(f"\n💪 Trying direct method...")
            result = await check_and_create_final_deliverable(workspace_id, force=True)
            
            if result:
                print(f"   ✅ Direct method returned: {result}")
                
                # Check again
                final_check = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
                if len(final_check.data) > new_count:
                    print(f"   🎉 Created {len(final_check.data) - new_count} deliverable(s)")
            else:
                print(f"   ❌ Direct method returned None")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Final check
    print(f"\n📊 FINAL STATUS:")
    final_deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    print(f"   Total deliverables: {len(final_deliverables.data)}")
    
    if len(final_deliverables.data) == 0:
        print(f"\n⚠️  DIAGNOSIS: No deliverables created despite force flag")
        print(f"   Possible issues:")
        print(f"   1. Quality score validation might be blocking")
        print(f"   2. Task results might be considered non-substantive")
        print(f"   3. The check_and_create_final_deliverable function might have additional checks")


if __name__ == "__main__":
    asyncio.run(main())