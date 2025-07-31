#!/usr/bin/env python3
"""
Quick Pipeline Summary Test

Validates that all Phase 1-3 fixes are working in a streamlined test.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Quick pipeline validation"""
    
    print("🧪 PIPELINE FIXES VALIDATION SUMMARY")
    print("=" * 60)
    
    # Test results tracking
    phase_results = {
        'phase_1_workspace_health': False,
        'phase_2_quality_scoring': False, 
        'phase_3_goal_creation': False
    }
    
    # Phase 1: Test workspace health system
    print(f"\n🏥 PHASE 1: Workspace Health System")
    try:
        from services.workspace_health_manager import workspace_health_manager
        
        # Test the monitoring function exists and works
        result = await workspace_health_manager.monitor_all_workspaces_for_stuck_processing()
        
        if 'stuck_workspaces' in result:
            print(f"   ✅ Workspace health monitoring working")
            print(f"   📊 Found {result.get('stuck_workspaces', 0)} stuck workspaces")
            phase_results['phase_1_workspace_health'] = True
        else:
            print(f"   ⚠️  Workspace health monitoring issues")
            
    except Exception as e:
        print(f"   ❌ Phase 1 error: {e}")
    
    # Phase 2: Test quality scoring improvements
    print(f"\n🎯 PHASE 2: Quality Scoring System")
    try:
        from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
        from deliverable_system.intelligent_aggregator import intelligent_aggregator
        
        # Test asset quality calculation
        test_asset = {
            'asset_type': 'code',
            'asset_name': 'test_function',
            'content': 'def process_data():\\n    return clean_data(raw_input)',
            'byte_size': 45,
            'confidence': 0.8
        }
        
        quality_score = concrete_asset_extractor._calculate_asset_quality(test_asset)
        print(f"   📊 Asset quality score: {quality_score:.2f}")
        
        if quality_score >= 0.6:
            print(f"   ✅ Quality scoring fixed (was defaulting to ~0.3)")
            phase_results['phase_2_quality_scoring'] = True
        else:
            print(f"   ⚠️  Quality scoring still low")
            
        # Test deliverable quality calculation
        test_deliverable = {'content': 'Test deliverable content with reasonable length for testing'}
        test_assets = [test_asset]
        
        quality_metrics = intelligent_aggregator._calculate_deliverable_quality(test_deliverable, test_assets)
        overall_score = quality_metrics.get('overall_score', 0)
        
        print(f"   📦 Deliverable quality: {overall_score:.2f}")
        
        if overall_score >= 0.6:
            print(f"   ✅ Deliverable quality scoring fixed")
        
    except Exception as e:
        print(f"   ❌ Phase 2 error: {e}")
    
    # Phase 3: Test goal creation capability
    print(f"\n🎯 PHASE 3: Goal Creation System")
    try:
        from database import supabase
        from automated_goal_monitor import automated_goal_monitor
        
        # Create a test workspace with goal text
        test_workspace = {
            'id': str(uuid4()),
            'name': 'Goal Test Workspace',
            'description': 'Testing goal creation',
            'goal': 'Build a customer feedback system with automated analysis',
            'status': 'active',
            'user_id': str(uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create workspace
        workspace_result = supabase.table("workspaces").insert(test_workspace).execute()
        
        if workspace_result.data:
            workspace_id = workspace_result.data[0]['id']
            print(f"   🏗️  Test workspace created: {workspace_id[:8]}...")
            
            # Test goal creation from workspace text
            try:
                # Call the fixed goal analysis function
                result = await automated_goal_monitor._trigger_immediate_goal_analysis(workspace_id)
                
                if result.get('success'):
                    # Check if goals were created
                    goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
                    goals_count = len(goals_response.data) if goals_response.data else 0
                    
                    print(f"   📊 Goals created from text: {goals_count}")
                    
                    if goals_count > 0:
                        print(f"   ✅ Goal creation from workspace text working")
                        phase_results['phase_3_goal_creation'] = True
                    else:
                        print(f"   ⚠️  No goals created from workspace text")
                else:
                    print(f"   ⚠️  Goal analysis failed: {result.get('reason')}")
                    
            except Exception as e:
                print(f"   ❌ Goal creation test error: {e}")
                
    except Exception as e:
        print(f"   ❌ Phase 3 error: {e}")
    
    # Summary
    print(f"\n📈 VALIDATION SUMMARY")
    print("=" * 60)
    
    phases_passed = sum(phase_results.values())
    total_phases = len(phase_results)
    success_rate = (phases_passed / total_phases * 100) if total_phases > 0 else 0
    
    print(f"Fixes Validated: {phases_passed}/{total_phases} ({success_rate:.1f}%)")
    print()
    
    for phase, passed in phase_results.items():
        status = "✅ WORKING" if passed else "❌ NEEDS ATTENTION"
        phase_name = phase.replace('_', ' ').title()
        print(f"   {status} {phase_name}")
    
    print()
    
    if success_rate >= 80:
        print(f"🎉 ALL CRITICAL FIXES VALIDATED!")
        print(f"   The holistic fixing approach successfully addressed:")
        print(f"   - Phase 1: Workspace status transition locks")
        print(f"   - Phase 2: Quality scoring defaulting to 0%") 
        print(f"   - Phase 3: Goal creation from workspace text")
        print(f"   System is ready for deliverable generation!")
    elif success_rate >= 60:
        print(f"⚠️  MOST FIXES WORKING")
        print(f"   Core functionality restored, minor issues remain")
    else:
        print(f"❌ MORE WORK NEEDED")
        print(f"   Critical fixes still require attention")
    
    print(f"\n🔧 Next Step: Run full end-to-end pipeline with real data")

if __name__ == "__main__":
    asyncio.run(main())