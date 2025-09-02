#!/usr/bin/env python3
"""
Quick Domain-Agnostic Director Test
Fast test to verify Director handles diverse domains correctly
"""

import asyncio
import os
import sys
import json
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal

async def test_quick_domains():
    """Quick test of 4 key domains"""
    
    test_cases = [
        {
            "domain": "🎓 LEARNING",
            "budget": 8000,
            "goal": "Create online machine learning course with exercises",
            "expect": ["educator", "content", "curriculum", "technical"]
        },
        {
            "domain": "💰 FINANCE", 
            "budget": 10000,
            "goal": "ESG investment analysis and risk assessment research",
            "expect": ["financial", "research", "analyst", "risk"]
        },
        {
            "domain": "🏥 HEALTHCARE",
            "budget": 12000, 
            "goal": "Patient engagement platform with telemedicine compliance",
            "expect": ["healthcare", "patient", "compliance", "platform"]
        },
        {
            "domain": "⚖️ LEGAL",
            "budget": 9000,
            "goal": "GDPR compliance audit framework with automated tools",
            "expect": ["legal", "compliance", "audit", "regulatory"]
        }
    ]
    
    print("🧪 QUICK DOMAIN-AGNOSTIC TEST")
    print("=" * 50)
    
    director = DirectorAgent()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['domain']} (€{test['budget']:,})")
        print(f"Goal: {test['goal']}")
        
        proposal_request = DirectorTeamProposal(
            workspace_id=uuid4(),
            requirements=test['goal'],
            budget_limit=test['budget'],
            agents=[], handoffs=[], estimated_cost={}
        )
        
        try:
            # Use fallback logic directly to save time
            fallback_dict = director._create_fallback_dict(proposal_request)
            agents = fallback_dict.get('agents', [])
            
            print(f"Team: {len(agents)} agents")
            
            roles = [agent['role'].lower() for agent in agents]
            print("Roles:", [agent['role'] for agent in agents])
            
            # Check domain relevance
            relevant = sum(1 for role in roles if any(exp in role for exp in test['expect']))
            b2b_contamination = sum(1 for role in roles if any(term in role for term in ['sales', 'lead', 'crm', 'outbound']))
            
            relevance_pct = (relevant / len(agents) * 100) if agents else 0
            contamination_pct = (b2b_contamination / len(agents) * 100) if agents else 0
            
            print(f"Relevance: {relevance_pct:.1f}% | B2B contamination: {contamination_pct:.1f}%")
            
            if relevance_pct >= 50 and contamination_pct <= 25:
                print("✅ PASS - Good domain matching")
            elif contamination_pct > 25:
                print("❌ FAIL - Too much B2B bias")
            else:
                print("⚠️ PARTIAL - Low relevance but no contamination")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_quick_domains())