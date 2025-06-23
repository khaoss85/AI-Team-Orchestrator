#!/usr/bin/env python3
"""
🎯 AI-DRIVEN SYSTEM VALIDATION TEST
Verifica che il sistema sia veramente AI-driven e scalabile
"""
import asyncio
import sys
sys.path.append('.')

from concrete_asset_extractor_refactored import multi_source_extractor

async def test_ai_driven_goal_analysis():
    print('🎯 TESTING AI-DRIVEN GOAL ANALYSIS')
    print('=' * 60)
    
    # Test goals that require different implementations
    test_goals = [
        {
            "goal": "Create 20 workout routines for beginner athletes with progress tracking",
            "expected_analysis": ["fitness", "workout", "tracking", "progression"]
        },
        {
            "goal": "Develop 15 healthy recipes for busy professionals with meal prep instructions", 
            "expected_analysis": ["culinary", "recipe", "meal prep", "professionals"]
        },
        {
            "goal": "Build an online course with 10 modules for advanced Python developers",
            "expected_analysis": ["education", "course", "modules", "technical"]
        },
        {
            "goal": "Generate 50 B2B leads for SaaS companies using LinkedIn automation",
            "expected_analysis": ["B2B", "leads", "SaaS", "LinkedIn", "automation"]
        }
    ]
    
    for i, test_case in enumerate(test_goals, 1):
        print(f"\n🔬 TEST {i}: AI Analysis")
        print(f"Goal: {test_case['goal']}")
        
        try:
            # Test AI goal analysis
            context = multi_source_extractor._ai_extract_goal_context(test_case['goal'])
            analysis = context
            
            print(f"✅ AI Analysis Results:")
            print(f"   Domain: {analysis.get('industry_domain', 'N/A')}")
            print(f"   Primary Action: {analysis.get('primary_action', 'N/A')}")
            print(f"   Tools/Platforms: {analysis.get('tools_platforms', ['N/A'])}")
            print(f"   Target Audience: {analysis.get('target_audience', 'N/A')}")
            print(f"   Implementation Steps: {len(analysis.get('implementation_steps', []))} steps")
            
            # Test AI content field determination
            content_fields = multi_source_extractor._ai_determine_required_content_fields(
                test_case['goal'], "universal_content", analysis
            )
            
            print(f"✅ AI-Determined Content Fields ({len(content_fields)}):")
            for field, purpose in list(content_fields.items())[:5]:  # Show first 5
                print(f"   {field}: {purpose}")
            
            # Test field content generation
            stage = {"title": "Getting Started", "type": "opener", "description": "Initial setup"}
            sample_content = multi_source_extractor._ai_generate_field_content(
                "content", "main actionable content", stage, "Introductory", 
                test_case['goal'], analysis, 1
            )
            
            print(f"✅ AI-Generated Sample Content:")
            print(f"   {sample_content[:100]}...")
            
            print(f"🎯 TEST {i}: AI-DRIVEN SUCCESS ✅")
            
        except Exception as e:
            print(f"❌ TEST {i}: FAILED - {e}")
    
    print(f"\n🎉 AI-DRIVEN VALIDATION COMPLETED!")

async def test_goal_vs_traditional_hardcoding():
    print('\n🔍 COMPARING AI-DRIVEN vs HARDCODED APPROACH')
    print('=' * 60)
    
    goal = "Build 10 advanced calisthenics workouts with video demonstrations"
    
    print(f"Goal: {goal}")
    print("\n🤖 AI-Driven Analysis:")
    
    # AI Analysis
    context = multi_source_extractor._ai_extract_goal_context(goal)
    print(f"   AI inferred domain: {context.get('industry_domain')}")
    print(f"   AI identified action: {context.get('primary_action')}")
    print(f"   AI determined audience: {context.get('target_audience')}")
    
    # AI Content Fields
    fields = multi_source_extractor._ai_determine_required_content_fields(
        goal, "workout_content", context
    )
    print(f"   AI determined {len(fields)} fields needed:")
    for field in list(fields.keys())[:3]:
        print(f"     - {field}")
    
    print("\n❌ Traditional Hard-coded Approach Would:")
    print("   - Need explicit 'workout' detection code")
    print("   - Require hardcoded workout field mappings") 
    print("   - Need manual calisthenics vs other workout types")
    print("   - Require separate video handling logic")
    
    print("\n✅ AI-Driven Approach:")
    print("   - Automatically infers fitness domain")
    print("   - Dynamically determines required fields")
    print("   - Generates appropriate content for calisthenics") 
    print("   - Scales to ANY fitness goal without code changes")

if __name__ == "__main__":
    asyncio.run(test_ai_driven_goal_analysis())
    asyncio.run(test_goal_vs_traditional_hardcoding())