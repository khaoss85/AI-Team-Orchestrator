#!/usr/bin/env python3
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
            print("\nTop duplicate functions:")
            for func, files in list(report["details"]["functions"].items())[:5]:
                print(f"  - {func}: {len(files)} occurrences")
        
        return report

if __name__ == "__main__":
    detector = DuplicateDetector()
    detector.generate_report()
