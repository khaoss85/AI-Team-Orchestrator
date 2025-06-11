#!/usr/bin/env python3
"""
Simple debugging without external dependencies
"""
import os
import sys
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Check environment variables
print("🔍 Environment Variables Check:")
print(f"SUPABASE_URL exists: {'SUPABASE_URL' in os.environ}")
print(f"SUPABASE_KEY exists: {'SUPABASE_KEY' in os.environ}")

# Check if .env file exists
env_file = os.path.join(os.path.dirname(__file__), '.env')
print(f".env file exists: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    print("📄 Contents of .env file (first few lines):")
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()[:5]  # First 5 lines only
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0] if '=' in line else line.strip()
                    print(f"  {i}. {key}=***")
    except Exception as e:
        print(f"Error reading .env: {e}")

# Try to import and test database connection
try:
    print("\n🔄 Testing database import...")
    
    # Manual env loading
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    from database import supabase, list_tasks
    print("✅ Database import successful")
    
    # Try a simple query
    print("\n🔍 Testing database connection...")
    result = supabase.table("workspaces").select("id, name, created_at").order("created_at", desc=True).limit(5).execute()
    
    if result.data:
        print(f"✅ Found {len(result.data)} recent workspaces:")
        for i, ws in enumerate(result.data, 1):
            print(f"  {i}. {ws.get('name', 'Unnamed')} (ID: {ws['id'][:8]}...)")
        
        # Use first workspace automatically for testing
        workspace_id = result.data[0]['id']
        print(f"\nUsing first workspace: {workspace_id}")
        
        print(f"\n🔍 Debugging workspace: {workspace_id}")
        
        # Get tasks for workspace
        print("📊 Fetching tasks...")
        result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        
        if result.data:
            tasks = result.data
            print(f"Total tasks: {len(tasks)}")
            
            # Status breakdown
            status_counts = {}
            creation_type_counts = {}
            intelligent_ai_tasks = []
            final_deliverable_tasks = []
            
            for task in tasks:
                status = task.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                
                creation_type = task.get("creation_type", "unknown")
                creation_type_counts[creation_type] = creation_type_counts.get(creation_type, 0) + 1
                
                if creation_type == "intelligent_ai_deliverable":
                    intelligent_ai_tasks.append(task)
                
                # Check for final deliverable flags
                context_data = task.get("context_data", {}) or {}
                if isinstance(context_data, dict):
                    if (context_data.get("is_final_deliverable") or 
                        context_data.get("deliverable_aggregation") or
                        context_data.get("triggers_project_completion") or
                        context_data.get("final_deliverable")):
                        final_deliverable_tasks.append(task)
            
            print("\n📈 Status Breakdown:")
            for status, count in status_counts.items():
                print(f"  • {status}: {count}")
            
            print("\n🏗️ Creation Type Breakdown:")
            for creation_type, count in creation_type_counts.items():
                print(f"  • {creation_type}: {count}")
            
            print(f"\n🤖 Intelligent AI Deliverable Tasks: {len(intelligent_ai_tasks)}")
            for task in intelligent_ai_tasks:
                print(f"  • ID: {task['id']}")
                print(f"    Name: {task.get('name', 'Unnamed')}")
                print(f"    Status: {task.get('status')}")
                print(f"    Created: {task.get('created_at')}")
                print(f"    Updated: {task.get('updated_at')}")
                
                # Check context_data structure
                context_data = task.get("context_data", {})
                if isinstance(context_data, dict):
                    print(f"    Context keys: {list(context_data.keys())}")
                    # Check for final deliverable flags
                    final_flags = []
                    for key in context_data:
                        if 'final' in key.lower() or 'deliverable' in key.lower():
                            final_flags.append(f"{key}={context_data[key]}")
                    if final_flags:
                        print(f"    Final deliverable flags: {final_flags}")
                    else:
                        print(f"    No final deliverable flags found")
                else:
                    print(f"    Context data type: {type(context_data)}")
                
                # Check result payload
                result_data = task.get("result")
                if result_data:
                    print(f"    Has result: Yes (type: {type(result_data).__name__})")
                    if isinstance(result_data, dict):
                        print(f"    Result keys: {list(result_data.keys())}")
                else:
                    print(f"    Has result: No")
                print()
            
            print(f"\n🎯 Final Deliverable Tasks (by context flags): {len(final_deliverable_tasks)}")
            for task in final_deliverable_tasks:
                print(f"  • {task.get('name', 'Unnamed')} (Status: {task.get('status')})")
        
        else:
            print("❌ No tasks found in workspace")
    
    else:
        print("❌ No workspaces found")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()