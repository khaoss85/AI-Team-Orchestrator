#!/usr/bin/env python3
"""
Domain-Agnostic Director Test
Verifies the Director correctly generates teams for ANY business domain,
not just B2B projects. Tests learning, financial research, healthcare,
e-commerce, legal, creative, and other domains.
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

async def test_domain_agnostic_proposals():
    """Test Director generates appropriate teams across ALL business domains"""
    
    # Comprehensive test cases covering diverse domains
    test_cases = [
        {
            "domain": "🎓 LEARNING & EDUCATION",
            "budget": 8000,
            "goal": "Create comprehensive online course curriculum for machine learning fundamentals with interactive exercises and assessments",
            "expected_roles": ["educator", "content", "curriculum", "technical", "instructional"],
            "avoid_roles": ["sales", "lead", "crm", "instagram"]
        },
        {
            "domain": "💰 FINANCIAL RESEARCH", 
            "budget": 12000,
            "goal": "Conduct comprehensive market analysis of ESG investment opportunities in European renewable energy sector with risk assessment",
            "expected_roles": ["financial", "research", "analyst", "market", "risk"],
            "avoid_roles": ["social media", "content creator", "instagram", "tiktok"]
        },
        {
            "domain": "🏥 HEALTHCARE & MEDICAL",
            "budget": 15000, 
            "goal": "Develop patient engagement platform for chronic disease management with telemedicine integration and compliance framework",
            "expected_roles": ["healthcare", "medical", "compliance", "patient", "platform"],
            "avoid_roles": ["marketing", "social", "lead generation", "sales"]
        },
        {
            "domain": "⚖️ LEGAL & COMPLIANCE",
            "budget": 10000,
            "goal": "Create GDPR compliance audit framework for multinational corporations with automated assessment tools",
            "expected_roles": ["legal", "compliance", "audit", "regulatory", "privacy"],
            "avoid_roles": ["content", "social", "marketing", "instagram"]
        },
        {
            "domain": "🛒 E-COMMERCE & RETAIL",
            "budget": 9000,
            "goal": "Launch sustainable fashion marketplace with supply chain transparency and customer loyalty program",
            "expected_roles": ["ecommerce", "marketplace", "supply", "retail", "customer"],
            "avoid_roles": ["b2b sales", "lead generation", "email sequences"]
        },
        {
            "domain": "🎨 CREATIVE & DESIGN",
            "budget": 7000,
            "goal": "Design comprehensive brand identity system for sustainable architecture firm including visual guidelines and digital assets",
            "expected_roles": ["design", "creative", "brand", "visual", "identity"],
            "avoid_roles": ["sales", "lead", "crm", "financial", "research"]
        },
        {
            "domain": "🏭 MANUFACTURING & SUPPLY CHAIN",
            "budget": 14000,
            "goal": "Optimize manufacturing processes for semiconductor production with predictive maintenance and quality control systems", 
            "expected_roles": ["manufacturing", "process", "quality", "production", "optimization"],
            "avoid_roles": ["social media", "content", "marketing", "instagram"]
        },
        {
            "domain": "🌱 SUSTAINABILITY & ENVIRONMENT",
            "budget": 11000,
            "goal": "Develop carbon footprint tracking system for small businesses with automated reporting and offset recommendations",
            "expected_roles": ["sustainability", "environmental", "carbon", "tracking", "reporting"],
            "avoid_roles": ["sales", "lead generation", "social media", "content"]
        },
        {
            "domain": "🔬 RESEARCH & DEVELOPMENT",
            "budget": 13000,
            "goal": "Research applications of quantum computing in cryptographic security for financial institutions",
            "expected_roles": ["research", "quantum", "cryptographic", "security", "technical"],
            "avoid_roles": ["marketing", "social", "content", "instagram", "sales"]
        },
        {
            "domain": "🚀 STARTUP & INNOVATION",
            "budget": 8500,
            "goal": "Validate product-market fit for AI-powered mental health chatbot through user research and prototype development",
            "expected_roles": ["product", "research", "validation", "prototype", "development"],
            "avoid_roles": ["lead generation", "email sequences", "sales", "crm"]
        }
    ]
    
    print("=" * 100)
    print("🧪 TESTING DOMAIN-AGNOSTIC AI-DRIVEN DIRECTOR")
    print("=" * 100)
    print("🎯 Objective: Verify Director generates appropriate teams for ANY business domain")
    print("🤖 Expected: AI-driven role selection based on project semantics, not hard-coded keywords")
    print("❌ Anti-pattern: B2B roles for non-B2B projects, generic 'Project Manager' fallbacks")
    print("=" * 100)
    
    director = DirectorAgent()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 TEST {i}/10: {test_case['domain']}")
        print(f"💰 Budget: €{test_case['budget']:,}")
        print(f"🎯 Goal: {test_case['goal'][:80]}...")
        print("-" * 60)
        
        # Create proposal request
        proposal_request = DirectorTeamProposal(
            workspace_id=uuid4(),
            requirements=test_case['goal'],
            budget_limit=test_case['budget'],
            agents=[],
            handoffs=[],
            estimated_cost={}
        )
        
        try:
            # Test the director proposal generation
            proposal = await director.create_team_proposal(proposal_request)
            
            print(f"✅ Team Generated: {len(proposal.agents)} agents")
            print(f"💵 Total Cost: €{proposal.estimated_cost.get('total_estimated_cost', 0):,}")
            
            # Analyze team composition
            agent_roles = [agent.role.lower() for agent in proposal.agents]
            print(f"👥 Team Roles:")
            for j, agent in enumerate(proposal.agents, 1):
                seniority_emoji = {"junior": "🔰", "senior": "⭐", "expert": "👑"}.get(agent.seniority, "❓")
                print(f"   {j}. {seniority_emoji} {agent.role} ({agent.seniority}) - {agent.name}")
            
            # Domain relevance analysis
            expected_matches = sum(1 for role in agent_roles 
                                 if any(exp in role for exp in test_case['expected_roles']))
            avoid_matches = sum(1 for role in agent_roles 
                              if any(avoid in role for avoid in test_case['avoid_roles']))
            
            # Calculate domain alignment score
            total_agents = len(proposal.agents)
            relevance_score = (expected_matches / total_agents * 100) if total_agents > 0 else 0
            contamination_score = (avoid_matches / total_agents * 100) if total_agents > 0 else 0
            
            print(f"📊 Domain Analysis:")
            print(f"   ✅ Relevant roles: {expected_matches}/{total_agents} ({relevance_score:.1f}%)")
            print(f"   ❌ Irrelevant roles: {avoid_matches}/{total_agents} ({contamination_score:.1f}%)")
            
            # Determine test result
            if relevance_score >= 60 and contamination_score <= 20:
                result = "✅ PASS"
                print(f"   🎯 Result: {result} - Domain-appropriate team composition")
            elif contamination_score > 20:
                result = "❌ FAIL" 
                print(f"   🎯 Result: {result} - Too many irrelevant roles (B2B contamination?)")
            else:
                result = "⚠️ PARTIAL"
                print(f"   🎯 Result: {result} - Low domain relevance but no contamination")
            
            # Store results for summary
            results.append({
                "domain": test_case['domain'],
                "budget": test_case['budget'],
                "team_size": total_agents,
                "relevance_score": relevance_score,
                "contamination_score": contamination_score,
                "result": result,
                "roles": [f"{agent.role} ({agent.seniority})" for agent in proposal.agents]
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
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
    print("📋 DOMAIN-AGNOSTIC DIRECTOR TEST SUMMARY")
    print("=" * 100)
    
    passed = sum(1 for r in results if r.get('result') == '✅ PASS')
    failed = sum(1 for r in results if r.get('result') == '❌ FAIL') 
    partial = sum(1 for r in results if r.get('result') == '⚠️ PARTIAL')
    errors = sum(1 for r in results if r.get('result') == '❌ ERROR')
    
    print(f"🎯 Overall Results: {passed} PASS | {partial} PARTIAL | {failed} FAIL | {errors} ERROR")
    
    # Detailed analysis per domain
    print(f"\n📊 Detailed Analysis:")
    for result in results:
        if 'relevance_score' in result:
            print(f"   {result['domain']:<25} | {result['result']:<10} | "
                  f"Relevance: {result['relevance_score']:5.1f}% | "
                  f"Contamination: {result['contamination_score']:5.1f}% | "
                  f"Team: {result['team_size']} agents")
    
    # Overall assessment
    success_rate = (passed / len(results) * 100) if results else 0
    print(f"\n🏆 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ EXCELLENT: Director demonstrates strong domain-agnostic capabilities")
    elif success_rate >= 60:
        print("⚠️ GOOD: Director works across domains but needs improvement") 
    elif success_rate >= 40:
        print("❌ POOR: Director shows B2B bias, needs AI-driven domain classification")
    else:
        print("🚨 CRITICAL: Director fails domain-agnostic requirements")
    
    # Identify patterns
    print(f"\n🔍 Pattern Analysis:")
    avg_relevance = sum(r.get('relevance_score', 0) for r in results if 'relevance_score' in r) / len([r for r in results if 'relevance_score' in r])
    avg_contamination = sum(r.get('contamination_score', 0) for r in results if 'contamination_score' in r) / len([r for r in results if 'contamination_score' in r])
    
    print(f"   📈 Average Domain Relevance: {avg_relevance:.1f}%")
    print(f"   📉 Average Contamination: {avg_contamination:.1f}%")
    
    if avg_contamination > 20:
        print("   🚨 WARNING: High contamination suggests hard-coded B2B bias")
        print("   💡 Recommendation: Implement AI-driven domain classification")
    
    if avg_relevance < 50:
        print("   🚨 WARNING: Low relevance suggests generic team generation")
        print("   💡 Recommendation: Enhance semantic role matching")
    
    print("\n" + "=" * 100)
    print("🏁 DOMAIN-AGNOSTIC TEST COMPLETE")
    print("=" * 100)
    
    return results

if __name__ == "__main__":
    # Ensure we have OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Test may not work properly.")
    
    asyncio.run(test_domain_agnostic_proposals())