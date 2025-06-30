#!/usr/bin/env python3
"""
Test script for AI-driven deliverable generation
Tests the new system with the problematic workspace to verify it generates real content instead of templates
"""

import asyncio
import json
import logging
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_driven_deliverable_creation():
    """Test AI-driven deliverable creation with real workspace"""
    try:
        # Import the new AI-driven system
        from services.ai_driven_deliverable_system import ai_driven_deliverable_system
        from database import list_tasks, get_workspace_goals, get_workspace
        
        # Test with the problematic workspace
        workspace_id = 'ad8424d8-f95a-4a41-8e8e-bc131a9c54f6'
        
        print(f"\n🤖 Testing AI-Driven Deliverable Creation")
        print(f"Workspace ID: {workspace_id}")
        print("=" * 60)
        
        # Step 1: Get completed tasks
        print("\n1️⃣ Getting completed tasks...")
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=50)
        print(f"Found {len(completed_tasks)} completed tasks")
        
        if completed_tasks:
            for task in completed_tasks[:3]:  # Show first 3
                print(f"  - {task.get('name', 'No name')}")
        
        # Step 2: Get workspace goals
        print("\n2️⃣ Getting workspace goals...")
        workspace_goals = await get_workspace_goals(workspace_id)
        print(f"Found {len(workspace_goals)} goals")
        
        for goal in workspace_goals:
            print(f"  - {goal.get('title', 'No title')} (Status: {goal.get('status')})")
        
        # Step 3: Get workspace context
        print("\n3️⃣ Getting workspace context...")
        workspace_context = await get_workspace(workspace_id)
        if workspace_context:
            print(f"  - Name: {workspace_context.get('name', 'No name')}")
            print(f"  - Description: {workspace_context.get('description', 'No description')[:100]}...")
        
        # Step 4: Run AI-driven deliverable creation
        print("\n4️⃣ Running AI-driven deliverable creation...")
        print("This will test the complete pipeline:")
        print("  - AI Content Discovery (no hardcoded patterns)")
        print("  - AI Semantic Goal Mapping (no keyword matching)")
        print("  - AI Content Reality Validation (no template patterns)")
        print("  - AI Asset Generation (if needed)")
        print("  - AI Deliverable Structure Creation")
        
        result = await ai_driven_deliverable_system.create_deliverable_from_tasks(
            workspace_id,
            completed_tasks,
            workspace_goals,
            workspace_context
        )
        
        # Step 5: Analyze results
        print("\n5️⃣ AI-Driven Results Analysis")
        print("=" * 40)
        print(f"✅ Content Quality Level: {result.content_quality_level.value}")
        print(f"✅ Business Specificity: {result.business_specificity_score:.1f}/100")
        print(f"✅ Usability Score: {result.usability_score:.1f}/100")
        print(f"✅ Creation Confidence: {result.creation_confidence:.1f}/100")
        print(f"✅ Mapped Goal ID: {result.mapped_goal_id}")
        
        print(f"\n📝 Creation Reasoning:")
        print(result.creation_reasoning)
        
        # Step 6: Content Analysis
        print(f"\n📦 Generated Content Structure:")
        deliverable_content = result.deliverable_content
        if isinstance(deliverable_content, dict):
            for key, value in deliverable_content.items():
                if isinstance(value, (str, int, float)):
                    print(f"  - {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                elif isinstance(value, list):
                    print(f"  - {key}: List with {len(value)} items")
                elif isinstance(value, dict):
                    print(f"  - {key}: Dict with {len(value)} keys")
        
        # Step 7: Quality Validation
        print(f"\n🔍 Quality Validation:")
        validations = result.quality_validations
        
        if 'validation_result' in validations:
            validation = validations['validation_result']
            print(f"  - Reality Level: {validation.reality_level.value}")
            print(f"  - Business Specificity: {validation.business_specificity_score:.1f}")
            print(f"  - Usability: {validation.usability_score:.1f}")
            print(f"  - Quality Gates Passed: {sum(validation.quality_gates_passed.values())}/{len(validation.quality_gates_passed)}")
        
        # Step 8: Improvement Suggestions
        if result.improvement_suggestions:
            print(f"\n💡 Improvement Suggestions:")
            for i, suggestion in enumerate(result.improvement_suggestions[:5], 1):
                print(f"  {i}. {suggestion}")
        
        # Step 9: Template Detection Test
        print(f"\n🕵️ Template Detection Test:")
        content_str = json.dumps(result.deliverable_content, default=str).lower()
        
        template_indicators = [
            "aimed at", "designed to", "focused on", "lorem ipsum", 
            "placeholder", "example", "template", "sample"
        ]
        
        found_templates = [indicator for indicator in template_indicators if indicator in content_str]
        
        if found_templates:
            print(f"  ⚠️ TEMPLATE INDICATORS FOUND: {found_templates}")
            print("  ❌ System still generating template content!")
        else:
            print(f"  ✅ NO TEMPLATE INDICATORS FOUND")
            print("  🎉 System successfully generating real content!")
        
        # Step 10: Comparison with previous system
        print(f"\n📊 Comparison with Previous System:")
        print("Previous deliverable content contained:")
        print("  - 'Aimed at introducing the SaaS product...' (TEMPLATE)")
        print("  - 'Designed to build credibility...' (TEMPLATE)")
        print("  - Generic implementation guidance (TEMPLATE)")
        print()
        print("New AI-driven system should contain:")
        print("  - Business-specific content")
        print("  - Real implementation details")
        print("  - Actionable assets")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in AI-driven deliverable test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_ai_content_extractor_only():
    """Test just the AI content extractor component"""
    try:
        from services.universal_ai_content_extractor import universal_ai_content_extractor
        from database import list_tasks
        
        workspace_id = 'ad8424d8-f95a-4a41-8e8e-bc131a9c54f6'
        
        print(f"\n🔍 Testing AI Content Extractor Only")
        print("=" * 40)
        
        # Get completed tasks
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
        print(f"Analyzing {len(completed_tasks)} completed tasks...")
        
        # Test AI content extraction
        content_analysis = await universal_ai_content_extractor.extract_real_content(
            completed_tasks,
            "Email sequence creation for SaaS outbound sales",
            {"name": "B2B Outbound Sales Lists", "industry": "SaaS"}
        )
        
        print(f"\n📊 AI Content Analysis Results:")
        print(f"  - Reality Score: {content_analysis.reality_score:.1f}/100")
        print(f"  - Usability Score: {content_analysis.usability_score:.1f}/100")
        print(f"  - Business Specificity: {content_analysis.business_specificity:.1f}/100")
        print(f"  - Confidence: {content_analysis.confidence:.1f}/100")
        
        print(f"\n🤖 AI Reasoning:")
        print(content_analysis.reasoning)
        
        print(f"\n📦 Discovered Content:")
        for key, value in content_analysis.discovered_content.items():
            print(f"  - {key}: {str(value)[:150]}{'...' if len(str(value)) > 150 else ''}")
        
        print(f"\n❌ Missing Elements:")
        for element in content_analysis.missing_elements:
            print(f"  - {element}")
        
        return content_analysis
        
    except Exception as e:
        print(f"❌ Error in AI content extractor test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function"""
    print("🚀 Starting AI-Driven Deliverable System Tests")
    print("=" * 60)
    
    # Test 1: AI Content Extractor only
    print("\n📋 TEST 1: AI Content Extractor Component")
    content_result = await test_ai_content_extractor_only()
    
    # Test 2: Full AI-driven deliverable creation
    print("\n📋 TEST 2: Complete AI-Driven Deliverable Creation")
    deliverable_result = await test_ai_driven_deliverable_creation()
    
    # Summary
    print(f"\n🎯 FINAL SUMMARY")
    print("=" * 30)
    
    if content_result:
        print(f"✅ AI Content Extractor: Working")
        print(f"   Reality Score: {content_result.reality_score:.1f}")
    else:
        print(f"❌ AI Content Extractor: Failed")
    
    if deliverable_result:
        print(f"✅ AI Deliverable Creation: Working")
        print(f"   Quality Level: {deliverable_result.content_quality_level.value}")
        print(f"   Business Specificity: {deliverable_result.business_specificity_score:.1f}")
    else:
        print(f"❌ AI Deliverable Creation: Failed")

if __name__ == "__main__":
    asyncio.run(main())