#!/usr/bin/env python3
"""
Check deliverable content
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_deliverable():
    workspace_id = "35241c49-6b11-487a-80d8-4583ea50f60c"
    
    print(f"📦 CHECKING DELIVERABLE CONTENT")
    print(f"Workspace: {workspace_id}")
    print("="*60)
    
    # Get deliverables
    try:
        deliverables_response = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
        deliverables = deliverables_response.data if deliverables_response.data else []
        
        print(f"Found {len(deliverables)} deliverable(s)")
        
        for i, deliverable in enumerate(deliverables, 1):
            print(f"\n📄 DELIVERABLE {i}:")
            print(f"   ID: {deliverable.get('id')}")
            print(f"   Type: {deliverable.get('type')}")
            print(f"   Status: {deliverable.get('status')}")
            
            content = deliverable.get('content')
            if content:
                print(f"   Content length: {len(str(content))} characters")
                content_str = str(content)
                if len(content_str) > 0:
                    preview_length = min(500, len(content_str))
                    print(f"   Content preview ({preview_length} chars):")
                    print(f"   '{content_str[:preview_length]}...'")
                    
                    # Analysis
                    content_lower = content_str.lower()
                    has_emails = '@' in content_str
                    has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa', 'maria'])
                    has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'how to'])
                    
                    print(f"   📊 ANALYSIS:")
                    print(f"      Has emails: {has_emails}")
                    print(f"      Has names: {has_names}")  
                    print(f"      Has methodology: {has_methodology}")
                else:
                    print(f"   ❌ Content is empty")
            else:
                print(f"   ❌ No content field")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_deliverable())