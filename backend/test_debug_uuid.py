#!/usr/bin/env python3
"""
🔍 Debug UUID fields in AssetRequirement
"""

import asyncio
import logging
from uuid import UUID, uuid4

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_debug_uuid_fields():
    """Debug esatto dei campi UUID"""
    
    print("🔍 DEBUGGING UUID FIELDS")
    print("=" * 40)
    
    try:
        # Import and initialize
        from services.asset_requirements_generator import AssetRequirementsGenerator
        from models import WorkspaceGoal
        
        generator = AssetRequirementsGenerator()
        print("✅ Generator initialized")
        
        # Create test goal with explicit workspace_id
        test_goal = WorkspaceGoal(
            id=UUID("3cc07f9a-4ee8-4c58-a97a-db1b99038d30"),
            workspace_id=UUID("2f32d993-ef56-4b65-ac0f-3dcebf654b5e"),  # Explicit UUID
            metric_type="api_documentation",
            target_value=100.0,
            current_value=0.0,
            description="Create comprehensive REST API documentation",
            priority=1,
            status="active",
            created_at="2025-06-25T12:51:33.500628+00:00",
            updated_at="2025-06-25T12:51:33.500639+00:00",
            validation_frequency_minutes=20,
            confidence=0.8,
            semantic_context={},
            goal_type="deliverable",
            is_percentage=False,
            is_minimum=True,
            progress_percentage=0.0,
            asset_completion_rate=0.0,
            quality_score=0.0,
            asset_requirements_count=0,
            assets_completed_count=0,
            ai_validation_enabled=True,
            memory_insights={}
        )
        
        print(f"Goal ID: {test_goal.id} (type: {type(test_goal.id)})")
        print(f"Workspace ID: {test_goal.workspace_id} (type: {type(test_goal.workspace_id)})")
        
        # Test single requirement creation manually
        from models import AssetRequirement
        from database_asset_extensions import AssetDrivenDatabaseManager
        
        # Create requirement manually
        test_requirement = AssetRequirement(
            id=uuid4(),
            goal_id=test_goal.id,
            workspace_id=test_goal.workspace_id,
            asset_name="Test API Documentation",
            description="Test requirement",
            asset_type="document",
            asset_format="structured_data",
            priority="high",
            estimated_effort="medium",
            user_impact="high",
            weight=1.0,
            mandatory=True,
            business_value_score=0.8,
            acceptance_criteria={},
            validation_rules={},
            value_proposition="Test value",
            status="pending",
            progress_percentage=0.0,
            ai_generated=True,
            language_agnostic=True,
            sdk_compatible=True
        )
        
        print(f"Requirement ID: {test_requirement.id} (type: {type(test_requirement.id)})")
        print(f"Requirement Goal ID: {test_requirement.goal_id} (type: {type(test_requirement.goal_id)})")
        print(f"Requirement Workspace ID: {test_requirement.workspace_id} (type: {type(test_requirement.workspace_id)})")
        
        # Test database insertion
        db_manager = AssetDrivenDatabaseManager()
        print("📥 Attempting to save requirement...")
        
        saved_requirement = await db_manager.create_asset_requirement(test_requirement)
        print(f"✅ Saved requirement: {saved_requirement.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug_uuid_fields())