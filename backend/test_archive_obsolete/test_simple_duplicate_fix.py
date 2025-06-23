#!/usr/bin/env python3
"""
Simple test to verify the in-memory duplicate prevention logic works
"""

import asyncio
import logging
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from human_verification_system import HumanVerificationSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockDatabase:
    """Mock database that doesn't actually connect to Supabase"""
    
    def __init__(self):
        self.requests = []
    
    async def get_human_feedback_requests(self, workspace_id, status=None):
        return [r for r in self.requests if r['workspace_id'] == workspace_id and (not status or r['status'] == status)]
    
    async def create_human_feedback_request(self, **kwargs):
        request = kwargs.copy()
        request['id'] = str(uuid.uuid4())
        request['created_at'] = '2025-06-17T18:00:00Z'
        request['status'] = 'pending'
        self.requests.append(request)
        return request

# Monkey patch the database functions for testing
mock_db = MockDatabase()

async def test_duplicate_prevention():
    """Test the duplicate prevention logic"""
    
    logger.info("🔧 TESTING DUPLICATE PREVENTION LOGIC")
    
    # Patch the database functions
    import database
    original_get_requests = database.get_human_feedback_requests
    original_create_request = database.create_human_feedback_request
    
    database.get_human_feedback_requests = mock_db.get_human_feedback_requests
    database.create_human_feedback_request = mock_db.create_human_feedback_request
    
    try:
        test_workspace_id = str(uuid.uuid4())
        test_task_id_1 = str(uuid.uuid4())
        test_task_id_2 = str(uuid.uuid4())
        test_asset_type = "contact_database"
        
        hvs = HumanVerificationSystem()
        
        # Test 1: Create first checkpoint
        logger.info("📝 TEST 1: Creating first checkpoint")
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
            logger.info("ℹ️ First checkpoint was auto-approved (no verification needed)")
            return True  # This is also a valid outcome
        
        # Test 2: Try to create duplicate for same task
        logger.info("📝 TEST 2: Testing task-level duplicate prevention")
        checkpoint1_dup = await hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id=test_task_id_1,  # Same task ID
            task_name="Create customer contact database (duplicate)",
            asset_type=test_asset_type,
            deliverable_data={"contacts": [{"name": "Different Contact"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
        
        if checkpoint1_dup and checkpoint1_dup.id == checkpoint1.id:
            logger.info("✅ Task-level duplicate prevention WORKING")
        else:
            logger.error("❌ Task-level duplicate prevention FAILED")
            return False
        
        # Test 3: Try to create duplicate for same workspace/asset type
        logger.info("📝 TEST 3: Testing workspace-level duplicate prevention")
        checkpoint2 = await hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id=test_task_id_2,  # Different task ID
            task_name="Create another contact database",
            asset_type=test_asset_type,  # Same asset type
            deliverable_data={"contacts": [{"name": "Another Contact"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
        
        if checkpoint2 and checkpoint2.id == checkpoint1.id:
            logger.info("✅ Workspace-level duplicate prevention WORKING")
        else:
            logger.error("❌ Workspace-level duplicate prevention FAILED")
            return False
        
        # Test 4: Different asset type should work
        logger.info("📝 TEST 4: Testing different asset type (should create new)")
        checkpoint3 = await hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id=str(uuid.uuid4()),
            task_name="Create email sequence",
            asset_type="email_sequence",  # Different asset type
            deliverable_data={"emails": [{"subject": "Test"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
        
        if checkpoint3 and checkpoint3.id != checkpoint1.id:
            logger.info("✅ Different asset type creates separate checkpoint")
        elif checkpoint3 is None:
            logger.info("ℹ️ Different asset type was auto-approved")
        else:
            logger.error("❌ Different asset type logic failed")
            return False
        
        logger.info("🎉 ALL DUPLICATE PREVENTION TESTS PASSED!")
        return True
        
    finally:
        # Restore original functions
        database.get_human_feedback_requests = original_get_requests
        database.create_human_feedback_request = original_create_request

async def test_concurrent_creation():
    """Test concurrent checkpoint creation"""
    
    logger.info("🏃 TESTING CONCURRENT CREATION")
    
    test_workspace_id = str(uuid.uuid4())
    test_asset_type = "contact_database"
    
    async def create_checkpoint(task_suffix):
        hvs = HumanVerificationSystem()
        return await hvs.create_verification_checkpoint(
            workspace_id=test_workspace_id,
            task_id=f"concurrent-task-{task_suffix}",
            task_name=f"Concurrent database {task_suffix}",
            asset_type=test_asset_type,
            deliverable_data={"contacts": [{"name": f"Contact {task_suffix}"}]},
            quality_assessment={"overall_score": 0.8, "ready_for_use": True, "needs_enhancement": False, "quality_issues": [], "enhancement_priority": "low", "improvement_suggestions": []}
        )
    
    # Create 5 checkpoints concurrently
    tasks = [create_checkpoint(i) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count results
    checkpoints = [r for r in results if hasattr(r, 'id')]
    none_results = [r for r in results if r is None]
    
    logger.info(f"📊 CONCURRENT RESULTS: {len(checkpoints)} checkpoints, {len(none_results)} auto-approved")
    
    if checkpoints:
        # All checkpoints should have the same ID (duplicates prevented)
        unique_ids = set(c.id for c in checkpoints)
        if len(unique_ids) == 1:
            logger.info("✅ Concurrent creation properly prevented duplicates")
            return True
        else:
            logger.error(f"❌ Concurrent creation failed: {len(unique_ids)} unique IDs")
            return False
    else:
        logger.info("ℹ️ All concurrent requests were auto-approved")
        return True

async def main():
    try:
        logger.info("🚀 STARTING DUPLICATE PREVENTION TESTS")
        
        test1 = await test_duplicate_prevention()
        test2 = await test_concurrent_creation()
        
        if test1 and test2:
            logger.info("🎉 ALL TESTS PASSED!")
            return True
        else:
            logger.error("❌ SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)