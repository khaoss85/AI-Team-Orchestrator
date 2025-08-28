#!/usr/bin/env python3
"""
Apply migration 013 to add dual-format fields to deliverables table
"""

import asyncio
from database import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_deliverables_dual_format_migration():
    """Apply the dual-format migration to deliverables table"""
    
    logger.info("🚀 Applying dual-format migration to deliverables table...")
    
    try:
        # Read migration file
        with open('/Users/pelleri/Documents/ai-team-orchestrator/backend/migrations/013_add_dual_format_to_deliverables.sql', 'r') as f:
            migration_sql = f.read()
        
        logger.info("📄 Migration SQL loaded successfully")
        
        # Apply migration using Supabase RPC
        # Since we can't run DDL directly via Python client, we'll show the SQL to copy-paste
        logger.info("📋 PLEASE COPY THE FOLLOWING SQL AND RUN IN SUPABASE SQL EDITOR:")
        logger.info("=" * 80)
        print(migration_sql)
        logger.info("=" * 80)
        
        # Let's check current deliverables to see what we're working with
        logger.info("📊 Checking current deliverables...")
        
        result = supabase.table('deliverables').select('id, title, content, created_at').limit(5).execute()
        
        if result.data:
            logger.info(f"✅ Found {len(result.data)} deliverables in database")
            for deliverable in result.data:
                logger.info(f"  - {deliverable.get('title', 'Untitled')} ({deliverable.get('id', 'no-id')})")
        else:
            logger.info("⚠️ No deliverables found in database")
            
        # Check if the columns already exist
        try:
            test_result = supabase.table('deliverables').select('display_content').limit(1).execute()
            logger.info("✅ display_content column already exists - migration may already be applied")
        except Exception as e:
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                logger.info("❌ display_content column does not exist - migration needed")
            else:
                logger.warning(f"⚠️ Error checking column existence: {e}")
        
        logger.info("🏁 Migration check complete!")
        
    except Exception as e:
        logger.error(f"❌ Migration application failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(apply_deliverables_dual_format_migration())