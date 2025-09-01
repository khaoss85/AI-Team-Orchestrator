#!/usr/bin/env python3
"""
Investigation script for WorkspaceMemory system
Queries database directly to understand the memory tables structure and content
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import json

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"📊 {title}")
    print(f"{'='*80}")

async def investigate_workspace_memory():
    """Main investigation function"""
    workspace_id = "f5c4f1e0-a887-4431-b43e-aea6d62f2d4a"
    
    print(f"\n🔍 WORKSPACE MEMORY INVESTIGATION")
    print(f"📁 Workspace ID: {workspace_id}")
    print(f"🕐 Investigation Time: {datetime.now().isoformat()}")
    
    # 1. Check workspace_insights table
    print_section("WORKSPACE_INSIGHTS TABLE")
    try:
        # Get all insights for this workspace
        insights_response = supabase.table("workspace_insights").select("*").eq("workspace_id", workspace_id).execute()
        insights = insights_response.data if insights_response else []
        
        print(f"✅ Total insights found: {len(insights)}")
        
        if insights:
            # Group by insight_type
            insights_by_type = {}
            for insight in insights:
                insight_type = insight.get("insight_type", "unknown")
                if insight_type not in insights_by_type:
                    insights_by_type[insight_type] = []
                insights_by_type[insight_type].append(insight)
            
            print(f"\n📈 Insights by type:")
            for insight_type, items in insights_by_type.items():
                print(f"  - {insight_type}: {len(items)} insights")
                # Show sample
                if items:
                    sample = items[0]
                    print(f"    Sample: {sample.get('content', 'No content')[:100]}...")
                    print(f"    Confidence: {sample.get('confidence_score', 0)}")
                    print(f"    Tags: {sample.get('relevance_tags', [])}")
        else:
            print("❌ No insights found in workspace_insights table")
            
            # Check if there are ANY insights in the table
            all_insights_response = supabase.table("workspace_insights").select("workspace_id").execute()
            all_insights = all_insights_response.data if all_insights_response else []
            unique_workspaces = set(i['workspace_id'] for i in all_insights)
            print(f"\n📊 Total insights in database: {len(all_insights)}")
            print(f"📊 Unique workspaces with insights: {len(unique_workspaces)}")
            if unique_workspaces:
                print(f"   Sample workspace IDs: {list(unique_workspaces)[:3]}")
    except Exception as e:
        print(f"❌ Error querying workspace_insights: {e}")
    
    # 2. Check memory_context table
    print_section("MEMORY_CONTEXT TABLE")
    try:
        context_response = supabase.table("memory_context").select("*").eq("workspace_id", workspace_id).execute()
        contexts = context_response.data if context_response else []
        
        print(f"✅ Total contexts found: {len(contexts)}")
        
        if contexts:
            for ctx in contexts[:3]:  # Show first 3
                print(f"\n  Context Type: {ctx.get('context_type')}")
                print(f"  Importance: {ctx.get('importance_score', 0)}")
                print(f"  Content: {ctx.get('context', 'No context')[:100]}...")
        else:
            print("❌ No context found in memory_context table")
    except Exception as e:
        print(f"❌ Error querying memory_context: {e}")
    
    # 3. Check memory_patterns table
    print_section("MEMORY_PATTERNS TABLE")
    try:
        patterns_response = supabase.table("memory_patterns").select("*").eq("workspace_id", workspace_id).execute()
        patterns = patterns_response.data if patterns_response else []
        
        print(f"✅ Total patterns found: {len(patterns)}")
        
        if patterns:
            for pattern in patterns[:3]:
                print(f"\n  Pattern Type: {pattern.get('pattern_type')}")
                print(f"  Confidence: {pattern.get('confidence', 0)}")
                print(f"  Usage Count: {pattern.get('usage_count', 0)}")
                print(f"  Success Indicators: {pattern.get('success_indicators', [])}")
        else:
            print("❌ No patterns found in memory_patterns table")
    except Exception as e:
        print(f"❌ Error querying memory_patterns: {e}")
    
    # 4. Check learning_patterns table
    print_section("LEARNING_PATTERNS TABLE")
    try:
        learning_response = supabase.table("learning_patterns").select("*").eq("workspace_id", workspace_id).execute()
        learnings = learning_response.data if learning_response else []
        
        print(f"✅ Total learning patterns found: {len(learnings)}")
        
        if learnings:
            for learning in learnings[:3]:
                print(f"\n  Pattern Name: {learning.get('pattern_name')}")
                print(f"  Pattern Type: {learning.get('pattern_type')}")
                print(f"  Strength: {learning.get('pattern_strength', 0)}")
                print(f"  Confidence: {learning.get('confidence_score', 0)}")
                print(f"  Usage Count: {learning.get('usage_count', 0)}")
        else:
            print("❌ No learning patterns found in learning_patterns table")
    except Exception as e:
        print(f"❌ Error querying learning_patterns: {e}")
    
    # 5. Check recent tasks to see if they should have generated insights
    print_section("RECENT COMPLETED TASKS (Should Generate Insights)")
    try:
        # Get recent completed tasks
        tasks_response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "completed").order("completed_at", desc=True).limit(5).execute()
        tasks = tasks_response.data if tasks_response else []
        
        print(f"✅ Recent completed tasks: {len(tasks)}")
        
        for task in tasks:
            print(f"\n  Task: {task.get('title', 'Untitled')[:60]}...")
            print(f"  Completed: {task.get('completed_at', 'Unknown')}")
            print(f"  Agent: {task.get('assigned_agent_id', 'No agent')}")
            
            # Check if this task has associated insights
            task_insights = supabase.table("workspace_insights").select("id, insight_type").eq("task_id", task['id']).execute()
            if task_insights.data:
                print(f"  ✅ Has {len(task_insights.data)} insights")
            else:
                print(f"  ❌ No insights generated for this task")
    except Exception as e:
        print(f"❌ Error querying tasks: {e}")
    
    # 6. Test if insight generation is enabled
    print_section("CONFIGURATION CHECK")
    print(f"ENABLE_WORKSPACE_MEMORY: {os.getenv('ENABLE_WORKSPACE_MEMORY', 'not set')}")
    print(f"MEMORY_RETENTION_DAYS: {os.getenv('MEMORY_RETENTION_DAYS', 'not set')}")
    print(f"MIN_CONFIDENCE_THRESHOLD: {os.getenv('MIN_CONFIDENCE_THRESHOLD', 'not set')}")
    
    # 7. Summary and recommendations
    print_section("INVESTIGATION SUMMARY")
    print("""
    🔍 Investigation Complete!
    
    Based on the findings above, we can determine:
    1. Whether insights are being generated and stored
    2. Whether the API is correctly retrieving stored insights
    3. Whether the configuration is enabling memory features
    4. What needs to be fixed to enable the WorkspaceMemory system
    """)

if __name__ == "__main__":
    asyncio.run(investigate_workspace_memory())