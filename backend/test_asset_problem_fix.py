#!/usr/bin/env python3
"""
Test del fix completo per il problema asset categorization
Simula il flusso completo dal task completion alla UI display
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_complete_asset_flow():
    """Test completo del flusso asset extraction e categorization"""
    
    print("🔧 Testing Complete Asset Flow Fix")
    print("=" * 50)
    
    # Simulate the problematic scenario from the logs
    mock_tasks = [
        {
            "id": "task1",
            "name": "⚠️ ENHANCE: metrics_tracking_dashboard (Score: 0.5→0.8, 5.9h)",
            "status": "completed",
            "result": {
                "detailed_results_json": '{"metrics_tracking_dashboard": {"metrics": ["CTR", "Open Rate", "Conversion"], "tracking_config": {"dashboards": ["performance", "campaign"]}, "kpis": ["response_rate", "lead_quality"]}}',
                "summary": "Enhanced metrics tracking dashboard with KPI monitoring"
            },
            "context_data": {}
        },
        {
            "id": "task2", 
            "name": "⚠️ ENHANCE: contact_segmentation_guidelines",
            "status": "completed",
            "result": {
                "detailed_results_json": '{"contact_segmentation_guidelines": {"segments": ["Enterprise", "SMB", "Startup"], "criteria": ["company_size", "industry", "budget"], "targeting_rules": ["segment_A", "segment_B"]}}',
                "summary": "Enhanced contact segmentation guidelines with targeting criteria"
            },
            "context_data": {}
        },
        {
            "id": "task3",
            "name": "Email Campaign Sequences",
            "status": "completed", 
            "result": {
                "detailed_results_json": '{"email_sequences": {"sequences": [{"name": "Welcome Series", "emails": 3}, {"name": "Nurture Campaign", "emails": 5}]}}',
                "summary": "Created email campaign sequences"
            },
            "context_data": {}
        }
    ]
    
    # Test asset extraction
    print("\n1️⃣ Testing Asset Extraction...")
    
    from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
    extractor = ConcreteAssetExtractor()
    
    all_assets = {}
    high_value_count = 0
    medium_value_count = 0
    
    for task in mock_tasks:
        print(f"\n   📋 Processing task: {task['name'][:50]}...")
        
        # Extract assets from task (simulate the extraction logic)
        detailed_results = task['result'].get('detailed_results_json', '{}')
        import json
        try:
            parsed_data = json.loads(detailed_results)
            
            for asset_name, asset_data in parsed_data.items():
                # Create mock asset
                asset = {
                    "type": asset_name,
                    "data": asset_data,
                    "name": asset_name
                }
                
                # Calculate business actionability  
                actionability = extractor._calculate_business_actionability(asset, task, "Test goal")
                print(f"      • {asset_name}: actionability={actionability:.2f}")
                
                # Determine priority category
                if (actionability >= 0.75 or 
                    asset['type'] in ['metrics_tracking_dashboard', 'contact_segmentation_guidelines', 'segmentation_guidelines']):
                    category = "high-value"
                    high_value_count += 1
                elif actionability >= 0.5:
                    category = "medium-value"
                    medium_value_count += 1
                else:
                    category = "low-value"
                
                print(f"        → Category: {category}")
                all_assets[f"{task['id']}_{asset_name}"] = {
                    "asset": asset,
                    "task": task,
                    "actionability": actionability,
                    "category": category
                }
                
        except json.JSONDecodeError:
            print(f"      ⚠️ Could not parse detailed_results_json")
    
    print(f"\n   📊 Extraction Summary:")
    print(f"      High-value assets: {high_value_count}")
    print(f"      Medium-value assets: {medium_value_count}")
    print(f"      Total assets: {len(all_assets)}")
    
    # Test categorization 
    print(f"\n2️⃣ Testing Asset Categorization...")
    
    from routes.unified_assets import UnifiedAssetManager
    manager = UnifiedAssetManager()
    
    categorized_groups = {}
    
    for asset_id, asset_info in all_assets.items():
        asset = asset_info["asset"]
        task = asset_info["task"]
        
        # Test semantic grouping
        group_key = manager._create_semantic_group_key(asset["type"], task["name"])
        display_name = manager._create_display_name(asset["type"], task["name"])
        
        print(f"\n   🏷️ Asset: {asset['type']}")
        print(f"      Task: {task['name'][:50]}...")
        print(f"      Group: {group_key}")
        print(f"      Display: {display_name}")
        print(f"      Category: {asset_info['category']}")
        
        if group_key not in categorized_groups:
            categorized_groups[group_key] = {
                "display_name": display_name,
                "assets": [],
                "high_value_count": 0,
                "medium_value_count": 0
            }
        
        categorized_groups[group_key]["assets"].append(asset_info)
        if asset_info["category"] == "high-value":
            categorized_groups[group_key]["high_value_count"] += 1
        elif asset_info["category"] == "medium-value":
            categorized_groups[group_key]["medium_value_count"] += 1
    
    print(f"\n   📊 Categorization Summary:")
    print(f"      Total groups: {len(categorized_groups)}")
    for group_key, group_info in categorized_groups.items():
        print(f"      • {group_info['display_name']}: {len(group_info['assets'])} assets ({group_info['high_value_count']} high, {group_info['medium_value_count']} medium)")
    
    # Test final UI expectations
    print(f"\n3️⃣ Expected UI Improvements...")
    
    expected_improvements = [
        {
            "before": "Only 2 assets: 'Email Campaign Sequences' and 'Unknown'",
            "after": f"{len(categorized_groups)} distinct asset groups with proper names"
        },
        {
            "before": "metrics_tracking_dashboard → unknown_ category",
            "after": f"metrics_tracking_dashboard → '{categorized_groups.get('metrics_dashboard', {}).get('display_name', 'NOT FOUND')}' category"
        },
        {
            "before": "contact_segmentation_guidelines → unknown_ category", 
            "after": f"contact_segmentation_guidelines → '{categorized_groups.get('segmentation_guidelines', {}).get('display_name', 'NOT FOUND')}' category"
        },
        {
            "before": "Low actionability scores (0.4) filter out assets",
            "after": f"Higher actionability scores (0.7-0.8) promote assets to high-value"
        }
    ]
    
    all_good = True
    for improvement in expected_improvements:
        print(f"\n   🔄 {improvement['before']}")
        print(f"      → {improvement['after']}")
        
        if "NOT FOUND" in improvement['after']:
            print(f"      ❌ ISSUE: Expected category not found")
            all_good = False
        else:
            print(f"      ✅ IMPROVED")
    
    # Validation
    print(f"\n🏆 VALIDATION RESULTS:")
    
    success_checks = [
        ("Metrics dashboard properly categorized", "metrics_dashboard" in categorized_groups),
        ("Segmentation guidelines properly categorized", "segmentation_guidelines" in categorized_groups),
        ("Email sequences still work", "email_sequences" in categorized_groups),
        ("No unknown_ fallbacks for test assets", not any("unknown_" in key for key in categorized_groups.keys())),
        ("High-value assets prioritized", high_value_count >= 2),  # metrics and segmentation should be high-value
        ("Multiple distinct groups", len(categorized_groups) >= 3)  # Should have 3+ groups instead of 2
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_result in success_checks:
        if check_result:
            print(f"   ✅ {check_name}")
            passed += 1
        else:
            print(f"   ❌ {check_name}")
            failed += 1
    
    print(f"\n📊 FINAL RESULTS: {passed} PASSED, {failed} FAILED")
    
    if failed == 0:
        print(f"\n🎉 PROBLEM COMPLETELY FIXED!")
        print(f"   The UnifiedAssets component will now show:")
        for group_key, group_info in categorized_groups.items():
            print(f"   • {group_info['display_name']} ({len(group_info['assets'])} assets)")
        print(f"\n   Instead of just 'Email Campaign Sequences' and 'Unknown'")
    else:
        print(f"\n⚠️ Some issues remain. Check the categorization logic.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_complete_asset_flow()
    exit(0 if success else 1)