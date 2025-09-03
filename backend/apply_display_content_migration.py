#!/usr/bin/env python3
"""
Apply the display_content migration to add AI-enhanced display fields to asset_artifacts table
"""

import logging
import asyncio
from database import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_migration():
    """Apply migration 012 to add display_content fields"""
    try:
        logger.info("🚀 Applying migration 012: Add AI-Driven Dual-Format Display Fields")
        
        # Read the migration SQL file
        with open('migrations/012_add_dual_format_display_fields.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements (skip BEGIN/COMMIT and SELECT at the end)
        statements = []
        for statement in migration_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.upper().startswith(('BEGIN', 'COMMIT', 'SELECT')):
                statements.append(statement)
        
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
                
            # Get first few words for logging
            statement_preview = ' '.join(statement.split()[:5])
            logger.info(f"  [{i}/{len(statements)}] Executing: {statement_preview}...")
            
            try:
                # Use raw SQL execution through Supabase RPC or direct connection
                # Since Supabase client doesn't support DDL, we'll check if columns exist first
                if 'ALTER TABLE' in statement and 'ADD COLUMN' in statement:
                    # Extract column name
                    import re
                    match = re.search(r'ADD COLUMN IF NOT EXISTS (\w+)', statement)
                    if match:
                        column_name = match.group(1)
                        
                        # Check if column exists by trying to select it
                        try:
                            test_result = supabase.table('asset_artifacts').select(column_name).limit(1).execute()
                            logger.info(f"    ✅ Column {column_name} already exists")
                        except Exception as e:
                            if '42703' in str(e):  # Column doesn't exist
                                logger.warning(f"    ⚠️ Column {column_name} doesn't exist - needs manual creation")
                            else:
                                logger.error(f"    ❌ Error checking column {column_name}: {e}")
                
                elif 'CREATE INDEX' in statement:
                    # Indexes need to be created manually
                    logger.info(f"    ℹ️ Index creation needs to be done manually in Supabase dashboard")
                    
                elif 'COMMENT ON COLUMN' in statement:
                    # Comments are informational
                    logger.info(f"    ℹ️ Comment statement (informational only)")
                    
                elif 'UPDATE asset_artifacts' in statement:
                    # This is the data update statement - we can skip it for now
                    logger.info(f"    ⏭️ Skipping data update statement (will be handled after schema changes)")
                    
            except Exception as e:
                logger.error(f"    ❌ Error executing statement: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("📋 MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info("""
The following columns need to be added manually in Supabase dashboard:

1. Go to: https://supabase.com/dashboard/project/szerliaxjcverzdoisik/editor
2. Navigate to the 'asset_artifacts' table
3. Add the following columns:

REQUIRED COLUMNS:
- display_content (text, nullable)
- display_format (varchar(20), default: 'html')
- display_summary (text, nullable)
- display_metadata (jsonb, default: '{}')
- auto_display_generated (boolean, default: false)
- display_content_updated_at (timestamp, nullable)
- content_transformation_status (varchar(20), default: 'pending')
- content_transformation_error (text, nullable)
- transformation_timestamp (timestamp, nullable)
- transformation_method (varchar(20), default: 'ai')
- display_quality_score (float8, default: 0.0, check: >= 0.0 AND <= 1.0)
- user_friendliness_score (float8, default: 0.0, check: >= 0.0 AND <= 1.0)
- readability_score (float8, default: 0.0, check: >= 0.0 AND <= 1.0)
- ai_confidence (float8, default: 0.0, check: >= 0.0 AND <= 1.0)

After adding these columns manually, run:
  python transform_existing_deliverables.py --check

To verify the columns were added successfully.
""")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(apply_migration())