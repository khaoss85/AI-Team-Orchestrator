#!/usr/bin/env python3
"""
Check assets content for workspace
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_assets():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"📦 CHECKING ASSETS CONTENT")
    print(f"Workspace: {workspace_id}")
    print("="*60)
    
    # Get assets directly
    try:
        assets_response = supabase.table("assets").select("*").eq("workspace_id", workspace_id).execute()
        assets = assets_response.data if assets_response.data else []
        
        print(f"Found {len(assets)} asset(s)")
        
        for i, asset in enumerate(assets, 1):
            print(f"\n📄 ASSET {i}:")
            print(f"   ID: {asset.get('id')}")
            print(f"   Type: {asset.get('type')}")
            print(f"   Name: {asset.get('name')}")
            print(f"   Status: {asset.get('status')}")
            
            content = asset.get('content')
            if content:
                print(f"   Content length: {len(str(content))} characters")
                content_str = str(content)
                if len(content_str) > 0:
                    preview_length = min(800, len(content_str))
                    print(f"   Content preview ({preview_length} chars):")
                    print(f"   '{content_str[:preview_length]}...'")
                    
                    # Analysis for real data
                    content_lower = content_str.lower()
                    has_emails = '@' in content_str and '.com' in content_str
                    has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa', 'maria', 'andrea', 'marco', 'giulia', 'luca'])
                    has_methodology = any(word in content_lower for word in ['strategia', 'approccio', 'come trovare', 'puoi utilizzare', 'considera di usare'])
                    
                    print(f"   📊 ANALYSIS:")
                    print(f"      Has emails: {has_emails}")
                    print(f"      Has names: {has_names}")  
                    print(f"      Has methodology: {has_methodology}")
                    
                    if has_emails and has_names and not has_methodology:
                        print(f"      ✅ VERDICT: REAL CONTACT DATA")
                    elif has_methodology:
                        print(f"      ❌ VERDICT: METHODOLOGY/STRATEGY")
                    else:
                        print(f"      ⚠️  VERDICT: OTHER CONTENT TYPE")
                else:
                    print(f"   ❌ Content is empty")
            else:
                print(f"   ❌ No content field")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        
    # Also check objectives to see completion status
    try:
        objectives_response = supabase.table("objectives").select("*").eq("workspace_id", workspace_id).execute()
        objectives = objectives_response.data if objectives_response.data else []
        
        print(f"\n🎯 OBJECTIVES: {len(objectives)}")
        for obj in objectives:
            title = obj.get('title', 'No title')[:50]
            progress = obj.get('progress_percentage', 0)
            status = obj.get('status', 'unknown')
            print(f"   - {title}... [{progress}%] ({status})")
    
    except Exception as e:
        print(f"❌ Error checking objectives: {e}")

if __name__ == "__main__":
    asyncio.run(check_assets())