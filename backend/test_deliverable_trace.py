#!/usr/bin/env python3
"""
Emergency diagnostic trace for deliverable creation flow
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configure logging to see everything
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Trace the actual flow
async def trace_deliverable_creation():
    print("\n" + "="*80)
    print("🚨 EMERGENCY DIAGNOSTIC TRACE - DELIVERABLE CREATION")
    print("="*80)
    
    workspace_id = 'f79d87cc-b61f-491d-9226-4220e39e71ad'
    
    # Import and check services
    print("\n📦 SERVICE AVAILABILITY:")
    print("-"*40)
    
    # 1. Check AI Goal Matcher
    try:
        from services.ai_goal_matcher import AIGoalMatcher
        matcher = AIGoalMatcher()
        print(f"✅ AI Goal Matcher: Loaded")
        print(f"   - OpenAI Available: {matcher.openai_available}")
        print(f"   - OpenAI Key Set: {bool(os.getenv('OPENAI_API_KEY'))}")
    except Exception as e:
        print(f"❌ AI Goal Matcher: {e}")
    
    # 2. Check Display Transformer
    try:
        from services.ai_content_display_transformer import transform_deliverable_to_html
        print(f"✅ Display Transformer: Loaded")
    except Exception as e:
        print(f"❌ Display Transformer: {e}")
    
    # 3. Check Real Tool Pipeline
    try:
        from services.real_tool_integration_pipeline import real_tool_integration_pipeline
        print(f"✅ Real Tool Pipeline: Loaded")
    except Exception as e:
        print(f"❌ Real Tool Pipeline: {e}")
    
    # Now trace the actual database functions
    print("\n🔍 TRACING DATABASE FLOW:")
    print("-"*40)
    
    from database import (
        create_deliverable,
        get_workspace_goals,
        list_tasks,
        get_workspace
    )
    
    # Get workspace data
    print(f"\n📊 Workspace: {workspace_id}")
    
    # Check goals
    goals = await get_workspace_goals(workspace_id)
    print(f"\n🎯 Goals found: {len(goals) if goals else 0}")
    if goals:
        for g in goals[:2]:
            print(f"  - {g.get('description', 'No description')[:50]}...")
            print(f"    Status: {g.get('status')}, Progress: {g.get('progress')}")
    
    # Check completed tasks
    tasks = await list_tasks(workspace_id, status="completed", limit=10)
    print(f"\n✅ Completed tasks: {len(tasks) if tasks else 0}")
    if tasks:
        for t in tasks[:2]:
            print(f"  - {t.get('name', 'No name')[:50]}...")
    
    # Test deliverable creation with full tracing
    print("\n🧪 TESTING DELIVERABLE CREATION:")
    print("-"*40)
    
    test_deliverable = {
        'title': 'DIAGNOSTIC TEST DELIVERABLE',
        'type': 'test_asset',
        'content': {'test': 'Emergency diagnostic test content'}
    }
    
    # Monkey-patch logging to capture the flow
    original_create = create_deliverable
    
    async def traced_create(workspace_id, deliverable_data):
        print(f"\n📍 ENTERING create_deliverable")
        print(f"   Workspace: {workspace_id}")
        print(f"   Data: {deliverable_data}")
        
        # Call original with extra logging
        result = await original_create(workspace_id, deliverable_data)
        
        print(f"\n📍 RESULT from create_deliverable:")
        if result:
            print(f"   ID: {result.get('id')}")
            print(f"   Goal ID: {result.get('goal_id', 'NULL')}")
            print(f"   Display Content: {'Present' if result.get('display_content') else 'NULL'}")
        else:
            print("   ❌ No result returned")
        
        return result
    
    # Try to create a test deliverable
    try:
        result = await traced_create(workspace_id, test_deliverable)
        
        if result:
            print("\n✅ Test deliverable created successfully")
            
            # Check if it has AI enhancements
            print("\n🔍 AI ENHANCEMENT STATUS:")
            print(f"  Goal ID: {result.get('goal_id', 'NULL')}")
            print(f"  Display Content: {'✅ Present' if result.get('display_content') else '❌ NULL'}")
            
            # Check asset artifact
            from database import supabase
            artifacts = supabase.table('asset_artifacts') \
                .select('*') \
                .eq('workspace_id', workspace_id) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            if artifacts.data:
                artifact = artifacts.data[0]
                print("\n🎨 Asset Artifact:")
                print(f"  Display Content: {'✅ Present' if artifact.get('display_content') else '❌ NULL'}")
                print(f"  Display Format: {artifact.get('display_format', 'NULL')}")
        else:
            print("\n❌ Test deliverable creation failed")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(trace_deliverable_creation())