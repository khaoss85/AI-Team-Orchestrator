#!/usr/bin/env python3
"""
Test Enhanced Achievement Extraction System
Verifies that the new robust achievement extraction correctly identifies deliverables
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_achievement_extraction():
    """Test the enhanced achievement extraction system"""
    print("🧪 Testing Enhanced Achievement Extraction System...")
    
    try:
        from services.deliverable_achievement_mapper import deliverable_achievement_mapper
        from database import extract_task_achievements
        
        # Test scenarios with realistic task outputs
        test_scenarios = [
            {
                "name": "Contact List Task",
                "task_name": "Compile List of 500 ICP Contacts in SaaS",
                "result_payload": {
                    "output": "Successfully compiled a comprehensive list of 500 ICP contacts in the SaaS industry",
                    "contacts_compiled": 500,
                    "industry": "SaaS",
                    "verification_status": "completed",
                    "data_quality": "high"
                },
                "expected_items": 500,
                "expected_deliverables": 1
            },
            {
                "name": "Email Sequence Task", 
                "task_name": "Create 7-Email Lead Nurturing Sequence",
                "result_payload": {
                    "output": "Created a complete 7-email nurturing sequence with subject lines and CTAs",
                    "sequence_length": 7,
                    "email_templates": ["welcome", "value_1", "value_2", "case_study", "demo", "urgency", "final"],
                    "completion_status": "delivered"
                },
                "expected_items": 7,
                "expected_deliverables": 1
            },
            {
                "name": "Marketing Strategy Task",
                "task_name": "Develop Comprehensive Instagram Marketing Strategy", 
                "result_payload": {
                    "output": "Developed a comprehensive Instagram marketing strategy including content calendar, posting schedule, and engagement tactics",
                    "strategy_components": {
                        "content_calendar": "30-day calendar created",
                        "posting_schedule": "3 posts per day schedule defined",
                        "engagement_tactics": "5 key tactics outlined"
                    },
                    "deliverable_status": "completed"
                },
                "expected_items": 1,
                "expected_deliverables": 1
            },
            {
                "name": "Data Analysis Task",
                "task_name": "Analyze Customer Data and Generate Insights Report",
                "result_payload": {
                    "output": "Analyzed 1,250 customer records and generated comprehensive insights report",
                    "records_processed": 1250,
                    "insights_generated": 15,
                    "report_sections": ["demographics", "behavior", "preferences", "recommendations"],
                    "metrics": {
                        "conversion_rate": "12.5%",
                        "retention_rate": "85%",
                        "satisfaction_score": "4.2/5"
                    }
                },
                "expected_items": 1250,
                "expected_deliverables": 1
            }
        ]
        
        total_tests = len(test_scenarios)
        passed_tests = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test {i}/{total_tests}: {scenario['name']}")
            print(f"   Task: '{scenario['task_name']}'")
            
            try:
                # Test the enhanced achievement extraction
                achievement_result = await deliverable_achievement_mapper.extract_achievements_robust(
                    scenario["result_payload"], 
                    scenario["task_name"]
                )
                
                print(f"   🤖 Method: {achievement_result.extraction_method}")
                print(f"   🎯 Confidence: {achievement_result.confidence_score:.2f}")
                print(f"   💡 Reasoning: {achievement_result.reasoning}")
                print(f"   📊 Results:")
                print(f"     - Items Created: {achievement_result.items_created}")
                print(f"     - Deliverables: {achievement_result.deliverables_completed}")
                print(f"     - Data Processed: {achievement_result.data_processed}")
                print(f"     - Metrics: {achievement_result.metrics_achieved}")
                
                # Verify expectations
                success = True
                if "expected_items" in scenario:
                    if achievement_result.items_created < scenario["expected_items"] * 0.8:  # 80% tolerance
                        print(f"   ❌ Items created too low: {achievement_result.items_created} < {scenario['expected_items']}")
                        success = False
                    else:
                        print(f"   ✅ Items created OK: {achievement_result.items_created} >= {scenario['expected_items']}")
                
                if "expected_deliverables" in scenario:
                    if achievement_result.deliverables_completed < scenario["expected_deliverables"]:
                        print(f"   ❌ Deliverables too low: {achievement_result.deliverables_completed} < {scenario['expected_deliverables']}")
                        success = False
                    else:
                        print(f"   ✅ Deliverables OK: {achievement_result.deliverables_completed} >= {scenario['expected_deliverables']}")
                
                if achievement_result.confidence_score < 0.3:
                    print(f"   ❌ Confidence too low: {achievement_result.confidence_score:.2f}")
                    success = False
                else:
                    print(f"   ✅ Confidence acceptable: {achievement_result.confidence_score:.2f}")
                
                if success:
                    print(f"   🎉 PASS: {scenario['name']}")
                    passed_tests += 1
                else:
                    print(f"   ❌ FAIL: {scenario['name']}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        # Test database integration
        print(f"\n🔗 Testing database integration...")
        try:
            # Test the public wrapper function
            db_result = await extract_task_achievements(
                test_scenarios[0]["result_payload"],
                test_scenarios[0]["task_name"]
            )
            
            if db_result and any(v > 0 for v in db_result.values()):
                print(f"   ✅ Database integration working: {db_result}")
                passed_tests += 1
                total_tests += 1
            else:
                print(f"   ❌ Database integration failed: {db_result}")
                total_tests += 1
                
        except Exception as e:
            print(f"   ❌ Database integration error: {e}")
            total_tests += 1
        
        # Final results
        print(f"\n🏁 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("🎉 Achievement extraction system working well!")
            return True
        else:
            print(f"⚠️ Achievement extraction needs improvement")
            return False
        
    except ImportError as e:
        print(f"❌ Could not import achievement mapper: {e}")
        return False
    except Exception as e:
        print(f"❌ Critical error in achievement extraction tests: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_achievement_extraction())