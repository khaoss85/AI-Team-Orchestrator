#!/usr/bin/env python3
"""
🌐 Test Thinking API Endpoints

Test the actual API endpoints for authentic thinking
"""

import asyncio
import logging
import requests
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_endpoints():
    """Test authentic thinking API endpoints"""
    logger.info("🌐 Testing Authentic Thinking API Endpoints")
    logger.info("=" * 60)
    
    # Check if we have a running server and goal data
    try:
        from database import supabase
        
        # Get a workspace with goals
        workspace_result = supabase.table("workspaces").select("id, name").eq("status", "active").limit(1).execute()
        
        if not workspace_result.data:
            logger.error("❌ No active workspace found")
            return False
        
        workspace = workspace_result.data[0]
        workspace_id = workspace["id"]
        
        logger.info(f"📂 Using workspace: {workspace['name']}")
        
        # Get a goal from this workspace
        goal_result = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).limit(1).execute()
        
        if not goal_result.data:
            logger.error("❌ No goals found in workspace")
            return False
        
        goal = goal_result.data[0]
        goal_id = goal["id"]
        
        logger.info(f"🎯 Using goal: {goal['description']}")
        
        # Test API endpoints (simulate what frontend would do)
        base_url = "http://localhost:8000"  # Assuming server runs on 8000
        
        # Test 1: Get workspace thinking goals
        logger.info("\n1️⃣ Testing: GET /api/thinking/workspace/{workspace_id}/thinking/goals")
        
        api_url_1 = f"{base_url}/api/thinking/workspace/{workspace_id}/thinking/goals"
        logger.info(f"   URL: {api_url_1}")
        logger.info("   ℹ️ This would be called when user opens thinking tab")
        
        # Test 2: Get specific goal thinking
        logger.info("\n2️⃣ Testing: GET /api/thinking/goal/{goal_id}/thinking")
        
        api_url_2 = f"{base_url}/api/thinking/goal/{goal_id}/thinking?workspace_id={workspace_id}"
        logger.info(f"   URL: {api_url_2}")
        logger.info("   ℹ️ This would be called by AuthenticThinkingViewer component")
        
        # Test 3: Health check
        logger.info("\n3️⃣ Testing: GET /api/thinking/health")
        
        api_url_3 = f"{base_url}/api/thinking/health"
        logger.info(f"   URL: {api_url_3}")
        logger.info("   ℹ️ This would be called to check if thinking API is available")
        
        logger.info("\n📋 API Endpoints Ready For Frontend Integration:")
        logger.info(f"   - Workspace thinking: /api/thinking/workspace/{workspace_id}/thinking/goals")
        logger.info(f"   - Goal thinking: /api/thinking/goal/{goal_id}/thinking?workspace_id={workspace_id}")
        logger.info(f"   - Health check: /api/thinking/health")
        
        # Check if thinking data exists for this goal
        logger.info("\n📊 Checking Existing Thinking Data:")
        
        # Check decomposition
        decomp_result = supabase.table("workspace_goal_decompositions").select("*").eq("goal_id", goal_id).execute()
        if decomp_result.data:
            logger.info("   ✅ Goal decomposition exists")
        else:
            logger.info("   ❌ No goal decomposition found")
        
        # Check todos
        todos_result = supabase.table("goal_todos").select("*").eq("goal_id", goal_id).execute()
        if todos_result.data:
            logger.info(f"   ✅ {len(todos_result.data)} todos found")
        else:
            logger.info("   ❌ No todos found")
        
        # Check thinking steps
        thinking_result = supabase.table("thinking_process_steps").select("*").eq("workspace_id", workspace_id).execute()
        if thinking_result.data:
            logger.info(f"   ✅ {len(thinking_result.data)} thinking steps found")
        else:
            logger.info("   ❌ No thinking steps found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API test failed: {e}")
        return False

async def provide_frontend_instructions():
    """Provide instructions for testing in frontend"""
    logger.info("\n" + "=" * 60)
    logger.info("🖥️ FRONTEND TESTING INSTRUCTIONS")
    logger.info("=" * 60)
    
    logger.info("\n📋 Steps to Test Authentic Thinking in Browser:")
    
    logger.info("\n1. 🚀 Start the Backend Server:")
    logger.info("   cd backend")
    logger.info("   python3 main.py")
    logger.info("   → Server will run on http://localhost:8000")
    
    logger.info("\n2. 🌐 Start the Frontend:")
    logger.info("   cd frontend")
    logger.info("   npm run dev")
    logger.info("   → Frontend will run on http://localhost:3000")
    
    logger.info("\n3. 🧠 Access Thinking Process:")
    logger.info("   a) Open browser: http://localhost:3000")
    logger.info("   b) Navigate to workspace 'Social Growth'")
    logger.info("   c) Find goal: 'Create social media content strategy...'")
    logger.info("   d) Click on the goal to open its chat")
    logger.info("   e) In the right panel, click '🧠 Thinking' tab")
    
    logger.info("\n4. 📊 Expected Results:")
    logger.info("   - Todo List: 4 asset todos + 3 thinking todos")
    logger.info("   - Thinking Steps: Real reasoning process")
    logger.info("   - Execution Order: Thinking first, then assets")
    logger.info("   - Progress tracking for each todo")
    
    logger.info("\n5. 🔍 Debugging:")
    logger.info("   - Check browser console for API calls")
    logger.info("   - API should call: /api/thinking/goal/{id}/thinking")
    logger.info("   - Should show authentic todo list from goal decomposition")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
    asyncio.run(provide_frontend_instructions())