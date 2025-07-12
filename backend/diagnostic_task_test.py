#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC TASK EXECUTION TEST
================================================================================
Test specifico per diagnosticare perché i task falliscono durante l'esecuzione
e raccogliere informazioni dettagliate sui motivi del fallimento.
"""

import requests
import time
import json
import logging
from uuid import uuid4

# --- Configuration ---
BASE_URL = "http://localhost:8000"
MAX_WAIT_TIME = 120  # 2 minuti per il primo task
POLLING_INTERVAL = 10  # 10 secondi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_diagnostic_test():
    """
    Esegue un test diagnostico focalizzato sull'analisi dei fallimenti dei task.
    """
    workspace_id = None
    try:
        # --- FASE 1: SETUP ---
        logging.info("=== FASE 1: SETUP ===")
        workspace_id = _create_workspace_and_goal()
        assert workspace_id, "Setup fallito: impossibile creare workspace e goal."

        # --- FASE 2: TRIGGER ---
        logging.info("\n=== FASE 2: TRIGGER AUTONOMOUS FLOW ===")
        _trigger_and_approve_proposal(workspace_id)

        # --- FASE 3: WAIT FOR FIRST TASK ---
        logging.info("\n=== FASE 3: WAITING FOR FIRST TASK CREATION ===")
        first_task_id = _wait_for_first_task_creation(workspace_id)
        assert first_task_id, "Nessun task è stato creato entro il tempo limite."

        # --- FASE 4: DEEP DIAGNOSIS ---
        logging.info("\n=== FASE 4: DEEP TASK EXECUTION DIAGNOSIS ===")
        _deep_task_diagnosis(workspace_id, first_task_id)

        logging.info("\n✅ Diagnostic test completato con successo!")
        return True

    except Exception as e:
        logging.error(f"\n❌ Diagnostic test fallito: {e}", exc_info=True)
        return False
    finally:
        # --- CLEANUP ---
        if workspace_id:
            logging.info("\n=== CLEANUP ===")
            _cleanup(workspace_id)

def _create_workspace_and_goal() -> str:
    """Crea un workspace e un obiettivo, restituendo il workspace_id."""
    # Create workspace
    workspace_data = {
        "name": f"Diagnostic Test Workspace - {uuid4()}",
        "goal": "Generate a simple contact list of 5 potential leads in the SaaS industry."
    }
    response = requests.post(f"{BASE_URL}/workspaces", json=workspace_data, timeout=10)
    assert response.status_code in [200, 201], f"Workspace creation failed: {response.text}"
    workspace = response.json()
    workspace_id = workspace['id']
    logging.info(f"✅ Workspace creato: {workspace_id}")

    # Create goal
    goal_data = {
        "workspace_id": workspace_id,
        "description": "Generate a simple contact list of 5 potential leads in the SaaS industry.",
        "metric_type": "deliverable_quality",
        "target_value": 80.0,
    }
    response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", json=goal_data, timeout=10)
    assert response.status_code in [200, 201], f"Goal creation failed: {response.text}"
    logging.info("✅ Goal creato con successo.")
    return workspace_id

def _trigger_and_approve_proposal(workspace_id: str):
    """Crea e approva una proposta di team per avviare il flusso."""
    proposal_payload = {
        "workspace_id": workspace_id,
        "requirements": "Generate a simple contact list of 5 potential leads in the SaaS industry.",
        "budget_limit": 50.0
    }
    response = requests.post(f"{BASE_URL}/api/director/proposal", json=proposal_payload, timeout=30)
    assert response.status_code == 200, f"Director proposal failed: {response.text}"
    proposal = response.json()
    proposal_id = proposal.get("proposal_id")
    assert proposal_id, "La risposta della proposta non contiene un proposal_id."
    logging.info(f"✅ Proposta di team creata: {proposal_id}")

    # Approve the proposal
    approval_response = requests.post(f"{BASE_URL}/api/director/approve/{workspace_id}", params={"proposal_id": proposal_id}, timeout=10)
    assert approval_response.status_code in [200, 204], f"Proposal approval failed: {approval_response.text}"
    logging.info("✅ Proposta di team approvata, flusso autonomo avviato.")

def _wait_for_first_task_creation(workspace_id: str) -> str:
    """Attende la creazione del primo task e restituisce il task_id."""
    start_time = time.time()
    
    while time.time() - start_time < MAX_WAIT_TIME:
        try:
            tasks_res = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/tasks", timeout=5)
            if tasks_res.status_code == 200:
                tasks = tasks_res.json()
                if isinstance(tasks, list) and len(tasks) > 0:
                    first_task = tasks[0]
                    task_id = first_task.get('id')
                    logging.info(f"✅ Primo task creato: {task_id}")
                    logging.info(f"📋 Task name: {first_task.get('name', 'N/A')}")
                    logging.info(f"🎯 Task status: {first_task.get('status', 'N/A')}")
                    logging.info(f"👤 Assigned to agent: {first_task.get('agent_id', 'N/A')}")
                    return task_id
            else:
                logging.warning(f"⚠️ Task endpoint returned {tasks_res.status_code}")
        except Exception as e:
            logging.error(f"Errore durante controllo task: {e}")
        
        logging.info(f"⏳ Attendendo creazione task... ({int(time.time() - start_time)}s)")
        time.sleep(POLLING_INTERVAL)
    
    return None

def _deep_task_diagnosis(workspace_id: str, task_id: str):
    """Esegue una diagnosi approfondita del task execution."""
    logging.info(f"🔍 Iniziando diagnosi approfondita per task {task_id}")
    
    # 1. Verifica agenti nel workspace
    logging.info("\n--- 1. VERIFICA AGENTI ---")
    agents_res = requests.get(f"{BASE_URL}/agents/{workspace_id}", timeout=5)
    if agents_res.status_code == 200:
        agents = agents_res.json()
        logging.info(f"✅ Trovati {len(agents)} agenti:")
        for agent in agents:
            logging.info(f"  - {agent.get('name')} ({agent.get('role')}) - Status: {agent.get('status')}")
    else:
        logging.error(f"❌ Errore recupero agenti: {agents_res.status_code}")

    # 2. Monitora esecuzione task
    logging.info("\n--- 2. MONITORAGGIO ESECUZIONE TASK ---")
    start_time = time.time()
    previous_status = None
    
    while time.time() - start_time < MAX_WAIT_TIME:
        try:
            task_res = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/tasks", timeout=5)
            if task_res.status_code == 200:
                tasks = task_res.json()
                current_task = next((t for t in tasks if t.get('id') == task_id), None)
                
                if current_task:
                    current_status = current_task.get('status')
                    
                    if current_status != previous_status:
                        logging.info(f"🔄 Status changed: {previous_status} → {current_status}")
                        previous_status = current_status
                        
                        # Log dettagli del task
                        logging.info(f"📊 Task details:")
                        logging.info(f"  - Name: {current_task.get('name', 'N/A')}")
                        logging.info(f"  - Agent ID: {current_task.get('agent_id', 'N/A')}")
                        logging.info(f"  - Priority: {current_task.get('priority', 'N/A')}")
                        logging.info(f"  - Result: {current_task.get('result', 'N/A')[:100] if current_task.get('result') else 'None'}...")
                        
                        if current_status == 'failed':
                            logging.error("❌ TASK FALLITO! Raccogliendo informazioni diagnostiche...")
                            _analyze_task_failure(workspace_id, task_id, current_task)
                            return
                        elif current_status == 'completed':
                            logging.info("✅ TASK COMPLETATO! Successo!")
                            _analyze_task_success(current_task)
                            return
                
        except Exception as e:
            logging.error(f"Errore durante monitoraggio: {e}")
        
        time.sleep(POLLING_INTERVAL)
    
    logging.warning("⏰ Timeout raggiunto durante monitoraggio task")

def _analyze_task_failure(workspace_id: str, task_id: str, task_data: dict):
    """Analizza in dettaglio perché un task è fallito."""
    logging.error("🚨 ANALISI FALLIMENTO TASK 🚨")
    
    # 1. Stampa tutti i dettagli del task
    logging.error(f"📋 Task completo: {json.dumps(task_data, indent=2)}")
    
    # 2. Controlla se ci sono errori specifici nei log del server
    logging.error("📝 Controllando i log del server per errori recenti...")
    try:
        # Cerca nei log recenti
        import subprocess
        result = subprocess.run(['tail', '-50', 'server.log'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_lines = result.stdout.split('\n')
            error_lines = [line for line in log_lines if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed', task_id])]
            if error_lines:
                logging.error("🔍 Errori trovati nei log:")
                for line in error_lines[-10:]:  # Ultimi 10 errori
                    logging.error(f"  {line}")
            else:
                logging.info("ℹ️ Nessun errore specifico trovato nei log recenti")
    except Exception as e:
        logging.error(f"Errore durante lettura log: {e}")
    
    # 3. Prova a ottenere più dettagli dal debug endpoint
    try:
        debug_res = requests.get(f"{BASE_URL}/api/debug/task-details/{task_id}", timeout=5)
        if debug_res.status_code == 200:
            debug_data = debug_res.json()
            logging.error(f"🔧 Debug info: {json.dumps(debug_data, indent=2)}")
        else:
            logging.error(f"❌ Debug endpoint non disponibile: {debug_res.status_code}")
    except Exception as e:
        logging.error(f"Errore debug endpoint: {e}")
    
    # 4. Prova l'endpoint task status corretto
    try:
        task_status_res = requests.get(f"{BASE_URL}/monitoring/task/{task_id}/status", timeout=5)
        if task_status_res.status_code == 200:
            task_status_data = task_status_res.json()
            logging.error(f"📋 Task status (monitoring endpoint): {json.dumps(task_status_data, indent=2)}")
        else:
            logging.error(f"❌ Task status endpoint error: {task_status_res.status_code} - {task_status_res.text}")
    except Exception as e:
        logging.error(f"Errore task status endpoint: {e}")

def _analyze_task_success(task_data: dict):
    """Analizza un task completato con successo."""
    logging.info("🎉 ANALISI SUCCESSO TASK 🎉")
    result = task_data.get('result', '')
    logging.info(f"📝 Risultato: {result[:500]}..." if len(result) > 500 else f"📝 Risultato: {result}")

def _cleanup(workspace_id: str):
    """Pulisce le risorse create durante il test."""
    try:
        response = requests.delete(f"{BASE_URL}/workspaces/{workspace_id}", timeout=10)
        logging.info(f"🧹 Cleanup response: {response.status_code}")
    except Exception as e:
        logging.error(f"Cleanup fallito: {e}")

if __name__ == "__main__":
    if run_diagnostic_test():
        exit(0)
    else:
        exit(1)