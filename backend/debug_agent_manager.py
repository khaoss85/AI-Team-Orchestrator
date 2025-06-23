#!/usr/bin/env python3
"""
Debug script to test AgentManager initialization
"""

import os
import sys
import logging
import asyncio
from uuid import UUID

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agents.manager import AgentManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_agent_manager():
    """Debug AgentManager initialization"""
    workspace_id = "74cca01f-5a08-4cb1-891f-4833acbe53ff"
    
    logger.info(f"🔍 Starting AgentManager debug for workspace {workspace_id}")
    
    try:
        # Create and initialize AgentManager
        manager = AgentManager(UUID(workspace_id))
        logger.info("✅ AgentManager created successfully")
        
        # Initialize the manager
        success = await manager.initialize()
        logger.info(f"📊 Initialization result: {success}")
        
        if success:
            logger.info(f"✅ Successfully initialized {len(manager.agents)} agents:")
            for agent_id, specialist in manager.agents.items():
                logger.info(f"   - {specialist.agent_data.name} (ID: {agent_id})")
        else:
            logger.error("❌ AgentManager initialization failed")
            
        return manager
        
    except Exception as e:
        logger.error(f"❌ Error in debug_agent_manager: {e}", exc_info=True)
        return None

async def main():
    """Main debug function"""
    logger.info("🚀 Starting AgentManager debug session...")
    
    manager = await debug_agent_manager()
    
    if manager and manager.agents:
        logger.info("🎉 Debug completed successfully!")
        logger.info(f"📊 Final state:")
        logger.info(f"   - Workspace ID: {manager.workspace_id}")
        logger.info(f"   - Initialized agents: {len(manager.agents)}")
        logger.info(f"   - Initialization time: {manager.initialization_time}")
    else:
        logger.error("💥 Debug failed - AgentManager could not be initialized properly")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)