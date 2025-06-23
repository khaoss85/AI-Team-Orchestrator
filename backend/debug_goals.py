#!/usr/bin/env python3

import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')
from database import supabase
from models import GoalStatus
from datetime import datetime, timedelta

print("=== DEBUGGING GOAL VALIDATION QUERY ===")

# Original query from _get_workspaces_needing_validation
cutoff_time = datetime.now() - timedelta(minutes=20)
print(f"Cutoff time: {cutoff_time}")

response = supabase.table("workspace_goals").select(
    "workspace_id"
).eq(
    "status", GoalStatus.ACTIVE.value
).or_(
    f"last_validation_at.is.null,last_validation_at.lt.{cutoff_time.isoformat()}"
).execute()

workspace_ids = list(set(row["workspace_id"] for row in response.data))
print(f"Workspaces from query: {len(workspace_ids)}")
for workspace_id in workspace_ids:
    print(f"  - {workspace_id}")

# Check what goals exist
all_goals = supabase.table("workspace_goals").select("workspace_id, status, last_validation_at").execute()
print(f"\nAll goals in database: {len(all_goals.data)}")
for goal in all_goals.data:
    print(f"  - {goal['workspace_id']} - status: {goal['status']} - last_validation: {goal.get('last_validation_at', 'None')}")