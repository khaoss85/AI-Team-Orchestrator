#!/usr/bin/env python3
"""
Test Goal Validation API to debug dashboard issues
"""

import asyncio
import logging
import os
import sys
import json
from uuid import UUID

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_goal_validation_api():
    """Test the goal validation API directly"""
    
    print("🔍 TESTING GOAL VALIDATION API")
    print("="*50)
    
    try:
        # Import the validation route function directly
        from routes.goal_validation import validate_workspace_goals
        from database import supabase
        
        # Get existing workspace
        workspaces = supabase.table('workspaces').select('*').limit(1).execute().data
        if not workspaces:
            print("❌ No workspaces found in database")
            return
            
        workspace = workspaces[0]
        workspace_id = UUID(workspace['id'])
        
        print(f"📋 Testing workspace: {workspace['name']}")
        print(f"🎯 Goal: {workspace.get('goal', 'None')}")
        
        # Test the validation endpoint
        result = await validate_workspace_goals(
            workspace_id=workspace_id,
            use_database_goals=True
        )
        
        print("\n📊 API RESPONSE STRUCTURE:")
        print(json.dumps(result, indent=2, default=str))
        
        # Analyze the response structure
        print("\n🔍 ANALYSIS:")
        if 'validations' in result:
            validations = result['validations']
            print(f"✅ Found {len(validations)} validations")
            
            if validations:
                validation = validations[0]
                print("\n📋 First validation structure:")
                for key, value in validation.items():
                    print(f"  {key}: {type(value).__name__} = {value}")
        else:
            print("❌ No 'validations' key in response")
        
        # Check for frontend expected fields
        print("\n🎯 FRONTEND COMPATIBILITY CHECK:")
        frontend_fields = [
            'target_requirement', 'actual_achievement', 'achievement_percentage',
            'gap_percentage', 'is_valid', 'severity', 'validation_details', 'recommendations'
        ]
        
        if 'validations' in result and result['validations']:
            validation = result['validations'][0]
            for field in frontend_fields:
                if field in validation:
                    print(f"  ✅ {field}: {validation[field]}")
                else:
                    print(f"  ❌ {field}: MISSING")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_goal_validation_api())