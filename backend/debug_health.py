#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')
from automated_goal_monitor import automated_goal_monitor

async def debug_health_checks():
    workspace_ids = [
        '89e35f1b-f772-4fec-a6d0-37b9dd8492fe',  # B2B Outbound Sales Lists
        'f9f614db-d418-4ec1-9685-3f77d6f4ef13'   # Test E2E Auto-Start Workspace
    ]
    
    for workspace_id in workspace_ids:
        print(f"\nTesting workspace: {workspace_id}")
        is_healthy = await automated_goal_monitor._check_workspace_health(workspace_id)
        print(f"Health result: {is_healthy}")

asyncio.run(debug_health_checks())