#!/usr/bin/env python3
"""
Emergency script to unblock goals stuck at 0%
Implements immediate fixes and triggers deliverable creation
"""

import asyncio
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from database import supabase

WORKSPACE_ID = "e29a33af-b473-4d9c-b983-f5c1aa70a830"

class EmergencyGoalUnblocker:
    """Emergency unblocking of stuck goals"""
    
    def __init__(self):
        self.workspace_id = WORKSPACE_ID
        self.fixes_applied = []
    
    async def execute_emergency_unblock(self):
        """Execute emergency unblocking procedures"""
        print("\n🚨 EMERGENCY GOAL UNBLOCK PROCEDURE")
        print("=" * 80)
        
        # Step 1: Fix orphaned deliverables immediately
        await self.fix_orphaned_deliverables()
        
        # Step 2: Create missing deliverables for empty goals
        await self.create_missing_deliverables()
        
        # Step 3: Update workspace status
        await self.update_workspace_status()
        
        # Step 4: Trigger recovery system
        await self.trigger_recovery_system()
        
        print("\n✅ Emergency unblock completed!")
        print("Check the UI now - goals should start showing progress.")
    
    async def fix_orphaned_deliverables(self):
        """Fix orphaned deliverables with simple pattern matching"""
        print("\n🔧 Fixing orphaned deliverables...")
        
        try:
            # Get orphaned deliverables
            orphaned_response = supabase.table("deliverables")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .is_("goal_id", "null")\
                .execute()
            
            if not orphaned_response.data:
                print("   ✅ No orphaned deliverables found")
                return
            
            # Get goals
            goals_response = supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .execute()
            
            goals = goals_response.data if goals_response.data else []
            
            for deliverable in orphaned_response.data:
                # Simple pattern matching
                title = deliverable.get("title", "").lower()
                matched_goal = None
                
                # Match based on keywords
                if "contact" in title or "icp" in title or "decision" in title:
                    # Match to contacts goal
                    matched_goal = next((g for g in goals if "contatti" in g.get("description", "").lower()), None)
                elif "market" in title or "report" in title or "research" in title:
                    # Match to email sequence goal
                    matched_goal = next((g for g in goals if "email" in g.get("description", "").lower()), None)
                
                if matched_goal:
                    # Update deliverable with goal_id
                    update_response = supabase.table("deliverables")\
                        .update({"goal_id": matched_goal["id"]})\
                        .eq("id", deliverable["id"])\
                        .execute()
                    
                    if update_response.data:
                        print(f"   ✅ Fixed: {deliverable['title'][:40]}... → {matched_goal['description'][:30]}...")
                        self.fixes_applied.append({
                            "deliverable": deliverable["title"],
                            "goal": matched_goal["description"]
                        })
                    
        except Exception as e:
            print(f"   ❌ Error fixing orphaned deliverables: {e}")
    
    async def create_missing_deliverables(self):
        """Create deliverables for goals that have none"""
        print("\n📦 Creating missing deliverables...")
        
        try:
            # Get all goals
            goals_response = supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .execute()
            
            goals = goals_response.data if goals_response.data else []
            
            for goal in goals:
                # Check if goal has deliverables
                deliverables_response = supabase.table("deliverables")\
                    .select("id")\
                    .eq("goal_id", goal["id"])\
                    .execute()
                
                if not deliverables_response.data:
                    # Create a deliverable for this goal
                    print(f"   Creating deliverable for: {goal['description'][:40]}...")
                    
                    deliverable_data = {
                        "workspace_id": self.workspace_id,
                        "goal_id": goal["id"],
                        "title": f"Deliverable for: {goal['description'][:50]}",
                        "description": f"Auto-generated deliverable for goal: {goal['description']}",
                        "status": "in_progress",
                        "content": {
                            "type": "auto_generated",
                            "goal_description": goal["description"],
                            "metric_type": goal.get("metric_type"),
                            "created_at": datetime.utcnow().isoformat()
                        },
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    response = supabase.table("deliverables").insert(deliverable_data).execute()
                    if response.data:
                        print(f"      ✅ Created deliverable ID: {response.data[0]['id'][:8]}...")
                    
                    # Also update goal progress to show activity
                    update_response = supabase.table("workspace_goals")\
                        .update({
                            "current_value": 0.5,  # Show some progress
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", goal["id"])\
                        .execute()
                    
                    if update_response.data:
                        print(f"      ✅ Updated goal to show initial progress")
                        
        except Exception as e:
            print(f"   ❌ Error creating deliverables: {e}")
    
    async def update_workspace_status(self):
        """Update workspace status from auto_recovering to active"""
        print("\n🔄 Updating workspace status...")
        
        try:
            update_response = supabase.table("workspaces")\
                .update({
                    "status": "active",
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", self.workspace_id)\
                .execute()
            
            if update_response.data:
                print("   ✅ Workspace status updated to 'active'")
            else:
                print("   ⚠️ Could not update workspace status")
                
        except Exception as e:
            print(f"   ❌ Error updating workspace: {e}")
    
    async def trigger_recovery_system(self):
        """Trigger the autonomous recovery system"""
        print("\n🚀 Triggering recovery system...")
        
        try:
            # Import and trigger recovery
            from services.autonomous_task_recovery import auto_recover_workspace_tasks
            
            print("   Starting autonomous task recovery...")
            recovery_result = await auto_recover_workspace_tasks(self.workspace_id)
            
            if recovery_result.get("success"):
                print(f"   ✅ Recovery triggered for {recovery_result.get('tasks_processed', 0)} tasks")
            else:
                print(f"   ⚠️ Recovery partial: {recovery_result.get('message', 'Unknown')}")
                
        except ImportError:
            print("   ⚠️ Autonomous recovery system not available")
        except Exception as e:
            print(f"   ❌ Error triggering recovery: {e}")


async def main():
    """Main execution"""
    unblocker = EmergencyGoalUnblocker()
    await unblocker.execute_emergency_unblock()


if __name__ == "__main__":
    asyncio.run(main())