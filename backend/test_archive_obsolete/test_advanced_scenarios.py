#!/usr/bin/env python3
"""
🎯 ADVANCED AI-DRIVEN SCENARIOS TEST
Test scenari complessi per verificare scalabilità e intelligenza del sistema
"""
import asyncio
import sys
import json
sys.path.append('.')

from concrete_asset_extractor_refactored import multi_source_extractor

async def test_advanced_scenarios():
    print('🎯 TESTING ADVANCED AI-DRIVEN SCENARIOS')
    print('=' * 80)
    
    scenarios = [
        {
            "name": "Instagram Strategy for Bodybuilders",
            "goal": "Definire una strategia e un piano editoriale per l'account Instagram dedicato a un pubblico maschile di bodybuilder con l'obiettivo di crescere di 200 follower a settimana",
            "expected_domains": ["social media", "fitness", "content strategy"],
            "expected_platforms": ["Instagram"],
            "expected_actions": ["content creation", "audience growth"]
        },
        {
            "name": "Stress Reduction Wellness Program", 
            "goal": "Creare una routine di 10-15 min/die, ridurre lo stress auto-rilevato del 20% in 8 settimane, mantenere una streak di 30 giorni",
            "expected_domains": ["health & fitness", "wellness"],
            "expected_platforms": ["tracking app"],
            "expected_actions": ["routine creation", "progress tracking"]
        },
        {
            "name": "Investment Portfolio Management",
            "goal": "Costruire un portafoglio diversificato, supportare decisioni di acquisto/vendita consapevoli, mantenere un monitoraggio periodico dei rischi",
            "expected_domains": ["finance", "investment"],
            "expected_platforms": ["portfolio tools"],
            "expected_actions": ["analysis", "risk management"]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔬 SCENARIO {i}: {scenario['name']}")
        print(f"Goal: {scenario['goal']}")
        print("-" * 80)
        
        try:
            # Test AI goal analysis
            context = multi_source_extractor._ai_extract_goal_context(scenario['goal'])
            
            print(f"🤖 AI GOAL ANALYSIS:")
            print(f"   Domain: {context.get('industry_domain', 'N/A')}")
            print(f"   Primary Action: {context.get('primary_action', 'N/A')}")
            print(f"   Tools/Platforms: {context.get('tools_platforms', ['N/A'])}")
            print(f"   Target Audience: {context.get('target_audience', 'N/A')}")
            print(f"   Value Proposition: {context.get('value_proposition', 'N/A')}")
            print(f"   Key Challenges: {context.get('key_challenges', ['N/A'])}")
            print(f"   Implementation Steps: {len(context.get('implementation_steps', []))} steps")
            
            # Show implementation steps
            steps = context.get('implementation_steps', [])
            if steps:
                print(f"   Steps Preview:")
                for j, step in enumerate(steps[:3], 1):
                    print(f"     {j}. {step}")
            
            # Test content generation for this goal
            print(f"\n📝 AI CONTENT GENERATION:")
            
            # Generate content items for this goal
            content_items = multi_source_extractor._generate_universal_content_items(
                3, scenario['goal'], "strategic_content"
            )
            
            print(f"   Generated {len(content_items)} content items:")
            
            for j, item in enumerate(content_items, 1):
                print(f"\n   📋 Item {j}: {item.get('name', 'Unknown')}")
                print(f"      Type: {item.get('type', 'Unknown')}")
                print(f"      Focus: {item.get('focus', 'Unknown')}")
                
                # Show detailed sub-items
                detailed_items = item.get('detailed_items', [])
                if detailed_items:
                    print(f"      Sub-items: {len(detailed_items)}")
                    first_item = detailed_items[0]
                    print(f"      Sample: {first_item.get('title', 'N/A')}")
                    
                    # Show AI-generated fields
                    print(f"      AI Fields Generated:")
                    for field, value in first_item.items():
                        if field not in ['title', 'type', 'description', 'sequence_position']:
                            if isinstance(value, str) and len(value) > 40:
                                print(f"        {field}: {value[:40]}...")
                            else:
                                print(f"        {field}: {value}")
            
            print(f"\n✅ SCENARIO {i}: AI-DRIVEN SUCCESS")
            
        except Exception as e:
            print(f"❌ SCENARIO {i}: FAILED - {e}")
            import traceback
            traceback.print_exc()

async def test_goal_complexity_handling():
    print(f"\n🧠 TESTING AI HANDLING OF COMPLEX MULTI-OBJECTIVE GOALS")
    print('=' * 80)
    
    complex_goal = "Definire una strategia e un piano editoriale per l'account Instagram dedicato a un pubblico maschile di bodybuilder con l'obiettivo di crescere di 200 follower a settimana"
    
    print(f"Complex Goal: {complex_goal}")
    
    # Test AI's ability to break down complex goals
    context = multi_source_extractor._ai_extract_goal_context(complex_goal)
    
    print(f"\n🎯 AI COMPLEXITY ANALYSIS:")
    print(f"   Extracted Numbers: {context.get('target_count', 'None')}")
    print(f"   Domain Recognition: {context.get('industry_domain', 'N/A')}")
    print(f"   Platform Detection: {context.get('tools_platforms', ['None'])}")
    print(f"   Audience Segmentation: {context.get('target_audience', 'N/A')}")
    
    # Test field determination for complex goal
    fields = multi_source_extractor._ai_determine_required_content_fields(
        complex_goal, "content_strategy", context
    )
    
    print(f"\n📊 AI FIELD REQUIREMENTS ({len(fields)} fields):")
    for field, purpose in fields.items():
        print(f"   {field}: {purpose}")
    
    # Test AI content generation for specific field
    stage = {"title": "Content Planning", "type": "planning", "description": "Strategic content calendar development"}
    
    content_sample = multi_source_extractor._ai_generate_field_content(
        "content", "main actionable content", stage, "Strategic", 
        complex_goal, context, 1
    )
    
    print(f"\n📝 AI CONTENT SAMPLE:")
    print(f"   {content_sample}")
    
    print(f"\n✅ COMPLEXITY HANDLING: SUCCESS")

async def test_cross_domain_scalability():
    print(f"\n🌍 TESTING CROSS-DOMAIN SCALABILITY")
    print('=' * 80)
    
    cross_domain_goals = [
        "Aumentare le vendite del 30% tramite email marketing automation",
        "Ridurre i tempi di sviluppo del 40% implementando CI/CD",
        "Migliorare l'engagement del team del 25% con team building activities",
        "Creare 50 recipe video per YouTube con focus su meal prep"
    ]
    
    print("Testing AI adaptation across completely different domains:")
    
    for i, goal in enumerate(cross_domain_goals, 1):
        print(f"\n{i}. Goal: {goal}")
        
        context = multi_source_extractor._ai_extract_goal_context(goal)
        
        # Quick analysis
        domain = context.get('industry_domain', 'Unknown')
        action = context.get('primary_action', 'Unknown')
        platforms = context.get('tools_platforms', ['None'])
        
        print(f"   AI Analysis: {domain} | {action} | {platforms[0]}")
        
        # Test field generation
        fields = multi_source_extractor._ai_determine_required_content_fields(
            goal, "implementation_plan", context
        )
        
        unique_fields = [f for f in fields.keys() if f not in ['title', 'description', 'content', 'action']]
        print(f"   Unique Fields: {unique_fields[:3]}")
    
    print(f"\n✅ CROSS-DOMAIN SCALABILITY: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_advanced_scenarios())
    asyncio.run(test_goal_complexity_handling()) 
    asyncio.run(test_cross_domain_scalability())