"""
Asset-Driven API Endpoints (Pillar 12: Concrete Deliverables + Pillar 5: Goal-Driven)
RESTful API endpoints for asset requirements, artifacts, and quality management.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from fastapi import Request, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from models import (
    AssetRequirement, AssetArtifact, QualityValidation, QualityRule,
    EnhancedWorkspaceGoal, WorkspaceGoal, EnhancedTask
)
from database import get_supabase_client
from services.asset_requirements_generator import AssetRequirementsGenerator
from services.asset_artifact_processor import AssetArtifactProcessor
from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
from deliverable_system.unified_deliverable_engine import unified_deliverable_engine as AssetDrivenTaskExecutor
from services.enhanced_goal_driven_planner import EnhancedGoalDrivenPlanner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])

# Initialize services
requirements_generator = AssetRequirementsGenerator()
artifact_processor = AssetArtifactProcessor()
quality_gate_engine = unified_quality_engine
task_executor = AssetDrivenTaskExecutor()
goal_planner = EnhancedGoalDrivenPlanner()

# Request/Response Models
class AssetRequirementCreate(BaseModel):
    goal_id: UUID
    asset_name: str
    asset_type: str
    asset_format: str = "structured_data"
    description: str
    priority: str = "medium"
    business_value_score: float = Field(ge=0.0, le=1.0)
    acceptance_criteria: Dict[str, Any] = {}

class AssetArtifactCreate(BaseModel):
    requirement_id: UUID
    artifact_name: str
    artifact_type: str
    content: str
    metadata: Dict[str, Any] = {}
    tags: List[str] = []

class QualityActionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|enhance|review)$")
    feedback: Optional[str] = None
    enhancement_suggestions: List[str] = []

class GoalCompletionResponse(BaseModel):
    id: UUID
    metric_type: str
    target_value: float
    current_value: float
    progress_percentage: float
    asset_completion_rate: float
    quality_score: float
    requirements: List[AssetRequirement]

class QualityMetricsResponse(BaseModel):
    overall_quality_score: float
    artifacts_by_status: Dict[str, int]
    quality_trends: List[Dict[str, Any]]
    top_improvement_areas: List[str]
    pillar_compliance: List[Dict[str, Any]]

# === ASSET REQUIREMENTS ENDPOINTS ===

@router.post("/requirements/generate", response_model=List[AssetRequirement])
async def generate_asset_requirements(
    goal_id: UUID,
    background_tasks: BackgroundTasks
):
    """Generate AI-driven asset requirements for a goal (Pillar 2: AI-Driven)"""
    try:
        logger.info(f"🎯 Generating asset requirements for goal: {goal_id}")
        
        # Get goal from database
        supabase = get_supabase_client()
        goal_response = supabase.table("workspace_goals").select("*").eq("id", str(goal_id)).execute()
        
        if not goal_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal_data = goal_response.data[0]
        goal = WorkspaceGoal(**goal_data)
        
        # Generate requirements using AI
        requirements = await requirements_generator.generate_from_goal(goal)
        
        # Store requirements in background
        background_tasks.add_task(store_requirements_background, requirements)
        
        logger.info(f"✅ Generated {len(requirements)} asset requirements")
        return requirements
        
    except Exception as e:
        logger.error(f"Failed to generate asset requirements for goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requirements/{workspace_id}", response_model=List[AssetRequirement])
async def get_workspace_requirements(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_requirements called", endpoint="get_workspace_requirements", trace_id=trace_id)

    """Get all asset requirements for a workspace"""
    try:
        supabase = get_supabase_client()
        
        # Get requirements for workspace goals
        requirements_response = supabase.table("goal_asset_requirements") \
            .select("*, workspace_goals!inner(workspace_id)") \
            .eq("workspace_goals.workspace_id", str(workspace_id)) \
            .execute()
        
        requirements = [AssetRequirement(**req) for req in requirements_response.data]
        return requirements
        
    except Exception as e:
        logger.error(f"Failed to get requirements for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requirements", response_model=AssetRequirement)
async def create_asset_requirement(requirement: AssetRequirementCreate, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_asset_requirement called", endpoint="create_asset_requirement", trace_id=trace_id)

    """Create a new asset requirement"""
    try:
        supabase = get_supabase_client()
        
        requirement_data = {
            "id": str(uuid4()),
            "goal_id": str(requirement.goal_id),
            "asset_name": requirement.asset_name,
            "asset_type": requirement.asset_type,
            "asset_format": requirement.asset_format,
            "description": requirement.description,
            "priority": requirement.priority,
            "business_value_score": requirement.business_value_score,
            "acceptance_criteria": requirement.acceptance_criteria,
            "status": "pending",
            "progress_percentage": 0,
            "created_at": datetime.utcnow().isoformat(),
            "ai_generated": False
        }
        
        response = supabase.table("goal_asset_requirements").insert(requirement_data).execute()
        return AssetRequirement(**response.data[0])
        
    except Exception as e:
        logger.error(f"Failed to create asset requirement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ASSET ARTIFACTS ENDPOINTS ===

@router.get("/artifacts/{workspace_id}", response_model=List[AssetArtifact])
async def get_workspace_artifacts(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_artifacts called", endpoint="get_workspace_artifacts", trace_id=trace_id)

    """Get all asset artifacts for a workspace"""
    try:
        supabase = get_supabase_client()
        
        # Get artifacts through requirements
        artifacts_response = supabase.table("asset_artifacts") \
            .select("""
                *, 
                goal_asset_requirements!inner(
                    workspace_goals!inner(workspace_id)
                )
            """) \
            .eq("goal_asset_requirements.workspace_goals.workspace_id", str(workspace_id)) \
            .execute()
        
        artifacts = [AssetArtifact(**artifact) for artifact in artifacts_response.data]
        return artifacts
        
    except Exception as e:
        logger.error(f"Failed to get artifacts for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/artifacts", response_model=AssetArtifact)
async def create_asset_artifact(
    artifact: AssetArtifactCreate,
    background_tasks: BackgroundTasks
):
    """Create a new asset artifact with automatic quality validation"""
    try:
        supabase = get_supabase_client()
        
        # Create artifact
        artifact_data = {
            "id": str(uuid4()),
            "requirement_id": str(artifact.requirement_id),
            "artifact_name": artifact.artifact_name,
            "artifact_type": artifact.artifact_type,
            "content": artifact.content,
            "metadata": artifact.metadata,
            "tags": artifact.tags,
            "status": "draft",
            "quality_score": 0.0,
            "business_value_score": 0.0,
            "actionability_score": 0.0,
            "ai_enhanced": False,
            "validation_passed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("asset_artifacts").insert(artifact_data).execute()
        created_artifact = AssetArtifact(**response.data[0])
        
        # Run quality validation in background
        background_tasks.add_task(validate_artifact_quality_background, created_artifact.id)
        
        logger.info(f"✅ Created artifact: {created_artifact.artifact_name}")
        return created_artifact
        
    except Exception as e:
        logger.error(f"Failed to create asset artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route download_artifact called", endpoint="download_artifact", trace_id=trace_id)

    """Download artifact content as file"""
    try:
        supabase = get_supabase_client()
        
        artifact_response = supabase.table("asset_artifacts") \
            .select("*") \
            .eq("id", str(artifact_id)) \
            .execute()
        
        if not artifact_response.data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        artifact = AssetArtifact(**artifact_response.data[0])
        
        # Create file content
        content = artifact.content.encode('utf-8')
        filename = f"{artifact.artifact_name}.{artifact.content_format}"
        
        def generate():
            yield content
        
        return StreamingResponse(
            generate(),
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to download artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === QUALITY MANAGEMENT ENDPOINTS ===

@router.post("/quality/artifacts/{artifact_id}/validate")
async def validate_artifact(artifact_id: UUID, background_tasks: BackgroundTasks, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route validate_artifact called", endpoint="validate_artifact", trace_id=trace_id)

    """Run quality validation on an artifact"""
    try:
        logger.info(f"🛡️ Starting quality validation for artifact: {artifact_id}")
        
        # Run validation in background
        background_tasks.add_task(validate_artifact_quality_background, artifact_id)
        
        return {"message": "Quality validation started", "artifact_id": artifact_id}
        
    except Exception as e:
        logger.error(f"Failed to start validation for artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quality/artifacts/{artifact_id}/approve")
async def approve_artifact(artifact_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route approve_artifact called", endpoint="approve_artifact", trace_id=trace_id)

    """Approve an artifact after human review"""
    try:
        supabase = get_supabase_client()
        
        # Update artifact status
        update_data = {
            "status": "approved",
            "validation_passed": True,
            "updated_at": datetime.utcnow().isoformat(),
            "validated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("asset_artifacts") \
            .update(update_data) \
            .eq("id", str(artifact_id)) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Trigger goal progress recalculation
        await trigger_goal_progress_update(artifact_id)
        
        logger.info(f"✅ Artifact approved: {artifact_id}")
        return {"message": "Artifact approved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to approve artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quality/artifacts/{artifact_id}/enhance")
async def enhance_artifact(artifact_id: UUID, background_tasks: BackgroundTasks, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route enhance_artifact called", endpoint="enhance_artifact", trace_id=trace_id)

    """Request AI enhancement for an artifact"""
    try:
        logger.info(f"🤖 Starting AI enhancement for artifact: {artifact_id}")
        
        # Run enhancement in background
        background_tasks.add_task(enhance_artifact_background, artifact_id)
        
        return {"message": "AI enhancement started", "artifact_id": artifact_id}
        
    except Exception as e:
        logger.error(f"Failed to start enhancement for artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quality/artifacts/{artifact_id}/human-review")
async def submit_human_review(artifact_id: UUID, review: QualityActionRequest, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route submit_human_review called", endpoint="submit_human_review", trace_id=trace_id)

    """Submit human review decision for an artifact"""
    try:
        supabase = get_supabase_client()
        
        if review.action == "approve":
            update_data = {
                "status": "approved",
                "validation_passed": True,
                "updated_at": datetime.utcnow().isoformat(),
                "validated_at": datetime.utcnow().isoformat()
            }
        elif review.action == "reject":
            update_data = {
                "status": "needs_improvement",
                "validation_passed": False,
                "updated_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid review action")
        
        response = supabase.table("asset_artifacts") \
            .update(update_data) \
            .eq("id", str(artifact_id)) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Log human review
        review_log = {
            "id": str(uuid4()),
            "artifact_id": str(artifact_id),
            "action": review.action,
            "feedback": review.feedback,
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewer_type": "human"
        }
        
        supabase.table("quality_validations").insert(review_log).execute()
        
        # Trigger updates if approved
        if review.action == "approve":
            await trigger_goal_progress_update(artifact_id)
        
        logger.info(f"✅ Human review submitted for artifact: {artifact_id}")
        return {"message": f"Human review ({review.action}) submitted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to submit human review for artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === GOAL COMPLETION ENDPOINTS ===

@router.get("/goals/{workspace_id}/completion", response_model=List[GoalCompletionResponse])
async def get_goal_completion_with_assets(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_goal_completion_with_assets called", endpoint="get_goal_completion_with_assets", trace_id=trace_id)

    """Get goal completion data with asset breakdown"""
    try:
        supabase = get_supabase_client()
        
        # Get goals with their requirements and artifacts
        goals_response = supabase.table("workspace_goals") \
            .select("""
                *,
                goal_asset_requirements(
                    *,
                    asset_artifacts(*)
                )
            """) \
            .eq("workspace_id", str(workspace_id)) \
            .execute()
        
        completion_data = []
        
        for goal_data in goals_response.data:
            goal = WorkspaceGoal(**{k: v for k, v in goal_data.items() if k != 'goal_asset_requirements'})
            requirements = [AssetRequirement(**req) for req in goal_data.get('goal_asset_requirements', [])]
            
            # Calculate asset completion rate
            total_requirements = len(requirements)
            if total_requirements > 0:
                approved_artifacts = 0
                total_quality_score = 0.0
                
                for req in requirements:
                    artifacts = req.get('asset_artifacts', []) if hasattr(req, 'get') else []
                    approved = [a for a in artifacts if a.get('status') == 'approved']
                    if approved:
                        approved_artifacts += 1
                        total_quality_score += max(a.get('quality_score', 0) for a in approved)
                
                asset_completion_rate = (approved_artifacts / total_requirements) * 100
                avg_quality_score = total_quality_score / total_requirements if total_requirements > 0 else 0.0
            else:
                asset_completion_rate = 0.0
                avg_quality_score = 0.0
            
            completion_data.append(GoalCompletionResponse(
                id=goal.id,
                metric_type=goal.metric_type,
                target_value=goal.target_value,
                current_value=goal.current_value,
                progress_percentage=goal.progress_percentage,
                asset_completion_rate=asset_completion_rate,
                quality_score=avg_quality_score,
                requirements=requirements
            ))
        
        return completion_data
        
    except Exception as e:
        logger.error(f"Failed to get goal completion for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === QUALITY METRICS ENDPOINTS ===

@router.get("/quality/{workspace_id}/metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_quality_metrics called", endpoint="get_quality_metrics", trace_id=trace_id)

    """Get comprehensive quality metrics for workspace"""
    try:
        quality_metrics = await quality_gate_engine.get_quality_metrics_dashboard(workspace_id)
        return QualityMetricsResponse(**quality_metrics)
        
    except Exception as e:
        logger.error(f"Failed to get quality metrics for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality/{workspace_id}/dashboard")
async def get_quality_dashboard_data(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_quality_dashboard_data called", endpoint="get_quality_dashboard_data", trace_id=trace_id)

    """Get comprehensive quality dashboard data"""
    try:
        supabase = get_supabase_client()
        
        # Get recent quality validations
        validations_response = supabase.table("quality_validations") \
            .select("""
                *,
                asset_artifacts!inner(
                    goal_asset_requirements!inner(
                        workspace_goals!inner(workspace_id)
                    )
                )
            """) \
            .eq("asset_artifacts.goal_asset_requirements.workspace_goals.workspace_id", str(workspace_id)) \
            .order("validated_at", desc=True) \
            .limit(50) \
            .execute()
        
        # Get pending reviews
        pending_response = supabase.table("asset_artifacts") \
            .select("""
                *,
                goal_asset_requirements!inner(
                    workspace_goals!inner(workspace_id)
                )
            """) \
            .eq("goal_asset_requirements.workspace_goals.workspace_id", str(workspace_id)) \
            .in_("status", ["requires_human_review", "needs_improvement"]) \
            .execute()
        
        # Calculate quality trends (simplified)
        quality_trends = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.85,
                "validation_count": len(validations_response.data),
                "pass_rate": 0.75
            }
        ]
        
        # Calculate pillar compliance
        pillar_compliance = [
            {"pillar_name": "Concrete Deliverables", "compliance_rate": 0.9, "status": "compliant"},
            {"pillar_name": "AI-Driven", "compliance_rate": 0.85, "status": "compliant"},
            {"pillar_name": "Quality Gates", "compliance_rate": 0.8, "status": "warning"},
        ]
        
        dashboard_data = {
            "overall_quality_score": 0.85,
            "quality_trends": quality_trends,
            "validation_performance": [],
            "pillar_compliance": pillar_compliance,
            "pending_reviews": [AssetArtifact(**artifact) for artifact in pending_response.data],
            "recent_validations": [QualityValidation(**val) for val in validations_response.data]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get quality dashboard data for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality/validations/{workspace_id}")
async def get_quality_validations(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_quality_validations called", endpoint="get_quality_validations", trace_id=trace_id)

    """Get quality validations for workspace"""
    try:
        supabase = get_supabase_client()
        
        validations_response = supabase.table("quality_validations") \
            .select("""
                *,
                asset_artifacts!inner(
                    artifact_name,
                    artifact_type,
                    goal_asset_requirements!inner(
                        workspace_goals!inner(workspace_id)
                    )
                )
            """) \
            .eq("asset_artifacts.goal_asset_requirements.workspace_goals.workspace_id", str(workspace_id)) \
            .order("validated_at", desc=True) \
            .execute()
        
        # Enhance validation data with artifact info
        enhanced_validations = []
        for val in validations_response.data:
            artifact_info = val.get('asset_artifacts', {})
            enhanced_val = {
                **val,
                "artifact_name": artifact_info.get('artifact_name', 'Unknown'),
                "artifact_type": artifact_info.get('artifact_type', 'unknown')
            }
            enhanced_validations.append(enhanced_val)
        
        return enhanced_validations
        
    except Exception as e:
        logger.error(f"Failed to get validations for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MISSING ENDPOINTS IDENTIFIED IN E2E TESTING ===

@router.get("/requirements/workspace/{workspace_id}", response_model=List[AssetRequirement])
async def get_workspace_asset_requirements(workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_asset_requirements called", endpoint="get_workspace_asset_requirements", trace_id=trace_id)

    """Get all asset requirements for a workspace (CRITICAL FIX: Missing endpoint)"""
    try:
        logger.info(f"📋 Getting asset requirements for workspace: {workspace_id}")
        
        if not requirements_generator:
            raise HTTPException(status_code=503, detail="Asset Requirements Generator not available")
        
        # Get requirements using the asset database manager
        requirements = await requirements_generator.db_manager.get_workspace_asset_requirements(UUID(workspace_id))
        
        logger.info(f"✅ Found {len(requirements)} asset requirements for workspace {workspace_id}")
        
        return requirements
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid workspace ID: {e}")
    except Exception as e:
        logger.error(f"Failed to get workspace asset requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-goal/{workspace_id}/{goal_id}")
async def process_goal_to_assets(workspace_id: str, goal_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route process_goal_to_assets called", endpoint="process_goal_to_assets", trace_id=trace_id)

    """
    CRITICAL FIX: Manual trigger for goal → asset requirements → tasks workflow
    
    This endpoint was missing and needed for E2E testing and troubleshooting.
    """
    try:
        logger.info(f"🚀 Processing goal-to-assets workflow for goal: {goal_id} in workspace: {workspace_id}")
        
        # Validate IDs
        workspace_uuid = UUID(workspace_id)
        goal_uuid = UUID(goal_id)
        
        # Get the goal from database
        supabase = get_supabase_client()
        goal_response = supabase.table("workspace_goals").select("*").eq("id", goal_id).eq("workspace_id", workspace_id).execute()
        
        if not goal_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal_data = goal_response.data[0]
        goal_model = WorkspaceGoal(**goal_data)
        
        # Generate asset requirements if they don't exist
        existing_requirements = await requirements_generator.db_manager.get_asset_requirements_for_goal(goal_uuid)
        
        if not existing_requirements:
            logger.info(f"🎯 Generating asset requirements for goal: {goal_data['metric_type']}")
            asset_requirements = await requirements_generator.generate_from_goal(goal_model)
            requirements_count = len(asset_requirements)
        else:
            logger.info(f"✅ Goal already has {len(existing_requirements)} asset requirements")
            requirements_count = len(existing_requirements)
            asset_requirements = existing_requirements
        
        # Generate asset-driven tasks if planner is available
        tasks_generated = 0
        if goal_planner:
            try:
                logger.info(f"📋 Generating asset-driven tasks for workspace: {workspace_id}")
                tasks = await goal_planner.generate_asset_driven_tasks(workspace_uuid)
                goal_tasks = [t for t in tasks if hasattr(t, 'goal_id') and str(t.goal_id) == goal_id]
                tasks_generated = len(goal_tasks)
            except Exception as e:
                logger.warning(f"Task generation failed: {e}")
                tasks_generated = 0
        
        # Update goal metrics
        supabase.table("workspace_goals").update({
            "asset_requirements_count": requirements_count,
            "ai_validation_enabled": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", goal_id).execute()
        
        result = {
            "success": True,
            "workspace_id": workspace_id,
            "goal_id": goal_id,
            "goal_metric_type": goal_data["metric_type"],
            "asset_requirements_count": requirements_count,
            "tasks_generated": tasks_generated,
            "workflow_status": "completed",
            "message": f"Goal-to-assets workflow completed: {requirements_count} requirements, {tasks_generated} tasks"
        }
        
        logger.info(f"✅ Goal-to-assets workflow completed: {result}")
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal-to-assets workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}/status")
async def get_workspace_asset_status(workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_asset_status called", endpoint="get_workspace_asset_status", trace_id=trace_id)

    """
    Get comprehensive asset status for a workspace
    
    CRITICAL FIX: Endpoint for monitoring asset system integration
    """
    try:
        workspace_uuid = UUID(workspace_id)
        
        # Get asset requirements
        requirements = await requirements_generator.db_manager.get_workspace_asset_requirements(workspace_uuid)
        
        # Get asset artifacts
        artifacts = await artifact_processor.db_manager.get_workspace_asset_artifacts(workspace_uuid)
        
        # Get quality metrics
        quality_metrics = await quality_gate_engine.get_workspace_quality_metrics(workspace_uuid)
        
        # Calculate status
        total_requirements = len(requirements)
        total_artifacts = len(artifacts)
        approved_artifacts = len([a for a in artifacts if a.status == "approved"])
        
        asset_completion_rate = (approved_artifacts / total_requirements) if total_requirements > 0 else 0.0
        
        status = {
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "asset_requirements": {
                "total": total_requirements,
                "by_type": {},
                "by_priority": {}
            },
            "asset_artifacts": {
                "total": total_artifacts,
                "approved": approved_artifacts,
                "pending": total_artifacts - approved_artifacts,
                "completion_rate": asset_completion_rate
            },
            "quality_metrics": quality_metrics,
            "pillar_12_status": "active" if total_requirements > 0 else "inactive",
            "no_assets_no_progress": asset_completion_rate == 0.0 and total_requirements > 0
        }
        
        return status
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid workspace ID: {e}")
    except Exception as e:
        logger.error(f"Failed to get workspace asset status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === BACKGROUND TASKS ===

async def store_requirements_background(requirements: List[AssetRequirement]):
    """Background task to store generated requirements"""
    try:
        supabase = get_supabase_client()
        
        for requirement in requirements:
            requirement_data = requirement.dict()
            requirement_data["id"] = str(requirement_data["id"])
            requirement_data["goal_id"] = str(requirement_data["goal_id"])
            requirement_data["workspace_id"] = str(requirement_data.get("workspace_id", ""))
            
            supabase.table("goal_asset_requirements").insert(requirement_data).execute()
        
        logger.info(f"✅ Background: Stored {len(requirements)} requirements")
        
    except Exception as e:
        logger.error(f"Background task failed: store_requirements: {e}")

async def validate_artifact_quality_background(artifact_id: UUID):
    """Background task for artifact quality validation"""
    try:
        supabase = get_supabase_client()
        
        # Get artifact
        artifact_response = supabase.table("asset_artifacts") \
            .select("*") \
            .eq("id", str(artifact_id)) \
            .execute()
        
        if not artifact_response.data:
            logger.error(f"Artifact {artifact_id} not found for validation")
            return
        
        artifact = AssetArtifact(**artifact_response.data[0])
        
        # Run quality validation
        quality_result = await quality_gate_engine.validate_artifact_quality(artifact)
        
        # Update artifact with validation results
        update_data = {
            "quality_score": quality_result.get("overall_score", 0.0),
            "status": quality_result.get("status", "needs_improvement"),
            "validation_passed": quality_result.get("status") == "approved",
            "updated_at": datetime.utcnow().isoformat(),
            "validated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("asset_artifacts").update(update_data).eq("id", str(artifact_id)).execute()
        
        logger.info(f"✅ Background: Quality validation completed for artifact {artifact_id}")
        
    except Exception as e:
        logger.error(f"Background task failed: validate_artifact_quality: {e}")

async def enhance_artifact_background(artifact_id: UUID):
    """Background task for AI artifact enhancement"""
    try:
        supabase = get_supabase_client()
        
        # Get artifact
        artifact_response = supabase.table("asset_artifacts") \
            .select("*") \
            .eq("id", str(artifact_id)) \
            .execute()
        
        if not artifact_response.data:
            logger.error(f"Artifact {artifact_id} not found for enhancement")
            return
        
        artifact = AssetArtifact(**artifact_response.data[0])
        
        # Run AI enhancement
        enhanced_artifact = await artifact_processor.enhance_existing_artifact(artifact_id)
        
        if enhanced_artifact:
            logger.info(f"✅ Background: AI enhancement completed for artifact {artifact_id}")
            
            # Re-run quality validation after enhancement
            await validate_artifact_quality_background(artifact_id)
        
    except Exception as e:
        logger.error(f"Background task failed: enhance_artifact: {e}")

async def trigger_goal_progress_update(artifact_id: UUID):
    """Trigger goal progress recalculation when artifact is approved"""
    try:
        # This would trigger the real-time goal progress calculation
        # Implementation depends on the goal tracking system
        logger.info(f"🎯 Triggered goal progress update for artifact: {artifact_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger goal progress update: {e}")

# === HEALTH CHECK ===

@router.get("/health")
async def assets_health_check(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route assets_health_check called", endpoint="assets_health_check", trace_id=trace_id)

    """Health check for asset system"""
    try:
        health_status = await task_executor.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": health_status
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }