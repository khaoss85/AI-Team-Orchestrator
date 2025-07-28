#!/usr/bin/env python3
"""
Examine the actual deliverables created
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def examine_deliverables():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"Examining deliverables for workspace: {workspace_id}")
    print("=" * 80)
    
    # Get deliverables
    deliverables_result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_result.data
    
    print(f"Found {len(deliverables)} deliverables\n")
    
    for i, deliverable in enumerate(deliverables, 1):
        print(f"DELIVERABLE {i}:")
        print("-" * 20)
        print(f"ID: {deliverable.get('id', 'Unknown')}")
        print(f"Name: {deliverable.get('name', 'Unnamed')}")
        print(f"Type: {deliverable.get('type', 'Unknown')}")
        print(f"Created: {deliverable.get('created_at', 'Unknown')}")
        
        content = deliverable.get('content', '')
        print(f"Content length: {len(str(content))}")
        print(f"Content preview:")
        print(str(content)[:1000] + "..." if len(str(content)) > 1000 else str(content))
        print("\n" + "="*60 + "\n")
        
        # Also check the full content structure
        print("Full deliverable structure:")
        for key, value in deliverable.items():
            if key != 'content':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: <content of length {len(str(value))}>")
        print()

if __name__ == "__main__":
    asyncio.run(examine_deliverables())