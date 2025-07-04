
import asyncio
import json
import logging
import subprocess
import time
import requests
import os
from uuid import uuid4

# --- CONFIGURAZIONE (TODO: Sostituire con valori reali) ---
BASE_URL = "http://127.0.0.1:8000"
SERVER_LOG_PATH = "/Users/pelleri/Documents/ai-team-orchestrator/server.log"
DB_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING") # Esempio, adattare al driver DB
WORKSPACE_ID = None
GOAL_ID = None
TRACE_ID = str(uuid4())

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FUNZIONI DI AUDIT ---

async def start_server():
    """Avvia il server backend in un processo separato."""
    logging.info("Avvio del server backend...")
    # Assicurarsi che il server venga eseguito dalla directory corretta
    server_process = subprocess.Popen(
        ["/Users/pelleri/Documents/ai-team-orchestrator/backend/.venv/bin/python", "main.py"],
        cwd="/Users/pelleri/Documents/ai-team-orchestrator/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    await asyncio.sleep(15) # Attendi che il server si avvii
    
    # Leggi e stampa l'output del server per il debug
    server_output = server_process.stderr.read().decode()
    if server_output:
        logging.info(f"Output del server:\n{server_output}")
    logging.info(f"Server avviato con PID: {server_process.pid}")
    return server_process

def stop_server(process):
    """Ferma il processo del server."""
    logging.info("Fermo del server backend...")
    process.terminate()
    process.wait()
    logging.info("Server fermato.")

def inject_goal():
    """Inietta un workspace e un goal di test via API."""
    global WORKSPACE_ID, GOAL_ID
    headers = {"X-Trace-ID": TRACE_ID}
    workspace_data = {"name": f"Audit-Test-Workspace-{int(time.time())}"}
    
    try:
        response = requests.post(f"{BASE_URL}/workspaces", json=workspace_data, headers=headers, timeout=15)
        response.raise_for_status()
        WORKSPACE_ID = response.json()["id"]
        logging.info(f"Workspace di test creato con successo. WORKSPACE_ID: {WORKSPACE_ID}")

        goal_data = {"description": "Audit test goal: validate E2E tracing."}
        response = requests.post(f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/goals", json=goal_data, headers=headers, timeout=15)
        response.raise_for_status()
        GOAL_ID = response.json()["id"]
        logging.info(f"Goal di test creato con successo. GOAL_ID: {GOAL_ID}")
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante l'iniezione del goal: {e}")
        raise

def trace_in_logs():
    """Verifica la presenza del Trace ID nei log del server."""
    logging.info(f"Verifica del TRACE_ID ({TRACE_ID}) in {SERVER_LOG_PATH}...")
    try:
        with open(SERVER_LOG_PATH, "r") as f:
            logs = f.read()
            if TRACE_ID in logs:
                logging.info("✅ TRACE_ID trovato nei log del server.")
                return True
            else:
                logging.warning("❌ TRACE_ID NON trovato nei log del server.")
                return False
    except FileNotFoundError:
        logging.error(f"File di log non trovato: {SERVER_LOG_PATH}")
        return False

async def trace_in_database():
    """Verifica la propagazione del Trace ID nel database."""
    # Questa è una pseudo-implementazione. Richiede un driver DB come psycopg2.
    # TODO: Implementare con il driver DB corretto.
    logging.info("Verifica della propagazione del TRACE_ID nel database (pseudo-codice)...")
    
    # Esempio di query per verificare la presenza del trace_id
    # query_tasks = f"SELECT COUNT(*) FROM tasks WHERE trace_id = '{TRACE_ID}';"
    # query_events = f"SELECT COUNT(*) FROM integration_events WHERE trace_id = '{TRACE_ID}';"
    
    # In un'implementazione reale, si eseguirebbero queste query.
    # Per ora, simuliamo un successo parziale.
    logging.warning("⚠️ La verifica del DB è simulata. Implementare con un driver reale.")
    logging.info("✅ (Simulato) Trovato riferimento al WORKSPACE_ID nella tabella tasks.")
    logging.warning("❌ (Simulato) Campo trace_id non trovato nelle tabelle principali.")
    return True

async def check_for_duplicates():
    """Verifica la presenza di duplicati nel database."""
    logging.info("Verifica di duplicati nel database (pseudo-codice)...")
    
    # Esempio di query per rilevare task duplicati
    # query_duplicates = """
    # SELECT name, COUNT(*)
    # FROM tasks
    # WHERE workspace_id = '{WORKSPACE_ID}'
    # GROUP BY name
    # HAVING COUNT(*) > 1;
    # """
    
    logging.warning("⚠️ La verifica dei duplicati è simulata.")
    logging.info("✅ (Simulato) Nessun task duplicato trovato per il workspace di test.")
    return True

async def main():
    """Funzione principale dell'audit."""
    server_process = None
    try:
        server_process = await start_server()
        inject_goal()
        
        logging.info("Attesa di 30 secondi per la propagazione degli eventi...")
        await asyncio.sleep(30)
        
        trace_in_logs()
        await trace_in_database()
        await check_for_duplicates()
        
    finally:
        if server_process:
            stop_server(server_process)
        logging.info("Audit completato.")

if __name__ == "__main__":
    asyncio.run(main())
