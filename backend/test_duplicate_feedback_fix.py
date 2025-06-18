#!/usr/bin/env python3
"""
Test script to verify the duplicate feedback request fix

This script tests the enhanced duplicate prevention logic in the human verification system.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from human_verification_system import HumanVerificationSystem, VerificationCheckpoint, VerificationStatus
from database import create_human_feedback_request, get_human_feedback_requests, delete_human_feedback_requests_by_workspace

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_duplicate_prevention():
    """Test the enhanced duplicate prevention mechanism"""
    
    logger.info("🔧 TESTING DUPLICATE FEEDBACK REQUEST PREVENTION")
    
    # Create test workspace and task IDs (using valid UUIDs)
    import uuid
    test_workspace_id = str(uuid.uuid4())
    test_task_id_1 = str(uuid.uuid4())
    test_task_id_2 = str(uuid.uuid4())
    test_asset_type = "contact_database"
    
    logger.info(f"Using test workspace ID: {test_workspace_id}")
    
    # Clean up any existing test data
    try:
        await delete_human_feedback_requests_by_workspace(test_workspace_id)
        logger.info(f"✅ Cleaned up existing test data for workspace {test_workspace_id}")
    except Exception as e:
        logger.info(f"⚠️ No existing test data to clean up: {e}")
    
    # Initialize human verification system
    hvs = HumanVerificationSystem()
    
    # Test 1: Basic duplicate prevention by task ID
    logger.info("\n📝 TEST 1: Task-level duplicate prevention")
    
    checkpoint1 = await hvs.create_verification_checkpoint(
        workspace_id=test_workspace_id,
        task_id=test_task_id_1,
        task_name="Create customer contact database",
        asset_type=test_asset_type,
        deliverable_data={"contacts": [{"name": "Test Contact", "email": "test@example.com"}]},
        quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
    )
    
    if checkpoint1:
        logger.info(f"✅ Created first checkpoint: {checkpoint1.id}")
    else:
        logger.info("❌ First checkpoint was not created (auto-approved)")
        return False
    
    # Try to create duplicate for same task
    checkpoint1_duplicate = await hvs.create_verification_checkpoint(
        workspace_id=test_workspace_id,
        task_id=test_task_id_1,  # Same task ID
        task_name="Create customer contact database (duplicate attempt)",
        asset_type=test_asset_type,
        deliverable_data={"contacts": [{"name": "Different Contact", "email": "different@example.com"}]},
        quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
    )
    
    if checkpoint1_duplicate and checkpoint1_duplicate.id == checkpoint1.id:
        logger.info("✅ Task-level duplicate prevention WORKING: Returned existing checkpoint")
    else:
        logger.error("❌ Task-level duplicate prevention FAILED: Created new checkpoint")
        return False
    
    # Test 2: Workspace-level duplicate prevention by asset type
    logger.info("\n📝 TEST 2: Workspace-level duplicate prevention")
    
    checkpoint2 = await hvs.create_verification_checkpoint(
        workspace_id=test_workspace_id,
        task_id=test_task_id_2,  # Different task ID
        task_name="Create another customer contact database",
        asset_type=test_asset_type,  # Same asset type
        deliverable_data={"contacts": [{"name": "Another Contact", "email": "another@example.com"}]},
        quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
    )
    
    if checkpoint2 and checkpoint2.id == checkpoint1.id:
        logger.info("✅ Workspace-level duplicate prevention WORKING: Returned existing checkpoint")
    else:
        logger.error("❌ Workspace-level duplicate prevention FAILED: Created new checkpoint")
        return False
    
    # Test 3: Database-level duplicate prevention
    logger.info("\n📝 TEST 3: Database-level duplicate prevention")
    
    # Create a database feedback request directly to simulate existing request
    db_request = await create_human_feedback_request(
        workspace_id=test_workspace_id,
        request_type="contact_database_verification",
        title="Test Database Request",
        description="Test request to check database-level duplicate prevention",
        proposed_actions=[{"action": "approve", "label": "Approve"}],
        context={"asset_type": test_asset_type},
        priority="medium",
        timeout_hours=24
    )
    
    if db_request:
        logger.info(f"✅ Created database request: {db_request['id']}")
        
        # Now try to create checkpoint with enhanced duplicate detection
        new_hvs = HumanVerificationSystem()  # Fresh instance
        checkpoint3 = await new_hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id="test-task-999",
            task_name="Yet another contact database",
            asset_type=test_asset_type,
            deliverable_data={"contacts": [{"name": "Third Contact", "email": "third@example.com"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
        
        if checkpoint3 is None:
            logger.info("✅ Database-level duplicate prevention WORKING: No checkpoint created")
        else:
            logger.error("❌ Database-level duplicate prevention FAILED: Created checkpoint despite existing DB request")
            return False
    else:
        logger.error("❌ Failed to create test database request")
        return False
    
    # Test 4: Check that different asset types don't trigger false positives
    logger.info("\n📝 TEST 4: Different asset types should not conflict")
    
    checkpoint4 = await hvs.create_verification_checkpoint(
        workspace_id=test_workspace_id,
        task_id="test-task-different",
        task_name="Create email sequence",
        asset_type="email_sequence",  # Different asset type
        deliverable_data={"emails": [{"subject": "Test Email", "body": "Test content"}]},
        quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
    )
    
    if checkpoint4 and checkpoint4.asset_type == "email_sequence":
        logger.info("✅ Different asset type WORKING: Created separate checkpoint")
    else:
        logger.error("❌ Different asset type FAILED: Should have created new checkpoint")
        return False
    
    # Clean up test data
    logger.info("\n🧹 CLEANING UP TEST DATA")
    try:
        await delete_human_feedback_requests_by_workspace(test_workspace_id)
        logger.info("✅ Cleaned up test database requests")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup warning: {e}")
    
    logger.info("\n🎉 ALL TESTS PASSED: Duplicate prevention is working correctly!")
    return True

async def test_concurrent_creation():
    """Test concurrent checkpoint creation to check for race conditions"""
    
    logger.info("\n🏃 TESTING CONCURRENT CHECKPOINT CREATION")
    
    import uuid
    test_workspace_id = str(uuid.uuid4())
    test_asset_type = "contact_database"
    
    # Clean up
    try:
        await delete_human_feedback_requests_by_workspace(test_workspace_id)
    except:
        pass
    
    async def create_checkpoint(task_suffix):
        """Helper function to create checkpoint"""
        hvs = HumanVerificationSystem()
        return await hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id=f"concurrent-task-{task_suffix}",
            task_name=f"Concurrent customer contact database {task_suffix}",
            asset_type=test_asset_type,
            deliverable_data={"contacts": [{"name": f"Contact {task_suffix}"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
    
    # Create multiple checkpoints concurrently
    tasks = [create_checkpoint(i) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check results
    successful_checkpoints = [r for r in results if isinstance(r, VerificationCheckpoint)]
    none_results = [r for r in results if r is None]
    exceptions = [r for r in results if isinstance(r, Exception)]
    
    logger.info(f"📊 CONCURRENT RESULTS:")
    logger.info(f"   - Successful checkpoints: {len(successful_checkpoints)}")
    logger.info(f"   - None results (duplicates prevented): {len(none_results)}")
    logger.info(f"   - Exceptions: {len(exceptions)}")
    
    if exceptions:
        for i, exc in enumerate(exceptions):
            logger.error(f"   - Exception {i}: {exc}")
    
    # Verify only one unique checkpoint was created
    unique_checkpoints = set()
    for checkpoint in successful_checkpoints:
        if checkpoint:
            unique_checkpoints.add(checkpoint.id)
    
    if len(unique_checkpoints) <= 1:
        logger.info("✅ Concurrent creation test PASSED: Only one unique checkpoint created")
        return True
    else:
        logger.error(f"❌ Concurrent creation test FAILED: {len(unique_checkpoints)} unique checkpoints created")
        return False

async def main():
    """Run all tests"""
    try:
        logger.info("🚀 STARTING DUPLICATE FEEDBACK REQUEST TESTS")
        
        # Test basic duplicate prevention
        test1_passed = await test_duplicate_prevention()
        
        # Test concurrent creation
        test2_passed = await test_concurrent_creation()
        
        if test1_passed and test2_passed:
            logger.info("\n🎉 ALL TESTS PASSED! Duplicate prevention fix is working correctly.")
            return True
        else:
            logger.error("\n❌ SOME TESTS FAILED! Please review the duplicate prevention logic.")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST EXECUTION FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)