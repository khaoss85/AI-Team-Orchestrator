#!/usr/bin/env python3

import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')
from database import supabase
from models import GoalStatus

print("=== INVESTIGATING ALL WORKSPACES WITH ACTIVE GOALS ===")

response = supabase.table('workspace_goals').select('workspace_id').eq('status', GoalStatus.ACTIVE.value).execute()
workspace_ids = list(set(row['workspace_id'] for row in response.data))

for i, workspace_id in enumerate(workspace_ids, 1):
    print(f"\n--- WORKSPACE {i}/{len(workspace_ids)}: {workspace_id} ---")
    
    # Get workspace details
    ws_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
    if ws_response.data:
        ws = ws_response.data[0]
        print(f"Name: {ws['name']}")
        print(f"Status: {ws['status']}")
        print(f"Created: {ws['created_at']}")
    else:
        print("Workspace not found")
        continue
    
    # Get agents
    agents_response = supabase.table('agents').select('id, name, status, role').eq('workspace_id', workspace_id).execute()
    agents = agents_response.data or []
    active_agents = [a for a in agents if a.get('status') == 'active']
    
    print(f"Agents: {len(agents)} total, {len(active_agents)} active")
    if agents:
        for agent in agents[:3]:  # Show first 3
            print(f"  - {agent['name']} ({agent['role']}) - {agent['status']}")
        if len(agents) > 3:
            print(f"  ... and {len(agents) - 3} more")
    
    # Health check indicator
    if ws['status'] != 'created' and active_agents:
        print("✅ Appears healthy")
    else:
        issues = []
        if ws['status'] == 'created':
            issues.append('STATUS=created')
        if not agents:
            issues.append('NO_AGENTS')
        elif not active_agents:
            issues.append('NO_ACTIVE_AGENTS')
        print(f"🚨 Issues: {', '.join(issues)}")