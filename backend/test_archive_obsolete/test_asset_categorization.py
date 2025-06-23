#!/usr/bin/env python3
"""
Test del sistema di categorizzazione asset migliorato
Verifica che assets come metrics_tracking_dashboard e contact_segmentation_guidelines
vengano categorizzati correttamente invece di finire in "unknown_"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_asset_categorization():
    """Test delle nuove categorizzazioni asset"""
    
    print("🔧 Testing Enhanced Asset Categorization")
    print("=" * 50)
    
    # Import the UnifiedAssetManager class
    from routes.unified_assets import UnifiedAssetManager
    
    # Create test instance
    unified_assets = UnifiedAssetManager()
    
    # Test cases based on the log examples
    test_cases = [
        {
            "asset_type": "metrics_tracking_dashboard",
            "task_name": "⚠️ ENHANCE: metrics_tracking_dashboard (Score: 0.5→0.8, 5.9h)",
            "expected_group": "metrics_dashboard",
            "expected_display": "Metrics & Tracking Dashboard"
        },
        {
            "asset_type": "contact_segmentation_guidelines", 
            "task_name": "⚠️ ENHANCE: contact_segmentation_guidelines",
            "expected_group": "segmentation_guidelines",
            "expected_display": "Contact Segmentation Guidelines"
        },
        {
            "asset_type": "dashboard",
            "task_name": "Create KPI Dashboard",
            "expected_group": "metrics_dashboard", 
            "expected_display": "Metrics & Tracking Dashboard"
        },
        {
            "asset_type": "guidelines",
            "task_name": "Audience Targeting Guidelines",
            "expected_group": "segmentation_guidelines",
            "expected_display": "Contact Segmentation Guidelines"
        },
        {
            "asset_type": "unknown",
            "task_name": "Email campaign tracking metrics dashboard",
            "expected_group": "metrics_dashboard",
            "expected_display": "Metrics & Tracking Dashboard" 
        },
        {
            "asset_type": "unknown",
            "task_name": "Contact segmentation and targeting guidelines", 
            "expected_group": "segmentation_guidelines",
            "expected_display": "Contact Segmentation Guidelines"
        },
        {
            "asset_type": "email_templates",
            "task_name": "Email Campaign Sequences",
            "expected_group": "email_sequences",
            "expected_display": "Email Campaign Sequences"
        }
    ]
    
    # Test each case
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: {test_case['asset_type']} | {test_case['task_name'][:50]}...")
        
        # Test semantic group key
        group_key = unified_assets._create_semantic_group_key(
            test_case["asset_type"], 
            test_case["task_name"]
        )
        
        # Test display name
        display_name = unified_assets._create_display_name(
            test_case["asset_type"],
            test_case["task_name"] 
        )
        
        # Check results
        group_correct = group_key == test_case["expected_group"]
        display_correct = display_name == test_case["expected_display"]
        
        if group_correct and display_correct:
            print(f"   ✅ PASS: Group='{group_key}', Display='{display_name}'")
            passed += 1
        else:
            print(f"   ❌ FAIL:")
            if not group_correct:
                print(f"      Group: Expected '{test_case['expected_group']}', Got '{group_key}'")
            if not display_correct:
                print(f"      Display: Expected '{test_case['expected_display']}', Got '{display_name}'")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} PASSED, {failed} FAILED")
    
    # Test business actionability scoring
    print(f"\n🎯 Testing Business Actionability Scoring...")
    
    from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
    extractor = ConcreteAssetExtractor()
    
    scoring_tests = [
        {
            "asset": {"type": "metrics_tracking_dashboard", "data": {"metrics": ["ctr", "open_rate"], "tracking": True}},
            "task": {"name": "metrics tracking dashboard"},
            "expected_min": 0.7,  # Should be medium-high
            "description": "Metrics dashboard with structured data"
        },
        {
            "asset": {"type": "contact_segmentation_guidelines", "data": {"segments": ["enterprise", "smb"], "criteria": ["size", "industry"]}},
            "task": {"name": "contact segmentation guidelines"},
            "expected_min": 0.75,  # Should be high
            "description": "Segmentation guidelines with structured data"
        },
        {
            "asset": {"type": "dashboard", "data": {}},
            "task": {"name": "generic dashboard"},
            "expected_min": 0.6,  # Should be medium
            "description": "Generic dashboard"
        }
    ]
    
    scoring_passed = 0
    scoring_failed = 0
    
    for i, test in enumerate(scoring_tests, 1):
        print(f"\n{i}️⃣ Scoring: {test['description']}")
        
        score = extractor._calculate_business_actionability(
            test["asset"], 
            test["task"], 
            "Test workspace goal"
        )
        
        if score >= test["expected_min"]:
            print(f"   ✅ PASS: Score={score:.2f} (>={test['expected_min']})")
            scoring_passed += 1
        else:
            print(f"   ❌ FAIL: Score={score:.2f} (expected >={test['expected_min']})")
            scoring_failed += 1
    
    print(f"\n📊 Scoring Results: {scoring_passed} PASSED, {scoring_failed} FAILED")
    
    # Summary
    total_passed = passed + scoring_passed
    total_failed = failed + scoring_failed
    
    print(f"\n🏆 OVERALL RESULTS:")
    print(f"   ✅ {total_passed} tests passed")
    print(f"   ❌ {total_failed} tests failed")
    
    if total_failed == 0:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Assets like 'metrics_tracking_dashboard' and 'contact_segmentation_guidelines'")
        print(f"   will now be properly categorized instead of falling into 'unknown_'")
        print(f"\n🔧 Expected improvements:")
        print(f"   • Metrics dashboards → 'Metrics & Tracking Dashboard' category")
        print(f"   • Segmentation guidelines → 'Contact Segmentation Guidelines' category") 
        print(f"   • Higher business actionability scores (0.7-0.8 instead of 0.4-0.6)")
        print(f"   • Better asset visibility in the UI")
    else:
        print(f"\n⚠️ Some tests failed. Review the categorization logic.")
    
    return total_failed == 0

if __name__ == "__main__":
    success = test_asset_categorization()
    exit(0 if success else 1)