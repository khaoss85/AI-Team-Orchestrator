# backend/deliverable_system/unified_deliverable_engine.py
import logging
import os
import json
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, ValidationError, Field

from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine
from database import get_supabase_client, supabase
from models import AssetRequirement, WorkspaceGoal, AssetArtifact, EnhancedTask
from datetime import datetime
from services.unified_memory_engine import unified_memory_engine # <-- IMPORT ADDED

logger = logging.getLogger(__name__)

# --- Enums and Pydantic Models for Validation ---

class DeliverableType(str, Enum):
    """Enum for different types of deliverables."""
    CONTACT_DATABASE = "contact_database"
    CONTENT_STRATEGY = "content_strategy"
    # Add other deliverable types here

class ContactDatabaseDeliverable(BaseModel):
    """Validation model for a contact database deliverable."""
    contacts: List[Dict[str, Any]]
    total_contacts: int = Field(..., ge=0)
    icp_criteria: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    collection_method: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)

# Mapping from DeliverableType to Pydantic model
DELIVERABLE_MODELS = {
    DeliverableType.CONTACT_DATABASE: ContactDatabaseDeliverable,
}


class UnifiedDeliverableEngine:
    def __init__(self):
        logger.info("🔧 Unified Deliverable Engine initialized.")
        self.supabase = get_supabase_client()
        self.ai_client = None
        if os.getenv("OPENAI_API_KEY"):
            from openai import AsyncOpenAI
            self.ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.enhancement_model = os.getenv("AI_ENHANCEMENT_MODEL", "gpt-4o-mini")
        
        # Database manager for backward compatibility
        self.db_manager = self

    def validate_deliverable(self, data: Dict[str, Any], deliverable_type: DeliverableType) -> bool:
        """
        Validates deliverable data against a Pydantic model based on its type.
        This method fixes the AttributeError found in tests.
        """
        validation_model = DELIVERABLE_MODELS.get(deliverable_type)
        
        if not validation_model:
            logger.error(f"No validation model found for deliverable type: {deliverable_type}")
            return False
            
        try:
            validation_model(**data)
            logger.info(f"✅ Deliverable of type '{deliverable_type}' passed validation.")
            return True
        except ValidationError as e:
            logger.warning(f"🔥 Deliverable of type '{deliverable_type}' failed validation: {e}")
            return False

    async def generate_requirements_from_goal(self, goal: WorkspaceGoal) -> List[AssetRequirement]:
        """Generate asset requirements from a workspace goal, enhanced by memory."""
        logger.info(f"🎯 Generating asset requirements for goal: {goal.description}")
        
        if not self.ai_client:
            logger.warning("AI client not available for requirement generation")
            return []
        
        try:
            # <-- LINKING: Use Memory Engine to get context -->
            memory_query = f"Requirements for goals similar to: {goal.description}"
            relevant_memories = await unified_memory_engine.get_relevant_context(
                workspace_id=goal.workspace_id,
                query=memory_query,
                max_results=3
            )
            memory_context = [mem.content for mem in relevant_memories]
            
            # Use AI to analyze goal and generate requirements
            prompt = f"""
            Analyze this goal and generate concrete asset requirements.
            
            Goal Description: {goal.description}
            Metric: {goal.metric_type}
            Target: {goal.target_value}

            Leverage these past insights from similar goals:
            {json.dumps(memory_context, indent=2)}
            
            Generate 3-5 specific deliverable assets that would demonstrate goal achievement.
            For each asset, specify:
            - Name
            - Type (document, code, design, data, etc.)
            - Description
            - Acceptance criteria
            """
            
            response = await self.ai_client.chat.completions.create(
                model=self.enhancement_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # This is simplified - real implementation would parse structured output
            requirements = []
            
            # For now, create a basic requirement
            requirement = AssetRequirement(
                id=uuid4(),
                goal_id=goal.id,
                workspace_id=goal.workspace_id,
                asset_name=f"Deliverable for {goal.description}",
                asset_type="document",
                asset_format="structured_data",
                description=f"Primary deliverable demonstrating achievement of: {goal.description}",
                priority="high",
                business_value_score=0.8,
                acceptance_criteria={"completeness": "Must fully address goal objectives"},
                required_tools=["research", "analysis"],
                estimated_effort_hours=8.0,
                status="pending"
            )
            requirements.append(requirement)
            
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to generate requirements: {e}")
            return []

    async def process_task_output(self, task: EnhancedTask, requirement: AssetRequirement) -> Optional[AssetArtifact]:
        """
        Process task output into a structured asset artifact and store it in memory.
        """
        logger.info(f"🏭 Processing task output for requirement: {requirement.asset_name}")
        raw_content = self._extract_task_content(task)
        if not raw_content:
            return None
        
        structured_content = await self._structure_and_enhance_content(raw_content, requirement)
        if not structured_content:
            return None

        artifact = AssetArtifact(
            requirement_id=requirement.id,
            task_id=task.id,
            workspace_id=requirement.workspace_id,
            name=structured_content.get("artifact_name", requirement.asset_name),
            type=requirement.asset_type,
            content=structured_content.get("enhanced_content", {}),
        )
        
        # <-- LINKING: Store artifact creation in Memory Engine -->
        await unified_memory_engine.store_context(
            workspace_id=artifact.workspace_id,
            context_type="artifact_created",
            content={
                "artifact_name": artifact.name,
                "artifact_type": artifact.type,
                "related_task": task.name,
            },
            importance_score=0.7
        )
        
        return artifact

    def _extract_task_content(self, task: EnhancedTask) -> Optional[str]:
        return task.result

    async def _structure_and_enhance_content(self, raw_content: str, requirement: AssetRequirement) -> Optional[Dict[str, Any]]:
        if not self.ai_client: return None
        # Simplified AI call
        return {"artifact_name": requirement.asset_name, "enhanced_content": {"data": raw_content}}

    async def get_workspace_asset_artifacts(self, workspace_id: UUID) -> List[AssetArtifact]:
        """Get all asset artifacts for a workspace"""
        try:
            artifacts_response = self.supabase.table("asset_artifacts") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            artifacts = []
            for data in artifacts_response.data:
                # Map database fields for compatibility
                if 'name' in data and not data.get('artifact_name'):
                    data['artifact_name'] = data['name']
                if 'type' in data and not data.get('artifact_type'):
                    data['artifact_type'] = data['type']
                artifacts.append(AssetArtifact(**data))
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to get workspace artifacts: {e}")
            return []
    
    async def get_workspace_asset_requirements(self, workspace_id: UUID) -> List[AssetRequirement]:
        """Get all asset requirements for a workspace"""
        try:
            requirements_response = self.supabase.table("goal_asset_requirements") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            return [AssetRequirement(**req) for req in requirements_response.data]
            
        except Exception as e:
            logger.error(f"Failed to get workspace requirements: {e}")
            return []
    
    async def enhance_existing_artifact(self, artifact_id: UUID) -> Optional[AssetArtifact]:
        """Enhance an existing artifact with AI"""
        try:
            # Get artifact
            artifact_response = self.supabase.table("asset_artifacts") \
                .select("*") \
                .eq("id", str(artifact_id)) \
                .single() \
                .execute()
            
            if not artifact_response.data:
                return None
            
            artifact_data = artifact_response.data
            if 'name' in artifact_data and not artifact_data.get('artifact_name'):
                artifact_data['artifact_name'] = artifact_data['name']
            if 'type' in artifact_data and not artifact_data.get('artifact_type'):
                artifact_data['artifact_type'] = artifact_data['type']
            
            artifact = AssetArtifact(**artifact_data)
            
            if not self.ai_client:
                logger.warning("AI client not available for enhancement")
                return artifact
            
            # Enhance content with AI
            prompt = f"""
            Enhance this artifact content to make it more comprehensive and actionable:
            Name: {artifact.artifact_name}
            Type: {artifact.artifact_type}
            Current Content: {artifact.content}
            
            Provide enhanced content that is more detailed, structured, and valuable.
            """
            
            response = await self.ai_client.chat.completions.create(
                model=self.enhancement_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            enhanced_content = response.choices[0].message.content
            
            # Update artifact with enhanced content
            update_data = {
                "content": {"enhanced": enhanced_content, "original": artifact.content},
                "metadata": {**artifact.metadata, "ai_enhanced": True, "enhanced_at": datetime.utcnow().isoformat()},
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("asset_artifacts") \
                .update(update_data) \
                .eq("id", str(artifact_id)) \
                .execute()
            
            # Return updated artifact
            artifact.content = update_data["content"]
            artifact.metadata = update_data["metadata"]
            
            return artifact
            
        except Exception as e:
            logger.error(f"Failed to enhance artifact: {e}")
            return None
    
    async def check_and_create_final_deliverable(self, workspace_id: str) -> Optional[str]:
        """
        Check if workspace is ready for final deliverable and create it if needed.
        Returns deliverable ID if created, None otherwise.
        """
        try:
            logger.info(f"Checking final deliverable readiness for workspace {workspace_id}")
            
            # Get workspace goals and check completion
            goals_response = self.supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
            
            if not goals_response.data:
                logger.info(f"No goals found for workspace {workspace_id}")
                return None
            
            # Check if all goals are completed
            all_goals_completed = all(
                goal.get('current_value', 0) >= goal.get('target_value', 100) 
                for goal in goals_response.data
            )
            
            if not all_goals_completed:
                logger.info(f"Not all goals completed for workspace {workspace_id}")
                return None
            
            # Create final deliverable
            return await self.create_intelligent_deliverable(workspace_id, "final_deliverable")
            
        except Exception as e:
            logger.error(f"Error checking final deliverable for workspace {workspace_id}: {e}")
            return None

    async def create_intelligent_deliverable(self, workspace_id: str, deliverable_type: str, **kwargs) -> Optional[str]:
        """
        Create an intelligent deliverable for the workspace.
        Returns deliverable ID if created, None otherwise.
        """
        try:
            logger.info(f"Creating intelligent deliverable of type {deliverable_type} for workspace {workspace_id}")
            
            # Create asset artifact
            artifact_data = {
                "id": str(uuid4()),
                "workspace_id": workspace_id,
                "name": f"Final Deliverable - {deliverable_type}",
                "type": deliverable_type,
                "content": {"type": deliverable_type, "status": "completed"},
                "metadata": {
                    "created_by": "unified_deliverable_engine",
                    "creation_type": "intelligent_deliverable"
                },
                "quality_score": 85.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("asset_artifacts").insert(artifact_data).execute()
            
            if result.data:
                logger.info(f"Created deliverable {result.data[0]['id']} for workspace {workspace_id}")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating intelligent deliverable: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the deliverable engine"""
        try:
            # Test database connection
            test_response = self.supabase.table("workspace_goals").select("id").limit(1).execute()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "database": "connected",
                    "ai_client": "available" if self.ai_client else "unavailable"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

unified_deliverable_engine = UnifiedDeliverableEngine()

# Standalone functions for backward compatibility
async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """
    Check if workspace is ready for final deliverable and create it if needed.
    Returns deliverable ID if created, None otherwise.
    """
    try:
        return await unified_deliverable_engine.check_and_create_final_deliverable(workspace_id)
    except Exception as e:
        logger.error(f"Error in check_and_create_final_deliverable: {e}")
        return None

async def create_intelligent_deliverable(workspace_id: str, deliverable_type: str, **kwargs) -> Optional[str]:
    """
    Create an intelligent deliverable for the workspace.
    Returns deliverable ID if created, None otherwise.
    """
    try:
        return await unified_deliverable_engine.create_intelligent_deliverable(workspace_id, deliverable_type, **kwargs)
    except Exception as e:
        logger.error(f"Error in create_intelligent_deliverable: {e}")
        return None

# Alias for backward compatibility
deliverable_aggregator = unified_deliverable_engine
