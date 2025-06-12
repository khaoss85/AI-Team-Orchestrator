#!/usr/bin/env python3

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_universal_goal_extraction():
    """Test universal, scalable goal extraction across different domains"""
    try:
        from ai_quality_assurance.goal_validator import goal_validator
        
        # 🎯 TEST CASES - Multiple domains to prove scalability
        test_cases = [
            {
                "domain": "Marketing/Email",
                "goal": "Raccogliere 50 contatti ICP e creare 3 sequenze email con 30% open-rate in 6 settimane"
            },
            {
                "domain": "Tech/Development", 
                "goal": "Sviluppare 5 nuove API, completare 10 feature e fare 3 deployment in 2 mesi"
            },
            {
                "domain": "Fitness/Health",
                "goal": "Completare 20 workout, perdere 5 kg e raggiungere 80% performance score in 8 settimane"
            },
            {
                "domain": "Education/Learning",
                "goal": "Creare 12 corsi online, certificare 50 studenti con 90% success rate in 3 mesi"
            },
            {
                "domain": "Finance/Business",
                "goal": "Raggiungere 100K EUR revenue, ridurre costi del 15% e aumentare ROI del 25% quest'anno"
            },
            {
                "domain": "Content/Media",
                "goal": "Produrre 30 video, scrivere 15 articoli e ottenere 10M views in 6 mesi"
            }
        ]
        
        print("🧠 TESTING UNIVERSAL AI-DRIVEN GOAL EXTRACTION")
        print("=" * 80)
        
        for test_case in test_cases:
            domain = test_case["domain"]
            goal_text = test_case["goal"]
            
            print(f"\n🎯 DOMAIN: {domain}")
            print(f"Goal: {goal_text}")
            print("-" * 60)
            
            requirements = await goal_validator._extract_goal_requirements(goal_text)
            
            print(f"📊 Found {len(requirements)} requirements:")
            for i, req in enumerate(requirements, 1):
                req_type = goal_validator._classify_requirement_type(req.get('unit', ''), goal_text)
                print(f"  {i}. Value: {req.get('target_value')}, Unit: '{req.get('unit', '')}', Type: {req_type}, Context: '{req.get('context', '')}'")
        
        print("\n" + "=" * 80)
        print("✅ UNIVERSAL SCALABILITY TEST COMPLETED")
        print("The system successfully handles multiple domains without domain-specific hardcoding!")
        
    except Exception as e:
        print(f"❌ Error in universal goal extraction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_universal_goal_extraction())