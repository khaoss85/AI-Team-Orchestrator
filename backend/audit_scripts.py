#!/usr/bin/env python3
"""
AI Team Orchestrator - Technical Audit Scripts
Generated for comprehensive system analysis
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any

class SystemAuditor:
    """Comprehensive system audit utilities"""
    
    def __init__(self, backend_path: str = "."):
        self.backend_path = Path(backend_path)
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": [],
            "statistics": {},
            "duplications": {},
            "trace_analysis": {},
            "db_analysis": {}
        }
    
    def find_duplicate_test_files(self) -> Dict[str, List[str]]:
        """Find all duplicate test files based on patterns"""
        test_patterns = [
            "*e2e*.py",
            "*test*.py",
            "*_test.py"
        ]
        
        test_files = defaultdict(list)
        for pattern in test_patterns:
            for file in self.backend_path.rglob(pattern):
                if "test_env" not in str(file) and "venv" not in str(file):
                    # Group by base name pattern
                    base_name = re.sub(r'(_\d+|_v\d+|_final|_nuevo|_real|_simple|_auto)', '', file.stem)
                    test_files[base_name].append(str(file))
        
        # Filter only duplicates
        duplicates = {k: v for k, v in test_files.items() if len(v) > 1}
        self.audit_results["duplications"]["test_files"] = duplicates
        return duplicates
    
    def analyze_functional_silos(self) -> Dict[str, Any]:
        """Analyze functional overlaps between modules"""
        overlapping_modules = {
            "quality_assurance": ["ai_quality_assurance/", "services/ai_quality_gate_engine.py"],
            "deliverable_system": ["deliverable_system/", "services/asset_first_deliverable_system.py"],
            "orchestrators": ["services/unified_orchestrator.py", "services/deprecated_orchestrators/"],
            "memory_systems": ["services/memory_system.py", "services/universal_memory_architecture.py"],
            "goal_systems": ["goal_driven_task_planner.py", "services/enhanced_goal_driven_planner.py"]
        }
        
        silo_analysis = {}
        for category, paths in overlapping_modules.items():
            files = []
            for path in paths:
                full_path = self.backend_path / path
                if full_path.is_dir():
                    files.extend([str(f) for f in full_path.rglob("*.py")])
                elif full_path.exists():
                    files.append(str(full_path))
            
            # Analyze imports and function names for overlap
            functions = defaultdict(list)
            imports = defaultdict(int)
            
            for file in files:
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        # Extract function definitions
                        func_matches = re.findall(r'def\s+(\w+)\s*\(', content)
                        for func in func_matches:
                            functions[func].append(file)
                        
                        # Extract imports
                        import_matches = re.findall(r'from\s+(\w+)\s+import|import\s+(\w+)', content)
                        for match in import_matches:
                            module = match[0] or match[1]
                            imports[module] += 1
                except:
                    pass
            
            # Find duplicate functions
            duplicate_funcs = {k: v for k, v in functions.items() if len(v) > 1}
            
            silo_analysis[category] = {
                "files": len(files),
                "duplicate_functions": duplicate_funcs,
                "common_imports": dict(sorted(imports.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        
        self.audit_results["functional_silos"] = silo_analysis
        return silo_analysis
    
    def check_trace_id_propagation(self) -> Dict[str, Any]:
        """Check for X-Trace-ID header propagation"""
        trace_analysis = {
            "files_with_trace": [],
            "files_without_trace": [],
            "trace_patterns": defaultdict(int)
        }
        
        # Check all Python files in routes/
        routes_path = self.backend_path / "routes"
        for py_file in routes_path.glob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
                
                # Look for trace ID patterns
                if any(pattern in content for pattern in ["X-Trace-ID", "trace_id", "traceId", "x-trace-id"]):
                    trace_analysis["files_with_trace"].append(str(py_file))
                    
                    # Count specific patterns
                    for pattern in ["X-Trace-ID", "trace_id", "traceId", "x-trace-id"]:
                        count = len(re.findall(pattern, content, re.IGNORECASE))
                        if count > 0:
                            trace_analysis["trace_patterns"][pattern] += count
                else:
                    trace_analysis["files_without_trace"].append(str(py_file))
        
        self.audit_results["trace_analysis"] = trace_analysis
        return trace_analysis
    
    def analyze_api_endpoints(self) -> Dict[str, Any]:
        """Analyze API endpoint consistency"""
        endpoint_analysis = {
            "endpoints": [],
            "prefix_usage": defaultdict(int),
            "inconsistencies": []
        }
        
        # Read main.py to see how routers are mounted
        main_file = self.backend_path / "main.py"
        prefix_map = {}
        
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                # Extract router includes with prefixes
                router_matches = re.findall(
                    r'app\.include_router\((\w+)(?:,\s*prefix\s*=\s*["\']([^"\']+)["\'])?\)',
                    content
                )
                for router_name, prefix in router_matches:
                    prefix_map[router_name] = prefix or ""
                    if prefix:
                        endpoint_analysis["prefix_usage"][prefix] += 1
        
        # Check for duplicate router includes
        router_counts = Counter([match[0] for match in router_matches])
        duplicates = {k: v for k, v in router_counts.items() if v > 1}
        if duplicates:
            endpoint_analysis["inconsistencies"].append({
                "type": "duplicate_router_includes",
                "details": duplicates
            })
        
        # Check for mixed /api prefix usage
        api_prefixed = [p for p in prefix_map.values() if p.startswith("/api")]
        non_api_prefixed = [p for p in prefix_map.values() if p and not p.startswith("/api")]
        
        if api_prefixed and non_api_prefixed:
            endpoint_analysis["inconsistencies"].append({
                "type": "mixed_api_prefix",
                "api_prefixed_count": len(api_prefixed),
                "non_api_prefixed_count": len(non_api_prefixed)
            })
        
        self.audit_results["api_analysis"] = endpoint_analysis
        return endpoint_analysis
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze database schema for duplications and missing constraints"""
        db_analysis = {
            "tables": {},
            "missing_constraints": [],
            "duplicate_tables": [],
            "indexes": defaultdict(list)
        }
        
        # Find all SQL files
        sql_files = list(self.backend_path.rglob("*.sql"))
        
        for sql_file in sql_files:
            with open(sql_file, 'r') as f:
                content = f.read()
                
                # Extract table definitions
                table_matches = re.findall(
                    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
                    content, re.IGNORECASE
                )
                
                for table in table_matches:
                    if table not in db_analysis["tables"]:
                        db_analysis["tables"][table] = {
                            "files": [],
                            "has_unique_constraints": False,
                            "indexes": []
                        }
                    db_analysis["tables"][table]["files"].append(str(sql_file))
                    
                    # Check for UNIQUE constraints
                    if re.search(rf'{table}.*?UNIQUE', content, re.IGNORECASE | re.DOTALL):
                        db_analysis["tables"][table]["has_unique_constraints"] = True
                
                # Extract indexes
                index_matches = re.findall(
                    r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)',
                    content, re.IGNORECASE
                )
                for index_name, table_name in index_matches:
                    db_analysis["indexes"][table_name].append(index_name)
        
        # Find duplicate table definitions
        for table, info in db_analysis["tables"].items():
            if len(info["files"]) > 1:
                db_analysis["duplicate_tables"].append({
                    "table": table,
                    "files": info["files"]
                })
        
        # Check for missing unique constraints on critical tables
        critical_tables = ["tasks", "agents", "workspaces"]
        for table in critical_tables:
            if table in db_analysis["tables"] and not db_analysis["tables"][table]["has_unique_constraints"]:
                db_analysis["missing_constraints"].append(table)
        
        self.audit_results["db_analysis"] = db_analysis
        return db_analysis
    
    def analyze_logging_consistency(self) -> Dict[str, Any]:
        """Analyze logging mechanism consistency"""
        logging_analysis = {
            "logging_tables": defaultdict(list),
            "logging_patterns": defaultdict(int),
            "inconsistencies": []
        }
        
        # Search for different logging patterns
        py_files = list(self.backend_path.rglob("*.py"))
        
        for py_file in py_files:
            if "test_env" in str(py_file) or "venv" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                    # Check for different logging table references
                    if "execution_logs" in content:
                        logging_analysis["logging_tables"]["execution_logs"].append(str(py_file))
                    if "thinking_process_steps" in content:
                        logging_analysis["logging_tables"]["thinking_process_steps"].append(str(py_file))
                    if "audit_logs" in content:
                        logging_analysis["logging_tables"]["audit_logs"].append(str(py_file))
                    
                    # Check for different logging patterns
                    patterns = [
                        (r'logger\.\w+\(', "logger"),
                        (r'logging\.\w+\(', "logging"),
                        (r'print\(', "print"),
                        (r'console\.log\(', "console.log")
                    ]
                    
                    for pattern, name in patterns:
                        count = len(re.findall(pattern, content))
                        if count > 0:
                            logging_analysis["logging_patterns"][name] += count
            except:
                pass
        
        # Check for mixed logging approaches
        if len(logging_analysis["logging_tables"]) > 1:
            logging_analysis["inconsistencies"].append({
                "type": "multiple_logging_tables",
                "tables": list(logging_analysis["logging_tables"].keys())
            })
        
        self.audit_results["logging_analysis"] = logging_analysis
        return logging_analysis
    
    def generate_trace_verification_script(self) -> str:
        """Generate script to verify trace ID propagation"""
        script = '''#!/usr/bin/env python3
"""
Trace ID Propagation Verification Script
Tests end-to-end trace ID flow through the system
"""

import requests
import uuid
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TRACE_ID = str(uuid.uuid4())

def test_trace_propagation():
    """Test trace ID propagation through various endpoints"""
    
    headers = {
        "X-Trace-ID": TRACE_ID,
        "Content-Type": "application/json"
    }
    
    results = {
        "trace_id": TRACE_ID,
        "timestamp": datetime.now().isoformat(),
        "endpoints_tested": [],
        "propagation_success": [],
        "propagation_failures": []
    }
    
    # Test endpoints that should propagate trace ID
    test_endpoints = [
        ("POST", "/workspaces", {"name": "Test Workspace", "description": "Trace test"}),
        ("GET", "/workspaces", None),
        ("POST", "/api/director/analyze", {"workspace_id": "test-id"}),
        ("GET", "/api/agents", None),
        ("GET", "/api/tasks", None)
    ]
    
    for method, endpoint, data in test_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
            
            results["endpoints_tested"].append({
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code
            })
            
            # Check if trace ID is in response headers
            if "X-Trace-ID" in response.headers:
                if response.headers["X-Trace-ID"] == TRACE_ID:
                    results["propagation_success"].append(endpoint)
                else:
                    results["propagation_failures"].append({
                        "endpoint": endpoint,
                        "reason": "Different trace ID returned",
                        "returned_id": response.headers.get("X-Trace-ID")
                    })
            else:
                results["propagation_failures"].append({
                    "endpoint": endpoint,
                    "reason": "No trace ID in response"
                })
                
        except Exception as e:
            results["propagation_failures"].append({
                "endpoint": endpoint,
                "reason": f"Error: {str(e)}"
            })
    
    # Save results
    with open(f"trace_verification_{TRACE_ID[:8]}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"Trace ID Propagation Test Results")
    print(f"=================================")
    print(f"Trace ID: {TRACE_ID}")
    print(f"Endpoints tested: {len(results['endpoints_tested'])}")
    print(f"Successful propagations: {len(results['propagation_success'])}")
    print(f"Failed propagations: {len(results['propagation_failures'])}")
    
    if results['propagation_failures']:
        print("\\nFailures:")
        for failure in results['propagation_failures']:
            print(f"  - {failure['endpoint']}: {failure['reason']}")
    
    return results

if __name__ == "__main__":
    test_trace_propagation()
'''
        
        script_path = self.backend_path / "verify_trace_propagation.py"
        with open(script_path, 'w') as f:
            f.write(script)
        
        return str(script_path)
    
    def generate_log_extraction_script(self) -> str:
        """Generate script for log extraction and analysis"""
        script = '''#!/usr/bin/env python3
"""
Log Extraction and Analysis Script
Extracts and analyzes logs from various sources
"""

import os
import re
import json
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path

class LogAnalyzer:
    def __init__(self):
        self.logs = {
            "execution_logs": [],
            "thinking_process_steps": [],
            "file_logs": [],
            "combined_timeline": []
        }
        
    def extract_from_database(self):
        """Extract logs from database tables"""
        try:
            from database import supabase
            
            # Extract execution logs
            exec_logs = supabase.table("execution_logs").select("*").execute()
            self.logs["execution_logs"] = exec_logs.data or []
            
            # Extract thinking process steps if table exists
            try:
                thinking_logs = supabase.table("thinking_process_steps").select("*").execute()
                self.logs["thinking_process_steps"] = thinking_logs.data or []
            except:
                print("thinking_process_steps table not found")
                
        except Exception as e:
            print(f"Database extraction error: {e}")
    
    def extract_from_files(self, log_dir="./"):
        """Extract logs from log files"""
        log_patterns = {
            "error": re.compile(r'ERROR.*'),
            "warning": re.compile(r'WARNING.*'),
            "info": re.compile(r'INFO.*'),
            "trace_id": re.compile(r'(X-Trace-ID|trace_id|traceId):\s*([\\w-]+)'),
            "timestamp": re.compile(r'(\\d{4}-\\d{2}-\\d{2}[T\\s]\\d{2}:\\d{2}:\\d{2})')
        }
        
        for log_file in Path(log_dir).glob("*.log"):
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    log_entry = {
                        "file": str(log_file),
                        "line": line_num,
                        "content": line.strip()
                    }
                    
                    # Extract patterns
                    for pattern_name, pattern in log_patterns.items():
                        match = pattern.search(line)
                        if match:
                            log_entry[pattern_name] = match.group(0)
                    
                    self.logs["file_logs"].append(log_entry)
    
    def analyze_patterns(self):
        """Analyze log patterns and anomalies"""
        analysis = {
            "total_logs": len(self.logs["execution_logs"]) + len(self.logs["file_logs"]),
            "error_count": 0,
            "warning_count": 0,
            "trace_ids": set(),
            "duplicate_logs": [],
            "time_gaps": [],
            "error_patterns": Counter()
        }
        
        # Analyze execution logs
        seen_logs = defaultdict(list)
        for log in self.logs["execution_logs"]:
            key = f"{log.get('type')}:{log.get('content')}"
            seen_logs[key].append(log.get('created_at'))
            
            if log.get('type') == 'error':
                analysis["error_count"] += 1
                if 'content' in log:
                    error_msg = str(log['content']).get('error', '') if isinstance(log['content'], dict) else str(log['content'])
                    analysis["error_patterns"][error_msg[:50]] += 1
        
        # Find duplicates
        for key, timestamps in seen_logs.items():
            if len(timestamps) > 1:
                analysis["duplicate_logs"].append({
                    "log_key": key,
                    "count": len(timestamps),
                    "timestamps": timestamps[:5]  # First 5 occurrences
                })
        
        # Analyze file logs
        for log in self.logs["file_logs"]:
            if "error" in log:
                analysis["error_count"] += 1
            if "warning" in log:
                analysis["warning_count"] += 1
            if "trace_id" in log:
                analysis["trace_ids"].add(log["trace_id"])
        
        return analysis
    
    def generate_report(self):
        """Generate comprehensive log analysis report"""
        self.extract_from_database()
        self.extract_from_files()
        analysis = self.analyze_patterns()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_logs": analysis["total_logs"],
                "error_count": analysis["error_count"],
                "warning_count": analysis["warning_count"],
                "unique_trace_ids": len(analysis["trace_ids"])
            },
            "duplicates": analysis["duplicate_logs"][:10],  # Top 10 duplicates
            "top_errors": dict(analysis["error_patterns"].most_common(10)),
            "recommendations": []
        }
        
        # Add recommendations
        if analysis["error_count"] > 100:
            report["recommendations"].append("High error rate detected - investigate error patterns")
        if len(analysis["duplicate_logs"]) > 50:
            report["recommendations"].append("Many duplicate logs - consider deduplication")
        if len(analysis["trace_ids"]) == 0:
            report["recommendations"].append("No trace IDs found - implement trace ID propagation")
        
        # Save report
        with open(f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(json.dumps(report, indent=2))
        return report

if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.generate_report()
'''
        
        script_path = self.backend_path / "analyze_logs.py"
        with open(script_path, 'w') as f:
            f.write(script)
        
        return str(script_path)
    
    def generate_duplicate_detection_script(self) -> str:
        """Generate script to detect and analyze duplicates"""
        script = '''#!/usr/bin/env python3
"""
Duplicate Detection Script
Identifies duplicate code, functions, and database entries
"""

import os
import re
import ast
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class DuplicateDetector:
    def __init__(self, root_path="."):
        self.root_path = Path(root_path)
        self.duplicates = {
            "functions": defaultdict(list),
            "classes": defaultdict(list),
            "imports": defaultdict(list),
            "sql_tables": defaultdict(list),
            "file_hashes": defaultdict(list)
        }
    
    def hash_file_content(self, file_path: Path) -> str:
        """Generate hash of file content"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def extract_python_elements(self, file_path: Path):
        """Extract functions, classes, and imports from Python file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_signature = f"{node.name}({len(node.args.args)} args)"
                        self.duplicates["functions"][func_signature].append(str(file_path))
                    
                    elif isinstance(node, ast.ClassDef):
                        self.duplicates["classes"][node.name].append(str(file_path))
                    
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self.duplicates["imports"][alias.name].append(str(file_path))
                        else:
                            module = node.module or ""
                            for alias in node.names:
                                import_name = f"{module}.{alias.name}" if module else alias.name
                                self.duplicates["imports"][import_name].append(str(file_path))
                                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def extract_sql_elements(self, file_path: Path):
        """Extract table definitions from SQL files"""
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Extract table names
            table_matches = re.findall(
                r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
                content, re.IGNORECASE
            )
            
            for table in table_matches:
                self.duplicates["sql_tables"][table].append(str(file_path))
    
    def analyze_directory(self):
        """Analyze all files in directory"""
        # Analyze Python files
        for py_file in self.root_path.rglob("*.py"):
            if "test_env" not in str(py_file) and "venv" not in str(py_file):
                self.extract_python_elements(py_file)
                
                # Check for duplicate file content
                file_hash = self.hash_file_content(py_file)
                self.duplicates["file_hashes"][file_hash].append(str(py_file))
        
        # Analyze SQL files
        for sql_file in self.root_path.rglob("*.sql"):
            self.extract_sql_elements(sql_file)
    
    def generate_report(self) -> Dict:
        """Generate duplicate detection report"""
        self.analyze_directory()
        
        report = {
            "summary": {
                "duplicate_functions": 0,
                "duplicate_classes": 0,
                "duplicate_files": 0,
                "duplicate_sql_tables": 0
            },
            "details": {
                "functions": {},
                "classes": {},
                "identical_files": [],
                "sql_tables": {}
            }
        }
        
        # Process function duplicates
        for func, files in self.duplicates["functions"].items():
            if len(files) > 1:
                report["summary"]["duplicate_functions"] += 1
                report["details"]["functions"][func] = files
        
        # Process class duplicates
        for cls, files in self.duplicates["classes"].items():
            if len(files) > 1:
                report["summary"]["duplicate_classes"] += 1
                report["details"]["classes"][cls] = files
        
        # Process identical files
        for file_hash, files in self.duplicates["file_hashes"].items():
            if len(files) > 1:
                report["summary"]["duplicate_files"] += 1
                report["details"]["identical_files"].append({
                    "hash": file_hash,
                    "files": files
                })
        
        # Process SQL table duplicates
        for table, files in self.duplicates["sql_tables"].items():
            if len(files) > 1:
                report["summary"]["duplicate_sql_tables"] += 1
                report["details"]["sql_tables"][table] = files
        
        # Save report
        import json
        with open("duplicate_detection_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("Duplicate Detection Report")
        print("=========================")
        print(f"Duplicate functions: {report['summary']['duplicate_functions']}")
        print(f"Duplicate classes: {report['summary']['duplicate_classes']}")
        print(f"Identical files: {report['summary']['duplicate_files']}")
        print(f"Duplicate SQL tables: {report['summary']['duplicate_sql_tables']}")
        
        if report["details"]["functions"]:
            print("\\nTop duplicate functions:")
            for func, files in list(report["details"]["functions"].items())[:5]:
                print(f"  - {func}: {len(files)} occurrences")
        
        return report

if __name__ == "__main__":
    detector = DuplicateDetector()
    detector.generate_report()
'''
        
        script_path = self.backend_path / "detect_duplicates.py"
        with open(script_path, 'w') as f:
            f.write(script)
        
        return str(script_path)
    
    def run_full_audit(self):
        """Run complete system audit"""
        print("Starting comprehensive system audit...")
        
        # Run all analyses
        self.find_duplicate_test_files()
        self.analyze_functional_silos()
        self.check_trace_id_propagation()
        self.analyze_api_endpoints()
        self.analyze_database_schema()
        self.analyze_logging_consistency()
        
        # Generate scripts
        scripts_generated = {
            "trace_verification": self.generate_trace_verification_script(),
            "log_analysis": self.generate_log_extraction_script(),
            "duplicate_detection": self.generate_duplicate_detection_script()
        }
        
        self.audit_results["scripts_generated"] = scripts_generated
        
        # Save results
        with open("comprehensive_audit_results.json", "w") as f:
            json.dump(self.audit_results, f, indent=2)
        
        return self.audit_results

if __name__ == "__main__":
    auditor = SystemAuditor()
    results = auditor.run_full_audit()
    print(f"Audit complete. Results saved to comprehensive_audit_results.json")