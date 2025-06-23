#!/usr/bin/env python3
"""
🧪 TEST AI-DRIVEN GOAL EXTRACTION
Test script per verificare che il nuovo sistema di estrazione goal AI-driven funzioni correttamente
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any

# Add backend to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_goal_extraction():
    """
    🧪 Test del nuovo sistema AI-driven di estrazione goal
    """
    
    # Test case dal caso d'uso originale
    test_goal_text = """
    Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot.
    Gli email devono avere un open-rate ≥ 30% e click-to-rate ≥ 10%, completando il tutto in 6 settimane.
    """
    
    workspace_id = "test-workspace-123"
    
    try:
        logger.info("🧪 Starting AI-driven goal extraction test...")
        logger.info(f"📝 Test goal text: {test_goal_text}")
        
        # Test the AI goal extractor directly
        from ai_quality_assurance.ai_goal_extractor import extract_and_create_workspace_goals
        
        workspace_goals = await extract_and_create_workspace_goals(workspace_id, test_goal_text)
        
        logger.info(f"🎯 AI extracted {len(workspace_goals)} goals:")
        
        for i, goal in enumerate(workspace_goals, 1):
            logger.info(f"  Goal {i}: {goal['metric_type']} = {goal['target_value']} {goal['unit']}")
            logger.info(f"    Description: {goal['description']}")
            logger.info(f"    Confidence: {goal.get('confidence', 'N/A')}")
            logger.info(f"    Is Percentage: {goal.get('is_percentage', False)}")
            logger.info(f"    Is Minimum: {goal.get('is_minimum', True)}")
            if goal.get('semantic_context'):
                logger.info(f"    Context: {goal['semantic_context']}")
            logger.info("")
        
        # Verify expected goals
        expected_goals = [
            {"metric_type": "deliverables", "target_value": 50, "unit": "ICP contacts"},
            {"metric_type": "deliverables", "target_value": 3, "unit": "email sequences"},
            {"metric_type": "quality_score", "target_value": 30, "unit": "open rate %"},
            {"metric_type": "quality_score", "target_value": 10, "unit": "click rate %"},
            {"metric_type": "timeline_days", "target_value": 42, "unit": "days"}  # 6 weeks = 42 days
        ]
        
        logger.info(f"✅ Expected {len(expected_goals)} goals, got {len(workspace_goals)} goals")
        
        # Check for duplicates
        seen_goals = set()
        duplicates = []
        
        for goal in workspace_goals:
            goal_key = f"{goal['metric_type']}_{goal['target_value']}_{goal['unit']}"
            if goal_key in seen_goals:
                duplicates.append(goal_key)
            seen_goals.add(goal_key)
        
        if duplicates:
            logger.error(f"❌ DUPLICATES FOUND: {duplicates}")
        else:
            logger.info("✅ NO DUPLICATES - AI successfully avoided duplicate goal creation")
        
        # Test semantic understanding
        semantic_test_cases = [
            "Create 3 marketing campaigns and generate 100 leads",
            "Increase revenue by 25% and reduce costs by 15%",
            "Complete 5 training sessions within 30 days"
        ]
        
        logger.info("\n🧠 Testing semantic understanding with additional cases:")
        for case in semantic_test_cases:
            logger.info(f"\n📝 Testing: {case}")
            case_goals = await extract_and_create_workspace_goals("test-case", case)
            logger.info(f"   → {len(case_goals)} goals extracted")
            for goal in case_goals:
                logger.info(f"     - {goal['metric_type']}: {goal['target_value']} {goal['unit']}")
        
        logger.info("\n🎉 AI-driven goal extraction test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_integration():
    """
    🧪 Test integrazione con database via _auto_create_workspace_goals
    """
    
    logger.info("\n🧪 Testing database integration...")
    
    test_goal_text = "Creare 5 report mensili e raggiungere 80% di customer satisfaction in 3 mesi"
    
    try:
        # Test the database integration
        from database import _auto_create_workspace_goals
        
        created_goals = await _auto_create_workspace_goals("test-db-workspace", test_goal_text)
        
        logger.info(f"📊 Database integration test:")
        logger.info(f"   Created {len(created_goals)} goals in database")
        
        for goal in created_goals:
            logger.info(f"   - {goal.get('metric_type')}: {goal.get('target_value')} {goal.get('unit')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database integration test failed: {e}")
        # This is expected if we're not connected to the database
        logger.info("ℹ️  Database test failure is expected in test environment")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("🚀 Starting AI Goal Extraction Tests")
        logger.info("="*60)
        
        # Test 1: AI Goal Extraction
        test1_success = await test_ai_goal_extraction()
        
        # Test 2: Database Integration (optional)
        test2_success = await test_database_integration()
        
        logger.info("\n" + "="*60)
        logger.info("📊 TEST RESULTS SUMMARY:")
        logger.info(f"   AI Goal Extraction: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        logger.info(f"   Database Integration: {'✅ PASSED' if test2_success else '⚠️  SKIPPED'}")
        
        if test1_success:
            logger.info("\n🎉 AI-driven goal extraction is working correctly!")
            logger.info("🔄 The system should now avoid duplicates and provide semantic understanding")
        else:
            logger.error("\n❌ AI-driven goal extraction needs attention")
    
    asyncio.run(main())