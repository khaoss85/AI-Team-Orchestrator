#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE VERIFICATION TEST
Tests all three critical fixes and their integration points
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fix_1_goal_task_connection():
    """
    🎯 Fix #1: Goal-Task Connection Pipeline Test
    """
    logger.info("🎯 TESTING FIX #1: Goal-Task Connection Pipeline")
    
    try:
        # Test 1: ai_link_task_to_goals function exists and is callable
        from database import ai_link_task_to_goals
        logger.info("✅ ai_link_task_to_goals function found")
        
        # Test 2: create_task properly calls ai_link_task_to_goals
        from database import create_task
        logger.info("✅ create_task function found")
        
        # Test 3: task_analyzer imports exist
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        
        # Check if _handle_goal_progress_update method exists
        if hasattr(analyzer, '_handle_goal_progress_update'):
            logger.info("✅ _handle_goal_progress_update method found")
        else:
            logger.error("❌ _handle_goal_progress_update method missing")
            return False
        
        # Test 4: Check handle_task_completion calls goal progress update
        import inspect
        source = inspect.getsource(analyzer.handle_task_completion)
        if '_handle_goal_progress_update' in source:
            logger.info("✅ handle_task_completion calls _handle_goal_progress_update")
        else:
            logger.error("❌ handle_task_completion doesn't call _handle_goal_progress_update")
            return False
            
        logger.info("🎯 FIX #1: ALL CHECKS PASSED")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error in Fix #1: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Fix #1: {e}")
        return False

async def test_fix_2_real_data_enforcement():
    """
    🤖 Fix #2: Real Data Enforcement Test
    """
    logger.info("🤖 TESTING FIX #2: Real Data Enforcement")
    
    try:
        # Test 1: AIContentEnhancer class exists
        from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
        enhancer = AIContentEnhancer()
        logger.info("✅ AIContentEnhancer class found")
        
        # Test 2: enhance_content_for_business_use method exists
        if hasattr(enhancer, 'enhance_content_for_business_use'):
            logger.info("✅ enhance_content_for_business_use method found")
        else:
            logger.error("❌ enhance_content_for_business_use method missing")
            return False
        
        # Test 3: Check update_task_status integration
        from database import update_task_status
        import inspect
        source = inspect.getsource(update_task_status)
        if 'AIContentEnhancer' in source:
            logger.info("✅ update_task_status integrates AIContentEnhancer")
        else:
            logger.error("❌ update_task_status doesn't integrate AIContentEnhancer")
            return False
        
        # Test 4: Check for content enhancement validation
        if 'enhance_content_for_business_use' in source:
            logger.info("✅ update_task_status calls enhance_content_for_business_use")
        else:
            logger.error("❌ update_task_status doesn't call enhance_content_for_business_use")
            return False
        
        # Test 5: enhancement_orchestrator integration
        try:
            from ai_quality_assurance.enhancement_orchestrator import EnhancementPlan
            logger.info("✅ enhancement_orchestrator module found")
        except ImportError:
            logger.error("❌ enhancement_orchestrator module missing")
            return False
        
        logger.info("🤖 FIX #2: ALL CHECKS PASSED")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error in Fix #2: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Fix #2: {e}")
        return False

async def test_fix_3_memory_driven_intelligence():
    """
    🧠 Fix #3: Memory-Driven Intelligence Test
    """
    logger.info("🧠 TESTING FIX #3: Memory-Driven Intelligence")
    
    try:
        # Test 1: AIMemoryIntelligence class exists
        from ai_quality_assurance.ai_memory_intelligence import AIMemoryIntelligence
        memory_intel = AIMemoryIntelligence()
        logger.info("✅ AIMemoryIntelligence class found")
        
        # Test 2: extract_actionable_insights method exists
        if hasattr(memory_intel, 'extract_actionable_insights'):
            logger.info("✅ extract_actionable_insights method found")
        else:
            logger.error("❌ extract_actionable_insights method missing")
            return False
        
        # Test 3: generate_corrective_actions method exists
        if hasattr(memory_intel, 'generate_corrective_actions'):
            logger.info("✅ generate_corrective_actions method found")
        else:
            logger.error("❌ generate_corrective_actions method missing")
            return False
        
        # Test 4: Check task_analyzer integration
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        
        if hasattr(analyzer, '_handle_memory_intelligence_extraction'):
            logger.info("✅ _handle_memory_intelligence_extraction method found")
        else:
            logger.error("❌ _handle_memory_intelligence_extraction method missing")
            return False
        
        # Test 5: Check handle_task_completion calls memory intelligence
        import inspect
        source = inspect.getsource(analyzer.handle_task_completion)
        if '_handle_memory_intelligence_extraction' in source:
            logger.info("✅ handle_task_completion calls _handle_memory_intelligence_extraction")
        else:
            logger.error("❌ handle_task_completion doesn't call _handle_memory_intelligence_extraction")
            return False
        
        # Test 6: workspace_memory module exists
        try:
            from workspace_memory import WorkspaceMemory, workspace_memory
            logger.info("✅ workspace_memory module found")
        except ImportError:
            logger.error("❌ workspace_memory module missing")
            return False
        
        # Test 7: Memory models exist
        from models import WorkspaceInsight, InsightType, MemoryQueryRequest, MemoryQueryResponse
        logger.info("✅ All memory models found")
        
        logger.info("🧠 FIX #3: ALL CHECKS PASSED")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error in Fix #3: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Fix #3: {e}")
        return False

async def test_integration_flow():
    """
    🔄 Test the complete integration flow
    """
    logger.info("🔄 TESTING INTEGRATION FLOW")
    
    try:
        # Test the complete task completion flow
        from task_analyzer import TaskAnalyzer
        from models import Task, TaskStatus
        
        # Create a mock task
        mock_task = Task(
            id=uuid4(),
            name="Test Integration Task",
            workspace_id=str(uuid4()),
            status=TaskStatus.COMPLETED,
            assigned_to_role="Test Specialist"
        )
        
        mock_result = {
            "test_content": "Sample [Placeholder] content",
            "execution_time_seconds": 5.2,
            "model_used": "gpt-4o-mini"
        }
        
        analyzer = TaskAnalyzer()
        
        # Check that the sequence is correct in handle_task_completion
        import inspect
        source = inspect.getsource(analyzer.handle_task_completion)
        
        # Verify the order: goal progress first, then memory intelligence
        goal_pos = source.find('_handle_goal_progress_update')
        memory_pos = source.find('_handle_memory_intelligence_extraction')
        
        if goal_pos > 0 and memory_pos > 0 and goal_pos < memory_pos:
            logger.info("✅ Integration sequence correct: Goal → Memory → Processing")
        else:
            logger.error("❌ Integration sequence incorrect")
            return False
        
        logger.info("🔄 INTEGRATION FLOW: ALL CHECKS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in integration flow test: {e}")
        return False

async def test_critical_bugs():
    """
    🐛 Test for known critical bugs
    """
    logger.info("🐛 TESTING FOR CRITICAL BUGS")
    
    try:
        # Bug 1: Check for update_data reference error in database.py
        from database import update_task_status
        import inspect
        source = inspect.getsource(update_task_status)
        
        if 'update_data.get(' in source:
            logger.error("❌ CRITICAL BUG: update_data reference error in update_task_status")
            return False
        else:
            logger.info("✅ No update_data reference error found")
        
        # Bug 2: Check for missing async/await patterns
        if 'await enhancer.enhance_content_for_business_use' in source:
            logger.info("✅ Correct async/await pattern for content enhancement")
        else:
            logger.warning("⚠️ Potential async/await issue in content enhancement")
        
        # Bug 3: Check for circular imports
        try:
            from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
            from ai_quality_assurance.ai_memory_intelligence import AIMemoryIntelligence
            from task_analyzer import TaskAnalyzer
            from database import create_task, update_task_status
            logger.info("✅ No circular import issues detected")
        except ImportError as e:
            logger.error(f"❌ Potential circular import: {e}")
            return False
        
        logger.info("🐛 CRITICAL BUGS: ALL CHECKS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in critical bugs test: {e}")
        return False

async def main():
    """
    🔍 Run comprehensive verification of all three fixes
    """
    logger.info("🔍 STARTING COMPREHENSIVE VERIFICATION")
    logger.info("=" * 60)
    
    results = []
    
    # Test each fix
    results.append(("Fix #1: Goal-Task Connection", await test_fix_1_goal_task_connection()))
    results.append(("Fix #2: Real Data Enforcement", await test_fix_2_real_data_enforcement()))
    results.append(("Fix #3: Memory-Driven Intelligence", await test_fix_3_memory_driven_intelligence()))
    results.append(("Integration Flow", await test_integration_flow()))
    results.append(("Critical Bugs Check", await test_critical_bugs()))
    
    logger.info("=" * 60)
    logger.info("🔍 VERIFICATION RESULTS")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - SYSTEM READY")
    else:
        logger.error("💥 SOME TESTS FAILED - NEEDS ATTENTION")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())