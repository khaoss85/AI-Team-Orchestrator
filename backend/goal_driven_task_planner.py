# backend/goal_driven_task_planner.py

import json
import logging
import asyncio
import os
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
    🎯 STEP 2: Goal-Driven Task Planner - AI-DRIVEN & UNIVERSAL
    
    Sostituisce la logica analitica del PM con task generation 
    guidata da target numerici dei workspace_goals.
    
    Invece di creare "Market analysis", crea "Collect 50 contacts".
    """
    
    def __init__(self):
        self.task_templates = self._load_task_templates()
        
        # 🤖 Initialize AI for universal task generation
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ AI Task Planner initialized with OpenAI")
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for AI task generation")
        else:
            self.ai_available = False
        
    def _load_task_templates(self) -> Dict[str, Dict]:
        """🤖 DEPRECATED: Templates replaced with AI-driven generation"""
        # All templates removed - using AI generation instead
        return {}
    
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
    
    async def plan_tasks_for_goal(
        self, 
        workspace_goal: Dict[str, Any], 
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """
        🚀 PUBLIC METHOD: Plan tasks for a specific goal
        
        This is called by the immediate goal analysis trigger to start the team.
        """
        try:
            # Convert dict to WorkspaceGoal object
            goal = WorkspaceGoal(**workspace_goal)
            
            # Generate tasks using the internal method
            tasks = await self._generate_tasks_for_goal(goal)
            
            # Create tasks in database and trigger execution
            created_tasks = []
            for task_data in tasks:
                # Add workspace_id and execution metadata
                task_data.update({
                    "workspace_id": workspace_id,
                    "status": TaskStatus.PENDING.value,
                    "created_at": datetime.now().isoformat(),
                    "is_goal_driven": True,
                    "auto_generated": True
                })
                
                # Insert into database
                response = supabase.table("tasks").insert(task_data).execute()
                if response.data:
                    created_tasks.extend(response.data)
                    logger.info(f"✅ Created task: {task_data['name']}")
            
            logger.info(f"🎯 Successfully created {len(created_tasks)} tasks for goal {goal.metric_type}")
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error planning tasks for goal: {e}")
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
        
        logger.info(f"🤖 Generating AI-driven tasks for {goal.metric_type} (gap: {gap} {goal.unit})")
        
        # 🎯 STRATEGIC: Create concrete, actionable tasks
        tasks = []
        
        # 🤖 UNIVERSAL AI-DRIVEN TASK GENERATION
        # Get workspace context for better task generation
        workspace_context = await self._get_workspace_context(goal.workspace_id)
        
        # Use AI for ALL goal types - no more hardcoded templates
        tasks.extend(await self._generate_ai_driven_tasks(goal, gap, workspace_context))
        
        return tasks
    
    async def _get_workspace_context(self, workspace_id: UUID) -> Dict[str, Any]:
        """
        🎯 Get workspace context for better AI task generation
        """
        try:
            # Get workspace info
            response = supabase.table("workspaces").select("*").eq(
                "id", str(workspace_id)
            ).single().execute()
            
            workspace_data = response.data
            
            return {
                "name": workspace_data.get("name", "Project"),
                "description": workspace_data.get("goal", "Universal business project"),
                "industry": workspace_data.get("industry", "General business"),
                "project_type": workspace_data.get("project_type", "Universal")
            }
            
        except Exception as e:
            logger.warning(f"Could not get workspace context: {e}")
            return {
                "name": "Universal Project",
                "description": "Universal business project",
                "industry": "General business",
                "project_type": "Universal"
            }
    
    async def _generate_ai_driven_tasks(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN UNIVERSAL TASK GENERATION
        Sostituisce tutti i template hardcoded con AI che comprende il contesto
        """
        if not self.ai_available:
            return await self._fallback_generic_tasks(goal, gap)
        
        try:
            prompt = f"""You are a universal project management AI. Generate SPECIFIC, ACTIONABLE tasks to achieve this goal.

GOAL CONTEXT:
- Goal: {goal.description}
- Metric Type: {goal.metric_type}
- Target: {goal.target_value} {goal.unit}
- Gap to fill: {gap} {goal.unit}
- Workspace: {workspace_context.get('name', 'Unknown')}
- Industry context: {workspace_context.get('description', 'Universal business')}

IMPORTANT INSTRUCTIONS:
1. Generate tasks that are SPECIFIC and ACTIONABLE (not generic like "research market")
2. Make tasks appropriate for ANY industry (not just B2B/SaaS/marketing)
3. Include concrete deliverables and success criteria
4. Consider the specific metric type and gap to fill
5. Tasks should be granular enough for someone to execute immediately

Generate 1-3 specific tasks in this JSON format:
{{
    "tasks": [
        {{
            "name": "Specific task name that clearly states what to do",
            "description": "Detailed description of exactly what needs to be accomplished",
            "type": "task_type_based_on_goal",
            "priority": 1-5,
            "contribution_expected": number,
            "success_criteria": [
                "Specific criterion 1",
                "Specific criterion 2"
            ],
            "estimated_duration_hours": number,
            "required_skills": ["skill1", "skill2"],
            "deliverable_type": "what_will_be_produced"
        }}
    ]
}}

Examples of GOOD vs BAD tasks:
❌ BAD: "Research the market" (too vague)
✅ GOOD: "Create database of 50 potential customers with contact details"

❌ BAD: "Improve email marketing" (not specific)  
✅ GOOD: "Write 3 email templates for customer onboarding sequence"

❌ BAD: "Analyze competition" (not actionable)
✅ GOOD: "Create comparison chart of top 5 competitors' pricing models"

Focus on the specific gap ({gap} {goal.unit}) and make tasks that directly contribute to closing it."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert project manager who creates specific, actionable tasks for any industry."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            tasks = []
            
            for task_data in result.get("tasks", []):
                task = {
                    "goal_id": str(goal.id),
                    "metric_type": goal.metric_type if isinstance(goal.metric_type, str) else goal.metric_type.value,
                    "name": task_data["name"],
                    "description": task_data["description"],
                    "type": task_data.get("type", "goal_driven"),
                    "priority": task_data.get("priority", 3),
                    "contribution_expected": task_data.get("contribution_expected", gap / len(result["tasks"])),
                    "success_criteria": task_data.get("success_criteria", []),
                    "estimated_duration_hours": task_data.get("estimated_duration_hours", 4),
                    "required_skills": task_data.get("required_skills", []),
                    "deliverable_type": task_data.get("deliverable_type", "project_output"),
                    "numerical_target": {
                        "metric": goal.metric_type.value,
                        "target": task_data.get("contribution_expected", gap / len(result["tasks"])),
                        "unit": goal.unit,
                        "validation_method": "manual_verification"
                    }
                }
                tasks.append(task)
                
            logger.info(f"🤖 AI generated {len(tasks)} universal tasks for {goal.metric_type} goal")
            return tasks
            
        except Exception as e:
            logger.error(f"AI task generation failed: {e}")
            return await self._fallback_generic_tasks(goal, gap)
    
    async def _fallback_generic_tasks(self, goal: WorkspaceGoal, gap: float) -> List[Dict[str, Any]]:
        """Fallback quando AI non è disponibile"""
        return [{
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "name": f"Achieve {gap} {goal.unit}",
            "description": f"Work towards achieving {gap} {goal.unit} for goal: {goal.description}",
            "type": "generic_goal_task",
            "priority": 3,
            "contribution_expected": gap,
            "success_criteria": [f"Deliver {gap} {goal.unit}"],
            "estimated_duration_hours": 8,
            "required_skills": ["general_execution"],
            "deliverable_type": "goal_output"
        }]
    
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
            workspace_id = str(goal.workspace_id)
            
            # Calculate corrective action needed
            remaining_gap = goal.remaining_value
            
            # 🎯 INTELLIGENT AGENT ROLE SELECTION
            # Get available agents in workspace to assign to existing roles only
            selected_agent_role = await self._select_best_available_agent_role(
                workspace_id=workspace_id,
                task_type="corrective_action",
                required_skills=["rapid_execution", "goal_achievement"]
            )
            
            # Skip task creation if no agents available
            if selected_agent_role is None:
                logger.warning(f"⚠️ No agents available in workspace {workspace_id} - skipping corrective task creation")
                return {}
            
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
                    "role": str(selected_agent_role["role"]) if hasattr(selected_agent_role["role"], 'value') else selected_agent_role["role"],
                    "agent_id": selected_agent_role.get("agent_id"),  # Direct assignment if possible
                    "skills": ["rapid_execution", "goal_achievement"],
                    "seniority": selected_agent_role.get("seniority", "expert"),
                    "selection_strategy": selected_agent_role.get("strategy", "availability_based")
                }
            }
            
            role_str = str(selected_agent_role["role"]) if hasattr(selected_agent_role["role"], 'value') else selected_agent_role["role"]
            logger.warning(
                f"🚨 Created CRITICAL corrective task for goal {goal_id}: {corrective_task['name']} "
                f"-> Assigned to role '{role_str}' "
                f"({selected_agent_role.get('strategy', 'unknown')} strategy)"
            )
            return corrective_task
            
        except Exception as e:
            logger.error(f"Error creating corrective task: {e}")
            return {}
    
    async def _select_best_available_agent_role(
        self,
        workspace_id: str,
        task_type: str = "corrective_action",
        required_skills: List[str] = None
    ) -> Dict[str, Any]:
        """
        🎯 INTELLIGENT AGENT ROLE SELECTION
        
        Selects the best available agent role from existing agents in workspace.
        Ensures corrective tasks are only assigned to agents that actually exist.
        """
        try:
            # Get all available agents in workspace
            response = supabase.table("agents").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", "active"
            ).execute()
            
            available_agents = response.data or []
            
            if not available_agents:
                logger.warning(f"⚠️ No active agents found in workspace {workspace_id} - skipping task creation")
                # Return None to indicate no task should be created
                return None
            
            logger.info(f"📋 Found {len(available_agents)} active agents in workspace {workspace_id}")
            
            # 🎯 STRATEGY 1: Look for high-seniority agents first
            expert_agents = [
                agent for agent in available_agents
                if agent.get("seniority", "").lower() in ["expert", "senior"]
            ]
            
            if expert_agents:
                selected_agent = expert_agents[0]
                logger.info(f"✅ Selected expert/senior agent: {selected_agent.get('name')} ({selected_agent.get('role')})")
                return {
                    "role": selected_agent["role"],
                    "agent_id": selected_agent["id"],
                    "seniority": selected_agent.get("seniority", "expert"),
                    "strategy": "seniority_based",
                    "agent_name": selected_agent.get("name")
                }
            
            # 🎯 STRATEGY 2: Look for management/coordination roles
            manager_keywords = ["manager", "coordinator", "director", "lead", "pm", "project"]
            manager_agents = [
                agent for agent in available_agents
                if any(keyword in agent.get("role", "").lower() for keyword in manager_keywords)
            ]
            
            if manager_agents:
                selected_agent = manager_agents[0]
                logger.info(f"✅ Selected manager agent: {selected_agent.get('name')} ({selected_agent.get('role')})")
                return {
                    "role": selected_agent["role"],
                    "agent_id": selected_agent["id"],
                    "seniority": selected_agent.get("seniority", "senior"),
                    "strategy": "management_role_based",
                    "agent_name": selected_agent.get("name")
                }
            
            # 🎯 STRATEGY 3: Look for specialist roles that can handle diverse tasks
            specialist_keywords = ["specialist", "engineer", "developer", "analyst", "consultant"]
            specialist_agents = [
                agent for agent in available_agents
                if any(keyword in agent.get("role", "").lower() for keyword in specialist_keywords)
            ]
            
            if specialist_agents:
                selected_agent = specialist_agents[0]
                logger.info(f"✅ Selected specialist agent: {selected_agent.get('name')} ({selected_agent.get('role')})")
                return {
                    "role": selected_agent["role"],
                    "agent_id": selected_agent["id"],
                    "seniority": selected_agent.get("seniority", "junior"),
                    "strategy": "specialist_role_based",
                    "agent_name": selected_agent.get("name")
                }
            
            # 🎯 STRATEGY 4: Use any available agent as last resort
            selected_agent = available_agents[0]
            logger.warning(f"⚠️ Using any available agent as fallback: {selected_agent.get('name')} ({selected_agent.get('role')})")
            return {
                "role": selected_agent["role"],
                "agent_id": selected_agent["id"],
                "seniority": selected_agent.get("seniority", "junior"),
                "strategy": "any_available_fallback",
                "agent_name": selected_agent.get("name")
            }
            
        except Exception as e:
            logger.error(f"Error selecting agent role for corrective task: {e}")
            # Return safe fallback that executor can handle
            return {
                "role": "task_assignment_failed",
                "strategy": "error_fallback",
                "error": str(e)
            }
    
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