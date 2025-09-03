#!/usr/bin/env python3
"""
Apply Specialist Assistants Migration
Creates the specialist_assistants table for shared document access
"""

import asyncio
import os
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from database import get_supabase_client

async def apply_specialist_migration():
    """Apply the specialist assistants migration"""
    
    print("=" * 80)
    print("📋 APPLYING SPECIALIST ASSISTANTS MIGRATION")
    print("=" * 80)
    
    try:
        supabase = get_supabase_client()
        
        # Read and execute the migration SQL
        migration_sql = """
-- Table for mapping specialist agents to their OpenAI assistants
CREATE TABLE IF NOT EXISTS specialist_assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    assistant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    document_access_enabled BOOLEAN DEFAULT true,
    last_document_sync TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one assistant per agent per workspace
    UNIQUE(workspace_id, agent_id)
);"""
        
        print("📋 Creating specialist_assistants table...")
        
        # Execute the raw SQL via rpc call (Supabase SQL runner)
        result = supabase.rpc('run_sql', {'sql': migration_sql}).execute()
        
        if result:
            print("✅ Migration executed successfully")
        else:
            print("❌ Migration execution failed")
            return False
            
        # Verify table creation
        print("\n🔍 Verifying table creation...")
        
        # Try to select from the new table (should be empty but accessible)
        verify_result = supabase.table("specialist_assistants").select("id").limit(1).execute()
        
        print("✅ Table verification successful")
        print("✅ specialist_assistants table is ready for use")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        
        # Try alternative approach - create via direct SQL if possible
        print("\n🔧 Trying alternative table creation...")
        try:
            # Manual table creation via Python/SQL
            create_table_sql = """
            INSERT INTO information_schema.tables (table_name) VALUES ('specialist_assistants')
            ON CONFLICT DO NOTHING;
            """
            
            # Just verify we can access the database
            workspaces = supabase.table("workspaces").select("id").limit(1).execute()
            print("✅ Database connection confirmed")
            print("⚠️ Manual table creation may be required via Supabase dashboard")
            
            return False
            
        except Exception as e2:
            print(f"❌ Alternative approach failed: {e2}")
            return False

if __name__ == "__main__":
    asyncio.run(apply_specialist_migration())