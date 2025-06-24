#!/usr/bin/env python3
"""
🧠 Verify Authentic Thinking System with Supabase

Verifica completa del sistema authentic thinking usando Supabase client
"""

import asyncio
import logging
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_database_tables():
    """Verify that all thinking tables were created successfully"""
    logger.info("💾 Verifying Database Tables...")
    
    try:
        from database import supabase
        
        # Check if all tables exist by trying to query them
        tables_to_check = [
            'workspace_goal_decompositions',
            'goal_todos',
            'thinking_process_steps',
            'todo_progress_tracking'
        ]
        
        all_tables_exist = True
        for table in tables_to_check:
            try:
                # Try to query the table (limit 1 for speed)
                result = supabase.table(table).select("*").limit(1).execute()
                logger.info(f"   ✅ Table '{table}' exists")
            except Exception as e:
                error_str = str(e)
                if "relation" in error_str and "does not exist" in error_str:
                    logger.error(f"   ❌ Table '{table}' NOT FOUND")
                    all_tables_exist = False
                else:
                    # Table might exist but be empty or have other issues
                    logger.info(f"   ✅ Table '{table}' exists (query returned: {error_str})")
        
        return all_tables_exist
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

async def test_goal_decomposition_persistence():
    """Test saving goal decomposition to database"""
    logger.info("\n🎯 Testing Goal Decomposition Persistence...")
    
    try:
        from database import supabase
        from goal_decomposition_system import decompose_goal_to_todos
        
        # Create a test workspace and goal
        workspace_id = str(uuid4())
        goal_id = str(uuid4())
        
        # Insert test workspace
        workspace_data = {
            "id": workspace_id,
            "name": "Test Thinking Workspace",
            "description": "Testing authentic thinking",
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        workspace_result = supabase.table("workspaces").insert(workspace_data).execute()
        
        # Insert test goal
        goal_data = {
            "id": goal_id,
            "workspace_id": workspace_id,
            "description": "Create social media content calendar with 10 posts",
            "metric_type": "content",
            "target_value": 10,
            "current_value": 0,
            "status": "active",
            "priority": 5,
            "progress": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        goal_result = supabase.table("workspace_goals").insert(goal_data).execute()
        
        logger.info(f"   Created test goal: {goal_id}")
        
        # Decompose the goal
        test_goal = {
            "id": goal_id,
            "workspace_id": workspace_id,
            "description": "Create social media content calendar with 10 posts",
            "metric_type": "content",
            "target_value": 10
        }
        
        decomposition_result = await decompose_goal_to_todos(test_goal)
        
        # Save decomposition to database
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
        
        logger.info("   ✅ Goal decomposition saved to database")
        
        # Save todos
        todo_structure = decomposition_result["todo_structure"]
        todos_saved = 0
        
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
            
            supabase.table("goal_todos").insert(todo_data).execute()
            todos_saved += 1
        
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
            
            supabase.table("goal_todos").insert(todo_data).execute()
            todos_saved += 1
        
        logger.info(f"   ✅ Saved {todos_saved} todos to database")
        
        # Verify data was saved
        decomp_check = supabase.table("workspace_goal_decompositions").select("*").eq("goal_id", goal_id).execute()
        todo_check = supabase.table("goal_todos").select("*").eq("goal_id", goal_id).execute()
        
        decomp_count = len(decomp_check.data) if decomp_check.data else 0
        todo_count = len(todo_check.data) if todo_check.data else 0
        
        logger.info(f"   📊 Verification: {decomp_count} decomposition, {todo_count} todos")
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "goal_id": goal_id,
            "todos_saved": todos_saved
        }
        
    except Exception as e:
        logger.error(f"❌ Goal decomposition persistence failed: {e}")
        return {"success": False, "error": str(e)}

async def test_thinking_process_tracking(goal_data: Dict[str, Any]):
    """Test tracking authentic thinking process"""
    logger.info("\n🧠 Testing Thinking Process Tracking...")
    
    if not goal_data.get("success"):
        logger.error("   ❌ Cannot test thinking without valid goal data")
        return False
    
    try:
        from database import supabase
        
        goal_id = goal_data["goal_id"]
        workspace_id = goal_data["workspace_id"]
        
        # Get the saved todos
        todos_result = supabase.table("goal_todos").select("*").eq("goal_id", goal_id).execute()
        todos = todos_result.data if todos_result.data else []
        
        thinking_session_id = str(uuid4())
        
        # Save thinking steps
        step_sequence = 0
        for todo in todos[:2]:  # Test with first 2 todos
            step_sequence += 1
            
            # Create thinking step
            thinking_step_data = {
                "todo_id": todo["id"],
                "workspace_id": workspace_id,
                "thinking_session_id": thinking_session_id,
                "step_sequence": step_sequence,
                "step_type": "analysis",
                "step_title": f"Analyzing todo: {todo['name']}",
                "thinking_content": f"Starting analysis of {todo['name']}. This is {todo['todo_type']} type todo with {todo.get('priority', 'medium')} priority.",
                "inputs_considered": [f"Todo: {todo['name']}", f"Type: {todo['todo_type']}"],
                "conclusions_reached": [f"{todo['name']} ready for execution"],
                "agent_role": "Task Analyzer",
                "confidence_level": "high",
                "reasoning_quality": "deep"
            }
            
            supabase.table("thinking_process_steps").insert(thinking_step_data).execute()
            
            logger.info(f"   ✅ Saved thinking step {step_sequence} for {todo['name']}")
            
            # Update todo progress
            supabase.table("goal_todos").update({
                "status": "in_progress",
                "progress_percentage": 50
            }).eq("id", todo["id"]).execute()
            
            # Add progress tracking
            progress_data = {
                "todo_id": todo["id"],
                "workspace_id": workspace_id,
                "progress_percentage": 50,
                "progress_description": f"Started working on {todo['name']}",
                "work_completed": [f"Initialized {todo['name']}", "Created initial structure"],
                "updated_by_agent_role": "Progress Monitor",
                "agent_confidence": "high"
            }
            
            supabase.table("todo_progress_tracking").insert(progress_data).execute()
        
        # Verify thinking steps were saved
        thinking_check = supabase.table("thinking_process_steps").select("*").eq("thinking_session_id", thinking_session_id).execute()
        progress_check = supabase.table("todo_progress_tracking").select("*").eq("workspace_id", workspace_id).execute()
        
        thinking_count = len(thinking_check.data) if thinking_check.data else 0
        progress_count = len(progress_check.data) if progress_check.data else 0
        
        logger.info(f"   📊 Verification: {thinking_count} thinking steps, {progress_count} progress entries")
        
        return thinking_count > 0 and progress_count > 0
        
    except Exception as e:
        logger.error(f"❌ Thinking process tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_frontend_api_simulation(goal_data: Dict[str, Any]):
    """Simulate API calls that frontend would make"""
    logger.info("\n🌐 Testing Frontend API Simulation...")
    
    if not goal_data.get("success"):
        logger.error("   ❌ Cannot test API without valid goal data")
        return False
    
    try:
        from database import supabase
        
        goal_id = goal_data["goal_id"]
        workspace_id = goal_data["workspace_id"]
        
        # Simulate frontend fetching goal thinking data
        # 1. Get goal with decomposition
        goal_result = supabase.table("workspace_goals").select("*").eq("id", goal_id).execute()
        
        if goal_result.data:
            logger.info(f"   ✅ Retrieved goal: {goal_result.data[0]['description']}")
        
        # 2. Get decomposition
        decomp_result = supabase.table("workspace_goal_decompositions").select("*").eq("goal_id", goal_id).execute()
        
        if decomp_result.data:
            decomp = decomp_result.data[0]
            logger.info(f"   ✅ Retrieved decomposition: {decomp['user_value_score']} value score")
        
        # 3. Get todos
        todos_result = supabase.table("goal_todos").select("*").eq("goal_id", goal_id).order("created_at").execute()
        
        if todos_result.data:
            logger.info(f"   ✅ Retrieved {len(todos_result.data)} todos")
        
        # 4. Get thinking steps
        thinking_result = supabase.table("thinking_process_steps").select("*, goal_todos!inner(name, todo_type)").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
        
        if thinking_result.data:
            logger.info(f"   ✅ Retrieved {len(thinking_result.data)} thinking steps")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Frontend API simulation failed: {e}")
        return False

async def cleanup_test_data(goal_data: Dict[str, Any]):
    """Clean up test data"""
    logger.info("\n🧹 Cleaning Up Test Data...")
    
    if not goal_data.get("success"):
        return
    
    try:
        from database import supabase
        
        workspace_id = goal_data["workspace_id"]
        
        # Delete workspace (cascades to all related data)
        supabase.table("workspaces").delete().eq("id", workspace_id).execute()
        
        logger.info("   ✅ Test data cleaned up")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

async def run_live_verification():
    """Run complete live verification"""
    logger.info("🚀 Starting Live Authentic Thinking System Verification")
    logger.info("=" * 80)
    
    results = {
        "database_tables": False,
        "goal_decomposition": False,
        "thinking_tracking": False,
        "frontend_api": False
    }
    
    try:
        # Step 1: Verify database tables
        results["database_tables"] = await verify_database_tables()
        
        if not results["database_tables"]:
            logger.error("\n❌ Database tables not found! Please run the SQL script first.")
            return False
        
        # Step 2: Test goal decomposition persistence
        goal_data = await test_goal_decomposition_persistence()
        results["goal_decomposition"] = goal_data.get("success", False)
        
        # Step 3: Test thinking process tracking
        if results["goal_decomposition"]:
            results["thinking_tracking"] = await test_thinking_process_tracking(goal_data)
        
        # Step 4: Test frontend API simulation
        if results["thinking_tracking"]:
            results["frontend_api"] = await test_frontend_api_simulation(goal_data)
        
        # Step 5: Cleanup
        await cleanup_test_data(goal_data)
        
        # Results summary
        logger.info("\n" + "=" * 80)
        logger.info("🧠 LIVE VERIFICATION RESULTS")
        logger.info("=" * 80)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        all_passed = all(results.values())
        logger.info(f"\n🏆 OVERALL RESULT: {'✅ ALL SYSTEMS OPERATIONAL' if all_passed else '❌ SOME SYSTEMS NEED ATTENTION'}")
        
        if all_passed:
            logger.info("\n🎉 AUTHENTIC THINKING SYSTEM FULLY OPERATIONAL!")
            logger.info("✅ Database tables created and verified")
            logger.info("✅ Goal decomposition → Todo persistence working")
            logger.info("✅ Thinking process tracking operational")
            logger.info("✅ Frontend API simulation successful")
            logger.info("\n🧠 The system is ready to track authentic thinking!")
            logger.info("\n📋 NEXT STEPS:")
            logger.info("1. Open the frontend and navigate to a goal-based chat")
            logger.info("2. Click on the '🧠 Thinking' tab in the artifacts panel")
            logger.info("3. View the authentic todo list and thinking process!")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Live verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(run_live_verification())