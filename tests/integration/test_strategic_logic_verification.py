#!/usr/bin/env python3
"""
🎯 TEST LOGICA STRATEGICA - VERIFICA IMPLEMENTAZIONE CORE
Verifica che la logica di recupero strategico sia implementata correttamente
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from ai_agents.manager import AgentManager
from models import Task, TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TestStrategicLogicVerification:
    """Test per verificare la logica di recupero strategico"""
    
    def __init__(self):
        self.test_workspace_id = str(uuid.uuid4())
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "enhanced_get_task_insights_implemented": False,
            "strategic_insights_method_implemented": False,
            "format_insight_content_implemented": False,
            "enhanced_task_formatting_implemented": False,
            "success": False
        }
    
    async def run_logic_verification(self):
        """Verifica la logica di recupero strategico"""
        logger.info("🎯 INIZIO TEST LOGICA STRATEGICA")
        logger.info("=" * 60)
        
        try:
            # Test 1: Verify AgentManager has enhanced methods
            await self.verify_agent_manager_enhancements()
            
            # Test 2: Verify method implementations
            await self.verify_method_implementations()
            
            # Test 3: Verify task enhancement logic
            await self.verify_task_enhancement_logic()
            
            # Calculate success
            self.test_results["success"] = all([
                self.test_results["enhanced_get_task_insights_implemented"],
                self.test_results["strategic_insights_method_implemented"],
                self.test_results["format_insight_content_implemented"],
                self.test_results["enhanced_task_formatting_implemented"]
            ])
            
            if self.test_results["success"]:
                logger.info("🎉 LOGICA STRATEGICA COMPLETAMENTE IMPLEMENTATA!")
            else:
                logger.warning("⚠️ Alcune implementazioni mancano")
                
        except Exception as e:
            logger.error(f"❌ Test fallito: {e}")
            self.test_results["success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_results()
        return self.test_results
    
    async def verify_agent_manager_enhancements(self):
        """Test 1: Verify AgentManager has enhanced methods"""
        logger.info("🔧 TEST 1: Verifying AgentManager Enhancements")
        
        # Create AgentManager instance
        manager = AgentManager(UUID(self.test_workspace_id))
        
        # Check for enhanced methods
        enhanced_methods = [
            '_get_task_insights',
            '_get_strategic_insights',
            '_enhance_task_with_insights',
            '_format_insight_content'
        ]
        
        missing_methods = []
        for method in enhanced_methods:
            if not hasattr(manager, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.error(f"❌ Missing methods: {missing_methods}")
            return False
        
        logger.info("✅ All enhanced methods found in AgentManager")
        return True
    
    async def verify_method_implementations(self):
        """Test 2: Verify method implementations"""
        logger.info("🔧 TEST 2: Verifying Method Implementations")
        
        manager = AgentManager(UUID(self.test_workspace_id))
        
        # Test _get_strategic_insights implementation
        try:
            test_task = Task(
                id=UUID(str(uuid.uuid4())),
                workspace_id=UUID(self.test_workspace_id),
                name="Test Task",
                description="Test task for strategic insights",
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            strategic_insights = await manager._get_strategic_insights(test_task)
            logger.info(f"✅ _get_strategic_insights: returned {len(strategic_insights)} insights")
            self.test_results["strategic_insights_method_implemented"] = True
            
        except Exception as e:
            logger.error(f"❌ _get_strategic_insights failed: {e}")
            self.test_results["strategic_insights_method_implemented"] = False
        
        # Test _format_insight_content implementation
        try:
            test_content = json.dumps({
                "pattern_name": "Test Pattern",
                "success_factors": ["factor1", "factor2"],
                "recommendations": ["rec1", "rec2"]
            })
            
            formatted = manager._format_insight_content(test_content)
            logger.info(f"✅ _format_insight_content: formatted content length {len(formatted)}")
            
            # Check if formatted content contains expected elements
            if "Success factors:" in formatted and "Recommendations:" in formatted:
                self.test_results["format_insight_content_implemented"] = True
                logger.info("✅ _format_insight_content: properly formats structured content")
            else:
                logger.warning("⚠️ _format_insight_content: missing expected formatting")
                
        except Exception as e:
            logger.error(f"❌ _format_insight_content failed: {e}")
            self.test_results["format_insight_content_implemented"] = False
    
    async def verify_task_enhancement_logic(self):
        """Test 3: Verify task enhancement logic"""
        logger.info("🔧 TEST 3: Verifying Task Enhancement Logic")
        
        manager = AgentManager(UUID(self.test_workspace_id))
        
        try:
            # Create test task
            test_task = Task(
                id=UUID(str(uuid.uuid4())),
                workspace_id=UUID(self.test_workspace_id),
                name="Test Enhancement Task",
                description="Test task for enhancement logic",
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create mock insights - strategic and task-specific
            mock_insights = [
                {
                    "insight_type": "task_success_pattern",
                    "content": json.dumps({
                        "pattern_name": "Test Success Pattern",
                        "success_factors": ["factor1", "factor2"]
                    }),
                    "similarity_score": 0.85,
                    "strategic": False
                },
                {
                    "insight_type": "agent_performance_insight",
                    "content": json.dumps({
                        "performance_category": "high_performer",
                        "recommendations": ["rec1", "rec2"]
                    }),
                    "strategic": True,
                    "source": "learning_feedback_engine"
                }
            ]
            
            # Test task enhancement
            enhanced_task = await manager._enhance_task_with_insights(test_task, mock_insights)
            
            # Check enhancement
            enhanced_desc = enhanced_task.description
            
            # Verify both sections are present
            has_task_specific = "TASK-SPECIFIC INSIGHTS" in enhanced_desc
            has_strategic = "STRATEGIC LEARNING FROM SYSTEM ANALYSIS" in enhanced_desc
            has_importance_note = "Consider both task-specific patterns and strategic system insights" in enhanced_desc
            
            logger.info(f"✅ Enhanced task description length: {len(enhanced_desc)}")
            logger.info(f"✅ Contains task-specific section: {has_task_specific}")
            logger.info(f"✅ Contains strategic section: {has_strategic}")
            logger.info(f"✅ Contains importance note: {has_importance_note}")
            
            # Log enhanced description for inspection
            logger.info("\\n" + "="*50)
            logger.info("🔍 ENHANCED TASK DESCRIPTION SAMPLE:")
            logger.info("="*50)
            logger.info(enhanced_desc)
            logger.info("="*50)
            
            if has_task_specific and has_strategic and has_importance_note:
                self.test_results["enhanced_task_formatting_implemented"] = True
                logger.info("✅ Task enhancement logic correctly implemented")
            else:
                logger.warning("⚠️ Task enhancement logic missing some elements")
                
        except Exception as e:
            logger.error(f"❌ Task enhancement verification failed: {e}")
            self.test_results["enhanced_task_formatting_implemented"] = False
        
        # Test _get_task_insights (enhanced version)
        try:
            # This will test the enhanced version that combines both types
            all_insights = await manager._get_task_insights(test_task)
            logger.info(f"✅ _get_task_insights: returned {len(all_insights)} total insights")
            self.test_results["enhanced_get_task_insights_implemented"] = True
            
        except Exception as e:
            logger.error(f"❌ _get_task_insights failed: {e}")
            self.test_results["enhanced_get_task_insights_implemented"] = False
    
    def _print_results(self):
        """Print test results"""
        logger.info("\\n" + "=" * 60)
        logger.info("🎯 RISULTATI TEST LOGICA STRATEGICA")
        logger.info("=" * 60)
        
        tests = [
            ("Enhanced _get_task_insights", "enhanced_get_task_insights_implemented"),
            ("Strategic insights method", "strategic_insights_method_implemented"),
            ("Format insight content", "format_insight_content_implemented"),
            ("Enhanced task formatting", "enhanced_task_formatting_implemented")
        ]
        
        for test_name, result_key in tests:
            result = self.test_results[result_key]
            status = "✅" if result else "❌"
            logger.info(f"  {status} {test_name}: {result}")
        
        success_count = sum(1 for _, key in tests if self.test_results[key])
        logger.info(f"\\n📊 Success Rate: {success_count}/{len(tests)} ({success_count/len(tests)*100:.1f}%)")
        
        if self.test_results["success"]:
            logger.info("\\n🎉 LOGICA STRATEGICA COMPLETAMENTE IMPLEMENTATA!")
            logger.info("✅ Il sistema ora può:")
            logger.info("  - Recuperare insight strategici dal learning system")
            logger.info("  - Combinare insight task-specific e strategici")
            logger.info("  - Formattare correttamente entrambi i tipi")
            logger.info("  - Iniettare guidance completa nei task")
            logger.info("\\n🎯 SISTEMA PRONTO PER IL 100% AUTO-MIGLIORAMENTO!")
        else:
            logger.warning("\\n⚠️ Alcune implementazioni mancano")
            logger.warning("Il sistema non è completamente auto-migliorante")
        
        logger.info("=" * 60)

async def main():
    """Execute the strategic logic verification test"""
    logger.info("🚀 Starting Strategic Logic Verification Test")
    
    test = TestStrategicLogicVerification()
    results = await test.run_logic_verification()
    
    return 0 if results["success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)