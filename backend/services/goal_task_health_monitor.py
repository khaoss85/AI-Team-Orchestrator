# backend/services/goal_task_health_monitor.py
"""
🛡️ STRATEGIC SELF-HEALING: Goal-Task Health Monitor

This service continuously monitors the health of goal-task relationships and automatically
fixes issues like:
1. Goals with no tasks
2. Tasks with no agent assignments
3. Failed tasks that need retry with proper agents
4. Orphaned tasks without goals

This prevents the systematic failure where goals (especially deliverable_ types) 
get stuck with no progress.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from database import supabase
from models import GoalStatus, TaskStatus

logger = logging.getLogger(__name__)


class GoalTaskHealthMonitor:
    """
    Monitor and heal goal-task relationship issues automatically
    """
    
    def __init__(self):
        # Configuration
        self.check_interval_seconds = int(os.getenv("GOAL_TASK_HEALTH_CHECK_INTERVAL", "300"))  # 5 minutes
        self.max_retries_per_task = int(os.getenv("MAX_TASK_RETRIES", "3"))
        self.is_running = False
        
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if self.is_running:
            logger.warning("Goal-Task Health Monitor already running")
            return
            
        self.is_running = True
        logger.info(f"🏥 Starting Goal-Task Health Monitor (check every {self.check_interval_seconds}s)")
        
        while self.is_running:
            try:
                await self._run_health_check_cycle()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Error in health check cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_monitoring(self):
        """Stop the health monitoring"""
        self.is_running = False
        logger.info("🛑 Stopped Goal-Task Health Monitor")
    
    async def _run_health_check_cycle(self):
        """Execute one complete health check cycle"""
        cycle_start = datetime.now()
        logger.info(f"🔍 Starting goal-task health check at {cycle_start}")
        
        try:
            # 1. Check for goals without tasks
            goals_without_tasks = await self._find_goals_without_tasks()
            if goals_without_tasks:
                logger.warning(f"🚨 Found {len(goals_without_tasks)} goals without tasks")
                await self._create_tasks_for_orphaned_goals(goals_without_tasks)
            
            # 2. Check for tasks without agents
            tasks_without_agents = await self._find_tasks_without_agents()
            if tasks_without_agents:
                logger.warning(f"🚨 Found {len(tasks_without_agents)} tasks without agents")
                await self._assign_agents_to_orphaned_tasks(tasks_without_agents)
            
            # 3. Check for failed tasks that can be retried
            failed_tasks = await self._find_failed_tasks_for_retry()
            if failed_tasks:
                logger.warning(f"🚨 Found {len(failed_tasks)} failed tasks to retry")
                await self._retry_failed_tasks(failed_tasks)
            
            # 4. Log cycle summary
            cycle_duration = datetime.now() - cycle_start
            logger.info(
                f"✅ Health check completed in {cycle_duration.total_seconds():.1f}s. "
                f"Fixed: {len(goals_without_tasks)} goals, {len(tasks_without_agents)} tasks, "
                f"retried {len(failed_tasks)} failed tasks"
            )
            
        except Exception as e:
            logger.error(f"Error in health check cycle: {e}")
    
    async def _find_goals_without_tasks(self) -> List[Dict[str, Any]]:
        """Find active goals that have no tasks"""
        try:
            # Get all active goals
            goals_response = supabase.table("workspace_goals").select("*").eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            goals = goals_response.data or []
            goals_without_tasks = []
            
            for goal in goals:
                # Check if goal has any tasks
                tasks_response = supabase.table("tasks").select("id").eq(
                    "goal_id", goal["id"]
                ).limit(1).execute()
                
                if not tasks_response.data:
                    goals_without_tasks.append(goal)
                    logger.warning(
                        f"📋 Goal without tasks: {goal['metric_type']} "
                        f"(ID: {goal['id']}, Workspace: {goal['workspace_id']})"
                    )
            
            return goals_without_tasks
            
        except Exception as e:
            logger.error(f"Error finding goals without tasks: {e}")
            return []
    
    async def _find_tasks_without_agents(self) -> List[Dict[str, Any]]:
        """Find pending/failed tasks that have no agent assigned"""
        try:
            # Find tasks with no agent that are not completed
            tasks_response = supabase.table("tasks").select("*").is_(
                "agent_id", "null"
            ).in_(
                "status", ["pending", "failed", "in_progress"]
            ).execute()
            
            tasks = tasks_response.data or []
            
            for task in tasks:
                logger.warning(
                    f"📋 Task without agent: {task['name']} "
                    f"(ID: {task['id']}, Status: {task['status']})"
                )
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error finding tasks without agents: {e}")
            return []
    
    async def _find_failed_tasks_for_retry(self) -> List[Dict[str, Any]]:
        """Find failed tasks that can be retried"""
        try:
            # Find recently failed tasks (within last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            tasks_response = supabase.table("tasks").select("*").eq(
                "status", "failed"
            ).gte(
                "updated_at", cutoff_time.isoformat()
            ).execute()
            
            tasks = tasks_response.data or []
            
            # Filter tasks that haven't exceeded max retries
            retriable_tasks = []
            for task in tasks:
                retry_count = task.get("retry_count", 0)
                if retry_count < self.max_retries_per_task:
                    retriable_tasks.append(task)
            
            return retriable_tasks
            
        except Exception as e:
            logger.error(f"Error finding failed tasks for retry: {e}")
            return []
    
    async def _create_tasks_for_orphaned_goals(self, goals: List[Dict[str, Any]]):
        """Create tasks for goals that have none"""
        try:
            from goal_driven_task_planner import goal_driven_task_planner
            
            for goal in goals:
                try:
                    workspace_id = goal["workspace_id"]
                    
                    logger.info(f"🔧 Creating tasks for orphaned goal: {goal['metric_type']}")
                    
                    # Use the task planner to create tasks
                    tasks = await goal_driven_task_planner.plan_tasks_for_goal(
                        workspace_goal=goal,
                        workspace_id=workspace_id
                    )
                    
                    if tasks:
                        logger.info(f"✅ Created {len(tasks)} tasks for goal {goal['metric_type']}")
                        
                        # Log the healing action
                        supabase.table("logs").insert({
                            "workspace_id": workspace_id,
                            "type": "system",
                            "message": f"AUTO-HEALING: Created {len(tasks)} tasks for orphaned goal",
                            "metadata": {
                                "action": "goal_task_healing",
                                "goal_id": goal["id"],
                                "goal_type": goal["metric_type"],
                                "tasks_created": len(tasks),
                                "component": "goal_task_health_monitor"
                            },
                            "created_at": datetime.now().isoformat()
                        }).execute()
                    else:
                        logger.error(f"❌ Failed to create tasks for goal {goal['metric_type']}")
                        
                except Exception as e:
                    logger.error(f"Error creating tasks for goal {goal.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in task creation for orphaned goals: {e}")
    
    async def _assign_agents_to_orphaned_tasks(self, tasks: List[Dict[str, Any]]):
        """Assign agents to tasks that have none"""
        try:
            # Group tasks by workspace
            workspace_tasks = {}
            for task in tasks:
                workspace_id = task["workspace_id"]
                if workspace_id not in workspace_tasks:
                    workspace_tasks[workspace_id] = []
                workspace_tasks[workspace_id].append(task)
            
            # Process each workspace
            for workspace_id, ws_tasks in workspace_tasks.items():
                # Get available agents for the workspace
                agents_response = supabase.table("agents").select("*").eq(
                    "workspace_id", workspace_id
                ).in_(
                    "status", ["available", "active"]
                ).execute()
                
                available_agents = agents_response.data or []
                
                if not available_agents:
                    logger.error(f"❌ No agents available for workspace {workspace_id}")
                    
                    # Try to create basic agents
                    await self._auto_provision_agents_for_workspace(workspace_id)
                    
                    # Re-fetch agents
                    agents_response = supabase.table("agents").select("*").eq(
                        "workspace_id", workspace_id
                    ).in_(
                        "status", ["available", "active"]
                    ).execute()
                    available_agents = agents_response.data or []
                
                if available_agents:
                    # Assign agents to tasks (round-robin)
                    agent_index = 0
                    for task in ws_tasks:
                        agent = available_agents[agent_index % len(available_agents)]
                        
                        # Update task with agent assignment
                        supabase.table("tasks").update({
                            "agent_id": agent["id"],
                            "updated_at": datetime.now().isoformat()
                        }).eq("id", task["id"]).execute()
                        
                        logger.info(
                            f"✅ Assigned agent {agent['name']} to task {task['name']}"
                        )
                        
                        agent_index += 1
                    
                    # Log the healing action
                    supabase.table("logs").insert({
                        "workspace_id": workspace_id,
                        "type": "system",
                        "message": f"AUTO-HEALING: Assigned agents to {len(ws_tasks)} orphaned tasks",
                        "metadata": {
                            "action": "agent_assignment_healing",
                            "tasks_fixed": len(ws_tasks),
                            "agents_used": len(available_agents),
                            "component": "goal_task_health_monitor"
                        },
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    
        except Exception as e:
            logger.error(f"Error assigning agents to orphaned tasks: {e}")
    
    async def _retry_failed_tasks(self, tasks: List[Dict[str, Any]]):
        """Retry failed tasks with proper agent assignment"""
        try:
            for task in tasks:
                try:
                    retry_count = task.get("retry_count", 0)
                    
                    # Check if task has an agent
                    if not task.get("agent_id"):
                        # Assign an agent first
                        await self._assign_agents_to_orphaned_tasks([task])
                    
                    # Reset task status to pending for retry
                    supabase.table("tasks").update({
                        "status": "pending",
                        "retry_count": retry_count + 1,
                        "updated_at": datetime.now().isoformat(),
                        "error_message": None  # Clear previous error
                    }).eq("id", task["id"]).execute()
                    
                    logger.info(
                        f"🔄 Reset task {task['name']} for retry (attempt {retry_count + 1})"
                    )
                    
                except Exception as e:
                    logger.error(f"Error retrying task {task.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in task retry process: {e}")
    
    async def _auto_provision_agents_for_workspace(self, workspace_id: str):
        """Auto-provision basic agents for a workspace"""
        try:
            logger.info(f"🤖 Auto-provisioning agents for workspace {workspace_id}")
            
            # Get workspace details
            workspace_response = supabase.table("workspaces").select("*").eq(
                "id", workspace_id
            ).single().execute()
            
            if not workspace_response.data:
                logger.error(f"Workspace {workspace_id} not found")
                return
            
            workspace = workspace_response.data
            workspace_name = workspace.get("name", "Unknown")
            
            # Create basic agent team
            agents = [
                {
                    "workspace_id": workspace_id,
                    "name": "Emergency Task Handler",
                    "role": "specialist",
                    "seniority": "senior",
                    "description": f"Auto-provisioned specialist for {workspace_name}",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "workspace_id": workspace_id,
                    "name": "Emergency Coordinator",
                    "role": "project_manager",
                    "seniority": "senior",
                    "description": f"Auto-provisioned coordinator for {workspace_name}",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            # Insert agents
            for agent in agents:
                try:
                    supabase.table("agents").insert(agent).execute()
                    logger.info(f"✅ Created agent: {agent['name']}")
                except Exception as e:
                    logger.error(f"Failed to create agent {agent['name']}: {e}")
            
        except Exception as e:
            logger.error(f"Error auto-provisioning agents: {e}")
    
    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        """Check health of a specific workspace's goals and tasks"""
        try:
            # Get workspace goals
            goals_response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            goals = goals_response.data or []
            
            health_report = {
                "workspace_id": workspace_id,
                "total_goals": len(goals),
                "goals_without_tasks": [],
                "tasks_without_agents": [],
                "failed_tasks": [],
                "health_score": 100.0
            }
            
            for goal in goals:
                # Check tasks for this goal
                tasks_response = supabase.table("tasks").select("*").eq(
                    "goal_id", goal["id"]
                ).execute()
                
                tasks = tasks_response.data or []
                
                if not tasks:
                    health_report["goals_without_tasks"].append({
                        "goal_id": goal["id"],
                        "metric_type": goal["metric_type"]
                    })
                    health_report["health_score"] -= 10
                
                for task in tasks:
                    if not task.get("agent_id"):
                        health_report["tasks_without_agents"].append({
                            "task_id": task["id"],
                            "task_name": task["name"]
                        })
                        health_report["health_score"] -= 5
                    
                    if task.get("status") == "failed":
                        health_report["failed_tasks"].append({
                            "task_id": task["id"],
                            "task_name": task["name"]
                        })
                        health_report["health_score"] -= 3
            
            health_report["health_score"] = max(0, health_report["health_score"])
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error checking workspace health: {e}")
            return {
                "workspace_id": workspace_id,
                "error": str(e),
                "health_score": 0
            }


# Singleton instance
goal_task_health_monitor = GoalTaskHealthMonitor()