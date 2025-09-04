#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
backend_root = Path(__file__).parent
load_dotenv(backend_root / ".env")

def check_deliverables_schema():
    """Check if dual-format columns exist in deliverables table"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return False
        
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔍 CHECKING: Current deliverables table schema...")
        
        # Query information_schema to get column information
        result = supabase.rpc(
            'execute_sql',
            {
                'query': """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = 'deliverables'
                        AND (column_name LIKE 'display_%' 
                             OR column_name LIKE 'transformation_%'
                             OR column_name LIKE 'content_transformation_%'
                             OR column_name LIKE 'ai_%'
                             OR column_name IN ('readability_score', 'user_friendliness_score'))
                    ORDER BY ordinal_position;
                """
            }
        )
        
        if result.data:
            print("✅ FOUND: Dual-format columns in deliverables table:")
            for row in result.data:
                print(f"   - {row['column_name']} ({row['data_type']}) default: {row.get('column_default', 'NULL')}")
            
            # Check for essential columns
            column_names = [row['column_name'] for row in result.data]
            essential_columns = [
                'display_content',
                'display_format', 
                'transformation_timestamp',
                'content_transformation_status',
                'display_quality_score'
            ]
            
            missing_columns = [col for col in essential_columns if col not in column_names]
            if missing_columns:
                print(f"⚠️  MISSING: Essential columns: {missing_columns}")
                return False
            else:
                print("✅ ALL ESSENTIAL COLUMNS PRESENT")
                return True
                
        else:
            print("❌ NO dual-format columns found in deliverables table")
            return False
            
    except Exception as e:
        print(f"❌ ERROR checking schema: {e}")
        
        # Fallback: Try direct table query
        try:
            print("\n🔄 FALLBACK: Attempting direct table query...")
            result = supabase.table('deliverables').select('*').limit(1).execute()
            
            if result.data and len(result.data) > 0:
                columns = list(result.data[0].keys())
                dual_format_columns = [col for col in columns if 
                    col.startswith('display_') or 
                    col.startswith('transformation_') or
                    col.startswith('content_transformation_') or
                    col.startswith('ai_') or
                    col in ['readability_score', 'user_friendliness_score']
                ]
                
                if dual_format_columns:
                    print(f"✅ FOUND via fallback: {dual_format_columns}")
                    return True
                else:
                    print("❌ NO dual-format columns found via fallback")
                    return False
            else:
                print("❌ No data in deliverables table to check schema")
                return False
                
        except Exception as fallback_error:
            print(f"❌ FALLBACK ERROR: {fallback_error}")
            return False

def check_sample_deliverables():
    """Check sample deliverables to see transformation status"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        print("\n📊 CHECKING: Sample deliverables transformation status...")
        
        result = supabase.table('deliverables').select(
            'id, title, status, display_content, display_format, content_transformation_status, transformation_timestamp'
        ).order('created_at', desc=True).limit(5).execute()
        
        if result.data:
            print("📋 Recent deliverables:")
            for item in result.data:
                has_display = "✅" if item.get('display_content') else "❌"
                status = item.get('content_transformation_status', 'unknown')
                print(f"   {has_display} {item['title'][:50]}... | Status: {status} | Display: {bool(item.get('display_content'))}")
        else:
            print("❌ No deliverables found")
            
    except Exception as e:
        print(f"❌ ERROR checking sample deliverables: {e}")

if __name__ == "__main__":
    print("🔍 DATABASE SCHEMA VERIFICATION")
    print("=" * 50)
    
    schema_ok = check_deliverables_schema()
    check_sample_deliverables()
    
    print("\n" + "=" * 50)
    if schema_ok:
        print("✅ RESULT: Dual-format schema appears to be in place")
        print("💡 TIP: Run migration 022 if you need to refresh/update the schema")
    else:
        print("❌ RESULT: Dual-format schema NOT found - migration 022 needed")
        print("🚀 ACTION: Execute migration 022 in Supabase SQL Editor")
        
    print("\nMigration file: /backend/migrations/022_add_display_content_to_deliverables.sql")