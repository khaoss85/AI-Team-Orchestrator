#!/usr/bin/env python3
"""
Pure AI Domain Director Test
Tests the director using 100% AI-driven semantic domain classification
without any hard-coded keywords or patterns.
"""

import asyncio
import os
import sys
import json
from uuid import uuid4

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal
from services.pure_ai_domain_classifier import classify_project_domain_pure_ai

async def test_pure_ai_director():
    """Test Director with Pure AI Domain Classification enabled"""
    
    # Enable Pure AI Domain Classification
    os.environ["ENABLE_PURE_AI_DOMAIN_CLASSIFICATION"] = "true"
    os.environ["DOMAIN_CLASSIFICATION_MODEL"] = "gpt-4o"
    os.environ["AI_DOMAIN_CONFIDENCE_THRESHOLD"] = "0.7"
    
    test_cases = [
        {
            "domain": "🧬 BIOTECH RESEARCH",
            "budget": 15000,
            "goal": "Develop computational pipeline for CRISPR gene editing optimization in cancer immunotherapy applications",
            "expected_ai_domain": "biotechnology",
            "should_work": True
        },
        {
            "domain": "🛸 AEROSPACE ENGINEERING", 
            "budget": 20000,
            "goal": "Design autonomous navigation system for small satellite constellation with collision avoidance algorithms",
            "expected_ai_domain": "aerospace",
            "should_work": True
        },
        {
            "domain": "🌾 AGTECH PRECISION FARMING",
            "budget": 12000, 
            "goal": "Create AI-driven precision agriculture platform using drone imagery and soil sensors for yield optimization",
            "expected_ai_domain": "agricultural_technology",
            "should_work": True
        },
        {
            "domain": "🎮 GAMING & ENTERTAINMENT",
            "budget": 8000,
            "goal": "Build multiplayer VR game with haptic feedback and procedural world generation for immersive storytelling",
            "expected_ai_domain": "entertainment_technology",
            "should_work": True
        },
        {
            "domain": "⚡ RENEWABLE ENERGY",
            "budget": 18000,
            "goal": "Optimize wind farm energy storage system with predictive maintenance and grid integration algorithms",
            "expected_ai_domain": "energy_technology",
            "should_work": True
        }
    ]
    
    print("=" * 100)
    print("🤖 PURE AI-DRIVEN DOMAIN DIRECTOR TEST")
    print("=" * 100)
    print("🎯 Testing 100% AI semantic understanding (NO keyword lists)")
    print("🌍 Supporting unlimited business domains through pure AI analysis")
    print("=" * 100)
    
    director = DirectorAgent()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 TEST {i}/5: {test_case['domain']}")
        print(f"💰 Budget: €{test_case['budget']:,}")
        print(f"🎯 Goal: {test_case['goal'][:80]}...")
        print(f"🤖 Expected AI Domain: {test_case['expected_ai_domain']}")
        print("-" * 80)
        
        # First, test pure AI classification directly
        print("🧠 Step 1: Pure AI Classification Test")
        try:
            ai_result = await classify_project_domain_pure_ai(
                project_goal=test_case['goal'],
                budget=test_case['budget']
            )
            
            if ai_result:
                print(f"   ✅ AI Classification: {ai_result.primary_domain}")
                print(f"   📊 Confidence: {ai_result.confidence_score:.3f} ({ai_result.confidence_level.value})")
                print(f"   🎯 Specialists: {ai_result.specialist_roles}")
                print(f"   💭 Reasoning: {ai_result.reasoning[:150]}...")
            else:
                print("   ❌ AI Classification failed")
                
        except Exception as e:
            print(f"   ❌ AI Classification error: {e}")
        
        # Second, test director team generation
        print("\n🎪 Step 2: Director Team Generation Test")
        
        proposal_request = DirectorTeamProposal(
            workspace_id=uuid4(),
            requirements=test_case['goal'],
            budget_limit=test_case['budget'],
            agents=[], handoffs=[], estimated_cost={}
        )
        
        try:
            # Test director with AI classification
            proposal = await director.create_team_proposal(proposal_request)
            
            print(f"   ✅ Team Generated: {len(proposal.agents)} agents")
            print(f"   💵 Total Cost: €{proposal.estimated_cost.get('total_estimated_cost', 0):,}")
            
            # Analyze team composition
            agent_roles = [agent.role for agent in proposal.agents]
            print(f"   👥 Team Roles:")
            for j, agent in enumerate(proposal.agents, 1):
                seniority_emoji = {"junior": "🔰", "senior": "⭐", "expert": "👑"}.get(agent.seniority, "❓")
                print(f"      {j}. {seniority_emoji} {agent.role} ({agent.seniority}) - {agent.name}")
            
            # Check for domain-specific roles
            generic_roles = ["Task Execution Specialist", "Task Executor", "General Specialist"]
            specific_roles = [role for role in agent_roles if role not in generic_roles and "Project Manager" not in role]
            
            specificity_score = len(specific_roles) / len(agent_roles) if agent_roles else 0
            
            print(f"\n   📊 Team Analysis:")
            print(f"      Domain-specific roles: {len(specific_roles)}/{len(agent_roles)} ({specificity_score:.1%})")
            print(f"      Generic roles: {len(agent_roles) - len(specific_roles)}")
            
            # Determine success
            if specificity_score >= 0.6:  # 60%+ domain-specific roles
                result = "✅ SUCCESS"
                print(f"   🎯 Result: {result} - High domain specificity")
            elif specificity_score >= 0.4:
                result = "⚠️ PARTIAL"
                print(f"   🎯 Result: {result} - Moderate domain specificity")  
            else:
                result = "❌ POOR"
                print(f"   🎯 Result: {result} - Low domain specificity (too generic)")
            
            results.append({
                "domain": test_case['domain'],
                "budget": test_case['budget'],
                "team_size": len(agent_roles),
                "specificity_score": specificity_score,
                "result": result,
                "roles": agent_roles,
                "ai_domain": ai_result.primary_domain if ai_result else "N/A",
                "ai_confidence": ai_result.confidence_score if ai_result else 0.0
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "domain": test_case['domain'],
                "budget": test_case['budget'],
                "result": "❌ ERROR",
                "error": str(e)
            })
    
    # Generate comprehensive summary
    print("\n" + "=" * 100)
    print("📋 PURE AI DOMAIN DIRECTOR TEST SUMMARY")
    print("=" * 100)
    
    if results and all('specificity_score' in r for r in results):
        successes = sum(1 for r in results if r.get('result') == '✅ SUCCESS')
        partials = sum(1 for r in results if r.get('result') == '⚠️ PARTIAL')
        failures = sum(1 for r in results if r.get('result') in ['❌ POOR', '❌ ERROR'])
        
        print(f"🎯 Overall Results: {successes} SUCCESS | {partials} PARTIAL | {failures} FAILURES")
        
        # Detailed analysis
        print(f"\n📊 Detailed Analysis:")
        for result in results:
            if 'specificity_score' in result:
                print(f"   {result['domain']:<30} | {result['result']:<12} | "
                      f"Specificity: {result['specificity_score']:.1%} | "
                      f"AI: {result['ai_domain']:<20} ({result['ai_confidence']:.2f})")
        
        # Overall assessment
        success_rate = (successes / len(results) * 100) if results else 0
        avg_specificity = sum(r.get('specificity_score', 0) for r in results if 'specificity_score' in r) / len([r for r in results if 'specificity_score' in r])
        avg_ai_confidence = sum(r.get('ai_confidence', 0) for r in results if 'ai_confidence' in r) / len([r for r in results if 'ai_confidence' in r])
        
        print(f"\n🏆 Performance Metrics:")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Domain Specificity: {avg_specificity:.1%}")
        print(f"   Average AI Confidence: {avg_ai_confidence:.3f}")
        
        if success_rate >= 80 and avg_specificity >= 0.6:
            print("\n✅ EXCELLENT: Pure AI Domain Classification working exceptionally well!")
            print("   🌟 System successfully supports unlimited business domains")
            print("   🤖 AI semantic understanding is highly effective")
        elif success_rate >= 60 and avg_specificity >= 0.4:
            print("\n⚠️ GOOD: Pure AI Classification functional but needs optimization")
            print("   💡 Consider tuning confidence thresholds or adding more context")
        else:
            print("\n❌ NEEDS IMPROVEMENT: AI Classification requires enhancement")
            print("   🔧 Review model settings, prompts, or context enrichment")
        
        print(f"\n🔍 Key Insights:")
        unique_domains = set(r.get('ai_domain', '') for r in results if r.get('ai_domain', '') != 'N/A')
        print(f"   📈 Unique domains identified: {len(unique_domains)}")
        print(f"   🌍 Domains: {', '.join(sorted(unique_domains))}")
        print(f"   🎯 Domain coverage: UNLIMITED (no keyword constraints)")
        
    print("\n" + "=" * 100)
    print("🏁 PURE AI DOMAIN TEST COMPLETE")
    print("=" * 100)
    
    return results

if __name__ == "__main__":
    # Ensure we have OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Error: OPENAI_API_KEY not set. Test cannot run.")
        sys.exit(1)
    
    asyncio.run(test_pure_ai_director())