#!/usr/bin/env python3
"""
SYSTEMATIC TASK FLOW ANALYZER
=============================
Analisi architetturale completa del flusso task execution
Approccio sistematico: analizza architettura e dipendenze, non quick-fix
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Import per accesso diretto al database
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_tasks, list_agents, get_workspaces_with_pending_tasks

class TaskExecutionFlowAnalyzer:
    """Analizzatore sistematico del flusso di esecuzione task"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api"
        self.analysis_results = {}
        
    async def analyze_complete_flow(self, workspace_id: str) -> Dict[str, Any]:
        """Analisi completa di tutti i layer del sistema"""
        
        logger.info("🏗️ STARTING SYSTEMATIC ARCHITECTURE ANALYSIS")
        logger.info("=" * 60)
        
        results = {
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "layers": {}
        }
        
        # LAYER 1: Database Layer
        logger.info("📊 LAYER 1: DATABASE ANALYSIS")
        results["layers"]["database"] = await self._analyze_database_layer(workspace_id)
        
        # LAYER 2: Executor Polling Layer  
        logger.info("🔍 LAYER 2: EXECUTOR POLLING ANALYSIS")
        results["layers"]["executor_polling"] = await self._analyze_executor_polling_layer()
        
        # LAYER 3: Task Queue Layer
        logger.info("📋 LAYER 3: TASK QUEUE ANALYSIS")
        results["layers"]["task_queue"] = await self._analyze_task_queue_layer()
        
        # LAYER 4: Agent Manager Layer
        logger.info("👥 LAYER 4: AGENT MANAGER ANALYSIS")
        results["layers"]["agent_manager"] = await self._analyze_agent_manager_layer(workspace_id)
        
        # LAYER 5: OpenAI SDK Layer
        logger.info("🤖 LAYER 5: OPENAI SDK ANALYSIS")
        results["layers"]["openai_sdk"] = await self._analyze_openai_sdk_layer()
        
        # COMPREHENSIVE DIAGNOSIS
        logger.info("🎯 COMPREHENSIVE DIAGNOSIS")
        results["diagnosis"] = self._generate_diagnosis(results["layers"])
        
        return results
    
    async def _analyze_database_layer(self, workspace_id: str) -> Dict[str, Any]:
        """Analisi completa del layer database"""
        analysis = {}
        
        try:
            # Check workspace with pending tasks
            workspaces_with_pending = await get_workspaces_with_pending_tasks()
            analysis["workspaces_with_pending"] = workspaces_with_pending
            analysis["target_workspace_in_pending"] = workspace_id in workspaces_with_pending
            
            # Check tasks
            all_tasks = await list_tasks(workspace_id)
            pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
            analysis["total_tasks"] = len(all_tasks)
            analysis["pending_tasks"] = len(pending_tasks)
            
            # Check agents
            agents = await list_agents(workspace_id) 
            available_agents = [a for a in agents if a.get('status') == 'available']
            analysis["total_agents"] = len(agents)
            analysis["available_agents"] = len(available_agents)
            
            # Task assignment analysis
            assigned_tasks = [t for t in pending_tasks if t.get('agent_id')]
            unassigned_tasks = [t for t in pending_tasks if not t.get('agent_id')]
            analysis["assigned_pending_tasks"] = len(assigned_tasks)
            analysis["unassigned_pending_tasks"] = len(unassigned_tasks)
            
            # Detailed task info
            if assigned_tasks:
                sample_task = assigned_tasks[0]
                analysis["sample_assigned_task"] = {
                    "id": sample_task.get('id'),
                    "name": sample_task.get('name'),
                    "agent_id": sample_task.get('agent_id'),
                    "status": sample_task.get('status'),
                    "created_at": sample_task.get('created_at')
                }
            
            analysis["status"] = "healthy"
            logger.info(f"✅ DATABASE: {len(workspaces_with_pending)} workspaces, {len(pending_tasks)} pending tasks, {len(available_agents)} available agents")
            
        except Exception as e:
            analysis["status"] = "error"
            analysis["error"] = str(e)
            logger.error(f"❌ DATABASE ERROR: {e}")
            
        return analysis
    
    async def _analyze_executor_polling_layer(self) -> Dict[str, Any]:
        """Analisi del layer executor polling"""
        analysis = {}
        
        try:
            # Check executor status
            response = requests.get(f"{self.base_url}/monitoring/executor/status", timeout=5)
            if response.status_code == 200:
                executor_status = response.json()
                analysis["executor_status"] = executor_status
                analysis["is_running"] = executor_status.get('is_running', False)
                analysis["is_paused"] = executor_status.get('is_paused', True)
                
                if analysis["is_running"] and not analysis["is_paused"]:
                    analysis["status"] = "healthy"
                    logger.info(f"✅ EXECUTOR: Running and active")
                else:
                    analysis["status"] = "unhealthy"
                    logger.warning(f"⚠️ EXECUTOR: Not running or paused")
            else:
                analysis["status"] = "error"
                analysis["error"] = f"Status endpoint returned {response.status_code}"
                logger.error(f"❌ EXECUTOR: Status endpoint failed")
                
        except Exception as e:
            analysis["status"] = "error"
            analysis["error"] = str(e)
            logger.error(f"❌ EXECUTOR ERROR: {e}")
            
        return analysis
    
    async def _analyze_task_queue_layer(self) -> Dict[str, Any]:
        """Analisi del layer task queue interno"""
        analysis = {}
        
        try:
            # Try to get queue stats if available
            response = requests.get(f"{self.base_url}/monitoring/executor/detailed-stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                analysis["queue_stats"] = stats
                analysis["tasks_in_queue"] = stats.get('tasks_in_queue', 0)
                analysis["active_tasks"] = stats.get('active_tasks', 0)
                analysis["completed_tasks"] = stats.get('tasks_completed_successfully', 0)
                analysis["failed_tasks"] = stats.get('tasks_failed', 0)
                
                if analysis["tasks_in_queue"] > 0 or analysis["active_tasks"] > 0:
                    analysis["status"] = "active"
                    logger.info(f"✅ TASK QUEUE: {analysis['tasks_in_queue']} queued, {analysis['active_tasks']} active")
                else:
                    analysis["status"] = "empty"
                    logger.warning(f"⚠️ TASK QUEUE: Empty (no queued or active tasks)")
            else:
                analysis["status"] = "unknown"
                analysis["error"] = f"Stats endpoint returned {response.status_code}"
                logger.warning(f"⚠️ TASK QUEUE: Stats unavailable")
                
        except Exception as e:
            analysis["status"] = "error" 
            analysis["error"] = str(e)
            logger.error(f"❌ TASK QUEUE ERROR: {e}")
            
        return analysis
    
    async def _analyze_agent_manager_layer(self, workspace_id: str) -> Dict[str, Any]:
        """Analisi del layer agent manager"""
        analysis = {}
        
        try:
            # Check agents API endpoint
            response = requests.get(f"{self.base_url}/agents/{workspace_id}", timeout=5)
            if response.status_code == 200:
                agents_data = response.json()
                analysis["agents_accessible"] = True
                analysis["agents_count"] = len(agents_data)
                
                # Check agent capabilities
                if agents_data:
                    sample_agent = agents_data[0]
                    analysis["sample_agent"] = {
                        "id": sample_agent.get('id'),
                        "name": sample_agent.get('name'),
                        "role": sample_agent.get('role'),
                        "status": sample_agent.get('status')
                    }
                
                analysis["status"] = "healthy"
                logger.info(f"✅ AGENT MANAGER: {len(agents_data)} agents accessible")
            else:
                analysis["status"] = "error"
                analysis["error"] = f"Agents endpoint returned {response.status_code}"
                logger.error(f"❌ AGENT MANAGER: Agents endpoint failed")
                
        except Exception as e:
            analysis["status"] = "error"
            analysis["error"] = str(e)
            logger.error(f"❌ AGENT MANAGER ERROR: {e}")
            
        return analysis
    
    async def _analyze_openai_sdk_layer(self) -> Dict[str, Any]:
        """Analisi del layer OpenAI SDK"""
        analysis = {}
        
        try:
            # Check if OpenAI API key is configured
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            analysis["api_key_configured"] = bool(api_key and len(api_key) > 10)
            
            if analysis["api_key_configured"]:
                analysis["api_key_length"] = len(api_key)
                analysis["status"] = "configured"
                logger.info(f"✅ OPENAI SDK: API key configured ({len(api_key)} chars)")
            else:
                analysis["status"] = "not_configured"
                logger.error(f"❌ OPENAI SDK: API key not configured")
                
        except Exception as e:
            analysis["status"] = "error"
            analysis["error"] = str(e)
            logger.error(f"❌ OPENAI SDK ERROR: {e}")
            
        return analysis
    
    def _generate_diagnosis(self, layers: Dict[str, Any]) -> Dict[str, Any]:
        """Genera diagnosi completa basata sull'analisi di tutti i layer"""
        
        diagnosis = {
            "overall_health": "unknown",
            "broken_layers": [],
            "healthy_layers": [],
            "critical_issues": [],
            "recommendations": []
        }
        
        # Analyze each layer
        for layer_name, layer_data in layers.items():
            layer_status = layer_data.get('status', 'unknown')
            
            if layer_status in ['healthy', 'configured', 'active']:
                diagnosis["healthy_layers"].append(layer_name)
            elif layer_status in ['error', 'unhealthy', 'not_configured']:
                diagnosis["broken_layers"].append(layer_name)
                diagnosis["critical_issues"].append(f"{layer_name}: {layer_data.get('error', 'Unknown issue')}")
        
        # Database layer analysis
        db_layer = layers.get('database', {})
        if db_layer.get('assigned_pending_tasks', 0) > 0:
            diagnosis["recommendations"].append("✅ Tasks are correctly assigned to agents")
        else:
            diagnosis["critical_issues"].append("❌ No assigned pending tasks found")
            
        # Task queue analysis  
        queue_layer = layers.get('task_queue', {})
        if queue_layer.get('tasks_in_queue', 0) == 0 and queue_layer.get('active_tasks', 0) == 0:
            diagnosis["critical_issues"].append("❌ No tasks in executor queue - polling mechanism broken")
            diagnosis["recommendations"].append("🔧 Check executor polling logic and task filtering")
        
        # Overall health
        if len(diagnosis["broken_layers"]) == 0:
            diagnosis["overall_health"] = "healthy"
        elif len(diagnosis["broken_layers"]) < len(layers) / 2:
            diagnosis["overall_health"] = "degraded"
        else:
            diagnosis["overall_health"] = "critical"
            
        return diagnosis

async def main():
    """Main analysis function"""
    
    analyzer = TaskExecutionFlowAnalyzer()
    
    # Use the workspace we know has pending tasks
    workspace_id = "5756d14c-6ff7-4d9e-a889-14b12bdf293c"
    
    # Run comprehensive analysis
    results = await analyzer.analyze_complete_flow(workspace_id)
    
    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("🎯 SYSTEMATIC ANALYSIS RESULTS")
    logger.info("=" * 60)
    
    diagnosis = results["diagnosis"]
    logger.info(f"🏥 Overall Health: {diagnosis['overall_health'].upper()}")
    
    if diagnosis["healthy_layers"]:
        logger.info(f"✅ Healthy Layers: {', '.join(diagnosis['healthy_layers'])}")
        
    if diagnosis["broken_layers"]:
        logger.info(f"❌ Broken Layers: {', '.join(diagnosis['broken_layers'])}")
        
    if diagnosis["critical_issues"]:
        logger.info("🚨 Critical Issues:")
        for issue in diagnosis["critical_issues"]:
            logger.info(f"   {issue}")
            
    if diagnosis["recommendations"]:
        logger.info("💡 Recommendations:")
        for rec in diagnosis["recommendations"]:
            logger.info(f"   {rec}")
    
    # Save detailed results
    with open('systematic_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    logger.info("📄 Detailed results saved to systematic_analysis_results.json")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    print("\n🎯 SYSTEMATIC ANALYSIS COMPLETE")
    print("Run this script to identify the exact broken layer in task execution flow")