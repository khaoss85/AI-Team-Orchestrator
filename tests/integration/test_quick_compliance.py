#!/usr/bin/env python3
"""
🚀 QUICK COMPLIANCE TEST
========================
Test veloce e concentrato sui risultati principali
"""

import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime

# Add backend to path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_compliance_test():
    """Test veloce di compliance"""
    
    logger.info("🚀 QUICK COMPLIANCE TEST")
    logger.info("=" * 50)
    
    results = {
        "openai_sdk_trace": False,
        "pillar_7_autonomous": False,
        "pillar_8_quality_gates": False,
        "details": {}
    }
    
    try:
        # Test 1: OpenAI SDK + Trace
        logger.info("🧪 TEST 1: OpenAI SDK + Trace")
        
        from services.ai_provider_abstraction import ai_provider_manager
        
        trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
        logger.info(f"Trace enabled: {trace_enabled}")
        
        test_agent = {
            "name": "QuickTestAgent",
            "model": "gpt-4o-mini",
            "instructions": "Respond with: SUCCESS"
        }
        
        start_time = time.time()
        result = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=test_agent,
            prompt="Test"
        )
        execution_time = time.time() - start_time
        
        sdk_success = result and isinstance(result, dict)
        results["openai_sdk_trace"] = sdk_success and trace_enabled
        results["details"]["sdk"] = {"time": execution_time, "trace": trace_enabled}
        
        logger.info(f"✅ SDK + Trace: {'PASS' if results['openai_sdk_trace'] else 'FAIL'}")
        
        # Test 2: Pillar 7 - Autonomous Pipeline
        logger.info("🧪 TEST 2: Pillar 7 - Autonomous Pipeline")
        
        from services.unified_orchestrator import get_unified_orchestrator
        from deliverable_system.unified_deliverable_engine import DeliverablePipeline
        
        orchestrator = get_unified_orchestrator()
        pipeline = DeliverablePipeline()
        
        # Check configuration
        eliminate_human = os.getenv("ELIMINATE_HUMAN_INTERVENTION", "false").lower() == "true"
        autonomous_pipeline = os.getenv("PIPELINE_FULLY_AUTONOMOUS", "false").lower() == "true"
        
        # Test lifecycle
        await orchestrator.start()
        await pipeline.start()
        
        orchestrator_autonomous = orchestrator.is_autonomous()
        orchestrator_running = orchestrator.is_running()
        pipeline_running = pipeline.is_running()
        
        await orchestrator.stop()
        await pipeline.stop()
        
        pillar_7_success = eliminate_human and autonomous_pipeline and orchestrator_autonomous
        results["pillar_7_autonomous"] = pillar_7_success
        results["details"]["pillar_7"] = {
            "eliminate_human": eliminate_human,
            "autonomous_pipeline": autonomous_pipeline,
            "orchestrator_autonomous": orchestrator_autonomous
        }
        
        logger.info(f"✅ Pillar 7: {'PASS' if results['pillar_7_autonomous'] else 'FAIL'}")
        
        # Test 3: Pillar 8 - Quality Gates
        logger.info("🧪 TEST 3: Pillar 8 - Quality Gates")
        
        from ai_quality_assurance.unified_quality_engine import unified_quality_engine
        
        test_content = "Business analysis document with market research and strategic recommendations."
        
        validation_result = await unified_quality_engine.validate_asset_quality(
            asset_content=test_content,
            asset_type="business_document",
            workspace_id="test-workspace"
        )
        
        quality_gates_success = (
            "quality_score" in validation_result and
            "needs_enhancement" in validation_result and
            not validation_result.get("requires_human_review", True)
        )
        
        results["pillar_8_quality_gates"] = quality_gates_success
        results["details"]["pillar_8"] = {
            "validation_method": validation_result.get("validation_method", "unknown"),
            "quality_score": validation_result.get("quality_score", 0),
            "autonomous_decision": not validation_result.get("requires_human_review", True)
        }
        
        logger.info(f"✅ Pillar 8: {'PASS' if results['pillar_8_quality_gates'] else 'FAIL'}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    
    # Summary
    logger.info("=" * 50)
    logger.info("🏁 COMPLIANCE SUMMARY")
    logger.info("=" * 50)
    
    total_tests = len([k for k in results.keys() if k != "details"])
    passed_tests = sum(results[k] for k in results.keys() if k != "details")
    
    for test_name, result in results.items():
        if test_name != "details":
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
    
    success_rate = passed_tests / total_tests
    overall_success = success_rate >= 0.75  # 3/4 tests must pass
    
    logger.info(f"Success Rate: {success_rate:.1%}")
    logger.info(f"Overall Result: {'✅ SYSTEM COMPLIANT' if overall_success else '❌ SYSTEM NOT COMPLIANT'}")
    
    # Save results
    with open("quick_compliance_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("📊 Results saved to quick_compliance_results.json")
    
    return overall_success

async def main():
    """Main function"""
    success = await quick_compliance_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)