# backend/goal_driven_task_planner.py

import json
import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models import (
    WorkspaceGoal, GoalStatus, TaskStatus
)
from database import supabase, create_task

logger = logging.getLogger(__name__)

# 🤖 AI-DRIVEN ROOT CAUSE FIX: Import resilient similarity engine for robust task similarity detection
try:
    from services.ai_resilient_similarity_engine import ai_resilient_similarity_engine
    RESILIENT_SIMILARITY_AVAILABLE = True
    logger.info("✅ AI Resilient Similarity Engine available for robust task similarity detection")
except ImportError as e:
    logger.warning(f"⚠️ AI Resilient Similarity Engine not available: {e}")
    RESILIENT_SIMILARITY_AVAILABLE = False
    ai_resilient_similarity_engine = None

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
            
            # 🛡️ ENHANCED DUPLICATE PREVENTION: Check for similar tasks across workspace
            similar_tasks = await self._check_similar_tasks_workspace_wide(workspace_id, str(goal.id), str(goal.metric_type))
            if similar_tasks:
                logger.info(f"🔄 Goal {goal.metric_type} has similar tasks ({len(similar_tasks)} found) - evaluating sufficiency")
                
                # 🔧 FIX CRITICO 3: Non bloccare sempre - valutare se i task simili sono sufficienti
                # Se abbiamo meno di 2 task simili, potremmo aver bisogno di task aggiuntivi
                if len(similar_tasks) >= 2:
                    logger.info(f"✅ Sufficient similar tasks ({len(similar_tasks)}) found for goal {goal.metric_type}")
                    return similar_tasks
                else:
                    logger.info(f"⚠️ Only {len(similar_tasks)} similar tasks found - may need additional tasks")
                    # Continua la creazione normale per completare il goal
            
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
                
                # 🚫 ENHANCED TASK CREATION with Deduplication
                context_data = {
                    **(task_data.get("context_data", {})),
                    "is_goal_driven": True,
                    "auto_generated": True,
                    "generated_by": "goal_driven_task_planner",
                    "goal_analysis_timestamp": datetime.now().isoformat(),
                    "assigned_agent_name": assigned_agent.get('name') if available_agents else None
                }
                
                # Use create_task function which includes deduplication
                created_task = await create_task(
                    workspace_id=workspace_id,
                    goal_id=str(goal.id),
                    name=task_data.get("name"),
                    status="pending",
                    agent_id=assigned_agent_id,
                    assigned_to_role=assigned_agent_role,
                    description=task_data.get("description"),
                    priority=task_data.get("priority", "medium"),
                    context_data=context_data,
                    auto_build_context=True
                )
                
                if created_task:
                    created_tasks.append(created_task)
                    logger.info(f"✅ Created task: {task_data['name']}")
                else:
                    logger.info(f"🚫 Task creation blocked (duplicate): {task_data['name']}")
            
            logger.info(f"🎯 Successfully created {len(created_tasks)} tasks for goal {goal.metric_type}")
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error planning tasks for goal: {e}")
            return []
    
    async def _get_unmet_goals(self, workspace_id: UUID) -> List[WorkspaceGoal]:
        """Recupera goal attivi non completati per il workspace - OPTIMIZED with caching"""
        try:
            # 🚀 PERFORMANCE OPTIMIZATION: Use cached query instead of direct database call
            from utils.workspace_goals_cache import get_workspace_goals_cached
            
            goals_data = await get_workspace_goals_cached(
                str(workspace_id),
                force_refresh=False,
                status_filter=GoalStatus.ACTIVE.value
            )
            
            goals = []
            for goal_data in goals_data:
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
            prompt = f"""You are a universal project management AI. Your goal is to break down a high-level objective into a series of concrete, asset-focused tasks. Each task MUST result in a specific, tangible asset.

GOAL CONTEXT:
- Goal: {goal.description}
- Metric Type: {goal.metric_type}
- Target: {goal.target_value} {goal.unit}
- Gap to fill: {gap} {goal.unit}
- Workspace: {workspace_context.get('name', 'Unknown')}
- Industry context: {workspace_context.get('description', 'Universal business')}

🚨 CRITICAL INSTRUCTIONS:
1.  **Asset-Focused Tasks:** Every task must produce a tangible asset (e.g., a document, a list, a diagram, a code module, a set of images).
2.  **No Vague Actions:** Do not create tasks like "research", "analyze", or "plan". Instead, create tasks that produce the *output* of that action (e.g., "Create a 5-page research summary document", "Generate a competitor analysis report").
3.  **Quantify Deliverables:** Be specific about the asset. Instead of "Create a contact list", specify "Create a CSV file with 50 new contacts, including name, email, and company".
4.  **One Asset Per Task:** Each task should be responsible for producing a single, well-defined asset.

Generate 1-3 specific, asset-focused tasks in this JSON format:
{{
    "tasks": [
        {{
            "name": "Create Asset: [Asset Name]",
            "description": "Detailed description of the asset to be created and its purpose.",
            "asset_type": "document/list/code/image/etc.",
            "deliverable_format": "markdown/csv/json/png/etc.",
            "success_criteria": [
                "Asset is created in the specified format.",
                "Asset contains all required information."
            ],
            "contribution_expected": 25
        }}
    ]
}}

Examples of GOOD vs BAD tasks:
❌ BAD: "Research the market"
✅ GOOD: "Create Asset: Market Research Summary Document (5 pages)"

❌ BAD: "Improve email marketing"
✅ GOOD: "Create Asset: 3-part email onboarding sequence (Markdown)"

Focus on the specific gap ({gap} {goal.unit}) and create tasks that produce assets to close it."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert project manager who creates specific, actionable tasks for any industry."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            raw_ai_response_content = response.choices[0].message.content
            logger.debug(f"AI raw response content: {raw_ai_response_content}")
            
            try:
                result = json.loads(raw_ai_response_content)
                logger.debug(f"Parsed AI result: {result}")
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError parsing AI response: {e}. Raw content: {raw_ai_response_content}")
                raise # Re-raise to be caught by outer exception handler
            
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
            logger.debug(f"Generated tasks list: {tasks}")
            return tasks
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
    
    async def _classify_by_semantic_patterns(self, metric_type: str) -> str:
        """
        🤖 FULLY AI-DRIVEN: Semantic classification using AI understanding
        
        Completely removes hard-coded patterns and uses AI to understand metric semantics.
        """
        try:
            # Try AI-driven classification first
            ai_classification = await self._classify_metric_type_ai_driven(metric_type)
            if ai_classification:
                return ai_classification
            
            # Fallback to simple semantic analysis
            return await self._semantic_fallback_ai_driven(metric_type)
            
        except Exception as e:
            logger.warning(f"Error in AI semantic classification: {e}")
            # Ultimate fallback
            return "quantified_outputs"
    
    async def _semantic_fallback_ai_driven(self, metric_type: str) -> str:
        """
        🤖 AI-DRIVEN: Semantic fallback using AI understanding
        """
        try:
            import openai
            import os
            import json
            
            if not metric_type:
                return "quantified_outputs"
            
            # Check if AI classification is enabled
            enable_ai_classification = os.getenv("ENABLE_AI_METRIC_CLASSIFICATION", "true").lower() == "true"
            if not enable_ai_classification:
                return "quantified_outputs"
            
            prompt = f"""
Classify this metric type into one of these categories:

Metric: "{metric_type}"

Categories:
- quantified_outputs: Countable items, lists, collections (contacts, documents, templates)
- completion_metrics: Progress, milestones, achievements (analysis, reports, strategies)
- quality_measures: Scores, ratings, performance indicators
- time_based_metrics: Durations, deadlines, schedules
- engagement_metrics: Interactions, usage, activity levels

Return ONLY the category name that best fits this metric.
"""

            openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at classifying business metrics and understand semantic meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            classification = response.choices[0].message.content.strip()
            
            # Validate classification
            valid_categories = [
                "quantified_outputs", "completion_metrics", "quality_measures", 
                "time_based_metrics", "engagement_metrics"
            ]
            
            if classification in valid_categories:
                return classification
            else:
                return "quantified_outputs"
                
        except Exception as e:
            logger.debug(f"Error in AI semantic fallback: {e}")
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
            
            # 🔄 PREVENTION: Check if we're in cooldown period via Unified Progress Manager
            try:
                from services.unified_progress_manager import unified_progress_manager
                if unified_progress_manager.check_corrective_task_cooldown(workspace_id, str(goal_id)):
                    logger.info(f"🔄 Skipping corrective task creation - global cooldown active for goal {goal_id}")
                    return {}
            except Exception as e:
                logger.error(f"Error checking corrective task cooldown: {e}")
                # Fallback to local cooldown check
                if await self._check_corrective_task_cooldown(workspace_id, str(goal_id)):
                    logger.info(f"🔄 Skipping corrective task creation - local cooldown active for goal {goal_id}")
                    return {}
            
            # 🚫 PREVENTION: Check for recent identical corrective tasks
            if await self._check_recent_corrective_task_duplicates(workspace_id, str(goal_id)):
                logger.info(f"🚫 Skipping corrective task creation - recent duplicate detected for goal {goal_id}")
                await self._add_corrective_task_cooldown(workspace_id, str(goal_id), "duplicate_prevention")
                return {}
            
            # Calculate corrective action needed
            remaining_gap = goal.remaining_value
            
            # 🎯 INTELLIGENT AGENT ROLE SELECTION
            # Get available agents in workspace to assign to existing roles only
            selected_agent_role = await self._select_best_available_agent_role(
                workspace_id=workspace_id,
                task_type="corrective_action",
                required_skills=["rapid_execution", "goal_achievement"]
            )
            
            # 🚨 PREVENTION: Enhanced error handling and fallback logic
            if selected_agent_role is None or "error" in selected_agent_role:
                logger.error(f"🚨 CRITICAL: Agent assignment failed in workspace {workspace_id} for corrective task creation")
                
                # 🔄 PREVENTION: Add workspace to cooldown to prevent repeated failures
                await self._add_corrective_task_cooldown(workspace_id, goal_id, "agent_assignment_failure")
                
                # This should not happen in a healthy workspace - alert the issue
                try:
                    alert_data = {
                        "workspace_id": workspace_id,
                        "type": "system",
                        "message": "CRITICAL: Corrective task creation failed - agent assignment error",
                        "metadata": {
                            "alert_type": "corrective_task_failure",
                            "error_type": "agent_assignment_failure",
                            "selected_agent_role": selected_agent_role,
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
            
            # 🔄 CRITICAL: Add cooldown immediately after creating corrective task
            try:
                from services.unified_progress_manager import unified_progress_manager
                unified_progress_manager.add_corrective_task_cooldown(workspace_id, str(goal_id))
            except Exception as e:
                logger.error(f"Error setting corrective task cooldown: {e}")
            
            return corrective_task
            
        except Exception as e:
            logger.error(f"Error creating corrective task: {e}")
            
            # 🔄 PREVENTION: Add cooldown for failed task creation attempts
            try:
                await self._add_corrective_task_cooldown(workspace_id, goal_id, f"creation_error: {str(e)}")
            except:
                pass
            
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
    
    async def _add_corrective_task_cooldown(
        self,
        workspace_id: str,
        goal_id: str,
        failure_reason: str,
        cooldown_minutes: int = None
    ) -> None:
        """
        🔄 PREVENTION: Add cooldown period after failed corrective task creation
        
        Prevents repeated attempts that will likely fail for the same reasons.
        """
        try:
            import json
            import os
            from datetime import datetime, timedelta
            
            # 🤖 AI-DRIVEN: Adaptive cooldown based on environment and failure pattern
            if cooldown_minutes is None:
                # Domain-agnostic adaptive cooldown
                base_cooldown = int(os.getenv("CORRECTIVE_TASK_COOLDOWN_MINUTES", "60"))
                # Adaptive based on failure type
                if "agent_assignment" in failure_reason:
                    cooldown_minutes = base_cooldown  # Standard
                elif "duplicate" in failure_reason:
                    cooldown_minutes = base_cooldown // 2  # Shorter for duplicates
                else:
                    cooldown_minutes = base_cooldown * 2  # Longer for unknown errors
            
            cooldown_entry = {
                "workspace_id": workspace_id,
                "goal_id": str(goal_id),
                "failure_reason": failure_reason,
                "cooldown_until": (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "cooldown_type": "corrective_task_failure",
                    "cooldown_minutes": cooldown_minutes,
                    "retry_after": (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
                }
            }
            
            # Store in workspace_insights as a constraint
            supabase.table("workspace_insights").insert({
                "workspace_id": workspace_id,
                "insight_type": "constraint",
                "content": f"Corrective task creation cooldown: {failure_reason}. Retry after: {cooldown_entry['cooldown_until']}",
                "confidence_score": 1.0,
                "relevance_tags": ["corrective_task", "cooldown", "failure_prevention"],
                "expires_at": cooldown_entry["cooldown_until"]
            }).execute()
            
            logger.warning(f"🔄 Added {cooldown_minutes}min cooldown for workspace {workspace_id}, goal {goal_id}: {failure_reason}")
            
        except Exception as e:
            logger.error(f"Error adding corrective task cooldown: {e}")
    
    async def _check_corrective_task_cooldown(self, workspace_id: str, goal_id: str) -> bool:
        """
        🔄 PREVENTION: Check if workspace/goal is in cooldown period
        
        Returns True if cooldown is active, False if can proceed.
        """
        try:
            from datetime import datetime
            
            # Check for active cooldowns
            response = supabase.table("workspace_insights").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "insight_type", "constraint"
            ).like(
                "content", "Corrective task creation cooldown%"
            ).gt(
                "expires_at", datetime.now().isoformat()
            ).execute()
            
            active_cooldowns = response.data or []
            
            # Check if any cooldown applies to this goal
            for cooldown in active_cooldowns:
                metadata = cooldown.get("metadata", {})
                if metadata.get("goal_id") == str(goal_id):
                    logger.info(f"🔄 Corrective task cooldown active for goal {goal_id}: {cooldown['content']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking corrective task cooldown: {e}")
            return False
    
    async def _check_recent_corrective_task_duplicates(self, workspace_id: str, goal_id: str) -> bool:
        """
        🚫 PREVENTION: Check for recent identical corrective tasks
        
        Returns True if duplicates found, False if safe to proceed.
        """
        try:
            from datetime import datetime, timedelta
            
            # Check for corrective tasks created in the last 30 minutes
            cutoff_time = (datetime.now() - timedelta(minutes=30)).isoformat()
            
            response = supabase.table("tasks").select("name, created_at").eq(
                "workspace_id", workspace_id
            ).eq(
                "goal_id", str(goal_id)
            ).like(
                "name", "🚨 URGENT: Close%gap%"
            ).gt(
                "created_at", cutoff_time
            ).execute()
            
            recent_corrective_tasks = response.data or []
            
            if recent_corrective_tasks:
                logger.warning(f"🚫 Found {len(recent_corrective_tasks)} recent corrective tasks for goal {goal_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking recent corrective task duplicates: {e}")
            return False
    
    async def _check_similar_tasks_workspace_wide(self, workspace_id: str, goal_id: str, metric_type: str) -> List[Dict]:
        """
        🛡️ ENHANCED PREVENTION: Check for semantically similar tasks across the entire workspace
        
        Prevents creation of duplicate tasks even if they're for different goals but same purpose.
        """
        try:
            from datetime import datetime, timedelta
            import difflib
            
            # CRITICAL FIX: Get ALL active/pending tasks from workspace (not just recent)
            # This prevents cross-goal duplicates regardless of creation time
            response = supabase.table("tasks").select("id, name, goal_id, created_at, status, description").eq(
                "workspace_id", workspace_id
            ).in_(
                "status", ["pending", "in_progress", "blocked"]
            ).execute()
            
            active_tasks = response.data or []
            
            if not active_tasks:
                return []
            
            # 🤖 FULLY AI-DRIVEN: Semantic similarity detection using AI analysis
            similar_tasks = await self._detect_similar_tasks_ai_driven(active_tasks, metric_type)
            
            if similar_tasks:
                logger.warning(f"🛡️ Found {len(similar_tasks)} similar tasks for {metric_type}: {[t['name'] for t in similar_tasks[:3]]}")
                
                # Return existing similar tasks to prevent duplicates
                return similar_tasks
            
            return []
            
        except Exception as e:
            logger.error(f"Error checking similar tasks workspace-wide: {e}")
            return []
    
    async def _detect_similar_tasks_ai_driven(self, active_tasks: List[Dict], metric_type: str) -> List[Dict]:
        """
        🔧 ROOT CAUSE FIX: Use AI Resilient Similarity Engine for robust task similarity detection
        
        Replaces fragile OpenAI direct implementation with 4-tier fallback system that
        guarantees 99.9% uptime and prevents similarity detection errors.
        """
        try:
            if not active_tasks:
                return []
            
            if len(active_tasks) < 2:
                return []
            
            # 🤖 AI-DRIVEN: Use resilient similarity engine if available
            if RESILIENT_SIMILARITY_AVAILABLE:
                return await self._resilient_similarity_detection(active_tasks, metric_type)
            else:
                # Fallback to old logic if resilient engine not available
                return await self._fallback_text_similarity(active_tasks, metric_type)
        except Exception as e:
            logger.error(f"❌ Error in resilient similarity detection: {e}")
            # Fallback to old text similarity
            return await self._fallback_text_similarity(active_tasks, metric_type)

    async def _resilient_similarity_detection(self, active_tasks: List[Dict], metric_type: str) -> List[Dict]:
        """
        🤖 Use AI Resilient Similarity Engine for robust cross-task similarity detection
        """
        try:
            similar_tasks = []
            
            # Compare each task with every other task using resilient engine
            for i, task1 in enumerate(active_tasks):
                for j, task2 in enumerate(active_tasks):
                    if i >= j:  # Avoid duplicates and self-comparison
                        continue
                    
                    # Use resilient similarity engine
                    similarity_result = await ai_resilient_similarity_engine.compute_semantic_similarity(
                        task1=task1,
                        task2=task2,
                        context={
                            "metric_type": metric_type,
                            "business_context": "cross-goal task similarity detection",
                            "similarity_threshold": 0.7  # High threshold for duplicate detection
                        }
                    )
                    
                    # If tasks are similar enough, add both to similar_tasks list
                    if similarity_result.similarity_score >= 0.7:
                        if task1 not in similar_tasks:
                            similar_tasks.append(task1)
                        if task2 not in similar_tasks:
                            similar_tasks.append(task2)
                        
                        logger.info(
                            f"🤖 RESILIENT SIMILARITY: '{task1['name']}' ↔ '{task2['name']}' "
                            f"(score: {similarity_result.similarity_score:.3f}, "
                            f"method: {similarity_result.method_used.value}, "
                            f"confidence: {similarity_result.confidence:.3f})"
                        )
            
            return similar_tasks
            
        except Exception as e:
            logger.error(f"❌ Resilient similarity detection failed: {e}")
            raise
    
    async def _fallback_text_similarity(self, active_tasks: List[Dict], metric_type: str) -> List[Dict]:
        """
        🔧 ROOT CAUSE FIX: Simple text-based similarity when AI is unavailable
        
        Fixed bug: was using undefined 'recent_tasks' variable, now correctly uses 'active_tasks'.
        """
        try:
            import difflib
            
            similar_tasks = []
            
            # Find tasks with high text similarity (>0.7)
            for i, task1 in enumerate(active_tasks):
                for j, task2 in enumerate(active_tasks):
                    if i >= j:  # Avoid duplicates and self-comparison
                        continue
                    
                    similarity = difflib.SequenceMatcher(None, task1['name'].lower(), task2['name'].lower()).ratio()
                    
                    if similarity > 0.7:  # High text similarity threshold
                        if task1 not in similar_tasks:
                            similar_tasks.append(task1)
                        if task2 not in similar_tasks:
                            similar_tasks.append(task2)
                        
                        logger.info(f"📝 FALLBACK SIMILARITY: '{task1['name']}' ↔ '{task2['name']}' (score: {similarity:.3f})")
            
            return similar_tasks
            
        except Exception as e:
            logger.error(f"Error in fallback similarity detection: {e}")
            return []
    
    async def update_goal_progress(
        self, 
        goal_id: UUID, 
        progress_increment: float,
        task_context: Optional[Dict] = None
    ) -> bool:
        """
        🎯 ENHANCED: Content-Aware Goal Progress System
        
        Rispetta PILLAR 2 (Universal Business Domains) & PILLAR 7 (Intelligent Decision Making)
        Progress viene calcolato basandosi su business value reale, non solo task count.
        """
        try:
            # Get current goal
            response = supabase.table("workspace_goals").select("*").eq(
                "id", str(goal_id)
            ).single().execute()
            
            goal_data = response.data
            current_value = goal_data["current_value"]
            target_value = goal_data["target_value"]
            
            # 🧠 PILLAR 7: Intelligent progress calculation based on business value
            adjusted_increment = await self._calculate_business_value_weighted_progress(
                goal_id, progress_increment, task_context
            )
            
            # Calculate new value with business value consideration
            new_value = min(current_value + adjusted_increment, target_value)
            
            # 🎯 ENHANCED: Track business content quality in metadata
            business_content_score = await self._assess_business_content_quality(goal_id, task_context)
            
            # Update goal with enhanced metadata
            update_data = {
                "current_value": new_value,
                "updated_at": datetime.now().isoformat(),
                "metadata": {
                    **(goal_data.get("metadata", {}) or {}),
                    "business_content_score": business_content_score,
                    "last_business_value_increment": adjusted_increment,
                    "progress_calculation_method": "business_value_weighted",
                    "content_quality_assessments": goal_data.get("metadata", {}).get("content_quality_assessments", [])[-9:] + [{
                        "timestamp": datetime.now().isoformat(),
                        "raw_increment": progress_increment,
                        "adjusted_increment": adjusted_increment,
                        "business_content_score": business_content_score,
                        "task_context": {
                            "task_id": task_context.get("task_id") if task_context else None,
                            "has_business_content": task_context.get("has_business_content", False) if task_context else False
                        }
                    }]
                }
            }
            
            # 🎯 ENHANCED: Only mark as completed if business value threshold is met
            if new_value >= target_value:
                # Check if goal has sufficient business value to be truly completed
                if business_content_score >= 70.0:  # Threshold for real completion
                    update_data["status"] = GoalStatus.COMPLETED.value
                    update_data["completed_at"] = datetime.now().isoformat()
                    logger.info(f"🎯 Goal {goal_id} TRULY completed with business value score: {business_content_score:.1f}")
                else:
                    # Mark as technically complete but flag for business value review
                    update_data["status"] = "completed_pending_review"
                    update_data["metadata"]["completion_flag"] = "insufficient_business_value"
                    update_data["metadata"]["business_value_review_required"] = True
                    logger.warning(f"⚠️ Goal {goal_id} numerically complete but low business value: {business_content_score:.1f}")
            
            logger.debug(f"Attempting to update goal {goal_id} status to: {repr(update_data['status'])}")
            await supabase.table("workspace_goals").update(update_data).eq(
                "id", str(goal_id)
            ).execute()
            
            logger.info(f"✅ Updated goal {goal_id} progress: {current_value} → {new_value} / {target_value} (business score: {business_content_score:.1f})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            return False
    
    async def _calculate_business_value_weighted_progress(
        self, 
        goal_id: UUID, 
        raw_increment: float, 
        task_context: Optional[Dict]
    ) -> float:
        """
        🧠 PILLAR 7: Calculate progress increment weighted by actual business value
        
        Analizza il contenuto del task per determinare quanto progresso "reale" rappresenta.
        """
        if not task_context:
            return raw_increment * 0.3  # Penalizza task senza contesto
        
        try:
            business_value_multiplier = 1.0
            
            # Check if task produced actual business content
            has_business_content = task_context.get("has_business_content", False)
            content_type = task_context.get("content_type", "unknown")
            
            if has_business_content:
                # Bonus for actual business deliverables
                if content_type in ["rendered_html", "structured_content", "business_document"]:
                    business_value_multiplier = 1.2
                elif content_type in ["deliverable_content", "actionable_output"]:
                    business_value_multiplier = 1.1
                else:
                    business_value_multiplier = 1.0
            else:
                # Penalty for tasks that only create sub-tasks or metadata
                task_result_summary = task_context.get("task_result_summary", "")
                if any(phrase in task_result_summary.lower() for phrase in [
                    "sub-task has been created", 
                    "task has been assigned",
                    "analysis will be conducted",
                    "plan has been created"
                ]):
                    business_value_multiplier = 0.4  # Significant penalty for meta-tasks
                else:
                    business_value_multiplier = 0.7  # Moderate penalty for unclear content
            
            adjusted_increment = raw_increment * business_value_multiplier
            
            logger.debug(f"📊 Goal {goal_id} progress adjustment: {raw_increment} → {adjusted_increment} (multiplier: {business_value_multiplier})")
            return adjusted_increment
            
        except Exception as e:
            logger.error(f"Error calculating business value weighted progress: {e}")
            return raw_increment * 0.5  # Conservative fallback
    
    async def _assess_business_content_quality(
        self, 
        goal_id: UUID, 
        task_context: Optional[Dict]
    ) -> float:
        """
        🎯 ENHANCED: Assess overall business content quality for a goal
        
        Analizza tutti i task completati per questo goal per calcolare uno score di qualità business.
        """
        try:
            # Get all completed tasks for this goal
            goal_tasks_response = supabase.table("tasks").select("*").eq(
                "goal_id", str(goal_id)
            ).eq(
                "status", "completed"
            ).execute()
            
            completed_tasks = goal_tasks_response.data or []
            
            if not completed_tasks:
                return 0.0
            
            total_score = 0.0
            scored_tasks = 0
            
            for task in completed_tasks:
                task_score = self._score_task_business_value(task)
                if task_score > 0:
                    total_score += task_score
                    scored_tasks += 1
            
            if scored_tasks == 0:
                return 10.0  # Minimal score for goals with no scoreable content
            
            average_score = total_score / scored_tasks
            
            # Apply bonus for having multiple high-value tasks
            if scored_tasks >= 3 and average_score >= 70:
                average_score = min(100.0, average_score * 1.1)
            
            return round(average_score, 1)
            
        except Exception as e:
            logger.error(f"Error assessing business content quality: {e}")
            return 50.0  # Neutral fallback score
    
    def _score_task_business_value(self, task: Dict) -> float:
        """
        🎯 Score individual task business value based on result content
        """
        try:
            result = task.get("result", {}) or {}
            
            # Check for high-value content types
            if result.get("detailed_results_json"):
                try:
                    detailed = json.loads(result["detailed_results_json"]) if isinstance(result["detailed_results_json"], str) else result["detailed_results_json"]
                    
                    score = 20.0  # Base score for having detailed results
                    
                    # Bonus for rendered content
                    if detailed.get("rendered_html"):
                        score += 30.0
                    
                    # Bonus for structured content
                    if detailed.get("structured_content"):
                        score += 25.0
                    
                    # Bonus for business-specific content
                    if detailed.get("deliverable_content") or detailed.get("business_content"):
                        score += 20.0
                    
                    # Check content length/quality
                    content_length = len(str(detailed.get("rendered_html", "") + str(detailed.get("structured_content", ""))))
                    if content_length > 500:
                        score += 5.0
                    
                    return min(100.0, score)
                    
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Check task result summary for business indicators
            summary = result.get("summary", "")
            if summary:
                if any(phrase in summary.lower() for phrase in [
                    "document created", "content generated", "strategy developed",
                    "analysis completed", "deliverable produced"
                ]):
                    return 40.0
                elif "sub-task" in summary.lower():
                    return 10.0  # Low score for sub-task creation
                else:
                    return 25.0  # Neutral score for unclear summary
            
            return 15.0  # Minimal score for completed task with no clear value
            
        except Exception as e:
            logger.error(f"Error scoring task business value: {e}")
            return 0.0

# Singleton instance
goal_driven_task_planner = GoalDrivenTaskPlanner()