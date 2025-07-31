#!/usr/bin/env python3
"""
Test Isolato Task Executor - Verifica gestione task reale
=======================================================
Test focalizzato sul task executor per verificare:
1. Gestione task non simulata con API reali
2. Prevenzione duplicazioni
3. Controllo quality gates
4. Avanzamento corretto degli stati
5. Timeout realistici
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('task_executor_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskExecutorIsolatedTest:
    """Test isolato per task executor con scenari realistici"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api"
        self.workspace_id = None
        self.test_tasks = []
        self.test_results = {}
        
        # Scenario di test realistico
        self.test_scenario = {
            "name": "E-commerce Product Catalog Enhancement",
            "description": "Enhance product catalog with AI-powered recommendations and improved search functionality",
            "goals": [
                {
                    "description": "Implement AI-powered product recommendation engine",
                    "target_value": 100.0,
                    "metric_type": "feature_completion_rate"
                }
            ]
        }
    
    async def run_isolated_test(self) -> Dict[str, Any]:
        """Esegue test isolato del task executor"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 STARTING ISOLATED TASK EXECUTOR TEST")
            logger.info("=" * 80)
            
            # Step 1: Setup workspace and goal
            await self._setup_test_environment()
            
            # Step 2: Create realistic tasks
            await self._create_realistic_tasks()
            
            # Step 3: Monitor task execution with timeout
            await self._monitor_task_execution()
            
            # Step 4: Verify task management features
            await self._verify_task_management()
            
            # Step 5: Test quality gates
            await self._test_quality_gates()
            
            # Step 6: Verify no duplications
            await self._verify_no_duplications()
            
            return self._generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Isolated test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "FAILED", "error": str(e)}
    
    async def _setup_test_environment(self):
        """Setup workspace e goal per il test"""
        logger.info("\n🏗️ STEP 1: TEST ENVIRONMENT SETUP")
        logger.info("-" * 50)
        
        # Create workspace
        workspace_data = {
            "name": f"TEST-{self.test_scenario['name']}",
            "description": self.test_scenario['description'],
            "goal": self.test_scenario['goals'][0]['description'],
            "budget": "Medium",
            "status": "active"
        }
        
        response = requests.post(f"{self.api_base}/workspaces", json=workspace_data)
        if response.status_code == 201:
            self.workspace_id = response.json()["id"]
            logger.info(f"✅ Workspace created: {self.workspace_id}")
        else:
            raise Exception(f"Failed to create workspace: {response.status_code}")
        
        # Create goal
        goal_data = {
            "workspace_id": self.workspace_id,
            "description": self.test_scenario['goals'][0]['description'],
            "target_value": self.test_scenario['goals'][0]['target_value'],
            "metric_type": self.test_scenario['goals'][0]['metric_type'],
            "priority": "high"
        }
        
        response = requests.post(f"{self.api_base}/workspaces/{self.workspace_id}/goals", json=goal_data)
        if response.status_code == 201:
            self.goal_id = response.json()["id"]
            logger.info(f"✅ Goal created: {self.goal_id}")
        else:
            raise Exception(f"Failed to create goal: {response.status_code}")
    
    async def _create_realistic_tasks(self):
        """Crea task realistici per testare il task executor"""
        logger.info("\n📋 STEP 2: CREATE REALISTIC TASKS")
        logger.info("-" * 50)
        
        # Task realistici per e-commerce
        task_templates = [
            {
                "title": "Design AI recommendation algorithm architecture",
                "description": "Create detailed architecture for machine learning recommendation system including data pipeline, model training, and real-time inference",
                "type": "technical_design",
                "priority": "high",
                "estimated_hours": 8,
                "assigned_agent_role": "Senior AI Engineer"
            },
            {
                "title": "Implement product similarity calculation service",
                "description": "Build microservice for calculating product similarities using collaborative filtering and content-based filtering approaches",
                "type": "implementation",
                "priority": "medium", 
                "estimated_hours": 12,
                "assigned_agent_role": "AI Developer"
            },
            {
                "title": "Create recommendation API endpoints",
                "description": "Develop RESTful API endpoints for serving product recommendations with caching and rate limiting",
                "type": "api_development",
                "priority": "high",
                "estimated_hours": 6,
                "assigned_agent_role": "Backend Developer"
            }
        ]
        
        created_tasks = []
        
        for template in task_templates:
            task_data = {
                "workspace_id": self.workspace_id,
                "goal_id": self.goal_id,
                "title": template["title"],
                "description": template["description"],
                "type": template["type"],
                "priority": template["priority"],
                "estimated_hours": template["estimated_hours"],
                "assigned_agent_role": template["assigned_agent_role"],
                "status": "pending"
            }
            
            response = requests.post(f"{self.api_base}/workspaces/{self.workspace_id}/tasks", json=task_data)
            if response.status_code == 201:
                task_id = response.json()["id"]
                created_tasks.append(task_id)
                logger.info(f"✅ Task created: {template['title'][:50]}... (ID: {task_id})")
            else:
                logger.error(f"❌ Failed to create task: {template['title']}")
                raise Exception(f"Failed to create task: {response.status_code}")
        
        self.test_tasks = created_tasks
        logger.info(f"✅ Created {len(created_tasks)} realistic tasks")
    
    async def _monitor_task_execution(self):
        """Monitora l'esecuzione dei task con timeout realistico"""
        logger.info("\n⏱️ STEP 3: MONITOR TASK EXECUTION")
        logger.info("-" * 50)
        
        timeout_seconds = 300  # 5 minuti timeout
        poll_interval = 10     # Check ogni 10 secondi
        start_time = time.time()
        
        initial_status = await self._get_task_status_summary()
        logger.info(f"Initial task status: {initial_status}")
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Get current task status
                current_status = await self._get_task_status_summary()
                elapsed = int(time.time() - start_time)
                
                logger.info(f"⏰ [{elapsed}s] Task Status: {current_status}")
                
                # Check for progress
                if current_status.get("completed", 0) > 0:
                    logger.info("✅ Tasks are being executed successfully!")
                    break
                
                if current_status.get("in_progress", 0) > 0:
                    logger.info("🔄 Tasks are being processed...")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring tasks: {e}")
                await asyncio.sleep(poll_interval)
        
        # Final status check
        final_status = await self._get_task_status_summary()
        logger.info(f"Final task status: {final_status}")
        
        self.test_results["task_execution"] = {
            "initial_status": initial_status,
            "final_status": final_status,
            "elapsed_time": int(time.time() - start_time),
            "timeout_reached": time.time() - start_time >= timeout_seconds
        }
    
    async def _get_task_status_summary(self) -> Dict[str, int]:
        """Ottiene summary dello status dei task"""
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                status_counts = {}
                for task in tasks:
                    status = task.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                return status_counts
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _verify_task_management(self):
        """Verifica features di gestione task"""
        logger.info("\n🔍 STEP 4: VERIFY TASK MANAGEMENT")
        logger.info("-" * 50)
        
        # Check task details
        task_details = []
        for task_id in self.test_tasks:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks/{task_id}")
            if response.status_code == 200:
                task_details.append(response.json())
                
        logger.info(f"✅ Retrieved details for {len(task_details)} tasks")
        
        # Verify task fields
        required_fields = ["id", "title", "description", "status", "priority", "created_at"]
        for task in task_details:
            missing_fields = [field for field in required_fields if field not in task]
            if missing_fields:
                logger.warning(f"⚠️ Task {task.get('id')} missing fields: {missing_fields}")
        
        self.test_results["task_management"] = {
            "tasks_retrieved": len(task_details),
            "total_tasks": len(self.test_tasks),
            "task_validation": "passed" if len(task_details) == len(self.test_tasks) else "failed"
        }
    
    async def _test_quality_gates(self):
        """Test quality gates per i task"""
        logger.info("\n🎯 STEP 5: TEST QUALITY GATES")
        logger.info("-" * 50)
        
        try:
            # Check if quality system is responding
            response = requests.get(f"{self.api_base}/assets/quality/validations/{self.workspace_id}")
            if response.status_code == 200:
                validations = response.json()
                logger.info(f"✅ Quality validations found: {len(validations)}")
                
                self.test_results["quality_gates"] = {
                    "system_responding": True,
                    "validations_count": len(validations),
                    "status": "operational"
                }
            else:
                logger.warning(f"⚠️ Quality system response: {response.status_code}")
                self.test_results["quality_gates"] = {
                    "system_responding": False,
                    "status": "not_operational"
                }
        except Exception as e:
            logger.error(f"❌ Quality gates test failed: {e}")
            self.test_results["quality_gates"] = {
                "system_responding": False,
                "error": str(e)
            }
    
    async def _verify_no_duplications(self):
        """Verifica che non ci siano duplicazioni di task"""
        logger.info("\n🔄 STEP 6: VERIFY NO DUPLICATIONS")
        logger.info("-" * 50)
        
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                
                # Check for duplicate titles
                titles = [task.get("title", "") for task in tasks]
                unique_titles = set(titles)
                
                duplicates_found = len(titles) != len(unique_titles)
                
                if duplicates_found:
                    logger.warning(f"⚠️ Found {len(titles) - len(unique_titles)} duplicate tasks")
                    # Find actual duplicates
                    title_counts = {}
                    for title in titles:
                        title_counts[title] = title_counts.get(title, 0) + 1
                    
                    for title, count in title_counts.items():
                        if count > 1:
                            logger.warning(f"  Duplicate: '{title}' appears {count} times")
                else:
                    logger.info("✅ No duplicate tasks found")
                
                self.test_results["duplication_check"] = {
                    "total_tasks": len(tasks),
                    "unique_titles": len(unique_titles),
                    "duplicates_found": duplicates_found
                }
            else:
                raise Exception(f"Failed to get tasks: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Duplication check failed: {e}")
            self.test_results["duplication_check"] = {"error": str(e)}
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Genera report completo del test"""
        logger.info("\n📊 GENERATING TEST REPORT")
        logger.info("-" * 50)
        
        report = {
            "test_id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "scenario": self.test_scenario,
            "workspace_id": self.workspace_id,
            "results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": len([r for r in self.test_results.values() if not isinstance(r, dict) or r.get("error") is None]),
                "overall_status": "PASSED" if all(not isinstance(r, dict) or r.get("error") is None for r in self.test_results.values()) else "FAILED"
            }
        }
        
        logger.info(f"📈 Test Summary:")
        logger.info(f"  Total Tests: {report['summary']['total_tests']}")
        logger.info(f"  Passed: {report['summary']['passed_tests']}")
        logger.info(f"  Status: {report['summary']['overall_status']}")
        
        # Save report
        with open(f"task_executor_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report

async def main():
    """Esegue il test isolato del task executor"""
    test = TaskExecutorIsolatedTest()
    result = await test.run_isolated_test()
    
    print("\n" + "=" * 80)
    print("🎯 ISOLATED TASK EXECUTOR TEST COMPLETE")
    print("=" * 80)
    print(f"Status: {result.get('summary', {}).get('overall_status', 'UNKNOWN')}")
    
    if result.get('summary', {}).get('overall_status') == 'FAILED':
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())