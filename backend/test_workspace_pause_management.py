#!/usr/bin/env python3
"""
Test Workspace Pause Management System
Verifies intelligent pause bypass and auto-recovery functionality
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_workspace_pause_management():
    """Test the workspace pause management system"""
    print("🧪 Testing Workspace Pause Management System...")
    
    try:
        from services.workspace_pause_manager import workspace_pause_manager
        from database import get_workspaces_with_pending_tasks
        
        # Test 1: Get pause status report
        print("\n📊 Test 1: Getting pause status report...")
        try:
            report = await workspace_pause_manager.get_pause_status_report()
            print(f"  📋 Total paused workspaces: {report.get('total_paused', 0)}")
            print(f"  📋 Recovery candidates: {len(report.get('recovery_candidates', []))}")
            print(f"  📋 High priority recoveries: {len(report.get('high_priority_recoveries', []))}")
            print(f"  📋 Total paused tasks: {report.get('total_paused_tasks', 0)}")
            print(f"  📋 Critical tasks in paused workspaces: {report.get('total_critical_tasks_paused', 0)}")
            
            if report.get('recovery_candidates'):
                print(f"  🔧 Top recovery candidates:")
                for candidate in report['recovery_candidates'][:3]:
                    print(f"    - W:{candidate['workspace_id'][:8]} Score: {candidate['recovery_score']:.1f}, Critical: {candidate['critical_tasks']}, Pending: {candidate['pending_tasks']}")
            
            print("  ✅ PASS: Pause status report generated successfully")
            
        except Exception as e:
            print(f"  ❌ FAIL: Error generating pause status report: {e}")
            return False
        
        # Test 2: Intelligent workspace selection
        print("\n🎯 Test 2: Testing intelligent workspace selection...")
        try:
            intelligent_workspaces = await workspace_pause_manager.get_intelligent_workspaces_with_pending_tasks()
            fallback_workspaces = []
            
            # Get fallback for comparison (temporarily disable intelligent manager)
            try:
                from database import supabase
                result = supabase.table("tasks").select("workspace_id, workspaces!inner(id, status)").eq("status", "pending").execute()
                
                if result.data:
                    for task in result.data:
                        workspace = task.get("workspaces")
                        if workspace and workspace.get("status") != "paused":
                            fallback_workspaces.append(task["workspace_id"])
                    fallback_workspaces = list(set(fallback_workspaces))
            except Exception as e:
                print(f"    Warning: Could not get fallback comparison: {e}")
            
            print(f"  📊 Intelligent selection: {len(intelligent_workspaces)} workspaces")
            print(f"  📊 Fallback selection: {len(fallback_workspaces)} workspaces")
            
            bypassed_count = len(intelligent_workspaces) - len(fallback_workspaces)
            if bypassed_count > 0:
                print(f"  🚨 CRITICAL BYPASS: {bypassed_count} paused workspaces allowed due to critical tasks")
            
            print("  ✅ PASS: Intelligent workspace selection working")
            
        except Exception as e:
            print(f"  ❌ FAIL: Error in intelligent workspace selection: {e}")
            return False
        
        # Test 3: Critical task detection
        print("\n🔍 Test 3: Testing critical task detection...")
        try:
            test_tasks = [
                {
                    "name": "URGENT: Close 40% gap in email sequences",
                    "description": "Critical corrective task to address goal validation failures",
                    "context_data": {"is_goal_driven_task": True, "task_type": "corrective"},
                    "priority": "high",
                    "created_at": "2025-06-29T10:00:00Z"
                },
                {
                    "name": "Regular development task",
                    "description": "Standard feature implementation",
                    "context_data": {},
                    "priority": "medium",
                    "created_at": "2025-06-29T08:00:00Z"
                }
            ]
            
            critical_count = 0
            for task in test_tasks:
                is_critical = await workspace_pause_manager._is_task_critical(task)
                if is_critical:
                    critical_count += 1
                    print(f"    ✓ Critical: '{task['name'][:40]}...'")
                else:
                    print(f"    - Regular: '{task['name'][:40]}...'")
            
            if critical_count == 1:  # Should detect 1 critical task
                print("  ✅ PASS: Critical task detection working correctly")
            else:
                print(f"  ❌ FAIL: Expected 1 critical task, found {critical_count}")
                return False
            
        except Exception as e:
            print(f"  ❌ FAIL: Error in critical task detection: {e}")
            return False
        
        # Test 4: Auto-recovery check
        print("\n🔄 Test 4: Testing auto-recovery check...")
        try:
            # This will check for recovery candidates but not actually recover
            print("    Running recovery analysis...")
            await workspace_pause_manager.check_and_recover_paused_workspaces()
            print("  ✅ PASS: Auto-recovery check completed without errors")
            
        except Exception as e:
            print(f"  ❌ FAIL: Error in auto-recovery check: {e}")
            return False
        
        # Test 5: Database integration
        print("\n🔗 Test 5: Testing database integration...")
        try:
            workspaces = await get_workspaces_with_pending_tasks()
            print(f"  📊 Found {len(workspaces)} workspaces with pending tasks")
            print("  ✅ PASS: Database integration working")
            
        except Exception as e:
            print(f"  ❌ FAIL: Error in database integration: {e}")
            return False
        
        print("\n🎉 All workspace pause management tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Could not import workspace pause manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Critical error in workspace pause management tests: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_workspace_pause_management())