#!/usr/bin/env python3
"""
🚀 Complete AI-Driven Pipeline Test
Tests the entire pipeline from task validation to real content generation

This test demonstrates the complete AI-driven solution:
1. Task validation with tool requirement analysis
2. Tool orchestration for real data collection (WebSearch)
3. Memory-enhanced content generation
4. Quality assessment and auto-improvement
5. Autonomous learning for future improvement
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_pipeline():
    """Test the complete AI-driven pipeline"""
    try:
        print("🚀 TESTING COMPLETE AI-DRIVEN PIPELINE")
        print("=" * 60)
        
        # Import the complete pipeline
        from services.real_tool_integration_pipeline import real_tool_integration_pipeline
        
        # Test scenario: Email sequences for SaaS company
        test_task = {
            "task_id": "test-email-sequences-001",
            "task_name": "Create 3 Email Sequences for SaaS Outreach",
            "task_objective": "Create comprehensive email sequences for B2B SaaS outreach targeting CMOs, including personalized subject lines, body content, and clear CTAs",
            "business_context": {
                "company_name": "TechFlow Analytics",
                "industry": "SaaS",
                "target_audience": "CMOs and Marketing Directors",
                "product_value_prop": "AI-powered marketing analytics platform",
                "company_size": "Series B startup",
                "geographic_focus": "North America"
            }
        }
        
        print(f"📋 Test Scenario:")
        print(f"   Task: {test_task['task_name']}")
        print(f"   Company: {test_task['business_context']['company_name']}")
        print(f"   Industry: {test_task['business_context']['industry']}")
        print(f"   Target: {test_task['business_context']['target_audience']}")
        print()
        
        # Execute complete pipeline
        print("🔄 Executing Complete AI-Driven Pipeline...")
        print("-" * 40)
        
        start_time = datetime.now()
        
        result = await real_tool_integration_pipeline.execute_complete_pipeline(
            task_id=test_task["task_id"],
            task_name=test_task["task_name"],
            task_objective=test_task["task_objective"],
            business_context=test_task["business_context"]
        )
        
        end_time = datetime.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Pipeline execution completed in {execution_duration:.1f} seconds")
        print()
        
        # Display results
        print("📊 PIPELINE EXECUTION RESULTS")
        print("=" * 40)
        print(f"Execution Successful: {'✅' if result.execution_successful else '❌'} {result.execution_successful}")
        print(f"Stages Completed: {len(result.stages_completed)}/6 - {', '.join(result.stages_completed)}")
        print(f"Content Quality Score: {result.content_quality_score:.1f}/100")
        print(f"Tool Usage Score: {result.tool_usage_score:.1f}/100")
        print(f"Business Readiness Score: {result.business_readiness_score:.1f}/100")
        print(f"Learning Patterns Created: {result.learning_patterns_created}")
        print(f"Execution Time: {result.execution_time:.1f} seconds")
        print(f"Confidence: {result.confidence:.1f}/100")
        print()
        
        if result.auto_improvements:
            print(f"🔧 Auto-Improvements Applied:")
            for improvement in result.auto_improvements:
                print(f"   • {improvement}")
            print()
        
        print(f"💭 Pipeline Reasoning:")
        print(f"   {result.pipeline_reasoning}")
        print()
        
        # Display generated content
        print("📄 GENERATED CONTENT")
        print("=" * 40)
        
        if result.final_content and result.final_content != {"error": "Content generation failed"}:
            # Pretty print the generated content
            content_str = json.dumps(result.final_content, indent=2, default=str)
            
            # Truncate if too long for readability
            if len(content_str) > 2000:
                content_preview = content_str[:2000] + "...\n[Content truncated for readability]"
                print(content_preview)
            else:
                print(content_str)
            
            print()
            
            # Content analysis
            print("🔍 CONTENT ANALYSIS")
            print("-" * 30)
            
            # Check for real email content indicators
            content_lower = content_str.lower()
            
            email_indicators = [
                ("subject lines", any(word in content_lower for word in ["subject:", "subject line", "re:", "fw:"])),
                ("email body content", any(word in content_lower for word in ["dear", "hi", "hello", "body:", "email body"])),
                ("call-to-action", any(word in content_lower for word in ["cta", "call to action", "book a demo", "schedule", "learn more"])),
                ("personalization", any(word in content_lower for word in ["[name]", "[company]", "personalized", "tailored"])),
                ("business specifics", test_task['business_context']['company_name'].lower() in content_lower),
                ("industry relevance", test_task['business_context']['industry'].lower() in content_lower)
            ]
            
            for indicator, found in email_indicators:
                status = "✅ Found" if found else "❌ Missing"
                print(f"   {indicator}: {status}")
            
            # Calculate content authenticity score
            authenticity_score = sum(1 for _, found in email_indicators if found) / len(email_indicators) * 100
            print(f"\n📈 Content Authenticity Score: {authenticity_score:.1f}/100")
            
        else:
            print("❌ No content generated or content generation failed")
            if "error" in result.final_content:
                print(f"   Error: {result.final_content['error']}")
        
        print()
        
        # Pipeline component analysis
        print("🔧 PIPELINE COMPONENT ANALYSIS")
        print("=" * 40)
        
        print("Stage Analysis:")
        expected_stages = ["validation", "tool_orchestration", "content_generation", "quality_assessment", "learning"]
        
        for stage in expected_stages:
            completed = stage in result.stages_completed
            status = "✅ Completed" if completed else "❌ Failed"
            print(f"   {stage.replace('_', ' ').title()}: {status}")
        
        print()
        
        # Success criteria evaluation
        print("🎯 SUCCESS CRITERIA EVALUATION")
        print("=" * 40)
        
        success_criteria = [
            ("Pipeline completes all stages", len(result.stages_completed) >= 5),
            ("Content quality meets threshold", result.content_quality_score >= 70),
            ("Tool usage is effective", result.tool_usage_score >= 60),
            ("Business readiness is high", result.business_readiness_score >= 70),
            ("Execution is confident", result.confidence >= 60),
            ("Real content is generated", authenticity_score >= 60 if 'authenticity_score' in locals() else False),
            ("Learning patterns created", result.learning_patterns_created > 0)
        ]
        
        passed_criteria = 0
        for criterion, passed in success_criteria:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {criterion}: {status}")
            if passed:
                passed_criteria += 1
        
        overall_success_rate = passed_criteria / len(success_criteria) * 100
        print(f"\n🏆 OVERALL SUCCESS RATE: {overall_success_rate:.1f}% ({passed_criteria}/{len(success_criteria)} criteria passed)")
        
        # Recommendations
        print()
        print("💡 RECOMMENDATIONS")
        print("=" * 40)
        
        if overall_success_rate >= 80:
            print("🌟 EXCELLENT: Pipeline is working very well!")
            print("   • The AI-driven approach is successfully generating real business content")
            print("   • Tool integration is effective and learning is taking place")
            print("   • System is ready for production use")
        elif overall_success_rate >= 60:
            print("⚡ GOOD: Pipeline is working with room for improvement")
            print("   • Core functionality is operational")
            print("   • Some optimizations needed for better quality")
            print("   • Continue monitoring and learning")
        else:
            print("🔧 NEEDS IMPROVEMENT: Pipeline requires optimization")
            print("   • Review failed stages and components")
            print("   • Check API keys and tool availability")
            print("   • Verify AI model access and prompts")
        
        # Next steps
        print()
        print("🚀 NEXT STEPS")
        print("=" * 20)
        print("1. Monitor pipeline performance in production")
        print("2. Review learning patterns for optimization opportunities")
        print("3. Test with different business contexts and asset types")
        print("4. Implement additional tools as needed")
        print("5. Monitor quality scores and adjust thresholds")
        
        return result
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_individual_components():
    """Test individual components separately"""
    try:
        print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
        print("=" * 40)
        
        # Test 1: AI Tool-Aware Validator
        print("🔍 Testing AI Tool-Aware Validator...")
        try:
            from services.ai_tool_aware_validator import ai_tool_aware_validator
            
            test_task_result = {
                "name": "Create email sequences",
                "status": "completed",
                "result": {
                    "summary": "Created planning document for email sequences",
                    "detailed_results_json": '{"planning_phase": "completed", "next_steps": "implementation"}'
                }
            }
            
            validation = await ai_tool_aware_validator.validate_task_completion_with_tools(
                task_result=test_task_result,
                task_name="Create email sequences",
                task_objective="Generate real email sequences for outreach",
                business_context={"industry": "SaaS"}
            )
            
            print(f"   ✅ Validator working: Completion level = {validation.completion_level.value}")
            print(f"   📊 Completion score: {validation.completion_score:.1f}/100")
            
        except Exception as e:
            print(f"   ❌ Validator test failed: {e}")
        
        # Test 2: AI Tool Orchestrator
        print("\n🔧 Testing AI Tool Orchestrator...")
        try:
            from services.ai_tool_orchestrator import ai_tool_orchestrator
            
            orchestration_result = await ai_tool_orchestrator.orchestrate_tools_for_task(
                task_objective="Research email sequence best practices",
                required_tools=["websearch"],
                business_context={"industry": "SaaS", "target": "CMOs"}
            )
            
            print(f"   ✅ Orchestrator working: Success = {orchestration_result.overall_success}")
            print(f"   📊 Data quality: {orchestration_result.data_quality_score:.1f}/100")
            print(f"   🔧 Tools executed: {len(orchestration_result.tool_results)}")
            
        except Exception as e:
            print(f"   ❌ Orchestrator test failed: {e}")
        
        # Test 3: Memory-Enhanced Asset Generator
        print("\n🎨 Testing Memory-Enhanced Asset Generator...")
        try:
            from services.memory_enhanced_ai_asset_generator import memory_enhanced_ai_asset_generator
            
            generation_result = await memory_enhanced_ai_asset_generator.generate_real_business_asset(
                asset_type="email_sequences",
                business_context={"company_name": "TestCorp", "industry": "SaaS"},
                goal_context="Generate B2B outreach sequences"
            )
            
            print(f"   ✅ Generator working: Quality = {generation_result.content_quality.value}")
            print(f"   📊 Business specificity: {generation_result.business_specificity_score:.1f}/100")
            print(f"   🔧 Tool integration: {generation_result.tool_integration_score:.1f}/100")
            
        except Exception as e:
            print(f"   ❌ Generator test failed: {e}")
        
        # Test 4: Autonomous Learning System
        print("\n📚 Testing Autonomous Learning System...")
        try:
            from services.autonomous_learning_memory_system import autonomous_learning_memory_system
            
            await autonomous_learning_memory_system.learn_from_successful_execution(
                execution_type="test_execution",
                context={"type": "email_generation"},
                approach_used={"tools": ["websearch"], "method": "ai_driven"},
                performance_metrics={"quality": 85, "speed": 90},
                outcome_quality=85
            )
            
            print(f"   ✅ Learning system working: Pattern stored successfully")
            print(f"   📊 Patterns in memory: {len(autonomous_learning_memory_system.learning_patterns)}")
            
        except Exception as e:
            print(f"   ❌ Learning system test failed: {e}")
        
        print("\n🎯 Individual component testing completed")
        
    except Exception as e:
        print(f"❌ Component testing failed: {e}")

async def main():
    """Main test function"""
    print("🤖 AI TEAM ORCHESTRATOR - COMPLETE PIPELINE TEST")
    print("🎯 Testing 100% AI-driven content generation pipeline")
    print("⚡ Root cause fix: Tasks will generate real content, not just planning")
    print("=" * 80)
    
    # Test individual components first
    await test_individual_components()
    
    # Test complete pipeline
    result = await test_complete_pipeline()
    
    print("\n" + "=" * 80)
    print("🏁 PIPELINE TEST COMPLETED")
    
    if result and result.execution_successful:
        print("✅ SUCCESS: AI-driven pipeline is operational and generating real content!")
        print("🎯 Root cause addressed: Real tools + AI generation = authentic business assets")
    else:
        print("❌ ISSUES DETECTED: Pipeline needs optimization")
        print("🔧 Review component logs and fix any configuration issues")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())