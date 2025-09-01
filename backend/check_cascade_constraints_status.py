#!/usr/bin/env python3
"""
🔍 CASCADE Constraints Status Checker
====================================
Diagnostic script to check current state of CASCADE constraints and orphaned records
before and after running migration 014.

Usage:
    python3 check_cascade_constraints_status.py

This script will:
1. Check for orphaned records in memory tables
2. Verify current foreign key constraint status
3. Test constraint behavior (read-only)
4. Provide recommendations for migration
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Database connection configuration
DATABASE_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST', 'localhost'),
    'port': os.getenv('SUPABASE_DB_PORT', 5432),
    'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
    'user': os.getenv('SUPABASE_DB_USER', 'postgres'),
    'password': os.getenv('SUPABASE_DB_PASSWORD', '')
}

async def check_database_connection():
    """Test database connectivity."""
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        await conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def check_orphaned_records():
    """Check for orphaned records in memory tables."""
    print("\n🔍 CHECKING ORPHANED RECORDS")
    print("=" * 50)
    
    conn = await asyncpg.connect(**DATABASE_CONFIG)
    try:
        # Check orphaned memory_context_entries
        orphaned_mce = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM memory_context_entries mce 
            WHERE mce.workspace_id IS NOT NULL 
              AND mce.workspace_id NOT IN (SELECT id FROM workspaces)
        """)
        
        # Check orphaned uma_performance_metrics  
        orphaned_upm = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM uma_performance_metrics upm
            WHERE upm.workspace_id IS NOT NULL 
              AND upm.workspace_id NOT IN (SELECT id FROM workspaces)
        """)
        
        # Get sample orphaned record IDs for investigation
        if orphaned_mce > 0:
            orphaned_mce_samples = await conn.fetch("""
                SELECT mce.workspace_id, COUNT(*) as record_count
                FROM memory_context_entries mce 
                WHERE mce.workspace_id IS NOT NULL 
                  AND mce.workspace_id NOT IN (SELECT id FROM workspaces)
                GROUP BY mce.workspace_id
                LIMIT 5
            """)
        else:
            orphaned_mce_samples = []
            
        if orphaned_upm > 0:
            orphaned_upm_samples = await conn.fetch("""
                SELECT upm.workspace_id, COUNT(*) as record_count
                FROM uma_performance_metrics upm
                WHERE upm.workspace_id IS NOT NULL 
                  AND upm.workspace_id NOT IN (SELECT id FROM workspaces)
                GROUP BY upm.workspace_id  
                LIMIT 5
            """)
        else:
            orphaned_upm_samples = []
        
        print(f"📊 Orphaned memory_context_entries: {orphaned_mce} records")
        if orphaned_mce_samples:
            print("   Sample orphaned workspace_ids:")
            for sample in orphaned_mce_samples:
                print(f"     {sample['workspace_id']}: {sample['record_count']} records")
        
        print(f"📊 Orphaned uma_performance_metrics: {orphaned_upm} records")
        if orphaned_upm_samples:
            print("   Sample orphaned workspace_ids:")
            for sample in orphaned_upm_samples:
                print(f"     {sample['workspace_id']}: {sample['record_count']} records")
                
        return {
            'memory_context_entries_orphaned': orphaned_mce,
            'uma_performance_metrics_orphaned': orphaned_upm,
            'needs_cleanup': orphaned_mce > 0 or orphaned_upm > 0
        }
        
    finally:
        await conn.close()

async def check_foreign_key_constraints():
    """Check current foreign key constraint status."""
    print("\n🔗 CHECKING FOREIGN KEY CONSTRAINTS")
    print("=" * 50)
    
    conn = await asyncpg.connect(**DATABASE_CONFIG)
    try:
        # Check memory_context_entries constraints
        mce_constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'memory_context_entries'
            AND constraint_type = 'FOREIGN KEY'
        """)
        
        # Check uma_performance_metrics constraints
        upm_constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'uma_performance_metrics'
            AND constraint_type = 'FOREIGN KEY'
        """)
        
        # Check for CASCADE behavior in constraint definitions
        mce_cascade_info = await conn.fetch("""
            SELECT 
                tc.constraint_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.table_name = 'memory_context_entries'
            AND tc.constraint_type = 'FOREIGN KEY'
        """)
        
        upm_cascade_info = await conn.fetch("""
            SELECT 
                tc.constraint_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.table_name = 'uma_performance_metrics'
            AND tc.constraint_type = 'FOREIGN KEY'
        """)
        
        print("📋 memory_context_entries foreign key constraints:")
        for constraint in mce_constraints:
            print(f"   {constraint['constraint_name']} ({constraint['constraint_type']})")
            
        print("\n📋 memory_context_entries CASCADE rules:")
        for info in mce_cascade_info:
            print(f"   {info['constraint_name']}: DELETE {info['delete_rule']}, UPDATE {info['update_rule']}")
        
        print("\n📋 uma_performance_metrics foreign key constraints:")
        for constraint in ump_constraints:
            print(f"   {constraint['constraint_name']} ({constraint['constraint_type']})")
            
        print("\n📋 uma_performance_metrics CASCADE rules:")
        for info in upm_cascade_info:
            print(f"   {info['constraint_name']}: DELETE {info['delete_rule']}, UPDATE {info['update_rule']}")
        
        # Determine if CASCADE constraints exist
        has_mce_cascade = any('cascade' in c['constraint_name'].lower() for c in mce_constraints)
        has_upm_cascade = any('cascade' in c['constraint_name'].lower() for c in upm_constraints)
        
        return {
            'memory_context_entries_constraints': len(mce_constraints),
            'uma_performance_metrics_constraints': len(upm_constraints),
            'has_mce_cascade': has_mce_cascade,
            'has_upm_cascade': has_upm_cascade,
            'mce_cascade_info': [dict(r) for r in mce_cascade_info],
            'upm_cascade_info': [dict(r) for r in upm_cascade_info]
        }
        
    finally:
        await conn.close()

async def check_workspace_insights_schema():
    """Check workspace_insights table schema."""
    print("\n📝 CHECKING WORKSPACE_INSIGHTS SCHEMA")
    print("=" * 50)
    
    conn = await asyncpg.connect(**DATABASE_CONFIG)
    try:
        # Get current schema
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'workspace_insights' 
            ORDER BY ordinal_position
        """)
        
        expected_columns = {
            'id', 'workspace_id', 'task_id', 'agent_role', 
            'insight_type', 'content', 'relevance_tags', 
            'confidence_score', 'expires_at', 'created_at', 
            'updated_at', 'metadata'
        }
        
        current_columns = {col['column_name'] for col in columns}
        missing_columns = expected_columns - current_columns
        extra_columns = current_columns - expected_columns
        
        print("📊 Current workspace_insights columns:")
        for col in columns:
            print(f"   {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        if missing_columns:
            print(f"\n⚠️  Missing columns: {', '.join(missing_columns)}")
        else:
            print("\n✅ All expected columns present")
            
        if extra_columns:
            print(f"\n📋 Extra columns: {', '.join(extra_columns)}")
        
        # Check for existing insights in target workspace
        insights_count = await conn.fetchval("""
            SELECT COUNT(*) FROM workspace_insights 
            WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
        """)
        
        print(f"\n📊 Existing insights for target workspace: {insights_count}")
        
        return {
            'current_columns': list(current_columns),
            'missing_columns': list(missing_columns),
            'extra_columns': list(extra_columns),
            'insights_count': insights_count,
            'schema_ready': len(missing_columns) == 0
        }
        
    finally:
        await conn.close()

async def generate_migration_recommendations(orphaned_status, constraint_status, schema_status):
    """Generate recommendations based on current state."""
    print("\n💡 MIGRATION RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = []
    
    if orphaned_status['needs_cleanup']:
        recommendations.append(
            "🧹 CLEANUP REQUIRED: Run orphaned record cleanup before adding CASCADE constraints"
        )
        recommendations.append(
            f"   - {orphaned_status['memory_context_entries_orphaned']} orphaned memory_context_entries"
        )
        recommendations.append(
            f"   - {orphaned_status['uma_performance_metrics_orphaned']} orphaned uma_performance_metrics"
        )
    else:
        recommendations.append("✅ No orphaned records found - safe to add CASCADE constraints")
    
    if not constraint_status['has_mce_cascade']:
        recommendations.append("🔗 ADD CASCADE: memory_context_entries needs CASCADE DELETE constraint")
    else:
        recommendations.append("✅ memory_context_entries already has CASCADE constraint")
        
    if not constraint_status['has_upm_cascade']:
        recommendations.append("🔗 ADD CASCADE: uma_performance_metrics needs CASCADE DELETE constraint")
    else:
        recommendations.append("✅ uma_performance_metrics already has CASCADE constraint")
    
    if not schema_status['schema_ready']:
        recommendations.append("📝 SCHEMA UPDATE: workspace_insights missing required columns")
        for col in schema_status['missing_columns']:
            recommendations.append(f"   - Missing: {col}")
    else:
        recommendations.append("✅ workspace_insights schema is ready")
    
    if schema_status['insights_count'] == 0:
        recommendations.append("💡 GENERATE INSIGHTS: Target workspace has no insights yet")
    else:
        recommendations.append(f"📊 Target workspace has {schema_status['insights_count']} existing insights")
    
    # Overall migration readiness
    if orphaned_status['needs_cleanup']:
        recommendations.append("\n🚨 MIGRATION READINESS: NOT READY - cleanup required first")
    else:
        recommendations.append("\n✅ MIGRATION READINESS: READY to run migration 014")
    
    for rec in recommendations:
        print(rec)
    
    return recommendations

async def main():
    """Main diagnostic function."""
    print("🔍 CASCADE CONSTRAINTS STATUS CHECKER")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target workspace: 1f1bf9cf-3c46-48ed-96f3-ec826742ee02")
    
    # Check database connectivity
    if not await check_database_connection():
        return
    
    try:
        # Run all checks
        orphaned_status = await check_orphaned_records()
        constraint_status = await check_foreign_key_constraints()
        schema_status = await check_workspace_insights_schema()
        
        # Generate recommendations
        recommendations = await generate_migration_recommendations(
            orphaned_status, constraint_status, schema_status
        )
        
        # Create summary report
        report = {
            'timestamp': datetime.now().isoformat(),
            'orphaned_records': orphaned_status,
            'foreign_key_constraints': constraint_status,
            'workspace_insights_schema': schema_status,
            'recommendations': recommendations,
            'migration_ready': not orphaned_status['needs_cleanup']
        }
        
        # Save report to file
        report_file = f"cascade_constraints_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        print("\n🎯 NEXT STEPS:")
        if orphaned_status['needs_cleanup']:
            print("1. Run migration 014 (it includes cleanup + constraint addition)")
            print("2. Verify results with this script again")
        else:
            print("1. Migration 014 is ready to run safely")
            print("2. Monitor logs during migration execution")
        
    except Exception as e:
        print(f"\n❌ ERROR during diagnostic: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())