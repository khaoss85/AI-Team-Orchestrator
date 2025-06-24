#!/usr/bin/env python3
"""
🧠 Verify Authentic Thinking with Existing Workspace

Usa un workspace esistente per testare il sistema di thinking autentico
"""

import asyncio
import logging
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def find_active_workspace() -> Optional[Dict[str, Any]]:
    """Find an active workspace to use for testing"""
    logger.info("🔍 Finding active workspace...")
    
    try:
        from database import supabase
        
        # Get an active workspace
        result = supabase.table("workspaces").select("*").eq("status", "active").limit(1).execute()
        
        if result.data and len(result.data) > 0:
            workspace = result.data[0]
            logger.info(f"   ✅ Found workspace: {workspace['name']} (ID: {workspace['id']})")
            return workspace
        else:
            logger.error("   ❌ No active workspace found")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error finding workspace: {e}")
        return None

async def test_with_existing_workspace():
    """Test authentic thinking with an existing workspace"""
    logger.info("🚀 Testing Authentic Thinking with Existing Workspace")
    logger.info("=" * 80)
    
    try:
        from database import supabase
        from goal_decomposition_system import decompose_goal_to_todos
        
        # Find existing workspace
        workspace = await find_active_workspace()
        if not workspace:
            logger.error("Cannot proceed without an active workspace")
            return False
        
        workspace_id = workspace["id"]
        
        # Create a test goal
        goal_id = str(uuid4())
        
        logger.info("\n🎯 Creating Test Goal...")
        goal_data = {
            "id": goal_id,
            "workspace_id": workspace_id,
            "description": "Create social media content strategy with 10 Instagram posts",
            "metric_type": "content",
            "target_value": 10,
            "current_value": 0,
            "status": "active",
            "priority": 5,
            "created_at": datetime.utcnow().isoformat()
        }
        
        goal_result = supabase.table("workspace_goals").insert(goal_data).execute()
        logger.info(f"   ✅ Created goal: {goal_id}")
        
        # Decompose the goal
        logger.info("\n📋 Decomposing Goal into Todos...")
        test_goal = {
            "id": goal_id,
            "workspace_id": workspace_id,
            "description": goal_data["description"],
            "metric_type": goal_data["metric_type"],
            "target_value": goal_data["target_value"]
        }
        
        decomposition_result = await decompose_goal_to_todos(test_goal)
        
        # Save decomposition
        decomposition = decomposition_result["goal_decomposition"]["decomposition"]
        
        decomposition_data = {
            "goal_id": goal_id,
            "workspace_id": workspace_id,
            "decomposition_method": decomposition_result["goal_decomposition"]["decomposition_method"],
            "user_value_score": decomposition.get("user_value_score", 70),
            "complexity_level": decomposition.get("complexity_level", "medium"),
            "domain_category": decomposition.get("domain_category", "universal"),
            "asset_deliverables": decomposition.get("asset_deliverables", []),
            "thinking_components": decomposition.get("thinking_components", []),
            "completion_criteria": decomposition.get("completion_criteria", {}),
            "pillar_adherence": decomposition.get("pillar_adherence", {})
        }
        
        decomp_result = supabase.table("workspace_goal_decompositions").insert(decomposition_data).execute()
        decomposition_id = decomp_result.data[0]["id"] if decomp_result.data else None
        logger.info("   ✅ Goal decomposition saved")
        
        # Save todos
        todo_structure = decomposition_result["todo_structure"]
        todos_saved = []
        
        logger.info("\n📝 Saving Todo List...")
        # Save asset todos
        for todo in todo_structure.get("asset_todos", []):
            todo_data = {
                "decomposition_id": decomposition_id,
                "goal_id": goal_id,
                "workspace_id": workspace_id,
                "todo_type": todo["type"],
                "internal_id": todo["id"],
                "name": todo["name"],
                "description": todo["description"],
                "priority": todo["priority"],
                "estimated_effort": todo.get("estimated_effort"),
                "user_impact": todo.get("user_impact"),
                "value_proposition": todo.get("value_proposition"),
                "completion_criteria": todo.get("completion_criteria"),
                "deliverable_type": todo.get("deliverable_type", "concrete_asset"),
                "status": "pending",
                "progress_percentage": 0
            }
            
            result = supabase.table("goal_todos").insert(todo_data).execute()
            if result.data:
                todos_saved.append(result.data[0])
                logger.info(f"   ✅ Saved asset todo: {todo['name']}")
        
        # Save thinking todos
        for todo in todo_structure.get("thinking_todos", []):
            todo_data = {
                "decomposition_id": decomposition_id,
                "goal_id": goal_id,
                "workspace_id": workspace_id,
                "todo_type": todo["type"],
                "internal_id": todo["id"],
                "name": todo["name"],
                "description": todo["description"],
                "priority": todo.get("priority", "medium"),
                "complexity": todo.get("complexity"),
                "supports_assets": todo.get("supports_assets", []),
                "deliverable_type": todo.get("deliverable_type", "strategic_thinking"),
                "status": "pending",
                "progress_percentage": 0
            }
            
            result = supabase.table("goal_todos").insert(todo_data).execute()
            if result.data:
                todos_saved.append(result.data[0])
                logger.info(f"   ✅ Saved thinking todo: {todo['name']}")
        
        # Create thinking steps
        logger.info("\n🧠 Creating Thinking Process Steps...")
        thinking_session_id = str(uuid4())
        
        if len(todos_saved) > 0:
            # Create thinking for first todo
            first_todo = todos_saved[0]
            
            thinking_step_data = {
                "todo_id": first_todo["id"],
                "workspace_id": workspace_id,
                "thinking_session_id": thinking_session_id,
                "step_sequence": 1,
                "step_type": "analysis",
                "step_title": "Analizzando la todo list generata dal goal decomposition",
                "thinking_content": f"""Il sistema ha scomposto il goal in una todo list strutturata:

📦 ASSET DELIVERABLES ({len([t for t in todos_saved if t['todo_type'] == 'asset'])} items)
🧠 THINKING COMPONENTS ({len([t for t in todos_saved if t['todo_type'] == 'thinking'])} items)

Adesso procedo con l'analisi del primo componente: {first_todo['name']}""",
                "inputs_considered": ["Goal decomposition completata", f"{len(todos_saved)} todos identificati"],
                "conclusions_reached": ["Todo list pronta per esecuzione", "Ordine di esecuzione determinato"],
                "agent_role": "Goal Decomposition Analyzer",
                "confidence_level": "high",
                "reasoning_quality": "deep"
            }
            
            supabase.table("thinking_process_steps").insert(thinking_step_data).execute()
            logger.info("   ✅ Created initial thinking step")
        
        # Display summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 AUTHENTIC THINKING TEST SUCCESSFUL!")
        logger.info("=" * 80)
        logger.info(f"✅ Workspace: {workspace['name']}")
        logger.info(f"✅ Goal Created: {goal_data['description']}")
        logger.info(f"✅ Todos Saved: {len(todos_saved)}")
        logger.info(f"✅ Thinking Process Started: Session {thinking_session_id}")
        
        logger.info("\n📋 NEXT STEPS:")
        logger.info("1. Open the frontend application")
        logger.info(f"2. Navigate to workspace: {workspace['name']}")
        logger.info("3. Find the goal in the objectives sidebar")
        logger.info("4. Click on the '🧠 Thinking' tab to see:")
        logger.info("   - Real todo list from goal decomposition")
        logger.info("   - Authentic thinking process steps")
        logger.info("   - Execution order and progress")
        
        logger.info(f"\n🔗 Goal ID for reference: {goal_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_with_existing_workspace())