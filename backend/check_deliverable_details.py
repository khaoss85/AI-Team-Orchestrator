#!/usr/bin/env python3
"""Check deliverable details"""

import os
import sys
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

workspace_id = "12e63f24-1cda-44aa-b5b1-caef243bb18c"

# Get deliverables
deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()

print(f"📦 DELIVERABLE DETAILS")
print("=" * 60)

for d in deliverables.data:
    print(f"\nDeliverable ID: {d['id']}")
    print(f"Title: {d.get('title', 'No title')}")
    print(f"Type: {d.get('type', 'Unknown')}")
    print(f"Status: {d.get('status', 'Unknown')}")
    print(f"Created: {d['created_at']}")
    
    # Show content preview
    content = d.get('content', '')
    if content:
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 40)
        if isinstance(content, dict):
            print(json.dumps(content, indent=2)[:500])
        else:
            print(str(content)[:500])
    
    # Show metadata
    metadata = d.get('metadata', {})
    if metadata:
        print(f"\nMetadata:")
        print(json.dumps(metadata, indent=2))
    
    # Show quality metrics
    quality = d.get('quality_metrics', {})
    if quality:
        print(f"\nQuality Metrics:")
        print(json.dumps(quality, indent=2))
    
    print("\n" + "-" * 60)