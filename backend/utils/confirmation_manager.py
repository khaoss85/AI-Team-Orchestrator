"""
Confirmation Manager - Two-step confirmation system for destructive actions
Universal system that prevents accidental data loss across any domain
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from enum import Enum

from ..database import get_supabase_client

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk levels for actions requiring confirmation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    """Types of actions that may require confirmation"""
    DELETE_AGENT = "delete_agent"
    REMOVE_DELIVERABLE = "remove_deliverable"
    RESET_BUDGET = "reset_budget"
    ARCHIVE_PROJECT = "archive_project"
    DELETE_TASKS = "delete_tasks"
    RESET_WORKSPACE = "reset_workspace"
    MODIFY_TEAM_SKILLS = "modify_team_skills"
    CHANGE_PROJECT_PHASE = "change_project_phase"
    BULK_DELETE = "bulk_delete"
    EXTERNAL_INTEGRATION = "external_integration"

class ConfirmationManager:
    """
    Universal confirmation manager for destructive or high-impact actions.
    Implements two-step confirmation with timeout and risk assessment.
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.supabase = get_supabase_client()
        
        # Risk-based expiration times
        self.expiration_times = {
            RiskLevel.LOW: timedelta(minutes=5),
            RiskLevel.MEDIUM: timedelta(minutes=3),
            RiskLevel.HIGH: timedelta(minutes=2),
            RiskLevel.CRITICAL: timedelta(minutes=1)
        }
        
        # Actions that always require confirmation
        self.always_confirm = {
            ActionType.DELETE_AGENT,
            ActionType.RESET_WORKSPACE,
            ActionType.ARCHIVE_PROJECT,
            ActionType.BULK_DELETE
        }
        
        # Risk assessment rules
        self.risk_rules = self._define_risk_rules()
    
    async def request_confirmation(
        self, 
        action_type: str,
        parameters: Dict[str, Any],
        description: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Request confirmation for a potentially destructive action.
        
        Args:
            action_type: Type of action (from ActionType enum)
            parameters: Action parameters
            description: Human-readable description of the action
            context: Additional context for risk assessment
            
        Returns:
            Dict with confirmation details or direct execution result
        """
        try:
            # Assess if confirmation is needed
            needs_confirmation, risk_level = await self._assess_confirmation_need(
                action_type, parameters, context or {}
            )
            
            if not needs_confirmation:
                # Execute action directly for low-risk operations
                return {
                    "requires_confirmation": False,
                    "executed_immediately": True,
                    "message": "Action executed successfully (low risk)",
                    "action_type": action_type
                }
            
            # Create confirmation request
            action_id = str(uuid4())
            expiration_time = datetime.now(timezone.utc) + self.expiration_times[risk_level]
            
            # Generate user-friendly confirmation message
            confirmation_message = await self._generate_confirmation_message(
                action_type, parameters, description, risk_level
            )
            
            # Store pending confirmation
            confirmation_data = {
                "action_id": action_id,
                "conversation_id": context.get("conversation_id"),
                "message_id": context.get("message_id"),
                "action_type": action_type,
                "action_description": description,
                "parameters": parameters,
                "risk_level": risk_level.value,
                "status": "pending",
                "expires_at": expiration_time.isoformat(),
                "metadata": {
                    "workspace_id": self.workspace_id,
                    "risk_assessment": await self._get_risk_assessment(action_type, parameters),
                    "alternatives": await self._suggest_alternatives(action_type, parameters)
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("pending_confirmations").insert(confirmation_data).execute()
            
            return {
                "requires_confirmation": True,
                "action_id": action_id,
                "confirmation_message": confirmation_message,
                "risk_level": risk_level.value,
                "expires_in_seconds": int(self.expiration_times[risk_level].total_seconds()),
                "alternatives": confirmation_data["metadata"]["alternatives"],
                "buttons": {
                    "confirm": f"✅ Yes, {self._get_action_verb(action_type)}",
                    "cancel": "❌ Cancel"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to request confirmation: {e}")
            return {
                "requires_confirmation": False,
                "error": True,
                "message": f"Failed to process confirmation request: {str(e)}"
            }
    
    async def _assess_confirmation_need(
        self, 
        action_type: str, 
        parameters: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> tuple[bool, RiskLevel]:
        """
        Assess whether confirmation is needed and determine risk level.
        Universal risk assessment that adapts to any domain.
        """
        try:
            action_enum = ActionType(action_type)
            
            # Always confirm certain actions
            if action_enum in self.always_confirm:
                return True, RiskLevel.HIGH
            
            # Apply risk rules
            risk_level = RiskLevel.LOW
            
            for rule in self.risk_rules:
                if rule["condition"](action_type, parameters, context):
                    rule_risk = RiskLevel(rule["risk_level"])
                    if self._risk_priority(rule_risk) > self._risk_priority(risk_level):
                        risk_level = rule_risk
            
            # Confirmation needed if risk is medium or higher
            needs_confirmation = self._risk_priority(risk_level) >= self._risk_priority(RiskLevel.MEDIUM)
            
            return needs_confirmation, risk_level
            
        except ValueError:
            # Unknown action type - default to requiring confirmation
            logger.warning(f"Unknown action type: {action_type}")
            return True, RiskLevel.MEDIUM
        except Exception as e:
            logger.error(f"Error assessing confirmation need: {e}")
            return True, RiskLevel.HIGH
    
    def _define_risk_rules(self) -> List[Dict[str, Any]]:
        """
        Define universal risk assessment rules.
        Rules are domain-agnostic and scale across any business vertical.
        """
        return [
            # Team member deletion rules
            {
                "name": "delete_only_team_member",
                "condition": lambda action, params, context: (
                    action == ActionType.DELETE_AGENT.value and 
                    self._is_only_team_member(params.get("agent_id"))
                ),
                "risk_level": RiskLevel.CRITICAL.value,
                "reason": "Deleting the only team member will leave project unmanned"
            },
            
            # Budget modification rules
            {
                "name": "large_budget_change",
                "condition": lambda action, params, context: (
                    "budget" in action and 
                    params.get("amount", 0) > self._get_budget_threshold()
                ),
                "risk_level": RiskLevel.HIGH.value,
                "reason": "Large budget changes may impact project viability"
            },
            
            # Data deletion rules
            {
                "name": "bulk_deletion",
                "condition": lambda action, params, context: (
                    "delete" in action and 
                    isinstance(params.get("items"), list) and 
                    len(params.get("items", [])) > 5
                ),
                "risk_level": RiskLevel.HIGH.value,
                "reason": "Bulk deletion may cause significant data loss"
            },
            
            # Project phase changes
            {
                "name": "phase_regression",
                "condition": lambda action, params, context: (
                    action == ActionType.CHANGE_PROJECT_PHASE.value and
                    self._is_phase_regression(params.get("from_phase"), params.get("to_phase"))
                ),
                "risk_level": RiskLevel.MEDIUM.value,
                "reason": "Moving to an earlier project phase may lose progress"
            },
            
            # External integrations
            {
                "name": "external_data_access",
                "condition": lambda action, params, context: (
                    action == ActionType.EXTERNAL_INTEGRATION.value and
                    params.get("access_level") in ["write", "admin"]
                ),
                "risk_level": RiskLevel.HIGH.value,
                "reason": "External integrations with write access pose security risks"
            },
            
            # Skill modifications that might break workflows
            {
                "name": "critical_skill_removal",
                "condition": lambda action, params, context: (
                    action == ActionType.MODIFY_TEAM_SKILLS.value and
                    self._removes_critical_skills(params.get("skills_to_remove", []))
                ),
                "risk_level": RiskLevel.MEDIUM.value,
                "reason": "Removing critical skills may impact project delivery"
            }
        ]
    
    async def _generate_confirmation_message(
        self, 
        action_type: str, 
        parameters: Dict[str, Any], 
        description: str, 
        risk_level: RiskLevel
    ) -> str:
        """
        Generate user-friendly confirmation message.
        Adapts language based on action type and risk level.
        """
        try:
            # Risk-based emoji and tone
            risk_indicators = {
                RiskLevel.LOW: "⚠️",
                RiskLevel.MEDIUM: "🚨",
                RiskLevel.HIGH: "⛔",
                RiskLevel.CRITICAL: "🚫"
            }
            
            risk_emoji = risk_indicators[risk_level]
            
            # Action-specific messages
            if action_type == ActionType.DELETE_AGENT.value:
                agent_name = parameters.get("agent_name", "this team member")
                return f"{risk_emoji} **Confirm Team Member Removal**\n\nAre you sure you want to remove **{agent_name}** from your team?\n\n• All their assigned tasks will become unassigned\n• Their skills and knowledge will be lost\n• This action cannot be undone\n\n{description}"
            
            elif action_type == ActionType.RESET_BUDGET.value:
                current_budget = parameters.get("current_budget", "unknown")
                return f"{risk_emoji} **Confirm Budget Reset**\n\nAre you sure you want to reset the project budget?\n\n• Current budget: €{current_budget}\n• All budget history will be lost\n• This may affect ongoing planning\n\n{description}"
            
            elif action_type == ActionType.ARCHIVE_PROJECT.value:
                project_name = parameters.get("project_name", "this project")
                return f"{risk_emoji} **Confirm Project Archive**\n\nAre you sure you want to archive **{project_name}**?\n\n• The project will become read-only\n• Team members will lose access\n• Active tasks will be suspended\n• This can be undone, but requires admin approval\n\n{description}"
            
            elif "delete" in action_type.lower():
                item_count = len(parameters.get("items", [1]))
                item_type = parameters.get("item_type", "items")
                return f"{risk_emoji} **Confirm Deletion**\n\nAre you sure you want to delete {item_count} {item_type}?\n\n• This action cannot be undone\n• All related data will be permanently lost\n• Dependencies may be affected\n\n{description}"
            
            # Generic confirmation message
            action_verb = self._get_action_verb(action_type)
            return f"{risk_emoji} **Confirmation Required**\n\nAre you sure you want to {action_verb}?\n\n{description}\n\n**Risk Level:** {risk_level.value.title()}"
            
        except Exception as e:
            logger.error(f"Failed to generate confirmation message: {e}")
            return f"⚠️ **Confirmation Required**\n\n{description}\n\nPlease confirm this action."
    
    async def _get_risk_assessment(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed risk assessment for the action"""
        try:
            assessment = {
                "action_type": action_type,
                "impact_level": "medium",
                "reversible": True,
                "affects_data": False,
                "affects_team": False,
                "affects_budget": False,
                "estimated_recovery_time": "immediate"
            }
            
            # Action-specific risk assessment
            if "delete" in action_type.lower():
                assessment.update({
                    "impact_level": "high",
                    "reversible": False,
                    "affects_data": True,
                    "estimated_recovery_time": "cannot recover"
                })
            
            if action_type == ActionType.DELETE_AGENT.value:
                assessment.update({
                    "affects_team": True,
                    "estimated_recovery_time": "15-30 minutes to recreate"
                })
            
            if "budget" in action_type.lower():
                assessment.update({
                    "affects_budget": True,
                    "impact_level": "high" if parameters.get("amount", 0) > 1000 else "medium"
                })
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate risk assessment: {e}")
            return {"error": str(e)}
    
    async def _suggest_alternatives(self, action_type: str, parameters: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest safer alternatives to the destructive action"""
        try:
            alternatives = []
            
            if action_type == ActionType.DELETE_AGENT.value:
                alternatives = [
                    {"action": "Deactivate agent instead", "description": "Keep agent data but mark as inactive"},
                    {"action": "Transfer tasks first", "description": "Reassign tasks to other team members"},
                    {"action": "Archive agent", "description": "Move to archived state for future reference"}
                ]
            
            elif action_type == ActionType.RESET_BUDGET.value:
                alternatives = [
                    {"action": "Adjust budget amount", "description": "Increase or decrease budget without resetting"},
                    {"action": "Create budget snapshot", "description": "Save current state before making changes"},
                    {"action": "Set new budget period", "description": "Start new budget cycle instead of reset"}
                ]
            
            elif "delete" in action_type.lower():
                alternatives = [
                    {"action": "Archive instead", "description": "Move items to archive for potential recovery"},
                    {"action": "Export data first", "description": "Create backup before deletion"},
                    {"action": "Selective deletion", "description": "Delete items one by one with review"}
                ]
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Failed to suggest alternatives: {e}")
            return []
    
    def _get_action_verb(self, action_type: str) -> str:
        """Get appropriate action verb for confirmation message"""
        verb_mapping = {
            ActionType.DELETE_AGENT.value: "remove this team member",
            ActionType.REMOVE_DELIVERABLE.value: "remove this deliverable", 
            ActionType.RESET_BUDGET.value: "reset the budget",
            ActionType.ARCHIVE_PROJECT.value: "archive this project",
            ActionType.DELETE_TASKS.value: "delete these tasks",
            ActionType.RESET_WORKSPACE.value: "reset the entire workspace",
            ActionType.BULK_DELETE.value: "delete multiple items"
        }
        
        return verb_mapping.get(action_type, "proceed with this action")
    
    def _risk_priority(self, risk_level: RiskLevel) -> int:
        """Get numeric priority for risk level comparison"""
        priorities = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return priorities.get(risk_level, 2)
    
    # Helper methods for risk assessment rules
    
    def _is_only_team_member(self, agent_id: str) -> bool:
        """Check if agent is the only team member"""
        try:
            result = self.supabase.table("agents")\
                .select("id", count="exact")\
                .eq("workspace_id", self.workspace_id)\
                .eq("status", "active")\
                .execute()
            
            return result.count == 1
            
        except Exception as e:
            logger.error(f"Failed to check team member count: {e}")
            return False
    
    def _get_budget_threshold(self) -> float:
        """Get budget threshold for high-risk classification"""
        try:
            # Get current workspace budget
            result = self.supabase.table("workspaces")\
                .select("max_budget")\
                .eq("id", self.workspace_id)\
                .execute()
            
            if result.data:
                max_budget = result.data[0].get("max_budget", 10000)
                return max_budget * 0.3  # 30% of total budget
            
            return 3000  # Default threshold
            
        except Exception as e:
            logger.error(f"Failed to get budget threshold: {e}")
            return 3000
    
    def _is_phase_regression(self, from_phase: str, to_phase: str) -> bool:
        """Check if phase change is a regression"""
        phase_order = [
            "planning", "initiation", "execution", "monitoring", "closure"
        ]
        
        try:
            from_index = phase_order.index(from_phase.lower())
            to_index = phase_order.index(to_phase.lower())
            return to_index < from_index
            
        except ValueError:
            return False
    
    def _removes_critical_skills(self, skills_to_remove: List[str]) -> bool:
        """Check if removing skills would eliminate critical capabilities"""
        critical_skills = [
            "project_management", "leadership", "quality_assurance",
            "architecture", "security", "compliance"
        ]
        
        return any(skill.lower() in [cs.lower() for cs in critical_skills] for skill in skills_to_remove)
    
    async def get_pending_confirmations(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all pending confirmations for workspace"""
        try:
            query = self.supabase.table("pending_confirmations")\
                .select("*")\
                .eq("status", "pending")\
                .gt("expires_at", datetime.now(timezone.utc).isoformat())
            
            # Filter by workspace through conversation_id or metadata
            result = query.execute()
            
            # Filter for this workspace
            workspace_confirmations = []
            for confirmation in result.data or []:
                metadata = confirmation.get("metadata", {})
                if metadata.get("workspace_id") == self.workspace_id:
                    workspace_confirmations.append(confirmation)
            
            return workspace_confirmations
            
        except Exception as e:
            logger.error(f"Failed to get pending confirmations: {e}")
            return []
    
    async def cleanup_expired_confirmations(self) -> int:
        """Clean up expired confirmations and return count cleaned"""
        try:
            # Mark expired confirmations
            result = self.supabase.table("pending_confirmations")\
                .update({"status": "expired"})\
                .eq("status", "pending")\
                .lt("expires_at", datetime.now(timezone.utc).isoformat())\
                .execute()
            
            count = len(result.data or [])
            logger.info(f"Cleaned up {count} expired confirmations")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired confirmations: {e}")
            return 0