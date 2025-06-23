#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')
from automated_goal_monitor import automated_goal_monitor

async def test_healthy_workspace():
    # Test with the healthy workspace that has 5 active agents
    healthy_workspace_id = '89e35f1b-f772-4fec-a6d0-37b9dd8492fe'
    print(f"Testing healthy workspace: {healthy_workspace_id}")
    
    is_healthy = await automated_goal_monitor._check_workspace_health(healthy_workspace_id)
    print(f"Health check result: {is_healthy}")
    
    if is_healthy:
        print("✅ Correctly identified healthy workspace!")
    else:
        print("❌ Incorrectly flagged healthy workspace as unhealthy")

asyncio.run(test_healthy_workspace())