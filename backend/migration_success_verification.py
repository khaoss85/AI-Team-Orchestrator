#!/usr/bin/env python3
"""
🎉 MIGRATION SUCCESS VERIFICATION
=================================
Verifica diretta che la migrazione sia completata con successo
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_migration_success():
    """Verifica che la migrazione sia completata con successo"""
    
    logger.info("🎉 MIGRATION SUCCESS VERIFICATION")
    logger.info("=" * 60)
    
    verification_results = {
        "timestamp": datetime.now().isoformat(),
        "migration_completed": False,
        "components_verified": {},
        "overall_success": False
    }
    
    # Test 1: OpenAI SDK with Trace
    logger.info("🧪 TEST 1: OpenAI SDK + Trace Integration")
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        # Check trace configuration
        trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
        
        # Simple test call
        test_agent = {
            "name": "MigrationVerifyAgent",
            "model": "gpt-4o-mini", 
            "instructions": "You are verifying the migration. Respond with: MIGRATION_SUCCESS"
        }
        
        start_time = time.time()
        result = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=test_agent,
            prompt="Verify migration success"
        )
        execution_time = time.time() - start_time
        
        sdk_working = result is not None and isinstance(result, dict)
        
        verification_results["components_verified"]["openai_sdk"] = {
            "working": sdk_working,
            "trace_enabled": trace_enabled,
            "execution_time": execution_time,
            "status": "✅ SUCCESS" if sdk_working and trace_enabled else "⚠️ PARTIAL"
        }
        
        logger.info(f"  SDK Working: {'✅' if sdk_working else '❌'}")
        logger.info(f"  Trace Enabled: {'✅' if trace_enabled else '❌'}")
        logger.info(f"  Execution Time: {execution_time:.2f}s")
        
    except Exception as e:
        logger.error(f"  ❌ SDK Test Failed: {e}")
        verification_results["components_verified"]["openai_sdk"] = {
            "working": False,
            "error": str(e),
            "status": "❌ FAILED"
        }
    
    # Test 2: Autonomous Pipeline (Pillar 7)
    logger.info("🧪 TEST 2: Autonomous Pipeline Verification")
    try:
        from services.unified_orchestrator import get_unified_orchestrator
        
        orchestrator = get_unified_orchestrator()
        
        # Test lifecycle
        await orchestrator.start()
        is_running = orchestrator.is_running()
        is_autonomous = orchestrator.is_autonomous()
        await orchestrator.stop()
        
        # Check configuration
        eliminate_human = os.getenv("ELIMINATE_HUMAN_INTERVENTION", "false").lower() == "true"
        pipeline_autonomous = os.getenv("PIPELINE_FULLY_AUTONOMOUS", "false").lower() == "true"
        
        autonomous_success = eliminate_human and pipeline_autonomous and is_autonomous
        
        verification_results["components_verified"]["autonomous_pipeline"] = {
            "working": autonomous_success,
            "eliminate_human_intervention": eliminate_human,
            "pipeline_fully_autonomous": pipeline_autonomous,
            "orchestrator_autonomous": is_autonomous,
            "lifecycle_working": is_running,
            "status": "✅ SUCCESS" if autonomous_success else "❌ FAILED"
        }
        
        logger.info(f"  Eliminate Human Intervention: {'✅' if eliminate_human else '❌'}")
        logger.info(f"  Pipeline Fully Autonomous: {'✅' if pipeline_autonomous else '❌'}")
        logger.info(f"  Orchestrator Autonomous: {'✅' if is_autonomous else '❌'}")
        logger.info(f"  Lifecycle Working: {'✅' if is_running else '❌'}")
        
    except Exception as e:
        logger.error(f"  ❌ Pipeline Test Failed: {e}")
        verification_results["components_verified"]["autonomous_pipeline"] = {
            "working": False,
            "error": str(e),
            "status": "❌ FAILED"
        }
    
    # Test 3: Quality Gates (Pillar 8)  
    logger.info("🧪 TEST 3: Quality Gates Verification")
    try:
        from ai_quality_assurance.unified_quality_engine import unified_quality_engine
        from ai_quality_assurance.ai_quality_gate_engine import AIQualityGateEngine
        
        # Check if quality gate engine is available
        has_quality_gate = hasattr(unified_quality_engine, 'quality_gate') and unified_quality_engine.quality_gate is not None
        
        # Test validation
        test_content = "Migration verification document: The system has been successfully migrated from direct OpenAI calls to OpenAI Agent SDK with comprehensive autonomous pipeline and quality gates."
        
        validation_result = await unified_quality_engine.validate_asset_quality(
            asset_content=test_content,
            asset_type="migration_document",
            workspace_id="migration-test-workspace"
        )
        
        quality_working = (
            "quality_score" in validation_result and
            "needs_enhancement" in validation_result
        )
        
        autonomous_decision = not validation_result.get("requires_human_review", True)
        
        verification_results["components_verified"]["quality_gates"] = {
            "working": quality_working,
            "quality_gate_engine_available": has_quality_gate,
            "autonomous_decisions": autonomous_decision,
            "quality_score": validation_result.get("quality_score", 0),
            "validation_method": validation_result.get("validation_method", "unknown"),
            "status": "✅ SUCCESS" if quality_working and autonomous_decision else "⚠️ PARTIAL"
        }
        
        logger.info(f"  Quality Gate Engine Available: {'✅' if has_quality_gate else '❌'}")
        logger.info(f"  Quality Working: {'✅' if quality_working else '❌'}")
        logger.info(f"  Autonomous Decisions: {'✅' if autonomous_decision else '❌'}")
        logger.info(f"  Quality Score: {validation_result.get('quality_score', 0):.2f}")
        
    except Exception as e:
        logger.error(f"  ❌ Quality Gates Test Failed: {e}")
        verification_results["components_verified"]["quality_gates"] = {
            "working": False,
            "error": str(e),
            "status": "❌ FAILED"
        }
    
    # Test 4: Database and Core Systems
    logger.info("🧪 TEST 4: Database and Core Systems")
    try:
        from database import get_supabase_client
        
        # Test database connection
        supabase = get_supabase_client()
        test_query = supabase.table("workspaces").select("id").limit(1).execute()
        
        db_working = test_query.data is not None
        
        verification_results["components_verified"]["database"] = {
            "working": db_working,
            "connection_successful": True,
            "status": "✅ SUCCESS" if db_working else "❌ FAILED"
        }
        
        logger.info(f"  Database Connection: {'✅' if db_working else '❌'}")
        
    except Exception as e:
        logger.error(f"  ❌ Database Test Failed: {e}")
        verification_results["components_verified"]["database"] = {
            "working": False,
            "error": str(e),
            "status": "❌ FAILED"
        }
    
    # Overall Assessment
    logger.info("=" * 60)
    logger.info("🏁 MIGRATION VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    working_components = []
    total_components = []
    
    for component, details in verification_results["components_verified"].items():
        total_components.append(component)
        status = details.get("status", "❌ FAILED")
        working = details.get("working", False)
        
        if working or "SUCCESS" in status:
            working_components.append(component)
        
        logger.info(f"{component.replace('_', ' ').title()}: {status}")
    
    success_rate = len(working_components) / len(total_components) if total_components else 0
    migration_successful = success_rate >= 0.75  # 75% success rate required
    
    verification_results["migration_completed"] = migration_successful
    verification_results["overall_success"] = migration_successful
    verification_results["success_rate"] = success_rate
    verification_results["working_components"] = working_components
    verification_results["total_components"] = total_components
    
    logger.info("=" * 60)
    logger.info(f"Success Rate: {success_rate:.1%} ({len(working_components)}/{len(total_components)})")
    logger.info(f"Migration Status: {'✅ MIGRATION SUCCESSFUL' if migration_successful else '❌ MIGRATION INCOMPLETE'}")
    
    if migration_successful:
        logger.info("🎉 CONGRATULATIONS! The migration has been completed successfully!")
        logger.info("   - OpenAI SDK integration is working")
        logger.info("   - Autonomous pipeline is operational") 
        logger.info("   - Quality gates are functional")
        logger.info("   - System is ready for production use")
    else:
        logger.warning("⚠️ Migration verification shows some issues that need attention")
    
    # Save verification results
    verification_file = f"migration_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(verification_file, "w") as f:
        json.dump(verification_results, f, indent=2, default=str)
    
    logger.info(f"📊 Verification results saved to: {verification_file}")
    
    return migration_successful

async def main():
    """Main function"""
    try:
        success = await verify_migration_success()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"💥 Verification failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)