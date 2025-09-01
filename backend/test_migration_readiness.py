#!/usr/bin/env python3
"""
Test Migration 013 Readiness
Validates current state and simulates post-migration behavior
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

def test_current_deliverables():
    """Test current deliverables in the workspace"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
        
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Get all deliverables
        result = supabase.table('deliverables').select('*').execute()
        
        if not result.data:
            print("⚠️ No deliverables found")
            return False
        
        print(f"📊 Found {len(result.data)} deliverables")
        
        # Check each deliverable
        dual_format_fields = [
            'display_content', 'display_format', 'display_summary', 
            'display_metadata', 'auto_display_generated', 'display_content_updated_at',
            'content_transformation_status', 'content_transformation_error',
            'transformation_timestamp', 'transformation_method',
            'display_quality_score', 'user_friendliness_score', 
            'readability_score', 'ai_confidence'
        ]
        
        deliverable_analysis = []
        
        for deliverable in result.data:
            analysis = {
                'id': deliverable.get('id'),
                'title': deliverable.get('title'),
                'content_type': type(deliverable.get('content', {})).__name__,
                'has_content': bool(deliverable.get('content')),
                'content_size': len(str(deliverable.get('content', ''))),
                'missing_fields': [],
                'existing_fields': []
            }
            
            for field in dual_format_fields:
                if field in deliverable and deliverable.get(field) is not None:
                    analysis['existing_fields'].append(field)
                else:
                    analysis['missing_fields'].append(field)
            
            deliverable_analysis.append(analysis)
        
        # Print analysis
        print("\n" + "="*80)
        print("📋 DELIVERABLE ANALYSIS")
        print("="*80)
        
        for i, analysis in enumerate(deliverable_analysis, 1):
            print(f"\n🔍 Deliverable {i}: {analysis['title']}")
            print(f"   ID: {analysis['id']}")
            print(f"   Content: {analysis['content_type']} ({analysis['content_size']} chars)")
            print(f"   Has Content: {'✅' if analysis['has_content'] else '❌'}")
            print(f"   Dual-Format Fields: {len(analysis['existing_fields'])}/{len(dual_format_fields)}")
            
            if analysis['missing_fields']:
                print(f"   Missing: {len(analysis['missing_fields'])} fields")
                # Show first few missing fields
                missing_preview = analysis['missing_fields'][:3]
                if len(analysis['missing_fields']) > 3:
                    missing_preview.append(f"... and {len(analysis['missing_fields'])-3} more")
                print(f"   ❌ {', '.join(missing_preview)}")
        
        # Summary
        total_missing = sum(len(a['missing_fields']) for a in deliverable_analysis)
        total_possible = len(deliverable_analysis) * len(dual_format_fields)
        
        print(f"\n📊 SUMMARY")
        print(f"   Total Deliverables: {len(deliverable_analysis)}")
        print(f"   Missing Fields: {total_missing}/{total_possible}")
        print(f"   Migration Needed: {'✅ YES' if total_missing > 0 else '❌ NO'}")
        
        # Show sample content
        print(f"\n🔍 SAMPLE CONTENT (First deliverable)")
        if deliverable_analysis:
            sample = result.data[0]
            content = sample.get('content', {})
            if isinstance(content, dict) and content:
                print("   Raw JSON structure:")
                for key, value in list(content.items())[:3]:  # Show first 3 keys
                    value_preview = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
                    print(f"     {key}: {value_preview}")
                if len(content) > 3:
                    print(f"     ... and {len(content)-3} more keys")
            else:
                print(f"   Content: {content}")
        
        return total_missing == 0
        
    except Exception as e:
        print(f"❌ Error testing deliverables: {e}")
        return False

def simulate_post_migration():
    """Simulate what will happen after migration is applied"""
    
    print("\n" + "="*80)
    print("🔮 POST-MIGRATION SIMULATION")
    print("="*80)
    
    print("\n✅ Expected Changes After Migration 013:")
    print("1. All 14 dual-format columns added to deliverables table")
    print("2. Existing deliverables marked with content_transformation_status = 'pending'")
    print("3. AI Content Display Transformer automatically processes pending deliverables")
    print("4. Raw JSON content transformed to professional HTML/Markdown")
    print("5. Frontend displays enhanced format instead of 'Raw JSON Content'")
    
    print("\n🔄 Automatic Transformation Process:")
    print("1. Backend detects deliverables with status = 'pending'")
    print("2. AI analyzes content structure (email, report, contact list, etc.)")
    print("3. Generates professional HTML with appropriate styling")
    print("4. Updates display_content, display_format, and quality scores")
    print("5. WebSocket broadcasts update to frontend")
    
    print("\n🎨 Frontend Display Enhancement:")
    print("Before: Shows 'Raw JSON Content' with technical data")
    print("After:  Shows formatted business documents (emails, reports, tables)")
    
    print("\n📊 Quality Metrics Tracking:")
    print("- display_quality_score: AI confidence in transformation")
    print("- user_friendliness_score: User experience rating")
    print("- readability_score: Content readability assessment")
    print("- ai_confidence: Overall transformation confidence")

def main():
    print("🧪 Testing Migration 013 Readiness")
    print("="*50)
    
    # Test current state
    migration_not_needed = test_current_deliverables()
    
    if migration_not_needed:
        print("\n🎉 Migration 013 already applied!")
        print("All dual-format fields are present.")
    else:
        print("\n🔧 Migration 013 required")
        print("Execute the SQL migration in Supabase Dashboard SQL Editor.")
        
        # Show simulation
        simulate_post_migration()
        
        print("\n📋 NEXT STEPS:")
        print("1. Copy SQL from: temp_migration_013.sql")
        print("2. Execute in Supabase Dashboard > SQL Editor")
        print("3. Run: python3 apply_migration_013.py (to validate)")
        print("4. Observe AI Content Display Transformer in action")

if __name__ == "__main__":
    main()