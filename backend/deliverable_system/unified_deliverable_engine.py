# backend/deliverable_system/unified_deliverable_engine.py
"""
Unified Deliverable Engine - Enhanced with Real Asset Extraction
"""

import asyncio
import logging
import json
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

# Backward compatibility functions
async def check_and_create_final_deliverable(workspace_id: str, deliverable_context: dict = None, force: bool = False):
    """Real deliverable creation from completed tasks"""
    logger.info(f"🔍 check_and_create_final_deliverable called for workspace {workspace_id} (force={force})")
    
    try:
        # Import required modules
        from database import list_tasks, create_deliverable, get_deliverables
        import json
        
        # Get completed tasks for this workspace
        completed_tasks = await list_tasks(workspace_id, status="completed")
        
        if not completed_tasks:
            logger.info(f"No completed tasks found for workspace {workspace_id}")
            return None
            
        # Check if we already have deliverables
        existing_deliverables = await get_deliverables(workspace_id)
        
        # Only create if we have enough tasks and not too many deliverables (unless forced)
        if len(completed_tasks) >= 1 and (force or len(existing_deliverables) < 3):
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

async def _aggregate_task_results(completed_tasks: list) -> str:
    """Aggregate results from completed tasks into a coherent deliverable using intelligent aggregation"""
    try:
        # Extract assets from all completed tasks
        logger.info(f"🔍 Starting intelligent aggregation for {len(completed_tasks)} completed tasks")
        
        # Use the asset extractor to get real assets from each task
        extractor = unified_deliverable_engine.asset_extractor
        task_assets = await extractor.extract_assets_from_task_batch(completed_tasks)
        
        # Flatten all assets into a single list
        all_assets = []
        for task_id, assets in task_assets.items():
            all_assets.extend(assets)
        
        # Get workspace context (if available from first task)
        workspace_context = {
            'workspace_id': completed_tasks[0].get('workspace_id') if completed_tasks else None,
            'project_name': 'AI Team Orchestrator Project',
            'domain': 'Software Development'
        }
        
        # Use intelligent aggregator to create deliverable
        aggregator = unified_deliverable_engine.aggregator
        deliverable_result = await aggregator.aggregate_assets_to_deliverable(
            assets=all_assets,
            context=workspace_context,
            goal_info=None  # Could be enhanced to pass actual goal info
        )
        
        # Extract the aggregated content
        if deliverable_result.get('status') == 'completed':
            logger.info(f"✅ Intelligent aggregation completed with quality score: {deliverable_result.get('quality_metrics', {}).get('overall_score', 0):.2f}")
            return deliverable_result.get('content', '')
        else:
            # If aggregation had issues, return structured error info
            return f"# Deliverable Generation Report\n\nStatus: {deliverable_result.get('status')}\n\n{deliverable_result.get('content', 'No content generated')}"
        
    except Exception as e:
        logger.error(f"Error in intelligent aggregation: {e}")
        # Fallback to simple task summary
        return _create_simple_task_summary(completed_tasks)

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