#!/usr/bin/env python3
"""
🚀 EXTENDED AUTONOMOUS E2E TEST
================================================================================
Test end-to-end avanzato per verificare l'intero flusso di orchestrazione autonoma,
dalla creazione del goal alla validazione del deliverable finale.
"""

import requests
import time
import json
import logging
from uuid import uuid4

# --- Configuration ---
BASE_URL = "http://localhost:8000"
WORKSPACE_COMPLETION_TIMEOUT = 600  # 10 minuti
POLLING_INTERVAL = 15  # 15 secondi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_extended_e2e_test():
    """
    Esegue il test E2E completo, attendendo il completamento del workspace
    e validando i risultati finali.
    """
    workspace_id = None
    try:
        # --- FASE 1: SETUP ---
        logging.info("--- FASE 1: SETUP ---")
        workspace_id = _create_workspace_and_goal()
        assert workspace_id, "Setup fallito: impossibile creare workspace e goal."

        # --- FASE 2: TRIGGER ---
        logging.info("\n--- FASE 2: TRIGGER AUTONOMOUS FLOW ---")
        _trigger_and_approve_proposal(workspace_id)

        # --- FASE 3: VERIFICA TASK CREATION ---
        logging.info("\n--- FASE 3: WAITING FOR TASK CREATION ---")
        task_creation_success = _wait_for_task_creation(workspace_id)
        assert task_creation_success, f"Nessun task è stato creato nel workspace {workspace_id} entro il tempo limite."
        
        # --- FASE 4: ATTESA ATTIVA ---
        logging.info("\n--- FASE 4: WAITING FOR WORKSPACE COMPLETION ---")
        completion_success = _poll_for_completion(workspace_id)
        assert completion_success, f"Timeout: il workspace {workspace_id} non ha raggiunto lo stato COMPLETED in {WORKSPACE_COMPLETION_TIMEOUT} secondi."

        # --- FASE 5: VERIFICA FINALE ---
        logging.info("\n--- FASE 5: VERIFYING FINAL STATE ---")
        _verify_final_state(workspace_id)

        logging.info("\n✅✅✅ Extended E2E Test PASSED! ✅✅✅")
        return True

    except Exception as e:
        logging.error(f"\n❌❌❌ Extended E2E Test FAILED: {e} ❌❌❌", exc_info=True)
        return False
    finally:
        # --- FASE 5: CLEANUP ---
        if workspace_id:
            logging.info("\n--- FASE 5: CLEANUP ---")
            _cleanup(workspace_id)

def _create_workspace_and_goal() -> str:
    """Crea un workspace e un obiettivo, restituendo il workspace_id."""
    # Create workspace
    workspace_data = {
        "name": f"E2E Test Workspace - {uuid4()}",
        "goal": "Generate a high-quality contact list of 10 potential leads in the SaaS industry."
    }
    response = requests.post(f"{BASE_URL}/api/workspaces", json=workspace_data, timeout=10)
    assert response.status_code in [200, 201], f"Workspace creation failed: {response.text}"
    workspace = response.json()
    workspace_id = workspace['id']
    logging.info(f"Workspace creato: {workspace_id}")

    # Create goal
    goal_data = {
        "workspace_id": workspace_id,
        "description": "Generate a high-quality contact list of 10 potential leads in the SaaS industry.",
        "metric_type": "deliverable_quality",
        "target_value": 90.0, # Target quality score
    }
    response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", json=goal_data, timeout=10)
    assert response.status_code in [200, 201], f"Goal creation failed: {response.text}"
    logging.info("Goal creato con successo.")
    return workspace_id

def _trigger_and_approve_proposal(workspace_id: str):
    """Crea e approva una proposta di team per avviare il flusso."""
    proposal_payload = {
        "workspace_id": workspace_id,
        "requirements": "Generate a high-quality contact list of 10 potential leads in the SaaS industry.",
        "budget_limit": 100.0
    }
    # Fase 2a: Generazione proposta (può richiedere fino a 2 minuti per team grossi)
    logging.info("⏳ Generando proposta di team (può richiedere fino a 2 minuti)...")
    response = requests.post(f"{BASE_URL}/api/director/proposal", json=proposal_payload, timeout=150)  # 2.5 minuti
    assert response.status_code == 200, f"Director proposal failed: {response.text}"
    proposal = response.json()
    proposal_id = proposal.get("proposal_id")
    assert proposal_id, "La risposta della proposta non contiene un proposal_id."
    logging.info(f"✅ Proposta di team generata: {proposal_id}")

    # Fase 2b: Conferma manuale simulata (in produzione sarebbe manuale)
    logging.info("📋 Simulando conferma manuale dell'utente...")
    time.sleep(1)  # Simula tempo di review da parte dell'utente
    
    # Fase 2c: Approvazione e avvio task generation (può richiedere 20-30 secondi)
    logging.info("⏳ Approvando proposta e avviando generazione task...")
    approval_response = requests.post(f"{BASE_URL}/api/director/approve/{workspace_id}", params={"proposal_id": proposal_id}, timeout=45)  # 45 secondi per task generation
    assert approval_response.status_code in [200, 204], f"Proposal approval failed: {approval_response.text}"
    logging.info("✅ Proposta approvata e task generation avviata.")

def _wait_for_task_creation(workspace_id: str, max_wait_time: int = 60) -> bool:
    """Attende che almeno un task sia stato creato nel workspace."""
    start_time = time.time()
    logging.info(f"⏳ Attendendo creazione task per un massimo di {max_wait_time} secondi...")
    
    while time.time() - start_time < max_wait_time:
        try:
            tasks_res = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=5)
            if tasks_res.status_code == 200:
                tasks = tasks_res.json()
                if isinstance(tasks, list) and len(tasks) > 0:
                    logging.info(f"✅ Task creati! Trovati {len(tasks)} task nel workspace")
                    return True
            
            elapsed = int(time.time() - start_time)
            logging.info(f"⏳ Ancora nessun task... ({elapsed}s/{max_wait_time}s)")
            time.sleep(5)
            
        except Exception as e:
            logging.error(f"Errore durante controllo task: {e}")
    
    logging.error(f"❌ Timeout: nessun task creato in {max_wait_time} secondi")
    return False

def _poll_for_completion(workspace_id: str) -> bool:
    """Interroga lo stato del workspace fino al completamento o al timeout, con logging diagnostico avanzato."""
    start_time = time.time()
    logging.info(f"Polling workspace {workspace_id} per un massimo di {WORKSPACE_COMPLETION_TIMEOUT} secondi...")
    failed_tasks_diagnosed = set()

    while time.time() - start_time < WORKSPACE_COMPLETION_TIMEOUT:
        try:
            # --- ESECUZIONE DIAGNOSTICA ---
            status_res = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}", timeout=5)
            goals_res = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", timeout=5)
            tasks_res = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=5)

            logging.info(f"--- DIAGNOSTICS (Time: {int(time.time() - start_time)}s) ---")

            # 1. Stampa stato del workspace
            if status_res.status_code == 200:
                workspace_data = status_res.json()
                logging.info(f"WORKSPACE STATUS: {json.dumps(workspace_data, indent=2)}")
                if workspace_data.get("status") == "completed":
                    logging.info("🎉🎉🎉 WORKSPACE COMPLETED! 🎉🎉🎉")
                    return True
            else:
                logging.warning(f"WORKSPACE STATUS: Code {status_res.status_code}, Response: {status_res.text}")

            # 2. Stampa stato dei goals (con fix per la struttura della risposta)
            if goals_res.status_code == 200:
                goals_data = goals_res.json()
                if isinstance(goals_data, dict) and 'goals' in goals_data and isinstance(goals_data['goals'], list):
                    goal_summary = [
                        {
                            "description": g.get('description', 'N/A')[:40],
                            "current": g.get('current_value'),
                            "target": g.get('target_value')
                        } for g in goals_data['goals']
                    ]
                    logging.info(f"GOALS: {json.dumps(goal_summary, indent=2)}")
                else:
                    logging.warning(f"GOALS data structure is not as expected: {goals_data}")
            else:
                logging.warning(f"GOALS: Code {goals_res.status_code}, Response: {goals_res.text}")

            # 3. Stampa riepilogo dei tasks e diagnostica i fallimenti
            if tasks_res.status_code == 200:
                tasks = tasks_res.json()
                if isinstance(tasks, list):
                    task_summary = {
                        "total": len(tasks),
                        "pending": len([t for t in tasks if t.get('status') == 'pending']),
                        "in_progress": len([t for t in tasks if t.get('status') == 'in_progress']),
                        "completed": len([t for t in tasks if t.get('status') == 'completed']),
                        "failed": len([t for t in tasks if t.get('status') == 'failed']),
                    }
                    logging.info(f"TASKS: {json.dumps(task_summary, indent=2)}")

                    # DIAGNOSTICA APPROFONDITA PER TASK FALLITI
                    failed_tasks = [t for t in tasks if t.get('status') == 'failed' and t.get('id') not in failed_tasks_diagnosed]
                    for task in failed_tasks:
                        task_id = task.get('id')
                        logging.error(f"🚨 DETECTED FAILED TASK: {task_id}. Retrieving details...")
                        try:
                            task_details_res = requests.get(f"{BASE_URL}/monitoring/task/{task_id}/status", timeout=5)
                            if task_details_res.status_code == 200:
                                logging.error(f"FAILED TASK DETAILS ({task_id}): {json.dumps(task_details_res.json(), indent=2)}")
                            else:
                                logging.error(f"Could not retrieve details for failed task {task_id}. Status: {task_details_res.status_code}")
                        except Exception as task_diag_e:
                            logging.error(f"Error retrieving details for task {task_id}: {task_diag_e}")
                        failed_tasks_diagnosed.add(task_id)
                else:
                    logging.warning(f"TASKS data is not a list of dicts: {tasks}")
            else:
                logging.warning(f"TASKS: Code {tasks_res.status_code}, Response: {tasks_res.text}")
            
            logging.info("------------------------------------")

        except Exception as diag_e:
            logging.error(f"CRITICAL Diagnostic Error: {diag_e}", exc_info=True)
        
        time.sleep(POLLING_INTERVAL)
        
    return False

def _verify_final_state(workspace_id: str):
    """Verifica lo stato finale del sistema dopo il completamento."""
    # 1. Verifica Task
    tasks_response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=10)
    assert tasks_response.status_code == 200, "Impossibile recuperare i task."
    tasks = tasks_response.json()
    assert len(tasks) > 0, "Nessun task è stato creato."
    completed_tasks = [t for t in tasks if t['status'] == 'completed']
    assert len(completed_tasks) > 0, "Nessun task è stato completato."
    logging.info(f"✅ VERIFICA TASK: {len(completed_tasks)}/{len(tasks)} task completati.")

    # 2. Verifica Deliverable
    deliverables_response = requests.get(f"{BASE_URL}/api/assets/artifacts/workspace/{workspace_id}", timeout=10)
    assert deliverables_response.status_code == 200, "Impossibile recuperare i deliverable."
    deliverables = deliverables_response.json()
    assert len(deliverables) > 0, "Nessun deliverable (artifact) è stato generato."
    logging.info(f"✅ VERIFICA DELIVERABLE: {len(deliverables)} artifact generati.")

    # 3. Verifica Qualità
    final_artifact = deliverables[0]
    quality_score = final_artifact.get("quality_score", 0.0)
    assert quality_score > 0, f"Il deliverable finale non ha un quality_score valido (score: {quality_score})."
    logging.info(f"✅ VERIFICA QUALITÀ: Il deliverable ha un quality_score di {quality_score:.2f}.")

    # 4. Verifica Memoria
    memory_response = requests.get(f"{BASE_URL}/api/memory/{workspace_id}/insights", timeout=10)
    assert memory_response.status_code == 200, "Impossibile recuperare gli insights dalla memoria."
    memory_insights = memory_response.json()
    contexts_stored = memory_insights.get("total_context_entries", 0)
    assert contexts_stored > 0, "Nessun contesto è stato memorizzato nel MemoryEngine."
    logging.info(f"✅ VERIFICA MEMORIA: {contexts_stored} contesti memorizzati.")

def _cleanup(workspace_id: str):
    """Pulisce le risorse create durante il test."""
    try:
        response = requests.delete(f"{BASE_URL}/api/workspaces/{workspace_id}", timeout=10)
        logging.info(f"Cleanup response: {response.status_code}")
    except Exception as e:
        logging.error(f"Cleanup fallito: {e}")

if __name__ == "__main__":
    if run_extended_e2e_test():
        exit(0)
    else:
        exit(1)
