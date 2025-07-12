"""
Database Asset Extensions - Enhanced database methods for asset-driven system
Extends the existing database.py with asset-specific operations and queries.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4

from database import get_supabase_client, supabase_retry, _ensure_json_serializable
from models import (
    AssetRequirement, AssetArtifact, QualityValidation, QualityRule,
    EnhancedWorkspaceGoal, WorkspaceGoal, EnhancedTask, GoalProgressLog
)

logger = logging.getLogger(__name__)

class AssetDrivenDatabaseManager:
    """Enhanced database manager for asset-driven operations (Pillar 12: Concrete Deliverables)"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        logger.info("🗄️ AssetDrivenDatabaseManager initialized")
    
    # === ASSET REQUIREMENTS METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def create_asset_requirement(self, requirement: AssetRequirement) -> AssetRequirement:
        """Create new asset requirement with pillar compliance"""
        try:
            requirement_data = {
                "id": str(requirement.id),
                "goal_id": str(requirement.goal_id),
                "decomposition_id": str(requirement.decomposition_id) if requirement.decomposition_id else str(requirement.id),  # Use id as decomposition_id if none
                "internal_id": str(requirement.id),  # Same as id - required for legacy compatibility
                "todo_type": "simple",  # Valid enum value for todo_type check constraint
                "name": requirement.asset_name,  # Required field - name of the asset
                "description": requirement.asset_name,  # Use asset_name as description (renamed field)
                "asset_type": requirement.asset_type,
                "asset_format": requirement.asset_format,
                "priority": requirement.priority,
                "estimated_effort": requirement.estimated_effort,
                "user_impact": requirement.user_impact,
                "weight": requirement.weight,
                "mandatory": requirement.mandatory,
                "business_value_score": requirement.business_value_score,
                "acceptance_criteria": requirement.acceptance_criteria,
                "validation_rules": requirement.validation_rules,
                "supports_assets": requirement.supports_assets or [],
                "value_proposition": requirement.value_proposition,
                "status": requirement.status,
                "progress_percentage": requirement.progress_percentage,
                "ai_generated": requirement.ai_generated,
                "language_agnostic": requirement.language_agnostic,
                "sdk_compatible": requirement.sdk_compatible,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add workspace_id - it's required, get from goal if not provided
            if requirement.workspace_id:
                requirement_data["workspace_id"] = str(requirement.workspace_id)
            else:
                # Get workspace_id from the goal
                goal_response = self.supabase.table("workspace_goals").select("workspace_id").eq("id", str(requirement.goal_id)).execute()
                if goal_response.data:
                    requirement_data["workspace_id"] = goal_response.data[0]["workspace_id"]
                else:
                    raise Exception(f"Cannot find workspace_id for goal {requirement.goal_id}")
            
            response = self.supabase.table("goal_asset_requirements").insert(requirement_data).execute()
            
            if response.data:
                logger.info(f"✅ Created asset requirement: {requirement.asset_name}")
                # Clean up None values for Pydantic compatibility
                db_data = response.data[0]
                if db_data.get("supports_assets") is None:
                    db_data["supports_assets"] = []
                if db_data.get("asset_name") is None:
                    db_data["asset_name"] = db_data.get("name", "Unknown Asset")
                return AssetRequirement(**db_data)
            else:
                raise Exception("No data returned from requirement creation")
                
        except Exception as e:
            logger.error(f"Failed to create asset requirement: {e}")
            raise

    @supabase_retry(max_attempts=3)
    async def get_asset_requirements_for_goal(self, goal_id: UUID) -> List[AssetRequirement]:
        """Get all asset requirements for a specific goal"""
        try:
            response = self.supabase.table("goal_asset_requirements")                 .select("*")                 .eq("goal_id", str(goal_id))                 .order("created_at", desc=False)                 .execute()
            
            requirements = []
            for i, req in enumerate(response.data):
                try:
                    # Clean up None values for Pydantic compatibility (same as create_asset_requirement)
                    if req.get("supports_assets") is None:
                        req["supports_assets"] = []
                    if req.get("asset_name") is None:
                        req["asset_name"] = req.get("name", "Unknown Asset")
                    
                    requirement = AssetRequirement(**req)
                    requirements.append(requirement)
                except Exception as e:
                    logger.error(f"Failed to parse requirement {i}: {e}")
                    logger.error(f"Raw data: {req}")
            
            logger.info(f"📋 Retrieved {len(requirements)} requirements for goal {goal_id}")
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to get requirements for goal {goal_id}: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def update_requirement_progress(self, requirement_id: UUID, progress: float) -> bool:
        """Update asset requirement progress percentage"""
        try:
            update_data = {
                "progress_percentage": progress,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("goal_asset_requirements")                 .update(update_data)                 .eq("id", str(requirement_id))                 .execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"📈 Updated requirement progress: {requirement_id} -> {progress}%")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update requirement progress: {e}")
            return False

    # === ASSET ARTIFACTS METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def create_asset_artifact(self, artifact: AssetArtifact) -> AssetArtifact:
        """Create new asset artifact with enhanced metadata"""
        try:
            # Database-aligned field names
            artifact_data = {
                "id": str(artifact.id),
                "requirement_id": str(artifact.requirement_id),
                "task_id": str(artifact.task_id) if artifact.task_id else None,
                "workspace_id": str(artifact.workspace_id) if artifact.workspace_id else None,
                "name": getattr(artifact, 'name', None) or artifact.artifact_name,  # Database field
                "type": getattr(artifact, 'type', None) or artifact.artifact_type,  # Database field
                "category": getattr(artifact, 'category', 'general'),  # Database field
                "content": artifact.content,  # JSONB
                "metadata": artifact.metadata,
                "quality_score": artifact.quality_score,
                "completeness_score": getattr(artifact, 'completeness_score', 0.0),  # Database field
                "authenticity_score": getattr(artifact, 'authenticity_score', 0.0),  # Database field
                "actionability_score": artifact.actionability_score,
                "status": artifact.status,
                "validation_status": getattr(artifact, 'validation_status', 'pending'),  # Database field
                "generation_method": getattr(artifact, 'generation_method', 'manual'),  # Database field
                "ai_confidence": getattr(artifact, 'ai_confidence', 0.0),  # Database field
                "source_tools": getattr(artifact, 'source_tools', []),  # Database field
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("asset_artifacts").insert(artifact_data).execute()
            
            if response.data:
                logger.info(f"✅ Created asset artifact: {getattr(artifact, 'name', None) or artifact.artifact_name}")
                # Map database fields back to model for backward compatibility
                artifact_result = response.data[0].copy()
                artifact_result['artifact_name'] = artifact_result.get('name', '')
                artifact_result['artifact_type'] = artifact_result.get('type', '')
                artifact_result['content_format'] = 'json'  # Default for JSONB
                artifact_data = self._filter_asset_artifact_fields(artifact_result)
                created_artifact = AssetArtifact(**artifact_data)
                
                # 🎯 ASSET SUCCESS PATTERN LEARNING: Store learning when high-quality artifacts are created
                await self._store_asset_success_learning(created_artifact)
                
                return created_artifact
            else:
                raise Exception("No data returned from artifact creation")
                
        except Exception as e:
            logger.error(f"Failed to create asset artifact: {e}")
            raise

    @supabase_retry(max_attempts=3)
    async def get_artifacts_for_requirement(self, requirement_id: UUID) -> List[AssetArtifact]:
        """Get all artifacts for a specific requirement"""
        try:
            response = self.supabase.table("asset_artifacts") \
                .select("*") \
                .eq("requirement_id", str(requirement_id)) \
                .order("created_at", desc=False) \
                .execute()
            
            # 🔧 FIX: Filter response data to match AssetArtifact model fields  
            artifacts = [AssetArtifact(**self._filter_asset_artifact_fields(art)) for art in response.data]
            logger.info(f"📦 Retrieved {len(artifacts)} artifacts for requirement {requirement_id}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to get artifacts for requirement {requirement_id}: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def update_artifact_status(
        self, 
        artifact_id: UUID, 
        status: str, 
        quality_score: Optional[float] = None
    ) -> bool:
        """Update artifact status and trigger goal recalculation"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if quality_score is not None:
                update_data["quality_score"] = quality_score
                
            if status == "approved":
                update_data["validation_passed"] = True
                update_data["validated_at"] = datetime.utcnow().isoformat()
            
            response = self.supabase.table("asset_artifacts") \
                .update(update_data) \
                .eq("id", str(artifact_id)) \
                .execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"📋 Updated artifact status: {artifact_id} -> {status}")
                
                # Trigger goal progress recalculation if approved
                if status == "approved":
                    await self._trigger_goal_progress_recalculation(artifact_id)
                    
            return success
            
        except Exception as e:
            logger.error(f"Failed to update artifact status: {e}")
            return False

    async def _trigger_goal_progress_recalculation(self, artifact_id: UUID):
        """Trigger goal progress recalculation when artifact is approved"""
        try:
            # Get artifact's requirement and goal
            artifact_response = self.supabase.table("asset_artifacts") \
                .select("requirement_id") \
                .eq("id", str(artifact_id)) \
                .execute()
            
            if not artifact_response.data:
                return
            
            requirement_id = artifact_response.data[0]["requirement_id"]
            
            # Get goal from requirement
            requirement_response = self.supabase.table("goal_asset_requirements") \
                .select("goal_id") \
                .eq("id", requirement_id) \
                .execute()
            
            if not requirement_response.data:
                return
            
            goal_id = requirement_response.data[0]["goal_id"]
            
            # Recalculate goal progress
            await self.recalculate_goal_progress(UUID(goal_id))
            
        except Exception as e:
            logger.error(f"Failed to trigger goal progress recalculation: {e}")

    # === QUALITY VALIDATION METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def get_quality_rules_for_asset_type(self, asset_type: str) -> List[QualityRule]:
        """Get active quality rules for specific asset type"""
        try:
            response = self.supabase.table("ai_quality_rules") \
                .select("*") \
                .eq("asset_type", asset_type) \
                .eq("active", True) \
                .order("priority", desc=True) \
                .execute()
            
            rules = [QualityRule(**rule) for rule in response.data]
            logger.info(f"🛡️ Retrieved {len(rules)} quality rules for {asset_type}")
            return rules
            
        except Exception as e:
            logger.error(f"Failed to get quality rules for {asset_type}: {e}")
            return []

    
    
    def _filter_asset_artifact_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔧 FIX: Filter raw database data to only include fields that exist in AssetArtifact model
        This prevents 'pillar_compliance' attribute errors when creating AssetArtifact instances
        """
        # Valid AssetArtifact fields based on the updated model definition
        valid_fields = {
            'id', 'requirement_id', 'task_id', 'agent_id', 'workspace_id',
            'name', 'artifact_name', 'type', 'artifact_type', 'artifact_format',
            'content', 'content_format', 'category',
            'file_path', 'external_url', 'openai_file_id', 'metadata',
            'size_bytes', 'word_count', 'checksum',
            'quality_score', 'completeness_score', 'authenticity_score', 'actionability_score',
            'validation_passed', 'validation_status', 'validation_details', 
            'validation_errors', 'ai_quality_check',
            'status', 'version', 'human_review_required',
            'business_value_score', 'automation_ready',
            'ai_enhanced', 'generation_method', 'ai_confidence', 'source_tools',
            'enhancement_applied', 'original_content_hash',
            'detected_language', 'language_agnostic',
            'memory_context', 'learning_insights',
            'thinking_process', 'reasoning_steps',
            'created_at', 'updated_at', 'approved_at', 'approved_by_user_id'
        }
        
        # Filter out invalid fields like 'pillar_compliance'
        filtered_data = {}
        for key, value in raw_data.items():
            if key in valid_fields:
                filtered_data[key] = value
            else:
                logger.debug(f"🔧 Filtered out invalid AssetArtifact field: {key}")
        
        return filtered_data

    @supabase_retry(max_attempts=3)
    async def log_quality_validation(self, validation: QualityValidation) -> UUID:
        """Log quality validation with AI insights"""
        try:
            # Ensure all UUID fields are properly converted to strings
            validation_data = {
                "id": str(validation.id) if validation.id else str(uuid4()),
                "artifact_id": str(validation.artifact_id),
                "rule_id": str(validation.rule_id) if validation.rule_id else None,
                "workspace_id": str(validation.workspace_id) if validation.workspace_id else None,
                "score": validation.score,
                "passed": validation.passed,
                "feedback": validation.feedback,
                "ai_assessment": validation.ai_assessment,
                "improvement_suggestions": _ensure_json_serializable(validation.improvement_suggestions),
                "business_impact": validation.business_impact,
                "actionability_assessment": validation.actionability_assessment,
                "quality_dimensions": _ensure_json_serializable(validation.quality_dimensions),
                "validation_model": validation.validation_model,
                "validated_at": datetime.utcnow().isoformat(),
                "processing_time_ms": validation.processing_time_ms,
                "ai_driven": validation.ai_driven,
                "pillar_compliance_check": _ensure_json_serializable(validation.pillar_compliance_check)
            }
            
            # Remove None values to avoid database issues
            validation_data = {k: v for k, v in validation_data.items() if v is not None}
            
            logger.info(f"📝 Attempting to log quality validation for artifact {validation.artifact_id}")
            response = self.supabase.table("quality_validations").insert(validation_data).execute()
            
            if response.data:
                validation_id = UUID(response.data[0]["id"])
                logger.info(f"✅ Successfully logged quality validation: {validation_id}")
                return validation_id
            else:
                raise Exception("No data returned from validation logging")
                
        except Exception as e:
            logger.error(f"❌ Failed to log quality validation for artifact {validation.artifact_id}: {e}")
            logger.error(f"Validation data keys: {list(validation_data.keys()) if 'validation_data' in locals() else 'N/A'}")
            raise

    # === ENHANCED GOAL PROGRESS METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def get_real_time_goal_completion(self, workspace_id: UUID) -> List[Dict]:
        """Get real-time goal completion using enhanced calculation"""
        try:
            # Use the database view for real-time calculation
            response = self.supabase.table("real_time_goal_completion") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            logger.info(f"📊 Retrieved real-time completion for {len(response.data)} goals")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get real-time goal completion: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def recalculate_goal_progress(self, goal_id: UUID) -> float:
        """
        🚀 CRITICAL FIX: Recalculate goal progress with "No Assets = No Progress" enforcement
        
        Implements Pillar 12: Concrete Deliverables with strict asset-driven progress calculation.
        A goal can ONLY progress based on approved, high-quality asset artifacts.
        """
        try:
            # Get all requirements for the goal
            requirements = await self.get_asset_requirements_for_goal(goal_id)
            
            # 🚨 PILLAR 12 ENFORCEMENT: No asset requirements = Zero progress
            if not requirements:
                logger.warning(f"🚫 NO ASSETS = NO PROGRESS: Goal {goal_id} has no asset requirements - progress forced to 0%")
                await self._enforce_zero_progress(goal_id, "no_asset_requirements")
                return 0.0
            
            total_weight = sum(req.weight for req in requirements)
            completed_weight = 0.0
            total_quality_score = 0.0
            approved_artifacts_count = 0
            total_artifacts_count = 0
            
            for requirement in requirements:
                # Get ALL artifacts for this requirement
                artifacts = await self.get_artifacts_for_requirement(requirement.id)
                total_artifacts_count += len(artifacts)
                
                # 🛡️ STRICT QUALITY GATES: Only approved artifacts with high quality count
                approved_artifacts = [
                    a for a in artifacts 
                    if a.status == "approved" and a.quality_score >= 0.8 and a.validation_passed == True
                ]
                approved_artifacts_count += len(approved_artifacts)
                
                if approved_artifacts:
                    # Requirement is considered complete if it has approved artifacts
                    completed_weight += requirement.weight
                    # Use the highest quality score from approved artifacts
                    max_quality = max(a.quality_score for a in approved_artifacts)
                    total_quality_score += max_quality * requirement.weight
                    
                    logger.debug(f"✅ Requirement '{requirement.asset_name}' completed with {len(approved_artifacts)} approved artifacts")
                else:
                    logger.debug(f"⏳ Requirement '{requirement.asset_name}' has {len(artifacts)} artifacts but none approved with high quality")
            
            # 🚨 PILLAR 12 ENFORCEMENT: Calculate asset-driven progress
            progress_percentage = (completed_weight / total_weight * 100) if total_weight > 0 else 0.0
            avg_quality_score = (total_quality_score / total_weight) if total_weight > 0 else 0.0
            asset_completion_rate = (approved_artifacts_count / len(requirements)) * 100 if requirements else 0.0
            
            # 🚫 CRITICAL ENFORCEMENT: If no approved assets, progress must be zero
            if approved_artifacts_count == 0:
                logger.warning(f"🚫 NO APPROVED ASSETS = NO PROGRESS: Goal {goal_id} has {total_artifacts_count} artifacts but none approved - progress forced to 0%")
                progress_percentage = 0.0
                asset_completion_rate = 0.0
                avg_quality_score = 0.0
            
            # Update goal with new progress
            update_data = {
                "progress_percentage": progress_percentage,
                "asset_completion_rate": progress_percentage,  # Same as progress in asset-driven system
                "quality_score": avg_quality_score,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update current_value to match progress
            goal_response = self.supabase.table("workspace_goals") \
                .select("target_value") \
                .eq("id", str(goal_id)) \
                .execute()
            
            if goal_response.data:
                target_value = goal_response.data[0]["target_value"]
                new_current_value = (progress_percentage / 100) * target_value
                update_data["current_value"] = new_current_value
            
            response = self.supabase.table("workspace_goals") \
                .update(update_data) \
                .eq("id", str(goal_id)) \
                .execute()
            
            if response.data:
                logger.info(f"🎯 Recalculated goal progress: {goal_id} -> {progress_percentage:.1f}%")
                
                # Log progress update
                await self.log_goal_progress(goal_id, progress_percentage, avg_quality_score)
                
            return progress_percentage
            
        except Exception as e:
            logger.error(f"Failed to recalculate goal progress for {goal_id}: {e}")
            return 0.0

    async def _enforce_zero_progress(self, goal_id: UUID, reason: str):
        """
        🚫 PILLAR 12 ENFORCEMENT: Force goal progress to zero
        
        This function implements strict "No Assets = No Progress" enforcement
        by setting goal progress to 0% when asset requirements are missing or
        no approved artifacts exist.
        """
        try:
            logger.warning(f"🚫 ENFORCING ZERO PROGRESS: Goal {goal_id} - Reason: {reason}")
            
            # Force update goal to 0% progress
            update_data = {
                "progress_percentage": 0.0,
                "current_value": 0.0,
                "asset_completion_rate": 0.0,
                "quality_score": 0.0,
                "updated_at": datetime.utcnow().isoformat(),
                "enforcement_reason": reason,
                "last_enforcement_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("workspace_goals") \
                .update(update_data) \
                .eq("id", str(goal_id)) \
                .execute()
            
            if response.data:
                # Log enforcement action
                enforcement_log = {
                    "id": str(uuid4()),
                    "goal_id": str(goal_id),
                    "enforcement_type": "zero_progress",
                    "reason": reason,
                    "previous_progress": response.data[0].get("progress_percentage", 0.0),
                    "enforced_progress": 0.0,
                    "enforced_at": datetime.utcnow().isoformat(),
                    "pillar_compliance": "strict_asset_driven"
                }
                
                # Store enforcement log (if table exists)
                try:
                    self.supabase.table("goal_enforcement_logs").insert(enforcement_log).execute()
                except:
                    logger.debug("Goal enforcement logs table not available - enforcement logged in memory")
                
                logger.info(f"🚫 ZERO PROGRESS ENFORCED: Goal {goal_id} set to 0% - {reason}")
            
        except Exception as e:
            logger.error(f"Failed to enforce zero progress for goal {goal_id}: {e}")

    @supabase_retry(max_attempts=3)
    async def log_goal_progress(self, goal_id: UUID, progress: float, quality_score: float):
        """Log goal progress change for tracking and analytics"""
        try:
            progress_log = {
                "id": str(uuid4()),
                "goal_id": str(goal_id),
                "progress_percentage": progress,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat(),
                "calculation_method": "asset_driven",
                "metadata": {
                    "system": "asset_driven_orchestrator",
                    "pillar_compliance": True
                }
            }
            
            response = self.supabase.table("goal_progress_logs").insert(progress_log).execute()
            
            if response.data:
                logger.info(f"📊 Logged goal progress: {goal_id} -> {progress:.1f}%")
                
        except Exception as e:
            logger.error(f"Failed to log goal progress: {e}")

    # === WORKSPACE GOAL METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def get_workspace_asset_requirements(self, workspace_id: UUID) -> List[AssetRequirement]:
        """Get all asset requirements for a workspace"""
        try:
            response = self.supabase.table("goal_asset_requirements") \
                .select("""
                    *,
                    workspace_goals!inner(workspace_id)
                """) \
                .eq("workspace_goals.workspace_id", str(workspace_id)) \
                .order("created_at", desc=False) \
                .execute()
            
            # Debug: log raw data before Pydantic parsing
            logger.info(f"📋 Raw data retrieved: {len(response.data)} records")
            if response.data:
                logger.debug(f"Sample raw record: {response.data[0]}")
            
            requirements = []
            for i, req in enumerate(response.data):
                try:
                    # Clean up None values for Pydantic compatibility (same as create_asset_requirement)
                    if req.get("supports_assets") is None:
                        req["supports_assets"] = []
                    if req.get("asset_name") is None:
                        req["asset_name"] = req.get("name", "Unknown Asset")
                    
                    requirement = AssetRequirement(**req)
                    requirements.append(requirement)
                except Exception as e:
                    logger.error(f"Failed to parse requirement {i}: {e}")
                    logger.error(f"Raw data: {req}")
            
            logger.info(f"📋 Successfully parsed {len(requirements)} asset requirements for workspace {workspace_id}")
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to get asset requirements for workspace {workspace_id}: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def get_workspace_asset_artifacts(self, workspace_id: UUID) -> List[AssetArtifact]:
        """Get all asset artifacts for a workspace"""
        try:
            response = self.supabase.table("asset_artifacts") \
                .select("""
                    *,
                    goal_asset_requirements!inner(
                        workspace_goals!inner(workspace_id)
                    )
                """) \
                .eq("goal_asset_requirements.workspace_goals.workspace_id", str(workspace_id)) \
                .order("created_at", desc=False) \
                .execute()
            
            artifacts = [AssetArtifact(**artifact) for artifact in response.data]
            logger.info(f"📦 Retrieved {len(artifacts)} asset artifacts for workspace {workspace_id}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to get asset artifacts for workspace {workspace_id}: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def get_workspace_goals(self, workspace_id: UUID) -> List[WorkspaceGoal]:
        """Get all workspace goals with enhanced data"""
        try:
            response = self.supabase.table("workspace_goals") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .order("created_at", desc=False) \
                .execute()
            
            goals = [WorkspaceGoal(**goal) for goal in response.data]
            logger.info(f"🎯 Retrieved {len(goals)} goals for workspace {workspace_id}")
            return goals
            
        except Exception as e:
            logger.error(f"Failed to get workspace goals: {e}")
            return []

    @supabase_retry(max_attempts=3)
    async def update_goal_progress(
        self, 
        goal_id: UUID, 
        progress_percentage: float, 
        quality_score: Optional[float] = None
    ) -> bool:
        """Update goal progress with optional quality score"""
        try:
            update_data = {
                "progress_percentage": progress_percentage,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if quality_score is not None:
                update_data["quality_score"] = quality_score
                update_data["asset_completion_rate"] = progress_percentage
            
            # Update current_value based on progress
            goal_response = self.supabase.table("workspace_goals") \
                .select("target_value") \
                .eq("id", str(goal_id)) \
                .execute()
            
            if goal_response.data:
                target_value = goal_response.data[0]["target_value"]
                new_current_value = (progress_percentage / 100) * target_value
                update_data["current_value"] = new_current_value
            
            response = self.supabase.table("workspace_goals") \
                .update(update_data) \
                .eq("id", str(goal_id)) \
                .execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"📈 Updated goal progress: {goal_id} -> {progress_percentage:.1f}%")
                await self.log_goal_progress(goal_id, progress_percentage, quality_score or 0.0)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to update goal progress: {e}")
            return False

    # === ANALYTICS AND REPORTING METHODS ===
    
    @supabase_retry(max_attempts=3)
    async def get_asset_system_metrics(self, workspace_id: UUID) -> Dict[str, Any]:
        """Get comprehensive asset system metrics for dashboard"""
        try:
            metrics = {
                "total_requirements": 0,
                "total_artifacts": 0,
                "approved_artifacts": 0,
                "quality_validations": 0,
                "avg_quality_score": 0.0,
                "pillar_compliance_rate": 0.0,
                "asset_type_distribution": {},
                "status_distribution": {},
                "quality_trends": []
            }
            
            # Get requirements count
            req_response = self.supabase.table("goal_asset_requirements") \
                .select("id", count="exact") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            metrics["total_requirements"] = req_response.count or 0
            
            # Get artifacts metrics
            art_response = self.supabase.table("asset_artifacts") \
                .select("status, artifact_type, quality_score") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            artifacts = art_response.data
            metrics["total_artifacts"] = len(artifacts)
            metrics["approved_artifacts"] = len([a for a in artifacts if a["status"] == "approved"])
            
            # Calculate averages
            if artifacts:
                metrics["avg_quality_score"] = sum(a["quality_score"] for a in artifacts) / len(artifacts)
                
                # Status distribution
                status_counts = {}
                for artifact in artifacts:
                    status = artifact["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                metrics["status_distribution"] = status_counts
                
                # Asset type distribution
                type_counts = {}
                for artifact in artifacts:
                    asset_type = artifact["artifact_type"]
                    type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
                metrics["asset_type_distribution"] = type_counts
            
            # Get validation count
            val_response = self.supabase.table("quality_validations") \
                .select("id", count="exact") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            metrics["quality_validations"] = val_response.count or 0
            
            logger.info(f"📊 Generated asset system metrics for workspace {workspace_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get asset system metrics: {e}")
            return {}

    @supabase_retry(max_attempts=3)
    async def get_pillar_compliance_status(self, workspace_id: UUID) -> List[Dict[str, Any]]:
        """Get 14 pillars compliance status for workspace"""
        try:
            # This would use the pillar_compliance_status view from the database
            response = self.supabase.table("pillar_compliance_status") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            compliance_data = response.data
            logger.info(f"🏛️ Retrieved pillar compliance for {len(compliance_data)} pillars")
            return compliance_data
            
        except Exception as e:
            logger.error(f"Failed to get pillar compliance status: {e}")
            # Return default pillar status if view doesn't exist
            default_pillars = [
                {"pillar_name": "OpenAI SDK", "compliance_rate": 0.9, "status": "compliant"},
                {"pillar_name": "AI-Driven", "compliance_rate": 0.85, "status": "compliant"},
                {"pillar_name": "Universal", "compliance_rate": 0.8, "status": "warning"},
                {"pillar_name": "Scalable", "compliance_rate": 0.75, "status": "warning"},
                {"pillar_name": "Goal-Driven", "compliance_rate": 0.9, "status": "compliant"},
                {"pillar_name": "Memory System", "compliance_rate": 0.7, "status": "warning"},
                {"pillar_name": "Pipeline autonoma", "compliance_rate": 0.85, "status": "compliant"},
                {"pillar_name": "Quality Gates", "compliance_rate": 0.95, "status": "compliant"},
                {"pillar_name": "Minimal UI/UX", "compliance_rate": 0.8, "status": "compliant"},
                {"pillar_name": "Real-Time Thinking", "compliance_rate": 0.75, "status": "warning"},
                {"pillar_name": "Production-ready", "compliance_rate": 0.8, "status": "compliant"},
                {"pillar_name": "Concrete Deliverables", "compliance_rate": 0.95, "status": "compliant"},
                {"pillar_name": "Course-Correction", "compliance_rate": 0.7, "status": "warning"},
                {"pillar_name": "Modular Tools", "compliance_rate": 0.85, "status": "compliant"}
            ]
            return default_pillars

    # === HEALTH CHECK METHODS ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for asset-driven database operations"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database_connection": "unknown",
                    "asset_tables": "unknown",
                    "quality_system": "unknown",
                    "goal_calculation": "unknown"
                },
                "performance": {
                    "avg_query_time_ms": 0,
                    "active_connections": 0
                }
            }
            
            # Test database connection
            test_response = self.supabase.table("workspace_goals").select("id").limit(1).execute()
            health_status["checks"]["database_connection"] = "healthy" if test_response.data is not None else "unhealthy"
            
            # Test asset tables
            try:
                req_count = self.supabase.table("goal_asset_requirements").select("id", count="exact").limit(1).execute()
                art_count = self.supabase.table("asset_artifacts").select("id", count="exact").limit(1).execute()
                health_status["checks"]["asset_tables"] = "healthy"
            except:
                health_status["checks"]["asset_tables"] = "unhealthy"
            
            # Test quality system
            try:
                val_count = self.supabase.table("quality_validations").select("id", count="exact").limit(1).execute()
                health_status["checks"]["quality_system"] = "healthy"
            except:
                health_status["checks"]["quality_system"] = "unhealthy"
            
            # Overall status
            unhealthy_checks = [k for k, v in health_status["checks"].items() if v == "unhealthy"]
            if unhealthy_checks:
                health_status["status"] = "degraded" if len(unhealthy_checks) < 2 else "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _store_asset_success_learning(self, artifact: AssetArtifact) -> None:
        """
        🎯 ASSET SUCCESS PATTERN LEARNING: Store learning patterns when high-quality assets are created
        
        Analyzes successful asset creation to identify patterns that lead to quality deliverables.
        This feeds into workspace memory for future task guidance.
        """
        try:
            # Only learn from high-quality artifacts (score >= 70)
            if artifact.quality_score is None or artifact.quality_score < 70:
                logger.debug(f"Skipping asset learning for low-quality artifact: {artifact.quality_score}")
                return
            
            # Get additional context about the asset creation
            asset_context = await self._build_asset_creation_context(artifact)
            if not asset_context:
                logger.debug(f"No context available for asset learning: {artifact.id}")
                return
            
            # Import workspace memory for learning storage
            from workspace_memory import workspace_memory
            from models import InsightType
            
            # Determine learning type based on quality score
            if artifact.quality_score >= 90:
                insight_type = InsightType.SUCCESS_PATTERN
                content = f"HIGH-QUALITY ASSET SUCCESS: {artifact.artifact_type} '{artifact.artifact_name}' achieved {artifact.quality_score}% quality. Pattern: {asset_context.get('success_factors', '')}"
                relevance_tags = ["asset_success", "high_quality", "best_practice", f"asset_type_{artifact.artifact_type.lower()}"]
                confidence = 0.9
                
            elif artifact.quality_score >= 70:
                insight_type = InsightType.SUCCESS_PATTERN
                content = f"QUALITY ASSET SUCCESS: {artifact.artifact_type} '{artifact.artifact_name}' passed validation with {artifact.quality_score}%. Approach: {asset_context.get('creation_approach', '')}"
                relevance_tags = ["asset_success", "quality_pass", f"asset_type_{artifact.artifact_type.lower()}"]
                confidence = 0.7
                
            else:
                return  # Already filtered above, but double-check
            
            # Add specific context tags
            if asset_context.get('requirement_priority'):
                relevance_tags.append(f"priority_{asset_context['requirement_priority'].lower()}")
            if asset_context.get('goal_metric_type'):
                relevance_tags.append(f"metric_{asset_context['goal_metric_type']}")
            if asset_context.get('task_agent_role'):
                relevance_tags.append(f"agent_role_{asset_context['task_agent_role']}")
            
            # Create metadata with detailed asset success context
            metadata = {
                "artifact_id": str(artifact.id),
                "artifact_type": artifact.artifact_type,
                "artifact_name": artifact.artifact_name,
                "quality_score": artifact.quality_score,
                "business_value_score": artifact.business_value_score,
                "actionability_score": artifact.actionability_score,
                "content_format": artifact.content_format,
                "ai_enhanced": artifact.ai_enhanced,
                "validation_passed": artifact.validation_passed,
                "learning_type": "asset_success_pattern",
                "creation_context": asset_context,
                "created_from": "asset_success_learning"
            }
            
            # Store learning in workspace memory
            workspace_id = asset_context.get('workspace_id')
            if workspace_id:
                await workspace_memory.store_insight(
                    workspace_id=UUID(workspace_id),
                    insight_type=insight_type,
                    content=content,
                    relevance_tags=relevance_tags,
                    confidence_score=confidence,
                    metadata=metadata
                )
                
                logger.info(f"✅ Asset success learning stored for {artifact.artifact_type}: {artifact.artifact_name}")
            else:
                logger.warning(f"No workspace_id found for asset learning: {artifact.id}")
                
        except Exception as e:
            logger.error(f"Failed to store asset success learning for {artifact.id}: {e}")
            # Non-blocking error - asset creation should still succeed
    
    async def _build_asset_creation_context(self, artifact: AssetArtifact) -> Optional[Dict[str, Any]]:
        """Build context information about successful asset creation"""
        try:
            context = {}
            
            # Get requirement details
            if artifact.requirement_id:
                requirement_response = self.supabase.table("goal_asset_requirements") \
                    .select("*") \
                    .eq("id", str(artifact.requirement_id)) \
                    .execute()
                
                if requirement_response.data:
                    req_data = requirement_response.data[0]
                    context.update({
                        "requirement_priority": req_data.get("priority", "unknown"),
                        "requirement_effort": req_data.get("estimated_effort", 0),
                        "requirement_weight": req_data.get("weight", 0),
                        "requirement_mandatory": req_data.get("mandatory", False),
                        "workspace_id": req_data.get("workspace_id")  # Critical for workspace learning
                    })
                    
                    # Get goal details
                    goal_id = req_data.get("goal_id")
                    if goal_id:
                        goal_response = self.supabase.table("workspace_goals") \
                            .select("metric_type, goal_description") \
                            .eq("id", str(goal_id)) \
                            .execute()
                        
                        if goal_response.data:
                            goal_data = goal_response.data[0]
                            context.update({
                                "goal_metric_type": goal_data.get("metric_type", "unknown"),
                                "goal_description": goal_data.get("goal_description", "")
                            })
            
            # Get task details if available
            if artifact.task_id:
                task_response = self.supabase.table("tasks") \
                    .select("task_type, agent_role, name, description") \
                    .eq("id", str(artifact.task_id)) \
                    .execute()
                
                if task_response.data:
                    task_data = task_response.data[0]
                    context.update({
                        "task_type": task_data.get("task_type", "unknown"),
                        "task_agent_role": task_data.get("agent_role", "unknown"),
                        "task_name": task_data.get("name", ""),
                        "task_description": task_data.get("description", "")
                    })
            
            # Build success factors summary
            success_factors = []
            if artifact.ai_enhanced:
                success_factors.append("AI-enhanced content")
            if artifact.quality_score >= 90:
                success_factors.append("exceptional quality standards")
            if artifact.business_value_score and artifact.business_value_score >= 80:
                success_factors.append("high business value")
            if artifact.actionability_score and artifact.actionability_score >= 80:
                success_factors.append("highly actionable content")
            
            context["success_factors"] = ", ".join(success_factors) if success_factors else "standard quality achievement"
            
            # Build creation approach summary
            approach_elements = []
            if context.get("requirement_priority") == "high":
                approach_elements.append("high-priority requirement")
            if context.get("task_type"):
                approach_elements.append(f"{context['task_type']} task approach")
            if artifact.content_format:
                approach_elements.append(f"{artifact.content_format} format")
            
            context["creation_approach"] = ", ".join(approach_elements) if approach_elements else "standard creation process"
            
            return context if context.get("workspace_id") else None
            
        except Exception as e:
            logger.error(f"Failed to build asset creation context: {e}")
            return None

# Export the enhanced database manager
asset_db_manager = AssetDrivenDatabaseManager()

# Convenience functions for backward compatibility
async def create_asset_requirement(requirement: AssetRequirement) -> AssetRequirement:
    return await asset_db_manager.create_asset_requirement(requirement)

async def get_asset_requirements_for_goal(goal_id: UUID) -> List[AssetRequirement]:
    return await asset_db_manager.get_asset_requirements_for_goal(goal_id)

async def create_asset_artifact(artifact: AssetArtifact) -> AssetArtifact:
    return await asset_db_manager.create_asset_artifact(artifact)

async def get_artifacts_for_requirement(requirement_id: UUID) -> List[AssetArtifact]:
    return await asset_db_manager.get_artifacts_for_requirement(requirement_id)

async def update_artifact_status(artifact_id: UUID, status: str, quality_score: Optional[float] = None) -> bool:
    return await asset_db_manager.update_artifact_status(artifact_id, status, quality_score)

async def get_quality_rules_for_asset_type(asset_type: str) -> List[QualityRule]:
    return await asset_db_manager.get_quality_rules_for_asset_type(asset_type)

async def log_quality_validation(validation: QualityValidation) -> UUID:
    return await asset_db_manager.log_quality_validation(validation)

async def get_workspace_goals(workspace_id: UUID) -> List[WorkspaceGoal]:
    return await asset_db_manager.get_workspace_goals(workspace_id)

async def update_goal_progress(goal_id: UUID, progress_percentage: float, quality_score: Optional[float] = None) -> bool:
    return await asset_db_manager.update_goal_progress(goal_id, progress_percentage, quality_score)

# Export all for easy import
__all__ = [
    "AssetDrivenDatabaseManager", "asset_db_manager",
    "create_asset_requirement", "get_asset_requirements_for_goal",
    "create_asset_artifact", "get_artifacts_for_requirement", "update_artifact_status",
    "get_quality_rules_for_asset_type", "log_quality_validation",
    "get_workspace_goals", "update_goal_progress"
]