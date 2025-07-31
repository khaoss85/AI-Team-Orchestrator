#!/usr/bin/env python3
"""
Test Pipeline Monitoring System

Tests the monitoring system that prevents future pipeline blocks.
"""

import asyncio
import os
import sys

# Add backend to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Test monitoring system implementation"""
    
    print("🚨 TESTING PIPELINE MONITORING SYSTEM")
    print("=" * 60)
    
    # Test monitoring system components
    test_results = {
        'workspace_health_monitoring': False,
        'quality_system_monitoring': False,
        'goal_system_monitoring': False,
        'monitoring_integration': False
    }
    
    # Test 1: Workspace Health Monitoring (Phase 1 prevention)
    print(f"\n🏥 TEST 1: Workspace Health Monitoring")
    try:
        from services.workspace_health_manager import workspace_health_manager
        
        # Test system-wide monitoring 
        result = await workspace_health_manager.monitor_all_workspaces_for_stuck_processing()
        
        print(f"   📊 Stuck workspaces found: {result.get('stuck_workspaces', 0)}")
        print(f"   🔧 Workspaces recovered: {result.get('recovered', 0)}")
        
        if 'stuck_workspaces' in result:
            test_results['workspace_health_monitoring'] = True
            print(f"   ✅ Workspace health monitoring operational")
        
    except Exception as e:
        print(f"   ❌ Workspace monitoring error: {e}")
    
    # Test 2: Quality System Monitoring (Phase 2 prevention)
    print(f"\n🎯 TEST 2: Quality System Monitoring")
    try:
        from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
        
        # Test quality calculation with monitoring data
        test_asset = {
            'asset_type': 'code',
            'asset_name': 'monitoring_sample',
            'content': 'def monitor_system():\\n    return health_check()',
            'byte_size': 50,
            'confidence': 0.85
        }
        
        quality_score = concrete_asset_extractor._calculate_asset_quality(test_asset)
        print(f"   📊 Sample quality score: {quality_score:.2f}")
        
        if quality_score >= 0.6:
            test_results['quality_system_monitoring'] = True
            print(f"   ✅ Quality system producing healthy scores")
        else:
            print(f"   ⚠️  Quality scores need attention")
            
    except Exception as e:
        print(f"   ❌ Quality monitoring error: {e}")
    
    # Test 3: Goal System Monitoring (Phase 3 prevention)
    print(f"\n🎯 TEST 3: Goal System Monitoring")
    try:
        from database import supabase
        
        # Check for potential goal creation issues
        workspaces_response = supabase.table("workspaces").select("id, goal").execute()
        workspaces_with_goals = [
            ws for ws in (workspaces_response.data or [])
            if ws.get("goal") and len(ws["goal"].strip()) > 10
        ]
        
        goal_issues = 0
        for workspace in workspaces_with_goals[:3]:  # Check first 3
            workspace_id = workspace["id"]
            
            goals_response = supabase.table("workspace_goals").select("id").eq(
                "workspace_id", workspace_id
            ).execute()
            
            if not goals_response.data:
                goal_issues += 1
        
        print(f"   📊 Workspaces with goals: {len(workspaces_with_goals)}")
        print(f"   ⚠️  Potential goal creation issues: {goal_issues}")
        
        if goal_issues <= len(workspaces_with_goals) * 0.5:  # Less than 50% issues
            test_results['goal_system_monitoring'] = True
            print(f"   ✅ Goal system monitoring functional")
        else:
            print(f"   ⚠️  Goal system needs monitoring attention")
            
    except Exception as e:
        print(f"   ❌ Goal monitoring error: {e}")
    
    # Test 4: Integrated Monitoring System
    print(f"\n🚨 TEST 4: Integrated Monitoring System")
    try:
        from services.pipeline_monitor import pipeline_monitor
        
        # Test comprehensive health check
        health_report = await pipeline_monitor.run_comprehensive_health_check()
        
        print(f"   🎯 Overall status: {health_report.get('overall_status', 'unknown')}")
        print(f"   📊 Components checked: {len(health_report.get('components', {}))}")
        print(f"   🚨 Alerts generated: {len(health_report.get('alerts', []))}")
        print(f"   💡 Recommendations: {len(health_report.get('recommendations', []))}")
        
        # Show some recommendations
        recommendations = health_report.get('recommendations', [])[:3]
        if recommendations:
            print(f"   💡 Sample recommendations:")
            for rec in recommendations:
                print(f"      - {rec}")
        
        if health_report.get('overall_status') in ['healthy', 'warning']:
            test_results['monitoring_integration'] = True
            print(f"   ✅ Integrated monitoring system operational")
        else:
            print(f"   ⚠️  Monitoring system needs attention")
            
    except Exception as e:
        print(f"   ❌ Integrated monitoring error: {e}")
    
    # Summary
    print(f"\n📈 MONITORING SYSTEM TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(test_results.values()) 
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print()
    
    for test_name, passed in test_results.items():
        status = "✅ OPERATIONAL" if passed else "❌ NEEDS WORK"
        display_name = test_name.replace('_', ' ').title()
        print(f"   {status} {display_name}")
    
    print()
    
    if success_rate >= 75:
        print(f"🎉 MONITORING SYSTEM READY!")
        print(f"   Proactive monitoring implemented to prevent:")
        print(f"   - Phase 1 issues: Workspace status locks")
        print(f"   - Phase 2 issues: Quality scoring problems")
        print(f"   - Phase 3 issues: Goal creation failures")
        print(f"   - Future pipeline blocks through early detection")
    elif success_rate >= 50:
        print(f"⚠️  MONITORING PARTIALLY WORKING")
        print(f"   Core monitoring functions operational")
    else:
        print(f"❌ MONITORING NEEDS MORE DEVELOPMENT")
        print(f"   Critical monitoring components require attention")
    
    print(f"\n🔧 PHASE 5: Monitoring implementation {'✅ COMPLETE' if success_rate >= 75 else '⚠️ IN PROGRESS'}")

if __name__ == "__main__":
    asyncio.run(main())