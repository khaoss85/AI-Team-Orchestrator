#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')
from automated_goal_monitor import automated_goal_monitor

async def test_final_filtering():
    print("Testing final workspace filtering after cleanup...")
    
    healthy_workspaces = await automated_goal_monitor._get_workspaces_needing_validation()
    print(f"✅ Healthy workspaces that will be monitored: {len(healthy_workspaces)}")
    
    for workspace_id in healthy_workspaces:
        print(f"  - {workspace_id}")
    
    # Should be 2 healthy workspaces now
    if len(healthy_workspaces) == 2:
        print("🎉 SUCCESS: Only healthy workspaces will be processed!")
    else:
        print(f"⚠️ Expected 2 healthy workspaces, got {len(healthy_workspaces)}")

asyncio.run(test_final_filtering())