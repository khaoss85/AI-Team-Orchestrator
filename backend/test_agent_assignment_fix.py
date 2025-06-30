#!/usr/bin/env python3
"""
Test the AI-driven backup agent assignment fix in _anti_loop_worker
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_agent_assignment_scenarios():
    """Test different scenarios of agent assignment in task execution"""
    
    print("🧪 Testing AI-driven backup agent assignment scenarios...")
    
    # Test scenarios to validate:
    # 1. Task with assigned_to_role but no agent_id
    # 2. Task with neither assigned_to_role nor agent_id 
    # 3. Task with agent_id already present
    
    test_scenarios = [
        {
            "name": "Task with role but no agent_id (should trigger backup assignment)",
            "task_dict": {
                "id": "test-task-1",
                "name": "Test Task with Role",
                "workspace_id": "bc41beb3-4380-434a-8280-92821006840e",
                "assigned_to_role": "Marketing Specialist",
                # "agent_id" missing - should trigger backup
                "priority": 5,
                "description": "Create marketing content"
            }
        },
        {
            "name": "Task without role and agent_id (should fail gracefully)",
            "task_dict": {
                "id": "test-task-2", 
                "name": "Task without Role or Agent",
                "workspace_id": "bc41beb3-4380-434a-8280-92821006840e",
                # Both "assigned_to_role" and "agent_id" missing
                "priority": 3,
                "description": "Generic task"
            }
        },
        {
            "name": "Task with existing agent_id (should proceed normally)",
            "task_dict": {
                "id": "test-task-3",
                "name": "Task with Agent ID", 
                "workspace_id": "bc41beb3-4380-434a-8280-92821006840e",
                "assigned_to_role": "Content Writer",
                "agent_id": "existing-agent-123",  # Already has agent_id
                "priority": 7,
                "description": "Write blog post"
            }
        }
    ]
    
    # Import the TaskExecutor logic to test the assignment method
    try:
        from executor import TaskExecutor
        from uuid import UUID
        
        # Create a test executor instance
        executor = TaskExecutor()
        
        for scenario in test_scenarios:
            print(f"\n🎯 Testing: {scenario['name']}")
            task_dict = scenario['task_dict']
            
            # Simulate the backup assignment logic from _anti_loop_worker
            current_agent_id = task_dict.get("agent_id")
            assigned_role = task_dict.get("assigned_to_role")
            workspace_id = task_dict.get("workspace_id")
            task_id = task_dict.get("id")
            
            print(f"   Initial state: agent_id={current_agent_id}, role={assigned_role}")
            
            if not current_agent_id and assigned_role:
                print(f"   ⚠️ Simulating backup assignment for role '{assigned_role}'")
                try:
                    assigned_agent_info = await executor._assign_agent_to_task_by_role(
                        task_dict, workspace_id, assigned_role
                    )
                    
                    if assigned_agent_info and "id" in assigned_agent_info:
                        task_dict["agent_id"] = str(assigned_agent_info["id"])
                        current_agent_id = str(assigned_agent_info["id"])
                        print(f"   ✅ Backup assignment successful: agent {assigned_agent_info['name']} (ID: {current_agent_id})")
                    else:
                        print(f"   ❌ Backup agent assignment failed")
                except Exception as e:
                    print(f"   ❌ Exception during backup assignment: {e}")
            
            # Final validation
            final_agent_id = task_dict.get("agent_id")
            if final_agent_id:
                print(f"   ✅ Task would proceed to execution with agent_id: {final_agent_id}")
            else:
                print(f"   ❌ Task would be failed - no agent_id after all attempts")
                
        print(f"\n🏁 Agent assignment testing complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_assignment_scenarios())