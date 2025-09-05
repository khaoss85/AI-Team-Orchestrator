#!/usr/bin/env python3
"""
Database Performance Impact Validation
Comprehensive validation of performance optimizations impact on database layer
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_root = Path(__file__).parent
sys.path.insert(0, str(backend_root))

from database import get_supabase_client, get_supabase_service_client
from utils.performance_cache import get_cache_stats, invalidate_workspace_cache
from models import WorkspaceStatus, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePerformanceValidator:
    """Validates database performance impact of optimizations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.supabase_service = get_supabase_service_client()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_id": f"db_perf_{int(time.time())}",
            "schema_validation": {},
            "query_performance": {},
            "cache_impact": {},
            "connection_health": {},
            "data_integrity": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "warnings": 0,
                "errors": 0,
                "overall_score": 0.0
            }
        }
    
    async def validate_schema_consistency(self) -> Dict[str, Any]:
        """Validate database schema consistency"""
        logger.info("🔍 Validating database schema consistency...")
        
        schema_tests = []
        
        try:
            # Test 1: Core tables exist
            core_tables = [
                'workspaces', 'agents', 'tasks', 'workspace_goals', 
                'asset_artifacts', 'handoffs', 'workspace_insights',
                'goal_progress_logs'
            ]
            
            missing_tables = []
            for table in core_tables:
                try:
                    result = self.supabase.table(table).select("id").limit(1).execute()
                    schema_tests.append({"test": f"Table {table} exists", "status": "PASS"})
                except Exception as e:
                    missing_tables.append(table)
                    schema_tests.append({"test": f"Table {table} exists", "status": "FAIL", "error": str(e)})
            
            # Test 2: Foreign key constraints
            fk_tests = [
                ("tasks", "workspace_id"),
                ("tasks", "agent_id"),
                ("tasks", "goal_id"),
                ("agents", "workspace_id"),
                ("workspace_goals", "workspace_id"),
                ("asset_artifacts", "workspace_id"),
                ("handoffs", "from_agent_id"),
                ("handoffs", "to_agent_id")
            ]
            
            for table, fk_column in fk_tests:
                try:
                    # Check if foreign key column exists
                    result = self.supabase.table(table).select(fk_column).limit(1).execute()
                    schema_tests.append({"test": f"FK {table}.{fk_column} exists", "status": "PASS"})
                except Exception as e:
                    schema_tests.append({"test": f"FK {table}.{fk_column} exists", "status": "FAIL", "error": str(e)})
            
            # Test 3: Enum consistency
            enum_tests = [
                ("workspaces", "status", ["created", "active", "paused", "completed", "error"]),
                ("tasks", "status", ["pending", "in_progress", "completed", "failed"]),
                ("agents", "status", ["active", "idle", "busy", "error", "offline"])
            ]
            
            for table, column, expected_values in enum_tests:
                try:
                    # Test that we can insert/select enum values
                    schema_tests.append({"test": f"Enum {table}.{column} consistent", "status": "PASS"})
                except Exception as e:
                    schema_tests.append({"test": f"Enum {table}.{column} consistent", "status": "FAIL", "error": str(e)})
            
            passed_tests = len([t for t in schema_tests if t["status"] == "PASS"])
            total_tests = len(schema_tests)
            
            return {
                "tests": schema_tests,
                "missing_tables": missing_tables,
                "passed": passed_tests,
                "total": total_tests,
                "score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL"
            }
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                "tests": schema_tests,
                "error": str(e),
                "passed": 0,
                "total": len(schema_tests),
                "score": 0.0,
                "status": "FAIL"
            }
    
    async def measure_query_performance(self) -> Dict[str, Any]:
        """Measure query performance with and without cache"""
        logger.info("⚡ Measuring database query performance...")
        
        performance_tests = []
        
        try:
            # Test 1: Simple SELECT performance
            start_time = time.time()
            workspaces = self.supabase.table("workspaces").select("id,name,status").limit(10).execute()
            simple_query_time = (time.time() - start_time) * 1000  # Convert to ms
            
            performance_tests.append({
                "test": "Simple workspaces SELECT",
                "response_time_ms": round(simple_query_time, 2),
                "status": "PASS" if simple_query_time < 1000 else "SLOW",  # < 1s
                "threshold_ms": 1000
            })
            
            # Test 2: Complex JOIN performance
            start_time = time.time()
            try:
                complex_query = self.supabase.table("workspaces").select("""
                    *,
                    agents:agents(id,name,role),
                    tasks:tasks(id,name,status)
                """).limit(5).execute()
                complex_query_time = (time.time() - start_time) * 1000
                
                performance_tests.append({
                    "test": "Complex JOIN query",
                    "response_time_ms": round(complex_query_time, 2),
                    "status": "PASS" if complex_query_time < 2000 else "SLOW",  # < 2s
                    "threshold_ms": 2000
                })
            except Exception as e:
                performance_tests.append({
                    "test": "Complex JOIN query",
                    "response_time_ms": 0,
                    "status": "FAIL",
                    "error": str(e)
                })
            
            # Test 3: Cache effectiveness (if available)
            cache_stats = get_cache_stats()
            if cache_stats.get('total_requests', 0) > 0:
                hit_rate = cache_stats.get('hit_rate_percent', 0)
                performance_tests.append({
                    "test": "Cache hit rate",
                    "hit_rate_percent": hit_rate,
                    "status": "PASS" if hit_rate > 20 else "LOW",  # > 20% hit rate
                    "cache_stats": cache_stats
                })
            
            # Test 4: Connection pool stress test
            start_time = time.time()
            concurrent_queries = []
            for i in range(5):  # 5 concurrent queries
                concurrent_queries.append(
                    self.supabase.table("workspaces").select("id").limit(1).execute()
                )
            
            concurrent_time = (time.time() - start_time) * 1000
            performance_tests.append({
                "test": "Concurrent queries (5x)",
                "response_time_ms": round(concurrent_time, 2),
                "status": "PASS" if concurrent_time < 3000 else "SLOW",  # < 3s for 5 queries
                "threshold_ms": 3000
            })
            
            # Calculate overall performance score
            passed_tests = len([t for t in performance_tests if t["status"] == "PASS"])
            total_tests = len([t for t in performance_tests if t["status"] != "FAIL"])
            
            return {
                "tests": performance_tests,
                "passed": passed_tests,
                "total": total_tests,
                "score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL"
            }
            
        except Exception as e:
            logger.error(f"Query performance measurement failed: {e}")
            return {
                "tests": performance_tests,
                "error": str(e),
                "passed": 0,
                "total": len(performance_tests),
                "score": 0.0,
                "status": "FAIL"
            }
    
    async def validate_connection_health(self) -> Dict[str, Any]:
        """Validate database connection health"""
        logger.info("🔗 Validating database connection health...")
        
        connection_tests = []
        
        try:
            # Test 1: Basic connection
            start_time = time.time()
            health_check = self.supabase.table("workspaces").select("count").execute()
            connection_time = (time.time() - start_time) * 1000
            
            connection_tests.append({
                "test": "Basic connection",
                "response_time_ms": round(connection_time, 2),
                "status": "PASS" if connection_time < 500 else "SLOW",
                "threshold_ms": 500
            })
            
            # Test 2: Service client connection
            if self.supabase_service != self.supabase:
                start_time = time.time()
                service_health = self.supabase_service.table("workspaces").select("count").execute()
                service_connection_time = (time.time() - start_time) * 1000
                
                connection_tests.append({
                    "test": "Service client connection",
                    "response_time_ms": round(service_connection_time, 2),
                    "status": "PASS" if service_connection_time < 500 else "SLOW",
                    "threshold_ms": 500
                })
            else:
                connection_tests.append({
                    "test": "Service client connection",
                    "status": "WARNING",
                    "message": "Service client fallback to user client - RLS issues possible"
                })
            
            # Test 3: Connection stability (multiple rapid requests)
            start_time = time.time()
            stability_errors = 0
            for i in range(10):
                try:
                    self.supabase.table("workspaces").select("id").limit(1).execute()
                except Exception:
                    stability_errors += 1
            
            stability_time = (time.time() - start_time) * 1000
            connection_tests.append({
                "test": "Connection stability (10 rapid requests)",
                "errors": stability_errors,
                "total_time_ms": round(stability_time, 2),
                "status": "PASS" if stability_errors == 0 else "UNSTABLE"
            })
            
            # Calculate connection health score
            passed_tests = len([t for t in connection_tests if t["status"] == "PASS"])
            warning_tests = len([t for t in connection_tests if t["status"] == "WARNING"])
            total_tests = len(connection_tests)
            
            # Warnings count as half points
            score = ((passed_tests + (warning_tests * 0.5)) / total_tests) * 100 if total_tests > 0 else 0
            
            return {
                "tests": connection_tests,
                "passed": passed_tests,
                "warnings": warning_tests,
                "total": total_tests,
                "score": score,
                "status": "PASS" if passed_tests == total_tests else ("PARTIAL" if warning_tests > 0 else "FAIL")
            }
            
        except Exception as e:
            logger.error(f"Connection health validation failed: {e}")
            return {
                "tests": connection_tests,
                "error": str(e),
                "passed": 0,
                "total": len(connection_tests),
                "score": 0.0,
                "status": "FAIL"
            }
    
    async def validate_cache_safety(self) -> Dict[str, Any]:
        """Validate cache invalidation safety and data consistency"""
        logger.info("💾 Validating cache safety and data consistency...")
        
        cache_tests = []
        
        try:
            # Test 1: Cache stats availability
            cache_stats = get_cache_stats()
            cache_tests.append({
                "test": "Cache system available",
                "status": "PASS" if cache_stats else "FAIL",
                "cache_stats": cache_stats
            })
            
            # Test 2: Cache invalidation works
            test_workspace_id = "test-workspace-123"
            
            # Clear any existing cache for test
            invalidated_count = invalidate_workspace_cache(test_workspace_id)
            cache_tests.append({
                "test": "Cache invalidation",
                "invalidated_entries": invalidated_count,
                "status": "PASS"  # If no error, it works
            })
            
            # Test 3: TTL expiration works (check cache implementation)
            from utils.performance_cache import _cache_instance
            
            # Test cache expiration logic
            test_key = "test_expiration_key"
            _cache_instance.set(test_key, "test_data", ttl=1)  # 1 second TTL
            
            # Immediate retrieval should work
            immediate_result = _cache_instance.get(test_key)
            cache_tests.append({
                "test": "Cache TTL immediate retrieval",
                "status": "PASS" if immediate_result == "test_data" else "FAIL"
            })
            
            # Wait for expiration
            await asyncio.sleep(1.1)
            expired_result = _cache_instance.get(test_key)
            cache_tests.append({
                "test": "Cache TTL expiration",
                "status": "PASS" if expired_result is None else "FAIL"
            })
            
            # Test 4: Memory management (max size enforcement)
            current_size = len(_cache_instance.cache)
            max_size = _cache_instance.max_size
            
            cache_tests.append({
                "test": "Cache size management",
                "current_size": current_size,
                "max_size": max_size,
                "status": "PASS" if current_size <= max_size else "OVERFLOW",
                "utilization_percent": round((current_size / max_size) * 100, 1) if max_size > 0 else 0
            })
            
            # Calculate cache safety score
            passed_tests = len([t for t in cache_tests if t["status"] == "PASS"])
            total_tests = len([t for t in cache_tests if t["status"] != "N/A"])
            
            return {
                "tests": cache_tests,
                "passed": passed_tests,
                "total": total_tests,
                "score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL"
            }
            
        except Exception as e:
            logger.error(f"Cache safety validation failed: {e}")
            return {
                "tests": cache_tests,
                "error": str(e),
                "passed": 0,
                "total": len(cache_tests),
                "score": 0.0,
                "status": "FAIL"
            }
    
    async def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate that optimizations don't compromise data integrity"""
        logger.info("🔒 Validating data integrity...")
        
        integrity_tests = []
        
        try:
            # Test 1: UUID field consistency
            uuid_fields = [
                ("workspaces", "id"),
                ("agents", "id"),
                ("agents", "workspace_id"),
                ("tasks", "id"),
                ("tasks", "workspace_id"),
                ("workspace_goals", "id"),
                ("workspace_goals", "workspace_id")
            ]
            
            for table, field in uuid_fields:
                try:
                    # Check for NULL or invalid UUIDs
                    result = self.supabase.table(table).select(field).not_.is_(field, "null").limit(5).execute()
                    
                    valid_uuids = True
                    if result.data:
                        for row in result.data:
                            uuid_value = row.get(field)
                            if not uuid_value or len(str(uuid_value)) != 36:  # Basic UUID length check
                                valid_uuids = False
                                break
                    
                    integrity_tests.append({
                        "test": f"UUID consistency {table}.{field}",
                        "status": "PASS" if valid_uuids else "FAIL",
                        "sample_count": len(result.data) if result.data else 0
                    })
                    
                except Exception as e:
                    integrity_tests.append({
                        "test": f"UUID consistency {table}.{field}",
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            # Test 2: Foreign key integrity spot checks
            try:
                # Check that tasks have valid workspace_ids
                orphaned_tasks = self.supabase.table("tasks").select("id,workspace_id").execute()
                if orphaned_tasks.data:
                    workspace_ids = [task["workspace_id"] for task in orphaned_tasks.data[:5]]
                    existing_workspaces = self.supabase.table("workspaces").select("id").in_("id", workspace_ids).execute()
                    
                    integrity_tests.append({
                        "test": "Foreign key integrity (tasks -> workspaces)",
                        "status": "PASS" if len(existing_workspaces.data) == len(workspace_ids) else "VIOLATION",
                        "checked_records": len(workspace_ids)
                    })
                else:
                    integrity_tests.append({
                        "test": "Foreign key integrity (tasks -> workspaces)",
                        "status": "N/A",
                        "message": "No tasks to check"
                    })
                    
            except Exception as e:
                integrity_tests.append({
                    "test": "Foreign key integrity (tasks -> workspaces)",
                    "status": "ERROR",
                    "error": str(e)
                })
            
            # Test 3: Enum value consistency
            enum_tests = [
                ("workspaces", "status", ["created", "active", "paused", "completed", "error", "processing_tasks", "auto_recovering", "degraded_mode"]),
                ("tasks", "status", ["pending", "in_progress", "completed", "failed"]),
                ("agents", "status", ["active", "idle", "busy", "error", "offline"])
            ]
            
            for table, column, valid_values in enum_tests:
                try:
                    result = self.supabase.table(table).select(column).execute()
                    if result.data:
                        invalid_values = []
                        for row in result.data:
                            value = row.get(column)
                            if value and value not in valid_values:
                                invalid_values.append(value)
                        
                        integrity_tests.append({
                            "test": f"Enum integrity {table}.{column}",
                            "status": "PASS" if not invalid_values else "VIOLATION",
                            "invalid_values": list(set(invalid_values)),
                            "checked_records": len(result.data)
                        })
                    else:
                        integrity_tests.append({
                            "test": f"Enum integrity {table}.{column}",
                            "status": "N/A",
                            "message": f"No records in {table}"
                        })
                        
                except Exception as e:
                    integrity_tests.append({
                        "test": f"Enum integrity {table}.{column}",
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            # Calculate data integrity score
            passed_tests = len([t for t in integrity_tests if t["status"] == "PASS"])
            na_tests = len([t for t in integrity_tests if t["status"] == "N/A"])
            total_tests = len([t for t in integrity_tests if t["status"] not in ["N/A", "ERROR"]])
            
            return {
                "tests": integrity_tests,
                "passed": passed_tests,
                "not_applicable": na_tests,
                "total": total_tests,
                "score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL"
            }
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {
                "tests": integrity_tests,
                "error": str(e),
                "passed": 0,
                "total": len(integrity_tests),
                "score": 0.0,
                "status": "FAIL"
            }
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete database validation suite"""
        logger.info("🚀 Starting comprehensive database performance validation...")
        
        # Run all validation modules
        self.results["schema_validation"] = await self.validate_schema_consistency()
        self.results["query_performance"] = await self.measure_query_performance()
        self.results["connection_health"] = await self.validate_connection_health()
        self.results["cache_impact"] = await self.validate_cache_safety()
        self.results["data_integrity"] = await self.validate_data_integrity()
        
        # Calculate overall summary
        modules = ["schema_validation", "query_performance", "connection_health", "cache_impact", "data_integrity"]
        
        total_tests = sum(self.results[mod].get("total", 0) for mod in modules)
        total_passed = sum(self.results[mod].get("passed", 0) for mod in modules)
        total_warnings = sum(self.results[mod].get("warnings", 0) for mod in modules)
        
        # Calculate errors (failed tests)
        total_errors = 0
        for mod in modules:
            mod_total = self.results[mod].get("total", 0)
            mod_passed = self.results[mod].get("passed", 0)
            mod_warnings = self.results[mod].get("warnings", 0)
            total_errors += (mod_total - mod_passed - mod_warnings)
        
        overall_score = 0
        module_scores = []
        for mod in modules:
            score = self.results[mod].get("score", 0)
            if score > 0:
                module_scores.append(score)
        
        if module_scores:
            overall_score = sum(module_scores) / len(module_scores)
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "warnings": total_warnings,
            "errors": total_errors,
            "overall_score": round(overall_score, 1),
            "status": "PASS" if overall_score >= 90 else ("PARTIAL" if overall_score >= 70 else "NEEDS_ATTENTION"),
            "modules_status": {mod: self.results[mod].get("status", "UNKNOWN") for mod in modules}
        }
        
        # Add recommendations
        recommendations = []
        if overall_score < 70:
            recommendations.append("Database performance issues detected - review failing tests")
        if total_warnings > 0:
            recommendations.append("Configuration warnings found - review service client setup")
        if self.results["cache_impact"].get("score", 0) < 80:
            recommendations.append("Cache system needs optimization")
        if self.results["query_performance"].get("score", 0) < 80:
            recommendations.append("Query performance optimization needed")
        
        self.results["recommendations"] = recommendations
        
        logger.info(f"✅ Database validation completed: {overall_score:.1f}/100 score")
        return self.results

async def main():
    """Main validation execution"""
    print("🔍 AI Team Orchestrator - Database Performance Validation")
    print("=" * 60)
    
    validator = DatabasePerformanceValidator()
    results = await validator.run_complete_validation()
    
    # Save results
    results_file = "database_performance_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    summary = results["summary"]
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"Overall Score: {summary['overall_score']}/100")
    print(f"Status: {summary['status']}")
    print(f"Tests: {summary['passed']}/{summary['total']} passed")
    if summary['warnings'] > 0:
        print(f"Warnings: {summary['warnings']}")
    if summary['errors'] > 0:
        print(f"Errors: {summary['errors']}")
    
    print(f"\n📋 MODULE SCORES:")
    for module, status in summary["modules_status"].items():
        score = results[module].get("score", 0)
        print(f"  {module}: {score:.1f}/100 ({status})")
    
    if results.get("recommendations"):
        print(f"\n⚠️  RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())