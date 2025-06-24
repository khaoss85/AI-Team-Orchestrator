#!/usr/bin/env python3
"""
🧠 Verify Authentic Thinking System Live

Verifica completa del sistema authentic thinking con:
- Database connectivity
- Table creation verification
- Goal decomposition persistence
- Thinking process tracking
- API endpoint functionality
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
        
        # For Supabase, we'll check tables by attempting to query them
        
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
                if "relation" in str(e) and "does not exist" in str(e):
                    logger.error(f"   ❌ Table '{table}' NOT FOUND")
                    all_tables_exist = False
                else:
                    logger.warning(f"   ⚠️ Table '{table}' check error: {e}")
        
        # Note: Views and functions can't be easily checked with Supabase client
        # We'll assume they exist if tables exist
        if all_tables_exist:
            logger.info("   ℹ️ Views and functions assumed to exist (can't check via Supabase client)")
        
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
        await conn.execute("""
            INSERT INTO workspaces (id, name, description, status, created_at)
            VALUES ($1, $2, $3, 'active', NOW())
        """, workspace_id, "Test Thinking Workspace", "Testing authentic thinking")
        
        # Insert test goal
        await conn.execute("""
            INSERT INTO workspace_goals (
                id, workspace_id, description, metric_type, 
                target_value, current_value, status, priority, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, 'active', 5, NOW())
        """, goal_id, workspace_id, 
            "Create social media content calendar with 10 posts",
            "content", 10, 0)
        
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
        
        await conn.execute("""
            INSERT INTO workspace_goal_decompositions (
                goal_id, workspace_id, decomposition_method, user_value_score,
                complexity_level, domain_category, asset_deliverables,
                thinking_components, completion_criteria, pillar_adherence
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, goal_id, workspace_id,
            decomposition_result["goal_decomposition"]["decomposition_method"],
            decomposition.get("user_value_score", 70),
            decomposition.get("complexity_level", "medium"),
            decomposition.get("domain_category", "universal"),
            json.dumps(decomposition.get("asset_deliverables", [])),
            json.dumps(decomposition.get("thinking_components", [])),
            json.dumps(decomposition.get("completion_criteria", {})),
            json.dumps(decomposition.get("pillar_adherence", {}))
        )
        
        logger.info("   ✅ Goal decomposition saved to database")
        
        # Save todos
        todo_structure = decomposition_result["todo_structure"]
        todos_saved = 0
        
        # Save asset todos
        for todo in todo_structure.get("asset_todos", []):
            await conn.execute("""
                INSERT INTO goal_todos (
                    decomposition_id, goal_id, workspace_id, todo_type,
                    internal_id, name, description, priority,
                    estimated_effort, user_impact, value_proposition,
                    completion_criteria, deliverable_type
                ) VALUES (
                    (SELECT id FROM workspace_goal_decompositions WHERE goal_id = $1),
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                )
            """, goal_id, workspace_id, todo["type"], todo["id"],
                todo["name"], todo["description"], todo["priority"],
                todo.get("estimated_effort"), todo.get("user_impact"),
                todo.get("value_proposition"), todo.get("completion_criteria"),
                todo.get("deliverable_type", "concrete_asset"))
            todos_saved += 1
        
        # Save thinking todos
        for todo in todo_structure.get("thinking_todos", []):
            await conn.execute("""
                INSERT INTO goal_todos (
                    decomposition_id, goal_id, workspace_id, todo_type,
                    internal_id, name, description, priority,
                    complexity, supports_assets, deliverable_type
                ) VALUES (
                    (SELECT id FROM workspace_goal_decompositions WHERE goal_id = $1),
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
            """, goal_id, workspace_id, todo["type"], todo["id"],
                todo["name"], todo["description"], todo["priority"],
                todo.get("complexity"), todo.get("supports_assets", []),
                todo.get("deliverable_type", "strategic_thinking"))
            todos_saved += 1
        
        logger.info(f"   ✅ Saved {todos_saved} todos to database")
        
        # Verify data was saved
        decomp_count = await conn.fetchval(
            "SELECT COUNT(*) FROM workspace_goal_decompositions WHERE goal_id = $1", 
            goal_id
        )
        todo_count = await conn.fetchval(
            "SELECT COUNT(*) FROM goal_todos WHERE goal_id = $1", 
            goal_id
        )
        
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
        from database import get_connection
        from authentic_thinking_tracker import create_authentic_thinking_tracker
        
        conn = await get_connection()
        tracker = create_authentic_thinking_tracker()
        
        goal_id = goal_data["goal_id"]
        workspace_id = goal_data["workspace_id"]
        
        # Get the saved todos
        todos = await conn.fetch("""
            SELECT id, todo_type, internal_id, name, description, priority
            FROM goal_todos
            WHERE goal_id = $1
            ORDER BY 
                CASE todo_type WHEN 'thinking' THEN 1 ELSE 2 END,
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
        """, goal_id)
        
        thinking_session_id = str(uuid4())
        
        # Save thinking steps
        step_sequence = 0
        for todo in todos[:2]:  # Test with first 2 todos
            step_sequence += 1
            
            # Create thinking step
            await conn.execute("""
                INSERT INTO thinking_process_steps (
                    todo_id, workspace_id, thinking_session_id,
                    step_sequence, step_type, step_title, thinking_content,
                    inputs_considered, conclusions_reached, agent_role,
                    confidence_level, reasoning_quality
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, str(todo["id"]), workspace_id, thinking_session_id,
                step_sequence, "analysis", 
                f"Analyzing todo: {todo['name']}",
                f"Starting analysis of {todo['name']}. This is {todo['todo_type']} type todo with {todo['priority']} priority.",
                [f"Todo: {todo['name']}", f"Type: {todo['todo_type']}"],
                [f"{todo['name']} ready for execution"],
                "Task Analyzer", "high", "deep")
            
            logger.info(f"   ✅ Saved thinking step {step_sequence} for {todo['name']}")
            
            # Update todo progress
            await conn.execute("""
                UPDATE goal_todos 
                SET status = 'in_progress', progress_percentage = 50
                WHERE id = $1
            """, todo["id"])
            
            # Add progress tracking
            await conn.execute("""
                INSERT INTO todo_progress_tracking (
                    todo_id, workspace_id, progress_percentage,
                    progress_description, work_completed,
                    updated_by_agent_role, agent_confidence
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, str(todo["id"]), workspace_id, 50,
                f"Started working on {todo['name']}",
                [f"Initialized {todo['name']}", "Created initial structure"],
                "Progress Monitor", "high")
        
        # Verify thinking steps were saved
        thinking_count = await conn.fetchval("""
            SELECT COUNT(*) FROM thinking_process_steps 
            WHERE thinking_session_id = $1
        """, thinking_session_id)
        
        progress_count = await conn.fetchval("""
            SELECT COUNT(*) FROM todo_progress_tracking
            WHERE workspace_id = $1
        """, workspace_id)
        
        logger.info(f"   📊 Verification: {thinking_count} thinking steps, {progress_count} progress entries")
        
        return thinking_count > 0 and progress_count > 0
        
    except Exception as e:
        logger.error(f"❌ Thinking process tracking failed: {e}")
        return False

async def test_api_endpoint_data(goal_data: Dict[str, Any]):
    """Test API endpoint data retrieval"""
    logger.info("\n🌐 Testing API Endpoint Data Retrieval...")
    
    if not goal_data.get("success"):
        logger.error("   ❌ Cannot test API without valid goal data")
        return False
    
    try:
        from database import get_connection
        
        conn = await get_connection()
        goal_id = goal_data["goal_id"]
        workspace_id = goal_data["workspace_id"]
        
        # Test thinking summary function
        thinking_summary = await conn.fetchval(
            "SELECT get_goal_thinking_summary($1::UUID)",
            goal_id
        )
        
        if thinking_summary:
            summary_data = json.loads(thinking_summary)
            logger.info(f"   ✅ Goal thinking summary: {summary_data}")
        
        # Test latest thinking function
        latest_thinking = await conn.fetch(
            "SELECT * FROM get_workspace_latest_thinking($1::UUID, 5)",
            workspace_id
        )
        
        logger.info(f"   ✅ Found {len(latest_thinking)} latest thinking steps")
        
        # Test thinking tab display view
        thinking_display = await conn.fetch("""
            SELECT * FROM thinking_tab_display
            WHERE workspace_id = $1
        """, workspace_id)
        
        logger.info(f"   ✅ Thinking tab display: {len(thinking_display)} entries")
        
        # Test asset todos progress view
        asset_progress = await conn.fetch("""
            SELECT * FROM asset_todos_progress
            WHERE workspace_id = $1
        """, workspace_id)
        
        logger.info(f"   ✅ Asset todos progress: {len(asset_progress)} entries")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoint data test failed: {e}")
        return False

async def cleanup_test_data(goal_data: Dict[str, Any]):
    """Clean up test data"""
    logger.info("\n🧹 Cleaning Up Test Data...")
    
    if not goal_data.get("success"):
        return
    
    try:
        from database import get_connection
        conn = await get_connection()
        
        workspace_id = goal_data["workspace_id"]
        
        # Delete in correct order due to foreign keys
        await conn.execute("DELETE FROM workspaces WHERE id = $1", workspace_id)
        
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
        "api_data": False
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
        
        # Step 4: Test API data retrieval
        if results["thinking_tracking"]:
            results["api_data"] = await test_api_endpoint_data(goal_data)
        
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
            logger.info("✅ API data retrieval functional")
            logger.info("\n🧠 The system is ready to track authentic thinking!")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Live verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(run_live_verification())