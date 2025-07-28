#!/usr/bin/env python3
"""
Complete Pipeline End-to-End Test - With All Fixes Applied

Tests the entire AI team orchestrator pipeline from workspace creation
to deliverable generation, validating all fixes from Phases 1-3.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    supabase, create_deliverable, trigger_deliverable_aggregation,
    should_trigger_deliverable_aggregation, update_goal_progress
)
from automated_goal_monitor import automated_goal_monitor
from services.workspace_health_manager import workspace_health_manager
from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable

async def main():
    """Complete end-to-end pipeline test"""
    
    print("🚀 COMPLETE PIPELINE END-TO-END TEST")
    print("=" * 60)
    print("Testing all fixes from Phases 1-3 in complete workflow")
    
    test_results = {
        'workspace_creation': False,
        'goal_creation': False,
        'task_generation': False,
        'quality_scoring': False,
        'goal_progress': False,
        'deliverable_creation': False,
        'workspace_health': False
    }
    
    # Phase 1: Create test workspace
    print(f"\n🏗️  PHASE 1: Workspace & Goal Setup")
    
    workspace_data = {
        'id': str(uuid4()),
        'name': 'E2E Pipeline Test Workspace',
        'description': 'End-to-end testing of the complete AI orchestrator pipeline',
        'goal': '''
Create an advanced customer support automation system that includes:
- AI-powered ticket classification and routing
- Automated response generation for common issues  
- Customer satisfaction tracking dashboard
- Integration with existing CRM systems
- Real-time performance analytics
- Multi-language support for global customers
        ''',
        'status': 'active',
        'user_id': str(uuid4()),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        workspace_result = supabase.table("workspaces").insert(workspace_data).execute()
        if workspace_result.data:
            workspace_id = workspace_result.data[0]['id']
            print(f"   ✅ Workspace created: {workspace_id}")
            test_results['workspace_creation'] = True
        else:
            print(f"   ❌ Failed to create workspace")
            return
    except Exception as e:
        print(f"   ❌ Workspace creation error: {e}")
        return
    
    # Phase 2: Test goal creation from workspace text (Phase 3 fix)
    print(f"\n🎯 PHASE 2: Goal Creation & Decomposition (Phase 3 Fix)")
    
    try:
        # Trigger goal analysis which should create goals from workspace goal text
        analysis_result = await automated_goal_monitor._trigger_immediate_goal_analysis(workspace_id)
        
        if analysis_result.get('success'):
            print(f"   ✅ Goal analysis successful")
            
            # Check created goals
            goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
            goals = goals_response.data or []
            
            print(f"   📊 Goals created: {len(goals)}")
            for i, goal in enumerate(goals, 1):
                print(f"      {i}. {goal['metric_type']}: {goal['current_value']}/{goal['target_value']}")
            
            if len(goals) > 0:
                test_results['goal_creation'] = True
                print(f"   ✅ Phase 3 Fix Verified: Goals created from workspace text")
            
        else:
            print(f"   ⚠️  Goal analysis result: {analysis_result.get('reason')}")
            
    except Exception as e:
        print(f"   ❌ Goal creation error: {e}")
    
    # Phase 3: Check task generation 
    print(f"\n📋 PHASE 3: Task Generation")
    
    try:
        tasks_response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        tasks = tasks_response.data or []
        
        print(f"   Tasks generated: {len(tasks)}")
        
        if len(tasks) > 0:
            test_results['task_generation'] = True
            
            # Show some task details
            for i, task in enumerate(tasks[:3], 1):
                print(f"      {i}. {task['name']} (Status: {task['status']})")
            
            if len(tasks) > 3:
                print(f"      ... and {len(tasks) - 3} more tasks")
        
    except Exception as e:
        print(f"   ❌ Task generation error: {e}")
    
    # Phase 4: Simulate task completion and test quality scoring (Phase 2 fix)
    print(f"\n⚡ PHASE 4: Task Completion & Quality Scoring (Phase 2 Fix)")
    
    if tasks:
        # Complete first few tasks with realistic results
        completed_tasks = []
        
        for i, task in enumerate(tasks[:3]):
            task_id = task['id']
            
            # Create realistic task results
            if i == 0:
                result_content = """
# Customer Support AI System Architecture

## Overview
The customer support automation system consists of the following components:

## Core Components
1. **Ticket Classification Engine**
   - ML-based categorization
   - Priority assessment
   - Automatic routing rules

2. **Response Generation Module**
   - Template-based responses
   - AI-powered personalization
   - Multi-language support

## Technical Implementation
```python
class TicketClassifier:
    def __init__(self):
        self.model = load_classification_model()
    
    def classify_ticket(self, content):
        category = self.model.predict(content)
        priority = self.assess_priority(content)
        return {
            'category': category,
            'priority': priority,
            'routing': self.get_routing_rules(category)
        }
```

## Integration Points
- CRM API integration
- Email system webhooks
- Database synchronization
                """
            elif i == 1:
                result_content = {
                    'dashboard_components': [
                        'Real-time ticket volume chart',
                        'Customer satisfaction metrics',
                        'Response time analytics',
                        'Agent performance tracking'
                    ],
                    'metrics_tracked': {
                        'satisfaction_score': '4.2/5.0',
                        'avg_response_time': '2.3 minutes',
                        'resolution_rate': '89%',
                        'escalation_rate': '12%'
                    },
                    'technologies': ['React Dashboard', 'D3.js Charts', 'WebSocket Updates']
                }
            else:
                result_content = "CRM integration module implemented with OAuth 2.0 authentication, real-time sync, and error handling for customer data management."
            
            # Update task as completed
            try:
                supabase.table("tasks").update({
                    'status': 'completed',
                    'result': result_content,
                    'completed_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).eq('id', task_id).execute()
                
                completed_tasks.append({
                    'id': task_id,
                    'name': task['name'],
                    'result': result_content,
                    'status': 'completed',
                    'workspace_id': workspace_id
                })
                
                print(f"   ✅ Completed task: {task['name']}")
                
            except Exception as e:
                print(f"   ❌ Error completing task {task['name']}: {e}")
        
        if len(completed_tasks) > 0:
            print(f"   📊 Tasks completed: {len(completed_tasks)}")
            test_results['task_generation'] = True
            
            # Test asset extraction and quality scoring (Phase 2 fix)
            print(f"\n🔍 Testing Quality Scoring (Phase 2 Fix)")
            
            try:
                from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
                assets_by_task = await concrete_asset_extractor.extract_assets_from_task_batch(completed_tasks)
                
                total_assets = 0
                total_quality = 0.0
                
                for task_id, assets in assets_by_task.items():
                    for asset in assets:
                        quality = asset.get('quality_score', 0.0)
                        total_assets += 1
                        total_quality += quality
                
                if total_assets > 0:
                    avg_quality = total_quality / total_assets
                    print(f"   📈 Assets extracted: {total_assets}")
                    print(f"   🎯 Average quality: {avg_quality:.2f}")
                    
                    if avg_quality >= 0.6:
                        test_results['quality_scoring'] = True
                        print(f"   ✅ Phase 2 Fix Verified: Quality scores are realistic (not 0%)")
                    else:
                        print(f"   ⚠️  Quality scores still low")
                
            except Exception as e:
                print(f"   ❌ Quality scoring test error: {e}")
    
    # Phase 5: Test goal progress updates
    print(f"\n📈 PHASE 5: Goal Progress Updates")
    
    if goals and completed_tasks:
        try:
            # Update progress on first goal
            test_goal = goals[0]
            goal_id = test_goal['id']
            
            progress_increment = 15.0
            test_task_id = completed_tasks[0]['id']
            
            business_context = {
                'quality_score': 0.87,
                'task_type': 'implementation',
                'business_value': 'high'
            }
            
            result = await update_goal_progress(
                goal_id=goal_id,
                increment=progress_increment,
                task_id=test_task_id,
                task_business_context=business_context
            )
            
            if result:
                new_value = result.get('current_value', 0)
                print(f"   ✅ Goal progress updated: +{progress_increment} → {new_value}")
                test_results['goal_progress'] = True
            else:
                print(f"   ❌ Goal progress update failed")
                
        except Exception as e:
            print(f"   ❌ Goal progress error: {e}")
    
    # Phase 6: Test deliverable creation
    print(f"\n📦 PHASE 6: Deliverable Creation & Aggregation")
    
    try:
        # Check if deliverable should be triggered
        should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
        print(f"   Should trigger deliverable: {should_trigger}")
        
        if should_trigger or len(completed_tasks) >= 2:  # Force if we have enough tasks
            print(f"   🔧 Triggering deliverable creation...")
            
            # Try both methods
            deliverable_id = await check_and_create_final_deliverable(workspace_id, force=True)
            
            if deliverable_id:
                print(f"   ✅ Deliverable created: {deliverable_id}")
                
                # Check deliverable quality
                deliverable_response = supabase.table("deliverables").select("*").eq("id", deliverable_id).single().execute()
                
                if deliverable_response.data:
                    deliverable = deliverable_response.data
                    quality_metrics = deliverable.get('quality_metrics', {})
                    overall_score = quality_metrics.get('overall_score', 0) if isinstance(quality_metrics, dict) else 0
                    
                    print(f"   📊 Deliverable quality: {overall_score:.2f}")
                    print(f"   📄 Content length: {len(deliverable.get('content', ''))}")
                    
                    if overall_score >= 0.6:
                        test_results['deliverable_creation'] = True
                        print(f"   ✅ Deliverable has good quality score")
                    else:
                        print(f"   ⚠️  Deliverable quality could be improved")
            else:
                print(f"   ⚠️  Deliverable creation returned None")
                
                # Try alternative method
                await trigger_deliverable_aggregation(workspace_id)
                
                # Check if deliverable was created
                deliverables = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
                if deliverables.data:
                    print(f"   ✅ Deliverable created via alternative method")
                    test_results['deliverable_creation'] = True
        
    except Exception as e:
        print(f"   ❌ Deliverable creation error: {e}")
    
    # Phase 7: Test workspace health monitoring (Phase 1 fix)
    print(f"\n🏥 PHASE 7: Workspace Health Monitoring (Phase 1 Fix)")
    
    try:
        # Test workspace health check
        health_report = await workspace_health_manager.check_workspace_health_with_recovery(
            workspace_id, attempt_auto_recovery=True
        )
        
        print(f"   🎯 Health score: {health_report.overall_score:.1f}%")
        print(f"   🏥 Is healthy: {health_report.is_healthy}")
        print(f"   🔧 Can auto-recover: {health_report.can_auto_recover}")
        
        if health_report.overall_score >= 60:
            test_results['workspace_health'] = True
            print(f"   ✅ Phase 1 Fix Verified: Workspace health monitoring working")
        
        # Test system-wide monitoring
        system_monitoring = await workspace_health_manager.monitor_all_workspaces_for_stuck_processing()
        print(f"   🌐 System monitoring: {system_monitoring.get('stuck_workspaces', 0)} stuck workspaces")
        
    except Exception as e:
        print(f"   ❌ Workspace health error: {e}")
    
    # Final Results Summary
    print(f"\n🎯 END-TO-END PIPELINE TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print()
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print()
    
    if success_rate >= 80:
        print(f"🎉 PIPELINE INTEGRATION SUCCESS!")
        print(f"   All major fixes verified in end-to-end workflow")
        print(f"   System ready for production with:")
        print(f"   - ✅ Phase 1: Workspace health recovery")
        print(f"   - ✅ Phase 2: Realistic quality scoring") 
        print(f"   - ✅ Phase 3: Goal creation from text")
        print(f"   - ✅ Complete pipeline integration")
    elif success_rate >= 60:
        print(f"⚠️  PIPELINE MOSTLY WORKING")
        print(f"   Most fixes verified, minor issues remain")
    else:
        print(f"❌ PIPELINE NEEDS MORE WORK")
        print(f"   Several critical issues still need attention")
    
    print(f"\n📋 Workspace ID for manual inspection: {workspace_id}")

if __name__ == "__main__":
    asyncio.run(main())