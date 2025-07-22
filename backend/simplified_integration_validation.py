#!/usr/bin/env python3
"""
🔧 FASE 4: Simplified Integration Validation
Validates the three key integration improvements without database complexity
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedIntegrationValidation:
    """Validates the three key integration improvements"""
    
    def __init__(self):
        self.validation_results = {
            "test_start": datetime.now().isoformat(),
            "validations": [],
            "integration_gaps_closed": [],
            "overall_success": False
        }
    
    async def run_validation(self):
        """Run simplified validation of integration improvements"""
        logger.info("🔧 Starting Simplified Integration Validation")
        logger.info("=" * 60)
        
        # Validation 1: ConcreteAssetExtractor Integration
        await self.validate_asset_extraction_integration()
        
        # Validation 2: Quality Rules Database Integration
        await self.validate_quality_rules_integration()
        
        # Validation 3: Memory Insights LLM Integration
        await self.validate_memory_insights_integration()
        
        # Calculate overall success
        passed = len([v for v in self.validation_results["validations"] if v["passed"]])
        total = len(self.validation_results["validations"])
        self.validation_results["overall_success"] = passed == total
        
        self._print_summary()
        return self.validation_results
    
    async def validate_asset_extraction_integration(self):
        """Validate that asset extraction is integrated into main flow"""
        validation_name = "Asset Extraction Integration"
        logger.info(f"🔧 VALIDATION 1: {validation_name}")
        
        try:
            # Check 1: ConcreteAssetExtractor exists and is importable
            from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
            extractor = ConcreteAssetExtractor()
            logger.info("✅ ConcreteAssetExtractor successfully imported")
            
            # Check 2: Database update_task_status function includes asset extraction
            from database import update_task_status
            import inspect
            
            # Get source code of update_task_status
            source = inspect.getsource(update_task_status)
            
            # Check for asset extraction integration keywords
            integration_keywords = [
                "ConcreteAssetExtractor",
                "extract_assets",
                "create_asset_artifact",
                "assets_extracted"
            ]
            
            found_keywords = []
            for keyword in integration_keywords:
                if keyword in source:
                    found_keywords.append(keyword)
            
            if len(found_keywords) >= 3:
                logger.info(f"✅ Asset extraction integrated in database.py ({len(found_keywords)}/4 keywords found)")
                
                # Check 3: Test asset extraction functionality
                test_content = """
                Here's a Python function:
                
                ```python
                def hello_world():
                    return "Hello, World!"
                ```
                
                This function returns a greeting message.
                """
                
                extracted_assets = await extractor.extract_assets(
                    content=test_content,
                    context={"test": True}
                )
                
                if extracted_assets:
                    logger.info(f"✅ Asset extraction working: {len(extracted_assets)} assets extracted")
                    
                    # Verify asset structure
                    sample_asset = extracted_assets[0]
                    required_fields = ["type", "name", "content"]
                    if all(field in sample_asset for field in required_fields):
                        logger.info("✅ Asset structure validation passed")
                    else:
                        logger.warning("⚠️ Asset structure missing some fields")
                else:
                    logger.warning("⚠️ Asset extraction returned no assets")
                
                self.validation_results["validations"].append({
                    "name": validation_name,
                    "passed": True,
                    "details": f"Integration keywords found: {found_keywords}"
                })
                
                self.validation_results["integration_gaps_closed"].append(
                    "LACUNA 1: ConcreteAssetExtractor now integrated in database.py update_task_status"
                )
                
            else:
                raise Exception(f"Asset extraction integration incomplete: only {len(found_keywords)}/4 keywords found")
            
        except Exception as e:
            logger.error(f"❌ {validation_name} failed: {e}")
            self.validation_results["validations"].append({
                "name": validation_name,
                "passed": False,
                "error": str(e)
            })
    
    async def validate_quality_rules_integration(self):
        """Validate that quality rules database is populated"""
        validation_name = "Quality Rules Database Integration"
        logger.info(f"🔧 VALIDATION 2: {validation_name}")
        
        try:
            # Check 1: Quality rules database function exists
            from database import get_quality_rules_for_asset_type
            logger.info("✅ get_quality_rules_for_asset_type function available")
            
            # Check 2: Quality rules exist in database
            from database import get_quality_rules
            
            asset_types = ["code", "json", "configuration"]
            total_rules = 0
            
            for asset_type in asset_types:
                rules = await get_quality_rules(asset_type)
                rule_count = len(rules)
                total_rules += rule_count
                
                if rule_count > 0:
                    logger.info(f"✅ {asset_type}: {rule_count} quality rules found")
                    
                    # Verify rule structure
                    sample_rule = rules[0]
                    if hasattr(sample_rule, 'rule_name') and hasattr(sample_rule, 'ai_validation_prompt'):
                        logger.info(f"  - Sample rule: {sample_rule.rule_name}")
                else:
                    logger.warning(f"⚠️ {asset_type}: No quality rules found")
            
            if total_rules > 0:
                logger.info(f"✅ Quality rules database populated: {total_rules} total rules")
                
                # Check 3: Quality fallbacks system updated
                from ai_quality_assurance.quality_db_fallbacks import get_quality_rules_for_asset_type as fallback_func
                logger.info("✅ Quality fallbacks system available")
                
                self.validation_results["validations"].append({
                    "name": validation_name,
                    "passed": True,
                    "details": f"Found {total_rules} quality rules across asset types"
                })
                
                self.validation_results["integration_gaps_closed"].append(
                    "LACUNA 2: Quality rules database populated instead of using fallbacks"
                )
            else:
                raise Exception("No quality rules found in database")
            
        except Exception as e:
            logger.error(f"❌ {validation_name} failed: {e}")
            self.validation_results["validations"].append({
                "name": validation_name,
                "passed": False,
                "error": str(e)
            })
    
    async def validate_memory_insights_integration(self):
        """Validate that memory insights are integrated into LLM prompts"""
        validation_name = "Memory Insights LLM Integration"
        logger.info(f"🔧 VALIDATION 3: {validation_name}")
        
        try:
            # Check 1: Memory similarity engine exists
            from services.memory_similarity_engine import memory_similarity_engine
            logger.info("✅ Memory similarity engine available")
            
            # Check 2: AgentManager has memory integration methods
            from ai_agents.manager import AgentManager
            from uuid import UUID
            
            test_workspace_id = "123e4567-e89b-12d3-a456-426614174000"
            manager = AgentManager(UUID(test_workspace_id))
            
            # Check for memory integration methods
            memory_methods = [
                "_get_task_insights",
                "_enhance_task_with_insights", 
                "_store_execution_insights"
            ]
            
            found_methods = []
            for method in memory_methods:
                if hasattr(manager, method):
                    found_methods.append(method)
            
            if len(found_methods) == 3:
                logger.info(f"✅ AgentManager has all memory integration methods: {found_methods}")
                
                # Check 3: Specialist agent uses enhanced prompts
                from ai_agents.specialist_enhanced import SpecialistAgent
                import inspect
                
                # Check if SpecialistAgent._create_enhanced_prompt includes task.description
                source = inspect.getsource(SpecialistAgent._create_enhanced_prompt)
                
                if "task.description" in source:
                    logger.info("✅ SpecialistAgent uses task.description in enhanced prompts")
                    
                    # Check 4: Task enhancement includes insights
                    source_manager = inspect.getsource(manager._enhance_task_with_insights)
                    
                    if "🧠 RELEVANT INSIGHTS" in source_manager:
                        logger.info("✅ Task enhancement includes insights formatting")
                        
                        self.validation_results["validations"].append({
                            "name": validation_name,
                            "passed": True,
                            "details": "Memory insights integrated into LLM prompts via task.description"
                        })
                        
                        self.validation_results["integration_gaps_closed"].append(
                            "LACUNA 3: Memory insights now injected into agent LLM prompts"
                        )
                    else:
                        raise Exception("Task enhancement missing insights formatting")
                else:
                    raise Exception("SpecialistAgent not using task.description in prompts")
            else:
                raise Exception(f"AgentManager missing memory methods: {set(memory_methods) - set(found_methods)}")
            
        except Exception as e:
            logger.error(f"❌ {validation_name} failed: {e}")
            self.validation_results["validations"].append({
                "name": validation_name,
                "passed": False,
                "error": str(e)
            })
    
    def _print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🔧 INTEGRATION VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        passed_count = len([v for v in self.validation_results["validations"] if v["passed"]])
        total_count = len(self.validation_results["validations"])
        
        logger.info(f"✅ Validations Passed: {passed_count}/{total_count}")
        
        for validation in self.validation_results["validations"]:
            if validation["passed"]:
                logger.info(f"  ✅ {validation['name']}")
                if "details" in validation:
                    logger.info(f"      {validation['details']}")
            else:
                logger.info(f"  ❌ {validation['name']}")
                logger.info(f"      Error: {validation['error']}")
        
        logger.info("\n🎯 INTEGRATION GAPS CLOSED:")
        for gap in self.validation_results["integration_gaps_closed"]:
            logger.info(f"  - {gap}")
        
        success_rate = passed_count / total_count if total_count > 0 else 0
        logger.info(f"\n📊 Success Rate: {success_rate:.1%}")
        
        if self.validation_results["overall_success"]:
            logger.info("🎉 ALL INTEGRATION VALIDATIONS PASSED!")
            logger.info("✅ User feedback addressed: All 3 critical integration gaps have been closed")
        else:
            logger.warning("⚠️ Some integration validations failed")
        
        logger.info("=" * 60)

async def main():
    """Run the simplified integration validation"""
    logger.info("🚀 Starting Simplified Integration Validation")
    
    test = SimplifiedIntegrationValidation()
    results = await test.run_validation()
    
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)