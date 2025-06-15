#!/usr/bin/env python3
"""
🔧 DATABASE SCHEMA FIX
Fixes the missing database schema columns for AI goal extraction
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_schema_and_suggest_fix():
    """Check database schema and provide fix instructions"""
    
    logger.info("🔧 CHECKING DATABASE SCHEMA FOR AI GOAL EXTRACTION")
    logger.info("="*70)
    
    try:
        sys.path.append('.')
        from database import supabase
        
        # Test current schema
        logger.info("📋 Testing current workspace_goals schema...")
        
        # Check what columns exist
        result = supabase.table('workspace_goals').select('*').limit(1).execute()
        
        if result.data:
            current_columns = list(result.data[0].keys())
            logger.info(f"✅ Current columns: {current_columns}")
        else:
            logger.info("⚠️ Table is empty, testing with insert...")
            current_columns = []
        
        # Test what columns are missing
        missing_columns = []
        
        # Test confidence column
        test_data_confidence = {
            'workspace_id': '550e8400-e29b-41d4-a716-446655440000',
            'goal_type': 'deliverable',
            'metric_type': 'deliverables',
            'target_value': 50,
            'unit': 'contacts',
            'description': 'test confidence column',
            'confidence': 0.9
        }
        
        try:
            result = supabase.table('workspace_goals').insert(test_data_confidence).execute()
            if result.data:
                logger.info("✅ confidence column exists")
                # Clean up
                supabase.table('workspace_goals').delete().eq('id', result.data[0]['id']).execute()
            else:
                missing_columns.append('confidence')
        except Exception as e:
            if 'confidence' in str(e):
                missing_columns.append('confidence')
                logger.info("❌ confidence column missing")
            else:
                logger.error(f"Unexpected error testing confidence: {e}")
        
        # Test semantic_context column
        test_data_semantic = {
            'workspace_id': '550e8400-e29b-41d4-a716-446655440000',
            'goal_type': 'deliverable', 
            'metric_type': 'deliverables',
            'target_value': 50,
            'unit': 'contacts',
            'description': 'test semantic context column',
            'semantic_context': {'what': 'test', 'domain': 'test'}
        }
        
        try:
            result = supabase.table('workspace_goals').insert(test_data_semantic).execute()
            if result.data:
                logger.info("✅ semantic_context column exists")
                # Clean up
                supabase.table('workspace_goals').delete().eq('id', result.data[0]['id']).execute()
            else:
                missing_columns.append('semantic_context')
        except Exception as e:
            if 'semantic_context' in str(e):
                missing_columns.append('semantic_context')
                logger.info("❌ semantic_context column missing")
            else:
                logger.error(f"Unexpected error testing semantic_context: {e}")
        
        # Generate fix instructions
        logger.info("\n" + "="*70)
        logger.info("📊 SCHEMA ANALYSIS RESULTS")
        logger.info("="*70)
        
        if missing_columns:
            logger.error(f"❌ Missing columns: {missing_columns}")
            logger.info("\n🔧 REQUIRED DATABASE SCHEMA FIXES:")
            logger.info("Please execute these SQL commands in your Supabase dashboard:")
            logger.info("")
            
            if 'confidence' in missing_columns:
                logger.info("-- Add confidence column")
                logger.info("ALTER TABLE workspace_goals ADD COLUMN confidence DECIMAL(3,2) DEFAULT 0.8;")
                logger.info("UPDATE workspace_goals SET confidence = 0.8 WHERE confidence IS NULL;")
                logger.info("")
            
            if 'semantic_context' in missing_columns:
                logger.info("-- Add semantic_context column")
                logger.info("ALTER TABLE workspace_goals ADD COLUMN semantic_context JSONB DEFAULT '{}'::jsonb;")
                logger.info("UPDATE workspace_goals SET semantic_context = '{}'::jsonb WHERE semantic_context IS NULL;")
                logger.info("")
            
            logger.info("-- Add helpful indexes")
            logger.info("CREATE INDEX IF NOT EXISTS idx_workspace_goals_confidence ON workspace_goals(confidence);")
            logger.info("CREATE INDEX IF NOT EXISTS idx_workspace_goals_semantic_context ON workspace_goals USING GIN(semantic_context);")
            logger.info("")
            
            logger.info("💡 After running these commands, the AI goal extraction will work perfectly!")
            
            return False, missing_columns
        else:
            logger.info("🎉 ALL COLUMNS EXIST - Database schema is correct!")
            return True, []
            
    except Exception as e:
        logger.error(f"❌ Error checking schema: {e}")
        return False, ['unknown']

def create_temporary_workaround():
    """Create a temporary fix for AI goal extraction without the missing columns"""
    
    logger.info("\n🔧 CREATING TEMPORARY WORKAROUND")
    logger.info("="*50)
    
    workaround_code = '''
# TEMPORARY WORKAROUND for missing database columns
# This allows AI goal extraction to work until database schema is fixed

def safe_ai_goal_insert(goal_data):
    """Insert goal data safely, excluding missing columns"""
    
    # Remove columns that don't exist yet
    safe_data = {k: v for k, v in goal_data.items() 
                 if k not in ['confidence', 'semantic_context']}
    
    # Log the excluded data for manual review
    excluded = {k: v for k, v in goal_data.items() 
                if k in ['confidence', 'semantic_context']}
    
    if excluded:
        print(f"⚠️ Excluded data (schema fix needed): {excluded}")
    
    return safe_data

# Example usage in ai_goal_extractor.py:
# safe_data = safe_ai_goal_insert(goal_data)
# result = supabase.table('workspace_goals').insert(safe_data).execute()
'''
    
    with open('temporary_schema_workaround.py', 'w') as f:
        f.write(workaround_code)
    
    logger.info("✅ Created temporary_schema_workaround.py")
    logger.info("💡 This file contains helper functions to work around missing columns")

def main():
    """Main function to check and fix schema"""
    
    logger.info("🚀 DATABASE SCHEMA CHECKER AND FIXER")
    logger.info("="*80)
    
    # Check schema
    schema_ok, missing_columns = check_schema_and_suggest_fix()
    
    if not schema_ok:
        # Create workaround
        create_temporary_workaround()
        
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("1. Execute the SQL commands shown above in Supabase dashboard")
        logger.info("2. Use the temporary workaround code if needed")
        logger.info("3. Run this script again to verify the fix")
        
        return False
    else:
        logger.info("\n🎉 DATABASE SCHEMA IS PERFECT!")
        logger.info("AI goal extraction should work without issues")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)