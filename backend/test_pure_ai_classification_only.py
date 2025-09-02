#!/usr/bin/env python3
"""
Pure AI Classification Service Test
Tests just the AI domain classification without full director integration
"""

import asyncio
import os
import sys

# Enable Pure AI Domain Classification BEFORE importing
os.environ["ENABLE_PURE_AI_DOMAIN_CLASSIFICATION"] = "true"
os.environ["DOMAIN_CLASSIFICATION_MODEL"] = "gpt-4o"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pure_ai_domain_classifier import classify_project_domain_pure_ai

async def test_pure_ai_classification():
    """Test Pure AI Domain Classification directly"""
    
    test_cases = [
        {
            "domain": "🧬 BIOTECH",
            "goal": "Develop CRISPR gene editing pipeline for cancer therapy",
        },
        {
            "domain": "🛸 AEROSPACE", 
            "goal": "Design autonomous navigation for satellite constellation",
        },
        {
            "domain": "🌾 AGTECH",
            "goal": "Create AI precision farming with drone sensors",
        }
    ]
    
    print("🤖 PURE AI CLASSIFICATION TEST")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['domain']}")
        print(f"Goal: {test_case['goal']}")
        
        try:
            result = await classify_project_domain_pure_ai(
                project_goal=test_case['goal'],
                budget=10000.0
            )
            
            if result:
                print(f"✅ Domain: {result.primary_domain}")
                print(f"📊 Confidence: {result.confidence_score:.3f}")
                print(f"🎯 Specialists: {result.specialist_roles}")
                print(f"💭 Reasoning: {result.reasoning[:100]}...")
            else:
                print("❌ Classification failed - service returned None")
                print("Debug: Check if ENABLE_PURE_AI_DOMAIN_CLASSIFICATION=true")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n🏁 TEST COMPLETE")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    asyncio.run(test_pure_ai_classification())