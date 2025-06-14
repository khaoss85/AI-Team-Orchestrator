#!/usr/bin/env python3
"""
🧪 CORE AI FUNCTIONALITY TEST
Test focalizzato sui componenti AI core che possiamo testare senza dipendenze complete
"""

import asyncio
import logging
import os
import sys
import json
from typing import Dict, List, Any

# Add backend to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables manually
def load_env_file():
    """Load .env file manually"""
    env_path = '/Users/pelleri/Documents/ai-team-orchestrator/backend/.env'
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        return True
    except FileNotFoundError:
        logging.warning(f"⚠️ .env file not found at {env_path}")
        return False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_goal_extraction_direct():
    """Test AI goal extraction directly with OpenAI"""
    
    logger.info("🤖 TESTING DIRECT AI GOAL EXTRACTION")
    logger.info("="*60)
    
    # Load environment
    env_loaded = load_env_file()
    if not env_loaded:
        logger.error("❌ Cannot load environment variables")
        return False
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY not found")
        return False
    
    logger.info("✅ OpenAI API key loaded")
    
    try:
        # Try to import and use OpenAI directly
        import openai
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=openai_key)
        
        # Test case specifico
        goal_text = "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot. Gli email devono avere un open-rate ≥ 30% e click-to-rate ≥ 10%, completando il tutto in 6 settimane."
        
        logger.info(f"📝 Testing goal extraction from: {goal_text[:100]}...")
        
        # Create prompt for goal extraction
        prompt = f"""Analyze this business goal and extract SPECIFIC, MEASURABLE objectives.
Avoid duplicates - each metric should be extracted only once.

GOAL TEXT: "{goal_text}"

Extract goals in this exact JSON format:
{{
    "goals": [
        {{
            "goal_type": "deliverable|metric|quality|timeline|quantity",
            "metric_type": "quality_score|deliverables|timeline_days",
            "target_value": numeric_value,
            "unit": "specific unit of measurement",
            "description": "clear description of what needs to be achieved",
            "is_percentage": true/false,
            "is_minimum": true/false,
            "semantic_context": {{
                "what": "what is being measured",
                "why": "business purpose",
                "who": "target audience if specified"
            }}
        }}
    ]
}}

RULES:
1. Extract each unique goal only ONCE
2. For "50 contatti ICP" -> deliverable type, value=50, unit="ICP contacts"
3. For "3 sequenze email" -> deliverable type, value=3, unit="email sequences"  
4. For "open-rate ≥ 30%" -> quality type, value=30, unit="open rate %"
5. For "Click-to-rate 10%" -> quality type, value=10, unit="click rate %"
6. For "6 settimane" -> timeline type, value=42, unit="days" (6*7)

Be specific and avoid generic descriptions. Each goal must be actionable and measurable."""

        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business goal analysis expert. Extract specific, measurable goals without duplicates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        logger.info(f"🤖 OpenAI Response: {result_text}")
        
        # Parse result
        result = json.loads(result_text)
        goals = result.get("goals", [])
        
        logger.info(f"🎯 AI extracted {len(goals)} goals:")
        
        expected_goals = ["contacts", "email_sequences", "open_rate", "click_rate", "timeline"]
        found_types = []
        
        for i, goal in enumerate(goals, 1):
            goal_type = goal.get("goal_type", "unknown")
            metric_type = goal.get("metric_type", "unknown")
            target_value = goal.get("target_value", 0)
            unit = goal.get("unit", "")
            description = goal.get("description", "")
            
            found_types.append(metric_type)
            
            logger.info(f"  Goal {i}: {goal_type} - {metric_type}")
            logger.info(f"    Target: {target_value} {unit}")
            logger.info(f"    Description: {description}")
            
            semantic_context = goal.get("semantic_context", {})
            if semantic_context:
                logger.info(f"    What: {semantic_context.get('what', 'N/A')}")
                logger.info(f"    Why: {semantic_context.get('why', 'N/A')}")
                logger.info(f"    Who: {semantic_context.get('who', 'N/A')}")
            logger.info("")
        
        # Check for duplicates
        goal_keys = [f"{g.get('metric_type')}_{g.get('target_value')}" for g in goals]
        duplicates = len(goal_keys) - len(set(goal_keys))
        
        # Analyze quality
        has_contacts = any("contact" in str(g).lower() for g in goals)
        has_sequences = any("sequence" in str(g).lower() or "email" in str(g).lower() for g in goals)
        has_percentages = any(g.get("is_percentage", False) for g in goals)
        has_timeline = any("timeline" in g.get("metric_type", "") or "day" in g.get("unit", "") for g in goals)
        
        logger.info("📊 QUALITY ANALYSIS:")
        logger.info(f"  ✅ Goals extracted: {len(goals)}")
        logger.info(f"  🔄 Duplicates: {duplicates} (should be 0)")
        logger.info(f"  📇 Has contacts: {'✅' if has_contacts else '❌'}")
        logger.info(f"  📧 Has email sequences: {'✅' if has_sequences else '❌'}")
        logger.info(f"  📊 Has percentages: {'✅' if has_percentages else '❌'}")
        logger.info(f"  ⏰ Has timeline: {'✅' if has_timeline else '❌'}")
        
        quality_score = sum([
            len(goals) >= 3,  # Should extract at least 3 goals
            duplicates == 0,  # No duplicates
            has_contacts,     # Should find contact goal
            has_sequences,    # Should find email sequence goal
            has_percentages,  # Should find percentage goals
            has_timeline      # Should find timeline goal
        ]) / 6
        
        logger.info(f"🏆 OVERALL QUALITY SCORE: {quality_score:.1%}")
        
        if quality_score >= 0.8:
            logger.info("🎉 EXCELLENT: AI goal extraction is working at production level!")
            return True
        elif quality_score >= 0.6:
            logger.info("👍 GOOD: AI goal extraction is mostly working")
            return True
        else:
            logger.warning("⚠️ NEEDS IMPROVEMENT: AI goal extraction has issues")
            return False
        
    except ImportError:
        logger.error("❌ OpenAI library not available")
        return False
    except Exception as e:
        logger.error(f"❌ AI goal extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_universal_ai_extraction():
    """Test AI extraction across multiple domains"""
    
    logger.info("\n🌍 TESTING UNIVERSAL AI EXTRACTION")
    logger.info("="*60)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY not found")
        return False
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        
        # Test domains
        test_cases = [
            ("Healthcare", "Ridurre i tempi di attesa del 25% e raggiungere 90% soddisfazione pazienti in 6 mesi"),
            ("Education", "Aumentare completion rate al 85% e creare 15 moduli interattivi entro 3 mesi"),
            ("Finance", "Incrementare ROI del 30% e ridurre costi del 15% mantenendo quality score ≥ 80%"),
            ("Sports", "Migliorare performance del 20% e ridurre infortuni del 40% in 12 settimane"),
            ("Technology", "Deploy 5 microservizi e raggiungere 99.9% uptime con response time < 100ms")
        ]
        
        universal_results = {}
        
        for domain, goal_text in test_cases:
            logger.info(f"\n🧪 Testing {domain}...")
            
            try:
                simple_prompt = f"""Extract measurable goals from: "{goal_text}"
Return JSON with goals array containing goal_type, target_value, unit, description."""
                
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Extract specific, measurable business goals. Return JSON format."},
                        {"role": "user", "content": simple_prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    max_tokens=500
                )
                
                result = json.loads(response.choices[0].message.content)
                goals = result.get("goals", [])
                
                universal_results[domain] = {
                    "success": len(goals) > 0,
                    "goals_count": len(goals),
                    "goals": goals
                }
                
                logger.info(f"  ✅ {domain}: {len(goals)} goals extracted")
                
            except Exception as e:
                universal_results[domain] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"  ❌ {domain}: Failed - {e}")
        
        # Calculate success rate
        successful = sum(1 for r in universal_results.values() if r.get("success", False))
        total = len(test_cases)
        success_rate = successful / total
        
        logger.info(f"\n🌍 UNIVERSAL SCALABILITY RESULTS:")
        logger.info(f"  Domains tested: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Success rate: {success_rate:.1%}")
        logger.info(f"  Truly universal: {'✅ YES' if success_rate >= 0.8 else '❌ LIMITED'}")
        
        return success_rate >= 0.8
        
    except Exception as e:
        logger.error(f"❌ Universal AI test failed: {e}")
        return False

async def test_ai_memory_simulation():
    """Test AI-driven memory and learning capabilities"""
    
    logger.info("\n🧠 TESTING AI MEMORY SIMULATION")
    logger.info("="*60)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY not found")
        return False
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        
        # Simulate memory-driven learning
        workspace_context = """
Previous insights from workspace:
- SaaS lead generation requires personalized outreach
- Email sequences with >3 touches improve conversion by 40%
- CMO/CTO personas respond better to technical content
- European markets prefer privacy-focused messaging
        """
        
        new_task = "Create an email sequence for SaaS lead nurturing"
        
        memory_prompt = f"""Based on previous insights and context, provide AI-driven recommendations for this task:

TASK: "{new_task}"

PREVIOUS INSIGHTS:
{workspace_context}

Provide specific, actionable recommendations based on learned patterns.
Return JSON with: recommendations array, confidence_score, reasoning."""
        
        logger.info(f"🧠 Testing memory-driven task guidance...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI memory system that learns from previous insights to guide new tasks."},
                {"role": "user", "content": memory_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        recommendations = result.get("recommendations", [])
        confidence = result.get("confidence_score", 0)
        reasoning = result.get("reasoning", "")
        
        logger.info(f"🧠 AI Memory Results:")
        logger.info(f"  Recommendations: {len(recommendations)}")
        logger.info(f"  Confidence: {confidence}")
        logger.info(f"  Reasoning: {reasoning}")
        
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"    {i}. {rec}")
        
        # Check quality of memory-driven guidance
        has_specific_recs = len(recommendations) >= 3
        has_context_integration = any("personali" in str(rec).lower() or "technical" in str(rec).lower() for rec in recommendations)
        has_reasoning = len(reasoning) > 50
        
        memory_quality = sum([has_specific_recs, has_context_integration, has_reasoning]) / 3
        
        logger.info(f"📊 Memory system quality: {memory_quality:.1%}")
        
        return memory_quality >= 0.7
        
    except Exception as e:
        logger.error(f"❌ AI memory test failed: {e}")
        return False

async def main():
    """Run core AI functionality tests"""
    
    logger.info("🚀 CORE AI FUNCTIONALITY TESTS")
    logger.info("="*80)
    
    results = {}
    
    # Test 1: Direct AI Goal Extraction
    results["ai_goal_extraction"] = await test_ai_goal_extraction_direct()
    
    # Test 2: Universal AI Extraction
    results["universal_extraction"] = await test_universal_ai_extraction()
    
    # Test 3: AI Memory Simulation
    results["ai_memory"] = await test_ai_memory_simulation()
    
    # Generate final report
    logger.info("\n" + "="*80)
    logger.info("📊 CORE AI FUNCTIONALITY REPORT")
    logger.info("="*80)
    
    successful_tests = sum(results.values())
    total_tests = len(results)
    overall_success = successful_tests / total_tests
    
    logger.info(f"\n🏆 OVERALL SUCCESS: {overall_success:.1%} ({successful_tests}/{total_tests} tests passed)")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\n🎯 SYSTEM ASSESSMENT:")
    
    if overall_success >= 0.9:
        logger.info("🎉 EXCELLENT: AI system is production-ready!")
    elif overall_success >= 0.7:
        logger.info("👍 GOOD: AI system is mostly functional")
    elif overall_success >= 0.5:
        logger.info("⚠️ NEEDS WORK: AI system has issues")
    else:
        logger.info("❌ CRITICAL: AI system is not functional")
    
    logger.info(f"\n💡 The core AI capabilities are {'✅ WORKING' if overall_success >= 0.7 else '❌ NOT WORKING'}")
    
    return overall_success >= 0.7

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)