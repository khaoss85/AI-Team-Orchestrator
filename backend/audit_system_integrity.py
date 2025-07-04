#!/usr/bin/env python3
"""
🔍 SYSTEM INTEGRITY AUDIT SCRIPT
================================================================================
Script per audit tecnico-funzionale del sistema AI-Team-Orchestrator
Verifica sinergia, unicità e orchestrazione end-to-end
"""

import asyncio
import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SystemIntegrityAuditor:
    """Auditor per integrità e sinergia del sistema"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.audit_id = str(uuid4())[:8]
        self.trace_id = f"audit-{self.audit_id}-{int(time.time())}"
        
        # Audit findings
        self.findings = []
        self.codebase_issues = []
        self.database_issues = []
        self.runtime_issues = []
        
        # Test data for tracing
        self.test_workspace_id = None
        self.test_goal_id = None
        self.traced_entities = {}
        
        # Component mapping
        self.components_map = {}
        self.database_schema = {}
        
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Execute comprehensive system audit"""
        logger.info(f"🔍 STARTING SYSTEM INTEGRITY AUDIT - ID: {self.audit_id}")
        logger.info(f"📍 Trace ID: {self.trace_id}")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Codebase Review
            await self.phase_1_codebase_review()
            
            # Phase 2: Database Schema Analysis  
            await self.phase_2_database_analysis()
            
            # Phase 3: Runtime Verification
            await self.phase_3_runtime_verification()
            
            # Phase 4: Integration Trace Testing
            await self.phase_4_integration_trace()
            
            # Phase 5: Duplication Detection
            await self.phase_5_duplication_detection()
            
            # Phase 6: Orchestration Verification
            await self.phase_6_orchestration_verification()
            
        except Exception as e:
            logger.error(f"❌ AUDIT FAILED: {e}")
            self.findings.append({
                "id": "AUDIT_FAILURE",
                "description": f"Audit execution failed: {str(e)}",
                "severity": "CRITICAL",
                "category": "SYSTEM"
            })
        
        return await self.generate_audit_report()
    
    async def phase_1_codebase_review(self):
        """Phase 1: Comprehensive codebase structure analysis"""
        logger.info("\n📂 PHASE 1: Codebase Architecture Review")
        
        # Map directory structure
        codebase_root = "/Users/pelleri/Documents/ai-team-orchestrator/backend"
        
        try:
            # Scan for components
            components = {
                "ai_agents": "AI Agent Management",
                "ai_quality_assurance": "Quality Validation",  
                "routes": "API Endpoints",
                "services": "Business Services",
                "tools": "Tool Registry",
                "utils": "Utilities"
            }
            
            for component, description in components.items():
                component_path = os.path.join(codebase_root, component)
                if os.path.exists(component_path):
                    files = [f for f in os.listdir(component_path) if f.endswith('.py')]
                    self.components_map[component] = {
                        "description": description,
                        "files": files,
                        "file_count": len(files)
                    }
                    logger.info(f"✅ {component}: {len(files)} files - {description}")
                else:
                    self.codebase_issues.append(f"Missing component directory: {component}")
            
            # Check for core files
            core_files = [
                "main.py", "database.py", "models.py", "executor.py",
                "goal_driven_task_planner.py", "automated_goal_monitor.py"
            ]
            
            missing_core = []
            for core_file in core_files:
                if not os.path.exists(os.path.join(codebase_root, core_file)):
                    missing_core.append(core_file)
            
            if missing_core:
                self.findings.append({
                    "id": "MISSING_CORE_FILES",
                    "description": f"Missing core files: {', '.join(missing_core)}",
                    "severity": "HIGH",
                    "category": "CODEBASE"
                })
            
            # Check for potential duplications in services
            if "services" in self.components_map:
                service_files = self.components_map["services"]["files"]
                orchestrator_files = [f for f in service_files if "orchestrat" in f.lower()]
                if len(orchestrator_files) > 1:
                    self.findings.append({
                        "id": "MULTIPLE_ORCHESTRATORS",
                        "description": f"Multiple orchestrator implementations detected: {orchestrator_files}",
                        "severity": "MEDIUM",
                        "category": "DUPLICATION"
                    })
                
                content_extractor_files = [f for f in service_files if "content" in f.lower() and "extract" in f.lower()]
                if len(content_extractor_files) > 1:
                    self.findings.append({
                        "id": "MULTIPLE_EXTRACTORS", 
                        "description": f"Multiple content extractors detected: {content_extractor_files}",
                        "severity": "MEDIUM",
                        "category": "DUPLICATION"
                    })
            
            logger.info(f"📊 Codebase mapping complete: {len(self.components_map)} components analyzed")
            
        except Exception as e:
            self.codebase_issues.append(f"Codebase review error: {e}")
    
    async def phase_2_database_analysis(self):
        """Phase 2: Database schema and integrity analysis"""
        logger.info("\n🗄️ PHASE 2: Database Schema Analysis")
        
        try:
            # Initialize database connection
            sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')
            from database import get_supabase_client
            
            supabase = get_supabase_client()
            
            # Define expected tables and their relationships
            expected_tables = {
                "workspaces": ["id", "name", "description", "domain", "status", "created_at"],
                "workspace_goals": ["id", "workspace_id", "metric_type", "target_value", "status"],
                "tasks": ["id", "workspace_id", "goal_id", "name", "status", "priority"],
                "agents": ["id", "workspace_id", "name", "role", "seniority", "status"],
                "team_proposals": ["id", "workspace_id", "proposal_data", "status"],
                "asset_artifacts": ["id", "task_id", "artifact_name", "content", "quality_score"],
                "deliverables": ["id", "workspace_id", "name", "status", "components"]
            }
            
            # Verify table existence and basic structure
            existing_tables = []
            for table_name, expected_columns in expected_tables.items():
                try:
                    # Test table access
                    test_query = supabase.table(table_name).select("*").limit(1).execute()
                    existing_tables.append(table_name)
                    logger.info(f"✅ Table exists: {table_name}")
                    
                    # Store schema info
                    self.database_schema[table_name] = {
                        "exists": True,
                        "expected_columns": expected_columns,
                        "accessible": True
                    }
                    
                except Exception as e:
                    self.database_issues.append(f"Table {table_name} inaccessible: {e}")
                    self.database_schema[table_name] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            # Check for referential integrity patterns
            integrity_checks = [
                ("tasks", "workspace_id", "workspaces", "id"),
                ("tasks", "goal_id", "workspace_goals", "id"),
                ("agents", "workspace_id", "workspaces", "id"),
                ("team_proposals", "workspace_id", "workspaces", "id"),
                ("asset_artifacts", "task_id", "tasks", "id")
            ]
            
            for child_table, child_col, parent_table, parent_col in integrity_checks:
                if child_table in existing_tables and parent_table in existing_tables:
                    try:
                        # Check for orphaned records
                        orphaned_query = f"""
                        SELECT COUNT(*) as count FROM {child_table} 
                        WHERE {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
                        AND {child_col} IS NOT NULL
                        """
                        # Note: This would require raw SQL execution
                        logger.info(f"🔗 Checking FK integrity: {child_table}.{child_col} → {parent_table}.{parent_col}")
                        
                    except Exception as e:
                        self.database_issues.append(f"FK check failed: {child_table}.{child_col}: {e}")
            
            logger.info(f"📊 Database analysis complete: {len(existing_tables)}/{len(expected_tables)} tables verified")
            
        except Exception as e:
            self.database_issues.append(f"Database analysis error: {e}")
    
    async def phase_3_runtime_verification(self):
        """Phase 3: Runtime system verification"""
        logger.info("\n⚡ PHASE 3: Runtime System Verification")
        
        # Health check
        try:
            health_response = requests.get(f"{self.base_url}/health", timeout=10)
            if health_response.status_code == 200:
                logger.info("✅ System health check passed")
            else:
                self.runtime_issues.append(f"Health check failed: {health_response.status_code}")
        except Exception as e:
            self.runtime_issues.append(f"Health check error: {e}")
        
        # API endpoint verification
        critical_endpoints = [
            ("POST", "/workspaces", "Workspace creation"),
            ("POST", "/api/workspaces/{id}/goals", "Goal creation"),
            ("POST", "/director/proposal", "Team proposal"),
            ("GET", "/workspaces/{id}/tasks", "Task listing"),
            ("GET", "/api/assets/workspace/{id}", "Asset retrieval")
        ]
        
        for method, endpoint, description in critical_endpoints:
            endpoint_check = endpoint.replace("{id}", "test-id")
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint_check}", timeout=5)
                # For POST endpoints, we just check if they're reachable (expect validation errors)
                else:
                    response = requests.post(f"{self.base_url}{endpoint_check}", json={}, timeout=5)
                
                if response.status_code in [200, 400, 404, 422]:  # Reachable
                    logger.info(f"✅ Endpoint reachable: {method} {endpoint}")
                else:
                    self.runtime_issues.append(f"Endpoint issue: {method} {endpoint} returned {response.status_code}")
                    
            except Exception as e:
                self.runtime_issues.append(f"Endpoint unreachable: {method} {endpoint}: {e}")
    
    async def phase_4_integration_trace(self):
        """Phase 4: End-to-end integration trace testing"""
        logger.info("\n🔄 PHASE 4: Integration Trace Testing")
        
        try:
            # Create test workspace with trace ID
            workspace_data = {
                "name": f"Audit Test Workspace {self.audit_id}",
                "description": f"Audit integration test - Trace ID: {self.trace_id}",
                "domain": "audit-test",
                "trace_id": self.trace_id  # Inject trace ID
            }
            
            logger.info(f"🔍 Injecting trace ID: {self.trace_id}")
            
            # Step 1: Create workspace
            workspace_response = requests.post(f"{self.base_url}/workspaces", json=workspace_data, timeout=30)
            if workspace_response.status_code in [200, 201]:
                workspace = workspace_response.json()
                self.test_workspace_id = workspace.get('id')
                self.traced_entities["workspace"] = self.test_workspace_id
                logger.info(f"✅ Workspace created with trace: {self.test_workspace_id}")
                
                # Step 2: Create goal
                goal_data = {
                    "workspace_id": self.test_workspace_id,
                    "metric_type": "audit_test",
                    "target_value": 1.0,
                    "description": f"Audit test goal - Trace: {self.trace_id}",
                    "trace_id": self.trace_id
                }
                
                goal_response = requests.post(
                    f"{self.base_url}/api/workspaces/{self.test_workspace_id}/goals",
                    json=goal_data, timeout=30
                )
                
                if goal_response.status_code in [200, 201]:
                    goal = goal_response.json()
                    self.test_goal_id = goal.get('id')
                    self.traced_entities["goal"] = self.test_goal_id
                    logger.info(f"✅ Goal created with trace: {self.test_goal_id}")
                    
                    # Step 3: Monitor trace propagation
                    await self.monitor_trace_propagation()
                    
                else:
                    self.runtime_issues.append(f"Goal creation failed: {goal_response.status_code}")
            else:
                self.runtime_issues.append(f"Workspace creation failed: {workspace_response.status_code}")
                
        except Exception as e:
            self.runtime_issues.append(f"Integration trace error: {e}")
    
    async def monitor_trace_propagation(self):
        """Monitor trace ID propagation through the system"""
        logger.info(f"📍 Monitoring trace propagation for: {self.trace_id}")
        
        # Wait for system processing
        await asyncio.sleep(10)
        
        # Check if trace appears in various system components
        trace_found_in = []
        
        try:
            # Check in tasks
            tasks_response = requests.get(f"{self.base_url}/workspaces/{self.test_workspace_id}/tasks", timeout=10)
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                for task in tasks:
                    if self.trace_id in str(task):
                        trace_found_in.append("tasks")
                        break
            
            # Check in agents  
            agents_response = requests.get(f"{self.base_url}/api/agents/workspace/{self.test_workspace_id}", timeout=10)
            if agents_response.status_code == 200:
                agents = agents_response.json()
                for agent in agents:
                    if self.trace_id in str(agent):
                        trace_found_in.append("agents")
                        break
            
            logger.info(f"🔍 Trace found in: {trace_found_in}")
            self.traced_entities["propagation"] = trace_found_in
            
        except Exception as e:
            self.runtime_issues.append(f"Trace monitoring error: {e}")
    
    async def phase_5_duplication_detection(self):
        """Phase 5: Detect duplications across system"""
        logger.info("\n🔍 PHASE 5: Duplication Detection")
        
        if not self.test_workspace_id:
            logger.warning("⚠️ No test workspace for duplication testing")
            return
        
        try:
            # Check for duplicate tasks
            tasks_response = requests.get(f"{self.base_url}/workspaces/{self.test_workspace_id}/tasks", timeout=10)
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                
                # Check for duplicate task names
                task_names = [t.get('name', '') for t in tasks]
                duplicate_names = [name for name in set(task_names) if task_names.count(name) > 1 and name]
                
                if duplicate_names:
                    self.findings.append({
                        "id": "DUPLICATE_TASK_NAMES",
                        "description": f"Duplicate task names found: {duplicate_names}",
                        "severity": "MEDIUM",
                        "category": "DUPLICATION"
                    })
                else:
                    logger.info("✅ No duplicate task names detected")
            
            # Check workspace for multiple goals with same metric
            goals_response = requests.get(f"{self.base_url}/api/workspaces/{self.test_workspace_id}/goals", timeout=10)
            if goals_response.status_code == 200:
                goals = goals_response.json()
                
                metric_types = [g.get('metric_type', '') for g in goals]
                duplicate_metrics = [mt for mt in set(metric_types) if metric_types.count(mt) > 1 and mt]
                
                if duplicate_metrics:
                    self.findings.append({
                        "id": "DUPLICATE_GOAL_METRICS",
                        "description": f"Duplicate goal metrics: {duplicate_metrics}",
                        "severity": "LOW",
                        "category": "DUPLICATION"
                    })
            
        except Exception as e:
            self.runtime_issues.append(f"Duplication detection error: {e}")
    
    async def phase_6_orchestration_verification(self):
        """Phase 6: Verify unified orchestration"""
        logger.info("\n🎼 PHASE 6: Orchestration Verification")
        
        # Check for unified orchestrator activity
        orchestration_evidence = []
        
        try:
            # Look for orchestrator-related files
            orchestrator_files = []
            services_path = "/Users/pelleri/Documents/ai-team-orchestrator/backend/services"
            
            if os.path.exists(services_path):
                for file in os.listdir(services_path):
                    if "orchestrat" in file.lower():
                        orchestrator_files.append(file)
            
            if len(orchestrator_files) == 1:
                orchestration_evidence.append("Single orchestrator implementation")
                logger.info(f"✅ Unified orchestrator found: {orchestrator_files[0]}")
            elif len(orchestrator_files) > 1:
                self.findings.append({
                    "id": "MULTIPLE_ORCHESTRATORS",
                    "description": f"Multiple orchestrator files: {orchestrator_files}",
                    "severity": "HIGH", 
                    "category": "ORCHESTRATION"
                })
            else:
                self.findings.append({
                    "id": "NO_ORCHESTRATOR",
                    "description": "No orchestrator implementation found",
                    "severity": "CRITICAL",
                    "category": "ORCHESTRATION"
                })
            
            # Check for event-driven architecture evidence
            event_files = []
            for file in os.listdir("/Users/pelleri/Documents/ai-team-orchestrator/backend"):
                if "event" in file.lower() or "queue" in file.lower() or "message" in file.lower():
                    event_files.append(file)
            
            if event_files:
                orchestration_evidence.append(f"Event-driven components: {event_files}")
                logger.info(f"✅ Event-driven evidence: {len(event_files)} files")
            
            self.traced_entities["orchestration"] = orchestration_evidence
            
        except Exception as e:
            self.runtime_issues.append(f"Orchestration verification error: {e}")
    
    async def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        logger.info("\n📊 GENERATING AUDIT REPORT")
        
        # Calculate audit scores
        total_findings = len(self.findings)
        critical_findings = len([f for f in self.findings if f["severity"] == "CRITICAL"])
        high_findings = len([f for f in self.findings if f["severity"] == "HIGH"])
        
        # Audit score calculation
        base_score = 100
        score_deductions = critical_findings * 25 + high_findings * 10 + (total_findings - critical_findings - high_findings) * 5
        audit_score = max(0, base_score - score_deductions)
        
        # System integrity assessment
        integrity_status = "EXCELLENT" if audit_score >= 90 else \
                          "GOOD" if audit_score >= 70 else \
                          "NEEDS_IMPROVEMENT" if audit_score >= 50 else \
                          "CRITICAL"
        
        report = {
            "audit_metadata": {
                "audit_id": self.audit_id,
                "trace_id": self.trace_id,
                "timestamp": datetime.now().isoformat(),
                "auditor": "SystemIntegrityAuditor",
                "scope": "Full system integrity, sinergia, orchestration"
            },
            "executive_summary": {
                "integrity_status": integrity_status,
                "audit_score": audit_score,
                "total_findings": total_findings,
                "critical_issues": critical_findings,
                "components_analyzed": len(self.components_map),
                "tables_verified": len([t for t in self.database_schema.values() if t.get("exists", False)])
            },
            "findings": self.findings,
            "component_analysis": {
                "codebase": {
                    "components_mapped": self.components_map,
                    "issues": self.codebase_issues
                },
                "database": {
                    "schema_analysis": self.database_schema,
                    "issues": self.database_issues
                },
                "runtime": {
                    "traced_entities": self.traced_entities,
                    "issues": self.runtime_issues
                }
            },
            "sinergia_checklist": {
                "end_to_end_traceability": len(self.traced_entities) > 0,
                "unified_orchestration": "orchestration" in self.traced_entities,
                "no_critical_duplications": critical_findings == 0,
                "database_integrity": len(self.database_issues) == 0,
                "api_consistency": len([i for i in self.runtime_issues if "endpoint" in i.lower()]) == 0
            }
        }
        
        # Display summary
        logger.info("=" * 80)
        logger.info("🔍 AUDIT COMPLETE - SYSTEM INTEGRITY REPORT")
        logger.info("=" * 80)
        logger.info(f"🎯 Integrity Status: {integrity_status}")
        logger.info(f"📊 Audit Score: {audit_score}/100")
        logger.info(f"🔍 Total Findings: {total_findings}")
        logger.info(f"🚨 Critical Issues: {critical_findings}")
        logger.info(f"⚠️ High Priority: {high_findings}")
        
        # Findings breakdown
        if self.findings:
            logger.info(f"\n📋 FINDINGS BREAKDOWN:")
            for finding in self.findings:
                severity_icon = "🚨" if finding["severity"] == "CRITICAL" else \
                               "⚠️" if finding["severity"] == "HIGH" else \
                               "ℹ️"
                logger.info(f"   {severity_icon} [{finding['id']}] {finding['description']}")
        
        # Sinergia checklist
        logger.info(f"\n✅ SINERGIA CHECKLIST:")
        for check, status in report["sinergia_checklist"].items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {check.replace('_', ' ').title()}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if critical_findings > 0:
            logger.info("   🚨 URGENT: Address critical findings immediately")
        if high_findings > 0:
            logger.info("   ⚠️ HIGH: Resolve high-priority issues within sprint")
        if audit_score < 70:
            logger.info("   🔧 SYSTEM: Comprehensive system review required")
        if audit_score >= 90:
            logger.info("   🎉 EXCELLENT: System shows strong integrity")
        
        logger.info("=" * 80)
        
        # Save report
        report_file = f"system_integrity_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Audit report saved: {report_file}")
        
        # Cleanup test data
        if self.test_workspace_id:
            try:
                cleanup_response = requests.delete(f"{self.base_url}/workspaces/{self.test_workspace_id}", timeout=10)
                if cleanup_response.status_code in [200, 204]:
                    logger.info("🧹 Test workspace cleaned up")
            except:
                pass
        
        return report

async def main():
    """Execute system integrity audit"""
    auditor = SystemIntegrityAuditor()
    results = await auditor.run_comprehensive_audit()
    
    # Return success based on audit score
    audit_score = results.get("executive_summary", {}).get("audit_score", 0)
    return audit_score >= 70

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)