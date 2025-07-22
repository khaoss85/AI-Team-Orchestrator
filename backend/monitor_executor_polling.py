#!/usr/bin/env python3
"""
Monitor executor polling in real-time per vedere i log dettagliati
"""

import subprocess
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_executor_logs():
    """Monitor dei log del server per vedere l'executor polling"""
    
    logger.info("🔍 Starting executor polling monitor")
    logger.info("Looking for POLLING logs from executor...")
    
    # Verifica che il server sia attivo
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Server is running")
        else:
            logger.error("❌ Server is not responding")
            return
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        return
    
    # Check executor status
    try:
        response = requests.get("http://localhost:8000/monitoring/executor/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            logger.info(f"✅ Executor status: {status}")
        else:
            logger.error(f"❌ Executor status failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Executor status error: {e}")
    
    logger.info("📊 Monitor running for 60 seconds...")
    logger.info("Look for lines containing '🔍 POLLING' in the server output")
    logger.info("If you don't see these logs, the executor polling loop is not running")
    
    # Wait and periodically check
    for i in range(12):  # 60 seconds, check every 5 seconds
        time.sleep(5)
        logger.info(f"⏰ Monitoring... {(i+1)*5}s elapsed")
        
        # Check if any tasks moved to queue
        try:
            response = requests.get("http://localhost:8000/monitoring/executor/detailed-stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                tasks_in_queue = stats.get('tasks_in_queue', 0)
                active_tasks = stats.get('active_tasks', 0)
                if tasks_in_queue > 0 or active_tasks > 0:
                    logger.info(f"🚀 ACTIVITY DETECTED! Queue: {tasks_in_queue}, Active: {active_tasks}")
                    break
                else:
                    logger.info(f"📊 Still empty - Queue: {tasks_in_queue}, Active: {active_tasks}")
        except Exception as e:
            logger.warning(f"⚠️ Stats check failed: {e}")
    
    logger.info("🏁 Monitoring complete")
    logger.info("Check the server logs for '🔍 POLLING' messages")

if __name__ == "__main__":
    monitor_executor_logs()