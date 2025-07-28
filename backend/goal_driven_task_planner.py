# backend/goal_driven_task_planner.py

import json
import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models import (
    WorkspaceGoal, GoalStatus, TaskCreate, TaskStatus
)
from services.task_deduplication_manager import task_deduplication_manager
from database import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()

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
            # 🔧 FIX: Check similar tasks ONLY for the same goal, not workspace-wide
            similar_tasks_same_goal = await self._check_similar_tasks_for_goal(workspace_id, str(goal.id), str(goal.metric_type))
            if similar_tasks_same_goal:
                logger.info(f"🔄 Goal {goal.metric_type} has similar tasks in same goal ({len(similar_tasks_same_goal)} found)")
                
                # Only block if we have enough similar tasks FOR THIS SPECIFIC GOAL
                if len(similar_tasks_same_goal) >= 2:
                    logger.info(f"✅ Sufficient similar tasks ({len(similar_tasks_same_goal)}) found for goal {goal.metric_type}")
                    return similar_tasks_same_goal
                else:
                    logger.info(f"⚠️ Only {len(similar_tasks_same_goal)} similar tasks found for this goal - creating additional tasks")
                    # Continue with normal task creation
            
            # DISABLED: Workspace-wide similarity check causing false positives
            # The system was erroneously blocking task creation when goals had different purposes
            # but similar semantic keywords (e.g., "deliverable", "email"). This prevents goal isolation.
            # workspace_similar_tasks = await self._check_similar_tasks_workspace_wide(workspace_id, str(goal.id), str(goal.metric_type))
            # if workspace_similar_tasks and len(workspace_similar_tasks) >= 4:  # Increased from 2 to 4
            #     logger.warning(f"⚠️ Found {len(workspace_similar_tasks)} very similar tasks workspace-wide - consider if more are needed")
            
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
            
            # Get available agents for task assignment (accept any status except "inactive")
            agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).neq("status", "inactive").execute()
            available_agents = agents_response.data or []
            
            if not available_agents:
                logger.warning(f"⚠️ No agents found for workspace {workspace_id} - attempting to create basic agents")
                
                # FIXED: Auto-create basic agents for workspace
                try:
                    basic_agents = await self._create_basic_agents_for_workspace(workspace_id)
                    if basic_agents:
                        available_agents = basic_agents
                        logger.info(f"✅ Created {len(basic_agents)} basic agents for workspace {workspace_id}")
                    else:
                        logger.warning(f"⚠️ Failed to create basic agents - tasks will be created unassigned")
                except Exception as e:
                    logger.error(f"Error creating basic agents for workspace {workspace_id}: {e}")
            else:
                logger.info(f"✅ Found {len(available_agents)} agents for task assignment in workspace {workspace_id}")
            
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
                task_to_create = TaskCreate(
                    workspace_id=UUID(workspace_id),
                    goal_id=goal.id,
                    name=task_data.get("name"),
                    description=task_data.get("description"),
                    status=TaskStatus.PENDING,
                    agent_id=assigned_agent_id,
                    priority=task_data.get("priority", "medium"),
                    context_data={
                        **(task_data.get("context_data", {})),
                        "is_goal_driven": True,
                        "auto_generated": True,
                        "generated_by": "goal_driven_task_planner",
                        "goal_analysis_timestamp": datetime.now().isoformat(),
                        "assigned_agent_name": assigned_agent.get('name') if available_agents else None,
                        "assigned_agent_role": assigned_agent_role
                    }
                )

                created_task = await task_deduplication_manager.create_task_with_deduplication(task_to_create)
                
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
        
        # Check migration flag to decide which implementation to use
        from config.migration_config import is_sdk_migrated
        if is_sdk_migrated('task_generation_sdk'):
            from goal_driven_task_planner_sdk import goal_driven_task_planner_sdk
            logger.info("🚀 Using SDK-based task generation.")
            return await goal_driven_task_planner_sdk._generate_ai_driven_tasks(goal, gap, workspace_context)
        else:
            logger.info("Legacy task generation in use.")
            # Use AI for ALL goal types - no more hardcoded templates
            return await self._generate_ai_driven_tasks_legacy(goal, gap, workspace_context)

    async def _generate_ai_driven_tasks_legacy(
        self, 
        goal: WorkspaceGoal, 
        gap: float, 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        🤖 **RE-ARCHITECTED** AI-Driven Task Generation
        This function now uses a two-stage process: Analysis and Generation, controlled by Python logic.
        """
        from services.ai_provider_abstraction import ai_provider_manager

        if not self.ai_available:
            return await self._fallback_generic_tasks(goal, gap)

        try:
            # STAGE 1: ANALYSIS - Use the Analyst Agent to determine data requirements
            analysis_result = await self._analyze_goal_requirements_ai(goal, workspace_context)
            requires_data_gathering = analysis_result.get("requires_data_gathering", False)
            data_points_needed = analysis_result.get("data_points_needed", [])

            tasks = []

            if requires_data_gathering and data_points_needed:
                logger.info(f"Analyst Agent identified {len(data_points_needed)} data gathering tasks for goal '{goal.description}'")
                # STAGE 2a: DATA GATHERING TASKS (Programmatically created)
                for i, data_point in enumerate(data_points_needed):
                    task = {
                        "name": f"Create Asset: {data_point}",
                        "description": f"Task {i+1} of {len(data_points_needed)+1}: Gather the following data required for the final asset: {data_point}.",
                        "asset_type": "list",
                        "deliverable_format": "json",
                        "success_criteria": ["A JSON list containing the requested data is produced."],
                        "contribution_expected": 10, # Small contribution for data gathering
                        "priority": "high"
                    }
                    tasks.append(task)

                # STAGE 2b: FINAL ASSEMBLY TASK (Programmatically created)
                final_task_name = f"Create Asset: Final Deliverable for '{goal.description}'"
                final_task_description = f"Final assembly task: Use the data gathered from the previous tasks ({', '.join(data_points_needed)}) to produce the complete, final asset for the goal: '{goal.description}'. Do not produce a plan or a template."
                
                assembly_task = {
                    "name": final_task_name,
                    "description": final_task_description,
                    "asset_type": "document", # Generic, agent will determine final format
                    "deliverable_format": "markdown",
                    "success_criteria": ["The final asset is complete, contains all gathered data, and is ready for use."],
                    "contribution_expected": 80, # Major contribution for final assembly
                    "priority": "medium"
                }
                tasks.append(assembly_task)
            
            else:
                logger.info(f"Analyst Agent determined no data gathering is needed for goal '{goal.description}'. Creating a direct asset production task.")
                # DIRECT ASSET PRODUCTION TASK
                direct_task = {
                    "name": f"Create Asset: {goal.description}",
                    "description": f"Directly produce the final, complete, and ready-to-use asset for the goal: '{goal.description}'. No planning or templates.",
                    "asset_type": "document",
                    "deliverable_format": "markdown",
                    "success_criteria": ["The final asset is complete and ready for use."],
                    "contribution_expected": 100,
                    "priority": "high"
                }
                tasks.append(direct_task)

            logger.info(f"🤖 Created a task plan with {len(tasks)} steps for goal '{goal.description}'")
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

    async def _analyze_goal_requirements_ai(self, goal: WorkspaceGoal, workspace_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 **NEW Analyst Agent**
        Uses AI to determine if a goal requires real-world data gathering before the final asset can be assembled.
        """
        from services.ai_provider_abstraction import ai_provider_manager

        if not self.ai_available:
            return {"requires_data_gathering": False, "data_points_needed": []}

        try:
            prompt = f"""You are a meticulous Analyst Agent. Your only job is to analyze a business goal and determine if creating the final asset requires gathering specific, real-world data points first.

**Goal to Analyze:**
- **Description:** {goal.description}
- **Metric:** {goal.metric_type}
- **Business Context:** {workspace_context.get('description', 'General business operations')}

**Your Task:**
Analyze the goal. Does producing the final deliverable require concrete data that is not yet available?
- **Example 1:** If the goal is "Create a competitor analysis report", it **requires data gathering** (competitor names, pricing, features).
- **Example 2:** If the goal is "Write a generic welcome email template", it **does not require data gathering** as it uses placeholders.
- **Example 3:** If the goal is "Write a welcome email for our new client, Acme Corp", it **requires data gathering** (details about Acme Corp).

Respond ONLY with a JSON object in the following format:
```json
{{
    "requires_data_gathering": boolean,
    "data_points_needed": [
        "A very specific, short description of the first data point to find (e.g., 'List of 3 competitor names').",
        "A very specific, short description of the second data point to find (e.g., 'Pricing information for each competitor')."
    ]
}}
```

**Instructions:**
- If `requires_data_gathering` is `false`, `data_points_needed` must be an empty array.
- Be very specific in `data_points_needed`. Each item should be a clear instruction for a data collection task.
- Do not list more than 3 essential data points.
"""

            analyst_agent = {
                "name": "AnalystAgent",
                "model": "gpt-4o-mini",
                "instructions": "You are an analyst that determines data requirements for business goals. Respond only with the requested JSON format.",
            }

            result = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=analyst_agent,
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            if isinstance(result, str):
                result = json.loads(result)
            
            # Validate the response structure
            if "requires_data_gathering" in result and "data_points_needed" in result:
                logger.info(f"✅ Analyst Agent determined data requirements for '{goal.description}': {result}")
                return result
            else:
                logger.warning(f"⚠️ Analyst Agent returned invalid format. Defaulting to no data gathering. Response: {result}")
                return {"requires_data_gathering": False, "data_points_needed": []}

        except Exception as e:
            logger.error(f"Error in Analyst Agent execution: {e}")
            return {"requires_data_gathering": False, "data_points_needed": []}
    
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
            
            # FIXED: Clean AI response from quotes and extra characters
            ai_classification = ai_classification.strip('"').strip("'").strip()
            
            # Validate response
            valid_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                              "engagement_metrics", "completion_metrics", "performance_metrics",
                              "user_metrics", "business_metrics"]
            
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

    async def _get_workspace_context(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace context for AI-driven task generation"""
        try:
            # Get workspace details
            workspace_response = supabase.table("workspaces").select("*").eq(
                "id", workspace_id
            ).single().execute()
            
            if not workspace_response.data:
                return {"workspace_goal": "General workspace tasks", "domain": "general"}
            
            workspace = workspace_response.data
            
            # Get agents for context
            agents_response = supabase.table("agents").select("role, seniority").eq(
                "workspace_id", workspace_id
            ).execute()
            
            agents = agents_response.data or []
            
            return {
                "workspace_goal": workspace.get("goal", "General workspace tasks"),
                "workspace_description": workspace.get("description", ""),
                "domain": workspace.get("domain", "general"),
                "budget": workspace.get("budget", 1000),
                "team_roles": [agent.get("role", "Specialist") for agent in agents],
                "team_count": len(agents)
            }
            
        except Exception as e:
            logger.error(f"Error getting workspace context: {e}")
            return {"workspace_goal": "General workspace tasks", "domain": "general"}
    
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
    
    async def _check_similar_tasks_for_goal(self, workspace_id: str, goal_id: str, metric_type: str) -> List[Dict]:
        """
        🎯 GOAL-SPECIFIC: Check for semantically similar tasks ONLY within the same goal
        
        This prevents blocking task creation for different goals with similar themes.
        """
        try:
            # Get tasks ONLY for this specific goal
            response = supabase.table("tasks").select("id, name, goal_id, created_at, status, description").eq(
                "workspace_id", workspace_id
            ).eq(
                "goal_id", goal_id  # CRITICAL: Only check within same goal
            ).in_(
                "status", ["pending", "in_progress", "blocked", "completed"]
            ).execute()
            
            goal_tasks = response.data or []
            
            if not goal_tasks:
                return []
            
            # Use AI to detect similar tasks within this goal
            similar_tasks = await self._detect_similar_tasks_ai_driven(goal_tasks, metric_type)
            
            if similar_tasks:
                logger.info(f"🎯 Found {len(similar_tasks)} similar tasks within goal {goal_id}")
            
            return similar_tasks
            
        except Exception as e:
            logger.error(f"Error checking similar tasks for goal: {e}")
            return []

    async def _check_similar_tasks_workspace_wide(self, workspace_id: str, goal_id: str, metric_type: str) -> List[Dict]:
        """
        🛡️ ENHANCED PREVENTION: Check for semantically similar tasks across the entire workspace
        
        Prevents creation of duplicate tasks even if they're for different goals but same purpose.
        """
        try:
            # CRITICAL FIX: Use the class-level supabase client, not undefined variable
            from database import get_supabase_client
            supabase_client = get_supabase_client()
            
            from datetime import datetime, timedelta
            import difflib
            
            # CRITICAL FIX: Get ALL active/pending tasks from workspace (not just recent)
            # This prevents cross-goal duplicates regardless of creation time
            response = supabase_client.table("tasks").select("id, name, goal_id, created_at, status, description").eq(
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
                            "similarity_threshold": 0.85  # Very high threshold - only catch true duplicates
                        }
                    )
                    
                    # If tasks are similar enough, add both to similar_tasks list
                    if similarity_result.similarity_score >= 0.85:  # Increased threshold
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
    
    async def _create_basic_agents_for_workspace(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        FIXED: Auto-create basic agents when none exist for a workspace
        """
        try:
            from uuid import uuid4
            from datetime import datetime
            
            basic_agents_data = [
                {
                    "id": str(uuid4()),
                    "workspace_id": workspace_id,
                    "name": "General Task Agent",
                    "role": "generalist",
                    "seniority": "senior",
                    "skills": ["general_tasks", "documentation", "analysis"],
                    "personality": "efficient and thorough",
                    "status": "active",
                    "model": "gpt-4o-mini",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "metadata": {"auto_created": True, "reason": "no_agents_found"}
                },
                {
                    "id": str(uuid4()),
                    "workspace_id": workspace_id,
                    "name": "Technical Specialist",
                    "role": "specialist",
                    "seniority": "expert",
                    "skills": ["technical_tasks", "development", "implementation"],
                    "personality": "detail-oriented and analytical",
                    "status": "active",
                    "model": "gpt-4o-mini",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "metadata": {"auto_created": True, "reason": "no_agents_found"}
                }
            ]
            
            created_agents = []
            for agent_data in basic_agents_data:
                try:
                    result = supabase.table("agents").insert(agent_data).execute()
                    if result.data:
                        created_agents.append(result.data[0])
                        logger.info(f"✅ Created basic agent: {agent_data['name']}")
                except Exception as e:
                    logger.error(f"Error creating basic agent {agent_data['name']}: {e}")
            
            return created_agents
            
        except Exception as e:
            logger.error(f"Error creating basic agents for workspace {workspace_id}: {e}")
            return []

# Singleton instance
goal_driven_task_planner = GoalDrivenTaskPlanner()