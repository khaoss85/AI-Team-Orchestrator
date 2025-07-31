"""
🔍 TEST AUTONOMOUS GOAL-DRIVEN TASK GENERATION
Verifica se il sistema genera automaticamente task dai goals senza interventi manuali
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
import requests
from database import supabase

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api"

class AutonomousGenerationTest:
    def __init__(self):
        self.workspace_id = None
        self.initial_task_count = 0
        self.final_task_count = 0
        self.goals_created = []
        self.tasks_generated = []
        self.monitoring_duration = 420  # 7 minutes (3+ goal validation cycles)
        
    async def run_test(self):
        logger.info("🔍 TESTING AUTONOMOUS GOAL-DRIVEN TASK GENERATION")
        logger.info("=" * 70)
        logger.info("Obiettivo: Verificare se il sistema genera task autonomamente dai goals")
        logger.info("Durata: 7 minuti (3+ cicli di validation)")
        logger.info("=" * 70)
        
        try:
            # FASE 1: Setup workspace e goals
            await self._setup_workspace_and_goals()
            
            # FASE 2: Verifica team esistente o ne crea uno
            await self._ensure_team_exists()
            
            # FASE 3: Snapshot iniziale
            await self._take_initial_snapshot()
            
            # FASE 4: Monitoraggio passivo (senza interventi)
            await self._passive_monitoring()
            
            # FASE 5: Analisi risultati
            await self._analyze_results()
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)

    async def _setup_workspace_and_goals(self):
        logger.info("\n📋 FASE 1: Setup Workspace e Goals")
        
        # Crea workspace
        workspace_data = {
            "name": f"Autonomous Generation Test {datetime.now().strftime('%H%M%S')}",
            "description": "Test per verificare generazione autonoma di task dai goals"
        }
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        response.raise_for_status()
        workspace = response.json()
        self.workspace_id = workspace["id"]
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        
        # Crea goals complessi che richiedono multiple task
        goals = [
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Create a complete Python web scraper with error handling, logging, and configuration",
                "metric_type": "deliverable_web_scraper",
                "target_value": 5,  # 5 componenti principali
                "current_value": 0,
                "status": "active",
                "priority": 1
            },
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Implement comprehensive testing suite with unit tests, integration tests, and performance tests",
                "metric_type": "test_suite_coverage",
                "target_value": 8,  # 8 test files diversi
                "current_value": 0,
                "status": "active", 
                "priority": 2
            },
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Create complete project documentation including API docs, user guide, and deployment instructions",
                "metric_type": "documentation_completeness",
                "target_value": 4,  # 4 tipi di documentazione
                "current_value": 0,
                "status": "active",
                "priority": 3
            }
        ]
        
        for goal in goals:
            result = supabase.table("workspace_goals").insert(goal).execute()
            if result.data:
                self.goals_created.append(goal)
                logger.info(f"✅ Goal created: {goal['description'][:60]}...")
        
        logger.info(f"📊 Total target value across all goals: {sum(g['target_value'] for g in goals)}")

    async def _ensure_team_exists(self):
        logger.info("\n👥 FASE 2: Verifica/Crea Team")
        
        # Controlla se esiste già un team
        agents_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/agents", timeout=10)
        if agents_response.status_code == 200 and agents_response.json():
            logger.info(f"✅ Team esistente trovato: {len(agents_response.json())} agenti")
            return
        
        # Crea nuovo team
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Complex Python web scraping project with testing and documentation",
            "budget": 200.0,
            "max_team_size": 5
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=90)
        proposal_response.raise_for_status()
        proposal_id = proposal_response.json()["proposal_id"]
        
        approval_response = requests.post(
            f"{API_BASE}/director/approve/{self.workspace_id}",
            params={"proposal_id": proposal_id},
            timeout=60
        )
        approval_response.raise_for_status()
        logger.info("✅ Nuovo team creato e approvato")

    async def _take_initial_snapshot(self):
        logger.info("\n📸 FASE 3: Snapshot Iniziale")
        
        tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
        if tasks_response.status_code == 200:
            initial_tasks = tasks_response.json()
            self.initial_task_count = len(initial_tasks)
            logger.info(f"📊 Task iniziali: {self.initial_task_count}")
            
            for task in initial_tasks:
                logger.info(f"   - {task.get('name', 'Unknown')} ({task.get('status', 'unknown')})")
        else:
            self.initial_task_count = 0
            logger.info("📊 Nessun task iniziale")

    async def _passive_monitoring(self):
        logger.info(f"\n⏱️ FASE 4: Monitoraggio Passivo ({self.monitoring_duration//60} minuti)")
        logger.info("   Verificando se il goal monitor genera automaticamente nuovi task...")
        logger.info("   ⚠️ NON effettueremo interventi manuali - solo osservazione!")
        
        start_time = time.time()
        check_interval = 30  # Ogni 30 secondi
        last_task_count = self.initial_task_count
        
        while time.time() - start_time < self.monitoring_duration:
            elapsed = int(time.time() - start_time)
            minutes_elapsed = elapsed // 60
            seconds_elapsed = elapsed % 60
            
            # Controlla task attuali
            tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
            if tasks_response.status_code == 200:
                current_tasks = tasks_response.json()
                current_count = len(current_tasks)
                
                # Log status ogni minuto
                if elapsed % 60 == 0 or current_count != last_task_count:
                    status_counts = {}
                    new_tasks_this_cycle = []
                    
                    for task in current_tasks:
                        status = task.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                        
                        # Identifica task nuovi (non nel snapshot iniziale)
                        if len(current_tasks) > self.initial_task_count:
                            task_name = task.get('name', 'Unknown')
                            if task_name not in [t.get('name', '') for t in self.tasks_generated]:
                                new_tasks_this_cycle.append(task_name)
                    
                    logger.info(f"\n⏰ {minutes_elapsed:02d}:{seconds_elapsed:02d} - Task: {current_count} | Status: {status_counts}")
                    
                    if new_tasks_this_cycle:
                        logger.info(f"   🆕 Nuovi task generati: {len(new_tasks_this_cycle)}")
                        for task_name in new_tasks_this_cycle:
                            logger.info(f"      ✨ {task_name}")
                            self.tasks_generated.append({"name": task_name, "generated_at": elapsed})
                    
                    last_task_count = current_count
            
            await asyncio.sleep(check_interval)

    async def _analyze_results(self):
        logger.info("\n📊 FASE 5: Analisi Risultati")
        
        # Snapshot finale
        tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
        final_tasks = tasks_response.json() if tasks_response.status_code == 200 else []
        self.final_task_count = len(final_tasks)
        
        # Calcola metriche
        tasks_generated = self.final_task_count - self.initial_task_count
        generation_rate = tasks_generated / (self.monitoring_duration / 60)  # task per minuto
        
        logger.info("=" * 70)
        logger.info("📈 RISULTATI FINALI")
        logger.info("=" * 70)
        
        logger.info(f"📊 METRICHE:")
        logger.info(f"   Task Iniziali: {self.initial_task_count}")
        logger.info(f"   Task Finali: {self.final_task_count}")
        logger.info(f"   Task Generati: {tasks_generated}")
        logger.info(f"   Durata: {self.monitoring_duration//60} minuti")
        logger.info(f"   Rate: {generation_rate:.2f} task/minuto")
        
        # Analizza distribuzione per status
        status_counts = {}
        completed_count = 0
        for task in final_tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == 'completed':
                completed_count += 1
        
        logger.info(f"\n📋 DISTRIBUZIONE STATUS:")
        for status, count in status_counts.items():
            logger.info(f"   {status}: {count}")
        
        # Calcola target completeness
        total_target = sum(g['target_value'] for g in self.goals_created)
        logger.info(f"\n🎯 PROGRESS VERSO GOALS:")
        logger.info(f"   Target totale: {total_target}")
        logger.info(f"   Task completati: {completed_count}")
        logger.info(f"   Completeness: {(completed_count/total_target)*100:.1f}%")
        
        # Determina autonomia
        is_truly_autonomous = tasks_generated > 0
        has_sufficient_generation = tasks_generated >= total_target * 0.5  # Almeno 50% dei task necessari
        
        logger.info(f"\n🤖 VALUTAZIONE AUTONOMIA:")
        logger.info(f"   Genera task autonomamente: {'✅ SÌ' if is_truly_autonomous else '❌ NO'}")
        logger.info(f"   Genera task sufficienti: {'✅ SÌ' if has_sufficient_generation else '❌ NO'}")
        
        if is_truly_autonomous and has_sufficient_generation:
            logger.info("\n🎉 RISULTATO: SISTEMA COMPLETAMENTE AUTONOMO!")
            logger.info("   Il goal monitor genera automaticamente task dai goals")
        elif is_truly_autonomous:
            logger.info("\n⚠️ RISULTATO: AUTONOMIA PARZIALE")
            logger.info("   Il sistema genera task ma potrebbe non essere sufficiente")
        else:
            logger.info("\n❌ RISULTATO: SISTEMA NON AUTONOMO")
            logger.info("   Il goal monitor non sta generando task automaticamente")
            logger.info("   POSSIBILI CAUSE:")
            logger.info("   - Goal monitor non in esecuzione")
            logger.info("   - Configurazione interval troppo lunga")
            logger.info("   - Condizioni di generazione non soddisfatte")
            logger.info("   - Bug nel sistema goal-driven")
        
        # Suggerimenti
        logger.info(f"\n💡 RACCOMANDAZIONI:")
        if not is_truly_autonomous:
            logger.info("   1. Verificare che automated_goal_monitor sia attivo nel server")
            logger.info("   2. Controllare GOAL_VALIDATION_INTERVAL_MINUTES in .env")
            logger.info("   3. Verificare log del server per errori del goal monitor")
        elif not has_sufficient_generation:
            logger.info("   1. Aumentare la complessità dei goals per richiedere più task")
            logger.info("   2. Verificare che il goal planner abbia abbastanza context")
            logger.info("   3. Considerare di abbassare le soglie di generazione")
        else:
            logger.info("   1. Sistema funziona perfettamente!")
            logger.info("   2. Può essere messo in produzione")
        
        logger.info("=" * 70)


async def main():
    test = AutonomousGenerationTest()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())