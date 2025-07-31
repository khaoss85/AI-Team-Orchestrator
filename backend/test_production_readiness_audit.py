#!/usr/bin/env python3
"""
🔍 **PRODUCTION READINESS AUDIT**

Critical audit to identify all fallbacks, missing dependencies, and gaps
that prevent true production deployment. This is the REAL test.
"""

import asyncio
import logging
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionAudit:
    def __init__(self):
        self.critical_issues = []
        self.fallback_instances = []
        self.missing_dependencies = []
        self.integration_gaps = []
        
    def log_critical(self, component: str, issue: str, impact: str):
        """Log a critical production issue"""
        self.critical_issues.append({
            "component": component,
            "issue": issue,
            "impact": impact,
            "timestamp": datetime.now().isoformat()
        })
        
    def log_fallback(self, component: str, fallback_type: str, reason: str):
        """Log a fallback activation"""
        self.fallback_instances.append({
            "component": component,
            "fallback_type": fallback_type,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
    def log_missing_dependency(self, dependency: str, required_by: str):
        """Log a missing dependency"""
        self.missing_dependencies.append({
            "dependency": dependency,
            "required_by": required_by,
            "timestamp": datetime.now().isoformat()
        })

async def audit_production_readiness():
    """🔍 Comprehensive production readiness audit"""
    
    audit = ProductionAudit()
    
    print("\n" + "="*80)
    print("🔍 PRODUCTION READINESS AUDIT")
    print("="*80)
    
    # Audit 1: Agent SDK Configuration
    print("\n📋 Audit 1: Agent SDK Configuration...")
    
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        # Test real SDK agent creation
        test_agent_config = {
            "name": "TestAgent",
            "instructions": "Test agent for production audit",
        }
        
        try:
            from agents import Agent as OpenAIAgent
            sdk_agent = OpenAIAgent(**test_agent_config)
            print("✅ Agent SDK: Configuration valid")
        except Exception as e:
            audit.log_critical(
                "Agent SDK", 
                f"Agent creation failed: {e}",
                "All AI calls will use fallback instead of real SDK"
            )
            print(f"❌ Agent SDK: {e}")
            
    except Exception as e:
        audit.log_critical("Agent SDK", f"SDK not available: {e}", "Complete AI functionality compromise")
        print(f"❌ Agent SDK: Not available - {e}")
    
    # Audit 2: Pipeline Dependencies
    print("\n📋 Audit 2: Pipeline Dependencies...")
    
    missing_modules = []
    required_modules = [
        ("backend.services", "RealToolIntegrationPipeline"),
        ("project_agents", "UniversalAIPipelineEngine"),
        ("services.sdk_memory_bridge", "HolisticMemoryManager"),
        ("models", "MemoryQueryResponse")
    ]
    
    for module_name, used_by in required_modules:
        try:
            __import__(module_name)
            print(f"✅ Dependency: {module_name}")
        except ImportError as e:
            audit.log_missing_dependency(module_name, used_by)
            missing_modules.append(module_name)
            print(f"❌ Missing: {module_name} (required by {used_by})")
    
    # Audit 3: Database Integration
    print("\n📋 Audit 3: Database Integration...")
    
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Test UUID handling
        try:
            import uuid
            test_uuid = str(uuid.uuid4())
            print(f"✅ Database: UUID generation working ({test_uuid[:8]}...)")
        except Exception as e:
            audit.log_critical("Database", f"UUID handling failed: {e}", "Memory storage will fail")
            print(f"❌ Database: UUID issue - {e}")
            
        # Test memory table structure
        try:
            # Test if memory tables exist and have correct structure
            response = supabase.table("memory_context_entries").select("id").limit(1).execute()
            print("✅ Database: Memory tables accessible")
        except Exception as e:
            audit.log_critical("Database", f"Memory tables issue: {e}", "Memory persistence broken")
            print(f"❌ Database: Memory tables - {e}")
            
    except Exception as e:
        audit.log_critical("Database", f"Database connection failed: {e}", "Complete data persistence failure")
        print(f"❌ Database: Connection failed - {e}")
    
    # Audit 4: Tool Integration Completeness
    print("\n📋 Audit 4: Tool Integration...")
    
    try:
        from tools.openai_sdk_tools import openai_tools_manager
        from tools.registry import tool_registry
        
        # Check if tools are actually executable
        sdk_tools = openai_tools_manager.get_all_tools()
        tool_descriptions = openai_tools_manager.get_tool_descriptions()
        
        print(f"✅ Tools: {len(tool_descriptions)} SDK tools available")
        
        # Test if tools can actually be executed
        try:
            test_result = await openai_tools_manager.execute_tool(
                "web_search", 
                {"query": "test"}, 
                {"workspace_id": "test"}
            )
            if test_result.get("success"):
                print("✅ Tools: Execution working")
            else:
                audit.log_critical("Tools", "Tool execution failed", "Tools available but not functional")
                print(f"❌ Tools: Execution failed - {test_result.get('error')}")
        except Exception as e:
            audit.log_critical("Tools", f"Tool execution error: {e}", "Tools not executable")
            print(f"❌ Tools: Execution error - {e}")
            
    except Exception as e:
        audit.log_critical("Tools", f"Tool system failed: {e}", "No tools available")
        print(f"❌ Tools: System failed - {e}")
    
    # Audit 5: Memory System Integration
    print("\n📋 Audit 5: Memory System Integration...")
    
    try:
        from services.holistic_memory_manager import get_holistic_memory_manager
        
        memory_manager = get_holistic_memory_manager()
        
        # Count available memory systems
        available_systems = len(memory_manager.memory_engines)
        expected_systems = 4  # unified, similarity, workspace, sdk
        
        print(f"📊 Memory Systems: {available_systems}/{expected_systems} integrated")
        
        if available_systems < expected_systems:
            missing_systems = expected_systems - available_systems
            audit.log_integration_gap(
                f"Memory Systems Incomplete",
                f"{missing_systems} memory systems missing",
                "Fragmented memory management"
            )
            
        # Test actual memory operations without errors
        try:
            from services.holistic_memory_manager import MemoryType, MemoryScope
            test_memory_id = await memory_manager.store_memory(
                content={"test": "production_audit"},
                memory_type=MemoryType.EXPERIENCE,
                scope=MemoryScope.WORKSPACE,
                workspace_id=str(uuid.uuid4()),  # Use proper UUID
                confidence=0.9
            )
            
            if test_memory_id and "error" not in str(test_memory_id).lower():
                print("✅ Memory: Storage working without errors")
            else:
                audit.log_critical("Memory", "Storage failed or errored", "Memory persistence unreliable")
                print(f"❌ Memory: Storage issue - {test_memory_id}")
                
        except Exception as e:
            audit.log_critical("Memory", f"Memory operations failed: {e}", "Memory system not functional")
            print(f"❌ Memory: Operations failed - {e}")
            
    except Exception as e:
        audit.log_critical("Memory", f"Memory system initialization failed: {e}", "No memory capabilities")
        print(f"❌ Memory: System failed - {e}")
    
    # Audit 6: End-to-End Flow Without Fallbacks
    print("\n📋 Audit 6: End-to-End Flow...")
    
    try:
        from services.real_tool_integration_pipeline import real_tool_integration_pipeline
        
        # This should work without ANY fallbacks in production
        tools = await real_tool_integration_pipeline._get_available_tools_dynamically()
        
        # Check if any fallback indicators
        fallback_indicators = []
        for tool in tools:
            if isinstance(tool, dict):
                if tool.get("source") == "fallback":
                    fallback_indicators.append(tool["name"])
        
        if fallback_indicators:
            audit.log_fallback(
                "Tool Discovery",
                "Fallback tools active",
                f"Using fallback for: {fallback_indicators}"
            )
            print(f"⚠️ Flow: Fallback tools detected - {fallback_indicators}")
        else:
            print("✅ Flow: No fallback tools detected")
            
        # Test actual tool requirements analysis
        try:
            required_tools = await real_tool_integration_pipeline._ai_determine_required_tools(
                task_name="Production Test",
                task_objective="Test production readiness",
                business_context={"workspace_id": str(uuid.uuid4()), "test": True}
            )
            
            if isinstance(required_tools, list) and len(required_tools) > 0:
                print("✅ Flow: Tool requirements analysis working")
            else:
                audit.log_critical(
                    "Pipeline Flow",
                    "Tool requirements analysis failed",
                    "Pipeline cannot determine required tools"
                )
                print("❌ Flow: Tool requirements analysis failed")
                
        except Exception as e:
            if "fallback" in str(e).lower():
                audit.log_fallback("Pipeline", "AI analysis fallback", str(e))
                print(f"⚠️ Flow: Using fallback for AI analysis - {e}")
            else:
                audit.log_critical("Pipeline", f"Tool analysis failed: {e}", "Pipeline broken")
                print(f"❌ Flow: Tool analysis failed - {e}")
            
    except Exception as e:
        audit.log_critical("Pipeline", f"Pipeline initialization failed: {e}", "Complete pipeline failure")
        print(f"❌ Flow: Pipeline failed - {e}")
    
    # Generate Production Readiness Report
    print("\n" + "="*80)
    print("📊 PRODUCTION READINESS ASSESSMENT")
    print("="*80)
    
    # Critical Issues
    if audit.critical_issues:
        print(f"\n🚨 CRITICAL ISSUES ({len(audit.critical_issues)}):")
        for issue in audit.critical_issues:
            print(f"❌ {issue['component']}: {issue['issue']}")
            print(f"   Impact: {issue['impact']}")
    else:
        print("\n✅ No critical issues found")
    
    # Fallback Instances
    if audit.fallback_instances:
        print(f"\n⚠️ ACTIVE FALLBACKS ({len(audit.fallback_instances)}):")
        for fallback in audit.fallback_instances:
            print(f"⚠️ {fallback['component']}: {fallback['fallback_type']}")
            print(f"   Reason: {fallback['reason']}")
    else:
        print("\n✅ No fallbacks detected")
    
    # Missing Dependencies
    if audit.missing_dependencies:
        print(f"\n📦 MISSING DEPENDENCIES ({len(audit.missing_dependencies)}):")
        for dep in audit.missing_dependencies:
            print(f"📦 {dep['dependency']} (required by {dep['required_by']})")
    else:
        print("\n✅ All dependencies available")
    
    # Production Readiness Score
    total_issues = len(audit.critical_issues) + len(audit.fallback_instances) + len(audit.missing_dependencies)
    
    if total_issues == 0:
        readiness_score = 100
        readiness_level = "PRODUCTION READY"
        readiness_emoji = "🎉"
    elif total_issues <= 2:
        readiness_score = 85
        readiness_level = "NEAR PRODUCTION READY"
        readiness_emoji = "⚠️"
    elif total_issues <= 5:
        readiness_score = 60
        readiness_level = "DEVELOPMENT READY"
        readiness_emoji = "🔧"
    else:
        readiness_score = 30
        readiness_level = "NOT PRODUCTION READY"
        readiness_emoji = "❌"
    
    print(f"\n{readiness_emoji} PRODUCTION READINESS: {readiness_level}")
    print(f"📊 Readiness Score: {readiness_score}/100")
    print(f"🐛 Total Issues: {total_issues}")
    
    print("="*80)
    
    return readiness_score >= 90, audit

# Add missing method to ProductionAudit class
def log_integration_gap(self, gap_type: str, description: str, impact: str):
    """Log an integration gap"""
    self.integration_gaps.append({
        "gap_type": gap_type,
        "description": description,
        "impact": impact,
        "timestamp": datetime.now().isoformat()
    })

# Monkey patch the method
ProductionAudit.log_integration_gap = log_integration_gap

async def main():
    """Main audit execution"""
    is_production_ready, audit_results = await audit_production_readiness()
    
    if is_production_ready:
        logger.info("🎉 System is PRODUCTION READY!")
        return True
    else:
        logger.error("❌ System is NOT production ready - issues must be fixed")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)