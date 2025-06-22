"""
Workspace Service - Universal abstraction layer for workspace operations
Adheres to AGNOSTIC and SCALABLE pillars by providing database-agnostic methods
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WorkspaceServiceInterface(ABC):
    """Abstract interface for workspace operations - AGNOSTIC pillar"""
    
    @abstractmethod
    async def add_team_member(self, workspace_id: str, role: str, seniority: str = "senior", skills: List[str] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_team_status(self, workspace_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def update_workspace_status(self, workspace_id: str, status: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_goal_progress(self, workspace_id: str, goal_id: str = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_deliverables(self, workspace_id: str, filter_type: str = "all") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def create_goal(self, workspace_id: str, title: str, description: str = "") -> Dict[str, Any]:
        pass


class SupabaseWorkspaceService(WorkspaceServiceInterface):
    """Supabase implementation - can be swapped for other databases"""
    
    def __init__(self, db_client):
        self.db_client = db_client
    
    async def add_team_member(self, workspace_id: str, role: str, seniority: str = "senior", skills: List[str] = None) -> Dict[str, Any]:
        """SCALABLE: Reuses existing logic, no duplication"""
        try:
            # Generate comprehensive agent data
            agent_name = f"{role.title()} Specialist"
            first_name = role.title()
            last_name = "Specialist"
            
            new_agent = {
                "workspace_id": workspace_id,
                "name": agent_name,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "seniority": seniority,
                "status": "created",
                "description": f"AI-generated {role} specialist for enhanced project capabilities",
                "system_prompt": f"You are a {seniority} {role} specialist. Provide expert guidance in {role} related tasks and collaborate effectively with the team.",
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "can_create_tools": False,
                "background_story": f"Experienced {seniority}-level {role} with expertise in supporting project goals and team collaboration."
            }
            
            result = self.db_client.table("agents").insert(new_agent).execute()
            agent_data = result.data[0] if result.data else None
            return {
                "success": True,
                "message": f"Successfully added {new_agent['name']} ({seniority} {role}) to the team",
                "data": agent_data,
                "details": f"New team member created with ID: {agent_data['id'] if agent_data else 'N/A'}. Status: {agent_data['status'] if agent_data else 'unknown'}"
            }
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_team_status(self, workspace_id: str) -> Dict[str, Any]:
        """SCALABLE: Uses existing API patterns"""
        try:
            agents = self.db_client.table("agents")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .execute()
                
            workspace = self.db_client.table("workspaces")\
                .select("*")\
                .eq("id", workspace_id)\
                .execute()
            
            # Also fetch handoffs for team collaboration info
            try:
                handoffs = self.db_client.table("handoffs")\
                    .select("*")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                handoffs_data = handoffs.data
            except Exception as handoff_error:
                logger.warning(f"Could not fetch handoffs: {handoff_error}")
                handoffs_data = []
                
            return {
                "success": True,
                "workspace_status": workspace.data[0]["status"] if workspace.data else "unknown",
                "team_members": len(agents.data),
                "agents": agents.data,
                "handoffs": handoffs_data,
                "message": f"Team has {len(agents.data)} members, {len(handoffs_data)} handoffs, workspace status: {workspace.data[0]['status'] if workspace.data else 'unknown'}"
            }
        except Exception as e:
            logger.error(f"Error getting team status: {e}")
            return {"success": False, "message": str(e)}
    
    async def update_workspace_status(self, workspace_id: str, status: str) -> Dict[str, Any]:
        """SCALABLE: Single responsibility"""
        try:
            result = self.db_client.table("workspaces")\
                .update({"status": status})\
                .eq("id", workspace_id)\
                .execute()
            
            if status == "active":
                # Update all agents to available
                self.db_client.table("agents")\
                    .update({"status": "available"})\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                message = "Team started successfully. All agents are now available for tasks."
            else:
                message = "Team activities paused. Current tasks will complete but no new tasks will start."
                
            return {"success": True, "message": message}
        except Exception as e:
            logger.error(f"Error updating workspace status: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_goal_progress(self, workspace_id: str, goal_id: str = None) -> Dict[str, Any]:
        """SCALABLE: Reuses existing business logic from goal services"""
        try:
            # SCALABLE: Reuse existing services when available
            # Try to import existing goal service to avoid duplication
            try:
                from ai_quality_assurance.strategic_goal_decomposer import StrategicGoalDecomposer
                goal_service = StrategicGoalDecomposer()
            except ImportError:
                # Fallback to simple implementation if service not available
                goal_service = None
            
            # Check if goals table exists first
            try:
                if goal_id:
                    # Get specific goal
                    goal = self.db_client.table("workspace_goals")\
                        .select("*")\
                        .eq("id", goal_id)\
                        .eq("workspace_id", workspace_id)\
                        .execute()
                    goals_data = goal.data
                else:
                    # Get all goals
                    goals = self.db_client.table("workspace_goals")\
                        .select("*")\
                        .eq("workspace_id", workspace_id)\
                        .execute()
                    goals_data = goals.data
                
                logger.info(f"📊 [get_goal_progress] Raw goals data: {goals_data}")
                
                results = []
                for goal in goals_data:
                    logger.info(f"🎯 [get_goal_progress] Processing goal: {goal}")
                    # Use existing progress calculation if available
                    progress = goal.get("completion_percentage", 0)
                    
                    results.append({
                        "goal_id": goal["id"],
                        "title": goal.get("title") or goal.get("name") or goal.get("goal_title") or f"Goal {goal['id']}",
                        "status": goal.get("status", "unknown"),
                        "progress": f"{progress:.0f}%",
                        "description": goal.get("description", "")
                    })
                
                return {
                    "success": True,
                    "goals": results,
                    "message": f"Found {len(results)} goal(s) with progress information"
                }
                
            except Exception as table_error:
                # Handle case where goals table doesn't exist
                if "does not exist" in str(table_error) or "42P01" in str(table_error):
                    return {
                        "success": True,
                        "goals": [],
                        "message": "Goals system not yet initialized for this workspace. The team is working on general workspace objectives without specific tracked goals."
                    }
                else:
                    # Re-raise other database errors
                    raise table_error
        except Exception as e:
            logger.error(f"Error getting goal progress: {e}")
            logger.error(f"Exception type: {type(e)}")
            return {"success": False, "message": str(e)}
    
    async def get_project_status(self, workspace_id: str) -> Dict[str, Any]:
        """Get comprehensive project status combining team, tasks, and deliverables"""
        try:
            # Get team status
            team_status = await self.get_team_status(workspace_id)
            
            # Get tasks summary
            try:
                tasks = self.db_client.table("tasks")\
                    .select("status")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                
                task_summary = {}
                for task in tasks.data:
                    status = task.get("status", "unknown")
                    task_summary[status] = task_summary.get(status, 0) + 1
                    
            except Exception:
                task_summary = {"info": "Task data not available"}
            
            # Get deliverables
            try:
                deliverables_result = await self.get_deliverables(workspace_id, "all")
                deliverables_count = len(deliverables_result.get("deliverables", [])) if deliverables_result.get("success") else 0
            except Exception:
                deliverables_count = 0
            
            # Get goals (safely)
            try:
                goals_result = await self.get_goal_progress(workspace_id)
                goals_info = goals_result.get("message", "Goals status unavailable")
                goals_count = len(goals_result.get("goals", [])) if goals_result.get("success") else 0
            except Exception:
                goals_info = "Goals system not available"
                goals_count = 0
            
            # Compose comprehensive status
            status_parts = []
            
            # Team info
            if team_status.get("success"):
                team_count = team_status.get("team_members", 0)
                workspace_status = team_status.get("workspace_status", "unknown")
                status_parts.append(f"Team: {team_count} members, workspace status: {workspace_status}")
            
            # Tasks info
            if task_summary and "info" not in task_summary:
                task_details = []
                for status, count in task_summary.items():
                    task_details.append(f"{count} {status}")
                if task_details:
                    status_parts.append(f"Tasks: {', '.join(task_details)}")
            
            # Deliverables info
            if deliverables_count > 0:
                status_parts.append(f"Deliverables: {deliverables_count} completed")
            else:
                status_parts.append("Deliverables: none completed yet")
            
            # Goals info
            if goals_count > 0:
                status_parts.append(f"Goals: {goals_count} tracked")
            else:
                status_parts.append(f"Goals: {goals_info}")
            
            return {
                "success": True,
                "message": "\n".join(status_parts),
                "details": {
                    "team": team_status,
                    "tasks": task_summary,
                    "deliverables_count": deliverables_count,
                    "goals_count": goals_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting project status: {e}")
            return {"success": False, "message": f"Could not retrieve project status: {str(e)}"}
    
    async def get_deliverables(self, workspace_id: str, filter_type: str = "all") -> Dict[str, Any]:
        """SCALABLE: Uses existing API endpoints"""
        try:
            # SCALABLE: Reuse existing API logic when available
            try:
                from routes.asset_management import get_unified_assets
                from routes.monitoring import get_project_deliverables
            except ImportError:
                # Fallback if routes not available
                get_unified_assets = None
                get_project_deliverables = None
            
            results = {"deliverables": [], "assets": []}
            
            if filter_type in ["deliverables", "all"]:
                # Use existing deliverables endpoint logic
                deliverables = self.db_client.table("project_deliverables")\
                    .select("*")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                
                results["deliverables"] = [{
                    "id": d["id"],
                    "title": d["title"],
                    "type": d["deliverable_type"],
                    "created_at": d["created_at"],
                    "content_preview": d.get("content", "")[:200] + "..." if d.get("content") else "No content"
                } for d in deliverables.data]
            
            if filter_type in ["assets", "all"]:
                # Use existing assets endpoint logic
                assets = self.db_client.table("project_assets")\
                    .select("*")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                
                results["assets"] = [{
                    "id": a["id"],
                    "name": a["name"],
                    "type": a["asset_type"],
                    "created_at": a["created_at"]
                } for a in assets.data]
            
            return {
                "success": True,
                "deliverables": results["deliverables"],
                "assets": results["assets"],
                "message": f"Found {len(results['deliverables'])} deliverables and {len(results['assets'])} assets"
            }
        except Exception as e:
            logger.error(f"Error getting deliverables: {e}")
            return {"success": False, "message": str(e)}
    
    async def create_goal(self, workspace_id: str, title: str, description: str = "") -> Dict[str, Any]:
        """SCALABLE: Uses existing goal creation patterns"""
        try:
            new_goal = {
                "workspace_id": workspace_id,
                "title": title,
                "description": description,
                "status": "active",
                "priority": "medium",
                "completion_percentage": 0
            }
            
            result = self.db_client.table("goals").insert(new_goal).execute()
            
            if result.data:
                goal = result.data[0]
                chat_id = f"goal-{goal['id']}"
                
                return {
                    "success": True,
                    "message": f"Created new goal: {goal['title']}",
                    "goal_id": goal["id"],
                    "chat_id": chat_id
                }
            else:
                return {"success": False, "message": "Failed to create goal"}
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return {"success": False, "message": str(e)}


def get_workspace_service(db_client) -> WorkspaceServiceInterface:
    """AGNOSTIC: Factory pattern allows swapping implementations"""
    return SupabaseWorkspaceService(db_client)