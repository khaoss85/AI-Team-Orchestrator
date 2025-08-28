#!/usr/bin/env python3
"""
Script to add unique constraint to deliverables table using direct PostgreSQL connection
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
import logging
from urllib.parse import urlparse

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection_params():
    """Extract PostgreSQL connection parameters from Supabase URL"""
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL not found in environment variables")
    
    # Parse the Supabase URL to get the database connection details
    # Supabase URLs follow the pattern: https://{project_ref}.supabase.co
    parsed = urlparse(supabase_url)
    project_ref = parsed.hostname.split('.')[0]
    
    # Construct PostgreSQL connection string
    # Supabase uses the following pattern for direct PostgreSQL connections
    host = f"aws-0-eu-west-1.pooler.supabase.com"
    port = 6543
    database = "postgres"
    user = f"postgres.{project_ref}"
    
    # We need the database password, which should be in env vars
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not password:
        # Try alternative env var names
        password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise ValueError("Database password not found. Set SUPABASE_DB_PASSWORD environment variable")
    
    return {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }

async def add_constraint_directly():
    """Add constraint using direct PostgreSQL connection"""
    
    try:
        # Get connection parameters
        conn_params = get_postgres_connection_params()
        logger.info(f"Connecting to PostgreSQL: {conn_params['host']}:{conn_params['port']}")
        
        # Connect to the database
        conn = await asyncpg.connect(
            host=conn_params['host'],
            port=conn_params['port'],
            database=conn_params['database'],
            user=conn_params['user'],
            password=conn_params['password']
        )
        
        logger.info("✅ Connected to PostgreSQL successfully")
        
        # SQL to add the constraint
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
        
        # Execute the SQL
        logger.info("Executing constraint addition SQL...")
        await conn.execute(constraint_sql)
        logger.info("✅ SQL executed successfully")
        
        # Verify the constraint was created
        verify_sql = """
        SELECT COUNT(*) as constraint_exists 
        FROM information_schema.table_constraints 
        WHERE table_name = 'deliverables' 
        AND constraint_name = 'unique_workspace_goal_title';
        """
        
        result = await conn.fetchval(verify_sql)
        
        if result and result > 0:
            logger.info("✅ Constraint verification successful - constraint exists")
        else:
            logger.warning("⚠️ Constraint verification failed - constraint may not exist")
        
        # Close connection
        await conn.close()
        logger.info("Database connection closed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding constraint directly: {e}")
        return False

async def test_constraint_via_supabase():
    """Test the constraint using Supabase client after direct addition"""
    
    # Import here to avoid circular imports
    from database import get_supabase_service_client
    
    supabase = get_supabase_service_client()
    
    logger.info("Testing constraint via Supabase client...")
    
    try:
        # Get an existing deliverable
        result = supabase.table('deliverables').select('workspace_id, goal_id, title').limit(1).execute()
        
        if not result.data:
            logger.warning("No existing deliverables to test with")
            return False
        
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
            if 'unique' in error_msg.lower() or 'duplicate' in error_msg.lower() or 'constraint' in error_msg.lower():
                logger.info("✅ Constraint is working - duplicate creation failed as expected")
                return True
            else:
                logger.error(f"Unexpected error during constraint test: {constraint_error}")
                return False
                
    except Exception as e:
        logger.error(f"Error testing constraint: {e}")
        return False

async def main():
    """Main execution function"""
    logger.info("🔒 Adding unique constraint to deliverables table (direct connection)...")
    
    try:
        # Add constraint directly
        success = await add_constraint_directly()
        
        if success:
            logger.info("✅ Constraint addition completed")
            
            # Test the constraint
            logger.info("Testing constraint effectiveness...")
            constraint_works = await test_constraint_via_supabase()
            
            if constraint_works:
                logger.info("🎉 Constraint is working perfectly!")
            else:
                logger.warning("⚠️ Constraint may not be effective. Check database logs.")
        else:
            logger.error("❌ Constraint addition failed")
            
    except Exception as e:
        logger.error(f"Error in direct constraint addition process: {e}")
        
        # Provide fallback instructions
        logger.info("\nFallback: Manual SQL execution required")
        logger.info("Execute this SQL in Supabase dashboard:")
        logger.info("-" * 50)
        logger.info("""
ALTER TABLE deliverables 
ADD CONSTRAINT unique_workspace_goal_title 
UNIQUE (workspace_id, goal_id, title);
        """)
        logger.info("-" * 50)
        
        raise

if __name__ == "__main__":
    asyncio.run(main())