#!/usr/bin/env python3
"""
Script to execute migration 011: Add unique constraint to deliverables table
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database import get_supabase_service_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_migration():
    """Execute the migration SQL"""
    
    # Read the migration SQL
    migration_file = backend_path / "migrations" / "011_add_unique_constraint_to_deliverables.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    logger.info("Executing migration 011: Add unique constraint to deliverables")
    
    try:
        # Get service client for admin operations
        supabase_service = get_supabase_service_client()
        
        # Execute the SQL using the RPC function
        # Since Supabase doesn't support direct SQL execution through the client,
        # we need to use the RPC (Remote Procedure Call) functionality
        logger.info("Note: Direct SQL execution through Python client requires RPC function")
        logger.info("Migration SQL content:")
        logger.info(migration_sql)
        
        # For now, we'll provide instructions for manual execution
        logger.info("\n" + "="*60)
        logger.info("MANUAL EXECUTION REQUIRED:")
        logger.info("="*60)
        logger.info("1. Go to your Supabase dashboard")
        logger.info("2. Navigate to SQL Editor")
        logger.info("3. Execute the following SQL:")
        logger.info("\n" + migration_sql)
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error executing migration: {e}")
        return False

async def verify_constraint():
    """Verify that the constraint was added successfully"""
    supabase = get_supabase_service_client()
    
    logger.info("Verifying unique constraint...")
    
    # We can't directly query system tables through Supabase client
    # But we can test the constraint by trying to create duplicates
    
    # Get an existing deliverable to test with
    try:
        result = supabase.table('deliverables').select('workspace_id, goal_id, title').limit(1).execute()
        
        if result.data:
            test_deliverable = result.data[0]
            logger.info("Testing constraint by attempting to create duplicate...")
            
            # Try to create a duplicate (this should fail with constraint)
            duplicate_data = {
                'workspace_id': test_deliverable['workspace_id'],
                'goal_id': test_deliverable['goal_id'],
                'title': test_deliverable['title'],
                'content': 'Test duplicate content',
                'type': 'document',
                'status': 'draft'
            }
            
            try:
                duplicate_result = supabase.table('deliverables').insert(duplicate_data).execute()
                logger.warning("⚠️ Constraint may not be active - duplicate was created")
                
                # Clean up the test duplicate
                if duplicate_result.data:
                    cleanup_result = supabase.table('deliverables').delete().eq(
                        'id', duplicate_result.data[0]['id']
                    ).execute()
                    logger.info("Cleaned up test duplicate")
                
            except Exception as constraint_error:
                logger.info("✅ Constraint is working - duplicate creation failed as expected")
                logger.debug(f"Constraint error: {constraint_error}")
        else:
            logger.warning("No existing deliverables found to test constraint")
            
    except Exception as e:
        logger.error(f"Error verifying constraint: {e}")

async def main():
    """Main execution function"""
    logger.info("🔒 Starting migration 011: Add unique constraint to deliverables")
    
    try:
        # Execute migration
        success = await execute_migration()
        
        if success:
            logger.info("✅ Migration instructions provided")
            
            # Ask user if they want to verify after manual execution
            response = input("\nHave you executed the SQL manually? (yes/no): ").strip().lower()
            if response == 'yes':
                await verify_constraint()
            else:
                logger.info("Skipping verification. Run this script again after executing the SQL.")
        else:
            logger.error("❌ Migration failed")
            
    except Exception as e:
        logger.error(f"Error in migration process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())