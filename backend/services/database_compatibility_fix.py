"""
🚨 EMERGENCY DATABASE COMPATIBILITY FIX
This module provides compatibility layer for missing database columns
until migration 012 can be properly applied through Supabase dashboard
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseCompatibilityLayer:
    """
    Provides compatibility for missing database columns by:
    1. Removing fields that don't exist in database before INSERT/UPDATE
    2. Adding default values for missing fields after SELECT
    3. Tracking what columns are missing for monitoring
    """
    
    # Known missing columns from migration 012
    MISSING_COLUMNS = {
        'asset_artifacts': [
            'display_content',
            'display_format', 
            'display_summary',
            'display_metadata',
            'auto_display_generated',
            'display_content_updated_at',
            'content_transformation_status',
            'content_transformation_error',
            'transformation_timestamp',
            'transformation_method',
            'display_quality_score',
            'user_friendliness_score',
            'readability_score',
            'ai_confidence'
        ]
    }
    
    # Default values for missing columns
    COLUMN_DEFAULTS = {
        'display_content': None,
        'display_format': 'html',
        'display_summary': None,
        'display_metadata': {},
        'auto_display_generated': False,
        'display_content_updated_at': None,
        'content_transformation_status': 'pending',
        'content_transformation_error': None,
        'transformation_timestamp': None,
        'transformation_method': 'ai',
        'display_quality_score': 0.0,
        'user_friendliness_score': 0.0,
        'readability_score': 0.0,
        'ai_confidence': 0.0
    }
    
    @classmethod
    def prepare_for_insert(cls, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove fields that don't exist in database before INSERT
        """
        if table_name not in cls.MISSING_COLUMNS:
            return data
            
        cleaned_data = data.copy()
        missing_cols = cls.MISSING_COLUMNS.get(table_name, [])
        
        removed_fields = []
        for col in missing_cols:
            if col in cleaned_data:
                del cleaned_data[col]
                removed_fields.append(col)
        
        if removed_fields:
            logger.warning(f"🚨 DATABASE COMPATIBILITY: Removed {len(removed_fields)} missing columns from {table_name} INSERT: {removed_fields}")
        
        return cleaned_data
    
    @classmethod
    def prepare_for_update(cls, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove fields that don't exist in database before UPDATE
        """
        return cls.prepare_for_insert(table_name, data)
    
    @classmethod
    def add_missing_fields_after_select(cls, table_name: str, records: list) -> list:
        """
        Add default values for missing fields after SELECT
        """
        if table_name not in cls.MISSING_COLUMNS:
            return records
            
        missing_cols = cls.MISSING_COLUMNS.get(table_name, [])
        
        for record in records:
            for col in missing_cols:
                if col not in record and col in cls.COLUMN_DEFAULTS:
                    record[col] = cls.COLUMN_DEFAULTS[col]
        
        return records
    
    @classmethod
    def check_column_exists(cls, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists (returns False for known missing columns)
        """
        if table_name in cls.MISSING_COLUMNS:
            return column_name not in cls.MISSING_COLUMNS[table_name]
        return True  # Assume it exists if we don't know about the table
    
    @classmethod
    def get_compatibility_report(cls) -> Dict[str, Any]:
        """
        Get a report of database compatibility issues
        """
        total_missing = sum(len(cols) for cols in cls.MISSING_COLUMNS.values())
        
        return {
            'status': 'DEGRADED',
            'missing_columns_count': total_missing,
            'affected_tables': list(cls.MISSING_COLUMNS.keys()),
            'details': cls.MISSING_COLUMNS,
            'recommendation': 'Apply migration 012_add_dual_format_display_fields.sql through Supabase dashboard',
            'timestamp': datetime.now().isoformat()
        }

# Global instance
db_compatibility = DatabaseCompatibilityLayer()

# Log compatibility status on import
compatibility_report = db_compatibility.get_compatibility_report()
logger.warning(f"""
🚨 DATABASE COMPATIBILITY MODE ACTIVE
=====================================
Missing {compatibility_report['missing_columns_count']} columns in database
Affected tables: {', '.join(compatibility_report['affected_tables'])}
Recommendation: {compatibility_report['recommendation']}
=====================================
""")