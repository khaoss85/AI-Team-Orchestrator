#!/usr/bin/env python3
"""
SQL Syntax Validation Script for SUPABASE_MANUAL_SQL_COMMANDS_FIXED.sql
Validates column-value alignment and data types before execution
"""

import re
import json

def validate_insert_statements():
    """Validate INSERT statements for column-value alignment"""
    
    with open('SUPABASE_MANUAL_SQL_COMMANDS_FIXED.sql', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 VALIDATING SQL SYNTAX...")
    print("=" * 50)
    
    # Extract INSERT statements
    insert_pattern = r'INSERT INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*(.*?)(?=;|\s*ON CONFLICT)'
    matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
    
    validation_results = []
    
    for i, (table_name, columns_str, values_str) in enumerate(matches, 1):
        print(f"\n📋 INSERT Statement #{i} - Table: {table_name}")
        print("-" * 40)
        
        # Parse columns
        columns = [col.strip() for col in columns_str.split(',') if col.strip()]
        column_count = len(columns)
        
        print(f"✅ Columns ({column_count}): {', '.join(columns[:5])}{'...' if column_count > 5 else ''}")
        
        # Parse VALUES sections (could be multiple)
        values_sections = re.findall(r'\((.*?)\)', values_str, re.DOTALL)
        
        print(f"📊 VALUES sections found: {len(values_sections)}")
        
        for j, values_section in enumerate(values_sections, 1):
            # Count values (rough approximation)
            values = re.split(r',(?![^\'\"]*[\'\"]\s*,)', values_section)
            value_count = len([v.strip() for v in values if v.strip()])
            
            print(f"   VALUES #{j}: {value_count} values")
            
            # Check alignment
            if column_count == value_count:
                print(f"   ✅ Column-Value alignment: OK ({column_count}={value_count})")
                validation_results.append(True)
            else:
                print(f"   ❌ MISMATCH: {column_count} columns ≠ {value_count} values")
                validation_results.append(False)
                
                # Show first few values for debugging
                first_values = [v.strip()[:30] + '...' if len(v.strip()) > 30 else v.strip() 
                               for v in values[:3]]
                print(f"   🔍 First values: {first_values}")
    
    # Check for boolean field issues
    print(f"\n🔍 CHECKING FOR BOOLEAN FIELD ISSUES...")
    print("-" * 40)
    
    boolean_issues = []
    if 'is_user_created' in content:
        # Look for boolean fields with non-boolean values
        boolean_pattern = r"'(\w+)',\s*--.*(?:user_created|boolean)"
        boolean_matches = re.findall(boolean_pattern, content, re.IGNORECASE)
        
        for match in boolean_matches:
            if match not in ['TRUE', 'FALSE', 'true', 'false']:
                boolean_issues.append(match)
                print(f"   ❌ Potential boolean issue: '{match}' should be TRUE/FALSE")
    
    if not boolean_issues:
        print("   ✅ No boolean field issues detected")
    
    # Final validation summary
    print(f"\n📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    total_statements = len(validation_results)
    successful_validations = sum(validation_results)
    
    print(f"Total INSERT statements: {total_statements}")
    print(f"Valid alignments: {successful_validations}")
    print(f"Invalid alignments: {total_statements - successful_validations}")
    print(f"Boolean issues: {len(boolean_issues)}")
    
    overall_status = successful_validations == total_statements and len(boolean_issues) == 0
    
    if overall_status:
        print("\n🎉 VALIDATION PASSED - SQL file ready for execution!")
        return True
    else:
        print("\n❌ VALIDATION FAILED - Fix issues before executing SQL")
        return False

if __name__ == "__main__":
    validate_insert_statements()