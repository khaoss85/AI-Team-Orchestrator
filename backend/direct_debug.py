#!/usr/bin/env python3
"""
Direct debugging using requests instead of supabase client
"""
import json
import requests

# Supabase configuration (from .env file)
SUPABASE_URL = "https://szerliaxjcverzdoisik.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN6ZXJsaWF4amN2ZXJ6ZG9pc2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4MDYwODAsImV4cCI6MjA2MjM4MjA4MH0.A0OLtI2ImcatW3QBTiw6uvsk7mSmzcyW9L4dBAkLUa8"

def make_supabase_request(table, params=None):
    """Make a direct request to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    print("🔍 Direct Supabase Database Investigation")
    print("=" * 50)
    
    try:
        # Get recent workspaces
        print("📊 Fetching recent workspaces...")
        workspaces = make_supabase_request("workspaces", {
            "select": "id,name,created_at,status",
            "order": "created_at.desc",
            "limit": "5"
        })
        
        if not workspaces:
            print("❌ No workspaces found")
            return
        
        print(f"✅ Found {len(workspaces)} recent workspaces:")
        for i, ws in enumerate(workspaces, 1):
            print(f"  {i}. {ws.get('name', 'Unnamed')} (ID: {ws['id'][:8]}...)")
            print(f"     Status: {ws.get('status')}, Created: {ws.get('created_at', '')[:10]}")
        
        # Get workspace to debug
        workspace_id = input("\nEnter workspace number (1-5) or full workspace ID: ").strip()
        
        if workspace_id.isdigit() and 1 <= int(workspace_id) <= len(workspaces):
            workspace_id = workspaces[int(workspace_id)-1]['id']
        elif len(workspace_id) < 30:  # Too short to be a UUID
            print("❌ Invalid input")
            return
        
        workspace_name = next((ws['name'] for ws in workspaces if ws['id'] == workspace_id), 'Unknown')
        print(f"\n🔍 Debugging workspace: {workspace_name} ({workspace_id[:8]}...)")
        
        # Get all tasks for this workspace
        print("\n📊 Fetching tasks...")
        tasks = make_supabase_request("tasks", {
            "select": "*",
            "workspace_id": f"eq.{workspace_id}",
            "order": "created_at.desc"
        })
        
        if not tasks:
            print("❌ No tasks found in workspace")
            return
        
        print(f"✅ Found {len(tasks)} tasks")
        
        # Analyze task breakdown
        status_counts = {}
        creation_type_counts = {}
        intelligent_ai_tasks = []
        final_deliverable_tasks = []
        
        for task in tasks:
            # Status breakdown
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Creation type breakdown  
            creation_type = task.get("creation_type", "unknown")
            creation_type_counts[creation_type] = creation_type_counts.get(creation_type, 0) + 1
            
            # Find intelligent AI deliverable tasks
            if creation_type == "intelligent_ai_deliverable":
                intelligent_ai_tasks.append(task)
            
            # Check for final deliverable flags in context_data
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                if (context_data.get("is_final_deliverable") or 
                    context_data.get("deliverable_aggregation") or
                    context_data.get("triggers_project_completion") or
                    context_data.get("final_deliverable")):
                    final_deliverable_tasks.append(task)
        
        # Print analysis
        print("\n📈 Task Status Breakdown:")
        for status, count in status_counts.items():
            print(f"  • {status}: {count}")
        
        print("\n🏗️ Creation Type Breakdown:")
        for creation_type, count in creation_type_counts.items():
            print(f"  • {creation_type}: {count}")
        
        print(f"\n🤖 Intelligent AI Deliverable Tasks: {len(intelligent_ai_tasks)}")
        for task in intelligent_ai_tasks:
            print(f"\n  📋 Task: {task.get('name', 'Unnamed')}")
            print(f"     ID: {task['id']}")
            print(f"     Status: {task.get('status')}")
            print(f"     Created: {task.get('created_at', '')[:19]}")
            print(f"     Updated: {task.get('updated_at', '')[:19]}")
            
            # Analyze context_data
            context_data = task.get("context_data", {})
            if isinstance(context_data, dict):
                print(f"     Context keys: {list(context_data.keys())}")
                
                # Look for final deliverable flags
                final_flags = {}
                for key, value in context_data.items():
                    if ('final' in key.lower() or 'deliverable' in key.lower() or 
                        'completion' in key.lower() or 'aggregation' in key.lower()):
                        final_flags[key] = value
                
                if final_flags:
                    print(f"     🎯 Final deliverable flags:")
                    for key, value in final_flags.items():
                        print(f"       - {key}: {value}")
                else:
                    print(f"     ❌ No final deliverable flags found")
            else:
                print(f"     ⚠️  Context data is not a dict: {type(context_data)}")
            
            # Check result payload
            result_data = task.get("result")
            if result_data:
                print(f"     ✅ Has result payload (type: {type(result_data).__name__})")
                if isinstance(result_data, dict):
                    print(f"     Result keys: {list(result_data.keys())}")
                    
                    # Check for detailed_results_json
                    detailed_json = result_data.get("detailed_results_json")
                    if detailed_json:
                        print(f"     📊 Has detailed_results_json (length: {len(str(detailed_json))})")
                        try:
                            if isinstance(detailed_json, str):
                                parsed = json.loads(detailed_json)
                                print(f"     Parsed JSON keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                        except json.JSONDecodeError:
                            print(f"     ⚠️  detailed_results_json is malformed")
                    else:
                        print(f"     ❌ No detailed_results_json found")
            else:
                print(f"     ❌ No result payload")
        
        print(f"\n🎯 Tasks with Final Deliverable Flags: {len(final_deliverable_tasks)}")
        for task in final_deliverable_tasks:
            print(f"  • {task.get('name', 'Unnamed')} (Status: {task.get('status')})")
            context_data = task.get("context_data", {})
            if isinstance(context_data, dict):
                final_flags = {k: v for k, v in context_data.items() 
                             if ('final' in k.lower() or 'deliverable' in k.lower() or 
                                 'completion' in k.lower() or 'aggregation' in k.lower())}
                print(f"    Flags: {final_flags}")
        
        # Check what the API would find for final deliverables
        print(f"\n🔍 API Final Deliverable Detection Logic:")
        api_final_deliverable = None
        for task in [t for t in tasks if t.get("status") == "completed"]:
            context_data = task.get("context_data", {}) or {}
            if (context_data.get("is_final_deliverable") or 
                context_data.get("deliverable_aggregation") or
                context_data.get("triggers_project_completion")):
                api_final_deliverable = task
                break
        
        if api_final_deliverable:
            print(f"✅ API would find final deliverable: {api_final_deliverable.get('name')}")
            print(f"   ID: {api_final_deliverable['id']}")
            print(f"   Status: {api_final_deliverable.get('status')}")
        else:
            print(f"❌ API would NOT find a final deliverable task")
            print(f"   Completed tasks: {len([t for t in tasks if t.get('status') == 'completed'])}")
            print(f"   Tasks with deliverable flags: {len(final_deliverable_tasks)}")
        
        # Recommendations
        print(f"\n🔧 Debugging Recommendations:")
        if not intelligent_ai_tasks:
            print("  1. No intelligent_ai_deliverable tasks found - check task creation logic")
        elif not any(t.get('status') == 'completed' for t in intelligent_ai_tasks):
            print("  2. Intelligent AI tasks exist but none are completed")
        elif not api_final_deliverable:
            print("  3. Completed intelligent AI tasks exist but lack proper final deliverable flags")
            print("     Required flags: is_final_deliverable, deliverable_aggregation, or triggers_project_completion")
        else:
            print("  4. Final deliverable task found - check frontend API call and response processing")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()