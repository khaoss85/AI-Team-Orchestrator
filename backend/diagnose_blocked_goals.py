#!/usr/bin/env python3
"""
Script di diagnosi completa per goal bloccati allo 0%
Workspace ID: e29a33af-b473-4d9c-b983-f5c1aa70a830
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

from database import supabase

WORKSPACE_ID = "e29a33af-b473-4d9c-b983-f5c1aa70a830"

class GoalBlockageDiagnostics:
    """Diagnostica completa del blocco dei goal"""
    
    def __init__(self):
        self.workspace_id = WORKSPACE_ID
        self.report = {
            "workspace_analysis": {},
            "goals_analysis": [],
            "tasks_analysis": [],
            "deliverables_analysis": [],
            "blocking_issues": [],
            "recommendations": []
        }
    
    async def run_full_diagnosis(self):
        """Esegue diagnosi completa"""
        print(f"\n🔍 DIAGNOSI BLOCCO GOAL - Workspace: {self.workspace_id}")
        print("=" * 80)
        
        # 1. Analisi workspace
        await self.analyze_workspace()
        
        # 2. Analisi goals
        await self.analyze_goals()
        
        # 3. Analisi tasks
        await self.analyze_tasks()
        
        # 4. Analisi deliverables
        await self.analyze_deliverables()
        
        # 5. Identificazione blocchi
        await self.identify_blockages()
        
        # 6. Generazione raccomandazioni
        self.generate_recommendations()
        
        # 7. Report finale
        self.print_report()
        
        return self.report
    
    async def analyze_workspace(self):
        """Analizza stato workspace"""
        print("\n📊 1. ANALISI WORKSPACE")
        print("-" * 40)
        
        try:
            # Get workspace data
            workspace_response = supabase.table("workspaces").select("*").eq("id", self.workspace_id).execute()
            
            if workspace_response.data:
                workspace = workspace_response.data[0]
                self.report["workspace_analysis"] = {
                    "id": workspace["id"],
                    "name": workspace.get("name", "Unknown"),
                    "status": workspace.get("status", "Unknown"),
                    "created_at": workspace.get("created_at"),
                    "updated_at": workspace.get("updated_at"),
                    "goal": workspace.get("goal", "No goal defined")
                }
                
                print(f"✅ Workspace: {workspace.get('name')}")
                print(f"   Status: {workspace.get('status')}")
                print(f"   Created: {workspace.get('created_at')}")
                
                # Check if status is problematic
                if workspace.get("status") in ["auto_recovering", "failed", "needs_intervention"]:
                    self.report["blocking_issues"].append({
                        "type": "workspace_status",
                        "severity": "HIGH",
                        "description": f"Workspace in problematic status: {workspace.get('status')}"
                    })
            else:
                print("❌ Workspace not found!")
                self.report["blocking_issues"].append({
                    "type": "workspace_missing",
                    "severity": "CRITICAL",
                    "description": "Workspace not found in database"
                })
                
        except Exception as e:
            print(f"❌ Error analyzing workspace: {e}")
            self.report["blocking_issues"].append({
                "type": "workspace_error",
                "severity": "CRITICAL",
                "description": str(e)
            })
    
    async def analyze_goals(self):
        """Analizza goals del workspace"""
        print("\n🎯 2. ANALISI GOALS")
        print("-" * 40)
        
        try:
            # Get goals
            goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", self.workspace_id).execute()
            
            if goals_response.data:
                print(f"✅ Found {len(goals_response.data)} goals")
                
                for goal in goals_response.data:
                    goal_analysis = {
                        "id": goal["id"],
                        "description": goal.get("description", "No description"),
                        "status": goal.get("status", "Unknown"),
                        "progress": goal.get("progress", 0),
                        "metric_type": goal.get("metric_type"),
                        "target_value": goal.get("target_value"),
                        "current_value": goal.get("current_value", 0),
                        "created_at": goal.get("created_at"),
                        "updated_at": goal.get("updated_at"),
                        "issues": []
                    }
                    
                    print(f"\n   📌 Goal: {goal.get('description')[:50]}...")
                    print(f"      Status: {goal.get('status')}")
                    print(f"      Progress: {goal.get('progress', 0)}%")
                    print(f"      Metric Type: {goal.get('metric_type')}")
                    
                    # Check for issues
                    if goal.get("progress", 0) == 0 and goal.get("status") == "active":
                        goal_analysis["issues"].append("Goal at 0% but marked as active")
                        self.report["blocking_issues"].append({
                            "type": "goal_stuck",
                            "severity": "HIGH",
                            "description": f"Goal '{goal.get('description')[:30]}' stuck at 0%",
                            "goal_id": goal["id"]
                        })
                    
                    if not goal.get("metric_type"):
                        goal_analysis["issues"].append("No metric type defined")
                    
                    self.report["goals_analysis"].append(goal_analysis)
            else:
                print("❌ No goals found for workspace!")
                self.report["blocking_issues"].append({
                    "type": "no_goals",
                    "severity": "CRITICAL",
                    "description": "No goals defined for workspace"
                })
                
        except Exception as e:
            print(f"❌ Error analyzing goals: {e}")
            self.report["blocking_issues"].append({
                "type": "goals_error",
                "severity": "HIGH",
                "description": str(e)
            })
    
    async def analyze_tasks(self):
        """Analizza tasks del workspace"""
        print("\n📋 3. ANALISI TASKS")
        print("-" * 40)
        
        try:
            # Get tasks
            tasks_response = supabase.table("tasks").select("*").eq("workspace_id", self.workspace_id).execute()
            
            if tasks_response.data:
                # Group tasks by status
                task_stats = {
                    "total": len(tasks_response.data),
                    "by_status": {},
                    "by_goal": {},
                    "failed_tasks": [],
                    "stuck_tasks": []
                }
                
                for task in tasks_response.data:
                    # Count by status
                    status = task.get("status", "unknown")
                    task_stats["by_status"][status] = task_stats["by_status"].get(status, 0) + 1
                    
                    # Count by goal
                    goal_id = task.get("goal_id", "no_goal")
                    task_stats["by_goal"][goal_id] = task_stats["by_goal"].get(goal_id, 0) + 1
                    
                    # Track failed tasks
                    if status == "failed":
                        task_stats["failed_tasks"].append({
                            "id": task["id"],
                            "title": task.get("title", "Unknown"),
                            "error": task.get("error_message", "No error message"),
                            "attempts": task.get("retry_count", 0)
                        })
                    
                    # Track stuck tasks (pending for >30 min)
                    if status == "pending":
                        created_at = task.get("created_at", "")
                        if created_at:
                            try:
                                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                if datetime.now(created_time.tzinfo) - created_time > timedelta(minutes=30):
                                    task_stats["stuck_tasks"].append({
                                        "id": task["id"],
                                        "title": task.get("title", "Unknown"),
                                        "created": created_at,
                                        "assigned_agent": task.get("assigned_agent_id")
                                    })
                            except:
                                pass
                
                print(f"✅ Found {task_stats['total']} tasks")
                print(f"\n   Status Distribution:")
                for status, count in task_stats["by_status"].items():
                    print(f"      {status}: {count}")
                
                print(f"\n   Failed Tasks: {len(task_stats['failed_tasks'])}")
                for failed in task_stats["failed_tasks"][:3]:  # Show first 3
                    print(f"      ❌ {failed['title'][:40]} - {failed['error'][:50]}")
                
                print(f"\n   Stuck Tasks (pending >30min): {len(task_stats['stuck_tasks'])}")
                for stuck in task_stats["stuck_tasks"][:3]:  # Show first 3
                    print(f"      ⏳ {stuck['title'][:40]} - Created: {stuck['created']}")
                
                self.report["tasks_analysis"] = task_stats
                
                # Add blocking issues
                if task_stats["failed_tasks"]:
                    self.report["blocking_issues"].append({
                        "type": "failed_tasks",
                        "severity": "HIGH",
                        "description": f"{len(task_stats['failed_tasks'])} tasks have failed",
                        "task_ids": [t["id"] for t in task_stats["failed_tasks"]]
                    })
                
                if task_stats["stuck_tasks"]:
                    self.report["blocking_issues"].append({
                        "type": "stuck_tasks",
                        "severity": "MEDIUM",
                        "description": f"{len(task_stats['stuck_tasks'])} tasks stuck in pending",
                        "task_ids": [t["id"] for t in task_stats["stuck_tasks"]]
                    })
                    
            else:
                print("❌ No tasks found for workspace!")
                self.report["blocking_issues"].append({
                    "type": "no_tasks",
                    "severity": "CRITICAL",
                    "description": "No tasks created for workspace"
                })
                
        except Exception as e:
            print(f"❌ Error analyzing tasks: {e}")
            self.report["blocking_issues"].append({
                "type": "tasks_error",
                "severity": "HIGH",
                "description": str(e)
            })
    
    async def analyze_deliverables(self):
        """Analizza deliverables del workspace"""
        print("\n📦 4. ANALISI DELIVERABLES")
        print("-" * 40)
        
        try:
            # Get deliverables
            deliverables_response = supabase.table("deliverables").select("*").eq("workspace_id", self.workspace_id).execute()
            
            if deliverables_response.data:
                deliverable_stats = {
                    "total": len(deliverables_response.data),
                    "by_status": {},
                    "by_goal": {},
                    "orphaned": [],
                    "incomplete": []
                }
                
                for deliverable in deliverables_response.data:
                    # Count by status
                    status = deliverable.get("status", "unknown")
                    deliverable_stats["by_status"][status] = deliverable_stats["by_status"].get(status, 0) + 1
                    
                    # Count by goal
                    goal_id = deliverable.get("goal_id")
                    if goal_id:
                        deliverable_stats["by_goal"][goal_id] = deliverable_stats["by_goal"].get(goal_id, 0) + 1
                    else:
                        deliverable_stats["orphaned"].append({
                            "id": deliverable["id"],
                            "title": deliverable.get("title", "Unknown")
                        })
                    
                    # Check for incomplete
                    if status != "completed" and deliverable.get("content"):
                        content = deliverable.get("content", {})
                        if isinstance(content, str):
                            try:
                                content = json.loads(content)
                            except:
                                pass
                        
                        # Check for placeholder content
                        content_str = str(content)
                        if any(placeholder in content_str.lower() for placeholder in ["todo", "placeholder", "lorem ipsum"]):
                            deliverable_stats["incomplete"].append({
                                "id": deliverable["id"],
                                "title": deliverable.get("title", "Unknown"),
                                "issue": "Contains placeholder content"
                            })
                
                print(f"✅ Found {deliverable_stats['total']} deliverables")
                
                print(f"\n   Status Distribution:")
                for status, count in deliverable_stats["by_status"].items():
                    print(f"      {status}: {count}")
                
                print(f"\n   Orphaned Deliverables (no goal): {len(deliverable_stats['orphaned'])}")
                for orphan in deliverable_stats["orphaned"][:3]:
                    print(f"      ❓ {orphan['title'][:50]}")
                
                print(f"\n   Incomplete Deliverables: {len(deliverable_stats['incomplete'])}")
                for incomplete in deliverable_stats["incomplete"][:3]:
                    print(f"      ⚠️ {incomplete['title'][:40]} - {incomplete['issue']}")
                
                self.report["deliverables_analysis"] = deliverable_stats
                
                # Add blocking issues
                if deliverable_stats["orphaned"]:
                    self.report["blocking_issues"].append({
                        "type": "orphaned_deliverables",
                        "severity": "MEDIUM",
                        "description": f"{len(deliverable_stats['orphaned'])} deliverables without goal association",
                        "deliverable_ids": [d["id"] for d in deliverable_stats["orphaned"]]
                    })
                
            else:
                print("❌ No deliverables found for workspace!")
                self.report["blocking_issues"].append({
                    "type": "no_deliverables",
                    "severity": "HIGH",
                    "description": "No deliverables created for workspace goals"
                })
                
        except Exception as e:
            print(f"❌ Error analyzing deliverables: {e}")
            self.report["blocking_issues"].append({
                "type": "deliverables_error",
                "severity": "HIGH",
                "description": str(e)
            })
    
    async def identify_blockages(self):
        """Identifica cause root dei blocchi"""
        print("\n🚧 5. IDENTIFICAZIONE BLOCCHI")
        print("-" * 40)
        
        # Analisi patterns di blocco
        critical_issues = [issue for issue in self.report["blocking_issues"] if issue["severity"] == "CRITICAL"]
        high_issues = [issue for issue in self.report["blocking_issues"] if issue["severity"] == "HIGH"]
        
        if critical_issues:
            print(f"❌ {len(critical_issues)} CRITICAL issues found!")
            for issue in critical_issues:
                print(f"   🔴 {issue['type']}: {issue['description']}")
        
        if high_issues:
            print(f"⚠️ {len(high_issues)} HIGH severity issues found!")
            for issue in high_issues:
                print(f"   🟡 {issue['type']}: {issue['description']}")
        
        # Root cause analysis
        root_causes = []
        
        # Check 1: No goals created
        if any(issue["type"] == "no_goals" for issue in self.report["blocking_issues"]):
            root_causes.append({
                "cause": "NO_GOALS_CREATED",
                "description": "Goal decomposition system failed to create goals from workspace objective",
                "impact": "No tasks or deliverables can be created without goals"
            })
        
        # Check 2: Tasks failing
        failed_task_count = len(self.report["tasks_analysis"].get("failed_tasks", []))
        if failed_task_count > 3:
            root_causes.append({
                "cause": "TASK_EXECUTION_FAILURE",
                "description": f"Multiple tasks ({failed_task_count}) failing during execution",
                "impact": "Goals cannot progress without successful task completion"
            })
        
        # Check 3: Workspace in recovery
        if self.report["workspace_analysis"].get("status") == "auto_recovering":
            root_causes.append({
                "cause": "WORKSPACE_IN_RECOVERY",
                "description": "Workspace is in auto-recovery mode, may have encountered critical failures",
                "impact": "System attempting automatic recovery but may need manual intervention"
            })
        
        # Check 4: Goal-Deliverable mapping issue
        if self.report["deliverables_analysis"].get("orphaned"):
            root_causes.append({
                "cause": "GOAL_DELIVERABLE_MAPPING_FAILURE",
                "description": "Deliverables created but not properly associated with goals",
                "impact": "Goal progress calculations incorrect, appearing as 0%"
            })
        
        self.report["root_causes"] = root_causes
        
        if root_causes:
            print(f"\n🔍 Identified {len(root_causes)} root causes:")
            for i, cause in enumerate(root_causes, 1):
                print(f"\n   {i}. {cause['cause']}")
                print(f"      Description: {cause['description']}")
                print(f"      Impact: {cause['impact']}")
    
    def generate_recommendations(self):
        """Genera raccomandazioni per risolvere i blocchi"""
        print("\n💡 6. RACCOMANDAZIONI")
        print("-" * 40)
        
        recommendations = []
        
        # Based on root causes
        for cause in self.report.get("root_causes", []):
            if cause["cause"] == "NO_GOALS_CREATED":
                recommendations.append({
                    "priority": 1,
                    "action": "TRIGGER_GOAL_DECOMPOSITION",
                    "description": "Manually trigger goal decomposition from workspace objective",
                    "command": f"python3 -c \"from services.goal_driven_system import create_goals_from_workspace_goal; import asyncio; asyncio.run(create_goals_from_workspace_goal('{self.workspace_id}'))\""
                })
            
            elif cause["cause"] == "TASK_EXECUTION_FAILURE":
                recommendations.append({
                    "priority": 1,
                    "action": "RETRY_FAILED_TASKS",
                    "description": "Trigger autonomous recovery for failed tasks",
                    "command": f"python3 -c \"from services.autonomous_task_recovery import auto_recover_workspace_tasks; import asyncio; asyncio.run(auto_recover_workspace_tasks('{self.workspace_id}'))\""
                })
            
            elif cause["cause"] == "WORKSPACE_IN_RECOVERY":
                recommendations.append({
                    "priority": 2,
                    "action": "MONITOR_RECOVERY",
                    "description": "Monitor auto-recovery progress and check logs for errors",
                    "command": f"tail -f backend/logs/*.log | grep '{self.workspace_id}'"
                })
            
            elif cause["cause"] == "GOAL_DELIVERABLE_MAPPING_FAILURE":
                recommendations.append({
                    "priority": 1,
                    "action": "FIX_GOAL_MAPPING",
                    "description": "Fix orphaned deliverables by remapping to correct goals",
                    "command": f"python3 fix_goal_deliverable_mapping.py --workspace {self.workspace_id}"
                })
        
        # General recommendations
        if not self.report.get("goals_analysis"):
            recommendations.append({
                "priority": 1,
                "action": "RECREATE_WORKSPACE",
                "description": "Consider recreating workspace with clearer objectives",
                "command": None
            })
        
        self.report["recommendations"] = sorted(recommendations, key=lambda x: x["priority"])
        
        for rec in self.report["recommendations"]:
            print(f"\n   Priority {rec['priority']}: {rec['action']}")
            print(f"   {rec['description']}")
            if rec.get("command"):
                print(f"   Command: {rec['command']}")
    
    def print_report(self):
        """Stampa report finale"""
        print("\n" + "=" * 80)
        print("📊 REPORT FINALE")
        print("=" * 80)
        
        # Summary
        print("\n🎯 SUMMARY:")
        print(f"   Workspace Status: {self.report['workspace_analysis'].get('status', 'Unknown')}")
        print(f"   Goals: {len(self.report.get('goals_analysis', []))}")
        print(f"   Tasks: {self.report.get('tasks_analysis', {}).get('total', 0)}")
        print(f"   Deliverables: {self.report.get('deliverables_analysis', {}).get('total', 0)}")
        print(f"   Blocking Issues: {len(self.report.get('blocking_issues', []))}")
        print(f"   Root Causes: {len(self.report.get('root_causes', []))}")
        
        # Critical Action Required
        if self.report.get("recommendations"):
            print("\n⚡ IMMEDIATE ACTION REQUIRED:")
            top_rec = self.report["recommendations"][0]
            print(f"   {top_rec['description']}")
            if top_rec.get("command"):
                print(f"\n   Execute: {top_rec['command']}")
        
        # Save report
        report_file = f"goal_blockage_report_{self.workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\n📁 Full report saved to: {report_file}")


async def main():
    """Main execution"""
    diagnostics = GoalBlockageDiagnostics()
    report = await diagnostics.run_full_diagnosis()
    
    # Return status code based on severity
    critical_count = len([i for i in report.get("blocking_issues", []) if i["severity"] == "CRITICAL"])
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)