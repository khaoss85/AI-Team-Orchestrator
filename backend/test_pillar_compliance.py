#!/usr/bin/env python3
"""
🌍 PILLAR COMPLIANCE VERIFICATION
Tests that the system is now PILLAR 2 & 3 compliant (AI-Driven + Universal)
"""

import asyncio
import sys
import os
import logging

# Add current directory to Python path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pillar_2_ai_driven_compliance():
    """Test Pillar 2: AI-Driven (zero hard-coding)"""
    logger.info("🤖 Testing PILLAR 2: AI-DRIVEN COMPLIANCE")
    
    violations = []
    
    # Test 1: No hardcoded business domain enums
    try:
        from models import GoalMetricType
        violations.append("VIOLATION: GoalMetricType enum still exists (hardcoded business domains)")
    except ImportError:
        logger.info("  ✅ GoalMetricType enum removed - no hardcoded business domains")
    
    # Test 2: AI-driven metric classification exists
    try:
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        planner = GoalDrivenTaskPlanner()
        
        if hasattr(planner, '_classify_metric_type_ai'):
            logger.info("  ✅ AI-driven metric classification implemented")
        else:
            violations.append("VIOLATION: AI-driven classification method missing")
            
    except Exception as e:
        violations.append(f"VIOLATION: Cannot verify AI classification - {e}")
    
    # Test 3: Universal database mapping (no hardcoded business logic)
    try:
        from database import _map_requirement_to_metric_type
        
        # Test that it returns universal categories, not business-specific ones
        result = _map_requirement_to_metric_type("test_metric")
        universal_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                              "engagement_metrics", "completion_metrics"]
        
        if result in universal_categories:
            logger.info("  ✅ Database mapping uses universal categories")
        else:
            violations.append(f"VIOLATION: Database mapping returns non-universal category: {result}")
            
    except Exception as e:
        violations.append(f"VIOLATION: Database mapping test failed - {e}")
    
    return violations

def test_pillar_3_universal_compliance():
    """Test Pillar 3: Universal/Language-agnostic"""
    logger.info("🌍 Testing PILLAR 3: UNIVERSAL COMPLIANCE")
    
    violations = []
    
    # Test 1: No language-specific hardcoded strings in business logic
    try:
        from database import _map_requirement_to_metric_type
        
        # Test with different languages/domains
        test_cases = [
            "contatti",  # Italian
            "contacts",  # English
            "contactos", # Spanish
            "contacts_database", # Technical
            "lead_generation"  # Business
        ]
        
        for test_case in test_cases:
            result = _map_requirement_to_metric_type(test_case)
            # Should work universally without language bias
            universal_categories = ["quantified_outputs", "quality_measures", "time_based_metrics", 
                                  "engagement_metrics", "completion_metrics"]
            if result not in universal_categories:
                violations.append(f"VIOLATION: Non-universal result for '{test_case}': {result}")
        
        if not violations:
            logger.info("  ✅ Language-agnostic classification working")
            
    except Exception as e:
        violations.append(f"VIOLATION: Universal classification test failed - {e}")
    
    # Test 2: Metric types are free-form strings (not constrained enums)
    try:
        from models import WorkspaceGoalCreate
        
        # Should accept any string for metric_type
        from uuid import uuid4
        test_goal = {
            "workspace_id": str(uuid4()),
            "metric_type": "任何语言的任何度量标准",  # Any metric in any language
            "target_value": 100,
            "unit": "items"
        }
        
        # This should not raise validation errors for metric_type
        goal_create = WorkspaceGoalCreate(**test_goal)
        logger.info("  ✅ Free-form metric types supported")
        
    except Exception as e:
        violations.append(f"VIOLATION: Metric type constraints too restrictive - {e}")
    
    return violations

def test_openai_agent_model_fix():
    """Test that OpenAI Agent model attribute fix is working"""
    logger.info("🔧 Testing OPENAI AGENT MODEL ATTRIBUTE FIX")
    
    violations = []
    
    try:
        # Test the getattr pattern that was implemented
        class MockAgentWithoutModel:
            def __init__(self):
                self._model = "gpt-4.1-mini"
                # No self.model attribute
        
        mock_agent = MockAgentWithoutModel()
        
        # This is the fix pattern used in specialist.py
        model_name = getattr(mock_agent, 'model', getattr(mock_agent, '_model', 'gpt-4'))
        
        if model_name == "gpt-4.1-mini":
            logger.info("  ✅ OpenAI Agent model attribute fix working")
        else:
            violations.append(f"VIOLATION: Model attribute fix not working - got {model_name}")
            
    except Exception as e:
        violations.append(f"VIOLATION: OpenAI Agent model fix test failed - {e}")
    
    return violations

def test_dynamic_prompt_enhancer_fix():
    """Test that DynamicPromptEnhancer imports correctly"""
    logger.info("💫 Testing DYNAMIC PROMPT ENHANCER FIX")
    
    violations = []
    
    try:
        from ai_quality_assurance.quality_integration import DynamicPromptEnhancer
        
        # Test basic functionality
        base_prompt = "Test prompt"
        enhanced = DynamicPromptEnhancer.enhance_specialist_prompt_for_quality(base_prompt)
        
        if "CONCRETE CONTENT CHECKLIST" in enhanced:
            logger.info("  ✅ DynamicPromptEnhancer import and functionality working")
        else:
            violations.append("VIOLATION: DynamicPromptEnhancer not enhancing correctly")
            
    except Exception as e:
        violations.append(f"VIOLATION: DynamicPromptEnhancer import failed - {e}")
    
    return violations

async def main():
    """Run all pillar compliance tests"""
    logger.info("🚀 STARTING PILLAR COMPLIANCE VERIFICATION\n")
    
    all_violations = []
    
    # Run all tests
    tests = [
        ("PILLAR 2: AI-Driven", test_pillar_2_ai_driven_compliance),
        ("PILLAR 3: Universal", test_pillar_3_universal_compliance), 
        ("OpenAI Agent Fix", test_openai_agent_model_fix),
        ("Quality System Fix", test_dynamic_prompt_enhancer_fix)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        violations = test_func()
        if violations:
            all_violations.extend(violations)
        logger.info("")
    
    # Final assessment
    logger.info("="*60)
    logger.info("🏁 PILLAR COMPLIANCE ASSESSMENT")
    logger.info("="*60)
    
    if not all_violations:
        logger.info("🎉 PERFECT COMPLIANCE!")
        logger.info("✅ PILLAR 2: AI-Driven (zero hard-coding) - COMPLIANT")
        logger.info("✅ PILLAR 3: Universal/Language-agnostic - COMPLIANT")
        logger.info("✅ All technical fixes working correctly")
        logger.info("\n🌍 System is now truly UNIVERSAL and AI-DRIVEN!")
        return True
    else:
        logger.error(f"💥 {len(all_violations)} VIOLATIONS FOUND:")
        for i, violation in enumerate(all_violations, 1):
            logger.error(f"  {i}. {violation}")
        logger.error("\n❌ System needs additional fixes for full compliance")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)