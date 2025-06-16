#!/usr/bin/env python3
"""
Test the FIXED Goal Validation API response structure
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

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
    except FileNotFoundError:
        print(f"⚠️ .env file not found at {env_path}")

load_env_file()

async def test_fixed_api_response():
    """Test the FIXED goal validation API with correct field mappings"""
    
    print("🔍 TESTING FIXED GOAL VALIDATION API")
    print("="*50)
    
    try:
        from ai_quality_assurance.goal_validator import goal_validator
        from database import supabase, get_workspace, list_tasks
        
        # Get existing workspace
        workspaces = supabase.table('workspaces').select('*').limit(1).execute().data
        if not workspaces:
            print("❌ No workspaces found in database")
            return
            
        workspace = workspaces[0]
        workspace_id = workspace['id']
        
        print(f"📋 Testing workspace: {workspace['name']}")
        print(f"🎯 Goal: {workspace.get('goal', 'None')}")
        
        # Get workspace details
        workspace_data = await get_workspace(workspace_id)
        workspace_goal = workspace_data.get("goal", "")
        
        # Get completed tasks
        all_tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        
        print(f"📋 Found {len(completed_tasks)} completed tasks")
        
        # Get database goals with FIXED query
        from models import GoalStatus
        database_goals = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).in_(
            "status", [GoalStatus.ACTIVE.value, GoalStatus.COMPLETED.value]
        ).execute().data
        
        print(f"🎯 Found {len(database_goals)} database goals")
        
        # Test validation with database goals
        if database_goals:
            print("\n🧪 Testing database goal validation...")
            validations = await goal_validator.validate_database_goals_achievement(
                database_goals, completed_tasks, workspace_id
            )
        else:
            print("\n🧪 Testing workspace goal validation...")
            validations = await goal_validator.validate_workspace_goal_achievement(
                workspace_goal, completed_tasks, workspace_id
            )
        
        print(f"✅ Got {len(validations)} validation results")
        
        # Simulate the FIXED API response structure
        if validations:
            # Calculate overall metrics (from goal_validation.py)
            overall_achievement = sum(1.0 - (v.gap_percentage / 100) for v in validations) / len(validations)
            critical_issues = [v for v in validations if v.severity.value == 'critical']
            high_issues = [v for v in validations if v.severity.value == 'high']
            
            # Determine validation status
            if len(critical_issues) > 0:
                validation_status = "critical_issues"
            elif len(high_issues) > 0:
                validation_status = "high_priority_issues"
            elif overall_achievement >= 0.9:
                validation_status = "goals_achieved"
            elif overall_achievement >= 0.7:
                validation_status = "mostly_achieved"
            else:
                validation_status = "significant_gaps"
            
            fixed_api_response = {
                "workspace_id": workspace_id,
                "workspace_goal": workspace_goal,
                "validation_status": validation_status,
                "overall_achievement": round(overall_achievement * 100, 1),
                "total_validations": len(validations),
                "critical_issues": len(critical_issues),
                "high_priority_issues": len(high_issues),
                # FIXED: Frontend expects 'validation_results' not 'validations'
                "validation_results": [
                    {
                        # FIXED: Frontend field name mappings
                        "target_requirement": v.target_requirement,
                        "actual_achievement": v.actual_achievement,
                        "achievement_percentage": round(100 - v.gap_percentage, 1),  # FIXED: Calculate achievement percentage
                        "gap_percentage": round(v.gap_percentage, 1),
                        "severity": v.severity.value,
                        "is_valid": v.is_valid,
                        "confidence": round(v.confidence, 2),
                        "message": v.validation_message,
                        "recommendations": v.recommendations[:3],
                        "validation_details": v.extracted_metrics,  # FIXED: Frontend expects this field
                        "extracted_metrics": v.extracted_metrics
                    }
                    for v in validations
                ],
                "completed_tasks_analyzed": len(completed_tasks),
                "validation_timestamp": datetime.now().isoformat()
            }
            
            print("\n📊 FIXED API RESPONSE (Frontend Compatible):")
            print(json.dumps(fixed_api_response, indent=2, default=str))
            
            # Check frontend compatibility
            print("\n✅ FRONTEND COMPATIBILITY CHECK:")
            validation_results = fixed_api_response["validation_results"]
            if validation_results:
                validation = validation_results[0]
                frontend_fields = [
                    'target_requirement', 'actual_achievement', 'achievement_percentage',
                    'gap_percentage', 'is_valid', 'severity', 'validation_details', 'recommendations'
                ]
                
                for field in frontend_fields:
                    if field in validation:
                        print(f"  ✅ {field}: {validation[field]}")
                    else:
                        print(f"  ❌ {field}: MISSING")
            
            print(f"\n🎯 SUMMARY:")
            print(f"  📊 Total validations: {len(validation_results)}")
            print(f"  🟢 Overall achievement: {fixed_api_response['overall_achievement']}%")
            print(f"  📈 Status: {fixed_api_response['validation_status']}")
            print(f"  🚨 Critical issues: {fixed_api_response['critical_issues']}")
            print(f"  ⚠️ High priority issues: {fixed_api_response['high_priority_issues']}")
            
            # Show individual validation results
            print(f"\n📋 INDIVIDUAL VALIDATION RESULTS:")
            for i, result in enumerate(validation_results, 1):
                print(f"  {i}. {result['target_requirement']} -> {result['actual_achievement']}")
                print(f"     Achievement: {result['achievement_percentage']}% | Gap: {result['gap_percentage']}% | Severity: {result['severity']}")
                print(f"     Valid: {'✅' if result['is_valid'] else '❌'}")
                
        else:
            print("❌ No validation results returned")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_api_response())