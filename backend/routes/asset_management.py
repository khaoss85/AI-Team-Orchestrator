from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from deliverable_system.requirements_analyzer import DeliverableRequirementsAnalyzer
from deliverable_system.schema_generator import AssetSchemaGenerator
from database import list_tasks, list_agents
from models import DeliverableRequirements, AssetSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/asset-management", tags=["asset-management"])

@router.get("/workspace/{workspace_id}/requirements", response_model=Dict[str, Any])
async def get_workspace_asset_requirements(workspace_id: UUID):
    """Get asset requirements analysis for a workspace"""
    try:
        analyzer = DeliverableRequirementsAnalyzer()
        requirements = await analyzer.analyze_deliverable_requirements(str(workspace_id))
        
        return {
            "workspace_id": str(workspace_id),
            "deliverable_category": requirements.deliverable_category,
            "primary_assets_needed": [
                {
                    "asset_type": asset.asset_type,
                    "asset_format": asset.asset_format,
                    "actionability_level": asset.actionability_level,
                    "business_impact": asset.business_impact,
                    "priority": asset.priority,
                    "validation_criteria": asset.validation_criteria
                }
                for asset in requirements.primary_assets_needed
            ],
            "deliverable_structure": requirements.deliverable_structure,
            "generated_at": requirements.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting asset requirements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset requirements: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/schemas", response_model=Dict[str, Any])
async def get_workspace_asset_schemas(workspace_id: UUID):
    """Get available asset schemas for a workspace"""
    try:
        analyzer = DeliverableRequirementsAnalyzer()
        schema_generator = AssetSchemaGenerator()
        
        # Get requirements first
        requirements = await analyzer.analyze_deliverable_requirements(str(workspace_id))
        
        # Generate schemas
        asset_schemas = await schema_generator.generate_asset_schemas(requirements)
        
        return {
            "workspace_id": str(workspace_id),
            "available_schemas": {
                name: {
                    "asset_name": schema.asset_name,
                    "schema_definition": schema.schema_definition,
                    "validation_rules": schema.validation_rules,
                    "usage_instructions": schema.usage_instructions,
                    "automation_ready": schema.automation_ready
                }
                for name, schema in asset_schemas.items()
            },
            "schema_count": len(asset_schemas),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting asset schemas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset schemas: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/extraction-status", response_model=Dict[str, Any])
async def get_asset_extraction_status(workspace_id: UUID):
    """Get status of asset extraction from completed tasks"""
    try:
        tasks = await list_tasks(str(workspace_id))
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        # Simulate asset extraction analysis
        extraction_candidates = []
        for task in completed_tasks:
            context_data = task.get("context_data", {}) or {}
            result = task.get("result", {}) or {}
            
            if isinstance(context_data, dict):
                if (context_data.get("asset_production") or 
                    context_data.get("asset_oriented_task")):
                    
                    # Check if has structured output
                    detailed_json = result.get("detailed_results_json", "")
                    has_structured_output = bool(detailed_json and len(detailed_json) > 100)
                    
                    extraction_candidates.append({
                        "task_id": task.get("id"),
                        "task_name": task.get("name"),
                        "asset_type": context_data.get("asset_type") or context_data.get("detected_asset_type"),
                        "has_structured_output": has_structured_output,
                        "output_size": len(detailed_json) if detailed_json else 0,
                        "extraction_ready": has_structured_output,
                        "completed_at": task.get("updated_at")
                    })
        
        return {
            "workspace_id": str(workspace_id),
            "extraction_summary": {
                "total_completed_tasks": len(completed_tasks),
                "asset_production_tasks": len(extraction_candidates),
                "extraction_ready_tasks": len([c for c in extraction_candidates if c["extraction_ready"]]),
                "extraction_readiness_rate": (
                    len([c for c in extraction_candidates if c["extraction_ready"]]) / 
                    len(extraction_candidates)
                ) * 100 if extraction_candidates else 0
            },
            "extraction_candidates": extraction_candidates,
            "next_steps": [
                "Run asset extraction on ready tasks",
                "Create final deliverable with extracted assets"
            ] if extraction_candidates else ["Complete more asset production tasks"],
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting extraction status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction status: {str(e)}"
        )
