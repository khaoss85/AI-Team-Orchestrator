#!/usr/bin/env python3
"""
Schema Discovery for asset_artifacts table

This script tries to determine what fields are accepted by the asset_artifacts table
by testing minimal inserts and progressively adding fields.
"""

import asyncio
import logging
from database import supabase
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_schema():
    """Test asset_artifacts table schema by trying minimal inserts"""
    print("🔍 Testing asset_artifacts table schema...")
    
    # Test 1: Absolute minimum fields
    test_data_minimal = {
        "id": str(uuid4()),
    }
    
    try:
        result = supabase.table('asset_artifacts').insert(test_data_minimal).execute()
        print("✅ Minimal insert works:", result.data)
        # Clean up
        if result.data:
            supabase.table('asset_artifacts').delete().eq('id', result.data[0]['id']).execute()
        return  # If this works, we know the minimum requirements
    except Exception as e:
        print("❌ Minimal insert failed:", e)
    
    # Test 2: Try required fields first, then optional ones
    required_fields = [
        ("artifact_name", "Test Artifact"),
        ("artifact_type", "test"),
    ]
    
    optional_fields = [
        ("content", {"test": "data"}),
        ("quality_score", 0.8),
        ("status", "draft"),
        ("workspace_id", "5975922e-c943-4d99-ad1d-25c01a81da7d"),
        ("requirement_id", str(uuid4())),
        ("task_id", str(uuid4())),
        ("created_at", "2025-08-27T13:00:00.000Z"),
        ("updated_at", "2025-08-27T13:00:00.000Z"),
        ("metadata", {"source": "test"}),
        ("validation_passed", True)
    ]
    
    test_data = {"id": str(uuid4())}
    
    # First add required fields
    print("\n🔧 Testing required fields...")
    for field_name, field_value in required_fields:
        test_data[field_name] = field_value
        try:
            result = supabase.table('asset_artifacts').insert(test_data.copy()).execute()
            print(f"✅ Insert with {field_name} works")
            # Clean up successful insert
            if result.data:
                supabase.table('asset_artifacts').delete().eq('id', result.data[0]['id']).execute()
        except Exception as e:
            print(f"❌ Insert with {field_name} failed: {e}")
            # Don't remove required fields, just note the failure
    
    # Then test optional fields
    print("\n🔧 Testing optional fields...")
    for field_name, field_value in optional_fields:
        test_data[field_name] = field_value
        try:
            result = supabase.table('asset_artifacts').insert(test_data.copy()).execute()
            print(f"✅ Insert with {field_name} works")
            # Clean up successful insert
            if result.data:
                supabase.table('asset_artifacts').delete().eq('id', result.data[0]['id']).execute()
        except Exception as e:
            print(f"❌ Insert with {field_name} failed: {e}")
            # Remove the failing field and continue
            del test_data[field_name]
    
    print(f"\n🎯 Working fields: {list(test_data.keys())}")
    return test_data

if __name__ == "__main__":
    working_schema = asyncio.run(test_schema())
    print(f"\n✅ Final working schema: {working_schema}")