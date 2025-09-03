#!/usr/bin/env python3
"""
Apply content extraction migration to enable true RAG capabilities
"""
import asyncio
import logging
from database import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_content_extraction_migration():
    """Apply the content extraction migration to workspace_documents table"""
    
    supabase = get_supabase_client()
    
    try:
        logger.info("🔄 Starting content extraction migration...")
        
        # Step 1: Add the new columns
        logger.info("📊 Adding new columns to workspace_documents...")
        
        migration_steps = [
            # Add columns (using individual steps for better error handling)
            {
                "name": "Add extracted_text column",
                "sql": "ALTER TABLE workspace_documents ADD COLUMN IF NOT EXISTS extracted_text TEXT;"
            },
            {
                "name": "Add text_chunks column",
                "sql": "ALTER TABLE workspace_documents ADD COLUMN IF NOT EXISTS text_chunks JSONB;"
            },
            {
                "name": "Add extraction_confidence column", 
                "sql": "ALTER TABLE workspace_documents ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT;"
            },
            {
                "name": "Add extraction_method column",
                "sql": "ALTER TABLE workspace_documents ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50);"
            },
            {
                "name": "Add extraction_timestamp column",
                "sql": "ALTER TABLE workspace_documents ADD COLUMN IF NOT EXISTS extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
            }
        ]
        
        # Execute each step
        for step in migration_steps:
            try:
                logger.info(f"  ⏳ {step['name']}...")
                result = supabase.rpc('execute_sql', {'query': step['sql']}).execute()
                logger.info(f"  ✅ {step['name']} completed")
            except Exception as e:
                logger.warning(f"  ⚠️ {step['name']} failed (may already exist): {e}")
        
        # Step 2: Create indexes (these might fail if they exist, that's ok)
        logger.info("📊 Creating indexes for performance...")
        
        index_steps = [
            "CREATE INDEX IF NOT EXISTS idx_workspace_documents_extracted_text ON workspace_documents USING gin(to_tsvector('english', COALESCE(extracted_text, '')))",
            "CREATE INDEX IF NOT EXISTS idx_workspace_documents_extraction_confidence ON workspace_documents(extraction_confidence)", 
            "CREATE INDEX IF NOT EXISTS idx_workspace_documents_workspace_extracted ON workspace_documents(workspace_id, extraction_confidence) WHERE extracted_text IS NOT NULL"
        ]
        
        for idx_sql in index_steps:
            try:
                logger.info(f"  ⏳ Creating index...")
                result = supabase.rpc('execute_sql', {'query': idx_sql}).execute()
                logger.info(f"  ✅ Index created")
            except Exception as e:
                logger.warning(f"  ⚠️ Index creation failed (may already exist): {e}")
        
        # Step 3: Verify the migration worked
        logger.info("🔍 Verifying migration...")
        
        # Check if the new columns exist by trying to select them
        try:
            result = supabase.table("workspace_documents").select(
                "id, filename, extracted_text, text_chunks, extraction_confidence, extraction_method, extraction_timestamp"
            ).limit(1).execute()
            logger.info("✅ Migration verification successful - all columns accessible")
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
        
        # Step 4: Show current status
        logger.info("📊 Checking current document status...")
        
        try:
            # Count total documents
            total_result = supabase.table("workspace_documents").select("id", count="exact").execute()
            total_docs = total_result.count or 0
            
            # Count documents with extracted content
            extracted_result = supabase.table("workspace_documents").select("id", count="exact").not_.is_("extracted_text", "null").execute()
            extracted_docs = extracted_result.count or 0
            
            logger.info(f"📄 Documents status:")
            logger.info(f"  • Total documents: {total_docs}")
            logger.info(f"  • With extracted content: {extracted_docs}")
            logger.info(f"  • Need content extraction: {total_docs - extracted_docs}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check document status: {e}")
        
        logger.info("🎉 Content extraction migration completed successfully!")
        logger.info("📝 Next steps:")
        logger.info("  1. Re-upload existing PDFs to trigger content extraction")
        logger.info("  2. Test RAG queries with document content")
        logger.info("  3. Upload book.pdf again to see the 15 pillars content")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(apply_content_extraction_migration())
    if success:
        print("\n🎉 SUCCESS: Content extraction migration applied!")
        print("The system now supports true RAG capabilities with PDF content extraction.")
    else:
        print("\n❌ FAILED: Migration could not be applied.")
        print("Check the logs above for details.")