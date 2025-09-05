#!/usr/bin/env python3
"""
Fix per il mapping goal-deliverable e il calcolo del progress
Per workspace: e29a33af-b473-4d9c-b983-f5c1aa70a830
"""

import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

from database import supabase
from services.ai_goal_matcher import AIGoalMatcher

class GoalDeliverableMapper:
    """Fix mapping issues between goals and deliverables"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.ai_matcher = AIGoalMatcher()
        self.fixes_applied = []
    
    async def run_fix(self):
        """Execute the complete fix process"""
        print(f"\n🔧 FIXING GOAL-DELIVERABLE MAPPING")
        print(f"Workspace: {self.workspace_id}")
        print("=" * 80)
        
        # 1. Get orphaned deliverables
        orphaned = await self.get_orphaned_deliverables()
        
        # 2. Get all goals
        goals = await self.get_workspace_goals()
        
        # 3. Fix mappings
        if orphaned and goals:
            await self.fix_orphaned_mappings(orphaned, goals)
        
        # 4. Recalculate goal progress
        await self.recalculate_goal_progress(goals)
        
        # 5. Trigger missing deliverables creation
        await self.trigger_missing_deliverables(goals)
        
        # 6. Print report
        self.print_report()
    
    async def get_orphaned_deliverables(self):
        """Get deliverables without goal association"""
        print("\n📦 Checking for orphaned deliverables...")
        
        try:
            # Get deliverables with null or missing goal_id
            response = supabase.table("deliverables")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .is_("goal_id", "null")\
                .execute()
            
            orphaned = response.data if response.data else []
            
            if orphaned:
                print(f"❌ Found {len(orphaned)} orphaned deliverables:")
                for d in orphaned:
                    print(f"   - {d['title'][:50]}... (ID: {d['id'][:8]}...)")
            else:
                print("✅ No orphaned deliverables found")
            
            return orphaned
            
        except Exception as e:
            print(f"❌ Error getting orphaned deliverables: {e}")
            return []
    
    async def get_workspace_goals(self):
        """Get all workspace goals"""
        print("\n🎯 Loading workspace goals...")
        
        try:
            response = supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .execute()
            
            goals = response.data if response.data else []
            
            if goals:
                print(f"✅ Found {len(goals)} goals:")
                for g in goals:
                    print(f"   - {g['description'][:50]}... (Progress: {g.get('progress', 0)}%)")
            else:
                print("❌ No goals found!")
            
            return goals
            
        except Exception as e:
            print(f"❌ Error getting goals: {e}")
            return []
    
    async def fix_orphaned_mappings(self, orphaned: List[Dict], goals: List[Dict]):
        """Fix mappings for orphaned deliverables using AI matcher"""
        print(f"\n🤖 Using AI Goal Matcher to fix {len(orphaned)} orphaned deliverables...")
        
        for deliverable in orphaned:
            try:
                # Use AI to match deliverable to best goal
                match_result = await self.ai_matcher.match_deliverable_to_goal(
                    deliverable_content=deliverable.get("content", {}),
                    deliverable_title=deliverable.get("title", ""),
                    goals=goals
                )
                
                if match_result and match_result.get("success"):
                    goal_id = match_result.get("goal_id")
                    confidence = match_result.get("confidence", 0)
                    reasoning = match_result.get("reasoning", "")
                    
                    if goal_id and confidence >= 0.6:  # Lower threshold for fixing existing deliverables
                        # Update deliverable with matched goal
                        update_response = supabase.table("deliverables")\
                            .update({"goal_id": goal_id})\
                            .eq("id", deliverable["id"])\
                            .execute()
                        
                        if update_response.data:
                            matched_goal = next((g for g in goals if g["id"] == goal_id), None)
                            goal_desc = matched_goal["description"][:30] if matched_goal else "Unknown"
                            
                            print(f"   ✅ Fixed: {deliverable['title'][:30]}... → {goal_desc}...")
                            print(f"      Confidence: {confidence:.2%} - {reasoning}")
                            
                            self.fixes_applied.append({
                                "deliverable_id": deliverable["id"],
                                "deliverable_title": deliverable["title"],
                                "goal_id": goal_id,
                                "goal_description": goal_desc,
                                "confidence": confidence,
                                "reasoning": reasoning
                            })
                        else:
                            print(f"   ❌ Failed to update deliverable {deliverable['id']}")
                    else:
                        print(f"   ⚠️ Low confidence ({confidence:.2%}) for {deliverable['title'][:30]}...")
                else:
                    print(f"   ⚠️ Could not match {deliverable['title'][:30]}...")
                    
            except Exception as e:
                print(f"   ❌ Error fixing {deliverable['id']}: {e}")
    
    async def recalculate_goal_progress(self, goals: List[Dict]):
        """Recalculate progress for all goals based on their deliverables"""
        print(f"\n📊 Recalculating goal progress for {len(goals)} goals...")
        
        for goal in goals:
            try:
                # Get deliverables for this goal
                deliverables_response = supabase.table("deliverables")\
                    .select("status")\
                    .eq("goal_id", goal["id"])\
                    .execute()
                
                deliverables = deliverables_response.data if deliverables_response.data else []
                
                if deliverables:
                    # Calculate progress based on completed deliverables
                    total = len(deliverables)
                    completed = sum(1 for d in deliverables if d.get("status") == "completed")
                    progress = int((completed / total) * 100) if total > 0 else 0
                    
                    # Update goal progress if different
                    if progress != goal.get("progress", 0):
                        update_response = supabase.table("workspace_goals")\
                            .update({
                                "progress": progress,
                                "current_value": completed,
                                "updated_at": datetime.utcnow().isoformat()
                            })\
                            .eq("id", goal["id"])\
                            .execute()
                        
                        if update_response.data:
                            print(f"   ✅ Updated {goal['description'][:30]}...: {goal.get('progress', 0)}% → {progress}%")
                        else:
                            print(f"   ❌ Failed to update progress for goal {goal['id']}")
                    else:
                        print(f"   ✓ {goal['description'][:30]}...: {progress}% (unchanged)")
                else:
                    print(f"   ⚠️ No deliverables found for {goal['description'][:30]}...")
                    
            except Exception as e:
                print(f"   ❌ Error updating goal {goal['id']}: {e}")
    
    async def trigger_missing_deliverables(self, goals: List[Dict]):
        """Trigger creation of missing deliverables for goals at 0%"""
        print(f"\n🚀 Checking for goals needing deliverable creation...")
        
        goals_needing_deliverables = []
        
        for goal in goals:
            if goal.get("progress", 0) == 0:
                # Check if goal has any deliverables
                deliverables_response = supabase.table("deliverables")\
                    .select("id")\
                    .eq("goal_id", goal["id"])\
                    .execute()
                
                if not deliverables_response.data:
                    goals_needing_deliverables.append(goal)
        
        if goals_needing_deliverables:
            print(f"❌ {len(goals_needing_deliverables)} goals need deliverables:")
            for goal in goals_needing_deliverables:
                print(f"   - {goal['description'][:50]}...")
                
                # Create a task to generate deliverables
                try:
                    task_data = {
                        "workspace_id": self.workspace_id,
                        "goal_id": goal["id"],
                        "title": f"Create deliverables for: {goal['description'][:50]}",
                        "description": f"Generate missing deliverables for goal: {goal['description']}",
                        "status": "pending",
                        "priority": 100,  # High priority
                        "type": "deliverable_creation",
                        "metadata": {
                            "goal_description": goal["description"],
                            "metric_type": goal.get("metric_type"),
                            "auto_generated": True
                        },
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    response = supabase.table("tasks").insert(task_data).execute()
                    if response.data:
                        print(f"      ✅ Created task to generate deliverables")
                    else:
                        print(f"      ❌ Failed to create generation task")
                        
                except Exception as e:
                    print(f"      ❌ Error creating task: {e}")
        else:
            print("✅ All goals have associated deliverables")
    
    def print_report(self):
        """Print final fix report"""
        print("\n" + "=" * 80)
        print("📊 FIX REPORT")
        print("=" * 80)
        
        if self.fixes_applied:
            print(f"\n✅ Fixed {len(self.fixes_applied)} deliverable mappings:")
            for fix in self.fixes_applied:
                print(f"\n   Deliverable: {fix['deliverable_title'][:40]}...")
                print(f"   → Goal: {fix['goal_description']}...")
                print(f"   Confidence: {fix['confidence']:.2%}")
                print(f"   Reasoning: {fix['reasoning'][:100]}...")
        else:
            print("\n✅ No mapping fixes needed")
        
        print("\n💡 NEXT STEPS:")
        print("1. Check the UI to verify goals are now showing progress")
        print("2. Monitor task execution for deliverable creation")
        print("3. Review workspace recovery status")
        print("\n✅ Fix process completed!")


async def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Fix goal-deliverable mapping issues")
    parser.add_argument("--workspace", "-w", 
                       default="e29a33af-b473-4d9c-b983-f5c1aa70a830",
                       help="Workspace ID to fix")
    
    args = parser.parse_args()
    
    fixer = GoalDeliverableMapper(args.workspace)
    await fixer.run_fix()


if __name__ == "__main__":
    asyncio.run(main())