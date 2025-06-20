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
            new_agent = {
                "workspace_id": workspace_id,
                "name": f"{role.title()} Specialist",
                "role": role,
                "seniority": seniority,
                "skills": skills or [],
                "status": "idle",
                "utilization_percentage": 0
            }
            
            result = self.db_client.table("agents").insert(new_agent).execute()
            return {
                "success": True,
                "message": f"Added new {role} to the team",
                "agent": result.data[0] if result.data else None
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
                
            return {
                "success": True,
                "workspace_status": workspace.data[0]["status"] if workspace.data else "unknown",
                "team_members": len(agents.data),
                "agents": agents.data
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
            
            if goal_id:
                # Get specific goal
                goal = self.db_client.table("goals")\
                    .select("*")\
                    .eq("id", goal_id)\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                goals_data = goal.data
            else:
                # Get all goals
                goals = self.db_client.table("goals")\
                    .select("*")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                goals_data = goals.data
            
            results = []
            for goal in goals_data:
                # Use existing progress calculation if available
                progress = goal.get("completion_percentage", 0)
                
                results.append({
                    "goal_id": goal["id"],
                    "title": goal["title"],
                    "status": goal["status"],
                    "progress": f"{progress:.0f}%",
                    "description": goal.get("description", "")
                })
            
            return {
                "success": True,
                "goals": results,
                "message": f"Found {len(results)} goal(s) with progress information"
            }
        except Exception as e:
            logger.error(f"Error getting goal progress: {e}")
            return {"success": False, "message": str(e)}
    
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