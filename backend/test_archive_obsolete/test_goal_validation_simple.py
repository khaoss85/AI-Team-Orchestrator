#!/usr/bin/env python3
"""
Test Goal Validation API to debug dashboard issues
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

async def test_goal_validation():
    """Test the goal validation directly without FastAPI"""
    
    print("🔍 TESTING GOAL VALIDATION DIRECTLY")
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
        
        # Get database goals (include completed goals)
        database_goals = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).in_(
            "status", ["active", "completed"]
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
        
        # Simulate the API response structure
        if validations:
            # Calculate overall metrics (from goal_validation.py)
            overall_achievement = sum(1.0 - (v.gap_percentage / 100) for v in validations) / len(validations)
            critical_issues = [v for v in validations if v.severity.value == 'critical']
            high_issues = [v for v in validations if v.severity.value == 'high']
            
            api_response = {
                "workspace_id": workspace_id,
                "workspace_goal": workspace_goal,
                "validation_status": "goals_achieved" if overall_achievement >= 0.9 else "significant_gaps",
                "overall_achievement": round(overall_achievement * 100, 1),
                "total_validations": len(validations),
                "critical_issues": len(critical_issues),
                "high_priority_issues": len(high_issues),
                "validations": [
                    {
                        "requirement": v.target_requirement,
                        "achievement": v.actual_achievement,
                        "gap_percentage": round(v.gap_percentage, 1),
                        "severity": v.severity.value,
                        "is_valid": v.is_valid,
                        "confidence": round(v.confidence, 2),
                        "message": v.validation_message,
                        "recommendations": v.recommendations[:3],
                        "extracted_metrics": v.extracted_metrics
                    }
                    for v in validations
                ],
                "completed_tasks_analyzed": len(completed_tasks),
                "validation_timestamp": datetime.now().isoformat()
            }
            
            print("\n📊 SIMULATED API RESPONSE:")
            print(json.dumps(api_response, indent=2, default=str))
            
            # Check field mapping issues
            print("\n🔍 FIELD MAPPING ANALYSIS:")
            print("Backend provides -> Frontend expects:")
            validation = api_response["validations"][0]
            print(f"  'requirement' -> 'target_requirement': {validation.get('requirement', 'MISSING')}")
            print(f"  'achievement' -> 'actual_achievement': {validation.get('achievement', 'MISSING')}")
            print(f"  'gap_percentage' -> 'gap_percentage': {validation.get('gap_percentage', 'MISSING')}")
            print(f"  'severity' -> 'severity': {validation.get('severity', 'MISSING')}")
            print(f"  'is_valid' -> 'is_valid': {validation.get('is_valid', 'MISSING')}")
            print(f"  'recommendations' -> 'recommendations': {validation.get('recommendations', 'MISSING')}")
            print(f"  MISSING -> 'achievement_percentage': Not provided by backend")
            print(f"  MISSING -> 'validation_details': Not provided by backend")
            
        else:
            print("❌ No validation results returned")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_goal_validation())