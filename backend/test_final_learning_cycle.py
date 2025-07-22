#!/usr/bin/env python3
"""
🎯 TEST FINALE - CICLO DI APPRENDIMENTO COMPLETO
Verifica che il LearningFeedbackEngine generi automaticamente nuovi workspace_insights
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

from database import (
    create_workspace, create_task, update_task_status, 
    get_memory_insights, add_memory_insight
)
from services.learning_feedback_engine import learning_feedback_engine
from models import TaskStatus, WorkspaceStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TestFinalLearningCycle:
    """Test finale per verificare il ciclo di apprendimento completo"""
    
    def __init__(self):
        self.test_workspace_id = str(uuid.uuid4())
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "learning_cycle_phases": [],
            "insights_generated": 0,
            "success": False
        }
    
    async def run_complete_learning_cycle_test(self):
        """Esegue il test completo del ciclo di apprendimento"""
        logger.info("🎯 INIZIO TEST CICLO DI APPRENDIMENTO COMPLETO")
        logger.info("=" * 70)
        
        try:
            # Fase 1: Setup workspace e task
            await self.setup_test_workspace()
            self.test_results["learning_cycle_phases"].append("setup_completed")
            
            # Fase 2: Crea task simulati per avere dati di performance
            await self.create_simulated_task_history()
            self.test_results["learning_cycle_phases"].append("task_history_created")
            
            # Fase 3: Esegui analisi performance per generare insights
            await self.execute_performance_analysis()
            self.test_results["learning_cycle_phases"].append("performance_analysis_completed")
            
            # Fase 4: Verifica che gli insights siano stati salvati nel database
            await self.verify_learning_insights_saved()
            self.test_results["learning_cycle_phases"].append("insights_verification_completed")
            
            # Fase 5: Verifica che il ciclo sia chiuso
            await self.verify_complete_learning_cycle()
            
            self.test_results["success"] = True
            logger.info("🎉 TEST CICLO DI APPRENDIMENTO COMPLETO SUPERATO!")
            
        except Exception as e:
            logger.error(f"❌ Test fallito: {e}")
            self.test_results["success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_final_results()
        return self.test_results
    
    async def setup_test_workspace(self):
        """Fase 1: Setup workspace di test"""
        logger.info("🔧 FASE 1: Setup Workspace di Test")
        
        workspace_data = {
            "name": "Learning Cycle Test Workspace",
            "description": "Test workspace per verificare il ciclo di apprendimento completo",
            "status": WorkspaceStatus.ACTIVE.value
        }
        
        await create_workspace(self.test_workspace_id, workspace_data, str(uuid.uuid4()))
        logger.info(f"✅ Workspace creato: {self.test_workspace_id}")
    
    async def create_simulated_task_history(self):
        """Fase 2: Crea task history simulata"""
        logger.info("🔧 FASE 2: Creazione Task History Simulata")
        
        # Crea task di successo
        success_tasks = [
            {
                "name": "Implementa API Authentication",
                "description": "Crea endpoint di autenticazione con JWT token",
                "status": TaskStatus.COMPLETED.value
            },
            {
                "name": "Crea Database Schema",
                "description": "Progetta schema database per utenti e permessi",
                "status": TaskStatus.COMPLETED.value
            },
            {
                "name": "Implementa Rate Limiting",
                "description": "Aggiunge rate limiting agli endpoint API",
                "status": TaskStatus.COMPLETED.value
            }
        ]
        
        # Crea task falliti
        failed_tasks = [
            {
                "name": "Deploy Production",
                "description": "Deploy dell'applicazione in produzione",
                "status": TaskStatus.FAILED.value
            },
            {
                "name": "Setup CI/CD",
                "description": "Configurazione pipeline di deployment",
                "status": TaskStatus.FAILED.value
            }
        ]
        
        all_tasks = success_tasks + failed_tasks
        
        for i, task_data in enumerate(all_tasks):
            task_id = str(uuid.uuid4())
            
            # Crea task nel database
            task_create_data = {
                "name": task_data["name"],
                "description": task_data["description"],
                "workspace_id": self.test_workspace_id,  # String format
                "status": TaskStatus.PENDING.value,  # String value
                "created_at": datetime.now().isoformat(),  # ISO format
                "updated_at": datetime.now().isoformat()  # ISO format
            }
            
            await create_task(task_id, task_create_data, TaskStatus.PENDING.value)
            
            # Simula risultato task
            task_result = {
                "result": f"Task {task_data['name']} result",
                "status": task_data["status"],
                "execution_time": 45.2 if task_data["status"] == "completed" else 120.5
            }
            
            if task_data["status"] == "failed":
                task_result["error_message"] = f"Failed to complete {task_data['name']}"
            
            # Aggiorna status
            await update_task_status(task_id, task_data["status"], task_result)
            
            logger.info(f"✅ Task creato: {task_data['name']} ({task_data['status']})")
        
        logger.info(f"✅ Creati {len(all_tasks)} task simulati")
    
    async def execute_performance_analysis(self):
        """Fase 3: Esegui analisi performance"""
        logger.info("🔧 FASE 3: Esecuzione Analisi Performance")
        
        # Conta insights prima dell'analisi
        insights_before = await get_memory_insights(self.test_workspace_id, limit=100)
        logger.info(f"📊 Insights prima dell'analisi: {len(insights_before)}")
        
        # Esegui analisi performance
        analysis_result = await learning_feedback_engine.analyze_workspace_performance(
            self.test_workspace_id
        )
        
        logger.info(f"📊 Risultato analisi: {analysis_result}")
        
        # Conta insights dopo l'analisi
        insights_after = await get_memory_insights(self.test_workspace_id, limit=100)
        logger.info(f"📊 Insights dopo l'analisi: {len(insights_after)}")
        
        insights_generated = len(insights_after) - len(insights_before)
        self.test_results["insights_generated"] = insights_generated
        
        logger.info(f"✅ Analisi completata: {insights_generated} nuovi insights generati")
    
    async def verify_learning_insights_saved(self):
        """Fase 4: Verifica che gli insights siano salvati"""
        logger.info("🔧 FASE 4: Verifica Insights Salvati nel Database")
        
        # Recupera tutti gli insights
        all_insights = await get_memory_insights(self.test_workspace_id, limit=100)
        
        # Verifica tipi di insight generati dal learning system
        learning_insight_types = [
            "task_success_pattern",
            "task_failure_lesson", 
            "agent_performance_insight",
            "timing_optimization_insight"
        ]
        
        found_learning_insights = []
        for insight in all_insights:
            insight_type = insight.get('insight_type')
            agent_role = insight.get('agent_role')
            
            if insight_type in learning_insight_types and agent_role == "learning_system":
                found_learning_insights.append(insight)
                
                # Mostra dettagli insight
                logger.info(f"✅ Insight trovato: {insight_type}")
                content = json.loads(insight.get('content', '{}'))
                if 'pattern_name' in content:
                    logger.info(f"  - Pattern: {content['pattern_name']}")
                elif 'failure_pattern' in content:
                    logger.info(f"  - Failure: {content['failure_pattern']}")
                elif 'performance_category' in content:
                    logger.info(f"  - Performance: {content['performance_category']}")
        
        logger.info(f"✅ Trovati {len(found_learning_insights)} insights del learning system")
        
        if len(found_learning_insights) == 0:
            raise Exception("Nessun insight generato dal learning system")
    
    async def verify_complete_learning_cycle(self):
        """Fase 5: Verifica ciclo completo"""
        logger.info("🔧 FASE 5: Verifica Ciclo di Apprendimento Completo")
        
        # Verifica che il ciclo sia chiuso:
        # 1. Esecuzione task -> 2. Analisi performance -> 3. Generazione insights -> 4. Salvataggio database
        
        cycle_checks = []
        
        # Check 1: Task execution data exists
        from database import list_tasks
        tasks = await list_tasks(self.test_workspace_id)
        if tasks:
            cycle_checks.append("✅ Task execution data present")
        else:
            cycle_checks.append("❌ No task execution data")
        
        # Check 2: Performance analysis completed
        insights = await get_memory_insights(self.test_workspace_id, limit=100)
        learning_insights = [i for i in insights if i.get('agent_role') == 'learning_system']
        if learning_insights:
            cycle_checks.append("✅ Performance analysis insights saved")
        else:
            cycle_checks.append("❌ No performance analysis insights")
        
        # Check 3: Insights are structured and actionable
        structured_insights = 0
        for insight in learning_insights:
            content = json.loads(insight.get('content', '{}'))
            if 'recommendations' in content or 'success_factors' in content:
                structured_insights += 1
        
        if structured_insights > 0:
            cycle_checks.append(f"✅ {structured_insights} structured, actionable insights")
        else:
            cycle_checks.append("❌ No structured insights")
        
        # Check 4: Learning system can access its own insights
        from services.memory_similarity_engine import memory_similarity_engine
        test_context = {
            'name': 'Test Authentication Task',
            'description': 'Test task for authentication system',
            'type': 'backend_development',
            'skills': ['Python', 'API', 'Authentication']
        }
        
        try:
            relevant_insights = await memory_similarity_engine.get_relevant_insights(
                workspace_id=self.test_workspace_id,
                task_context=test_context
            )
            if relevant_insights:
                cycle_checks.append("✅ Learning system can retrieve its own insights")
            else:
                cycle_checks.append("⚠️ Learning system found no relevant insights")
        except Exception as e:
            cycle_checks.append(f"❌ Learning system insight retrieval failed: {e}")
        
        # Stampa risultati
        logger.info("📊 Verifica Ciclo di Apprendimento:")
        for check in cycle_checks:
            logger.info(f"  {check}")
        
        successful_checks = len([c for c in cycle_checks if c.startswith("✅")])
        total_checks = len(cycle_checks)
        
        if successful_checks >= 3:  # Almeno 3 su 4 check devono passare
            logger.info("✅ Ciclo di apprendimento completo verificato!")
            self.test_results["learning_cycle_phases"].append("complete_cycle_verified")
        else:
            raise Exception(f"Ciclo incompleto: solo {successful_checks}/{total_checks} check superati")
    
    def _print_final_results(self):
        """Stampa risultati finali"""
        logger.info("\\n" + "=" * 70)
        logger.info("🎯 RISULTATI FINALI - TEST CICLO DI APPRENDIMENTO")
        logger.info("=" * 70)
        
        logger.info(f"✅ Fasi Completate: {len(self.test_results['learning_cycle_phases'])}")
        for fase in self.test_results['learning_cycle_phases']:
            logger.info(f"  - {fase}")
        
        logger.info(f"\\n📊 Insights Generati: {self.test_results['insights_generated']}")
        
        if self.test_results['success']:
            logger.info("\\n🎉 CICLO DI APPRENDIMENTO COMPLETO FUNZIONANTE!")
            logger.info("✅ Il sistema ora:")
            logger.info("  - Esegue task e raccoglie dati di performance")
            logger.info("  - Analizza i pattern per identificare successi e fallimenti")
            logger.info("  - Genera insights strutturati e actionable")
            logger.info("  - Salva gli insights nel database per riuso futuro")
            logger.info("  - Può recuperare insights per migliorare task futuri")
            logger.info("\\n🧠 Il sistema è ora veramente AUTO-MIGLIORANTE!")
        else:
            logger.warning("\\n⚠️ Ciclo di apprendimento non completamente funzionante")
        
        logger.info("=" * 70)

async def main():
    """Esegue il test finale del ciclo di apprendimento"""
    logger.info("🚀 Avvio Test Finale - Ciclo di Apprendimento Completo")
    
    test = TestFinalLearningCycle()
    risultati = await test.run_complete_learning_cycle_test()
    
    return 0 if risultati["success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)