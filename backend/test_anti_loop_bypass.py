#!/usr/bin/env python3
"""
Test Anti-Loop Bypass for Critical Tasks
Verifies that critical corrective tasks can bypass the anti-loop task limit
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_anti_loop_bypass():
    """Test the anti-loop bypass functionality"""
    print("🧪 Testing Anti-Loop Bypass for Critical Tasks...")
    
    try:
        from executor import TaskExecutor
        from models import TaskStatus
        from uuid import uuid4
        
        # Create task executor instance
        executor = TaskExecutor()
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Goal-driven corrective task",
                "task_dict": {
                    "id": str(uuid4()),
                    "name": "Fix goal completion issue",
                    "description": "Corrective task to address goal validation failures",
                    "workspace_id": "test-workspace-123",
                    "status": TaskStatus.PENDING.value,
                    "priority": "high",
                    "context_data": {
                        "is_goal_driven_task": True,
                        "task_type": "corrective_validation"
                    },
                    "created_at": "2025-06-29T10:00:00Z"
                },
                "expected_critical": True
            },
            {
                "name": "Critical keyword task",
                "task_dict": {
                    "id": str(uuid4()),
                    "name": "Emergency system repair required",
                    "description": "Urgent fix needed for critical system component",
                    "workspace_id": "test-workspace-456",
                    "status": TaskStatus.PENDING.value,
                    "priority": "high",
                    "created_at": "2025-06-29T10:00:00Z"
                },
                "expected_critical": True
            },
            {
                "name": "Deliverable creation task",
                "task_dict": {
                    "id": str(uuid4()),
                    "name": "Create final deliverable package",
                    "description": "Generate deliverable for completed project goals",
                    "workspace_id": "test-workspace-789",
                    "status": TaskStatus.PENDING.value,
                    "priority": "medium",
                    "created_at": "2025-06-29T10:00:00Z"
                },
                "expected_critical": True
            },
            {
                "name": "Regular task (should not bypass)",
                "task_dict": {
                    "id": str(uuid4()),
                    "name": "Regular development task",
                    "description": "Standard feature implementation",
                    "workspace_id": "test-workspace-999",
                    "status": TaskStatus.PENDING.value,
                    "priority": "medium",
                    "created_at": "2025-06-29T08:00:00Z"
                },
                "expected_critical": False
            }
        ]
        
        # Test each scenario
        results = []
        for scenario in test_scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            
            task_dict = scenario["task_dict"]
            expected = scenario["expected_critical"]
            
            try:
                is_critical = await executor._is_critical_corrective_task(task_dict)
                
                if is_critical == expected:
                    print(f"  ✅ PASS: Critical detection = {is_critical} (expected {expected})")
                    results.append(True)
                else:
                    print(f"  ❌ FAIL: Critical detection = {is_critical} (expected {expected})")
                    results.append(False)
                    
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                results.append(False)
        
        # Test anti-loop validation bypass
        print(f"\n🔧 Testing anti-loop validation bypass...")
        
        # Simulate workspace at limit
        test_workspace_id = "test-workspace-at-limit"
        executor.workspace_anti_loop_task_counts[test_workspace_id] = executor.max_tasks_per_workspace_anti_loop
        
        # Test critical task bypass
        critical_task = {
            "id": str(uuid4()),
            "name": "Critical goal completion fix",
            "description": "Emergency corrective task for goal validation",
            "workspace_id": test_workspace_id,
            "status": TaskStatus.PENDING.value,
            "priority": "high",
            "context_data": {
                "is_goal_driven_task": True,
                "task_type": "corrective_validation"
            },
            "created_at": "2025-06-29T10:00:00Z"
        }
        
        try:
            # This should return True (bypass limit)
            can_execute_critical = await executor._validate_task_execution(critical_task)
            if can_execute_critical:
                print(f"  ✅ PASS: Critical task bypassed anti-loop limit")
                results.append(True)
            else:
                print(f"  ❌ FAIL: Critical task blocked by anti-loop limit")
                results.append(False)
        except Exception as e:
            print(f"  ❌ ERROR in bypass test: {e}")
            results.append(False)
        
        # Test regular task blocked
        regular_task = {
            "id": str(uuid4()),
            "name": "Regular task",
            "description": "Standard task",
            "workspace_id": test_workspace_id,
            "status": TaskStatus.PENDING.value,
            "priority": "medium",
            "created_at": "2025-06-29T08:00:00Z"
        }
        
        try:
            # This should return False (blocked by limit)
            can_execute_regular = await executor._validate_task_execution(regular_task)
            if not can_execute_regular:
                print(f"  ✅ PASS: Regular task correctly blocked by anti-loop limit")
                results.append(True)
            else:
                print(f"  ❌ FAIL: Regular task incorrectly bypassed anti-loop limit")
                results.append(False)
        except Exception as e:
            print(f"  ❌ ERROR in regular task test: {e}")
            results.append(False)
        
        # Final results
        passed = sum(results)
        total = len(results)
        
        print(f"\n🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All anti-loop bypass tests passed!")
            return True
        else:
            print(f"⚠️ {total - passed} tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Critical error in anti-loop bypass tests: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_anti_loop_bypass())