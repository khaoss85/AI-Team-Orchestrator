#!/usr/bin/env python3
"""
🛠️ Fix Database Constraint for Universal metric_type
Removes hardcoded GoalMetricType constraint to enable agnostic goals
"""

import asyncio
import logging
from database import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_database_constraint():
    """Remove the hardcoded metric_type constraint"""
    
    logger.info("🔧 Removing hardcoded metric_type constraint...")
    
    try:
        # First check current constraint
        check_result = supabase.rpc('exec_sql', {
            'sql': """
            SELECT conname, contype 
            FROM pg_constraint 
            JOIN pg_class ON conrelid = pg_class.oid 
            WHERE pg_class.relname = 'workspace_goals' 
            AND contype = 'c';
            """
        }).execute()
        
        logger.info(f"Current constraints: {check_result.data}")
        
        # Remove the check constraint
        result = supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE workspace_goals DROP CONSTRAINT IF EXISTS workspace_goals_metric_type_check;'
        }).execute()
        
        logger.info("✅ Database constraint removed successfully")
        
        # Verify the constraint is gone
        verify_result = supabase.rpc('exec_sql', {
            'sql': """
            SELECT conname, contype 
            FROM pg_constraint 
            JOIN pg_class ON conrelid = pg_class.oid 
            WHERE pg_class.relname = 'workspace_goals' 
            AND contype = 'c';
            """
        }).execute()
        
        logger.info(f"Remaining constraints: {verify_result.data}")
        
        # Test with a custom metric_type
        logger.info("🧪 Testing with custom metric_type...")
        
        test_workspace = "4d21d8a8-ef5f-4e0c-93e5-8cdbdefd6bbd"  # From the logs
        
        test_insert = supabase.table("workspace_goals").insert({
            "workspace_id": test_workspace,
            "metric_type": "deliverable_test_custom",  # This should now work
            "target_value": 1.0,
            "unit": "item",
            "description": "Test custom metric type",
            "priority": 1
        }).execute()
        
        if test_insert.data:
            logger.info("✅ Custom metric_type test successful!")
            
            # Clean up test record
            supabase.table("workspace_goals").delete().eq(
                "metric_type", "deliverable_test_custom"
            ).execute()
            
            logger.info("🧹 Test record cleaned up")
        else:
            logger.error(f"❌ Test failed: {test_insert}")
        
    except Exception as e:
        logger.error(f"❌ Failed to fix constraint: {e}")
        logger.info("📝 Manual fix needed:")
        logger.info("1. Go to Supabase dashboard")
        logger.info("2. Navigate to Table Editor > workspace_goals")
        logger.info("3. Go to 'Constraints' tab")
        logger.info("4. Remove 'workspace_goals_metric_type_check' constraint")
        logger.info("5. Save changes")

if __name__ == "__main__":
    asyncio.run(fix_database_constraint())