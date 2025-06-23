# backend/goal_driven_task_planner.py

import json
import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models import (
    WorkspaceGoal, GoalStatus, TaskStatus,
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
            
            # 🛡️ DUPLICATE PREVENTION: Check if tasks already exist for this goal
            existing_tasks_response = supabase.table("tasks").select("id, name").eq(
                "workspace_id", workspace_id
            ).eq(
                "goal_id", str(goal.id)
            ).execute()
            
            existing_tasks = existing_tasks_response.data or []
            if existing_tasks:
                logger.info(f"🔄 Goal {goal.metric_type} already has {len(existing_tasks)} tasks - skipping duplicate creation")
                return existing_tasks
            
            # Generate tasks using the internal method
            tasks = await self._generate_tasks_for_goal(goal)
            
            # Get available agents for task assignment (agents change to "available" after start_team)
            agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).eq("status", "available").execute()
            available_agents = agents_response.data or []
            
            if not available_agents:
                logger.warning(f"⚠️ No available agents found for workspace {workspace_id} - tasks will be created unassigned")
            
            # Create tasks in database and trigger execution
            created_tasks = []
            agent_index = 0  # Round-robin assignment
            
            for task_data in tasks:
                # Assign agent if available (round-robin)
                assigned_agent_id = None
                assigned_agent_role = None
                
                if available_agents:
                    assigned_agent = available_agents[agent_index % len(available_agents)]
                    assigned_agent_id = assigned_agent["id"]
                    assigned_agent_role = assigned_agent.get("role")
                    agent_index += 1
                    logger.info(f"🎯 Assigning task '{task_data['name']}' to agent {assigned_agent.get('name')} ({assigned_agent_role})")
                
                # Add workspace_id and execution metadata
                task_data.update({
                    "workspace_id": workspace_id,
                    "agent_id": assigned_agent_id,  # 🔧 FIX: Assign agent_id to prevent orphaned tasks
                    "assigned_to_role": assigned_agent_role,
                    "status": "pending",  # Direct string instead of enum.value
                    "created_at": datetime.now().isoformat(),
                    "context_data": {
                        **(task_data.get("context_data", {})),
                        "is_goal_driven": True,
                        "auto_generated": True,
                        "generated_by": "goal_driven_task_planner",
                        "goal_analysis_timestamp": datetime.now().isoformat(),
                        "assigned_agent_name": assigned_agent.get('name') if available_agents else None
                    }
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
                # Store all metadata in context_data to avoid database schema issues
                context_data = {
                    "is_goal_driven": True,
                    "auto_generated": True,
                    "task_type": task_data.get("type", "goal_driven"),
                    "deliverable_type": task_data.get("deliverable_type", "project_output"),
                    "estimated_duration_hours": task_data.get("estimated_duration_hours", 4),
                    "required_skills": task_data.get("required_skills", []),
                    "success_criteria": task_data.get("success_criteria", []),
                    "numerical_target": {
                        "metric": str(goal.metric_type),
                        "target": task_data.get("contribution_expected", gap / len(result["tasks"])),
                        "unit": goal.unit,
                        "validation_method": "manual_verification"
                    }
                }
                
                # 🌍 PILLAR 2 & 3 COMPLIANCE: AI-driven metric type classification (universal)
                compatible_metric_type = await self._classify_metric_type_ai(str(goal.metric_type))
                
                task = {
                    "goal_id": str(goal.id),
                    "metric_type": compatible_metric_type,
                    "name": task_data["name"],
                    "description": task_data["description"],
                    "priority": self._convert_numeric_priority(task_data.get("priority", 3)),
                    "contribution_expected": task_data.get("contribution_expected", gap / len(result["tasks"])),
                    "context_data": {
                        **context_data,
                        "original_metric_type": str(goal.metric_type)  # Preserve original for future use
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
        context_data = {
            "is_goal_driven": True,
            "auto_generated": True,
            "task_type": "generic_goal_task",
            "deliverable_type": "goal_output",
            "estimated_duration_hours": 8,
            "required_skills": ["general_execution"],
            "success_criteria": [f"Deliver {gap} {goal.unit}"],
            "numerical_target": {
                "metric": str(goal.metric_type),
                "target": gap,
                "unit": goal.unit,
                "validation_method": "manual_verification"
            }
        }
        
        # 🌍 PILLAR 2 & 3 COMPLIANCE: AI-driven metric type classification (universal)
        compatible_metric_type = await self._classify_metric_type_ai(str(goal.metric_type))
        
        return [{
            "goal_id": str(goal.id),
            "metric_type": compatible_metric_type,
            "name": f"Achieve {gap} {goal.unit}",
            "description": f"Work towards achieving {gap} {goal.unit} for goal: {goal.description}",
            "priority": "low",
            "contribution_expected": gap,
            "context_data": {
                **context_data,
                "original_metric_type": str(goal.metric_type)
            }
        }]
    
    def _convert_numeric_priority(self, priority: Union[int, str]) -> str:
        """
        Convert numeric priority to string priority for Pydantic validation
        """
        if isinstance(priority, str) and priority in ["low", "medium", "high"]:
            return priority
            
        # Convert numeric to string
        priority_map = {
            1: "high",
            2: "medium", 
            3: "low",
            4: "low",
            5: "low"
        }
        
        if isinstance(priority, int):
            return priority_map.get(priority, "low")
        elif isinstance(priority, str) and priority.isdigit():
            return priority_map.get(int(priority), "low")
        else:
            return "low"  # Default fallback
    
    async def _classify_metric_type_ai(self, universal_metric_type: str) -> str:
        """
        🌍 PILLAR 2 & 3 COMPLIANCE: Resilient Universal AI Classification
        
        Multi-layered classification system:
        1. AI-driven semantic understanding (preferred)
        2. Pattern-based semantic analysis (fallback) 
        3. Universal default (ultimate fallback)
        
        Designed to work across all business domains without hard-coding
        """
        if not universal_metric_type:
            return self._get_semantic_fallback("")
        
        # 🤖 LAYER 1: AI-Driven Classification (Preferred)
        ai_result = await self._attempt_ai_classification(universal_metric_type)
        if ai_result:
            return ai_result
        
        # 🧠 LAYER 2: Semantic Pattern Analysis (Intelligent Fallback)
        semantic_result = self._classify_by_semantic_patterns(universal_metric_type)
        if semantic_result != "quantified_outputs":  # Only use if we found a specific pattern
            logger.info(f"🧠 Semantic classification: '{universal_metric_type}' → '{semantic_result}'")
            return semantic_result
        
        # 🌍 LAYER 3: Universal Default (Ultimate Fallback)
        fallback_result = self._get_semantic_fallback(universal_metric_type)
        logger.info(f"🌍 Universal fallback: '{universal_metric_type}' → '{fallback_result}'")
        return fallback_result
    
    async def _attempt_ai_classification(self, metric_type: str) -> Optional[str]:
        """🤖 Attempt AI classification with robust error handling"""
        try:
            from utils.model_settings_factory import create_model_settings
            import openai
            
            # 🔧 PILLAR 3: Robust model settings with guaranteed attributes
            model_settings = create_model_settings(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=50
            )
            
            # Verify we have required attributes
            if not hasattr(model_settings, 'model'):
                logger.warning(f"🤖 ModelSettings missing 'model' attribute, skipping AI classification")
                return None
            
            # Create OpenAI client
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            if not client.api_key:
                logger.warning(f"🤖 No OpenAI API key available, skipping AI classification")
                return None
            
            # 🌍 PILLAR 2: Universal classification prompt (domain-agnostic)
            classification_prompt = f"""Classify this metric type into ONE category:

Metric: "{metric_type}"

Categories:
- "quantified_outputs" (counts, lists, deliverables)
- "quality_measures" (scores, ratings, percentages)  
- "time_based_metrics" (deadlines, durations)
- "engagement_metrics" (interactions, responses)
- "completion_metrics" (progress, milestones)

Return ONLY the category name."""
            
            # 🔧 Use synchronous call (not async) for better reliability
            response = client.chat.completions.create(
                model=model_settings.model,
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=model_settings.max_tokens,
                temperature=model_settings.temperature
            )
            
            ai_classification = response.choices[0].message.content.strip().lower()
            
            # Validate response
            valid_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                              "engagement_metrics", "completion_metrics"]
            
            if ai_classification in valid_categories:
                logger.info(f"🤖 AI classified '{metric_type}' → '{ai_classification}'")
                return ai_classification
            else:
                logger.warning(f"🤖 AI returned invalid category '{ai_classification}'")
                return None
                
        except Exception as e:
            logger.warning(f"🤖 AI classification failed for '{metric_type}': {e}")
            return None
    
    def _classify_by_semantic_patterns(self, metric_type: str) -> str:
        """
        🧠 PILLAR 2: Semantic pattern-based classification (universal, no domain bias)
        Uses linguistic patterns rather than business-specific keywords
        """
        metric_lower = metric_type.lower()
        
        # 📊 Quality/Performance indicators (scores, rates, percentages)
        quality_patterns = ["score", "rate", "quality", "performance", "accuracy", 
                          "efficiency", "satisfaction", "rating", "index"]
        if any(pattern in metric_lower for pattern in quality_patterns):
            return "quality_measures"
        
        # ⏰ Time-based indicators
        time_patterns = ["time", "day", "week", "month", "duration", "deadline", 
                        "timeline", "schedule", "period"]
        if any(pattern in metric_lower for pattern in time_patterns):
            return "time_based_metrics"
        
        # 🤝 Engagement indicators (interactions, responses)
        engagement_patterns = ["engagement", "interaction", "response", "participation",
                             "activity", "usage", "adoption", "retention"]
        if any(pattern in metric_lower for pattern in engagement_patterns):
            return "engagement_metrics"
        
        # ✅ Completion indicators (progress, milestones)
        completion_patterns = ["completion", "progress", "milestone", "achievement",
                             "success", "done", "finished", "accomplished"]
        if any(pattern in metric_lower for pattern in completion_patterns):
            return "completion_metrics"
        
        # 🌍 Default to quantified outputs for everything else
        return "quantified_outputs"
    
    def _get_semantic_fallback(self, metric_type: str) -> str:
        """
        🌍 PILLAR 2: Universal semantic fallback based on content meaning
        Last resort classification that works for any business domain
        """
        if not metric_type:
            return "quantified_outputs"
        
        metric_lower = metric_type.lower()
        
        # Very broad semantic categories that apply universally
        if any(word in metric_lower for word in ["list", "collection", "database", "contacts", "items"]):
            return "quantified_outputs"
        elif any(word in metric_lower for word in ["analysis", "report", "strategy", "framework"]):
            return "completion_metrics" 
        elif any(word in metric_lower for word in ["sequence", "template", "content", "document"]):
            return "quantified_outputs"
        else:
            # Ultimate universal fallback
            return "quantified_outputs"
    
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
            
            # 🚨 CRITICAL ERROR: No agents available for corrective task creation
            if selected_agent_role is None:
                logger.error(f"🚨 CRITICAL: No agents available in workspace {workspace_id} for corrective task creation")
                
                # This should not happen in a healthy workspace - alert the issue
                try:
                    alert_data = {
                        "workspace_id": workspace_id,
                        "type": "system",
                        "message": "CRITICAL: Corrective task creation failed - no agents available",
                        "metadata": {
                            "alert_type": "corrective_task_failure",
                            "issue_type": "NO_AGENTS_FOR_CORRECTIVE_TASK",
                            "description": f"Goal-driven task planner could not create corrective task due to no available agents in workspace {workspace_id}",
                            "severity": "critical",
                            "requires_intervention": True,
                            "detected_at": datetime.now().isoformat(),
                            "component": "goal_driven_task_planner"
                        },
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("logs").insert(alert_data).execute()
                except Exception as e:
                    logger.error(f"Failed to create alert for no-agents issue: {e}")
                
                return {}
            
            # 🎯 CREATE URGENT CORRECTIVE TASK
            context_data = {
                "is_goal_driven": True,
                "auto_generated": True,
                "task_type": "corrective_action",
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
                    "metric": str(goal.metric_type),
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
            
            corrective_task = {
                "goal_id": str(goal.id),
                "metric_type": str(goal.metric_type),
                "name": f"🚨 URGENT: Close {gap_percentage:.1f}% gap in {str(goal.metric_type)}",
                "description": f"Critical corrective action required. Current gap: {remaining_gap} {goal.unit}. Must achieve target within 24 hours.",
                "priority": "high",  # Highest priority
                "contribution_expected": remaining_gap,
                "context_data": context_data
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
                "status", "available"
            ).execute()
            
            available_agents = response.data or []
            
            if not available_agents:
                logger.warning(f"⚠️ No available agents found in workspace {workspace_id} - skipping task creation")
                # Return None to indicate no task should be created
                return None
            
            logger.info(f"📋 Found {len(available_agents)} available agents in workspace {workspace_id}")
            
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