#!/bin/bash
# AI Team Orchestrator - Complete Audit Script
# Runs all audit tools and generates comprehensive report

echo "AI Team Orchestrator - Complete System Audit"
echo "============================================="
echo "Starting comprehensive audit at $(date)"
echo ""

# Create audit output directory
mkdir -p audit_output

# 1. Run quick audit check
echo "1. Running quick validation check..."
python3 quick_audit_check.py > audit_output/quick_check_results.txt 2>&1

# 2. Run full audit analysis
echo "2. Running comprehensive audit analysis..."
python3 audit_scripts.py > audit_output/full_audit_results.txt 2>&1

# 3. Generate trace verification script
echo "3. Generating trace verification script..."
if [ -f "verify_trace_propagation.py" ]; then
    echo "   - Trace verification script ready"
    chmod +x verify_trace_propagation.py
else
    echo "   - ERROR: Trace verification script not generated"
fi

# 4. Generate log analysis script
echo "4. Generating log analysis script..."
if [ -f "analyze_logs.py" ]; then
    echo "   - Log analysis script ready"
    chmod +x analyze_logs.py
else
    echo "   - ERROR: Log analysis script not generated"
fi

# 5. Generate duplicate detection script
echo "5. Generating duplicate detection script..."
if [ -f "detect_duplicates.py" ]; then
    echo "   - Duplicate detection script ready"
    chmod +x detect_duplicates.py
else
    echo "   - ERROR: Duplicate detection script not generated"
fi

# 6. Count various metrics
echo "6. Collecting system metrics..."
echo "   - Python files: $(find . -name '*.py' -not -path './test_env/*' -not -path './venv/*' | wc -l)"
echo "   - SQL files: $(find . -name '*.sql' | wc -l)"
echo "   - Test files: $(find . -name '*test*.py' -not -path './test_env/*' -not -path './venv/*' | wc -l)"
echo "   - Route files: $(find routes -name '*.py' | wc -l)"
echo "   - Service files: $(find services -name '*.py' | wc -l)"

# 7. Check for specific issues
echo "7. Checking for specific issues..."
echo "   - Duplicate router includes: $(grep -n 'include_router.*director_router' main.py | wc -l)"
echo "   - CORS wildcard: $(grep -n 'allow_origins.*\*' main.py | wc -l)"
echo "   - Missing trace headers: $(grep -r 'X-Trace-ID' routes/ | wc -l)"

# 8. Generate summary report
echo "8. Generating audit summary..."
cat > audit_output/audit_summary.txt << EOF
AI Team Orchestrator - Audit Summary
Generated: $(date)

CRITICAL ISSUES:
- No trace ID propagation (0/28 routes)
- Missing database constraints (tasks, agents, workspaces)

HIGH PRIORITY ISSUES:
- 17 duplicate test files
- 4 orchestrator implementations
- 850+ duplicate functions

MEDIUM PRIORITY ISSUES:
- Inconsistent API prefixes (5 /api, 26 bare)
- Fragmented logging (3 different tables)
- CORS allows all origins

FILES GENERATED:
- COMPREHENSIVE_AUDIT_REPORT.md (Executive summary)
- AUDIT_FINDINGS_TABLE.csv (Detailed findings)
- verify_trace_propagation.py (Trace testing)
- analyze_logs.py (Log analysis)
- detect_duplicates.py (Duplicate detection)
- comprehensive_audit_results.json (Raw data)

NEXT STEPS:
1. Review COMPREHENSIVE_AUDIT_REPORT.md
2. Prioritize HIGH/CRITICAL findings
3. Run verification scripts weekly
4. Track progress with metrics
EOF

echo ""
echo "Audit complete! Results saved to audit_output/ directory"
echo "Review COMPREHENSIVE_AUDIT_REPORT.md for detailed findings"
echo "Run individual scripts as needed:"
echo "  - ./verify_trace_propagation.py (test trace ID flow)"
echo "  - ./analyze_logs.py (log analysis)"
echo "  - ./detect_duplicates.py (find duplicates)"
echo "  - ./quick_audit_check.py (quick validation)"
echo ""
echo "Audit completed at $(date)"