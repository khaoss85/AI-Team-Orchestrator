#!/usr/bin/env python3
"""
Fix agent status - activate agents so TaskExecutor can use them
"""

import asyncio
import logging
from database import supabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def fix_agent_status():
    """Fix agent status to make them available for task execution"""
    logger.info("🔧 FIXING AGENT STATUS")
    logger.info("="*40)
    
    # Get all agents regardless of status
    try:
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").execute
        )
        
        all_agents = response.data
        logger.info(f"👥 Found {len(all_agents)} total agents")
        
        # Group by status
        status_counts = {}
        agents_by_workspace = {}
        
        for agent in all_agents:
            status = agent.get('status', 'unknown')
            workspace_id = agent.get('workspace_id')
            
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
            
            if workspace_id not in agents_by_workspace:
                agents_by_workspace[workspace_id] = []
            agents_by_workspace[workspace_id].append(agent)
        
        logger.info("📊 Agent Status Distribution:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count} agents")
        
        # Find agents that need to be activated
        inactive_agents = [a for a in all_agents if a.get('status') != 'active']
        logger.info(f"🔧 {len(inactive_agents)} agents need activation")
        
        # Activate all inactive agents
        activated_count = 0
        for agent in inactive_agents:
            try:
                update_response = await asyncio.to_thread(
                    supabase.table("agents").update({
                        "status": "active"
                    }).eq("id", agent["id"]).execute
                )
                
                logger.info(f"✅ Activated agent: {agent['name']} ({agent['role']}) in workspace {agent['workspace_id']}")
                activated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to activate agent {agent['name']}: {e}")
        
        logger.info(f"🎉 Activated {activated_count} agents")
        
        # Verify activation
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("status", "active").execute
        )
        
        active_agents = response.data
        logger.info(f"✅ Now have {len(active_agents)} active agents")
        
        # Show active agents by workspace
        active_by_workspace = {}
        for agent in active_agents:
            ws_id = agent['workspace_id']
            if ws_id not in active_by_workspace:
                active_by_workspace[ws_id] = []
            active_by_workspace[ws_id].append(agent)
        
        logger.info("📋 Active Agents by Workspace:")
        for ws_id, agents in active_by_workspace.items():
            logger.info(f"  Workspace {ws_id}: {len(agents)} agents")
            for agent in agents:
                logger.info(f"    - {agent['name']} ({agent['role']})")
        
        return activated_count > 0
            
    except Exception as e:
        logger.error(f"Failed to fix agent status: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(fix_agent_status())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}: Agent status fix complete")
    exit(0 if result else 1)