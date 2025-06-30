#!/usr/bin/env python3
"""
Debug Script for Deliverable Creation System

This script analyzes the deliverable generation pipeline to identify why
deliverables are not being created despite goals and tasks being generated.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_workspace, list_workspaces, list_tasks, list_agents,
    get_workspace_goals, supabase
)
from deliverable_aggregator import check_and_create_final_deliverable, deliverable_aggregator
from models import TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeliverableDebugger:
    """Debug the deliverable creation system"""
    
    def __init__(self):
        self.workspace_analysis = {}
        
    async def analyze_workspace_deliverable_status(self, workspace_id: str) -> Dict[str, Any]:
        """Comprehensive analysis of workspace deliverable readiness"""
        
        logger.info(f"🔍 ANALYZING WORKSPACE: {workspace_id}")
        
        analysis = {
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "workspace_data": None,
            "tasks_analysis": {},
            "goals_analysis": {},
            "deliverable_checks": {},
            "blocking_conditions": [],
            "recommendations": []
        }
        
        try:
            # 1. Get workspace data
            workspace = await get_workspace(workspace_id)
            analysis["workspace_data"] = {
                "exists": workspace is not None,
                "goal": workspace.get("goal", "") if workspace else None,
                "created_at": workspace.get("created_at") if workspace else None,
                "status": workspace.get("status") if workspace else None
            }
            
            if not workspace:
                analysis["blocking_conditions"].append("Workspace does not exist")
                return analysis
            
            # 2. Analyze tasks
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            pending_tasks = [t for t in tasks if t.get("status") == "pending"]
            in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
            failed_tasks = [t for t in tasks if t.get("status") == "failed"]
            
            analysis["tasks_analysis"] = {
                "total_tasks": len(tasks),
                "completed": len(completed_tasks),
                "pending": len(pending_tasks),
                "in_progress": len(in_progress_tasks),
                "failed": len(failed_tasks),
                "completion_rate": len(completed_tasks) / len(tasks) if tasks else 0,
                "has_structured_output": []
            }
            
            # Check for structured output in completed tasks
            for task in completed_tasks:
                result = task.get('result', {}) or {}
                detailed_json = result.get('detailed_results_json', '')
                summary = result.get('summary', '')
                
                has_output = bool(detailed_json or (summary and len(summary) > 100))
                if has_output:
                    analysis["tasks_analysis"]["has_structured_output"].append({
                        "task_id": task.get("id"),
                        "name": task.get("name", ""),
                        "has_json": bool(detailed_json),
                        "summary_length": len(summary) if summary else 0
                    })
            
            # 3. Analyze goals
            goals = await get_workspace_goals(workspace_id)
            analysis["goals_analysis"] = {
                "total_goals": len(goals),
                "goals_data": []
            }
            
            for goal in goals:
                goal_data = {
                    "id": goal.get("id"),
                    "metric_type": goal.get("metric_type"),
                    "progress_percentage": goal.get("progress_percentage", 0),
                    "status": goal.get("status"),
                    "business_value_score": goal.get("business_value_score", 0)
                }
                analysis["goals_analysis"]["goals_data"].append(goal_data)
            
            # 4. Check deliverable readiness using internal methods
            try:
                is_ready = await deliverable_aggregator._is_ready_for_deliverable(workspace_id)
                deliverable_exists = await deliverable_aggregator._deliverable_exists(workspace_id)
                
                analysis["deliverable_checks"] = {
                    "is_ready_for_deliverable": is_ready,
                    "deliverable_already_exists": deliverable_exists,
                    "min_completed_tasks_threshold": deliverable_aggregator.min_completed_tasks,
                    "readiness_threshold": deliverable_aggregator.readiness_threshold,
                    "meets_min_tasks": len(completed_tasks) >= deliverable_aggregator.min_completed_tasks,
                    "meets_readiness_threshold": analysis["tasks_analysis"]["completion_rate"] >= deliverable_aggregator.readiness_threshold
                }
                
            except Exception as e:
                analysis["deliverable_checks"]["error"] = str(e)
                logger.error(f"Error checking deliverable readiness: {e}")
            
            # 5. Identify blocking conditions
            if analysis["tasks_analysis"]["completed"] < deliverable_aggregator.min_completed_tasks:
                analysis["blocking_conditions"].append(f"Not enough completed tasks: {analysis['tasks_analysis']['completed']} < {deliverable_aggregator.min_completed_tasks}")
            
            if analysis["tasks_analysis"]["completion_rate"] < deliverable_aggregator.readiness_threshold:
                analysis["blocking_conditions"].append(f"Completion rate too low: {analysis['tasks_analysis']['completion_rate']:.2f} < {deliverable_aggregator.readiness_threshold}")
            
            if analysis["deliverable_checks"].get("deliverable_already_exists"):
                analysis["blocking_conditions"].append("Deliverable already exists")
            
            if not analysis["tasks_analysis"]["has_structured_output"]:
                analysis["blocking_conditions"].append("No tasks with structured output found")
            
            # 6. Generate recommendations
            if analysis["blocking_conditions"]:
                analysis["recommendations"].append("Address blocking conditions listed above")
            else:
                analysis["recommendations"].append("Workspace appears ready for deliverable creation")
            
            logger.info(f"✅ ANALYSIS COMPLETE for {workspace_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing workspace {workspace_id}: {e}")
            analysis["error"] = str(e)
            return analysis
    
    async def test_deliverable_creation(self, workspace_id: str) -> Dict[str, Any]:
        """Test deliverable creation for a specific workspace"""
        
        logger.info(f"🧪 TESTING DELIVERABLE CREATION: {workspace_id}")
        
        test_result = {
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "creation_attempted": False,
            "creation_successful": False,
            "deliverable_id": None,
            "error": None,
            "logs": []
        }
        
        try:
            # Attempt to create deliverable
            test_result["creation_attempted"] = True
            test_result["logs"].append("Attempting deliverable creation...")
            
            deliverable_id = await check_and_create_final_deliverable(workspace_id)
            
            if deliverable_id:
                test_result["creation_successful"] = True
                test_result["deliverable_id"] = deliverable_id
                test_result["logs"].append(f"✅ Deliverable created successfully: {deliverable_id}")
            else:
                test_result["logs"].append("❌ Deliverable creation returned None")
                
        except Exception as e:
            test_result["error"] = str(e)
            test_result["logs"].append(f"❌ Exception during creation: {e}")
            logger.error(f"Error testing deliverable creation: {e}")
        
        return test_result
        
    async def find_workspaces_for_analysis(self, limit: int = 10) -> List[str]:
        """Find workspaces that should have deliverables but don't"""
        
        logger.info(f"🔍 FINDING WORKSPACES FOR ANALYSIS (limit: {limit})")
        
        try:
            workspaces = await list_workspaces()
            logger.info(f"Found {len(workspaces)} total workspaces")
            
            candidate_workspaces = []
            
            for workspace in workspaces[:limit]:  # Limit to avoid overwhelming
                workspace_id = workspace.get("id")
                if not workspace_id:
                    continue
                
                try:
                    tasks = await list_tasks(workspace_id)
                    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
                    
                    # Check if workspace has potential for deliverable
                    if len(completed_tasks) >= 1:  # At least 1 completed task
                        # Check if deliverable already exists
                        has_deliverable = False
                        for task in tasks:
                            context_data = task.get("context_data", {}) or {}
                            if isinstance(context_data, dict) and context_data.get("is_final_deliverable"):
                                has_deliverable = True
                                break
                        
                        if not has_deliverable:
                            candidate_workspaces.append(workspace_id)
                            logger.info(f"  ✓ Candidate: {workspace_id} ({len(completed_tasks)} completed tasks)")
                    
                except Exception as e:
                    logger.error(f"Error analyzing workspace {workspace_id}: {e}")
                    continue
            
            logger.info(f"Found {len(candidate_workspaces)} candidate workspaces")
            return candidate_workspaces
            
        except Exception as e:
            logger.error(f"Error finding workspaces: {e}")
            return []
    
    async def comprehensive_analysis(self, workspace_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run comprehensive analysis on multiple workspaces"""
        
        if not workspace_ids:
            workspace_ids = await self.find_workspaces_for_analysis()
        
        logger.info(f"🔬 COMPREHENSIVE ANALYSIS on {len(workspace_ids)} workspaces")
        
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_workspaces_analyzed": len(workspace_ids),
            "workspaces": {},
            "summary": {
                "ready_for_deliverable": 0,
                "blocked_workspaces": 0,
                "successful_creations": 0,
                "failed_creations": 0,
                "common_blocking_conditions": {}
            }
        }
        
        for workspace_id in workspace_ids:
            try:
                # Analyze workspace
                analysis = await self.analyze_workspace_deliverable_status(workspace_id)
                
                # Test deliverable creation if it looks ready
                if not analysis.get("blocking_conditions"):
                    test_result = await self.test_deliverable_creation(workspace_id)
                    analysis["creation_test"] = test_result
                    
                    if test_result["creation_successful"]:
                        results["summary"]["successful_creations"] += 1
                    else:
                        results["summary"]["failed_creations"] += 1
                else:
                    results["summary"]["blocked_workspaces"] += 1
                
                results["workspaces"][workspace_id] = analysis
                
                # Track common blocking conditions
                for condition in analysis.get("blocking_conditions", []):
                    if condition not in results["summary"]["common_blocking_conditions"]:
                        results["summary"]["common_blocking_conditions"][condition] = 0
                    results["summary"]["common_blocking_conditions"][condition] += 1
                
                if not analysis.get("blocking_conditions"):
                    results["summary"]["ready_for_deliverable"] += 1
                
            except Exception as e:
                logger.error(f"Error in comprehensive analysis for {workspace_id}: {e}")
                results["workspaces"][workspace_id] = {"error": str(e)}
        
        return results

async def main():
    """Main debug function"""
    
    debugger = DeliverableDebugger()
    
    # Check if specific workspace ID provided
    if len(sys.argv) > 1:
        workspace_id = sys.argv[1]
        logger.info(f"🎯 DEBUGGING SPECIFIC WORKSPACE: {workspace_id}")
        
        analysis = await debugger.analyze_workspace_deliverable_status(workspace_id)
        print("\n" + "="*80)
        print("WORKSPACE ANALYSIS RESULTS")
        print("="*80)
        
        print(f"Workspace ID: {analysis['workspace_id']}")
        print(f"Timestamp: {analysis['timestamp']}")
        
        print(f"\n📊 WORKSPACE DATA:")
        workspace_data = analysis['workspace_data']
        print(f"  Exists: {workspace_data['exists']}")
        print(f"  Goal: {workspace_data['goal']}")
        print(f"  Status: {workspace_data['status']}")
        
        print(f"\n📋 TASKS ANALYSIS:")
        tasks = analysis['tasks_analysis']
        print(f"  Total: {tasks['total_tasks']}")
        print(f"  Completed: {tasks['completed']}")
        print(f"  Pending: {tasks['pending']}")
        print(f"  In Progress: {tasks['in_progress']}")
        print(f"  Failed: {tasks['failed']}")
        print(f"  Completion Rate: {tasks['completion_rate']:.2%}")
        print(f"  Tasks with Structured Output: {len(tasks['has_structured_output'])}")
        
        print(f"\n🎯 GOALS ANALYSIS:")
        goals = analysis['goals_analysis']
        print(f"  Total Goals: {goals['total_goals']}")
        for goal in goals['goals_data']:
            print(f"    - {goal['metric_type']}: {goal['progress_percentage']}% (Business Value: {goal['business_value_score']})")
        
        print(f"\n🔍 DELIVERABLE CHECKS:")
        checks = analysis['deliverable_checks']
        for key, value in checks.items():
            print(f"  {key}: {value}")
        
        print(f"\n🚫 BLOCKING CONDITIONS:")
        for condition in analysis['blocking_conditions']:
            print(f"  ❌ {condition}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print(f"  ✅ {rec}")
        
        # If workspace looks ready, test creation
        if not analysis['blocking_conditions']:
            print(f"\n🧪 TESTING DELIVERABLE CREATION...")
            test_result = await debugger.test_deliverable_creation(workspace_id)
            print(f"  Creation Attempted: {test_result['creation_attempted']}")
            print(f"  Creation Successful: {test_result['creation_successful']}")
            if test_result['deliverable_id']:
                print(f"  Deliverable ID: {test_result['deliverable_id']}")
            if test_result['error']:
                print(f"  Error: {test_result['error']}")
            for log in test_result['logs']:
                print(f"  {log}")
    
    else:
        # Run comprehensive analysis
        logger.info("🔬 RUNNING COMPREHENSIVE ANALYSIS")
        
        results = await debugger.comprehensive_analysis()
        
        print("\n" + "="*80)
        print("COMPREHENSIVE DELIVERABLE ANALYSIS RESULTS")
        print("="*80)
        
        print(f"Analysis Timestamp: {results['analysis_timestamp']}")
        print(f"Total Workspaces Analyzed: {results['total_workspaces_analyzed']}")
        
        summary = results['summary']
        print(f"\n📊 SUMMARY:")
        print(f"  Ready for Deliverable: {summary['ready_for_deliverable']}")
        print(f"  Blocked Workspaces: {summary['blocked_workspaces']}")
        print(f"  Successful Creations: {summary['successful_creations']}")
        print(f"  Failed Creations: {summary['failed_creations']}")
        
        print(f"\n🚫 COMMON BLOCKING CONDITIONS:")
        for condition, count in summary['common_blocking_conditions'].items():
            print(f"  {condition}: {count} workspace(s)")
        
        print(f"\n📋 DETAILED WORKSPACE RESULTS:")
        for workspace_id, analysis in results['workspaces'].items():
            if 'error' in analysis:
                print(f"  ❌ {workspace_id}: ERROR - {analysis['error']}")
            else:
                tasks = analysis['tasks_analysis']
                blocking = len(analysis['blocking_conditions'])
                print(f"  {'✅' if blocking == 0 else '❌'} {workspace_id}: {tasks['completed']}/{tasks['total_tasks']} tasks ({tasks['completion_rate']:.1%}), {blocking} blocking conditions")

if __name__ == "__main__":
    asyncio.run(main())