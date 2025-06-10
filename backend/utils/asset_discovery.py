"""
Enhanced asset discovery utilities that match frontend extraction logic
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def discover_assets_from_tasks(tasks: List[Dict]) -> Dict[str, Any]:
    """
    Comprehensive asset discovery that matches frontend logic
    """
    extracted_assets = {}
    asset_tasks = []
    completed_asset_tasks = []
    pending_asset_tasks = []
    
    logger.info(f"🔍 Starting asset discovery from {len(tasks)} tasks")
    
    for task in tasks:
        context_data = task.get("context_data", {}) or {}
        result = task.get("result", {}) or {}
        task_name = task.get("name", "")
        task_status = task.get("status", "")
        
        # Track if this task produces assets
        is_asset_task = False
        task_assets = {}
        
        # 1. Check for dual output format in completed tasks
        if task_status == "completed" and result.get("detailed_results_json"):
            try:
                detailed = result["detailed_results_json"]
                if isinstance(detailed, str):
                    detailed = json.loads(detailed)
                
                if detailed.get("structured_content"):
                    # Create asset from structured content
                    import re
                    asset_name = re.sub(r'[^a-z0-9_]', '', task_name.lower().replace(' ', '_'))
                    asset_data = {
                        "structured_content": detailed.get("structured_content"),
                        "rendered_html": detailed.get("rendered_html"),
                        "visual_summary": detailed.get("visual_summary"),
                        "actionable_insights": detailed.get("actionable_insights")
                    }
                    
                    task_assets[asset_name] = {
                        "asset_name": asset_name,
                        "asset_data": asset_data,
                        "source_task_id": task.get("id"),
                        "extraction_method": "dual_output_extraction",
                        "validation_score": 0.95,
                        "actionability_score": 0.9,
                        "ready_to_use": True,
                        "usage_instructions": detailed.get("visual_summary", "AI-generated business asset")
                    }
                    is_asset_task = True
                    
            except Exception as e:
                logger.debug(f"Error parsing detailed_results_json: {e}")
        
        # 2. Check context_data for precomputed deliverables
        if isinstance(context_data, dict):
            # Primary location: precomputed_deliverable.actionable_assets
            if context_data.get("precomputed_deliverable", {}).get("actionable_assets"):
                assets = context_data["precomputed_deliverable"]["actionable_assets"]
                for key, asset in assets.items():
                    if asset and isinstance(asset, dict):
                        task_assets[key] = {
                            **asset,
                            "source_task_id": task.get("id"),
                            "extraction_method": "precomputed_deliverable"
                        }
                        is_asset_task = True
            
            # Secondary location: direct actionable_assets
            if context_data.get("actionable_assets"):
                task_assets.update(context_data["actionable_assets"])
                is_asset_task = True
            
            # Check for final deliverable flags
            if (context_data.get("is_final_deliverable") or 
                context_data.get("deliverable_aggregation")):
                is_asset_task = True
            
            # Original detection criteria
            if (context_data.get("asset_production") or 
                context_data.get("asset_oriented_task") or
                "PRODUCE ASSET:" in task_name.upper()):
                is_asset_task = True
        
        # 3. Check result for actionable_assets
        if result.get("actionable_assets"):
            task_assets.update(result["actionable_assets"])
            is_asset_task = True
        
        # Add discovered assets to main collection
        extracted_assets.update(task_assets)
        
        # Track asset task information
        if is_asset_task:
            asset_info = {
                "task_id": task.get("id"),
                "task_name": task_name,
                "asset_type": _detect_asset_type(task_name, context_data),
                "status": task_status,
                "agent_role": task.get("assigned_to_role"),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "assets_count": len(task_assets)
            }
            
            asset_tasks.append(asset_info)
            
            if task_status == "completed":
                completed_asset_tasks.append(asset_info)
            elif task_status in ["pending", "in_progress"]:
                pending_asset_tasks.append(asset_info)
    
    # Calculate statistics
    total_assets = len(asset_tasks)
    completion_rate = len(completed_asset_tasks) / total_assets if total_assets > 0 else 0
    
    # Asset types breakdown
    asset_types = {}
    for task in asset_tasks:
        asset_type = task.get("asset_type", "unknown")
        if asset_type not in asset_types:
            asset_types[asset_type] = {"total": 0, "completed": 0}
        asset_types[asset_type]["total"] += 1
        if task.get("status") == "completed":
            asset_types[asset_type]["completed"] += 1
    
    logger.info(f"✅ Asset discovery complete: {len(extracted_assets)} assets, {total_assets} asset tasks")
    
    return {
        "extracted_assets": extracted_assets,
        "asset_summary": {
            "total_asset_tasks": total_assets,
            "completed_asset_tasks": len(completed_asset_tasks),
            "pending_asset_tasks": len(pending_asset_tasks),
            "completion_rate": round(completion_rate * 100, 1),
            "deliverable_ready": completion_rate >= 0.7,
            "total_assets_found": len(extracted_assets)
        },
        "asset_types_breakdown": asset_types,
        "completed_assets": completed_asset_tasks,
        "pending_assets": pending_asset_tasks,
        "analysis_timestamp": datetime.now().isoformat()
    }

def _detect_asset_type(task_name: str, context_data: Dict) -> str:
    """Detect asset type from task name and context"""
    # Check context data first
    if isinstance(context_data, dict):
        if context_data.get("detected_asset_type"):
            return context_data["detected_asset_type"]
        if context_data.get("asset_type"):
            return context_data["asset_type"]
    
    # Infer from task name
    name_lower = task_name.lower()
    if "strategy" in name_lower or "plan" in name_lower:
        return "strategy_document"
    elif "analysis" in name_lower or "research" in name_lower:
        return "analysis_report"
    elif "calendar" in name_lower:
        return "content_calendar"
    elif "content" in name_lower and "strategy" in name_lower:
        return "content_strategy"
    elif "budget" in name_lower or "financial" in name_lower:
        return "financial_document"
    elif "report" in name_lower or "document" in name_lower:
        return "business_document"
    else:
        return "business_asset"