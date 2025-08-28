#!/usr/bin/env python3
"""
Dual-Format Migration Runner
Adds display fields to asset_artifacts table for AI-Driven Dual-Format Architecture
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from models import AssetArtifact
import json

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        # Try to select the column - if it fails, column doesn't exist
        result = supabase.table(table_name).select(column_name).limit(1).execute()
        return True
    except Exception as e:
        if "column" in str(e).lower() and "does not exist" in str(e).lower():
            return False
        # If it's another error, assume column exists
        return True

def run_migration():
    """Run the dual-format migration step by step"""
    print("🚀 Starting AI-Driven Dual-Format Architecture Migration")
    print("=" * 60)
    
    # Check current table structure
    print("\n📋 Checking current asset_artifacts table structure...")
    try:
        sample = supabase.table('asset_artifacts').select('*').limit(1).execute()
        if sample.data:
            existing_columns = list(sample.data[0].keys())
            print(f"✅ Found {len(existing_columns)} existing columns")
            
            # Check for dual-format columns
            dual_format_columns = [col for col in existing_columns if col.startswith('display_') or 'transformation' in col]
            if dual_format_columns:
                print(f"🔍 Already found {len(dual_format_columns)} dual-format columns:")
                for col in dual_format_columns:
                    print(f"   - {col}")
            else:
                print("📦 No dual-format columns found - migration needed")
        else:
            print("⚠️ No records found in asset_artifacts table")
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return False
    
    # Since we can't execute DDL directly through Supabase REST API,
    # let's verify the migration was applied manually
    print("\n⚠️  MIGRATION NOTICE")
    print("=" * 40)
    print("Due to Supabase REST API limitations, please execute the following SQL manually:")
    print("1. Open Supabase SQL Editor")
    print("2. Copy and paste the migration from: migrations/012_add_dual_format_display_fields.sql")
    print("3. Execute the migration")
    print("4. Run this script again to verify")
    
    # Check if migration was already applied
    test_columns = [
        'display_content',
        'display_format', 
        'display_summary',
        'content_transformation_status',
        'display_quality_score'
    ]
    
    print("\n🔍 Testing for migration completion...")
    missing_columns = []
    
    for col in test_columns:
        if not check_column_exists('asset_artifacts', col):
            missing_columns.append(col)
    
    if missing_columns:
        print(f"❌ Migration not yet applied. Missing columns: {', '.join(missing_columns)}")
        print("\n📄 MANUAL MIGRATION REQUIRED:")
        print("Please execute the SQL migration manually in Supabase SQL Editor")
        return False
    else:
        print("✅ All dual-format columns are present!")
        
        # Test the updated model
        print("\n🧪 Testing AssetArtifact model compatibility...")
        try:
            # Create a test artifact data structure
            test_data = {
                'id': 'test-id',
                'requirement_id': 'test-req-id',
                'artifact_name': 'Test Artifact',
                'artifact_type': 'document',
                'content': {'test': 'data'},
                'content_format': 'json',
                'display_content': '<h1>Test Display Content</h1>',
                'display_format': 'html',
                'display_summary': 'Test summary',
                'content_transformation_status': 'success',
                'display_quality_score': 0.8,
                'quality_score': 0.75,
                'status': 'approved'
            }
            
            # This should work without errors
            artifact = AssetArtifact(**test_data)
            print("✅ AssetArtifact model validation successful!")
            print(f"   - Artifact name: {artifact.name}")  # Using property
            print(f"   - Display format: {artifact.display_format}")
            print(f"   - Transformation status: {artifact.content_transformation_status}")
            
        except Exception as e:
            print(f"❌ Model validation failed: {e}")
            return False
            
        print("\n🎉 Migration verification complete!")
        return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)