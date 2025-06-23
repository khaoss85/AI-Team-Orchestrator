#!/usr/bin/env python3
"""
🔍 VERIFY ALL FIXES STATUS
Controlla che tutti i fix implementati siano effettivamente applicati e funzionanti
"""

import os
import sys
import logging
import asyncio

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_fix_1_goal_metric_type_removal():
    """✅ Fix 1: Rimozione GoalMetricType enum deprecato"""
    logger.info("🔍 Check 1: GoalMetricType enum removal")
    
    try:
        from models import GoalMetricType
        logger.error("  ❌ FAIL: GoalMetricType enum still exists in models.py!")
        return False
    except ImportError:
        logger.info("  ✅ PASS: GoalMetricType enum successfully removed")
        return True

def check_fix_2_hardcoded_mappings_removal():
    """✅ Fix 2: Rimozione mapping hardcoded da goal_driven_task_planner.py"""
    logger.info("🔍 Check 2: Hard-coded business mappings removal")
    
    try:
        # Check if old method still exists
        with open("goal_driven_task_planner.py", "r") as f:
            content = f.read()
        
        # Should NOT contain hardcoded business mappings
        violations = []
        if "'contacts': " in content and "GoalMetricType.CONTACTS" in content:
            violations.append("Hardcoded contacts mapping found")
        if "'email_sequences': " in content and "GoalMetricType.EMAIL_SEQUENCES" in content:
            violations.append("Hardcoded email_sequences mapping found")
        if "'campaigns': " in content and "GoalMetricType.CAMPAIGNS" in content:
            violations.append("Hardcoded campaigns mapping found")
        
        # Should contain AI-driven classification
        if "_classify_metric_type_ai" not in content:
            violations.append("AI-driven classification method missing")
        
        if violations:
            logger.error(f"  ❌ FAIL: {', '.join(violations)}")
            return False
        else:
            logger.info("  ✅ PASS: Hard-coded mappings removed, AI classification implemented")
            return True
            
    except Exception as e:
        logger.error(f"  ❌ ERROR: Cannot verify mappings removal - {e}")
        return False

def check_fix_3_openai_agent_model_attribute():
    """✅ Fix 3: OpenAI Agent model attribute fix in specialist.py"""
    logger.info("🔍 Check 3: OpenAI Agent model attribute fix")
    
    try:
        with open("ai_agents/specialist.py", "r") as f:
            content = f.read()
        
        # Should contain getattr pattern for model access
        if "getattr(self.agent, 'model', getattr(self.agent, '_model'" in content:
            logger.info("  ✅ PASS: OpenAI Agent model attribute fix implemented")
            return True
        else:
            logger.error("  ❌ FAIL: OpenAI Agent model fix pattern not found")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ ERROR: Cannot verify agent model fix - {e}")
        return False

def check_fix_4_dynamic_prompt_enhancer():
    """✅ Fix 4: DynamicPromptEnhancer import fix"""
    logger.info("🔍 Check 4: DynamicPromptEnhancer import")
    
    try:
        from ai_quality_assurance.quality_integration import DynamicPromptEnhancer
        
        # Test basic functionality
        test_prompt = DynamicPromptEnhancer.enhance_specialist_prompt_for_quality("test")
        if "CONCRETE CONTENT CHECKLIST" in test_prompt:
            logger.info("  ✅ PASS: DynamicPromptEnhancer import and functionality working")
            return True
        else:
            logger.error("  ❌ FAIL: DynamicPromptEnhancer not functioning correctly")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ FAIL: DynamicPromptEnhancer import failed - {e}")
        return False

def check_fix_5_database_universal_mapping():
    """✅ Fix 5: Database universal mapping (no hardcoded business logic)"""
    logger.info("🔍 Check 5: Database universal mapping")
    
    try:
        from database import _map_requirement_to_metric_type
        
        # Test that it returns universal categories
        test_result = _map_requirement_to_metric_type("test_metric")
        universal_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                              "engagement_metrics", "completion_metrics"]
        
        if test_result in universal_categories:
            logger.info(f"  ✅ PASS: Database mapping returns universal category: {test_result}")
            return True
        else:
            logger.error(f"  ❌ FAIL: Database mapping returns non-universal category: {test_result}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ ERROR: Cannot verify database mapping - {e}")
        return False

async def check_fix_6_ai_driven_classification():
    """✅ Fix 6: AI-driven metric classification functionality"""
    logger.info("🔍 Check 6: AI-driven metric classification")
    
    try:
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        planner = GoalDrivenTaskPlanner()
        
        # Test AI classification
        if hasattr(planner, '_classify_metric_type_ai'):
            result = await planner._classify_metric_type_ai("test_metric")
            universal_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                                  "engagement_metrics", "completion_metrics"]
            
            if result in universal_categories:
                logger.info(f"  ✅ PASS: AI classification working, result: {result}")
                return True
            else:
                logger.error(f"  ❌ FAIL: AI classification returns invalid category: {result}")
                return False
        else:
            logger.error("  ❌ FAIL: AI classification method not found")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ ERROR: Cannot verify AI classification - {e}")
        return False

def check_sql_database_constraints():
    """⚠️ SQL Fix: Database constraints (needs manual verification)"""
    logger.info("🔍 Check 7: Database metric_type constraints")
    logger.warning("  ⚠️ MANUAL: SQL fix needs to be executed in Supabase:")
    logger.warning("     - Remove hardcoded metric_type enum constraints")
    logger.warning("     - Add universal length-only constraints")
    logger.warning("     - Execute fix_metric_type_universality.sql")
    return "manual"

async def main():
    """Run all fix verification checks"""
    logger.info("🚀 VERIFYING ALL IMPLEMENTED FIXES\n")
    
    checks = [
        ("GoalMetricType Enum Removal", check_fix_1_goal_metric_type_removal),
        ("Hard-coded Mappings Removal", check_fix_2_hardcoded_mappings_removal),
        ("OpenAI Agent Model Fix", check_fix_3_openai_agent_model_attribute),
        ("DynamicPromptEnhancer Fix", check_fix_4_dynamic_prompt_enhancer),
        ("Database Universal Mapping", check_fix_5_database_universal_mapping),
        ("AI-driven Classification", check_fix_6_ai_driven_classification),
        ("SQL Database Constraints", check_sql_database_constraints)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        logger.info(f"\n📋 Running: {check_name}")
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ {check_name} crashed: {e}")
            results.append((check_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("🏁 ALL FIXES VERIFICATION SUMMARY")
    logger.info("="*60)
    
    passed = 0
    manual = 0
    failed = 0
    
    for check_name, result in results:
        if result is True:
            logger.info(f"✅ IMPLEMENTED: {check_name}")
            passed += 1
        elif result == "manual":
            logger.warning(f"⚠️ MANUAL REQUIRED: {check_name}")
            manual += 1
        else:
            logger.error(f"❌ FAILED: {check_name}")
            failed += 1
    
    total = len(results)
    logger.info(f"\nResults: {passed} implemented, {manual} manual, {failed} failed (of {total} total)")
    
    if failed == 0:
        logger.info("🎉 ALL IMPLEMENTED FIXES ARE WORKING CORRECTLY!")
        if manual > 0:
            logger.warning(f"⚠️ {manual} manual step(s) still needed (SQL execution)")
        return True
    else:
        logger.error(f"💥 {failed} fixes have issues and need attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)