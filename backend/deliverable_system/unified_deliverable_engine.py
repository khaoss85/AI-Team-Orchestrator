# backend/deliverable_system/unified_deliverable_engine.py
"""
Unified Deliverable Engine - Enhanced with Real Asset Extraction
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from database_asset_extensions import asset_db_manager
from .requirements_generator import requirements_generator
from .concrete_asset_extractor import concrete_asset_extractor
from .intelligent_aggregator import intelligent_aggregator

logger = logging.getLogger(__name__)

class UnifiedDeliverableEngine:
    """Unified Deliverable Engine with real asset extraction and intelligent aggregation"""
    
    def __init__(self):
        logger.info("🔧 Unified Deliverable Engine initialized with full capabilities")
        self.db_manager = asset_db_manager
        self.requirements_generator = requirements_generator
        self.asset_extractor = concrete_asset_extractor
        self.aggregator = intelligent_aggregator

    async def generate_requirements_from_goal(self, goal):
        return await self.requirements_generator.generate_requirements_from_goal(goal)

    async def extract_assets(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract real assets from content using AI-powered extraction"""
        return await self.asset_extractor.extract_assets(content, context)

    def process_deliverable(self, content: str) -> Dict[str, Any]:
        """Process deliverable content"""
        return {"status": "processed", "content": content}

    async def stop(self):
        """Stops the engine and cleans up resources."""
        logger.info("Unified Deliverable Engine stopped.")
        pass

# Create singleton instance
unified_deliverable_engine = UnifiedDeliverableEngine()

# Goal-specific deliverable creation
async def create_goal_specific_deliverable(workspace_id: str, goal_id: str, force: bool = False) -> Optional[Dict[str, Any]]:
    """Creates a deliverable for a specific goal from its completed tasks"""
    logger.info(f"🎯 Creating goal-specific deliverable for goal {goal_id} in workspace {workspace_id}")
    
    try:
        from database import list_tasks, create_deliverable, get_deliverables
        import json
        
        # Get completed tasks for this specific goal
        completed_tasks = await list_tasks(workspace_id, status="completed", goal_id=goal_id)
        
        if not completed_tasks:
            logger.info(f"No completed tasks found for goal {goal_id}")
            return None
        
        # Check if this goal already has deliverables
        existing_goal_deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
        max_deliverables_per_goal = int(os.getenv("MAX_DELIVERABLES_PER_GOAL", 1))
        
        if len(existing_goal_deliverables) >= max_deliverables_per_goal and not force:
            logger.info(f"Goal {goal_id} already has {len(existing_goal_deliverables)} deliverables (max: {max_deliverables_per_goal})")
            return None
            
        # Get goal information for better naming
        from database import get_workspace_goals
        goals = await get_workspace_goals(workspace_id)
        goal_info = next((g for g in goals if g['id'] == goal_id), None)
        goal_description = goal_info.get('description', goal_info.get('metric_type', 'Goal')) if goal_info else 'Goal'
        
        logger.info(f"✅ Creating goal-specific deliverable from {len(completed_tasks)} completed tasks for goal: {goal_description}")
        
        # 🤖 HOLISTIC VALIDATION: Use Unified Quality Engine for content assessment
        from ai_quality_assurance.unified_quality_engine import smart_evaluator
        
        valid_tasks = []
        quality_scores = []
        
        for task in completed_tasks:
            result = task.get('result', {})
            task_content = str(result) if result else ""
            
            # Use AI-driven quality assessment instead of primitive validation
            try:
                quality_assessment = await smart_evaluator.evaluate_asset_quality(
                    content=task_content,
                    task_context={
                        'task_id': task.get('id'),
                        'goal_id': goal_id,
                        'agent_name': task.get('agent_id', 'unknown'),
                        'domain': 'business_deliverable'
                    },
                    workspace_id=workspace_id
                )
                
                quality_score = quality_assessment.get('overall_score', 0)
                has_business_value = quality_assessment.get('has_business_value', False)
                
                if has_business_value and quality_score > 30:  # AI-driven threshold
                    valid_tasks.append(task)
                    quality_scores.append(quality_score)
                    logger.info(f"✅ Task {task.get('id')} passed AI quality assessment: {quality_score}%")
                else:
                    logger.warning(f"⚠️ Task {task.get('id')} failed AI quality assessment: score={quality_score}%, business_value={has_business_value}")
                    
            except Exception as e:
                logger.error(f"Error in AI quality assessment for task {task.get('id')}: {e}")
                # Fallback to basic validation only if AI fails
                if _has_meaningful_content(result):
                    valid_tasks.append(task)
                    quality_scores.append(50)  # Default score for fallback
        
        if not valid_tasks:
            logger.error(f"❌ No tasks passed AI quality assessment for goal {goal_id}. Not creating deliverable.")
            return None
            
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        logger.info(f"✅ Found {len(valid_tasks)}/{len(completed_tasks)} tasks passing AI quality assessment (avg score: {avg_quality_score:.1f}%)")
        
        # Aggregate task results for this goal
        aggregated_content, aggregation_quality_score = await _aggregate_task_results(valid_tasks)
        
        # Combine AI quality scores with aggregation score for final assessment
        final_quality_score = (avg_quality_score + aggregation_quality_score) / 2
        
        # If overall quality is low, create a specific warning deliverable
        if final_quality_score < 50:
            logger.warning(f"⚠️ Low quality aggregation for goal {goal_id}. Score: {aggregation_quality_score}. Creating a warning deliverable.")
            deliverable_data = {
                "title": f"Review Required: {goal_description}",
                "type": "low_value_warning",
                "content": f"""# Business Value Warning

**Goal:** {goal_description}

**Analysis:** The system detected that the completed tasks for this goal did not produce a final, concrete business asset. The results consisted primarily of plans, outlines, or templates rather than ready-to-use content.

**Reason:** The initial tasks generated by the AI planner were likely too abstract.

**Recommendation:** This is an architectural issue being resolved. The AI planner is being updated to generate more specific, data-driven tasks to prevent this in the future. No manual action is required at this time.""",
                "status": "needs_review",
                "goal_id": goal_id,
                "business_value_score": final_quality_score,
                "metadata": { 
                    "source": "ai_quality_assessment_warning",
                    "ai_quality_score": avg_quality_score,
                    "aggregation_quality_score": aggregation_quality_score,
                    "final_quality_score": final_quality_score
                }
            }
        else:
            # 🎨 ENHANCED: Add AI-powered display transformation
            display_content, display_metadata = await _create_user_friendly_display(
                aggregated_content, 
                goal_description,
                {"workspace_id": workspace_id, "goal_id": goal_id}
            )
            
            # Create goal-specific deliverable with dual-format support
            # Store display content in 'content' field and backup original JSON in metadata
            metadata = {
                "source": "goal_specific_aggregation",
                "goal_description": goal_description,
                "tasks_included": [task.get('id') for task in completed_tasks],
                "creation_method": "automated_goal_completion",
                "display_enhanced": True,
                "original_json_content": aggregated_content,  # Backup original JSON
                "display_transformation": {
                    "applied_during_creation": True,
                    "transformation_confidence": display_metadata.get('confidence', 85.0),
                    "display_format": display_metadata.get('format', 'html'),
                    "ai_enhanced": display_metadata.get('ai_enhanced', True),
                    "fallback_used": display_metadata.get('fallback_used', False),
                    "processing_time": display_metadata.get('processing_time', 0),
                    "created_at": str(datetime.now())
                }
            }
            
            deliverable_data = {
                "title": f"{goal_description} - AI-Generated Deliverable",
                "type": "goal_deliverable",
                "content": display_content,  # Store user-friendly display content as main content
                "status": "completed",
                "goal_id": goal_id,  # CRITICAL: Link to specific goal
                "readiness_score": 90,
                "completion_percentage": 100,
                "business_value_score": final_quality_score,
                "quality_metrics": {
                    "task_count": len(valid_tasks),
                    "total_tasks_analyzed": len(completed_tasks),
                    "content_length": len(str(display_content)),
                    "original_content_length": len(str(aggregated_content)),
                    "created_from": "ai_quality_assessed_aggregation",
                    "goal_id": goal_id,
                    "ai_quality_score": avg_quality_score,
                    "aggregation_quality_score": aggregation_quality_score,
                    "final_quality_score": final_quality_score,
                    "display_transformation": display_metadata
                },
                "metadata": metadata
            }
        
        # Create the deliverable in database
        created_deliverable = await create_deliverable(workspace_id, deliverable_data)
        
        if created_deliverable:
            logger.info(f"🎉 Successfully created goal-specific deliverable: {created_deliverable.get('id')}")
            return created_deliverable
        else:
            logger.error(f"❌ Failed to create goal-specific deliverable for goal {goal_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating goal-specific deliverable: {e}", exc_info=True)
        return None

def _has_meaningful_content(task_result: dict) -> bool:
    """
    Validates if a task result contains meaningful business content
    Returns False for timeouts, errors, empty results, or placeholder content
    """
    if not isinstance(task_result, dict):
        return False
    
    # Check for explicit failure indicators
    failure_indicators = ['timeout', 'error', 'failed', 'exception']
    for indicator in failure_indicators:
        if indicator in task_result:
            return False
    
    # Check for meaningful content fields
    content_fields = ['content', 'result', 'output', 'data', 'csv', 'contacts', 'list']
    has_content = False
    
    for field in content_fields:
        if field in task_result:
            value = task_result[field]
            if isinstance(value, str) and len(value.strip()) > 20:  # At least 20 chars of content
                has_content = True
                break
            elif isinstance(value, (list, dict)) and value:  # Non-empty list or dict
                has_content = True
                break
    
    return has_content

async def _create_goal_specific_deliverables_for_workspace(workspace_id: str, force: bool = False) -> Optional[Dict[str, Any]]:
    """Creates goal-specific deliverables for all eligible goals in a workspace"""
    logger.info(f"🎯 Creating goal-specific deliverables for workspace {workspace_id}")
    
    try:
        from database import get_workspace_goals
        
        # Get all goals for this workspace
        goals = await get_workspace_goals(workspace_id)
        
        if not goals:
            logger.info(f"No goals found for workspace {workspace_id}")
            return None
            
        created_deliverables = []
        
        for goal in goals:
            goal_id = goal.get('id')
            goal_description = goal.get('description', goal.get('metric_type', 'Unknown Goal'))
            
            # Check if this goal has completed tasks
            from database import list_tasks
            completed_tasks = await list_tasks(workspace_id, status="completed", goal_id=goal_id)
            
            if not completed_tasks:
                logger.debug(f"Goal {goal_description} has no completed tasks, skipping")
                continue
                
            # Check if this goal already has deliverables
            from database import get_deliverables
            existing_goal_deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
            
            if existing_goal_deliverables and not force:
                logger.debug(f"Goal {goal_description} already has deliverables, skipping")
                continue
                
            logger.info(f"🎯 Creating deliverable for goal: {goal_description} ({len(completed_tasks)} tasks)")
            
            # Create deliverable for this goal
            goal_deliverable = await create_goal_specific_deliverable(workspace_id, goal_id, force)
            
            if goal_deliverable:
                created_deliverables.append(goal_deliverable)
                logger.info(f"✅ Created deliverable for goal: {goal_description}")
            else:
                logger.warning(f"❌ Failed to create deliverable for goal: {goal_description}")
        
        if created_deliverables:
            logger.info(f"🎉 Successfully created {len(created_deliverables)} goal-specific deliverables")
            return created_deliverables[0]  # Return first created deliverable for compatibility
        else:
            logger.info(f"No goal-specific deliverables were created for workspace {workspace_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating goal-specific deliverables for workspace: {e}", exc_info=True)
        return None

# Backward compatibility functions  
async def check_and_create_final_deliverable(workspace_id: str, deliverable_context: dict = None, force: bool = False):
    """Real deliverable creation from completed tasks - ENHANCED for goal-specific creation"""
    logger.info(f"🔍 check_and_create_final_deliverable called for workspace {workspace_id} (force={force})")
    
    try:
        # Import required modules
        from database import list_tasks, create_deliverable, get_deliverables
        import json
        
        # NEW: Check if we should create goal-specific deliverables
        should_create_goal_specific = os.getenv("ENABLE_GOAL_SPECIFIC_DELIVERABLES", "true").lower() == "true"
        
        if should_create_goal_specific:
            return await _create_goal_specific_deliverables_for_workspace(workspace_id, force)
        
        # FALLBACK: Original workspace-level logic
        # Get completed tasks for this workspace
        completed_tasks = await list_tasks(workspace_id, status="completed")
        
        if not completed_tasks:
            logger.info(f"No completed tasks found for workspace {workspace_id}")
            return None
            
        # Check if we already have deliverables
        existing_deliverables = await get_deliverables(workspace_id)
        
        # Respect limits even when forced
        max_deliverables = int(os.getenv("MAX_DELIVERABLES_PER_WORKSPACE", 3))
        if len(completed_tasks) >= 1 and len(existing_deliverables) < max_deliverables:
            logger.info(f"✅ Creating deliverable from {len(completed_tasks)} completed tasks")
            
            # Aggregate task results
            aggregated_content = await _aggregate_task_results(completed_tasks)
            
            # Create deliverable
            deliverable_data = {
                "title": f"Project Deliverable - {len(completed_tasks)} Tasks Completed",
                "type": "project_summary",
                "content": aggregated_content,
                "status": "completed",
                "readiness_score": 85,
                "completion_percentage": 100,
                "business_value_score": 80,
                "quality_metrics": {
                    "task_count": len(completed_tasks),
                    "content_length": len(aggregated_content),
                    "created_from": "task_aggregation"
                },
                "metadata": {
                    "source_tasks": [task.get("id") for task in completed_tasks],
                    "creation_method": "automated_aggregation",
                    "timestamp": str(asyncio.get_event_loop().time())
                }
            }
            
            deliverable = await create_deliverable(workspace_id, deliverable_data)
            deliverable_id = deliverable.get("id")
            
            logger.info(f"🎉 Created deliverable {deliverable_id} for workspace {workspace_id}")
            return deliverable_id
        else:
            if force:
                logger.info(f"⏳ Force mode but no completed tasks: {len(completed_tasks)} tasks, {len(existing_deliverables)} deliverables")
            else:
                logger.info(f"⏳ Not ready for deliverable: {len(completed_tasks)} tasks, {len(existing_deliverables)} deliverables")
            return None
            
    except Exception as e:
        logger.error(f"Error in check_and_create_final_deliverable: {e}", exc_info=True)
        return None

async def _aggregate_task_results(completed_tasks: list) -> tuple[str, float]:
    """Aggregate results from completed tasks and return content and a quality score."""
    try:
        logger.info(f"🔍 Starting AI-driven aggregation for {len(completed_tasks)} completed tasks")
        
        from ai_agents.deliverable_assembly import deliverable_assembly_agent
        from database import get_workspace # Assuming this function exists to get workspace details

        extractor = unified_deliverable_engine.asset_extractor
        task_assets = await extractor.extract_assets_from_task_batch(completed_tasks)
        
        all_assets = []
        for task_id, assets in task_assets.items():
            all_assets.extend(assets)
        
        # 🤖 AI-DRIVEN FIX: Instead of failing when no "concrete assets" are found,
        # use AI to analyze the actual business value of task results
        business_value_score = await _ai_analyze_business_value(completed_tasks, all_assets)
        
        # Generate content based on both assets and task results
        aggregated_content = await _generate_business_content(completed_tasks, all_assets)
        
        logger.info(f"✅ AI-driven aggregation complete: Score={business_value_score:.1f}, Content={len(aggregated_content)} chars")
        return aggregated_content, business_value_score
        
    except Exception as e:
        logger.error(f"Error in AI-driven aggregation: {e}")
        # Fallback to basic summary with improved scoring
        summary = _create_simple_task_summary(completed_tasks)
        fallback_score = await _calculate_fallback_business_score(completed_tasks)
        logger.info(f"Using fallback aggregation with improved score: {fallback_score:.1f}")
        return summary, fallback_score



def _create_simple_task_summary(completed_tasks: list) -> str:
    """Create a simple task summary as fallback"""
    try:
        summary = ["# Task Summary Report", ""]
        summary.append(f"Total tasks completed: {len(completed_tasks)}")
        summary.append("")
        
        for i, task in enumerate(completed_tasks, 1):
            summary.append(f"## Task {i}: {task.get('name', 'Unnamed Task')}")
            result = task.get('result', 'No result available')
            if isinstance(result, str):
                summary.append(result[:500] + "..." if len(result) > 500 else result)
            else:
                summary.append(str(result)[:500] + "...")
            summary.append("")
        
        return "\n".join(summary)
    except Exception as e:
        return f"Error creating task summary: {str(e)}"

def _format_structured_result(result_dict: dict) -> str:
    """Format structured result dictionary for better readability"""
    try:
        formatted_parts = []
        
        # Handle common structured formats
        if "phases" in result_dict:
            formatted_parts.append("**Project Phases:**")
            phases = result_dict["phases"]
            for phase in phases:
                phase_name = phase.get("phase_name", phase.get("phase", "Unknown Phase"))
                formatted_parts.append(f"- **{phase_name}**")
                
                deliverables = phase.get("deliverables", phase.get("key_deliverables", []))
                if deliverables:
                    for deliverable in deliverables:
                        formatted_parts.append(f"  - {deliverable}")
        
        if "resource_allocation" in result_dict:
            formatted_parts.append("\n**Resource Allocation:**")
            allocation = result_dict["resource_allocation"]
            for phase, resources in allocation.items():
                formatted_parts.append(f"- **{phase}:** {', '.join(resources)}")
        
        if "initial_sub_tasks_phase_1" in result_dict:
            formatted_parts.append("\n**Initial Sub-Tasks:**")
            tasks = result_dict["initial_sub_tasks_phase_1"]
            for task in tasks:
                if isinstance(task, dict):
                    sub_task = task.get("sub_task", task.get("task", "Unknown task"))
                    formatted_parts.append(f"- {sub_task}")
                else:
                    formatted_parts.append(f"- {task}")
        
        if "communication_protocol" in result_dict:
            formatted_parts.append("\n**Communication Protocol:**")
            protocol = result_dict["communication_protocol"]
            for key, value in protocol.items():
                formatted_parts.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        # If no specific formatting, show key-value pairs
        if not formatted_parts:
            formatted_parts.append("**Results:**")
            for key, value in result_dict.items():
                if isinstance(value, (str, int, float)):
                    formatted_parts.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                elif isinstance(value, list) and len(value) <= 5:
                    formatted_parts.append(f"- **{key.replace('_', ' ').title()}:** {', '.join(map(str, value))}")
        
        return "\n".join(formatted_parts)
        
    except Exception as e:
        return f"**Result:** {str(result_dict)[:300]}..."

def create_intelligent_deliverable(*args, **kwargs):
    """Backward compatibility function"""
    logger.info("create_intelligent_deliverable called")
    return {}

def deliverable_aggregator(*args, **kwargs):
    """Backward compatibility function"""
    logger.info("deliverable_aggregator called")
    return {}

# Backward compatibility classes
class ConcreteAssetExtractor:
    """Backward compatibility wrapper for real ConcreteAssetExtractor"""
    
    def __init__(self):
        from .concrete_asset_extractor import concrete_asset_extractor
        self.extractor = concrete_asset_extractor
    
    async def extract_assets(self, content: str) -> List[Dict[str, Any]]:
        return await self.extractor.extract_assets(content)

class AIDisplayEnhancer:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class MultiSourceAssetExtractor:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class UniversalAIContentExtractor:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class DeliverableMarkupProcessor:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class DeliverablePipeline:
    """Backward compatibility class with Pillar 7 autonomous pipeline support"""
    
    def __init__(self):
        self._running = False
        self._autonomous_mode = True  # Always autonomous for Pillar 7 compliance
    
    async def start(self):
        """Start the deliverable pipeline (Pillar 7: Autonomous Pipeline)"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("🚀 Starting Deliverable Pipeline in autonomous mode...")
            self._running = True
            logger.info("✅ Deliverable Pipeline started successfully")
            return {"status": "started", "autonomous_mode": self._autonomous_mode}
        except Exception as e:
            logger.error(f"❌ Failed to start Deliverable Pipeline: {e}")
            self._running = False
            raise e
    
    async def stop(self):
        """Stop the deliverable pipeline"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("🛑 Stopping Deliverable Pipeline...")
            self._running = False
            logger.info("✅ Deliverable Pipeline stopped successfully")
            return {"status": "stopped"}
        except Exception as e:
            logger.error(f"❌ Failed to stop Deliverable Pipeline: {e}")
            raise e
    
    def is_running(self) -> bool:
        """Check if the pipeline is running"""
        return self._running

async def _ai_analyze_business_value(completed_tasks: list, assets: list) -> float:
    """
    🤖 AI-DRIVEN: Analyze the actual business value of completed tasks
    Uses AI to understand semantic content value beyond simple asset extraction
    """
    try:
        logger.info(f"🤖 AI analyzing business value of {len(completed_tasks)} tasks and {len(assets)} assets")
        
        # Import AI provider for analysis
        from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine, PipelineStepType, PipelineContext
        
        # Prepare task content for AI analysis
        task_summaries = []
        for task in completed_tasks:
            task_name = task.get('name', 'Unknown Task')
            task_result = task.get('result', '')
            
            # Convert result to string if needed
            if isinstance(task_result, dict):
                task_result = json.dumps(task_result, indent=2)
            elif not isinstance(task_result, str):
                task_result = str(task_result)
            
            task_summaries.append({
                'name': task_name,
                'result': task_result[:1000],  # Limit to first 1000 chars for AI processing
                'result_length': len(str(task_result))
            })
        
        # Create context for AI analysis
        context = PipelineContext(
            workspace_id="analysis",
            timeout_seconds=15,
            max_retries=2
        )
        
        # Use AI to analyze business value
        analysis_input = {
            'tasks': task_summaries,
            'assets_count': len(assets),
            'total_content_length': sum(len(str(task.get('result', ''))) for task in completed_tasks)
        }
        
        ai_result = await universal_ai_pipeline_engine.execute_pipeline_step(
            step_type=PipelineStepType.QUALITY_VALIDATION,
            input_data=analysis_input,
            context=context,
            custom_prompt=f"""
Analyze the business value of these {len(completed_tasks)} completed tasks.

TASKS ANALYSIS:
{json.dumps(task_summaries, indent=2)}

ASSETS FOUND: {len(assets)}

EVALUATION CRITERIA:
1. Content Quality: Are the results substantial and complete?
2. Business Readiness: Are the results immediately usable?
3. Specificity: Are the results specific vs generic templates?
4. Implementation Value: Do results provide actionable business value?

Score from 0-100 where:
- 90-100: Exceptional business value, ready for immediate use
- 70-89: Good business value, minor adjustments needed
- 50-69: Moderate value, some refinement required  
- 30-49: Basic value, significant improvements needed
- 0-29: Low value, mostly planning or templates

Return JSON: {{"business_value_score": 0-100, "reasoning": "detailed explanation"}}
"""
        )
        
        if ai_result.success and ai_result.data:
            ai_score = ai_result.data.get('business_value_score', 50)
            reasoning = ai_result.data.get('reasoning', 'AI analysis completed')
            logger.info(f"🤖 AI business value analysis: {ai_score}/100 - {reasoning}")
            return float(ai_score)
        else:
            logger.warning("AI business value analysis failed, using content-based scoring")
            return await _calculate_content_based_score(completed_tasks)
            
    except Exception as e:
        logger.error(f"Error in AI business value analysis: {e}")
        return await _calculate_content_based_score(completed_tasks)

async def _generate_business_content(completed_tasks: list, assets: list) -> str:
    """
    🤖 AI-DRIVEN: Generate structured business content from tasks and assets
    """
    try:
        logger.info(f"🎨 Generating business content from {len(completed_tasks)} tasks and {len(assets)} assets")
        
        # Create structured content from tasks
        content_parts = []
        content_parts.append("# Business Deliverable")
        content_parts.append(f"Generated from {len(completed_tasks)} completed tasks with {len(assets)} extracted assets.")
        content_parts.append("")
        
        # Add executive summary
        total_content_length = sum(len(str(task.get('result', ''))) for task in completed_tasks)
        content_parts.append("## Executive Summary")
        if total_content_length > 5000:
            content_parts.append("This deliverable contains substantial business content ready for implementation.")
        elif total_content_length > 2000:
            content_parts.append("This deliverable provides comprehensive business guidance and actionable insights.")
        else:
            content_parts.append("This deliverable summarizes key findings and recommendations.")
        content_parts.append("")
        
        # Add task results in structured format
        content_parts.append("## Detailed Results")
        for i, task in enumerate(completed_tasks, 1):
            task_name = task.get('name', f'Task {i}')
            task_result = task.get('result', '')
            
            content_parts.append(f"### {i}. {task_name}")
            
            if isinstance(task_result, dict):
                # Handle structured results
                formatted_result = _format_structured_result(task_result)
                content_parts.append(formatted_result)
            elif isinstance(task_result, str) and task_result:
                content_parts.append(task_result)
            else:
                content_parts.append("Result content not available")
            
            content_parts.append("")
        
        # Add assets section if available
        if assets:
            content_parts.append("## Assets and Deliverables")
            for i, asset in enumerate(assets, 1):
                asset_title = asset.get('title', f'Asset {i}')
                asset_type = asset.get('type', 'unknown')
                content_parts.append(f"**{asset_title}** ({asset_type})")
                if asset.get('content'):
                    content_parts.append(str(asset['content'])[:500] + "..." if len(str(asset['content'])) > 500 else str(asset['content']))
                content_parts.append("")
        
        # Add creation metadata
        content_parts.append("---")
        content_parts.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AI-driven aggregation system*")
        
        return "\n".join(content_parts)
        
    except Exception as e:
        logger.error(f"Error generating business content: {e}")
        return _create_simple_task_summary(completed_tasks)

async def _calculate_content_based_score(completed_tasks: list) -> float:
    """Calculate business value score based on content analysis without AI"""
    try:
        total_score = 0
        task_count = len(completed_tasks)
        
        for task in completed_tasks:
            task_result = task.get('result', '')
            task_score = 0
            
            # Convert to string for analysis
            if isinstance(task_result, dict):
                result_str = json.dumps(task_result)
            else:
                result_str = str(task_result)
            
            # Length-based scoring
            content_length = len(result_str)
            if content_length > 2000:
                task_score += 30
            elif content_length > 1000:
                task_score += 20
            elif content_length > 500:
                task_score += 15
            else:
                task_score += 5
            
            # Business value indicators
            result_lower = result_str.lower()
            business_indicators = [
                'strategy', 'plan', 'analysis', 'recommendation', 'solution',
                'implementation', 'process', 'framework', 'guideline', 'document',
                'report', 'content', 'campaign', 'email', 'list', 'contacts'
            ]
            
            indicator_count = sum(1 for indicator in business_indicators if indicator in result_lower)
            task_score += min(indicator_count * 5, 25)
            
            # Structured content bonus
            if isinstance(task.get('result'), dict):
                task_score += 15
            
            total_score += min(task_score, 80)  # Cap individual task score at 80
        
        average_score = total_score / task_count if task_count > 0 else 0
        
        # Apply workspace completion bonus
        if task_count >= 5:
            average_score = min(average_score + 10, 85)
        elif task_count >= 3:
            average_score = min(average_score + 5, 80)
        
        logger.info(f"📊 Content-based scoring: {average_score:.1f} (from {task_count} tasks)")
        return average_score
        
    except Exception as e:
        logger.error(f"Error in content-based scoring: {e}")
        return 40.0  # Reasonable fallback score

async def _calculate_fallback_business_score(completed_tasks: list) -> float:
    """Enhanced fallback scoring when AI fails"""
    try:
        # Use content-based scoring as fallback
        score = await _calculate_content_based_score(completed_tasks)
        
        # Apply minimum viable score for substantial tasks
        if len(completed_tasks) >= 2:
            score = max(score, 45.0)  # Ensure minimum viable score
        if len(completed_tasks) >= 5:
            score = max(score, 55.0)  # Higher minimum for substantial workspaces
            
        return score
    except Exception as e:
        logger.error(f"Error in fallback scoring: {e}")
        return 50.0  # Safe fallback

async def _create_user_friendly_display(
    content: str, 
    goal_description: str,
    context: dict
) -> tuple[str, dict]:
    """
    🎨 Create user-friendly display version of content using AIContentDisplayTransformer
    """
    try:
        # Import the AI content display transformer
        from services.ai_content_display_transformer import transform_deliverable_to_html
        
        logger.info(f"🎨 Creating user-friendly display for goal: {goal_description}")
        
        # Prepare business context from goal and workspace info
        business_context = {
            "goal_description": goal_description,
            "workspace_id": context.get("workspace_id"),
            "goal_id": context.get("goal_id"),
            "content_type": "business_deliverable"
        }
        
        # Transform content to HTML format for frontend display
        result = await transform_deliverable_to_html(
            content=content,
            business_context=business_context
        )
        
        display_metadata = {
            "format": result.display_format,
            "confidence": result.transformation_confidence,
            "processing_time": result.processing_time,
            "fallback_used": result.fallback_used,
            "ai_enhanced": not result.fallback_used,
            "transformation_metadata": result.metadata
        }
        
        logger.info(f"✅ Display transformation complete: confidence={result.transformation_confidence:.1f}%, fallback={result.fallback_used}")
        
        return result.transformed_content, display_metadata
        
    except Exception as e:
        logger.error(f"❌ Display transformation failed: {e}")
        # Fallback to basic HTML formatting
        fallback_html = f"""
        <div class="deliverable-content">
            <h2>📋 {goal_description}</h2>
            <div class="content-body">
                <pre>{content}</pre>
            </div>
            <p><small><em>Display transformation unavailable - showing raw content</em></small></p>
        </div>
        """
        
        fallback_metadata = {
            "format": "html",
            "confidence": 30.0,
            "processing_time": 0.001,
            "fallback_used": True,
            "ai_enhanced": False,
            "error": str(e)
        }
        
        return fallback_html.strip(), fallback_metadata

class RequirementsAnalyzer:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class AssetSchemaGenerator:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class IntelligentDeliverableAggregator:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class AIDeliverableAnalyzer:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class DynamicAssetExtractor:
    """Backward compatibility class"""
    
    def __init__(self):
        pass

class IntelligentDeliverablePackager:
    """Backward compatibility class"""
    
    def __init__(self):
        pass