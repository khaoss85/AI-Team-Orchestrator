#!/usr/bin/env python3
"""
Check the specific deliverable showing raw JSON issue.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def check_problem_deliverable():
    # Look for the deliverable with the specific raw JSON issue mentioned by user
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    
    # First, let's find deliverables with the problematic display content pattern
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    print("🔍 SEARCHING FOR DELIVERABLES WITH RAW JSON IN DISPLAY CONTENT")
    print("=" * 80)
    
    problematic_deliverables = []
    
    for deliv in deliverables:
        display_content = deliv.get('display_content', '')
        
        # Check if display_content contains Python dict representation
        if "{'title':" in display_content or '{"title":' in display_content:
            problematic_deliverables.append(deliv)
            print(f"\n❌ FOUND PROBLEMATIC DELIVERABLE:")
            print(f"   Title: {deliv['title'][:60]}...")
            print(f"   ID: {deliv['id']}")
            print(f"   Goal ID: {deliv.get('goal_id')}")
            
            # Extract the problematic part
            if "{'title':" in display_content:
                print("\n   🐛 Python dict representation found in HTML!")
                # Find and display the problematic section
                start_idx = display_content.find("{'title':")
                end_idx = display_content.find("}", start_idx) + 1 if display_content.find("}", start_idx) != -1 else start_idx + 200
                problematic_section = display_content[max(0, start_idx-50):min(len(display_content), end_idx+50)]
                print(f"   Problematic section:\n   {problematic_section}")
            
            # Show what the display_content should look like
            print("\n   📝 Display Content Analysis:")
            print(f"   - Total length: {len(display_content)}")
            print(f"   - Starts with: {display_content[:100]}...")
            
            # Check if it's wrapped in HTML but contains raw dict
            if display_content.startswith('<div'):
                print("   - ⚠️ HTML wrapper present but contains raw dict strings")
            
            # Check the actual content field
            content = deliv.get('content')
            if content:
                if isinstance(content, dict):
                    print(f"\n   📋 Original content is dict with keys: {list(content.keys())[:5]}")
                elif isinstance(content, str):
                    print(f"\n   📋 Original content is string")
    
    print(f"\n\n📊 SUMMARY:")
    print(f"   Total deliverables checked: {len(deliverables)}")
    print(f"   Deliverables with raw JSON in display: {len(problematic_deliverables)}")
    
    if problematic_deliverables:
        print(f"\n🔧 FIX NEEDED:")
        print("   The AI content transformer is incorrectly embedding Python dict")
        print("   representations directly into the HTML instead of properly")
        print("   formatting them as HTML elements.")
        
        # Show an example of how it should be fixed
        example = problematic_deliverables[0]
        print(f"\n   Example deliverable needing fix: {example['id']}")
        print(f"   Title: {example['title'][:60]}...")

check_problem_deliverable()