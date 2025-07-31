"""
🔧 TEST SPECIFICO: TOOLS E HANDOFFS
Verifica se gli agenti usano effettivamente tools e handoffs con task mirati
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
import requests
from database import supabase
from ai_agents.manager import AgentManager
from uuid import UUID

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api"

class ToolsAndHandoffsTest:
    def __init__(self):
        self.workspace_id = None
        self.test_results = {
            "tools_usage": [],
            "handoffs_detected": [],
            "tasks_executed": []
        }
        
    async def run_test(self):
        logger.info("🔧 TESTING TOOLS AND HANDOFFS USAGE")
        logger.info("=" * 60)
        
        try:
            # Setup workspace
            await self._setup_test_workspace()
            
            # Crea team con diversi specialisti
            await self._create_diverse_team()
            
            # Crea task che FORZANO l'uso di tools e handoffs
            await self._create_tool_forcing_tasks()
            
            # Esegui task e monitora
            await self._execute_and_monitor_tasks()
            
            # Analizza risultati
            await self._analyze_results()
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)

    async def _setup_test_workspace(self):
        logger.info("\n📋 Setup Test Workspace")
        
        workspace_data = {
            "name": f"Tools & Handoffs Test {datetime.now().strftime('%H%M%S')}",
            "description": "Test workspace per verificare tools e handoffs"
        }
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        response.raise_for_status()
        workspace = response.json()
        self.workspace_id = workspace["id"]
        logger.info(f"✅ Workspace created: {self.workspace_id}")

    async def _create_diverse_team(self):
        logger.info("\n👥 Creating Diverse Team")
        
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Multi-domain project requiring research, development, design, and testing expertise",
            "budget": 150.0,
            "max_team_size": 4
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
        logger.info("✅ Team created with diverse specialists")

    async def _create_tool_forcing_tasks(self):
        logger.info("\n🎯 Creating Tasks That FORCE Tools and Handoffs Usage")
        
        # Task 1: Richiede WebSearch per informazioni attuali
        task1_data = {
            "workspace_id": self.workspace_id,
            "name": "Current Market Research: Python Web Scraping Tools 2024",
            "description": "Research and compare the TOP 5 Python web scraping libraries currently available in 2024. Include pricing, recent updates, GitHub stars, and community activity. This task REQUIRES current online research - do NOT use cached knowledge.",
            "priority": "high",
            "status": "pending"
        }
        
        # Task 2: Richiede handoff tra domini diversi
        task2_data = {
            "workspace_id": self.workspace_id,
            "name": "Design UI Mockup for Data Dashboard", 
            "description": "Create a UI/UX design mockup for a data visualization dashboard. This requires design expertise that may not be available to developers. Should be handed off to a designer if the current agent lacks UI/UX skills.",
            "priority": "high",
            "status": "pending"
        }
        
        # Task 3: Combina ricerca + handoff
        task3_data = {
            "workspace_id": self.workspace_id,
            "name": "Technical Architecture Analysis with Security Review",
            "description": "Research current best practices for secure Python web application architecture in 2024, then create a technical security review document. This may require both web research and specialized security expertise.",
            "priority": "medium",
            "status": "pending"
        }
        
        tasks_to_create = [task1_data, task2_data, task3_data]
        
        for task_data in tasks_to_create:
            result = supabase.table("tasks").insert(task_data).execute()
            if result.data:
                logger.info(f"✅ Created task: {task_data['name'][:50]}...")
            else:
                logger.error(f"❌ Failed to create task: {task_data['name']}")

    async def _execute_and_monitor_tasks(self):
        logger.info("\n🚀 Executing Tasks and Monitoring Tools/Handoffs")
        
        # Initialize AgentManager
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Get all pending tasks
        tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
        if tasks_response.status_code != 200:
            logger.error("Failed to get tasks")
            return
            
        tasks = tasks_response.json()
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        
        logger.info(f"Found {len(pending_tasks)} pending tasks")
        
        # Execute each task and monitor
        for i, task in enumerate(pending_tasks[:3], 1):  # Limite a 3 task
            task_id = task.get('id')
            task_name = task.get('name', 'Unknown')
            
            logger.info(f"\n🎯 [{i}/3] Executing: {task_name[:50]}...")
            logger.info(f"   Task ID: {task_id}")
            
            try:
                # Store pre-execution state for comparison
                pre_trace_count = await self._count_openai_traces()
                
                # Execute task
                result = await manager.execute_task(UUID(task_id))
                
                # Store post-execution state
                post_trace_count = await self._count_openai_traces()
                
                # Analyze execution
                execution_analysis = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "execution_time": getattr(result, 'execution_time', 0),
                    "status": getattr(result, 'status', 'unknown'),
                    "new_traces": post_trace_count - pre_trace_count
                }
                
                self.test_results["tasks_executed"].append(execution_analysis)
                
                # Check for tools and handoffs in result
                await self._analyze_task_execution(task_id, result)
                
                logger.info(f"   ✅ Task completed in {execution_analysis['execution_time']:.2f}s")
                logger.info(f"   📊 New traces generated: {execution_analysis['new_traces']}")
                
            except Exception as e:
                logger.error(f"   ❌ Task execution failed: {e}")

    async def _count_openai_traces(self) -> int:
        """Count current OpenAI traces (placeholder - would need OpenAI API access)"""
        # This is a placeholder since we can't directly access OpenAI trace API
        # In a real implementation, this would query the OpenAI traces
        return 0

    async def _analyze_task_execution(self, task_id: str, result):
        """Analyze task execution for tools and handoffs usage"""
        
        # Check task result for tool usage patterns
        result_content = str(getattr(result, 'result', ''))
        
        tools_used = []
        if 'search' in result_content.lower() or 'found' in result_content.lower():
            tools_used.append("WebSearchTool")
        if 'vector' in result_content.lower() or 'document' in result_content.lower():
            tools_used.append("FileSearchTool")
            
        if tools_used:
            self.test_results["tools_usage"].append({
                "task_id": task_id,
                "tools": tools_used
            })
            logger.info(f"   🔧 Tools detected: {', '.join(tools_used)}")
        else:
            logger.warning(f"   ⚠️ No tools detected in task result")
        
        # Check for handoff indicators
        if 'handoff' in result_content.lower() or 'transfer' in result_content.lower():
            self.test_results["handoffs_detected"].append({
                "task_id": task_id,
                "handoff_type": "detected_in_result"
            })
            logger.info(f"   🔄 Handoff detected in result")
        
        # Check database for delegation_chain updates
        try:
            task_data = supabase.table("tasks").select("context_data").eq("id", task_id).execute()
            if task_data.data and task_data.data[0].get('context_data'):
                context = task_data.data[0]['context_data']
                if 'delegation_chain' in context and len(context['delegation_chain']) > 0:
                    self.test_results["handoffs_detected"].append({
                        "task_id": task_id,
                        "handoff_type": "delegation_chain",
                        "chain_length": len(context['delegation_chain'])
                    })
                    logger.info(f"   🔄 Delegation chain found: {len(context['delegation_chain'])} handoffs")
        except Exception as e:
            logger.debug(f"Could not check delegation chain: {e}")

    async def _analyze_results(self):
        logger.info("\n📊 ANALISI RISULTATI FINALI")
        logger.info("=" * 60)
        
        tasks_count = len(self.test_results["tasks_executed"])
        tools_count = len(self.test_results["tools_usage"])
        handoffs_count = len(self.test_results["handoffs_detected"])
        
        logger.info(f"📋 TASK ESEGUITI: {tasks_count}")
        for task in self.test_results["tasks_executed"]:
            logger.info(f"   - {task['task_name'][:40]}... ({task['status']})")
        
        logger.info(f"\n🔧 TOOLS UTILIZZATI: {tools_count}")
        if tools_count > 0:
            for tool_usage in self.test_results["tools_usage"]:
                logger.info(f"   - Task {tool_usage['task_id'][:8]}...: {', '.join(tool_usage['tools'])}")
        else:
            logger.warning("   ❌ NESSUN TOOL UTILIZZATO!")
        
        logger.info(f"\n🔄 HANDOFFS RILEVATI: {handoffs_count}")
        if handoffs_count > 0:
            for handoff in self.test_results["handoffs_detected"]:
                logger.info(f"   - Task {handoff['task_id'][:8]}...: {handoff['handoff_type']}")
        else:
            logger.warning("   ❌ NESSUN HANDOFF RILEVATO!")
        
        # Calcola percentuali
        tools_percentage = (tools_count / tasks_count * 100) if tasks_count > 0 else 0
        handoffs_percentage = (handoffs_count / tasks_count * 100) if tasks_count > 0 else 0
        
        logger.info(f"\n📈 STATISTICHE:")
        logger.info(f"   Tools Usage Rate: {tools_percentage:.1f}%")
        logger.info(f"   Handoffs Rate: {handoffs_percentage:.1f}%")
        
        # Diagnosi
        logger.info(f"\n🔍 DIAGNOSI:")
        
        if tools_count == 0:
            logger.warning("❌ PROBLEMA: Agenti non usano tools")
            logger.info("   Possibili cause:")
            logger.info("   - WebSearchTool non configurato correttamente")
            logger.info("   - FileSearchTool richiede vector_store_ids")
            logger.info("   - Task non richiedono ricerca esterna")
            logger.info("   - Prompt non efficace nel forzare tool usage")
        
        if handoffs_count == 0:
            logger.warning("❌ PROBLEMA: Agenti non usano handoffs")
            logger.info("   Possibili cause:")
            logger.info("   - Agenti troppo confidenti nelle loro capacità")
            logger.info("   - Handoff tools non configurati correttamente")
            logger.info("   - Task non richiedono expertise cross-domain")
            logger.info("   - Prompt scoraggia handoffs")
        
        if tools_count > 0 and handoffs_count > 0:
            logger.info("✅ SUCCESS: Agenti usano sia tools che handoffs")
        elif tools_count > 0:
            logger.info("⚠️ PARTIAL: Agenti usano tools ma non handoffs")
        elif handoffs_count > 0:
            logger.info("⚠️ PARTIAL: Agenti usano handoffs ma non tools")
        else:
            logger.error("❌ FAILURE: Agenti non usano né tools né handoffs")
        
        # Salva risultati
        results_file = f"tools_handoffs_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"\n💾 Risultati salvati in: {results_file}")


async def main():
    test = ToolsAndHandoffsTest()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())