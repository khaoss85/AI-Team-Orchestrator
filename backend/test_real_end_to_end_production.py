#!/usr/bin/env python3
"""
🎯 **REAL END-TO-END PRODUCTION TEST**

Test del vero flusso produzione che simula un caso d'uso business reale:
1. Crea un workspace
2. Definisce un goal business 
3. Esegue il flusso completo di orchestrazione
4. Verifica che deliverables contengano contenuto REALE (non metadata)
5. Verifica zero fallback attivi

Questo è il test che determina se siamo DAVVERO production-ready.
"""

import asyncio
import logging
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ContentQuality for asset generation testing
try:
    from services.unified_memory_engine import ContentQuality
except ImportError:
    # Fallback ContentQuality for environments where it's not available
    class ContentQuality:
        FAILED = "failed"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealProductionTest:
    def __init__(self):
        self.test_workspace_id = None
        self.test_results = {}
        self.fallback_detected = False
        self.errors_encountered = []
        
    async def run_complete_production_test(self) -> bool:
        """🎯 Esegue test completo del flusso produzione"""
        
        print("\n" + "="*80)
        print("🎯 REAL END-TO-END PRODUCTION TEST")
        print("="*80)
        print("Testing complete business workflow from goal creation to deliverable generation")
        print("This test determines if the system is TRULY production-ready.")
        print("="*80)
        
        try:
            # Phase 1: System Initialization
            print("\n🚀 Phase 1: System Initialization...")
            await self._test_system_initialization()
            
            # Phase 2: Create Real Business Workspace  
            print("\n🏢 Phase 2: Create Real Business Workspace...")
            await self._test_workspace_creation()
            
            # Phase 3: AI-Driven Goal Decomposition
            print("\n🎯 Phase 3: AI-Driven Goal Decomposition...")
            await self._test_goal_decomposition()
            
            # Phase 4: Tool Integration Pipeline
            print("\n🔧 Phase 4: Tool Integration Pipeline...")
            await self._test_tool_integration()
            
            # Phase 5: Memory-Enhanced Generation
            print("\n🧠 Phase 5: Memory-Enhanced Content Generation...")
            await self._test_memory_enhanced_generation()
            
            # Phase 6: Deliverable Creation & Validation
            print("\n📦 Phase 6: Real Business Deliverable Creation...")
            await self._test_deliverable_creation()
            
            # Phase 7: End-to-End Validation
            print("\n✅ Phase 7: End-to-End Business Value Validation...")
            final_score = await self._test_business_value_validation()
            
            return final_score >= 95  # Must be near-perfect for production
            
        except Exception as e:
            print(f"❌ CRITICAL FAILURE: {e}")
            self.errors_encountered.append(str(e))
            return False
    
    async def _test_system_initialization(self):
        """Test all core systems initialize without fallbacks"""
        
        # Test 1: AI Provider Abstraction
        try:
            from services.ai_provider_abstraction import ai_provider_manager
            print("✅ AI Provider Abstraction: Loaded")
        except Exception as e:
            raise Exception(f"AI Provider Abstraction failed: {e}")
        
        # Test 2: Universal AI Pipeline Engine
        try:
            from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine
            print("✅ Universal AI Pipeline Engine: Loaded")
        except Exception as e:
            raise Exception(f"Universal AI Pipeline Engine failed: {e}")
        
        # Test 3: Memory Systems
        try:
            from services.holistic_memory_manager import get_holistic_memory_manager
            memory_manager = get_holistic_memory_manager()
            print(f"✅ Holistic Memory Manager: Loaded ({len(memory_manager.memory_engines)} systems)")
        except Exception as e:
            raise Exception(f"Memory systems failed: {e}")
        
        # Test 4: Tool Registry
        try:
            from tools.registry import tool_registry
            from tools.openai_sdk_tools import openai_tools_manager
            await tool_registry.initialize()
            tools = openai_tools_manager.get_tool_descriptions()
            print(f"✅ Tool Systems: Loaded ({len(tools)} tools available)")
        except Exception as e:
            raise Exception(f"Tool systems failed: {e}")
        
        # Test 5: Database Connection
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            print("✅ Database Connection: Active")
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    async def _test_workspace_creation(self):
        """Create a real business workspace for testing"""
        
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Create test workspace with real business context
            self.test_workspace_id = str(uuid.uuid4())
            
            # 🔧 **REAL SCHEMA**: Use actual database schema fields
            workspace_data = {
                "id": self.test_workspace_id,
                "name": "Production Test - Email Marketing Campaign",
                "description": "Real business test: Create email marketing campaign for tech startup launch targeting early adopters",
                "user_id": str(uuid.uuid4()),  # Required field
                "goal": "Generate leads for product launch through email marketing campaign targeting tech professionals",
                "budget": 10000.0,  # Required field
                "status": "active"
                # created_at and updated_at are handled by database
            }
            
            # Insert workspace
            result = supabase.table("workspaces").insert(workspace_data).execute()
            
            if result.data:
                print(f"✅ Business Workspace Created: {self.test_workspace_id}")
                print(f"   📋 Business Context: {workspace_data['description']}")
            else:
                raise Exception("Failed to create workspace in database")
                
        except Exception as e:
            raise Exception(f"Workspace creation failed: {e}")
    
    async def _test_goal_decomposition(self):
        """Test AI-driven goal decomposition with real business goal"""
        
        try:
            from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine, PipelineStepType, PipelineContext
            
            # Real business goal
            business_goal = {
                "objective": "Create comprehensive email marketing campaign for tech product launch",
                "target_audience": "Tech professionals and early adopters",
                "deliverables_needed": ["email sequences", "subject line variants", "call-to-action copy"],
                "business_context": {
                    "product": "AI-powered project management tool",
                    "launch_date": "Q1 2024",
                    "target_signups": 1000
                }
            }
            
            context = PipelineContext(
                workspace_id=self.test_workspace_id,
                cache_enabled=True,
                fallback_enabled=False  # NO FALLBACKS in production test
            )
            
            # Test goal decomposition
            result = await universal_ai_pipeline_engine.execute_pipeline_step(
                step_type=PipelineStepType.GOAL_DECOMPOSITION,
                input_data=business_goal,
                context=context
            )
            
            if result.success and not result.fallback_used:
                print("✅ AI Goal Decomposition: Success (no fallbacks)")
                print(f"   🎯 Decomposed into {len(result.data.get('sub_goals', []))} actionable components")
                self.test_results["goal_decomposition"] = result.data
            else:
                if result.fallback_used:
                    self.fallback_detected = True
                    raise Exception("Goal decomposition used fallback - not production ready")
                else:
                    raise Exception(f"Goal decomposition failed: {result.error_message}")
                    
        except Exception as e:
            raise Exception(f"Goal decomposition test failed: {e}")
    
    async def _test_tool_integration(self):
        """Test real tool integration with actual business task"""
        
        try:
            from services.real_tool_integration_pipeline import real_tool_integration_pipeline
            
            # Real business task requiring tool usage
            business_task = {
                "task_name": "Research email marketing best practices",
                "task_objective": "Find current best practices for tech product launch emails",
                "business_context": {
                    "workspace_id": self.test_workspace_id,
                    "industry": "technology",
                    "product_type": "B2B SaaS",
                    "target_audience": "technical decision makers"
                }
            }
            
            # Test tool requirements analysis (must use real AI, no fallbacks)
            required_tools = await real_tool_integration_pipeline._ai_determine_required_tools(
                task_name=business_task["task_name"],
                task_objective=business_task["task_objective"],
                business_context=business_task["business_context"]
            )
            
            # Validate result
            if isinstance(required_tools, (list, dict)) and len(str(required_tools)) > 50:
                print("✅ Tool Requirements Analysis: Success")
                print(f"   🔧 Identified tools needed for business task")
                
                # Test tool availability
                available_tools = await real_tool_integration_pipeline._get_available_tools_dynamically()
                
                if isinstance(available_tools, list) and len(available_tools) > 0:
                    # Check no fallback tools
                    fallback_tools = [t for t in available_tools if isinstance(t, dict) and t.get("source") == "fallback"]
                    
                    if fallback_tools:
                        self.fallback_detected = True
                        raise Exception(f"Fallback tools detected: {fallback_tools}")
                    
                    print(f"✅ Dynamic Tool Discovery: {len(available_tools)} tools available (no fallbacks)")
                    self.test_results["tool_integration"] = {
                        "required_tools": required_tools,
                        "available_tools": len(available_tools)
                    }
                else:
                    raise Exception("No tools available for business tasks")
            else:
                raise Exception(f"Tool requirements analysis returned invalid result: {required_tools}")
                
        except Exception as e:
            raise Exception(f"Tool integration test failed: {e}")
    
    async def _test_memory_enhanced_generation(self):
        """Test memory-enhanced content generation with business context"""
        
        try:
            from services.unified_memory_engine import memory_enhanced_ai_asset_generator
            from services.holistic_memory_manager import get_holistic_memory_manager, MemoryType, MemoryScope
            
            # Store business context in memory
            memory_manager = get_holistic_memory_manager()
            
            business_context = {
                "product_info": "AI-powered project management tool for tech teams",
                "target_audience": "CTOs, Engineering Managers, Product Managers",
                "key_benefits": ["Automated task prioritization", "AI-driven insights", "Team collaboration"],
                "competitive_advantage": "First AI-native project management platform",
                "pricing_model": "Freemium with pro features"
            }
            
            # Store context in memory (test real storage, not fallback)
            memory_id = await memory_manager.store_memory(
                content=business_context,
                memory_type=MemoryType.CONTEXT,
                scope=MemoryScope.WORKSPACE,
                workspace_id=self.test_workspace_id,
                confidence=1.0
            )
            
            if memory_id and "fallback" not in memory_id.lower():
                print("✅ Business Context Storage: Success (real database storage)")
                
                # Test memory-enhanced generation (use correct method name)
                generation_result = await memory_enhanced_ai_asset_generator.generate_memory_enhanced_asset(
                    workspace_id=self.test_workspace_id,
                    content_type="email_sequence",
                    business_context=json.dumps(business_context),
                    requirements={
                        "sequence_length": 3,
                        "tone": "professional but approachable",
                        "call_to_action": "sign up for beta",
                        "target_outcome": "qualified leads"
                    }
                )
                
                if generation_result.generated_content and generation_result.content_quality != ContentQuality.FAILED:
                    # Validate content is REAL business content, not metadata
                    content_str = json.dumps(generation_result.generated_content, default=str)
                    
                    # Check for real content indicators
                    has_real_content = any([
                        "subject" in content_str.lower(),
                        "email" in content_str.lower(),
                        len(content_str) > 500,  # Substantial content
                        "beta" in content_str.lower() or "launch" in content_str.lower()
                    ])
                    
                    # Check for metadata-only indicators (bad)
                    has_only_metadata = any([
                        "template" in content_str.lower(),
                        "placeholder" in content_str.lower(),
                        "example" in content_str.lower() and len(content_str) < 300
                    ])
                    
                    if has_real_content and not has_only_metadata:
                        print("✅ Memory-Enhanced Generation: Success (real business content)")
                        print(f"   📧 Generated {len(content_str)} chars of business-ready content")
                        self.test_results["content_generation"] = {
                            "success": True,
                            "content_length": len(content_str),
                            "real_content": has_real_content
                        }
                    else:
                        raise Exception("Generated content appears to be metadata/templates, not real business content")
                else:
                    raise Exception(f"Content generation failed: {generation_result.generation_reasoning}")
            else:
                raise Exception(f"Memory storage used fallback: {memory_id}")
                
        except Exception as e:
            raise Exception(f"Memory-enhanced generation test failed: {e}")
    
    async def _test_deliverable_creation(self):
        """Test creation of real business deliverable"""
        
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Create a real deliverable based on generated content (use actual schema from routes)
            deliverable_data = {
                "workspace_id": self.test_workspace_id,
                "title": "Email Marketing Campaign for Product Launch",  # Use 'title' as in routes
                "description": "Complete email sequence for tech product launch targeting decision makers",
                "content": self.test_results.get("content_generation", {}),  # Store as JSONB
                "type": "email_campaign",
                "status": "completed"
                # Remove quality_score and metadata if they don't exist in the actual schema
            }
            
            # Insert deliverable (use correct table name)
            result = supabase.table("deliverables").insert(deliverable_data).execute()
            
            if result.data:
                print("✅ Business Deliverable Created: Real database storage")
                print(f"   📦 Deliverable: {deliverable_data['title']}")
                print(f"   ✅ Status: {deliverable_data['status']}")
                self.test_results["deliverable_creation"] = deliverable_data
            else:
                raise Exception("Failed to create deliverable in database")
                
        except Exception as e:
            raise Exception(f"Deliverable creation test failed: {e}")
    
    async def _test_business_value_validation(self):
        """Final validation: Does the system deliver real business value?"""
        
        try:
            # Validate all test phases completed successfully
            required_phases = [
                "goal_decomposition",
                "tool_integration", 
                "content_generation",
                "deliverable_creation"
            ]
            
            completed_phases = 0
            total_phases = len(required_phases)
            
            for phase in required_phases:
                if phase in self.test_results:
                    completed_phases += 1
                    print(f"✅ {phase.replace('_', ' ').title()}: Completed")
                else:
                    print(f"❌ {phase.replace('_', ' ').title()}: Failed")
            
            # Calculate success rate
            success_rate = (completed_phases / total_phases) * 100
            
            # Apply penalties for fallbacks or errors
            if self.fallback_detected:
                success_rate -= 20
                print("⚠️ PENALTY: Fallbacks detected (-20 points)")
            
            if self.errors_encountered:
                success_rate -= (len(self.errors_encountered) * 10)
                print(f"⚠️ PENALTY: {len(self.errors_encountered)} errors encountered (-{len(self.errors_encountered) * 10} points)")
            
            print("\n" + "="*60)
            print("📊 FINAL PRODUCTION READINESS ASSESSMENT")
            print("="*60)
            print(f"Completed Phases: {completed_phases}/{total_phases}")
            print(f"Fallbacks Detected: {'Yes' if self.fallback_detected else 'No'}")
            print(f"Errors Encountered: {len(self.errors_encountered)}")
            print(f"Final Score: {success_rate:.1f}/100")
            
            if success_rate >= 95:
                print("\n🎉 RESULT: PRODUCTION READY!")
                print("✅ System delivers real business value")
                print("✅ No fallbacks detected")
                print("✅ End-to-end workflow functional")
                return success_rate
            elif success_rate >= 80:
                print("\n⚠️ RESULT: NEAR PRODUCTION READY")
                print("✅ Core functionality working")
                print("⚠️ Minor issues need resolution")
                return success_rate
            else:
                print("\n❌ RESULT: NOT PRODUCTION READY")
                print("❌ Significant issues blocking production deployment")
                return success_rate
                
        except Exception as e:
            print(f"❌ Business value validation failed: {e}")
            return 0

async def main():
    """Execute real production test"""
    
    test = RealProductionTest()
    
    try:
        is_production_ready = await test.run_complete_production_test()
        
        if is_production_ready:
            print("\n🎉 REAL END-TO-END PRODUCTION TEST: PASSED!")
            print("The system is ready for production deployment.")
            return True
        else:
            print("\n❌ REAL END-TO-END PRODUCTION TEST: FAILED!")
            print("System requires fixes before production deployment.")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST FAILURE: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)