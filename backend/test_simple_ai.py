#!/usr/bin/env python3
"""
Test simple AI content extractor
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_ai():
    """Test simple AI content extractor"""
    try:
        from services.simple_ai_content_extractor import simple_ai_content_extractor
        from database import list_tasks
        
        workspace_id = 'ad8424d8-f95a-4a41-8e8e-bc131a9c54f6'
        
        print(f"\n🔍 Testing Simple AI Content Extractor")
        print("=" * 40)
        
        # Get completed tasks
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
        print(f"Analyzing {len(completed_tasks)} completed tasks...")
        
        # Test simple AI content extraction
        result = await simple_ai_content_extractor.extract_real_content(
            completed_tasks,
            "Email sequence creation for SaaS outbound sales",
            {"name": "B2B Outbound Sales Lists", "industry": "SaaS"}
        )
        
        print(f"\n📊 Simple AI Analysis Results:")
        print(f"  - Reality Score: {result.reality_score:.1f}/100")
        print(f"  - Usability Score: {result.usability_score:.1f}/100")
        print(f"  - Confidence: {result.confidence:.1f}/100")
        
        print(f"\n🤖 AI Reasoning:")
        print(result.reasoning)
        
        print(f"\n📦 Discovered Content:")
        for key, value in result.discovered_content.items():
            print(f"  - {key}: {str(value)[:150]}{'...' if len(str(value)) > 150 else ''}")
        
        # Check if this is real content vs template
        if result.reality_score > 50:
            print(f"\n✅ REAL CONTENT DETECTED!")
        else:
            print(f"\n❌ Template/Generic content detected")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in simple AI test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function"""
    print("🚀 Testing Simple AI Content Extractor")
    result = await test_simple_ai()
    
    if result:
        print(f"\n🎯 FINAL RESULT: {'SUCCESS' if result.reality_score > 50 else 'NEEDS IMPROVEMENT'}")

if __name__ == "__main__":
    asyncio.run(main())