# backend/goal_driven_task_planner.py

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models import (
    WorkspaceGoal, GoalMetricType, GoalStatus, TaskStatus,
    WorkspaceGoalProgress
)
from database import supabase

logger = logging.getLogger(__name__)

class GoalDrivenTaskPlanner:
    """
    🎯 STEP 2: Goal-Driven Task Planner
    
    Sostituisce la logica analitica del PM con task generation 
    guidata da target numerici dei workspace_goals.
    
    Invece di creare "Market analysis", crea "Collect 50 contacts".
    """
    
    def __init__(self):
        self.task_templates = self._load_task_templates()
        
    def _load_task_templates(self) -> Dict[str, Dict]:
        """Carica template per task concreti per ogni metric type"""
        return {
            GoalMetricType.CONTACTS: {
                "base_template": {
                    "name": "Collect {gap} ICP contacts",
                    "description": "Find and collect {gap} high-quality ICP contacts with complete profile information (name, email, title, company)",
                    "success_criteria": [
                        "Find {gap} real contacts matching ICP criteria",
                        "Verify all contacts have valid email addresses", 
                        "Include complete profile data (name, title, company)",
                        "No fake, placeholder, or example contacts",
                        "Export ready-to-use contact database"
                    ],
                    "type": "contact_collection",
                    "priority": 1
                },
                "research_sources": [
                    "LinkedIn advanced search",
                    "Apollo.io database",
                    "Company websites and team pages",
                    "Industry conferences and events",
                    "Professional associations"
                ],
                "validation_criteria": {
                    "email_format": "@company.domain format",
                    "completeness": "Name, title, company required",
                    "quality": "No placeholder or example data"
                }
            },
            
            GoalMetricType.EMAIL_SEQUENCES: {
                "base_template": {
                    "name": "Create {gap} B2B email sequences",
                    "description": "Develop {gap} high-converting email sequences for B2B outreach with specific subject lines, body content, and CTAs",
                    "success_criteria": [
                        "Create {gap} complete email sequences",
                        "Include specific subject lines and body text",
                        "Add clear call-to-action for each email",
                        "Target ≥30% open rate, ≥10% click rate",
                        "Ready for immediate deployment in email platform"
                    ],
                    "type": "email_sequence_creation",
                    "priority": 2
                },
                "sequence_components": [
                    "Initial outreach email",
                    "Follow-up sequence (2-3 emails)",
                    "Re-engagement campaign",
                    "Meeting booking flow"
                ],
                "optimization_targets": {
                    "open_rate": "≥30%",
                    "click_rate": "≥10%",
                    "response_rate": "≥5%"
                }
            },
            
            GoalMetricType.CONTENT_PIECES: {
                "base_template": {
                    "name": "Create {gap} content pieces",
                    "description": "Develop {gap} ready-to-publish content pieces with complete text, visuals, and publishing schedule",
                    "success_criteria": [
                        "Create {gap} complete content pieces",
                        "Include full text and captions",
                        "Add relevant hashtags and CTAs",
                        "Provide publishing schedule",
                        "Ready for immediate publication"
                    ],
                    "type": "content_creation",
                    "priority": 3
                }
            },
            
            GoalMetricType.CAMPAIGNS: {
                "base_template": {
                    "name": "Launch {gap} marketing campaigns",
                    "description": "Design and launch {gap} complete marketing campaigns with assets, targeting, and tracking setup",
                    "success_criteria": [
                        "Design {gap} campaign strategies",
                        "Create all required campaign assets",
                        "Set up targeting and budget allocation",
                        "Implement tracking and analytics",
                        "Ready for immediate launch"
                    ],
                    "type": "campaign_creation",
                    "priority": 2
                }
            }
        }
    
    async def generate_tasks_for_unmet_goals(
        self, 
        workspace_id: UUID,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        🎯 CORE METHOD: Genera task concreti per goal non raggiunti
        
        Sostituisce completamente la logica analitica del PM.
        """
        try:
            # 1. Get unmet goals for workspace
            unmet_goals = await self._get_unmet_goals(workspace_id)
            
            if not unmet_goals:
                logger.info(f"✅ All goals met for workspace {workspace_id}")
                return []
            
            # 2. Generate concrete tasks for each unmet goal
            generated_tasks = []
            for goal in unmet_goals:
                tasks = await self._generate_tasks_for_goal(goal, context)
                generated_tasks.extend(tasks)
            
            logger.info(f"🎯 Generated {len(generated_tasks)} goal-driven tasks for workspace {workspace_id}")
            return generated_tasks
            
        except Exception as e:
            logger.error(f"Error generating goal-driven tasks: {e}")
            return []
    
    async def _get_unmet_goals(self, workspace_id: UUID) -> List[WorkspaceGoal]:
        """Recupera goal attivi non completati per il workspace"""
        try:
            response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", str(workspace_id)
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            goals = []
            for goal_data in response.data:
                # Convert to WorkspaceGoal model
                goal = WorkspaceGoal(**goal_data)
                
                # Only include goals that need work
                if not goal.is_completed and goal.remaining_value > 0:
                    goals.append(goal)
            
            logger.info(f"📊 Found {len(goals)} unmet goals for workspace {workspace_id}")
            return goals
            
        except Exception as e:
            logger.error(f"Error fetching unmet goals: {e}")
            return []
    
    async def _generate_tasks_for_goal(
        self, 
        goal: WorkspaceGoal, 
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Genera task concreti per un goal specifico"""
        
        gap = goal.remaining_value
        if gap <= 0:
            return []
        
        # Get template for this metric type
        template = self.task_templates.get(goal.metric_type)
        if not template:
            logger.warning(f"No template found for metric type: {goal.metric_type}")
            return []
        
        # 🎯 STRATEGIC: Create concrete, actionable tasks
        tasks = []
        
        if goal.metric_type == GoalMetricType.CONTACTS:
            tasks.extend(await self._generate_contact_collection_tasks(goal, gap, template))
        elif goal.metric_type == GoalMetricType.EMAIL_SEQUENCES:
            tasks.extend(await self._generate_email_sequence_tasks(goal, gap, template))
        elif goal.metric_type == GoalMetricType.CONTENT_PIECES:
            tasks.extend(await self._generate_content_creation_tasks(goal, gap, template))
        elif goal.metric_type == GoalMetricType.CAMPAIGNS:
            tasks.extend(await self._generate_campaign_tasks(goal, gap, template))
        else:
            # Fallback for other metric types
            tasks.extend(await self._generate_generic_tasks(goal, gap, template))
        
        return tasks
    
    async def _generate_contact_collection_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        template: Dict
    ) -> List[Dict[str, Any]]:
        """Genera task specifici per raccolta contatti"""
        
        tasks = []
        base_template = template["base_template"]
        
        # 🎯 CONCRETE TASK: Direct contact collection
        main_task = {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": base_template["name"].format(gap=int(gap)),
            "description": base_template["description"].format(gap=int(gap)),
            "type": base_template["type"],
            "priority": base_template["priority"],
            "contribution_expected": gap,
            "success_criteria": [
                criteria.format(gap=int(gap)) for criteria in base_template["success_criteria"]
            ],
            "numerical_target": {
                "metric": "contacts_collected",
                "target": gap,
                "unit": "contacts",
                "validation_method": "count_real_contacts_with_emails"
            },
            "research_sources": template["research_sources"],
            "validation_criteria": template["validation_criteria"],
            "estimated_duration_hours": max(2, gap * 0.5),  # 30 min per contact
            "agent_requirements": {
                "role": "contact_researcher",
                "skills": ["web_research", "data_extraction", "email_verification"],
                "seniority": "senior"
            },
            "completion_requirements": {
                "must_have_real_emails": True,
                "no_placeholder_data": True,
                "complete_profiles": True,
                "export_format": "structured_json"
            }
        }
        
        tasks.append(main_task)
        
        # 🎯 ADD VALIDATION TASK if gap is large
        if gap >= 10:
            validation_task = {
                "goal_id": str(goal.id),
                "metric_type": goal.metric_type.value,
                "name": f"Validate and clean {int(gap)} collected contacts",
                "description": f"Verify email validity and profile completeness for {int(gap)} contacts",
                "type": "contact_validation",
                "priority": 2,
                "contribution_expected": 0,  # Quality improvement, not quantity
                "depends_on": [main_task["name"]],
                "success_criteria": [
                    "Verify all email addresses are valid format",
                    "Remove any duplicate contacts",
                    "Ensure complete profile information",
                    "Export final validated contact database"
                ],
                "agent_requirements": {
                    "role": "data_validator",
                    "skills": ["data_cleaning", "email_verification"],
                    "seniority": "junior"
                }
            }
            tasks.append(validation_task)
        
        return tasks
    
    async def _generate_email_sequence_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        template: Dict
    ) -> List[Dict[str, Any]]:
        """Genera task per creazione sequenze email"""
        
        tasks = []
        base_template = template["base_template"]
        
        main_task = {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": base_template["name"].format(gap=int(gap)),
            "description": base_template["description"].format(gap=int(gap)),
            "type": base_template["type"],
            "priority": base_template["priority"],
            "contribution_expected": gap,
            "success_criteria": [
                criteria.format(gap=int(gap)) for criteria in base_template["success_criteria"]
            ],
            "numerical_target": {
                "metric": "email_sequences_created",
                "target": gap,
                "unit": "sequences",
                "validation_method": "count_complete_sequences"
            },
            "sequence_components": template["sequence_components"],
            "optimization_targets": template["optimization_targets"],
            "estimated_duration_hours": gap * 2,  # 2 hours per sequence
            "agent_requirements": {
                "role": "email_copywriter",
                "skills": ["copywriting", "b2b_marketing", "conversion_optimization"],
                "seniority": "senior"
            },
            "completion_requirements": {
                "complete_subject_lines": True,
                "full_email_body": True,
                "clear_ctas": True,
                "ready_for_deployment": True
            }
        }
        
        tasks.append(main_task)
        return tasks
    
    async def _generate_content_creation_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        template: Dict
    ) -> List[Dict[str, Any]]:
        """Genera task per creazione contenuti"""
        
        base_template = template["base_template"]
        
        task = {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": base_template["name"].format(gap=int(gap)),
            "description": base_template["description"].format(gap=int(gap)),
            "type": base_template["type"],
            "priority": base_template["priority"],
            "contribution_expected": gap,
            "success_criteria": [
                criteria.format(gap=int(gap)) for criteria in base_template["success_criteria"]
            ],
            "numerical_target": {
                "metric": "content_pieces_created",
                "target": gap,
                "unit": "pieces",
                "validation_method": "count_complete_content"
            },
            "estimated_duration_hours": gap * 1.5,  # 1.5 hours per content piece
            "agent_requirements": {
                "role": "content_creator",
                "skills": ["content_writing", "social_media", "visual_design"],
                "seniority": "senior"
            }
        }
        
        return [task]
    
    async def _generate_campaign_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        template: Dict
    ) -> List[Dict[str, Any]]:
        """Genera task per creazione campagne"""
        
        base_template = template["base_template"]
        
        task = {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": base_template["name"].format(gap=int(gap)),
            "description": base_template["description"].format(gap=int(gap)),
            "type": base_template["type"],
            "priority": base_template["priority"],
            "contribution_expected": gap,
            "success_criteria": [
                criteria.format(gap=int(gap)) for criteria in base_template["success_criteria"]
            ],
            "numerical_target": {
                "metric": "campaigns_created",
                "target": gap,
                "unit": "campaigns",
                "validation_method": "count_launched_campaigns"
            },
            "estimated_duration_hours": gap * 4,  # 4 hours per campaign
            "agent_requirements": {
                "role": "marketing_manager",
                "skills": ["campaign_strategy", "digital_marketing", "analytics"],
                "seniority": "expert"
            }
        }
        
        return [task]
    
    async def _generate_generic_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        template: Dict
    ) -> List[Dict[str, Any]]:
        """Fallback per metric types non specificamente supportati"""
        
        base_template = template.get("base_template", {})
        
        task = {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": f"Achieve {int(gap)} {goal.unit} for {goal.metric_type.value}",
            "description": f"Work towards achieving {int(gap)} {goal.unit} to meet the {goal.metric_type.value} goal",
            "type": "goal_achievement",
            "priority": 3,
            "contribution_expected": gap,
            "numerical_target": {
                "metric": goal.metric_type.value,
                "target": gap,
                "unit": goal.unit
            },
            "estimated_duration_hours": gap * 1,
            "agent_requirements": {
                "role": "generalist",
                "skills": ["problem_solving", "research"],
                "seniority": "senior"
            }
        }
        
        return [task]
    
    async def create_corrective_task(
        self, 
        goal_id: UUID, 
        gap_percentage: float,
        failure_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        🎯 STEP 3 INTEGRATION: Crea task correttivo quando Goal Validator rileva gap critico
        
        Chiamato da memory-driven course correction system.
        """
        try:
            # Get goal details
            response = supabase.table("workspace_goals").select("*").eq(
                "id", str(goal_id)
            ).single().execute()
            
            goal = WorkspaceGoal(**response.data)
            
            # Calculate corrective action needed
            remaining_gap = goal.remaining_value
            
            # 🎯 CREATE URGENT CORRECTIVE TASK
            corrective_task = {
                "goal_id": str(goal.id),
                "metric_type": goal.metric_type.value,
                "name": f"🚨 URGENT: Close {gap_percentage:.1f}% gap in {goal.metric_type.value}",
                "description": f"Critical corrective action required. Current gap: {remaining_gap} {goal.unit}. Must achieve target within 24 hours.",
                "type": "corrective_action",
                "priority": 1,  # Highest priority
                "contribution_expected": remaining_gap,
                "is_corrective": True,
                "urgency": "critical",
                "deadline_hours": 24,
                "failure_context": failure_context,
                "success_criteria": [
                    f"Close the {remaining_gap} {goal.unit} gap immediately",
                    "Use learnings from previous failures",
                    "Focus on concrete, measurable deliverables",
                    "No theoretical or analytical outputs"
                ],
                "numerical_target": {
                    "metric": goal.metric_type.value,
                    "target": remaining_gap,
                    "unit": goal.unit,
                    "validation_method": "immediate_numerical_verification"
                },
                "agent_requirements": {
                    "role": "expert_specialist",
                    "skills": ["rapid_execution", "goal_achievement"],
                    "seniority": "expert"
                }
            }
            
            logger.warning(f"🚨 Created CRITICAL corrective task for goal {goal_id}: {corrective_task['name']}")
            return corrective_task
            
        except Exception as e:
            logger.error(f"Error creating corrective task: {e}")
            return {}
    
    async def update_goal_progress(
        self, 
        goal_id: UUID, 
        progress_increment: float,
        task_context: Optional[Dict] = None
    ) -> bool:
        """
        Aggiorna il progresso di un goal quando un task viene completato
        """
        try:
            # Get current goal
            response = supabase.table("workspace_goals").select("*").eq(
                "id", str(goal_id)
            ).single().execute()
            
            goal_data = response.data
            current_value = goal_data["current_value"]
            target_value = goal_data["target_value"]
            
            # Calculate new value
            new_value = min(current_value + progress_increment, target_value)
            
            # Update goal
            update_data = {
                "current_value": new_value,
                "updated_at": datetime.now().isoformat()
            }
            
            # Mark as completed if target reached
            if new_value >= target_value:
                update_data["status"] = GoalStatus.COMPLETED.value
                update_data["completed_at"] = datetime.now().isoformat()
            
            supabase.table("workspace_goals").update(update_data).eq(
                "id", str(goal_id)
            ).execute()
            
            logger.info(f"✅ Updated goal {goal_id} progress: {current_value} → {new_value} / {target_value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            return False

# Singleton instance
goal_driven_task_planner = GoalDrivenTaskPlanner()