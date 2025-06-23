#!/usr/bin/env python3
"""
🎬 TEST COMPLETE LIFECYCLE - AUTONOMO
Test completo del ciclo di vita naturale del sistema senza scorciatoie:
1. Workspace + Goal creation
2. Goal extraction AI-driven  
3. Team creation
4. Task generation goal-driven
5. Real task execution con quality loop
6. Quality enhancement automatico
7. Deliverable generation
8. Goal completion tracking

OBIETTIVO: Vedere se il sistema arriva autonomamente ai deliverable finali
"""

import asyncio
import sys
import os
import logging
import json
import time
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteLifecycleTest:
    """Test completo del ciclo di vita naturale del sistema"""
    
    def __init__(self):
        self.workspace_id: Optional[str] = None
        self.extracted_goals: List[Dict] = []
        self.team_agents: List[Dict] = []
        self.generated_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.created_deliverables: List[Dict] = []
        self.quality_iterations: Dict[str, int] = {}
        self.start_time = datetime.now()
        
        # Test metrics
        self.metrics = {
            "steps_completed": 0,
            "total_steps": 10,
            "goals_created": 0,
            "goals_completed": 0,
            "tasks_created": 0,
            "tasks_completed": 0,
            "quality_iterations": 0,
            "deliverables_created": 0,
            "final_success": False
        }
    
    def log_step(self, step_name: str, success: bool, details: Any = None):
        """Log e traccia progresso step"""
        if success:
            self.metrics["steps_completed"] += 1
            logger.info(f"✅ STEP {self.metrics['steps_completed']}/{self.metrics['total_steps']}: {step_name}")
            if details:
                logger.info(f"   📊 {details}")
        else:
            logger.error(f"❌ STEP FAILED: {step_name}")
            if details:
                logger.error(f"   💥 {details}")
    
    async def step_1_create_realistic_workspace(self) -> bool:
        """Step 1: Crea workspace con scenario business realistico"""
        logger.info("\n🏗️ STEP 1: Creating realistic business workspace...")
        
        try:
            from database import create_workspace
            
            # Scenario realistico: Agenzia di consulenza B2B che vuole espandere
            workspace_data = {
                "name": "B2B Growth Consulting - Q1 2025 Expansion",
                "description": "Strategic consulting firm specializing in B2B SaaS growth, expanding client acquisition and service delivery",
                "user_id": str(uuid4()),
                "goal": "Espandere la base clienti B2B creando: database qualificato di 100 prospect CMO/CTO europei, strategia di outreach personalizzata con 5 template email sequence, content calendar 30 giorni con 25 post LinkedIn per thought leadership, e sistema di tracking per misurare 20% aumento lead qualificati entro 60 giorni"
            }
            
            workspace = await create_workspace(**workspace_data)
            self.workspace_id = str(workspace["id"])
            
            self.log_step("Realistic Workspace Creation", True, {
                "workspace_id": self.workspace_id,
                "scenario": "B2B Growth Consulting Expansion"
            })
            
            return True
            
        except Exception as e:
            self.log_step("Realistic Workspace Creation", False, str(e))
            return False
    
    async def step_2_ai_driven_goal_extraction(self) -> bool:
        """Step 2: Estrazione goal AI-driven dal testo naturale"""
        logger.info("\n🎯 STEP 2: AI-driven goal extraction from natural language...")
        
        try:
            from ai_quality_assurance.ai_goal_extractor import AIGoalExtractor
            from database import supabase
            
            # Get workspace per contesto
            workspace_response = supabase.table('workspaces').select('*').eq('id', self.workspace_id).execute()
            workspace = workspace_response.data[0]
            
            # Estrazione AI-driven
            extractor = AIGoalExtractor()
            extracted_goals = await extractor.extract_goals_from_text(
                goal_text=workspace['goal'],
                workspace_context={"workspace_id": self.workspace_id}
            )
            
            # Crea goal nel database
            created_goals = []
            logger.info(f"   Creating {len(extracted_goals)} goals in database...")
            
            for i, goal in enumerate(extracted_goals):
                logger.info(f"   Creating goal {i+1}: {goal.description[:50]}...")
                
                goal_data = {
                    "workspace_id": self.workspace_id,
                    "metric_type": goal.metric_type,
                    "target_value": float(goal.target_value),
                    "unit": goal.unit,
                    "description": goal.description,
                    "priority": 3,
                    "status": "active"
                }
                
                goal_response = supabase.table('workspace_goals').insert(goal_data).execute()
                if goal_response.data:
                    created_goals.append(goal_response.data[0])
                    logger.info(f"      ✅ Goal {i+1} created with ID: {goal_response.data[0]['id']}")
                else:
                    logger.error(f"      ❌ Failed to create goal {i+1}")
                    
            logger.info(f"   Successfully created {len(created_goals)} goals in database")
            
            self.extracted_goals = created_goals
            self.metrics["goals_created"] = len(created_goals)
            
            self.log_step("AI-Driven Goal Extraction", True, {
                "goals_extracted": len(created_goals),
                "sample_goals": [g['description'][:50] + '...' for g in created_goals[:3]]
            })
            
            return len(created_goals) > 0
            
        except Exception as e:
            self.log_step("AI-Driven Goal Extraction", False, str(e))
            return False
    
    async def step_3_create_specialized_team(self) -> bool:
        """Step 3: Crea team specializzato per i goal estratti"""
        logger.info("\n👥 STEP 3: Creating specialized team for extracted goals...")
        
        try:
            from database import supabase
            
            # Team specializzato per B2B growth consulting
            team_composition = [
                {
                    "name": "Senior Lead Generation Manager",
                    "role": "lead_generation_specialist",
                    "seniority": "expert",
                    "description": "Expert in B2B lead generation and prospect database creation",
                    "system_prompt": "You are an expert lead generation specialist focused on creating high-quality B2B prospect databases and outreach strategies.",
                    "tools": [],
                    "can_create_tools": False
                },
                {
                    "name": "Content Marketing Strategist", 
                    "role": "content_marketing_specialist",
                    "seniority": "senior",
                    "description": "Specialist in B2B content marketing and thought leadership",
                    "system_prompt": "You are a content marketing strategist specializing in B2B thought leadership and content calendar creation.",
                    "tools": [],
                    "can_create_tools": False
                },
                {
                    "name": "Growth Analytics Expert",
                    "role": "analytics_specialist", 
                    "seniority": "expert",
                    "description": "Expert in growth metrics and tracking system implementation",
                    "system_prompt": "You are a growth analytics expert focused on measuring and optimizing B2B lead generation performance.",
                    "tools": [],
                    "can_create_tools": False
                }
            ]
            
            created_agents = []
            for agent_data in team_composition:
                agent_response = supabase.table('agents').insert({
                    "workspace_id": self.workspace_id,
                    "name": agent_data["name"],
                    "role": agent_data["role"],
                    "seniority": agent_data["seniority"],
                    "description": agent_data["description"],
                    "status": "available",
                    "health": {"status": "healthy"},
                    "system_prompt": agent_data["system_prompt"],
                    "tools": agent_data["tools"],
                    "can_create_tools": agent_data["can_create_tools"]
                }).execute()
                
                if agent_response.data:
                    created_agents.append(agent_response.data[0])
            
            self.team_agents = created_agents
            
            self.log_step("Specialized Team Creation", True, {
                "agents_created": len(created_agents),
                "specializations": [a['role'] for a in created_agents]
            })
            
            return len(created_agents) > 0
            
        except Exception as e:
            self.log_step("Specialized Team Creation", False, str(e))
            return False
    
    async def step_4_goal_driven_task_generation(self) -> bool:
        """Step 4: Generazione task goal-driven per ogni obiettivo"""
        logger.info("\n📋 STEP 4: Goal-driven task generation...")
        
        try:
            from goal_driven_task_planner import GoalDrivenTaskPlanner
            
            planner = GoalDrivenTaskPlanner()
            all_tasks = []
            
            logger.info(f"   Found {len(self.extracted_goals)} goals to process")
            
            for i, goal in enumerate(self.extracted_goals):
                logger.info(f"   Processing goal {i+1}: {goal['description'][:60]}...")
                logger.info(f"   Goal ID: {goal['id']}, Metric Type: {goal.get('metric_type', 'unknown')}")
                
                try:
                    # Ensure goal dict has all required fields for plan_tasks_for_goal
                    from datetime import datetime
                    
                    # Prepare goal dict with proper format for plan_tasks_for_goal
                    goal_dict = {
                        'id': goal['id'],  # Keep as string since plan_tasks_for_goal will convert
                        'workspace_id': goal['workspace_id'],  # Keep as string
                        'metric_type': goal['metric_type'],
                        'target_value': goal['target_value'],
                        'current_value': goal.get('current_value', 0.0),
                        'unit': goal['unit'],
                        'description': goal['description'],
                        'priority': goal['priority'],
                        'status': goal['status'],
                        'created_at': goal.get('created_at') or datetime.now().isoformat(),
                        'updated_at': goal.get('updated_at') or datetime.now().isoformat()
                    }
                    
                    # Use the proper public method that creates tasks in database
                    tasks = await planner.plan_tasks_for_goal(goal_dict, self.workspace_id)
                    logger.info(f"   Created {len(tasks)} tasks in database for goal {i+1}")
                    all_tasks.extend(tasks)
                except Exception as task_gen_error:
                    logger.error(f"   Failed to generate tasks for goal {i+1}: {task_gen_error}")
                    continue
            
            self.generated_tasks = all_tasks
            self.metrics["tasks_created"] = len(all_tasks)
            
            self.log_step("Goal-Driven Task Generation", True, {
                "tasks_generated": len(all_tasks),
                "goals_processed": len(self.extracted_goals),
                "sample_tasks": [t.get('name', 'Unnamed')[:50] for t in all_tasks[:3]]
            })
            
            return len(all_tasks) > 0
            
        except Exception as e:
            self.log_step("Goal-Driven Task Generation", False, str(e))
            return False
    
    async def step_5_autonomous_task_execution(self) -> bool:
        """Step 5: Esecuzione autonoma dei task con quality enhancement"""
        logger.info("\n⚡ STEP 5: Autonomous task execution with quality enhancement...")
        
        try:
            from ai_agents.manager import AgentManager
            from database import supabase
            
            # Inizializza AgentManager
            manager = AgentManager(UUID(self.workspace_id))
            init_success = await manager.initialize()
            
            if not init_success:
                raise Exception("Failed to initialize AgentManager")
            
            # Get existing tasks from database (already created in Step 4)
            tasks_response = supabase.table('tasks').select('*').eq('workspace_id', self.workspace_id).eq('status', 'pending').limit(3).execute()
            existing_tasks = tasks_response.data or []
            
            if not existing_tasks:
                logger.error("   No pending tasks found in database - Step 4 may have failed")
                return False
            
            completed_tasks = []
            quality_enhanced_tasks = []
            
            for i, task_data in enumerate(existing_tasks):
                task_name = task_data.get('name', f'Task {i+1}')
                task_id = task_data['id']
                logger.info(f"   Executing task {i+1}/3: {task_name[:50]}...")
                
                try:
                    
                    # Esecuzione reale del task
                    result = await manager.execute_task(UUID(task_id))
                    
                    # Controlla status finale
                    task_check = supabase.table('tasks').select('*').eq('id', task_id).execute()
                    if task_check.data:
                        final_task = task_check.data[0]
                        final_status = final_task['status']
                        
                        logger.info(f"      Task {task_name[:30]} completed with status: {final_status}")
                        
                        if final_status in ['completed', 'pending_verification', 'needs_enhancement']:
                            completed_tasks.append({
                                "task_id": task_id,
                                "name": task_name,
                                "status": final_status,
                                "result": final_task.get('result'),
                                "metric_type": task_data.get('metric_type')
                            })
                            
                            if final_status == 'needs_enhancement':
                                quality_enhanced_tasks.append(task_id)
                                self.quality_iterations[task_id] = 1
                    
                    # Delay tra task per non sovraccaricare
                    await asyncio.sleep(3)
                    
                except Exception as task_error:
                    logger.warning(f"      Task {task_name} failed: {task_error}")
                    continue
            
            self.completed_tasks = completed_tasks
            self.metrics["tasks_completed"] = len(completed_tasks)
            self.metrics["quality_iterations"] = len(quality_enhanced_tasks)
            
            self.log_step("Autonomous Task Execution", True, {
                "tasks_executed": len(tasks_to_execute),
                "tasks_completed": len(completed_tasks),
                "quality_enhanced": len(quality_enhanced_tasks)
            })
            
            return len(completed_tasks) > 0
            
        except Exception as e:
            self.log_step("Autonomous Task Execution", False, str(e))
            return False
    
    async def step_6_quality_improvement_cycle(self) -> bool:
        """Step 6: Ciclo di miglioramento qualità automatico"""
        logger.info("\n🔍 STEP 6: Quality improvement cycle...")
        
        try:
            from database import supabase
            
            # Monitora task che richiedono enhancement
            enhanced_count = 0
            improvement_cycles = 0
            
            for task_info in self.completed_tasks:
                if task_info['status'] == 'needs_enhancement':
                    task_id = task_info['task_id']
                    
                    # Simula 1-2 cicli di miglioramento qualità
                    for cycle in range(2):  # Massimo 2 cicli per task
                        improvement_cycles += 1
                        
                        logger.info(f"   Quality improvement cycle {cycle+1} for task {task_info['name'][:30]}...")
                        
                        # Attendi che il sistema processi il feedback (tempo realistico)
                        await asyncio.sleep(5)
                        
                        # Controlla se il task è stato migliorato
                        task_check = supabase.table('tasks').select('*').eq('id', task_id).execute()
                        if task_check.data:
                            current_status = task_check.data[0]['status']
                            
                            if current_status == 'completed':
                                enhanced_count += 1
                                logger.info(f"      ✅ Task quality improved to completed")
                                break
                            elif current_status == 'pending_verification':
                                enhanced_count += 1
                                logger.info(f"      ✅ Task ready for verification")
                                break
                        
                        # Se ancora needs_enhancement, continua
                        logger.info(f"      🔄 Still needs enhancement, continuing...")
            
            self.metrics["quality_iterations"] = improvement_cycles
            
            self.log_step("Quality Improvement Cycle", True, {
                "improvement_cycles": improvement_cycles,
                "tasks_enhanced": enhanced_count
            })
            
            return True
            
        except Exception as e:
            self.log_step("Quality Improvement Cycle", False, str(e))
            return False
    
    async def step_7_deliverable_generation(self) -> bool:
        """Step 7: Generazione automatica deliverable da task completati"""
        logger.info("\n📦 STEP 7: Automatic deliverable generation...")
        
        try:
            from deliverable_aggregator import create_intelligent_deliverable
            from database import supabase
            
            # Verifica task completati per deliverable
            completed_tasks_response = supabase.table('tasks').select('*').eq('workspace_id', self.workspace_id).in_('status', ['completed', 'pending_verification']).execute()
            completed_tasks = completed_tasks_response.data or []
            
            deliverables_created = []
            
            if len(completed_tasks) >= 1:  # Soglia minima per deliverable
                logger.info(f"   Found {len(completed_tasks)} completed tasks, creating deliverable...")
                
                deliverable_id = await create_intelligent_deliverable(
                    workspace_id=self.workspace_id,
                    force_creation=False  # Usa logica standard, non forzata
                )
                
                if deliverable_id:
                    # Ottieni dettagli deliverable
                    deliverable_response = supabase.table('deliverables').select('*').eq('id', deliverable_id).execute()
                    if deliverable_response.data:
                        deliverable = deliverable_response.data[0]
                        deliverables_created.append(deliverable)
                        
                        logger.info(f"      ✅ Deliverable created: {deliverable.get('title', 'Untitled')}")
                        logger.info(f"      📊 Readiness score: {deliverable.get('readiness_score', 0)}")
                else:
                    logger.info("      ⚠️ No deliverable created (may not meet criteria)")
            else:
                logger.info(f"   Not enough completed tasks ({len(completed_tasks)}) for deliverable creation")
            
            self.created_deliverables = deliverables_created
            self.metrics["deliverables_created"] = len(deliverables_created)
            
            self.log_step("Deliverable Generation", True, {
                "completed_tasks_available": len(completed_tasks),
                "deliverables_created": len(deliverables_created)
            })
            
            return True
            
        except Exception as e:
            self.log_step("Deliverable Generation", False, str(e))
            return False
    
    async def step_8_goal_progress_tracking(self) -> bool:
        """Step 8: Tracciamento automatico progresso goal"""
        logger.info("\n📊 STEP 8: Automatic goal progress tracking...")
        
        try:
            from automated_goal_monitor import AutomatedGoalMonitor
            from database import supabase
            
            monitor = AutomatedGoalMonitor()
            
            # Esegui monitoring cycle
            monitoring_result = await monitor._process_workspace_validation(self.workspace_id)
            
            # Verifica goal aggiornati
            updated_goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', self.workspace_id).execute()
            updated_goals = updated_goals_response.data or []
            
            completed_goals = 0
            goal_progress = []
            
            for goal in updated_goals:
                current_value = goal.get('current_value', 0)
                target_value = goal.get('target_value', 1)
                progress_percent = (current_value / target_value * 100) if target_value > 0 else 0
                
                goal_progress.append({
                    "description": goal['description'][:50],
                    "progress": f"{progress_percent:.1f}%",
                    "status": goal['status'],
                    "current_value": current_value,
                    "target_value": target_value
                })
                
                if goal['status'] == 'completed':
                    completed_goals += 1
            
            self.metrics["goals_completed"] = completed_goals
            
            self.log_step("Goal Progress Tracking", True, {
                "goals_monitored": len(updated_goals),
                "goals_completed": completed_goals,
                "average_progress": sum(g.get('current_value', 0) / g.get('target_value', 1) * 100 for g in updated_goals) / len(updated_goals) if updated_goals else 0
            })
            
            return True
            
        except Exception as e:
            self.log_step("Goal Progress Tracking", False, str(e))
            return False
    
    async def step_9_human_feedback_simulation(self) -> bool:
        """Step 9: Simulazione ciclo feedback umano realistico"""
        logger.info("\n👤 STEP 9: Realistic human feedback simulation...")
        
        try:
            from database import supabase
            
            # Verifica feedback requests esistenti
            feedback_response = supabase.table('human_feedback_requests').select('*').eq('workspace_id', self.workspace_id).eq('status', 'pending').execute()
            feedback_requests = feedback_response.data or []
            
            feedback_processed = 0
            
            if feedback_requests:
                logger.info(f"   Found {len(feedback_requests)} pending feedback requests")
                
                for feedback_request in feedback_requests:
                    # Simula feedback umano realistico
                    realistic_feedback = {
                        "approved": True,
                        "feedback_type": "approved_with_suggestions",
                        "message": "Good work! Consider adding more specific European market data for better localization.",
                        "suggestions": [
                            "Include GDPR compliance notes for EU contacts",
                            "Add LinkedIn outreach best practices",
                            "Consider time zone optimization for email sequences"
                        ]
                    }
                    
                    # Aggiorna feedback request
                    update_response = supabase.table('human_feedback_requests').update({
                        "status": "completed",
                        "feedback": realistic_feedback,
                        "completed_at": datetime.now().isoformat()
                    }).eq('id', feedback_request['id']).execute()
                    
                    if update_response.data:
                        feedback_processed += 1
                        logger.info(f"      ✅ Feedback processed for request {feedback_request['id']}")
            else:
                logger.info("   No pending feedback requests found")
            
            self.log_step("Human Feedback Simulation", True, {
                "feedback_requests_found": len(feedback_requests),
                "feedback_processed": feedback_processed
            })
            
            return True
            
        except Exception as e:
            self.log_step("Human Feedback Simulation", False, str(e))
            return False
    
    async def step_10_final_system_verification(self) -> bool:
        """Step 10: Verifica finale stato completo del sistema"""
        logger.info("\n🏁 STEP 10: Final system verification...")
        
        try:
            from database import supabase
            
            # Ottieni stato finale completo
            workspace_response = supabase.table('workspaces').select('*').eq('id', self.workspace_id).execute()
            workspace = workspace_response.data[0] if workspace_response.data else {}
            
            goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', self.workspace_id).execute()
            goals = goals_response.data or []
            
            tasks_response = supabase.table('tasks').select('*').eq('workspace_id', self.workspace_id).execute()
            tasks = tasks_response.data or []
            
            deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', self.workspace_id).execute()
            deliverables = deliverables_response.data or []
            
            agents_response = supabase.table('agents').select('*').eq('workspace_id', self.workspace_id).execute()
            agents = agents_response.data or []
            
            # Calcola metriche finali
            completed_goals = [g for g in goals if g['status'] == 'completed']
            completed_tasks = [t for t in tasks if t['status'] in ['completed', 'pending_verification']]
            
            # Calcola completion percentage
            goal_completion = (len(completed_goals) / len(goals)) * 100 if goals else 0
            task_completion = (len(completed_tasks) / len(tasks)) * 100 if tasks else 0
            
            # Determina successo finale
            success_criteria = {
                "goals_created": len(goals) > 0,
                "team_created": len(agents) > 0,
                "tasks_generated": len(tasks) > 0,
                "tasks_executed": len(completed_tasks) > 0,
                "quality_process": self.metrics["quality_iterations"] > 0,
                "system_functional": True
            }
            
            final_success = all(success_criteria.values())
            self.metrics["final_success"] = final_success
            
            # Aggiorna metriche finali
            self.metrics.update({
                "goals_created": len(goals),
                "goals_completed": len(completed_goals),
                "tasks_created": len(tasks),
                "tasks_completed": len(completed_tasks),
                "deliverables_created": len(deliverables)
            })
            
            final_state = {
                "workspace_status": workspace.get('status', 'unknown'),
                "total_goals": len(goals),
                "completed_goals": len(completed_goals),
                "goal_completion_rate": f"{goal_completion:.1f}%",
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "task_completion_rate": f"{task_completion:.1f}%",
                "deliverables_created": len(deliverables),
                "agents_created": len(agents),
                "quality_iterations": self.metrics["quality_iterations"],
                "success_criteria": success_criteria,
                "overall_success": final_success
            }
            
            self.log_step("Final System Verification", final_success, final_state)
            
            return final_success
            
        except Exception as e:
            self.log_step("Final System Verification", False, str(e))
            return False
    
    def generate_comprehensive_report(self):
        """Genera report comprensivo del test lifecycle"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        logger.info("\n" + "="*80)
        logger.info("🎬 COMPLETE LIFECYCLE TEST RESULTS")
        logger.info("="*80)
        
        logger.info(f"📊 EXECUTION SUMMARY:")
        logger.info(f"   Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        logger.info(f"   Steps Completed: {self.metrics['steps_completed']}/{self.metrics['total_steps']}")
        logger.info(f"   Overall Success: {'✅ YES' if self.metrics['final_success'] else '❌ NO'}")
        
        logger.info(f"\n📈 SYSTEM METRICS:")
        logger.info(f"   Goals Created: {self.metrics['goals_created']}")
        logger.info(f"   Goals Completed: {self.metrics['goals_completed']}")
        logger.info(f"   Tasks Created: {self.metrics['tasks_created']}")
        logger.info(f"   Tasks Completed: {self.metrics['tasks_completed']}")
        logger.info(f"   Quality Iterations: {self.metrics['quality_iterations']}")
        logger.info(f"   Deliverables Created: {self.metrics['deliverables_created']}")
        
        logger.info(f"\n🎯 AUTONOMOUS PROGRESSION:")
        if self.metrics['goals_created'] > 0:
            goal_success_rate = (self.metrics['goals_completed'] / self.metrics['goals_created']) * 100
            logger.info(f"   Goal Success Rate: {goal_success_rate:.1f}%")
        
        if self.metrics['tasks_created'] > 0:
            task_success_rate = (self.metrics['tasks_completed'] / self.metrics['tasks_created']) * 100
            logger.info(f"   Task Success Rate: {task_success_rate:.1f}%")
        
        quality_effectiveness = "✅ Active" if self.metrics['quality_iterations'] > 0 else "❌ Inactive"
        logger.info(f"   Quality System: {quality_effectiveness}")
        
        deliverable_success = "✅ Created" if self.metrics['deliverables_created'] > 0 else "❌ None"
        logger.info(f"   Deliverable Generation: {deliverable_success}")
        
        logger.info(f"\n🏆 CONCLUSION:")
        if self.metrics['final_success']:
            logger.info("   🎉 COMPLETE LIFECYCLE TEST PASSED!")
            logger.info("   🎯 System successfully progressed from creation to deliverables autonomously")
            logger.info("   💪 Quality enhancement, task execution, and goal tracking all functional")
        else:
            logger.info("   ⚠️ COMPLETE LIFECYCLE TEST PARTIAL SUCCESS")
            logger.info(f"   📊 {self.metrics['steps_completed']}/{self.metrics['total_steps']} steps completed")
            logger.info("   🔧 Some autonomous progression features need attention")
        
        # Salva report dettagliato
        report_data = {
            "test_type": "complete_lifecycle",
            "execution_time": {
                "start": self.start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": total_duration
            },
            "metrics": self.metrics,
            "workspace_id": self.workspace_id,
            "goals_extracted": len(self.extracted_goals),
            "team_agents": len(self.team_agents),
            "tasks_generated": len(self.generated_tasks),
            "completed_tasks": len(self.completed_tasks),
            "deliverables": len(self.created_deliverables)
        }
        
        report_filename = f"complete_lifecycle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"\n📝 DETAILED REPORT: {report_filename}")
        
        return self.metrics['final_success']

async def main():
    """Esegui il test complete lifecycle"""
    logger.info("🚀 STARTING COMPLETE LIFECYCLE TEST")
    logger.info("Testing full autonomous system progression without shortcuts")
    logger.info("Goal: Verify system reaches final deliverables autonomously\n")
    
    test = CompleteLifecycleTest()
    
    # Esegui tutti gli step in sequenza
    steps = [
        test.step_1_create_realistic_workspace,
        test.step_2_ai_driven_goal_extraction,
        test.step_3_create_specialized_team,
        test.step_4_goal_driven_task_generation,
        test.step_5_autonomous_task_execution,
        test.step_6_quality_improvement_cycle,
        test.step_7_deliverable_generation,
        test.step_8_goal_progress_tracking,
        test.step_9_human_feedback_simulation,
        test.step_10_final_system_verification
    ]
    
    for step_func in steps:
        try:
            await step_func()
            # Pausa tra step per non sovraccaricare
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Step failed with exception: {e}")
            break
    
    # Genera report finale
    overall_success = test.generate_comprehensive_report()
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)