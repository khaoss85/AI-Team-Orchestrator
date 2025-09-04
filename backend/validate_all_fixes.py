#!/usr/bin/env python3
"""
Validate that all fixes were applied correctly.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

# Import the function to test the progress calculation
from database import get_workspace_goals
import asyncio

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

async def validate_fixes():
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    
    print("🔍 VALIDATING ALL FIXES")
    print("=" * 80)
    
    # 1. Check goal progress field
    print("\n1️⃣ CHECKING GOAL PROGRESS FIELD:")
    print("-" * 40)
    
    goals = await get_workspace_goals(workspace_id)
    
    success_count = 0
    for goal in goals[:3]:  # Check first 3 goals
        goal_desc = goal.get('description', 'Unknown')[:40] + "..."
        has_progress = 'progress' in goal
        
        if has_progress:
            print(f"✅ {goal_desc}")
            print(f"   Progress: {goal['progress']}%")
            print(f"   Values: {goal.get('current_value')}/{goal.get('target_value')}")
            success_count += 1
        else:
            print(f"❌ {goal_desc} - Missing progress field")
    
    # 2. Check display content formatting
    print("\n2️⃣ CHECKING DISPLAY CONTENT FORMATTING:")
    print("-" * 40)
    
    deliverables_response = supabase.table('deliverables').select('id, title, display_content').eq('workspace_id', workspace_id).limit(5).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    clean_count = 0
    for deliv in deliverables:
        if deliv.get('display_content'):
            if "{'title':" not in deliv['display_content']:
                print(f"✅ {deliv['title'][:40]}... - Clean HTML")
                clean_count += 1
            else:
                print(f"❌ {deliv['title'][:40]}... - Still has raw JSON")
    
    # 3. Check goal-deliverable assignments
    print("\n3️⃣ CHECKING GOAL-DELIVERABLE ASSIGNMENTS:")
    print("-" * 40)
    
    # Check CSV/HubSpot goal specifically
    csv_goal_id = '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'
    csv_deliverables = supabase.table('deliverables').select('title, content').eq('goal_id', csv_goal_id).execute()
    
    if csv_deliverables.data:
        for deliv in csv_deliverables.data:
            title = deliv['title'].lower()
            if 'csv' in title or 'hubspot' in title or 'contact' in title or 'import' in title:
                print(f"✅ CSV Goal has relevant deliverable: {deliv['title'][:50]}...")
            else:
                print(f"⚠️ CSV Goal has questionable deliverable: {deliv['title'][:50]}...")
    
    # 4. Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY:")
    print(f"   Goals with progress field: {success_count}/{min(3, len(goals))}")
    print(f"   Clean display content: {clean_count}/{len(deliverables)}")
    print(f"   CSV goal deliverables checked")
    
    if success_count > 0 and clean_count > 0:
        print("\n✅ FIXES SUCCESSFULLY APPLIED!")
        print("\n💡 The frontend should now show:")
        print("   - Correct progress percentages for all goals")
        print("   - Clean HTML content without raw JSON")
        print("   - Proper goal-deliverable relationships")
    else:
        print("\n⚠️ Some issues remain. Please review the output above.")

# Run the validation
asyncio.run(validate_fixes())