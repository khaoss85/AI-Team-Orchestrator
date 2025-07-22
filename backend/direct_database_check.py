# direct_database_check.py
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv(dotenv_path='backend/.env')
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Supabase URL or Key not found. Make sure they are in backend/.env")
        return

    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client created.")

    try:
        # 1. Verify schema of the 'deliverables' table
        # We can't directly get schema via client lib, but we can query all data
        # and infer the schema from the columns present.
        logger.info("Fetching all deliverables to check data integrity and infer schema...")
        response = supabase.table('deliverables').select('*').limit(5).execute()
        
        if response.data:
            logger.info(f"Successfully fetched {len(response.data)} deliverables.")
            logger.info("Sample deliverable record:")
            logger.info(response.data[0])
            
            # Check for common columns
            required_columns = ['id', 'workspace_id', 'created_at', 'title', 'content']
            first_record_keys = response.data[0].keys()
            missing_columns = [col for col in required_columns if col not in first_record_keys]
            
            if not missing_columns:
                logger.info("✅ Basic schema check passed (found required columns).")
            else:
                logger.error(f"❌ Schema check failed. Missing columns: {missing_columns}")

        else:
            logger.warning("No deliverables found to analyze.")

        # 2. Check for a specific workspace if provided
        # You can manually set this workspace_id to the one failing in the test
        test_workspace_id = "10fd5b7a-1b32-488d-805b-724f892c4082" 
        logger.info(f"Fetching deliverables for specific workspace: {test_workspace_id}")
        
        ws_response = supabase.table('deliverables').select('*').eq('workspace_id', test_workspace_id).execute()
        
        if ws_response.data:
            logger.info(f"Found {len(ws_response.data)} deliverables for workspace {test_workspace_id}.")
        else:
            logger.warning(f"No deliverables found for workspace {test_workspace_id}.")
            if ws_response.error:
                logger.error(f"Error fetching for workspace: {ws_response.error}")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
