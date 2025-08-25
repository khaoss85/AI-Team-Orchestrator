#!/usr/bin/env python3
"""
Comprehensive test for holistic quality integration
Tests the new AI-driven quality assessment vs the old primitive validation
"""
import os
import asyncio
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_holistic_quality_integration():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
    
    logger.info("🧪 TESTING: Holistic Quality Integration")
    logger.info("=" * 60)
    
    try:
        # Get the completed task that failed before
        response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
        
        if not response.data:
            logger.error("❌ No completed tasks found for testing")
            return
            
        test_task = response.data[0]
        logger.info(f"📋 Testing with task: {test_task.get('id')}")
        logger.info(f"   Description: {test_task.get('description')}")
        logger.info(f"   Result: {test_task.get('result')}")
        
        # Test 1: Old primitive validation
        logger.info("\n🔍 TEST 1: Old Primitive Validation")
        result = test_task.get('result', {})
        old_validation = _has_meaningful_content_old(result)
        logger.info(f"   Old validation result: {old_validation}")
        
        # Test 2: AI Quality Assessment
        logger.info("\n🤖 TEST 2: AI Quality Assessment")
        try:
            from ai_quality_assurance.unified_quality_engine import smart_evaluator
            
            task_content = str(result) if result else ""
            logger.info(f"   Content to analyze: {task_content[:100]}...")
            
            quality_assessment = await smart_evaluator.evaluate_asset_quality(
                content=task_content,
                task_context={
                    'task_id': test_task.get('id'),
                    'goal_id': 'test-goal',
                    'agent_name': test_task.get('agent_id', 'unknown'),
                    'domain': 'business_deliverable'
                },
                workspace_id=workspace_id
            )
            
            logger.info(f"   AI Assessment Result:")
            logger.info(f"     Overall Score: {quality_assessment.get('overall_score', 'N/A')}")
            logger.info(f"     Has Business Value: {quality_assessment.get('has_business_value', 'N/A')}")
            logger.info(f"     Quality Category: {quality_assessment.get('quality_category', 'N/A')}")
            logger.info(f"     Feedback: {quality_assessment.get('feedback', 'N/A')}")
            
        except Exception as e:
            logger.error(f"   ❌ AI Quality Assessment failed: {e}")
            quality_assessment = None
        
        # Test 3: Unified Deliverable Engine Integration
        logger.info("\n🔗 TEST 3: Unified Deliverable Engine Integration")
        try:
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            
            # Get a real goal ID from the workspace
            goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).limit(1).execute()
            
            if goals_response.data:
                goal_id = goals_response.data[0]['id']
                logger.info(f"   Testing with goal: {goal_id}")
                
                # This will test the new holistic validation
                deliverable_result = await create_goal_specific_deliverable(workspace_id, goal_id, force=True)
                
                if deliverable_result:
                    logger.info(f"   ✅ Deliverable created successfully: {deliverable_result.get('id')}")
                    
                    # Check if quality scores are present
                    quality_metrics = deliverable_result.get('quality_metrics', {})
                    logger.info(f"   Quality Metrics:")
                    logger.info(f"     AI Quality Score: {quality_metrics.get('ai_quality_score', 'N/A')}")
                    logger.info(f"     Aggregation Score: {quality_metrics.get('aggregation_quality_score', 'N/A')}")
                    logger.info(f"     Final Score: {quality_metrics.get('final_quality_score', 'N/A')}")
                else:
                    logger.info(f"   ℹ️ No deliverable created (likely due to quality validation)")
            else:
                logger.warning("   ⚠️ No goals found for testing")
                
        except Exception as e:
            logger.error(f"   ❌ Unified Engine test failed: {e}")
        
        # Test 4: Compare Results
        logger.info("\n📊 TEST 4: Results Comparison")
        logger.info("   Old Primitive Validation:")
        logger.info(f"     Result: {old_validation} (simple content check)")
        
        if quality_assessment:
            logger.info("   New AI Quality Assessment:")
            logger.info(f"     Business Value: {quality_assessment.get('has_business_value', False)}")
            logger.info(f"     Quality Score: {quality_assessment.get('overall_score', 0)}%")
            logger.info(f"     Would Pass: {quality_assessment.get('has_business_value', False) and quality_assessment.get('overall_score', 0) > 30}")
        
        # Test 5: Integration Check
        logger.info("\n🔧 TEST 5: Integration Health Check")
        
        # Check if unified quality engine is properly imported
        try:
            from ai_quality_assurance.unified_quality_engine import UnifiedQualityEngine
            engine = UnifiedQualityEngine()
            logger.info("   ✅ Unified Quality Engine: Available")
        except Exception as e:
            logger.error(f"   ❌ Unified Quality Engine: {e}")
        
        # Check if deliverable engine uses quality assessment
        try:
            import inspect
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            source = inspect.getsource(create_goal_specific_deliverable)
            
            if "smart_evaluator" in source:
                logger.info("   ✅ Deliverable Engine: Integrated with Quality Engine")
            else:
                logger.error("   ❌ Deliverable Engine: NOT integrated with Quality Engine")
                
            if "evaluate_asset_quality" in source:
                logger.info("   ✅ Quality Assessment: Being called")
            else:
                logger.error("   ❌ Quality Assessment: NOT being called")
                
        except Exception as e:
            logger.error(f"   ❌ Integration check failed: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🏁 TEST COMPLETED")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")

def _has_meaningful_content_old(task_result: dict) -> bool:
    """Old primitive validation for comparison"""
    if not isinstance(task_result, dict):
        return False
    
    # Check for explicit failure indicators
    failure_indicators = ['timeout', 'error', 'failed', 'exception']
    for indicator in failure_indicators:
        if indicator in task_result:
            return False
    
    # Check for meaningful content fields
    content_fields = ['content', 'result', 'output', 'data', 'csv', 'contacts', 'list']
    has_content = False
    
    for field in content_fields:
        if field in task_result:
            value = task_result[field]
            if isinstance(value, str) and len(value.strip()) > 20:  # At least 20 chars of content
                has_content = True
                break
            elif isinstance(value, (list, dict)) and value:  # Non-empty list or dict
                has_content = True
                break
    
    return has_content

if __name__ == "__main__":
    asyncio.run(test_holistic_quality_integration())