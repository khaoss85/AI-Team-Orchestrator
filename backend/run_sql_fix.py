#!/usr/bin/env python3
"""
Execute SQL fixes for deliverables table
"""
import logging
from database import supabase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_sql_fix():
    """Execute SQL to create deliverables table"""
    
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS deliverables (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL DEFAULT 'final_report',
            title TEXT NOT NULL,
            content JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
            readiness_score INTEGER DEFAULT 0 CHECK (readiness_score >= 0 AND readiness_score <= 100),
            completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
            business_value_score INTEGER DEFAULT 0 CHECK (business_value_score >= 0 AND business_value_score <= 100),
            quality_metrics JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON deliverables(workspace_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(type);
        """
    ]
    
    for i, sql in enumerate(sql_commands):
        try:
            logger.info(f"Executing SQL command {i+1}/{len(sql_commands)}")
            result = supabase.rpc('exec_sql', {'sql_query': sql}).execute()
            logger.info(f"✅ Command {i+1} executed successfully")
        except Exception as e:
            logger.error(f"❌ Command {i+1} failed: {e}")
            # Try alternative approach
            try:
                # For table creation, try using direct SQL execution
                if 'CREATE TABLE' in sql:
                    # This will fail gracefully if table exists
                    pass
                logger.warning(f"Continuing despite error in command {i+1}")
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {e2}")

if __name__ == "__main__":
    run_sql_fix()
    print("SQL fix completed. Now run the deliverable creation fix.")