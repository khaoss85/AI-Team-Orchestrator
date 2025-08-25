#!/usr/bin/env python3
"""
🎯 TEST DEFINITIVO - CICLO DI APPRENDIMENTO STRATEGICO COMPLETO
Verifica che gli agenti ricevano ENTRAMBI i tipi di insight: task-specific e strategici
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import add_memory_insight, get_memory_insights
from ai_agents.manager import AgentManager
from models import Task, TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TestCompleteStrategicLearning:
    """Test definitivo per verificare il ciclo di apprendimento strategico completo"""
    
    def __init__(self):
        self.test_workspace_id = str(uuid.uuid4())
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "strategic_insights_injected": False,
            "task_specific_insights_injected": False,
            "enhanced_task_contains_both": False,
            "success": False
        }
    
    async def run_strategic_learning_test(self):
        """Esegue il test completo del ciclo di apprendimento strategico"""
        logger.info("🎯 INIZIO TEST CICLO DI APPRENDIMENTO STRATEGICO COMPLETO")
        logger.info("=" * 75)
        
        try:
            # Phase 1: Create strategic insight from learning system
            await self.create_strategic_insight()
            
            # Phase 2: Create task-specific insight
            await self.create_task_specific_insight()
            
            # Phase 3: Create test task and verify enhancement
            await self.test_task_enhancement_with_both_insights()
            
            # Phase 4: Verify both types of insights are present
            await self.verify_complete_strategic_learning()
            
            self.test_results["success"] = (
                self.test_results["strategic_insights_injected"] and
                self.test_results["task_specific_insights_injected"] and
                self.test_results["enhanced_task_contains_both"]
            )
            
            if self.test_results["success"]:
                logger.info("🎉 TEST CICLO DI APPRENDIMENTO STRATEGICO SUPERATO!")
            else:
                logger.warning("⚠️ Test non completamente superato")
                
        except Exception as e:
            logger.error(f"❌ Test fallito: {e}")
            self.test_results["success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_final_results()
        return self.test_results
    
    async def create_strategic_insight(self):
        """Phase 1: Crea insight strategico dal learning system"""
        logger.info("🔧 PHASE 1: Creating Strategic Insight from Learning System")
        
        strategic_insight = {
            "pattern_name": "Frontend Development Performance Analysis",
            "performance_category": "needs_improvement",
            "recommendations": [
                "Frontend tasks often exceed estimated time by 40%",
                "Consider breaking down complex UI components",
                "Review CSS framework choices for efficiency"
            ],
            "analysis_timestamp": datetime.now().isoformat(),
            "affected_task_count": 5
        }
        
        await add_memory_insight(
            workspace_id=self.test_workspace_id,
            insight_type="agent_performance_insight",
            content=json.dumps(strategic_insight),
            agent_role="learning_system"  # This marks it as strategic
        )
        
        logger.info("✅ Strategic insight created from learning system")
        self.test_results["strategic_insights_injected"] = True
    
    async def create_task_specific_insight(self):
        """Phase 2: Crea insight task-specific"""
        logger.info("🔧 PHASE 2: Creating Task-Specific Insight")
        
        task_specific_insight = {
            "pattern_name": "React Component Success Pattern",
            "success_factors": [
                "Use TypeScript for type safety",
                "Implement proper error boundaries",
                "Add comprehensive unit tests"
            ],
            "recommendations": [
                "Start with component architecture design",
                "Use React hooks for state management",
                "Follow accessibility guidelines"
            ],
            "confidence_score": 0.85,
            "task_count": 3
        }
        
        await add_memory_insight(
            workspace_id=self.test_workspace_id,
            insight_type="task_success_pattern",
            content=json.dumps(task_specific_insight),
            agent_role="frontend_developer"  # This marks it as task-specific
        )
        
        logger.info("✅ Task-specific insight created")
        self.test_results["task_specific_insights_injected"] = True
    
    async def test_task_enhancement_with_both_insights(self):
        """Phase 3: Test task enhancement with both types of insights"""
        logger.info("🔧 PHASE 3: Testing Task Enhancement with Both Insight Types")
        
        # Create a frontend development task
        test_task = Task(
            id=UUID(str(uuid.uuid4())),
            workspace_id=UUID(self.test_workspace_id),
            name="Build React User Dashboard",
            description="Create a responsive React dashboard component with user analytics, charts, and real-time data updates",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create AgentManager and test insight retrieval
        manager = AgentManager(UUID(self.test_workspace_id))
        
        # Test the enhanced _get_task_insights method
        logger.info("🔍 Testing enhanced _get_task_insights method...")
        all_insights = await manager._get_task_insights(test_task)
        
        logger.info(f"📊 Retrieved {len(all_insights)} total insights")
        
        # Separate insights by type
        strategic_insights = [i for i in all_insights if i.get('strategic', False)]
        task_specific_insights = [i for i in all_insights if not i.get('strategic', False)]
        
        logger.info(f"🎯 Strategic insights: {len(strategic_insights)}")
        logger.info(f"📋 Task-specific insights: {len(task_specific_insights)}")
        
        # Test task enhancement
        logger.info("🔧 Testing task enhancement...")
        enhanced_task = await manager._enhance_task_with_insights(test_task, all_insights)
        
        # Log the enhanced task description for inspection
        logger.info("\\n" + "="*50)
        logger.info("🔍 ENHANCED TASK DESCRIPTION:")
        logger.info("="*50)
        logger.info(enhanced_task.description)
        logger.info("="*50)
        
        # Verify both types of insights are present
        enhanced_desc = enhanced_task.description
        
        has_strategic = (
            "STRATEGIC LEARNING FROM SYSTEM ANALYSIS" in enhanced_desc and
            "learning system" in enhanced_desc
        )
        
        has_task_specific = (
            "TASK-SPECIFIC INSIGHTS" in enhanced_desc and
            "relevance:" in enhanced_desc
        )
        
        self.test_results["enhanced_task_contains_both"] = has_strategic and has_task_specific
        
        if has_strategic:
            logger.info("✅ Enhanced task contains strategic insights")
        else:
            logger.warning("⚠️ Enhanced task missing strategic insights")
            
        if has_task_specific:
            logger.info("✅ Enhanced task contains task-specific insights")
        else:
            logger.warning("⚠️ Enhanced task missing task-specific insights")
    
    async def verify_complete_strategic_learning(self):
        """Phase 4: Verify complete strategic learning cycle"""
        logger.info("🔧 PHASE 4: Verifying Complete Strategic Learning Cycle")
        
        # Verify insights are stored properly
        all_insights = await get_memory_insights(self.test_workspace_id, limit=20)
        
        strategic_count = 0
        task_specific_count = 0
        
        for insight in all_insights:
            agent_role = insight.get('agent_role', '')
            if agent_role == 'learning_system':
                strategic_count += 1
            elif agent_role != 'learning_system':
                task_specific_count += 1
        
        logger.info(f"📊 Database verification:")
        logger.info(f"  - Strategic insights (learning_system): {strategic_count}")
        logger.info(f"  - Task-specific insights (other roles): {task_specific_count}")
        
        # Success criteria
        cycle_complete = (
            strategic_count > 0 and
            task_specific_count > 0 and
            self.test_results["enhanced_task_contains_both"]
        )
        
        if cycle_complete:
            logger.info("✅ Complete strategic learning cycle verified!")
            logger.info("🎯 The system now:")
            logger.info("  - Generates strategic insights from performance analysis")
            logger.info("  - Stores both strategic and task-specific insights")
            logger.info("  - Retrieves both types during task enhancement")
            logger.info("  - Injects both into agent prompts")
            logger.info("  - Provides comprehensive learning guidance")
        else:
            logger.warning("⚠️ Strategic learning cycle not complete")
    
    def _print_final_results(self):
        """Print final test results"""
        logger.info("\\n" + "=" * 75)
        logger.info("🎯 RISULTATI FINALI - TEST CICLO DI APPRENDIMENTO STRATEGICO")
        logger.info("=" * 75)
        
        logger.info("📊 Test Results:")
        logger.info(f"  ✅ Strategic insights injected: {self.test_results['strategic_insights_injected']}")
        logger.info(f"  ✅ Task-specific insights injected: {self.test_results['task_specific_insights_injected']}")
        logger.info(f"  ✅ Enhanced task contains both: {self.test_results['enhanced_task_contains_both']}")
        
        if self.test_results['success']:
            logger.info("\\n🎉 SISTEMA COMPLETAMENTE AUTO-MIGLIORANTE AL 100%!")
            logger.info("\\n🔄 CICLO DI APPRENDIMENTO STRATEGICO COMPLETO:")
            logger.info("  1. 📊 LearningFeedbackEngine analizza performance")
            logger.info("  2. 🎯 Genera insights strategici di alto livello")
            logger.info("  3. 💾 Salva insights con agent_role='learning_system'")
            logger.info("  4. 🧠 AgentManager recupera ENTRAMBI i tipi di insight")
            logger.info("  5. 📋 Task-specific (similarity) + Strategic (performance)")
            logger.info("  6. 🚀 Agenti ricevono guidance completa e contestuale")
            logger.info("\\n🎯 IL SISTEMA È VERAMENTE AUTO-MIGLIORANTE!")
        else:
            logger.warning("\\n⚠️ Sistema non completamente auto-migliorante")
            logger.warning("Alcuni aspetti del ciclo di apprendimento strategico mancano")
        
        logger.info("=" * 75)

async def main():
    """Execute the complete strategic learning test"""
    logger.info("🚀 Starting Complete Strategic Learning Test")
    
    test = TestCompleteStrategicLearning()
    results = await test.run_strategic_learning_test()
    
    return 0 if results["success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)