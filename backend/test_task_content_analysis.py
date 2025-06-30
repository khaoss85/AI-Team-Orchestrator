#!/usr/bin/env python3
"""
Detailed analysis of task content to understand why deliverables show generic content
"""

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_task_content():
    """Analyze the actual content in completed tasks"""
    try:
        from database import list_tasks
        
        workspace_id = 'ad8424d8-f95a-4a41-8e8e-bc131a9c54f6'
        
        print(f"\n🔍 DETAILED TASK CONTENT ANALYSIS")
        print(f"Workspace ID: {workspace_id}")
        print("=" * 60)
        
        # Get completed tasks
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
        print(f"Found {len(completed_tasks)} completed tasks")
        
        for i, task in enumerate(completed_tasks, 1):
            print(f"\n📋 TASK {i}: {task.get('name', 'No name')}")
            print("=" * 40)
            print(f"Status: {task.get('status')}")
            print(f"Agent: {task.get('agent_id')}")
            print(f"Created: {task.get('created_at')}")
            
            # Analyze the result structure
            result = task.get('result', {})
            print(f"\nResult Structure:")
            if isinstance(result, dict):
                print(f"  Keys: {list(result.keys())}")
                
                # Check different result formats
                if 'detailed_results_json' in result:
                    detailed_results = result['detailed_results_json']
                    print(f"  detailed_results_json type: {type(detailed_results)}")
                    
                    if isinstance(detailed_results, str):
                        try:
                            parsed = json.loads(detailed_results)
                            print(f"  Parsed JSON keys: {list(parsed.keys())}")
                            
                            # Look for email sequence content
                            for key, value in parsed.items():
                                if 'email' in key.lower() or 'sequence' in key.lower():
                                    print(f"\n  📧 EMAIL CONTENT FOUND in {key}:")
                                    print(f"    {str(value)[:200]}...")
                                    
                        except json.JSONDecodeError:
                            print(f"  detailed_results_json (raw): {str(detailed_results)[:200]}...")
                    else:
                        print(f"  detailed_results_json: {str(detailed_results)[:200]}...")
                
                if 'summary' in result:
                    summary = result['summary']
                    print(f"  Summary: {str(summary)[:200]}...")
                
                # Check for actual task output/content
                if 'output' in result:
                    output = result['output']
                    print(f"  Output: {str(output)[:200]}...")
                    
                # Look for any field that might contain real content
                for key, value in result.items():
                    if key not in ['status', 'task_id', 'model_used', 'tokens_used', 'cost_estimated']:
                        value_str = str(value)
                        if len(value_str) > 100:  # Substantial content
                            print(f"  {key}: {value_str[:150]}...")
            else:
                print(f"  Result (non-dict): {str(result)[:200]}...")
            
            # Check if task contains any real email sequence content
            task_str = json.dumps(task, default=str).lower()
            
            email_indicators = ['subject:', 'from:', 'body:', 'email template', 'dear', 'best regards']
            found_email_content = [indicator for indicator in email_indicators if indicator in task_str]
            
            if found_email_content:
                print(f"\n  ✅ REAL EMAIL CONTENT INDICATORS: {found_email_content}")
            else:
                print(f"\n  ❌ NO REAL EMAIL CONTENT FOUND")
            
            print("\n" + "-" * 40)
        
        # Summary Analysis
        print(f"\n📊 SUMMARY ANALYSIS")
        print("=" * 30)
        
        # Check if tasks contain substantial content
        tasks_with_content = 0
        tasks_with_email_content = 0
        
        for task in completed_tasks:
            result = task.get('result', {})
            
            # Check for substantial content
            if isinstance(result, dict):
                for key, value in result.items():
                    if len(str(value)) > 100:
                        tasks_with_content += 1
                        break
            
            # Check for email-specific content
            task_str = json.dumps(task, default=str).lower()
            if any(indicator in task_str for indicator in ['subject:', 'from:', 'body:', 'email template']):
                tasks_with_email_content += 1
        
        print(f"Tasks with substantial content: {tasks_with_content}/{len(completed_tasks)}")
        print(f"Tasks with email content: {tasks_with_email_content}/{len(completed_tasks)}")
        
        # Root cause analysis
        print(f"\n🎯 ROOT CAUSE ANALYSIS")
        print("=" * 30)
        
        if tasks_with_email_content == 0:
            print("❌ PROBLEM IDENTIFIED: No tasks contain real email sequences!")
            print("   The tasks completed but didn't generate actual email content.")
            print("   This is why deliverables show generic templates.")
            print("\n💡 SOLUTION:")
            print("   1. Tasks need to generate actual email content (subject, body, etc.)")
            print("   2. AI system should detect when task output is incomplete")
            print("   3. Asset generation should create real email sequences when missing")
        else:
            print("✅ Tasks do contain email content")
            print("❌ Problem is in deliverable extraction/mapping process")
        
        return completed_tasks
        
    except Exception as e:
        print(f"❌ Error in task content analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main analysis function"""
    print("🚀 Starting Detailed Task Content Analysis")
    tasks = await analyze_task_content()

if __name__ == "__main__":
    asyncio.run(main())