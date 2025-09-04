#!/usr/bin/env python3
"""
Check the display_content field to understand why it's showing raw JSON in frontend.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def check_display_content():
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    
    # Get a sample deliverable with display content issue
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).limit(5).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    print("🔍 CHECKING DISPLAY CONTENT FORMAT")
    print("=" * 80)
    
    for deliv in deliverables:
        print(f"\n📦 Deliverable: {deliv['title'][:60]}...")
        print(f"   ID: {deliv['id']}")
        
        # Check display_content field
        display_content = deliv.get('display_content')
        display_format = deliv.get('display_format', 'unknown')
        
        print(f"   Display Format: {display_format}")
        
        if display_content:
            print(f"   Display Content Length: {len(display_content)}")
            print(f"   Display Content Type: {type(display_content)}")
            
            # Check if it's HTML or raw Python dict string
            if display_content.startswith('<'):
                print("   ✅ Format: HTML")
                print(f"   Preview: {display_content[:200]}...")
            elif display_content.startswith('{\'') or display_content.startswith('{"'):
                print("   ❌ Format: Raw Python dict/JSON string")
                print(f"   Preview: {display_content[:200]}...")
            else:
                print("   ⚠️ Format: Unknown")
                print(f"   Preview: {display_content[:200]}...")
        else:
            print("   ❌ No display_content")
        
        # Check regular content field
        content = deliv.get('content')
        if content:
            content_type = type(content)
            print(f"\n   Content Field Type: {content_type}")
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    print(f"   Content is JSON string, parsed keys: {list(parsed.keys())[:5]}")
                except:
                    print(f"   Content is plain string: {content[:100]}...")
            elif isinstance(content, dict):
                print(f"   Content is dict, keys: {list(content.keys())[:5]}")

check_display_content()