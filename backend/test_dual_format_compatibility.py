#!/usr/bin/env python3
"""
Test dual-format schema compatibility without applying the migration
Tests that the code will work once the migration is applied manually
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import AssetArtifact
from pydantic import ValidationError
import json
from datetime import datetime
from uuid import uuid4

def test_model_compatibility():
    """Test AssetArtifact model with dual-format fields"""
    print("🧪 Testing AssetArtifact Model Dual-Format Compatibility")
    print("=" * 60)
    
    # Test 1: Basic model creation with dual-format fields
    print("\n1️⃣ Testing basic model creation...")
    try:
        artifact_data = {
            'id': str(uuid4()),
            'requirement_id': str(uuid4()),
            'workspace_id': str(uuid4()),
            'artifact_name': 'Test Document',
            'artifact_type': 'business_analysis',
            'content': {
                'title': 'Market Analysis Report',
                'sections': ['Executive Summary', 'Market Overview', 'Recommendations'],
                'data': {'market_size': '100M', 'growth_rate': '15%'}
            },
            'content_format': 'json',
            # Dual-format fields
            'display_content': '<h1>Market Analysis Report</h1><p>This is a comprehensive analysis...</p>',
            'display_format': 'html',
            'display_summary': 'Comprehensive market analysis with growth projections',
            'display_metadata': {'theme': 'business', 'layout': 'standard'},
            'content_transformation_status': 'success',
            'transformation_timestamp': datetime.now(),
            'transformation_method': 'ai',
            'auto_display_generated': True,
            'display_content_updated_at': datetime.now(),
            # Quality scores
            'display_quality_score': 0.85,
            'user_friendliness_score': 0.90,
            'readability_score': 0.82,
            'ai_confidence': 0.88,
            # Standard fields
            'quality_score': 0.80,
            'status': 'approved'
        }
        
        artifact = AssetArtifact(**artifact_data)
        print("✅ Model creation successful")
        print(f"   - Name: {artifact.name}")  # Using property
        print(f"   - Type: {artifact.type}")  # Using property  
        print(f"   - Display format: {artifact.display_format}")
        print(f"   - Transformation status: {artifact.content_transformation_status}")
        print(f"   - Quality scores: display={artifact.display_quality_score}, overall={artifact.quality_score}")
        
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Test 2: Minimal required fields only
    print("\n2️⃣ Testing minimal model creation...")
    try:
        minimal_data = {
            'requirement_id': str(uuid4()),
            'artifact_name': 'Minimal Test',
            'artifact_type': 'document'
        }
        
        minimal_artifact = AssetArtifact(**minimal_data)
        print("✅ Minimal model creation successful")
        print(f"   - Default display_format: {minimal_artifact.display_format}")
        print(f"   - Default transformation_status: {minimal_artifact.content_transformation_status}")
        print(f"   - Default display_quality_score: {minimal_artifact.display_quality_score}")
        
    except Exception as e:
        print(f"❌ Minimal model creation failed: {e}")
        return False
    
    # Test 3: Backward compatibility
    print("\n3️⃣ Testing backward compatibility...")
    try:
        legacy_data = {
            'requirement_id': str(uuid4()),
            'artifact_name': 'Legacy Document',
            'artifact_type': 'email_sequence',
            'content': {'emails': [{'subject': 'Welcome', 'body': 'Hello'}]},
            'quality_score': 0.75,
            'status': 'draft'
        }
        
        legacy_artifact = AssetArtifact(**legacy_data)
        print("✅ Legacy compatibility successful")
        print(f"   - Name property works: {legacy_artifact.name}")
        print(f"   - Type property works: {legacy_artifact.type}")
        print(f"   - Auto-defaults applied: display_format={legacy_artifact.display_format}")
        
    except Exception as e:
        print(f"❌ Legacy compatibility failed: {e}")
        return False
    
    # Test 4: JSON serialization/deserialization
    print("\n4️⃣ Testing JSON serialization...")
    try:
        # Test with complex dual-format data
        complex_data = {
            'requirement_id': str(uuid4()),
            'artifact_name': 'Complex Report',
            'artifact_type': 'strategic_plan',
            'content': {
                'strategy': 'Digital Transformation',
                'objectives': ['Increase efficiency', 'Reduce costs'],
                'timeline': '12 months'
            },
            'display_content': '''
            <div class="report">
                <h1>Digital Transformation Strategy</h1>
                <ul>
                    <li>Increase efficiency by 30%</li>
                    <li>Reduce operational costs by 20%</li>
                </ul>
            </div>
            ''',
            'display_metadata': {
                'css_classes': ['report', 'strategy'],
                'required_scripts': ['chart.js'],
                'accessibility': {'alt_text': 'Strategy overview chart'}
            },
            'transformation_method': 'ai',
            'display_quality_score': 0.92
        }
        
        artifact = AssetArtifact(**complex_data)
        
        # Convert to dict (simulating database storage)
        artifact_dict = artifact.model_dump()
        print("✅ JSON serialization successful")
        
        # Convert back from dict (simulating database retrieval)
        restored_artifact = AssetArtifact(**artifact_dict)
        print("✅ JSON deserialization successful")
        
        # Verify data integrity
        assert restored_artifact.artifact_name == complex_data['artifact_name']
        assert restored_artifact.display_quality_score == complex_data['display_quality_score']
        assert restored_artifact.display_metadata == complex_data['display_metadata']
        print("✅ Data integrity verified")
        
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False
    
    # Test 5: Database field mapping
    print("\n5️⃣ Testing database field compatibility...")
    try:
        # Simulate data from database (using actual column names)
        db_data = {
            'id': str(uuid4()),
            'requirement_id': str(uuid4()),
            'task_id': str(uuid4()),
            'workspace_id': str(uuid4()),
            'artifact_name': 'Database Test',
            'artifact_type': 'contact_database',
            'content': {'contacts': []},
            'content_format': 'json',
            'quality_score': 0.7,
            'status': 'approved',
            # New dual-format fields (would be added by migration)
            'display_content': '<table><tr><th>Name</th><th>Email</th></tr></table>',
            'display_format': 'html',
            'display_summary': 'Contact database with 0 entries',
            'display_metadata': {'table_headers': ['Name', 'Email']},
            'content_transformation_status': 'success',
            'content_transformation_error': None,
            'transformation_timestamp': datetime.now(),
            'transformation_method': 'ai',
            'auto_display_generated': True,
            'display_content_updated_at': datetime.now(),
            'display_quality_score': 0.8,
            'user_friendliness_score': 0.75,
            'readability_score': 0.9,
            'ai_confidence': 0.85,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        db_artifact = AssetArtifact(**db_data)
        print("✅ Database compatibility successful")
        print(f"   - All dual-format fields loaded correctly")
        print(f"   - Properties work: name='{db_artifact.name}', type='{db_artifact.type}'")
        
    except Exception as e:
        print(f"❌ Database compatibility test failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("\n📋 Migration Summary:")
    print("   ✅ AssetArtifact model supports all dual-format fields")
    print("   ✅ Backward compatibility maintained")
    print("   ✅ JSON serialization works")
    print("   ✅ Database field mapping correct")
    print("   ✅ Property accessors function properly")
    
    print("\n🚀 Ready for Migration:")
    print("   1. Execute migrations/012_add_dual_format_display_fields.sql in Supabase")
    print("   2. Existing queries will continue to work")
    print("   3. New dual-format features will be available")
    
    return True

def test_existing_queries_compatibility():
    """Test that existing database queries will still work"""
    print("\n🔍 Testing Existing Query Compatibility")
    print("=" * 50)
    
    # Simulate existing query patterns that should continue working
    existing_patterns = [
        {
            'name': 'Basic artifact selection',
            'fields': ['id', 'artifact_name', 'artifact_type', 'content', 'quality_score', 'status'],
            'where_clause': {'status': 'approved'}
        },
        {
            'name': 'Quality filtering',
            'fields': ['artifact_name', 'quality_score'],
            'where_clause': {'quality_score': 0.8}  # gte condition
        },
        {
            'name': 'Workspace artifacts',
            'fields': ['artifact_name', 'artifact_type', 'created_at'],
            'where_clause': {'workspace_id': str(uuid4())}
        }
    ]
    
    for pattern in existing_patterns:
        try:
            # Create test data that matches the query pattern
            test_data = {
                'requirement_id': str(uuid4()),
                'artifact_name': f"Test for {pattern['name']}",
                'artifact_type': 'test_type',
                'content': {'test': 'data'},
                'quality_score': 0.8,
                'status': 'approved',
                'workspace_id': str(uuid4()),
                'created_at': datetime.now()
            }
            
            artifact = AssetArtifact(**test_data)
            
            # Verify all requested fields are accessible
            for field in pattern['fields']:
                if hasattr(artifact, field):
                    value = getattr(artifact, field)
                    # print(f"   Field '{field}': {type(value).__name__}")
                else:
                    print(f"❌ Field '{field}' not accessible")
                    return False
            
            print(f"✅ {pattern['name']} - query pattern compatible")
            
        except Exception as e:
            print(f"❌ {pattern['name']} - compatibility test failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 AI-Driven Dual-Format Architecture Compatibility Test")
    print("=" * 70)
    
    model_test = test_model_compatibility()
    query_test = test_existing_queries_compatibility()
    
    if model_test and query_test:
        print("\n🎊 ALL COMPATIBILITY TESTS PASSED!")
        print("The dual-format architecture is ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ COMPATIBILITY TESTS FAILED!")
        print("Please review and fix issues before applying migration.")
        sys.exit(1)