#!/usr/bin/env python3
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
            "trace_id": re.compile(r'(X-Trace-ID|trace_id|traceId):\s*([\w-]+)'),
            "timestamp": re.compile(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})')
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
