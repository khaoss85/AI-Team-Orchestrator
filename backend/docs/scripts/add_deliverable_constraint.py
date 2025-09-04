#!/usr/bin/env python3
"""
Script to add unique constraint to deliverables table via Supabase RPC
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

async def add_constraint_via_rpc():
    """Try to add constraint using Supabase RPC"""
    supabase_service = get_supabase_service_client()
    
    # SQL to create the constraint
    constraint_sql = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE table_name = 'deliverables' 
            AND constraint_name = 'unique_workspace_goal_title'
        ) THEN
            ALTER TABLE deliverables 
            ADD CONSTRAINT unique_workspace_goal_title 
            UNIQUE (workspace_id, goal_id, title);
            RAISE NOTICE 'Added unique constraint: unique_workspace_goal_title';
        ELSE
            RAISE NOTICE 'Unique constraint unique_workspace_goal_title already exists';
        END IF;
    END
    $$;
    """
    
    try:
        # Try to execute via RPC (this may not work depending on Supabase setup)
        result = supabase_service.rpc('exec_sql', {'sql': constraint_sql}).execute()
        logger.info("✅ Constraint added via RPC")
        return True
    except Exception as e:
        logger.warning(f"RPC approach failed: {e}")
        return False

async def test_constraint():
    """Test if the constraint is working by trying to create a duplicate"""
    supabase = get_supabase_service_client()
    
    logger.info("Testing constraint...")
    
    try:
        # Get an existing deliverable
        result = supabase.table('deliverables').select('workspace_id, goal_id, title').limit(1).execute()
        
        if not result.data:
            logger.warning("No existing deliverables to test with")
            return
        
        existing = result.data[0]
        logger.info(f"Testing with existing deliverable: {existing['title'][:50]}...")
        
        # Try to create a duplicate
        duplicate_data = {
            'workspace_id': existing['workspace_id'],
            'goal_id': existing['goal_id'],
            'title': existing['title'],
            'content': 'Test duplicate for constraint verification',
            'type': 'document',
            'status': 'draft'
        }
        
        try:
            duplicate_result = supabase.table('deliverables').insert(duplicate_data).execute()
            
            # If we get here, constraint is not working
            logger.warning("⚠️ Constraint is NOT working - duplicate was created")
            
            # Clean up the duplicate
            if duplicate_result.data:
                supabase.table('deliverables').delete().eq('id', duplicate_result.data[0]['id']).execute()
                logger.info("Cleaned up test duplicate")
                
            return False
            
        except Exception as constraint_error:
            error_msg = str(constraint_error)
            if 'unique' in error_msg.lower() or 'duplicate' in error_msg.lower():
                logger.info("✅ Constraint is working - duplicate creation failed as expected")
                return True
            else:
                logger.error(f"Unexpected error during constraint test: {constraint_error}")
                return False
                
    except Exception as e:
        logger.error(f"Error testing constraint: {e}")
        return False

async def manual_execution_instructions():
    """Provide manual execution instructions"""
    logger.info("\n" + "="*70)
    logger.info("MANUAL SQL EXECUTION INSTRUCTIONS")
    logger.info("="*70)
    logger.info("1. Go to your Supabase dashboard")
    logger.info("2. Navigate to the SQL Editor")
    logger.info("3. Execute the following SQL:")
    logger.info("\n" + "-"*50)
    
    sql = """-- Add unique constraint to prevent duplicate deliverables
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE table_name = 'deliverables' 
        AND constraint_name = 'unique_workspace_goal_title'
    ) THEN
        ALTER TABLE deliverables 
        ADD CONSTRAINT unique_workspace_goal_title 
        UNIQUE (workspace_id, goal_id, title);
        RAISE NOTICE 'Added unique constraint: unique_workspace_goal_title';
    ELSE
        RAISE NOTICE 'Unique constraint unique_workspace_goal_title already exists';
    END IF;
END
$$;"""
    
    logger.info(sql)
    logger.info("-"*50)
    logger.info("4. Check for successful execution message")
    logger.info("5. Run this script again to verify the constraint")
    logger.info("="*70)

async def main():
    """Main execution function"""
    logger.info("🔒 Adding unique constraint to deliverables table...")
    
    try:
        # First, test if constraint already exists
        constraint_works = await test_constraint()
        
        if constraint_works:
            logger.info("✅ Constraint is already working!")
            return
        
        # Try RPC approach first
        logger.info("Attempting to add constraint via RPC...")
        rpc_success = await add_constraint_via_rpc()
        
        if rpc_success:
            # Verify it worked
            constraint_works = await test_constraint()
            if constraint_works:
                logger.info("✅ Constraint successfully added via RPC!")
                return
        
        # If RPC failed, provide manual instructions
        logger.info("RPC approach unsuccessful. Providing manual instructions...")
        await manual_execution_instructions()
        
        # Ask if user wants to test after manual execution
        print()  # Add a line break before input
        
        while True:
            try:
                response = input("Have you executed the SQL manually? (yes/no/quit): ").strip().lower()
                break
            except EOFError:
                # Handle case where we're running in non-interactive environment
                logger.info("Non-interactive environment detected. Exiting.")
                return
        
        if response == 'yes':
            constraint_works = await test_constraint()
            if constraint_works:
                logger.info("✅ Constraint verification successful!")
            else:
                logger.warning("⚠️ Constraint verification failed. Please check the SQL execution.")
        elif response == 'quit':
            logger.info("Exiting without verification.")
        else:
            logger.info("Please execute the SQL manually and run this script again for verification.")
            
    except Exception as e:
        logger.error(f"Error in constraint addition process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())