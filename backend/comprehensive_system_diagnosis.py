#!/usr/bin/env python3
"""
Comprehensive System Diagnosis Script
Analyzes all system components and identifies residual issues
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SystemDiagnostics:
    """Complete system diagnostics analyzer"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.issues_found = []
        self.warnings = []
        self.successes = []
        
    async def run_diagnostics(self):
        """Run all diagnostic tests"""
        print("\n🔍 COMPREHENSIVE SYSTEM DIAGNOSIS")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Test categories
        await self.test_api_health()
        await self.test_database_schema()
        await self.test_task_executor()
        await self.test_recovery_system()
        await self.test_quota_tracking()
        await self.test_deliverables_pipeline()
        await self.test_websocket_connections()
        await self.test_memory_patterns()
        
        # Summary report
        self.print_summary()
        
    async def test_api_health(self):
        """Test API endpoints health"""
        print("\n📡 Testing API Health...")
        endpoints = [
            "/health",
            "/api/workspaces/",
            "/api/tasks/?workspace_id=f79d87cc-b61f-491d-9226-4220e39e71ad",
            "/api/agents/?workspace_id=f79d87cc-b61f-491d-9226-4220e39e71ad",
            "/api/deliverables/?workspace_id=f79d87cc-b61f-491d-9226-4220e39e71ad",
            "/api/unified-assets/f79d87cc-b61f-491d-9226-4220e39e71ad"
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        self.successes.append(f"✅ {endpoint}: OK")
                    else:
                        self.issues_found.append(f"❌ {endpoint}: Status {response.status_code}")
                except Exception as e:
                    self.issues_found.append(f"❌ {endpoint}: {str(e)}")
                    
    async def test_database_schema(self):
        """Test database schema issues"""
        print("\n🗄️ Testing Database Schema...")
        
        # Import database module
        try:
            from database import db
            
            # Test problematic queries
            test_queries = [
                ("tasks", ["id", "status", "error_message", "workspace_id"]),
                ("deliverables", ["id", "status", "transformed_content"]),
                ("workspace_insights", ["id", "title", "insight_type"])
            ]
            
            for table, fields in test_queries:
                try:
                    # Test field access
                    query = db.get_supabase().table(table).select(",".join(fields)).limit(1)
                    result = query.execute()
                    if result.data is not None:
                        self.successes.append(f"✅ Table '{table}' schema: OK")
                    else:
                        self.warnings.append(f"⚠️ Table '{table}': No data")
                except Exception as e:
                    if "schema cache" in str(e):
                        self.issues_found.append(f"❌ Schema cache error for '{table}': {fields}")
                    else:
                        self.issues_found.append(f"❌ Database error for '{table}': {str(e)}")
                        
        except ImportError as e:
            self.issues_found.append(f"❌ Cannot import database module: {e}")
            
    async def test_task_executor(self):
        """Test task executor status"""
        print("\n⚙️ Testing Task Executor...")
        
        try:
            # Check if executor is running
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/executor/status")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "running":
                        self.successes.append("✅ Task Executor: Running")
                    else:
                        self.warnings.append(f"⚠️ Task Executor: {data.get('status', 'unknown')}")
                else:
                    self.issues_found.append(f"❌ Task Executor endpoint: Status {response.status_code}")
        except Exception as e:
            self.warnings.append(f"⚠️ Task Executor check failed: {str(e)}")
            
    async def test_recovery_system(self):
        """Test autonomous recovery system"""
        print("\n🔄 Testing Recovery System...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Check recovery status
                response = await client.get(f"{self.base_url}/api/monitoring/recovery-status")
                if response.status_code == 200:
                    data = response.json()
                    active_recoveries = data.get("active_recoveries", 0)
                    if active_recoveries > 0:
                        self.warnings.append(f"⚠️ Active recoveries in progress: {active_recoveries}")
                    else:
                        self.successes.append("✅ Recovery System: No active recoveries")
                else:
                    self.warnings.append(f"⚠️ Recovery status endpoint: {response.status_code}")
        except Exception as e:
            self.warnings.append(f"⚠️ Recovery system check failed: {str(e)}")
            
    async def test_quota_tracking(self):
        """Test OpenAI quota tracking"""
        print("\n💰 Testing Quota Tracking...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/quota/status")
                if response.status_code == 200:
                    data = response.json()
                    usage = data.get("current_usage", 0)
                    limit = data.get("monthly_limit", 0)
                    if limit > 0:
                        percentage = (usage / limit) * 100
                        if percentage > 90:
                            self.issues_found.append(f"❌ Quota critical: {percentage:.1f}% used")
                        elif percentage > 75:
                            self.warnings.append(f"⚠️ Quota warning: {percentage:.1f}% used")
                        else:
                            self.successes.append(f"✅ Quota healthy: {percentage:.1f}% used")
                    else:
                        self.warnings.append("⚠️ Quota tracking not configured")
                else:
                    self.warnings.append(f"⚠️ Quota endpoint: Status {response.status_code}")
        except Exception as e:
            self.warnings.append(f"⚠️ Quota check failed: {str(e)}")
            
    async def test_deliverables_pipeline(self):
        """Test deliverables transformation pipeline"""
        print("\n📦 Testing Deliverables Pipeline...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/deliverables/?workspace_id=f79d87cc-b61f-491d-9226-4220e39e71ad"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        untransformed = sum(1 for d in data if not d.get("transformed_content"))
                        timeout_count = len([d for d in data if "timeout" in str(d.get("status", "")).lower()])
                        
                        if timeout_count > 0:
                            self.issues_found.append(f"❌ Deliverables with timeout: {timeout_count}")
                        if untransformed > 0:
                            self.warnings.append(f"⚠️ Untransformed deliverables: {untransformed}")
                        if timeout_count == 0 and untransformed == 0:
                            self.successes.append("✅ Deliverables pipeline: All transformed")
                    else:
                        self.successes.append("✅ Deliverables pipeline: No pending items")
                else:
                    self.issues_found.append(f"❌ Deliverables endpoint: Status {response.status_code}")
        except Exception as e:
            self.issues_found.append(f"❌ Deliverables check failed: {str(e)}")
            
    async def test_websocket_connections(self):
        """Test WebSocket connections"""
        print("\n🔌 Testing WebSocket Connections...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/websocket/status")
                if response.status_code == 200:
                    data = response.json()
                    active = data.get("active_connections", 0)
                    errors = data.get("recent_errors", 0)
                    
                    if errors > 0:
                        self.warnings.append(f"⚠️ WebSocket errors: {errors}")
                    self.successes.append(f"✅ WebSocket connections: {active} active")
                elif response.status_code == 404:
                    self.warnings.append("⚠️ WebSocket status endpoint not found")
                else:
                    self.warnings.append(f"⚠️ WebSocket endpoint: Status {response.status_code}")
        except Exception as e:
            self.warnings.append(f"⚠️ WebSocket check failed: {str(e)}")
            
    async def test_memory_patterns(self):
        """Test memory patterns and insights"""
        print("\n🧠 Testing Memory Patterns...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/workspace-insights/?workspace_id=f79d87cc-b61f-491d-9226-4220e39e71ad"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        pattern_count = len([i for i in data if i.get("insight_type") == "success_pattern"])
                        lesson_count = len([i for i in data if i.get("insight_type") == "failure_lesson"])
                        
                        self.successes.append(f"✅ Memory patterns: {pattern_count} success, {lesson_count} failure")
                    else:
                        self.warnings.append("⚠️ No memory patterns found")
                else:
                    self.warnings.append(f"⚠️ Insights endpoint: Status {response.status_code}")
        except Exception as e:
            self.warnings.append(f"⚠️ Memory patterns check failed: {str(e)}")
            
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        # Critical issues
        if self.issues_found:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues_found)}):")
            for issue in self.issues_found:
                print(f"  {issue}")
        else:
            print("\n✅ No critical issues found!")
            
        # Warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        # Successes
        print(f"\n✅ SUCCESSFUL CHECKS ({len(self.successes)}):")
        for success in self.successes[:5]:  # Show first 5
            print(f"  {success}")
        if len(self.successes) > 5:
            print(f"  ... and {len(self.successes) - 5} more")
            
        # Calculate health score
        total_checks = len(self.issues_found) + len(self.warnings) + len(self.successes)
        if total_checks > 0:
            health_score = (len(self.successes) / total_checks) * 100
            
            print("\n" + "=" * 80)
            print(f"🏥 SYSTEM HEALTH SCORE: {health_score:.1f}%")
            
            if health_score >= 90:
                print("✅ System is healthy and operational")
            elif health_score >= 70:
                print("⚠️ System operational with minor issues")
            else:
                print("❌ System has critical issues requiring attention")
                
        print("=" * 80)
        
        # Recommendations
        if self.issues_found or self.warnings:
            print("\n📝 RECOMMENDATIONS:")
            
            if any("schema cache" in str(i) for i in self.issues_found):
                print("  1. Schema cache errors detected - consider refreshing Supabase connection")
                
            if any("timeout" in str(i) for i in self.issues_found):
                print("  2. Transformation timeouts detected - check AI service availability")
                
            if any("Quota" in str(i) for i in self.issues_found + self.warnings):
                print("  3. Quota issues detected - monitor OpenAI usage")
                
            if any("WebSocket" in str(i) for i in self.warnings):
                print("  4. WebSocket issues detected - check real-time connections")
                
            if any("Recovery" in str(w) for w in self.warnings):
                print("  5. Active recoveries detected - monitor task completion")

async def main():
    """Run diagnostics"""
    diagnostics = SystemDiagnostics()
    await diagnostics.run_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())