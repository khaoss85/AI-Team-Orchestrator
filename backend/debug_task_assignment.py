#!/usr/bin/env python3
"""
Debug task assignment - identify why tasks aren't being processed
"""

import asyncio
import logging
from database import supabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def debug_task_assignment():
    """Debug task assignment problem"""
    logger.info("🔍 DEBUGGING TASK ASSIGNMENT")
    logger.info("="*50)
    
    # Check pending tasks and their agent assignments
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "pending").limit(5).execute
        )
        
        pending_tasks = response.data
        logger.info(f"📋 Found {len(pending_tasks)} pending tasks")
        
        for i, task in enumerate(pending_tasks):
            logger.info(f"Task {i+1}:")
            logger.info(f"  ID: {task['id']}")
            logger.info(f"  Name: {task['name']}")
            logger.info(f"  Agent ID: {task.get('agent_id', 'None')}")
            logger.info(f"  Workspace ID: {task['workspace_id']}")
            logger.info(f"  Status: {task['status']}")
            logger.info("  ---")
            
    except Exception as e:
        logger.error(f"Failed to get pending tasks: {e}")
        return
    
    # Check available agents
    try:
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("status", "active").limit(5).execute
        )
        
        active_agents = response.data
        logger.info(f"👥 Found {len(active_agents)} active agents")
        
        for i, agent in enumerate(active_agents):
            logger.info(f"Agent {i+1}:")
            logger.info(f"  ID: {agent['id']}")
            logger.info(f"  Name: {agent['name']}")
            logger.info(f"  Role: {agent['role']}")
            logger.info(f"  Workspace ID: {agent['workspace_id']}")
            logger.info(f"  Status: {agent['status']}")
            logger.info("  ---")
            
    except Exception as e:
        logger.error(f"Failed to get active agents: {e}")
        return
    
    # Check if there are tasks without agent_id in the same workspace as agents
    unassigned_tasks = [t for t in pending_tasks if not t.get('agent_id')]
    workspace_agents = {}
    
    for agent in active_agents:
        ws_id = agent['workspace_id']
        if ws_id not in workspace_agents:
            workspace_agents[ws_id] = []
        workspace_agents[ws_id].append(agent)
    
    logger.info("🔧 ASSIGNMENT ANALYSIS:")
    logger.info(f"Tasks without agent_id: {len(unassigned_tasks)}")
    logger.info(f"Workspaces with agents: {list(workspace_agents.keys())}")
    
    for task in unassigned_tasks:
        ws_id = task['workspace_id']
        agents_in_workspace = workspace_agents.get(ws_id, [])
        logger.info(f"Task '{task['name']}' in workspace {ws_id}: {len(agents_in_workspace)} agents available")
        
        if agents_in_workspace:
            # Try to assign the first available agent
            agent = agents_in_workspace[0]
            logger.info(f"  → Could assign to agent: {agent['name']} ({agent['role']})")
            
            # Actually try to assign it
            try:
                update_response = await asyncio.to_thread(
                    supabase.table("tasks").update({
                        "agent_id": agent["id"]
                    }).eq("id", task["id"]).execute
                )
                logger.info(f"  ✅ Successfully assigned task to agent {agent['name']}")
            except Exception as e:
                logger.error(f"  ❌ Failed to assign task: {e}")
        else:
            logger.warning(f"  ⚠️ No agents available in workspace {ws_id}")

if __name__ == "__main__":
    asyncio.run(debug_task_assignment())