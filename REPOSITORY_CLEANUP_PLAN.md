# Repository Cleanup Plan

## 🧹 Files to Remove (Temporary/Test Files)

### Root Level Test Files (Safe to Remove)
- `./check_specific_deliverable.py` - DB check script
- `./test_director_quick_domains.py` - Quick test
- `./test_team_frontend_issue.py` - Frontend test
- `./test_agent_description_prevention.py` - Agent test  
- `./check_goal_schema.py` - Schema check
- `./master_e2e_test_suite.py` - Old test suite
- `./fix_route_syntax_errors.py` - Route fix script
- `./test_specialist_document_access.py` - Document test
- `./test_deduplication_fix.py` - Dedup test
- `./test_pdf_content_15_pillars.py` - PDF test
- `./test_migration_readiness.py` - Migration test
- `./test_real_world_document_usage.py` - Document test
- `./check_completed_tasks.py` - Task check
- `./test_ai_dual_format.py` - Dual format test
- `./test_document_rag_integration.py` - RAG test
- `./test_pdf_rag_system.py` - PDF RAG test
- `./test_simple_rag_fallback.py` - RAG fallback test
- `./test_fixed_director_via_api.py` - Director API test
- `./test_director_api.py` - Director test
- `./fix_all_goal_deliverable_issues.py` - Fix script
- `./test_quota_simple.py` - Quota simple test

### Backend Test Files (Safe to Remove)
- `./backend/force_executor_test.py` - Executor test
- `./backend/direct_database_check.py` - DB check
- `./backend/extended_autonomous_test.py` - Extended test
- `./backend/comprehensive_system_integrity_check.py` - Integrity check
- `./backend/test_quota_integration_verification.py` - **KEEP - Recent quota test**

### Backend Fix Scripts (Safe to Remove)
- `./backend/fix_memory_patterns_schema.sql` - Schema fix
- `./backend/fix_deliverables_schema.sql` - Schema fix
- `./backend/manual_constraint_fix_steps.md` - Manual steps

## 📁 Documentation to Move to `docs/`

### Technical Reports (Move to `docs/reports/`)
- `./LEARNING_EXTRACTION_ANALYSIS.md`
- `./OPENAI_QUOTA_SYSTEM_COMPLIANCE_REPORT.md`
- `./GOAL_DELIVERABLE_CONTENT_FIX_REPORT.md`
- `./AUTO_RECOVERY_COMPLIANCE_REPORT.md`
- `./CRITICAL_GOAL_DELIVERABLE_MAPPING_ANALYSIS_20250904.md`
- `./HARD_CODING_DETECTION_REPORT.md`
- `./RAG_SYSTEM_STATUS.md`
- `./WORKSPACE_BLOCKING_ANALYSIS_REPORT.md`
- `./QUOTA_SYSTEM_VERIFICATION_REPORT.md`
- `./deliverable_fixes_test_summary.md`
- `./GOAL_PROGRESS_INVESTIGATION_COMPLETE.md`
- `./MEMORY_SYSTEM_DATABASE_AUDIT_REPORT.md`
- `./DIRECTOR_FIX_SUMMARY.md`
- `./USER_INSIGHTS_MANAGEMENT_SYSTEM.md`
- `./DOCUMENT_MANAGEMENT_SYSTEM_AUDIT.md`
- `./PILLAR_VIOLATION_REPORT_GOAL_DELIVERABLE_MAPPING.md`
- `./MEMORY_SYSTEM_ARCHITECTURE_ANALYSIS.md`
- `./PILLAR_COMPLIANCE_REPORT.md`

### Recent Quota System Documentation (Move to `docs/systems/`)
- `./BUDGET_USAGE_CHAT_FINAL_CERTIFICATION.md`
- `./BUDGET_USAGE_CHAT_TESTING_REPORT.md`
- `./QUOTA_TRACKING_PILLAR_ANALYSIS.md`

### Backend Documentation (Move to `docs/backend/`)
- `./backend/goal_deliverable_mapping_fix_report.md`

## ✅ Files to Keep

### Core Test Files (Keep)
- `./backend/test_quota_integration_verification.py` - Recent quota system test
- Any files actively used for CI/CD or production monitoring

### Core Documentation (Keep at Root)
- `./CLAUDE.md` - Main configuration
- `./README.md` - Project readme

## 🎯 Cleanup Strategy

1. Create `docs/` structure with subdirectories
2. Move documentation to appropriate `docs/` subdirectories  
3. Remove temporary test and fix files
4. Update any references to moved files
5. Create final cleanup commit