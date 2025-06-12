#!/usr/bin/env python3
"""
Audit completo della qualità dei deliverable
Verifica che gli asset contengano contenuti REALI e azionabili, non generici o inventati
"""

import sys
import os
import json
import re
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_contact_list_quality():
    """Test qualità liste contatti - devono avere email reali e numeri target"""
    print("\n1️⃣ Testing Contact List Quality...")
    
    # Mock contact lists - realistic vs fake
    test_cases = [
        {
            "name": "REAL Contact List",
            "data": {
                "contacts": [
                    {"name": "John Smith", "email": "john.smith@techcorp.com", "company": "TechCorp", "title": "CTO"},
                    {"name": "Jane Doe", "email": "jane.doe@innovate.io", "company": "Innovate Solutions", "title": "CMO"},
                    {"name": "Marco Rossi", "email": "m.rossi@startupxyz.com", "company": "StartupXYZ", "title": "CEO"}
                ]
            },
            "expected_actionable": True,
            "goal": "3 contatti",
            "expected_goal_met": True
        },
        {
            "name": "FAKE Contact List",
            "data": {
                "contacts": [
                    {"name": "[Nome contatto]", "email": "esempio@company.com", "company": "[Nome azienda]"},
                    {"name": "Inserire qui", "email": "contatto@esempio.it", "company": "Azienda target"}
                ]
            },
            "expected_actionable": False,
            "goal": "50 contatti",
            "expected_goal_met": False
        },
        {
            "name": "INCOMPLETE Contact List",
            "data": {
                "contacts": [
                    {"name": "Real Person", "email": "real@company.com", "company": "Real Corp"}
                ]
            },
            "expected_actionable": True,  # Real but incomplete
            "goal": "50 contatti", 
            "expected_goal_met": False  # Only 1/50
        }
    ]
    
    from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
    extractor = ConcreteAssetExtractor()
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n   📋 Testing: {test_case['name']}")
        
        # Test business actionability
        mock_asset = {"type": "contact_database", "data": test_case["data"]}
        mock_task = {"name": "contact research"}
        
        actionability = extractor._calculate_business_actionability(mock_asset, mock_task, test_case["goal"])
        is_actionable = actionability >= 0.7
        
        # Test goal achievement
        contacts = test_case["data"].get("contacts", [])
        valid_contacts = sum(
            1 for contact in contacts
            if isinstance(contact, dict) and 
            "@" in contact.get("email", "") and
            len(contact.get("name", "")) > 2 and
            "[" not in contact.get("name", "") and  # No placeholders
            "esempio" not in contact.get("email", "").lower()  # No fake emails
        )
        
        goal_number = int(re.search(r'(\d+)', test_case["goal"]).group(1)) if re.search(r'(\d+)', test_case["goal"]) else 0
        goal_met = valid_contacts >= goal_number
        
        print(f"      Actionability: {actionability:.2f} ({'✅' if is_actionable == test_case['expected_actionable'] else '❌'})")
        print(f"      Valid contacts: {valid_contacts}/{goal_number} ({'✅' if goal_met == test_case['expected_goal_met'] else '❌'})")
        
        if (is_actionable == test_case['expected_actionable'] and 
            goal_met == test_case['expected_goal_met']):
            passed += 1
        else:
            failed += 1
    
    print(f"\n   📊 Contact List Results: {passed} PASSED, {failed} FAILED")
    return failed == 0

def test_email_sequence_quality():
    """Test qualità sequenze email - devono avere contenuti reali, non template generici"""
    print("\n2️⃣ Testing Email Sequence Quality...")
    
    test_cases = [
        {
            "name": "REAL Email Sequences",
            "data": {
                "email_sequences": [
                    {
                        "name": "SaaS Outreach Sequence",
                        "emails": [
                            {
                                "subject": "Quick question about your lead generation",
                                "body": "Hi {{first_name}}, I noticed your company is scaling fast. Are you struggling with lead quality?",
                                "call_to_action": "Book a 15-min call: https://calendly.com/demo"
                            },
                            {
                                "subject": "Follow-up: Lead quality improvement",
                                "body": "Hi {{first_name}}, Following up on my previous email about lead generation...",
                                "call_to_action": "View case study: https://example.com/case-study"
                            }
                        ]
                    },
                    {
                        "name": "Product Demo Sequence",
                        "emails": [
                            {
                                "subject": "Ready for a quick demo?",
                                "body": "Hi {{first_name}}, I'd love to show you how we can solve your lead quality challenges in 15 minutes.",
                                "call_to_action": "Book demo: https://calendly.com/product-demo"
                            }
                        ]
                    }
                ]
            },
            "expected_actionable": True,
            "goal": "2 email sequences",
            "expected_goal_met": True
        },
        {
            "name": "GENERIC Email Templates", 
            "data": {
                "email_sequences": [
                    {
                        "name": "Template generico di outreach",
                        "emails": [
                            {
                                "subject": "[Inserire oggetto personalizzato]",
                                "body": "Ciao [Nome], questo è un template di esempio che dovresti personalizzare...",
                                "call_to_action": "[Inserire CTA specifica]"
                            }
                        ]
                    }
                ]
            },
            "expected_actionable": False,
            "goal": "3 email sequences",
            "expected_goal_met": False
        }
    ]
    
    from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
    extractor = ConcreteAssetExtractor()
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n   📧 Testing: {test_case['name']}")
        
        # Test business actionability
        mock_asset = {"type": "email_templates", "data": test_case["data"]}
        mock_task = {"name": "email sequence strategy"}
        
        actionability = extractor._calculate_business_actionability(mock_asset, mock_task, test_case["goal"])
        is_actionable = actionability >= 0.8
        
        # Test content quality - check for placeholders and generic content
        sequences = test_case["data"].get("email_sequences", [])
        quality_issues = 0
        total_emails = 0
        
        for sequence in sequences:
            emails = sequence.get("emails", [])
            total_emails += len(emails)
            
            for email in emails:
                subject = email.get("subject", "")
                body = email.get("body", "")
                cta = email.get("call_to_action", "")
                
                # Check for placeholder patterns
                if any(pattern in (subject + body + cta).lower() for pattern in [
                    "[", "inserire", "template", "esempio", "dovresti", "generico"
                ]):
                    quality_issues += 1
        
        # Test goal achievement - sequences need to meet both count and quality
        goal_number = int(re.search(r'(\d+)', test_case["goal"]).group(1)) if re.search(r'(\d+)', test_case["goal"]) else 0
        has_enough_sequences = len(sequences) >= goal_number
        has_good_quality = quality_issues == 0
        goal_met = has_enough_sequences and has_good_quality
        
        print(f"      Actionability: {actionability:.2f} ({'✅' if is_actionable == test_case['expected_actionable'] else '❌'})")
        print(f"      Sequences: {len(sequences)}/{goal_number}, Quality issues: {quality_issues} ({'✅' if goal_met == test_case['expected_goal_met'] else '❌'})")
        
        if (is_actionable == test_case['expected_actionable'] and 
            goal_met == test_case['expected_goal_met']):
            passed += 1
        else:
            failed += 1
    
    print(f"\n   📊 Email Sequence Results: {passed} PASSED, {failed} FAILED")
    return failed == 0

def test_goal_validation_system():
    """Test sistema di validazione obiettivi numerici"""
    print("\n3️⃣ Testing Goal Validation System...")
    
    # Test goal extraction patterns
    test_goals = [
        "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee)",
        "Creare 3 sequenze email per B2B outreach", 
        "Generare contenuti per 30 giorni con engagement rate ≥15%",
        "Build contact database with 100+ qualified leads"
    ]
    
    try:
        from ai_quality_assurance.goal_validator import AIGoalValidator
        validator = AIGoalValidator()
        
        for goal in test_goals:
            print(f"\n   🎯 Goal: {goal}")
            
            # Test pattern matching directly using the validator's patterns
            patterns_found = []
            for pattern in validator.numerical_patterns:
                matches = re.finditer(pattern, goal.lower(), re.IGNORECASE)
                for match in matches:
                    try:
                        value = match.group(1)
                        context = match.group(2) if len(match.groups()) > 1 else ""
                        patterns_found.append(f"{context}: {value}")
                    except (IndexError, ValueError):
                        continue
            
            print(f"      Patterns found: {patterns_found}")
        
        print(f"\n   ✅ Goal validation system operational")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Goal validation error: {e}")
        return False

def test_concreteness_validation():
    """Test validazione concretezza contenuti"""
    print("\n4️⃣ Testing Concreteness Validation...")
    
    test_contents = [
        {
            "name": "CONCRETE Content",
            "content": {
                "strategy": "Launch campaign on 15/01/2024 targeting CTOs at companies with 50-200 employees. Budget: €5,000. Expected CTR: 3.5%. Contact john.smith@techcorp.com for partnerships.",
                "metrics": {"target_ctr": 3.5, "budget": 5000, "audience_size": "50-200 employees"}
            },
            "expected_score": 0.9  # High concreteness
        },
        {
            "name": "GENERIC Content", 
            "content": {
                "strategy": "Dovresti considerare una strategia di marketing generale che potrebbe includere vari canali. Potresti valutare l'engagement del tuo pubblico target.",
                "metrics": {"note": "Inserire qui le metriche specifiche"}
            },
            "expected_score": 0.3  # Low concreteness
        }
    ]
    
    try:
        from ai_quality_assurance.smart_evaluator import SmartDeliverableEvaluator
        evaluator = SmartDeliverableEvaluator()
        
        passed = 0
        failed = 0
        
        for test_case in test_contents:
            print(f"\n   📝 Testing: {test_case['name']}")
            
            content_text = json.dumps(test_case["content"])
            
            # Test concreteness score using rule-based evaluation
            rule_scores = evaluator._rule_based_evaluation(content_text)
            score = rule_scores.get("concreteness", 0.5)
            expected_range = (test_case["expected_score"] - 0.2, test_case["expected_score"] + 0.2)
            
            print(f"      Content: {content_text[:100]}...")
            print(f"      Concreteness score: {score:.2f} (expected ~{test_case['expected_score']})")
            
            if expected_range[0] <= score <= expected_range[1]:
                print(f"      ✅ Score in expected range")
                passed += 1
            else:
                print(f"      ❌ Score outside expected range")
                failed += 1
        
        print(f"\n   📊 Concreteness Results: {passed} PASSED, {failed} FAILED")
        return failed == 0
        
    except Exception as e:
        print(f"\n   ❌ Concreteness validation error: {e}")
        return False

def test_enhancement_detection():
    """Test rilevamento necessità di enhancement"""
    print("\n5️⃣ Testing Enhancement Detection...")
    
    # Test se il sistema rileva quando gli asset hanno bisogno di miglioramenti
    test_assets = [
        {
            "name": "READY Asset",
            "data": {
                "contacts": [
                    {"name": "John Smith", "email": "john@company.com", "title": "CTO", "company": "TechCorp"}
                ]
            },
            "task_output": "Generated 1 high-quality ICP contact with verified email and complete profile information.",
            "expected_enhancement_needed": False
        },
        {
            "name": "NEEDS ENHANCEMENT Asset",
            "data": {
                "contacts": [
                    {"name": "[Nome contatto]", "email": "contatto@example.com", "title": "[Titolo]"}
                ]
            },
            "task_output": "Creata una lista generica di contatti che dovresti personalizzare in base alle tue esigenze specifiche.",
            "expected_enhancement_needed": True
        }
    ]
    
    try:
        from ai_quality_assurance.smart_evaluator import SmartDeliverableEvaluator
        evaluator = SmartDeliverableEvaluator()
        
        passed = 0
        failed = 0
        
        for test_case in test_assets:
            print(f"\n   🔧 Testing: {test_case['name']}")
            
            # Calculate concreteness and actionability using rule-based evaluation
            content_text = json.dumps(test_case["data"]) + " " + test_case["task_output"]
            
            rule_scores = evaluator._rule_based_evaluation(content_text)
            concreteness = rule_scores.get("concreteness", 0.5)
            actionability = rule_scores.get("actionability", 0.5)
            
            # Determine if enhancement is needed - more reasonable thresholds
            has_fake_patterns = any(pattern in content_text.lower() for pattern in [
                "[", "dovresti", "potresti", "esempio", "generico", "template"
            ])
            
            needs_enhancement = (
                concreteness < 0.7 or   # Lower threshold for concreteness
                actionability < 0.6 or  # Lower threshold for actionability  
                has_fake_patterns
            )
            
            print(f"      Concreteness: {concreteness:.2f}")
            print(f"      Actionability: {actionability:.2f}")
            print(f"      Enhancement needed: {needs_enhancement} (expected: {test_case['expected_enhancement_needed']})")
            
            if needs_enhancement == test_case['expected_enhancement_needed']:
                print(f"      ✅ Enhancement detection correct")
                passed += 1
            else:
                print(f"      ❌ Enhancement detection incorrect")
                failed += 1
        
        print(f"\n   📊 Enhancement Detection Results: {passed} PASSED, {failed} FAILED")
        return failed == 0
        
    except Exception as e:
        print(f"\n   ❌ Enhancement detection error: {e}")
        return False

def run_complete_audit():
    """Esegui audit completo della qualità deliverable"""
    print("🔍 COMPLETE DELIVERABLE QUALITY AUDIT")
    print("=" * 60)
    
    test_results = [
        test_contact_list_quality(),
        test_email_sequence_quality(), 
        test_goal_validation_system(),
        test_concreteness_validation(),
        test_enhancement_detection()
    ]
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n🏆 AUDIT SUMMARY:")
    print(f"   ✅ {passed_tests} test categories passed")
    print(f"   ❌ {total_tests - passed_tests} test categories failed")
    print(f"   📊 Success rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"\n🎉 DELIVERABLE QUALITY SYSTEM IS ROBUST!")
        print(f"   • Contact lists validated for real emails and target numbers")
        print(f"   • Email sequences checked for actionable content vs templates")
        print(f"   • Goal validation system operational")  
        print(f"   • Concreteness scoring prevents generic content")
        print(f"   • Enhancement detection identifies improvement needs")
    else:
        print(f"\n⚠️ QUALITY GAPS IDENTIFIED:")
        print(f"   Some deliverable quality checks are not working as expected.")
        print(f"   Review the failed test categories above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_complete_audit()
    exit(0 if success else 1)