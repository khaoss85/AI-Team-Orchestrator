#!/usr/bin/env python3
"""
🚀 FORCE AUTONOMOUS ACTIVATION - Attiva il sistema autonomo
================================================================================
Questo script forza l'attivazione del sistema autonomo verificando che
l'AutomatedGoalMonitor processi i goal e generi task automaticamente.
"""

from pathlib import Path
import sys
sys.path.insert(0, '.')

import asyncio
import logging
from datetime import datetime
from database import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_autonomous_activation():
    """Forza l'attivazione del sistema autonomo"""
    
    try:
        # Import the automated goal monitor
        from automated_goal_monitor import automated_goal_monitor
        
        logger.info("🚀 FORCING AUTONOMOUS SYSTEM ACTIVATION")
        logger.info("=" * 80)
        
        # Get active goals that need processing
        supabase = get_supabase_client()
        
        active_goals = supabase.table('workspace_goals').select('*').eq('status', 'active').execute()
        logger.info(f"Found {len(active_goals.data)} active goals")
        
        if active_goals.data:
            goal = active_goals.data[0]
            logger.info(f"\n🎯 Processing goal: {goal['id']}")
            logger.info(f"   Description: {goal['description'][:80]}...")
            
            # Check if tasks already exist
            existing_tasks = supabase.table('tasks').select('*').eq('goal_id', goal['id']).execute()
            logger.info(f"   Existing tasks: {len(existing_tasks.data)}")
            
            if len(existing_tasks.data) == 0:
                logger.info("\n⚡ Triggering AutomatedGoalMonitor validation cycle...")
                
                # Force a validation cycle for the workspace
                await automated_goal_monitor.trigger_immediate_validation(goal['workspace_id'])
                
                # Check if tasks were created
                await asyncio.sleep(5)
                new_tasks = supabase.table('tasks').select('*').eq('goal_id', goal['id']).execute()
                
                if len(new_tasks.data) > 0:
                    logger.info(f"\n✅ SUCCESS! Generated {len(new_tasks.data)} tasks automatically:")
                    for task in new_tasks.data[:5]:
                        logger.info(f"   - {task.get('name', 'Unnamed')}")
                    
                    logger.info("\n🤖 AUTONOMOUS SYSTEM IS NOW ACTIVE!")
                    logger.info("   The system will continue processing automatically")
                else:
                    logger.warning("\n⚠️ No tasks generated yet. The system may need more time.")
            else:
                logger.info("\n✅ Tasks already exist - system is working!")
                
        else:
            logger.warning("No active goals found to process")
            
    except Exception as e:
        logger.error(f"Error activating autonomous system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_autonomous_activation())