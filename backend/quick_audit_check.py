#!/usr/bin/env python3
"""
Quick Audit Validation Script
Checks for specific issues identified in the comprehensive audit
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

def check_trace_id_implementation():
    """Check if any route implements X-Trace-ID"""
    routes_path = Path("routes")
    trace_patterns = ["X-Trace-ID", "x-trace-id", "trace_id", "traceId"]
    
    results = {
        "total_routes": 0,
        "routes_with_trace": 0,
        "routes_without_trace": []
    }
    
    for route_file in routes_path.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        results["total_routes"] += 1
        content = route_file.read_text()
        
        has_trace = any(pattern in content for pattern in trace_patterns)
        if has_trace:
            results["routes_with_trace"] += 1
        else:
            results["routes_without_trace"].append(str(route_file))
    
    return results

def check_duplicate_tests():
    """Count e2e test variations"""
    test_patterns = [
        "*e2e*.py",
        "comprehensive*.py",
        "*test*.py"
    ]
    
    test_files = defaultdict(int)
    for pattern in test_patterns:
        for test_file in Path(".").glob(pattern):
            if "test_env" not in str(test_file) and "venv" not in str(test_file):
                base_name = re.sub(r'(_\d+|_v\d+|_final|_nuevo|_real|_simple|_auto)', '', test_file.stem)
                test_files[base_name] += 1
    
    duplicates = {k: v for k, v in test_files.items() if v > 1}
    return {
        "total_test_patterns": len(test_files),
        "duplicate_patterns": len(duplicates),
        "duplicates": duplicates
    }

def check_api_consistency():
    """Check for API prefix inconsistencies"""
    main_file = Path("main.py")
    if not main_file.exists():
        return {"error": "main.py not found"}
    
    content = main_file.read_text()
    
    # Find all router includes
    router_pattern = r'app\.include_router\((\w+)(?:,\s*prefix\s*=\s*["\']([^"\']+)["\'])?\)'
    matches = re.findall(router_pattern, content)
    
    api_prefixed = []
    non_prefixed = []
    bare_routers = []
    
    for router_name, prefix in matches:
        if prefix:
            if prefix.startswith("/api"):
                api_prefixed.append((router_name, prefix))
            else:
                non_prefixed.append((router_name, prefix))
        else:
            bare_routers.append(router_name)
    
    return {
        "total_routers": len(matches),
        "api_prefixed": len(api_prefixed),
        "non_api_prefixed": len(non_prefixed),
        "bare_routers": len(bare_routers),
        "mixed_prefixes": len(api_prefixed) > 0 and (len(non_prefixed) > 0 or len(bare_routers) > 0)
    }

def check_database_constraints():
    """Check for missing UNIQUE constraints"""
    sql_file = Path("supabase_setup.sql")
    if not sql_file.exists():
        return {"error": "supabase_setup.sql not found"}
    
    content = sql_file.read_text()
    
    # Check critical tables for UNIQUE constraints
    critical_tables = ["tasks", "agents", "workspaces"]
    results = {}
    
    for table in critical_tables:
        # Look for UNIQUE constraints on this table
        table_pattern = rf'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{table}.*?(?=CREATE|$)'
        table_match = re.search(table_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if table_match:
            table_content = table_match.group(0)
            has_unique = "UNIQUE" in table_content.upper()
            results[table] = {
                "has_unique_constraint": has_unique,
                "table_found": True
            }
        else:
            results[table] = {
                "has_unique_constraint": False,
                "table_found": False
            }
    
    return results

def check_logging_fragmentation():
    """Check for multiple logging table usage"""
    logging_tables = ["execution_logs", "thinking_process_steps", "audit_logs"]
    table_usage = defaultdict(list)
    
    for py_file in Path(".").rglob("*.py"):
        if "test_env" in str(py_file) or "venv" in str(py_file):
            continue
            
        try:
            content = py_file.read_text()
            for table in logging_tables:
                if table in content:
                    table_usage[table].append(str(py_file))
        except:
            pass
    
    return {
        "tables_in_use": len(table_usage),
        "fragmented": len(table_usage) > 1,
        "usage_summary": {k: len(v) for k, v in table_usage.items()}
    }

def main():
    """Run all audit checks"""
    print("AI Team Orchestrator - Quick Audit Check")
    print("=" * 50)
    
    # Check 1: Trace ID Implementation
    print("\n1. Trace ID Implementation Check:")
    trace_results = check_trace_id_implementation()
    print(f"   Total routes: {trace_results['total_routes']}")
    print(f"   Routes with trace ID: {trace_results['routes_with_trace']}")
    print(f"   Coverage: {trace_results['routes_with_trace'] / max(trace_results['total_routes'], 1) * 100:.1f}%")
    
    # Check 2: Duplicate Tests
    print("\n2. Test Duplication Check:")
    test_results = check_duplicate_tests()
    print(f"   Total test patterns: {test_results['total_test_patterns']}")
    print(f"   Duplicate patterns: {test_results['duplicate_patterns']}")
    if test_results['duplicates']:
        print("   Top duplicates:")
        for pattern, count in sorted(test_results['duplicates'].items(), 
                                   key=lambda x: x[1], reverse=True)[:5]:
            print(f"     - {pattern}: {count} files")
    
    # Check 3: API Consistency
    print("\n3. API Routing Consistency Check:")
    api_results = check_api_consistency()
    if "error" not in api_results:
        print(f"   Total routers: {api_results['total_routers']}")
        print(f"   With /api prefix: {api_results['api_prefixed']}")
        print(f"   Without /api prefix: {api_results['non_api_prefixed'] + api_results['bare_routers']}")
        print(f"   Mixed prefixes: {'YES' if api_results['mixed_prefixes'] else 'NO'}")
    else:
        print(f"   Error: {api_results['error']}")
    
    # Check 4: Database Constraints
    print("\n4. Database Constraints Check:")
    db_results = check_database_constraints()
    if "error" not in db_results:
        for table, info in db_results.items():
            status = "✓" if info['has_unique_constraint'] else "✗"
            print(f"   {status} {table}: {'HAS' if info['has_unique_constraint'] else 'MISSING'} UNIQUE constraint")
    else:
        print(f"   Error: {db_results['error']}")
    
    # Check 5: Logging Fragmentation
    print("\n5. Logging Fragmentation Check:")
    log_results = check_logging_fragmentation()
    print(f"   Logging tables in use: {log_results['tables_in_use']}")
    print(f"   Fragmented: {'YES' if log_results['fragmented'] else 'NO'}")
    for table, count in log_results['usage_summary'].items():
        print(f"   - {table}: used in {count} files")
    
    # Summary
    print("\n" + "=" * 50)
    print("AUDIT SUMMARY:")
    issues = 0
    if trace_results['routes_with_trace'] == 0:
        print("❌ CRITICAL: No trace ID implementation found")
        issues += 1
    if test_results['duplicate_patterns'] > 5:
        print("❌ HIGH: Excessive test duplication")
        issues += 1
    if api_results.get('mixed_prefixes', False):
        print("❌ MEDIUM: Inconsistent API prefixes")
        issues += 1
    if db_results.get('tasks', {}).get('has_unique_constraint') == False:
        print("❌ HIGH: Missing database constraints")
        issues += 1
    if log_results['fragmented']:
        print("❌ MEDIUM: Fragmented logging strategy")
        issues += 1
    
    if issues == 0:
        print("✅ All checks passed!")
    else:
        print(f"\nTotal issues found: {issues}")
        print("Run 'python audit_scripts.py' for detailed analysis")

if __name__ == "__main__":
    main()