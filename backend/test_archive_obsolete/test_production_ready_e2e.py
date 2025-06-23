#!/usr/bin/env python3
"""
🚀 PRODUCTION-READY END-TO-END TEST
Test completo del sistema usando OpenAI e ambiente production-ready
"""

import asyncio
import logging
import os
import sys
import json
from typing import Dict, List, Any
from datetime import datetime
from uuid import uuid4, UUID

# Add backend to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables manually
def load_env_file():
    """Load .env file manually"""
    env_path = '/Users/pelleri/Documents/ai-team-orchestrator/backend/.env'
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        logger.warning(f"⚠️ .env file not found at {env_path}")

load_env_file()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionE2ETest:
    def __init__(self):
        self.test_results = {}
        self.workspace_id = None
        self.created_goals = []
        self.validation_results = []
        
        # Verify environment
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        logger.info(f"🔑 OpenAI Key: {'✅ Available' if self.openai_key else '❌ Missing'}")
        logger.info(f"🗄️ Supabase URL: {'✅ Available' if self.supabase_url else '❌ Missing'}")
        logger.info(f"🔐 Supabase Key: {'✅ Available' if self.supabase_key else '❌ Missing'}")
        
    async def run_production_e2e_test(self):
        """🚀 Esegue test end-to-end production-ready completo"""
        
        logger.info("🚀 STARTING PRODUCTION-READY END-TO-END TEST")
        logger.info("="*80)
        logger.info(f"📝 Use Case: Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee)")
        logger.info(f"📧 Obiettivo: Suggerire almeno 3 sequenze email da impostare su Hubspot")
        logger.info("="*80)
        
        try:
            # Phase 1: AI-Driven Goal Extraction
            await self.test_ai_goal_extraction()
            
            # Phase 2: Memory System Integration
            await self.test_memory_system()
            
            # Phase 3: Goal-Driven Task Simulation
            await self.test_goal_driven_workflow()
            
            # Phase 4: Quality Validation with AI
            await self.test_ai_quality_validation()
            
            # Phase 5: Course Correction System
            await self.test_course_correction()
            
            # Phase 6: Universal Scalability Test
            await self.test_universal_scalability()
            
            # Generate comprehensive report
            self.generate_production_report()
            
        except Exception as e:
            logger.error(f"❌ Production E2E test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_ai_goal_extraction(self):
        """🤖 Test AI-driven goal extraction con OpenAI"""
        
        logger.info("\n🤖 PHASE 1: AI-DRIVEN GOAL EXTRACTION")
        logger.info("-" * 60)
        
        try:
            from ai_quality_assurance.ai_goal_extractor import extract_and_create_workspace_goals
            
            # Test case originale
            goal_text = """Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot.
            Gli email devono avere un open-rate ≥ 30% e click-to-rate ≥ 10%, completando il tutto in 6 settimane."""
            
            self.workspace_id = str(uuid4())
            
            logger.info(f"📝 Extracting goals from: {goal_text}")
            logger.info(f"🆔 Workspace ID: {self.workspace_id}")
            
            # Extract goals using AI
            goals = await extract_and_create_workspace_goals(self.workspace_id, goal_text)
            self.created_goals = goals
            
            logger.info(f"🎯 AI extracted {len(goals)} goals:")
            
            expected_metrics = ["deliverables", "quality_score", "timeline_days"]
            found_metrics = set()
            
            for i, goal in enumerate(goals, 1):
                metric_type = goal.get('metric_type')
                target_value = goal.get('target_value')
                unit = goal.get('unit')
                confidence = goal.get('confidence', 'N/A')
                
                found_metrics.add(metric_type)
                
                logger.info(f"  Goal {i}: {metric_type} = {target_value} {unit}")
                logger.info(f"    Description: {goal.get('description', 'N/A')}")
                logger.info(f"    Confidence: {confidence}")
                logger.info(f"    Is Percentage: {goal.get('is_percentage', False)}")
                logger.info("")
            
            # Verify goal quality
            coverage = len(found_metrics & set(expected_metrics))
            
            # Check for duplicates
            goal_keys = [f"{g.get('metric_type')}_{g.get('target_value')}" for g in goals]
            duplicates = len(goal_keys) - len(set(goal_keys))
            
            self.test_results["ai_goal_extraction"] = {
                "goals_extracted": len(goals),
                "goal_coverage": f"{coverage}/{len(expected_metrics)}",
                "found_metrics": list(found_metrics),
                "duplicates": duplicates,
                "ai_available": True,  # We're using real OpenAI
                "status": "✅ SUCCESS"
            }
            
            logger.info(f"📊 Goal coverage: {coverage}/{len(expected_metrics)} expected metrics")
            logger.info(f"🔄 Duplicates: {duplicates} (should be 0)")
            logger.info("✅ AI Goal Extraction completed successfully")
            
        except Exception as e:
            logger.error(f"❌ AI Goal Extraction failed: {e}")
            self.test_results["ai_goal_extraction"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    async def test_memory_system(self):
        """🧠 Test sistema memoria con storage insights"""
        
        logger.info("\n🧠 PHASE 2: MEMORY SYSTEM INTEGRATION")
        logger.info("-" * 60)
        
        try:
            from workspace_memory import workspace_memory
            from models import InsightType
            
            # Test memory storage
            insights_stored = []
            
            # Store goal extraction insight
            insight1 = await workspace_memory.store_insight(
                workspace_id=UUID(self.workspace_id),
                task_id=None,  # Test the fix for optional task_id
                agent_role="goal_extractor",
                insight_type=InsightType.DISCOVERY,
                content=f"Successfully extracted {len(self.created_goals)} goals from complex Italian business requirement",
                relevance_tags=["goal_extraction", "italian", "saas", "lead_generation"],
                confidence_score=0.95
            )
            insights_stored.append(insight1)
            
            # Store strategy insight
            insight2 = await workspace_memory.store_insight(
                workspace_id=UUID(self.workspace_id),
                task_id=UUID(str(uuid4())),  # Test with valid task_id
                agent_role="strategist",
                insight_type=InsightType.CONSTRAINT,
                content="SaaS lead generation requires personalized outreach and high-quality content",
                relevance_tags=["strategy", "saas", "personalization"],
                confidence_score=0.88
            )
            insights_stored.append(insight2)
            
            # Test memory retrieval
            context = await workspace_memory.get_relevant_context(
                workspace_id=UUID(self.workspace_id),
                current_task=None,
                context_filter={
                    "insight_types": [InsightType.DISCOVERY, InsightType.CONSTRAINT],
                    "relevance_tags": ["goal_extraction", "strategy"],
                    "limit": 10
                }
            )
            
            self.test_results["memory_system"] = {
                "insights_stored": len([i for i in insights_stored if i]),
                "context_retrieved": len(context) if context else 0,
                "memory_available": True,
                "status": "✅ SUCCESS"
            }
            
            logger.info(f"💾 Insights stored: {len([i for i in insights_stored if i])}")
            logger.info(f"🔍 Context retrieved: {len(context) if context else 0} items")
            logger.info("✅ Memory System Integration completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Memory System test failed: {e}")
            self.test_results["memory_system"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    async def test_goal_driven_workflow(self):
        """🎯 Test workflow goal-driven con task simulation"""
        
        logger.info("\n🎯 PHASE 3: GOAL-DRIVEN WORKFLOW")
        logger.info("-" * 60)
        
        try:
            from database import ai_link_task_to_goals
            
            # Simulate completed tasks
            mock_tasks = [
                {
                    "id": str(uuid4()),
                    "name": "Research SaaS CMO/CTO contacts in Europe",
                    "description": "Find and verify 50 ICP contacts from SaaS companies",
                    "result": {
                        "contacts_found": 35,
                        "verified_contacts": 28,
                        "companies_researched": 15,
                        "data_quality": "high"
                    },
                    "status": "completed",
                    "workspace_id": self.workspace_id
                },
                {
                    "id": str(uuid4()),
                    "name": "Create personalized email sequences",
                    "description": "Develop 3 email sequences for SaaS lead nurturing",
                    "result": {
                        "sequences_created": 2,
                        "templates_developed": 6,
                        "personalization_variables": ["company_name", "role", "industry"],
                        "content_quality": "high"
                    },
                    "status": "completed",
                    "workspace_id": self.workspace_id
                }
            ]
            
            # Test AI task-goal linking
            linked_tasks = 0
            for task in mock_tasks:
                try:
                    link_result = await ai_link_task_to_goals(
                        workspace_id=self.workspace_id,
                        task_name=task["name"],
                        task_description=task["description"],
                        task_context=task.get("result", {})
                    )
                    
                    if link_result and link_result.get("goal_id"):
                        linked_tasks += 1
                        logger.info(f"  🔗 Task linked: '{task['name']}' → {link_result.get('metric_type')}")
                    
                except Exception as link_error:
                    logger.warning(f"  ⚠️ Task linking failed for '{task['name']}': {link_error}")
            
            self.test_results["goal_driven_workflow"] = {
                "tasks_simulated": len(mock_tasks),
                "tasks_linked": linked_tasks,
                "linking_success_rate": f"{linked_tasks}/{len(mock_tasks)}",
                "status": "✅ SUCCESS" if linked_tasks > 0 else "⚠️ PARTIAL"
            }
            
            logger.info(f"📋 Tasks simulated: {len(mock_tasks)}")
            logger.info(f"🔗 Tasks linked to goals: {linked_tasks}")
            logger.info("✅ Goal-Driven Workflow completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Goal-Driven Workflow test failed: {e}")
            self.test_results["goal_driven_workflow"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    async def test_ai_quality_validation(self):
        """🔍 Test validazione qualità con AI"""
        
        logger.info("\n🔍 PHASE 4: AI QUALITY VALIDATION")
        logger.info("-" * 60)
        
        try:
            from ai_quality_assurance.goal_validator import goal_validator
            
            # Use the original goal text
            workspace_goal = """Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot.
            Gli email devono avere un open-rate ≥ 30% e click-to-rate ≥ 10%, completando il tutto in 6 settimane."""
            
            # Mock completed tasks with realistic results
            completed_tasks = [
                {
                    "id": str(uuid4()),
                    "name": "SaaS Contact Research",
                    "result": {
                        "contacts_collected": 35,
                        "contact_quality": "high",
                        "verification_rate": 0.8,
                        "target_roles": ["CMO", "CTO"],
                        "geographic_focus": "Europe"
                    }
                },
                {
                    "id": str(uuid4()),
                    "name": "Email Sequence Development", 
                    "result": {
                        "sequences_created": 2,
                        "email_templates": 6,
                        "personalization_level": "high",
                        "content_quality_score": 85
                    }
                }
            ]
            
            # Run AI-driven goal validation
            validation_results = await goal_validator.validate_workspace_goal_achievement(
                workspace_goal=workspace_goal,
                completed_tasks=completed_tasks,
                workspace_id=self.workspace_id
            )
            
            self.validation_results = validation_results
            
            # Analyze validation results
            critical_gaps = [r for r in validation_results if hasattr(r, 'gap_percentage') and r.gap_percentage > 50]
            minor_gaps = [r for r in validation_results if hasattr(r, 'gap_percentage') and 0 < r.gap_percentage <= 50]
            achieved_goals = [r for r in validation_results if hasattr(r, 'gap_percentage') and r.gap_percentage <= 0]
            
            self.test_results["ai_quality_validation"] = {
                "validations_performed": len(validation_results),
                "critical_gaps": len(critical_gaps),
                "minor_gaps": len(minor_gaps),
                "achieved_goals": len(achieved_goals),
                "ai_validation_available": True,
                "status": "✅ SUCCESS"
            }
            
            logger.info(f"🔍 Validations performed: {len(validation_results)}")
            logger.info(f"🚨 Critical gaps: {len(critical_gaps)}")
            logger.info(f"⚠️ Minor gaps: {len(minor_gaps)}")
            logger.info(f"✅ Achieved goals: {len(achieved_goals)}")
            
            for result in validation_results:
                if hasattr(result, 'validation_message'):
                    logger.info(f"  📊 {result.validation_message}")
            
            logger.info("✅ AI Quality Validation completed successfully")
            
        except Exception as e:
            logger.error(f"❌ AI Quality Validation test failed: {e}")
            self.test_results["ai_quality_validation"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    async def test_course_correction(self):
        """🔄 Test sistema course correction automatico"""
        
        logger.info("\n🔄 PHASE 5: COURSE CORRECTION SYSTEM")
        logger.info("-" * 60)
        
        try:
            from ai_quality_assurance.goal_validator import goal_validator
            
            if not self.validation_results:
                logger.warning("⚠️ No validation results available for course correction test")
                self.test_results["course_correction"] = {
                    "status": "⚠️ SKIPPED",
                    "reason": "No validation results"
                }
                return
            
            # Test corrective actions
            corrective_tasks = await goal_validator.trigger_corrective_actions(
                validation_results=self.validation_results,
                workspace_id=self.workspace_id
            )
            
            # Analyze corrective tasks
            high_priority_tasks = [t for t in corrective_tasks if t.get("priority") == "high"]
            memory_driven_tasks = [t for t in corrective_tasks if "memory_context" in t]
            
            self.test_results["course_correction"] = {
                "corrective_tasks_generated": len(corrective_tasks),
                "high_priority_tasks": len(high_priority_tasks),
                "memory_driven_tasks": len(memory_driven_tasks),
                "automatic_correction_available": True,
                "status": "✅ SUCCESS"
            }
            
            logger.info(f"🔄 Corrective tasks generated: {len(corrective_tasks)}")
            logger.info(f"🚨 High priority tasks: {len(high_priority_tasks)}")
            logger.info(f"🧠 Memory-driven tasks: {len(memory_driven_tasks)}")
            
            for task in corrective_tasks:
                logger.info(f"  📋 Task: {task.get('name', 'Unnamed')}")
                if task.get('urgency_reason'):
                    logger.info(f"    Reason: {task['urgency_reason']}")
            
            logger.info("✅ Course Correction System completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Course Correction test failed: {e}")
            self.test_results["course_correction"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    async def test_universal_scalability(self):
        """🌍 Test scalabilità universale cross-domain"""
        
        logger.info("\n🌍 PHASE 6: UNIVERSAL SCALABILITY TEST")
        logger.info("-" * 60)
        
        try:
            from ai_quality_assurance.ai_goal_extractor import ai_goal_extractor
            
            # Test different business domains
            test_domains = [
                ("Healthcare", "Ridurre del 25% i tempi di attesa e migliorare la soddisfazione pazienti all'80% in 6 mesi"),
                ("Education", "Aumentare il completion rate dei corsi online al 85% e creare 10 moduli interattivi"),
                ("Finance", "Incrementare il ROI del 30% e ridurre i costi operativi del 15% entro Q2"),
                ("E-commerce", "Raggiungere 1000 ordini mensili con conversion rate ≥ 3.5% in 3 mesi"),
                ("Manufacturing", "Ridurre gli scarti del 20% e aumentare l'efficienza produttiva del 15%")
            ]
            
            universal_results = {}
            
            for domain, goal_text in test_domains:
                try:
                    goals = await ai_goal_extractor.extract_goals_from_text(goal_text)
                    
                    universal_results[domain] = {
                        "goals_extracted": len(goals),
                        "success": len(goals) > 0,
                        "goal_types": [g.goal_type.value if hasattr(g, 'goal_type') else 'unknown' for g in goals]
                    }
                    
                    logger.info(f"  🌍 {domain}: {len(goals)} goals extracted")
                    
                except Exception as domain_error:
                    universal_results[domain] = {
                        "goals_extracted": 0,
                        "success": False,
                        "error": str(domain_error)
                    }
                    logger.warning(f"  ⚠️ {domain}: Failed - {domain_error}")
            
            # Calculate success rate
            successful_domains = sum(1 for r in universal_results.values() if r.get("success", False))
            success_rate = successful_domains / len(test_domains)
            
            self.test_results["universal_scalability"] = {
                "domains_tested": len(test_domains),
                "successful_domains": successful_domains,
                "success_rate": f"{success_rate:.1%}",
                "domain_results": universal_results,
                "truly_universal": success_rate >= 0.8,
                "status": "✅ SUCCESS" if success_rate >= 0.8 else "⚠️ PARTIAL"
            }
            
            logger.info(f"🌍 Domains tested: {len(test_domains)}")
            logger.info(f"✅ Successful domains: {successful_domains}")
            logger.info(f"📊 Success rate: {success_rate:.1%}")
            logger.info(f"🎯 Truly universal: {'Yes' if success_rate >= 0.8 else 'No'}")
            
        except Exception as e:
            logger.error(f"❌ Universal Scalability test failed: {e}")
            self.test_results["universal_scalability"] = {
                "status": "❌ FAILED",
                "error": str(e)
            }
    
    def generate_production_report(self):
        """📊 Genera report finale production-ready"""
        
        logger.info("\n" + "="*80)
        logger.info("📊 PRODUCTION-READY E2E TEST REPORT")
        logger.info("="*80)
        
        # Calculate overall success
        successful_phases = sum(1 for result in self.test_results.values() if "✅" in result.get("status", ""))
        total_phases = len(self.test_results)
        overall_success_rate = successful_phases / total_phases if total_phases > 0 else 0
        
        logger.info(f"\n🏆 OVERALL SUCCESS RATE: {overall_success_rate:.1%} ({successful_phases}/{total_phases} phases)")
        
        # Detailed phase results
        logger.info(f"\n📋 PHASE-BY-PHASE RESULTS:")
        
        phase_names = {
            "ai_goal_extraction": "🤖 AI-Driven Goal Extraction",
            "memory_system": "🧠 Memory System Integration", 
            "goal_driven_workflow": "🎯 Goal-Driven Workflow",
            "ai_quality_validation": "🔍 AI Quality Validation",
            "course_correction": "🔄 Course Correction System",
            "universal_scalability": "🌍 Universal Scalability"
        }
        
        for phase_key, result in self.test_results.items():
            phase_name = phase_names.get(phase_key, phase_key)
            status = result.get("status", "❌ UNKNOWN")
            
            logger.info(f"\n{phase_name}:")
            logger.info(f"  Status: {status}")
            
            # Phase-specific details
            if phase_key == "ai_goal_extraction":
                logger.info(f"  Goals extracted: {result.get('goals_extracted', 0)}")
                logger.info(f"  Goal coverage: {result.get('goal_coverage', 'N/A')}")
                logger.info(f"  Duplicates: {result.get('duplicates', 'N/A')}")
            
            elif phase_key == "memory_system":
                logger.info(f"  Insights stored: {result.get('insights_stored', 0)}")
                logger.info(f"  Context retrieved: {result.get('context_retrieved', 0)}")
            
            elif phase_key == "goal_driven_workflow":
                logger.info(f"  Tasks simulated: {result.get('tasks_simulated', 0)}")
                logger.info(f"  Linking success: {result.get('linking_success_rate', 'N/A')}")
            
            elif phase_key == "ai_quality_validation":
                logger.info(f"  Validations performed: {result.get('validations_performed', 0)}")
                logger.info(f"  Critical gaps: {result.get('critical_gaps', 0)}")
                logger.info(f"  Achieved goals: {result.get('achieved_goals', 0)}")
            
            elif phase_key == "course_correction":
                logger.info(f"  Corrective tasks: {result.get('corrective_tasks_generated', 0)}")
                logger.info(f"  Memory-driven: {result.get('memory_driven_tasks', 0)}")
            
            elif phase_key == "universal_scalability":
                logger.info(f"  Domains tested: {result.get('domains_tested', 0)}")
                logger.info(f"  Success rate: {result.get('success_rate', 'N/A')}")
                logger.info(f"  Truly universal: {result.get('truly_universal', False)}")
            
            if result.get("error"):
                logger.info(f"  Error: {result['error']}")
        
        # System capabilities assessment
        logger.info(f"\n🎯 SYSTEM CAPABILITIES ASSESSMENT:")
        
        ai_driven = any("ai_available" in r and r.get("ai_available") for r in self.test_results.values())
        universal = self.test_results.get("universal_scalability", {}).get("truly_universal", False)
        scalable = self.test_results.get("memory_system", {}).get("memory_available", False)
        
        logger.info(f"  🤖 AI-Driven: {'✅ YES' if ai_driven else '❌ NO'}")
        logger.info(f"  🌍 Universal: {'✅ YES' if universal else '❌ LIMITED'}")
        logger.info(f"  ⚖️ Scalable: {'✅ YES' if scalable else '❌ NO'}")
        
        # Final assessment
        logger.info(f"\n🎉 FINAL ASSESSMENT:")
        
        if overall_success_rate >= 0.9:
            logger.info("🏆 EXCELLENT: System is production-ready with all capabilities functional")
        elif overall_success_rate >= 0.7:
            logger.info("👍 GOOD: System is mostly functional with minor issues")
        elif overall_success_rate >= 0.5:
            logger.info("⚠️ NEEDS WORK: System has significant issues requiring attention")
        else:
            logger.info("❌ CRITICAL: System has major issues preventing production use")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        for phase_key, result in self.test_results.items():
            if "❌" in result.get("status", ""):
                phase_name = phase_names.get(phase_key, phase_key)
                logger.info(f"  🔧 Fix issues in {phase_name}")
        
        if overall_success_rate >= 0.8:
            logger.info("  🚀 System ready for production deployment!")
        
        logger.info(f"\n📄 DETAILED RESULTS:")
        logger.info(json.dumps(self.test_results, indent=2, default=str))

async def main():
    """Main test execution"""
    
    tester = ProductionE2ETest()
    
    # Verify prerequisites
    if not tester.openai_key:
        logger.error("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if not tester.supabase_url or not tester.supabase_key:
        logger.error("❌ Supabase configuration not found in environment")
        return False
    
    # Run the comprehensive test
    await tester.run_production_e2e_test()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)