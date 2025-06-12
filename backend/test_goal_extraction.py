#!/usr/bin/env python3

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_goal_extraction():
    """Test goal extraction directly"""
    try:
        from ai_quality_assurance.goal_validator import goal_validator
        
        goal_text = "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot con target open-rate ≥ 30 % e Click-to-rate almeno del 10% in 6 settimane"
        
        print(f"🎯 Testing goal extraction...")
        print(f"Goal text: {goal_text}")
        
        requirements = await goal_validator._extract_goal_requirements(goal_text)
        
        print(f"📊 Found {len(requirements)} requirements:")
        for i, req in enumerate(requirements, 1):
            print(f"  {i}. Type: {req.get('type')}, Value: {req.get('target_value')}, Unit: '{req.get('unit')}', Context: '{req.get('context')}'")
        
        return requirements
        
    except Exception as e:
        print(f"❌ Error in goal extraction test: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(test_goal_extraction())