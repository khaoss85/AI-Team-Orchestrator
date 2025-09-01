#!/usr/bin/env python3
"""
Migration 013 Application Script
Purpose: Add AI-Driven Dual-Format Display Fields to deliverables table
Date: 2025-08-31
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

def apply_migration_013():
    """Apply Migration 013 to add dual-format display fields to deliverables table"""
    
    # Since Supabase Python client doesn't support ALTER TABLE directly,
    # we'll use the psql command line tool through subprocess
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        return False
    
    # Extract database connection details from Supabase URL
    # Format: https://xyz.supabase.co -> xyz.db.supabase.co:5432
    if "supabase.co" in supabase_url:
        project_ref = supabase_url.split("//")[1].split(".")[0]
        db_host = f"{project_ref}.db.supabase.co"
        db_port = "5432"
        db_name = "postgres"
    else:
        logger.error("❌ Unexpected Supabase URL format")
        return False
    
    # Read the migration SQL file
    migration_file = backend_dir / "migrations" / "013_add_dual_format_to_deliverables.sql"
    
    if not migration_file.exists():
        logger.error(f"❌ Migration file not found: {migration_file}")
        return False
    
    logger.info("📄 Migration SQL loaded from file")
    logger.info("🔧 Using alternative approach: Direct column additions via Supabase client")
    
    # Initialize Supabase client for validation
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("✅ Supabase client initialized")
    
    # Since we can't execute DDL directly, we'll document the required SQL
    # and provide instructions for manual execution
    
    migration_sql = """
-- Migration 013: Add AI-Driven Dual-Format Display Fields to deliverables table

-- 1. Add display content fields
ALTER TABLE deliverables 
ADD COLUMN IF NOT EXISTS display_content TEXT,
ADD COLUMN IF NOT EXISTS display_format VARCHAR(20) DEFAULT 'html',
ADD COLUMN IF NOT EXISTS display_summary TEXT,
ADD COLUMN IF NOT EXISTS display_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS auto_display_generated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS display_content_updated_at TIMESTAMP;

-- 2. Add content transformation tracking fields  
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS content_transformation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS content_transformation_error TEXT,
ADD COLUMN IF NOT EXISTS transformation_timestamp TIMESTAMP,
ADD COLUMN IF NOT EXISTS transformation_method VARCHAR(20) DEFAULT 'ai';

-- 3. Add display quality metrics
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS display_quality_score FLOAT DEFAULT 0.0 CHECK (display_quality_score >= 0.0 AND display_quality_score <= 1.0),
ADD COLUMN IF NOT EXISTS user_friendliness_score FLOAT DEFAULT 0.0 CHECK (user_friendliness_score >= 0.0 AND user_friendliness_score <= 1.0),
ADD COLUMN IF NOT EXISTS readability_score FLOAT DEFAULT 0.0 CHECK (readability_score >= 0.0 AND readability_score <= 1.0);

-- 4. Add AI confidence field
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT DEFAULT 0.0 CHECK (ai_confidence >= 0.0 AND ai_confidence <= 1.0);

-- 5. Create performance indexes
CREATE INDEX IF NOT EXISTS idx_deliverables_display_format ON deliverables(display_format);
CREATE INDEX IF NOT EXISTS idx_deliverables_transformation_status ON deliverables(content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_quality ON deliverables(display_quality_score);
CREATE INDEX IF NOT EXISTS idx_deliverables_auto_generated ON deliverables(auto_display_generated);
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_status ON deliverables(workspace_id, content_transformation_status);

-- 6. Update existing deliverables
UPDATE deliverables 
SET content_transformation_status = 'pending',
    transformation_timestamp = NOW(),
    updated_at = NOW()
WHERE content_transformation_status IS NULL;
"""

    # Write SQL to a temporary file for execution
    temp_sql_file = backend_dir / "temp_migration_013.sql"
    
    with open(temp_sql_file, 'w') as f:
        f.write(migration_sql)
    
    logger.info(f"📝 Migration SQL written to: {temp_sql_file}")
    
    print("\n" + "="*80)
    print("🚨 MANUAL MIGRATION REQUIRED")
    print("="*80)
    print("\nThe Supabase Python client doesn't support DDL operations directly.")
    print("Please execute the migration using one of these methods:")
    print("\n1. 🌐 Via Supabase Dashboard SQL Editor:")
    print("   - Go to your Supabase Dashboard")
    print("   - Navigate to SQL Editor")
    print("   - Copy and paste the SQL from the file below:")
    print(f"   - File: {temp_sql_file}")
    print("\n2. 📱 Via psql command line (if you have database password):")
    print("   - Use the psql connection string from Supabase Dashboard")
    print(f"   - Run: psql 'your-connection-string' -f {temp_sql_file}")
    print("\n3. 🔧 Alternative: Use Supabase REST API or another tool")
    print("\n" + "="*80)
    
    # For now, return False to indicate manual action needed
    return False

def validate_migration():
    """Validate that the migration was applied successfully"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing environment variables")
        return False
        
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Check if the new columns exist by querying a sample record
        result = supabase.table('deliverables').select('*').limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            
            # Check for dual-format fields
            dual_format_fields = [
                'display_content', 'display_format', 'display_summary', 
                'display_metadata', 'auto_display_generated', 'display_content_updated_at',
                'content_transformation_status', 'content_transformation_error',
                'transformation_timestamp', 'transformation_method',
                'display_quality_score', 'user_friendliness_score', 
                'readability_score', 'ai_confidence'
            ]
            
            existing_fields = [field for field in dual_format_fields if field in sample_record]
            missing_fields = [field for field in dual_format_fields if field not in sample_record]
            
            logger.info(f"✅ Existing dual-format fields: {len(existing_fields)}/{len(dual_format_fields)}")
            
            if len(missing_fields) == 0:
                logger.info("🎉 Migration 013 validation successful - all fields present!")
                return True
            else:
                logger.warning(f"⚠️ Migration incomplete - missing fields: {missing_fields}")
                return False
        else:
            logger.warning("⚠️ No deliverables found for validation")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration validation failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Migration 013 Application...")
    
    # First check current status
    if validate_migration():
        logger.info("✅ Migration 013 already applied successfully!")
        sys.exit(0)
    
    # Apply migration (will show manual instructions)
    apply_migration_013()
    
    logger.info("\n📋 Next Steps:")
    logger.info("1. Execute the SQL migration manually via Supabase Dashboard")
    logger.info("2. Run this script again to validate the migration")
    logger.info("3. Once validated, the AI Content Display Transformer will work automatically")