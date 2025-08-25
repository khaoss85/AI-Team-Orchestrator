#!/usr/bin/env python3
"""
AI Team Orchestrator - Improvement Monitoring Script
Tracks progress on audit findings over time
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess

class ImprovementMonitor:
    """Monitors improvement progress over time"""
    
    def __init__(self):
        self.metrics_file = Path("audit_metrics_history.json")
        self.baseline_date = "2025-07-04"
        
    def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "trace_id_coverage": self._check_trace_coverage(),
            "duplicate_test_count": self._count_duplicate_tests(),
            "api_consistency_score": self._check_api_consistency(),
            "database_constraint_coverage": self._check_db_constraints(),
            "logging_fragmentation": self._check_logging_fragmentation(),
            "orchestrator_consolidation": self._check_orchestrator_status(),
            "code_quality_metrics": self._collect_code_metrics()
        }
        return metrics
    
    def _check_trace_coverage(self) -> float:
        """Check percentage of routes with trace ID support"""
        routes_path = Path("routes")
        if not routes_path.exists():
            return 0.0
            
        total_routes = len([f for f in routes_path.glob("*.py") if f.name != "__init__.py"])
        trace_patterns = ["X-Trace-ID", "x-trace-id", "trace_id", "traceId"]
        
        routes_with_trace = 0
        for route_file in routes_path.glob("*.py"):
            if route_file.name == "__init__.py":
                continue
            try:
                content = route_file.read_text()
                if any(pattern in content for pattern in trace_patterns):
                    routes_with_trace += 1
            except:
                pass
        
        return (routes_with_trace / max(total_routes, 1)) * 100
    
    def _count_duplicate_tests(self) -> int:
        """Count duplicate test files"""
        test_files = list(Path(".").glob("*e2e*.py"))
        test_files.extend(Path(".").glob("comprehensive*.py"))
        
        # Filter out test_env and venv
        test_files = [f for f in test_files if "test_env" not in str(f) and "venv" not in str(f)]
        
        # Group by base pattern
        base_patterns = set()
        for test_file in test_files:
            import re
            base_name = re.sub(r'(_\d+|_v\d+|_final|_nuevo|_real|_simple|_auto)', '', test_file.stem)
            base_patterns.add(base_name)
        
        return len(test_files) - len(base_patterns)  # Duplicates = total - unique patterns
    
    def _check_api_consistency(self) -> float:
        """Check API consistency score (0-100)"""
        main_file = Path("main.py")
        if not main_file.exists():
            return 0.0
        
        try:
            content = main_file.read_text()
            import re
            
            # Find all router includes
            router_pattern = r'app\.include_router\((\w+)(?:,\s*prefix\s*=\s*["\']([^"\']+)["\'])?\)'
            matches = re.findall(router_pattern, content)
            
            if not matches:
                return 100.0  # No routers = consistent
            
            # Count consistent prefixes
            api_prefixed = sum(1 for _, prefix in matches if prefix and prefix.startswith("/api"))
            total_routers = len(matches)
            
            # Score: 100% if all have same prefix pattern, 0% if completely mixed
            consistency_score = (api_prefixed / total_routers) * 100
            if consistency_score < 50:
                consistency_score = 100 - consistency_score  # Favor no-prefix consistency
            
            return consistency_score
        except:
            return 0.0
    
    def _check_db_constraints(self) -> float:
        """Check database constraint coverage"""
        sql_file = Path("supabase_setup.sql")
        if not sql_file.exists():
            return 0.0
        
        try:
            content = sql_file.read_text()
            critical_tables = ["tasks", "agents", "workspaces"]
            tables_with_constraints = 0
            
            for table in critical_tables:
                # Look for UNIQUE constraints on this table
                import re
                table_pattern = rf'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{table}.*?(?=CREATE|$)'
                table_match = re.search(table_pattern, content, re.IGNORECASE | re.DOTALL)
                
                if table_match:
                    table_content = table_match.group(0)
                    if "UNIQUE" in table_content.upper():
                        tables_with_constraints += 1
            
            return (tables_with_constraints / len(critical_tables)) * 100
        except:
            return 0.0
    
    def _check_logging_fragmentation(self) -> int:
        """Count number of different logging tables in use"""
        logging_tables = ["execution_logs", "thinking_process_steps", "audit_logs"]
        tables_in_use = 0
        
        for table in logging_tables:
            # Check if table is referenced in any Python file
            found = False
            for py_file in Path(".").rglob("*.py"):
                if "test_env" in str(py_file) or "venv" in str(py_file):
                    continue
                try:
                    content = py_file.read_text()
                    if table in content:
                        found = True
                        break
                except:
                    pass
            
            if found:
                tables_in_use += 1
        
        return tables_in_use
    
    def _check_orchestrator_status(self) -> Dict[str, Any]:
        """Check orchestrator consolidation status"""
        deprecated_path = Path("services/deprecated_orchestrators")
        unified_path = Path("services/unified_orchestrator.py")
        
        return {
            "deprecated_files": len(list(deprecated_path.glob("*.py"))) if deprecated_path.exists() else 0,
            "unified_exists": unified_path.exists(),
            "consolidation_complete": unified_path.exists() and not deprecated_path.exists()
        }
    
    def _collect_code_metrics(self) -> Dict[str, int]:
        """Collect basic code quality metrics"""
        metrics = {
            "total_python_files": 0,
            "total_lines_of_code": 0,
            "total_functions": 0,
            "total_classes": 0
        }
        
        for py_file in Path(".").rglob("*.py"):
            if "test_env" in str(py_file) or "venv" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                metrics["total_python_files"] += 1
                metrics["total_lines_of_code"] += len(content.splitlines())
                
                # Count functions and classes
                import re
                metrics["total_functions"] += len(re.findall(r'def\s+\w+\s*\(', content))
                metrics["total_classes"] += len(re.findall(r'class\s+\w+', content))
            except:
                pass
        
        return metrics
    
    def save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to history file"""
        history = []
        
        # Load existing history
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Add new metrics
        history.append(metrics)
        
        # Keep only last 30 entries
        history = history[-30:]
        
        # Save updated history
        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def generate_progress_report(self) -> str:
        """Generate improvement progress report"""
        if not self.metrics_file.exists():
            return "No metrics history found. Run monitor first."
        
        try:
            with open(self.metrics_file, 'r') as f:
                history = json.load(f)
        except:
            return "Error reading metrics history."
        
        if len(history) < 2:
            return "Need at least 2 measurements to show progress."
        
        # Compare latest vs baseline
        latest = history[-1]
        baseline = history[0]
        
        report = f"""
AI Team Orchestrator - Improvement Progress Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROGRESS SUMMARY:
================

Trace ID Coverage:
  Baseline: {baseline['trace_id_coverage']:.1f}%
  Current:  {latest['trace_id_coverage']:.1f}%
  Change:   {latest['trace_id_coverage'] - baseline['trace_id_coverage']:+.1f}%

Duplicate Tests:
  Baseline: {baseline['duplicate_test_count']} duplicates
  Current:  {latest['duplicate_test_count']} duplicates
  Change:   {latest['duplicate_test_count'] - baseline['duplicate_test_count']:+d}

API Consistency:
  Baseline: {baseline['api_consistency_score']:.1f}%
  Current:  {latest['api_consistency_score']:.1f}%
  Change:   {latest['api_consistency_score'] - baseline['api_consistency_score']:+.1f}%

Database Constraints:
  Baseline: {baseline['database_constraint_coverage']:.1f}%
  Current:  {latest['database_constraint_coverage']:.1f}%
  Change:   {latest['database_constraint_coverage'] - baseline['database_constraint_coverage']:+.1f}%

Logging Fragmentation:
  Baseline: {baseline['logging_fragmentation']} tables
  Current:  {latest['logging_fragmentation']} tables
  Change:   {latest['logging_fragmentation'] - baseline['logging_fragmentation']:+d}

Orchestrator Status:
  Deprecated files: {latest['orchestrator_consolidation']['deprecated_files']}
  Unified exists: {latest['orchestrator_consolidation']['unified_exists']}
  Consolidation complete: {latest['orchestrator_consolidation']['consolidation_complete']}

CODE QUALITY TRENDS:
===================
Python files: {latest['code_quality_metrics']['total_python_files']} 
  ({latest['code_quality_metrics']['total_python_files'] - baseline['code_quality_metrics']['total_python_files']:+d})
Lines of code: {latest['code_quality_metrics']['total_lines_of_code']}
  ({latest['code_quality_metrics']['total_lines_of_code'] - baseline['code_quality_metrics']['total_lines_of_code']:+d})
Functions: {latest['code_quality_metrics']['total_functions']}
  ({latest['code_quality_metrics']['total_functions'] - baseline['code_quality_metrics']['total_functions']:+d})
Classes: {latest['code_quality_metrics']['total_classes']}
  ({latest['code_quality_metrics']['total_classes'] - baseline['code_quality_metrics']['total_classes']:+d})

RECOMMENDATIONS:
===============
"""
        
        # Add recommendations based on changes
        recommendations = []
        
        if latest['trace_id_coverage'] == 0:
            recommendations.append("🔴 CRITICAL: Still no trace ID implementation - this should be priority #1")
        elif latest['trace_id_coverage'] < 50:
            recommendations.append("🟡 Continue implementing trace ID in remaining routes")
        else:
            recommendations.append("🟢 Good progress on trace ID implementation")
        
        if latest['duplicate_test_count'] > 10:
            recommendations.append("🔴 HIGH: Still many duplicate tests - consolidate test suites")
        elif latest['duplicate_test_count'] > 5:
            recommendations.append("🟡 Some duplicate tests remain - continue consolidation")
        else:
            recommendations.append("🟢 Test duplication under control")
        
        if latest['database_constraint_coverage'] < 100:
            recommendations.append("🔴 Add missing database constraints on critical tables")
        else:
            recommendations.append("🟢 Database constraints properly implemented")
        
        if latest['logging_fragmentation'] > 1:
            recommendations.append("🟡 Consolidate logging to single table/strategy")
        else:
            recommendations.append("🟢 Logging strategy unified")
        
        if not latest['orchestrator_consolidation']['consolidation_complete']:
            recommendations.append("🟡 Complete orchestrator consolidation - remove deprecated files")
        else:
            recommendations.append("🟢 Orchestrator consolidation complete")
        
        report += "\n".join(recommendations)
        
        return report
    
    def run_monitoring(self):
        """Run complete monitoring cycle"""
        print("Collecting current metrics...")
        metrics = self.collect_current_metrics()
        
        print("Saving metrics to history...")
        self.save_metrics(metrics)
        
        print("Generating progress report...")
        report = self.generate_progress_report()
        
        # Save report
        report_file = f"improvement_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Progress report saved to {report_file}")
        print("\nSummary of current metrics:")
        print(f"  Trace ID Coverage: {metrics['trace_id_coverage']:.1f}%")
        print(f"  Duplicate Tests: {metrics['duplicate_test_count']}")
        print(f"  API Consistency: {metrics['api_consistency_score']:.1f}%")
        print(f"  DB Constraints: {metrics['database_constraint_coverage']:.1f}%")
        print(f"  Logging Tables: {metrics['logging_fragmentation']}")
        
        return metrics, report

if __name__ == "__main__":
    monitor = ImprovementMonitor()
    monitor.run_monitoring()