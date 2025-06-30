#!/usr/bin/env python3
"""
🔍 Test diretto dell'AssetRequirementsGenerator
"""

import asyncio
import logging
from uuid import UUID

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_asset_generation():
    """Test diretto della generazione asset requirements"""
    
    print("🔍 TESTING DIRECT ASSET REQUIREMENTS GENERATION")
    print("=" * 60)
    
    try:
        # Import and initialize
        from services.asset_requirements_generator import AssetRequirementsGenerator
        from models import WorkspaceGoal
        
        generator = AssetRequirementsGenerator()
        print("✅ AssetRequirementsGenerator initialized")
        
        # Create a test goal
        test_goal = WorkspaceGoal(
            id=UUID("3cc07f9a-4ee8-4c58-a97a-db1b99038d30"),
            workspace_id=UUID("2f32d993-ef56-4b65-ac0f-3dcebf654b5e"),
            metric_type="api_documentation",
            target_value=100.0,
            current_value=0.0,
            description="Create comprehensive REST API documentation with examples, authentication guide, and deployment instructions",
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
        
        print("✅ Test goal created")
        
        # Generate asset requirements
        print("🎯 Generating asset requirements...")
        requirements = await generator.generate_from_goal(test_goal)
        
        print(f"✅ Generated {len(requirements)} asset requirements:")
        for req in requirements:
            print(f"  • {req.asset_name} ({req.asset_type})")
            print(f"    Description: {req.description[:100]}...")
            print(f"    Priority: {req.priority}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_asset_generation())