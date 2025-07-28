# backend/ai_agents/manager.py
import logging
import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from database import (
    list_agents as db_list_agents_from_db,
    list_tasks as db_list_tasks_from_db,
    get_workspace,
    update_task_status,
    update_agent_status
)
from services.memory_similarity_engine import memory_similarity_engine
from models import (
    Agent as AgentModelPydantic,
    Task,
    TaskStatus,
    AgentStatus,
    AgentHealth,
    HealthStatus
)
from ai_agents.specialist_enhanced import SpecialistAgent
from services.sdk_memory_bridge import create_workspace_session

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, workspace_id: UUID):
        self.workspace_id = workspace_id
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        
        self.agents: Dict[UUID, SpecialistAgent] = {}
        
        # ANTI-LOOP CONFIGURATIONS
        self.execution_timeout = 300  # 5 minuti timeout per task
        self.max_retries = 1  # Massimo 1 retry per task
        self.task_execution_cache: Dict[str, datetime] = {}
        self.failed_tasks_cache: Dict[str, int] = {}
        
        # Monitoring
        self.initialization_time: Optional[datetime] = None
        self.last_health_check: Optional[datetime] = None

    async def initialize(self) -> bool:
        """
        Carica il workspace e inizializza tutti i SpecialistAgent.
        Versione migliorata con gestione errori completa e anti-loop.
        """
        try:
            start_time = datetime.now()
            
            # Verifica workspace esistente
            workspace = await get_workspace(str(self.workspace_id))
            if not workspace:
                logger.error(f"Workspace {self.workspace_id} non trovato. Impossibile inizializzare.")
                return False

            logger.info(f"Initializing AgentManager for workspace {self.workspace_id} "
                        f"(name={workspace.get('name','N/A')})")

            # Recupera agenti dal database con retry
            raw_agents = await self._safe_fetch_agents()
            if raw_agents is None:
                logger.error(f"Failed to fetch agents for workspace {self.workspace_id}")
                return False

            if not raw_agents:
                logger.info(f"Nessun agente per workspace {self.workspace_id}. Manager pronto comunque.")
                self.initialization_time = datetime.now()
                return True

            # Validazione e creazione SpecialistAgent
            valid_agents = await self._validate_and_create_agents(raw_agents)
            
            # Verifica che almeno un agente sia stato creato correttamente
            if not valid_agents:
                logger.warning(f"Nessun agente valido creato per workspace {self.workspace_id}.")
                # Return True comunque per permettere funzionamento base
                self.initialization_time = datetime.now()
                return True

            logger.info(f"Inizializzati {len(valid_agents)}/{len(raw_agents)} SpecialistAgent "
                       f"in {(datetime.now() - start_time).total_seconds():.2f}s")
            
            # Health check iniziale (opzionale)
            await self._initial_health_check()
            
            self.initialization_time = datetime.now()
            return True

        except Exception as e:
            logger.error(
                f"Errore critico inizializzazione AgentManager per workspace {self.workspace_id}: {e}",
                exc_info=True
            )
            return False

    async def _safe_fetch_agents(self, max_retries: int = 3) -> Optional[List[Dict]]:
        """Fetch agenti con retry logic"""
        for attempt in range(max_retries):
            try:
                agents = await db_list_agents_from_db(str(self.workspace_id))
                return agents
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to fetch agents: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All attempts failed to fetch agents: {e}")
                    return None

    async def _validate_and_create_agents(self, raw_agents: List[Dict]) -> List[AgentModelPydantic]:
        """Valida e crea SpecialistAgent con gestione errori robusta"""
        logger.info(f"Starting validation of {len(raw_agents)} raw agents")
        valid_agents: List[AgentModelPydantic] = []
        
        for i, agent_data in enumerate(raw_agents):
            try:
                logger.debug(f"Validating agent {i+1}/{len(raw_agents)}: {agent_data.get('name', 'Unknown')} (ID: {agent_data.get('id', '?')})")
                # Validazione Pydantic
                agent_model = AgentModelPydantic.model_validate(agent_data)
                valid_agents.append(agent_model)
                logger.debug(f"✅ Successfully validated agent: {agent_model.name}")
            except Exception as e:
                logger.error(
                    f"❌ Validazione fallita per agent ID {agent_data.get('id','?')}, name: {agent_data.get('name', 'Unknown')}: {e}",
                    exc_info=True
                )
                # Continua con gli altri agenti invece di fallire completamente

        if not valid_agents:
            logger.warning("No valid agents after Pydantic validation")
            return []

        logger.info(f"Successfully validated {len(valid_agents)}/{len(raw_agents)} agents")

        # Creazione SpecialistAgent con gestione errori
        successful_agents = []
        for i, agent_model in enumerate(valid_agents):
            try:
                logger.debug(f"Creating SpecialistAgent {i+1}/{len(valid_agents)}: {agent_model.name} (ID: {agent_model.id})")
                logger.info(f"🔍 Agent_model type: {type(agent_model)}")
                logger.info(f"🔍 Agent_model hard_skills type: {type(agent_model.hard_skills)}")
                logger.info(f"🔍 Agent_model hard_skills: {agent_model.hard_skills}")
                
                # Crea SpecialistAgent passando tutti gli agenti per handoff
                specialist = SpecialistAgent(
                    agent_data=agent_model,
                    all_workspace_agents_data=valid_agents  # Passa tutti per handoff
                )
                self.agents[agent_model.id] = specialist
                successful_agents.append(agent_model)
                logger.info(f"✅ Creato SpecialistAgent per {agent_model.name} (ID: {agent_model.id})")
            except Exception as e:
                logger.error(
                    f"❌ Errore creazione SpecialistAgent {agent_model.id} ({agent_model.name}): {e}",
                    exc_info=True
                )
                # Continua comunque con altri agenti

        if not successful_agents:
            raise Exception("No valid SpecialistAgents could be created from the provided agent data.")

        logger.info(f"Successfully created {len(successful_agents)}/{len(valid_agents)} SpecialistAgents")
        logger.info(f"Initialized agent IDs: {[str(aid) for aid in self.agents.keys()]}")
        return successful_agents

    async def _initial_health_check(self):
        """Health check iniziale opzionale"""
        try:
            healthy_count = 0
            for agent_id, specialist in self.agents.items():
                try:
                    # FIX: Serializza datetime per JSON
                    health_dict = {
                        "status": HealthStatus.HEALTHY.value,  # Usa .value per enum
                        "last_update": datetime.now().isoformat(),  # Converti a string
                        "details": {"initialization": "completed"}
                    }

                    await update_agent_status(
                        str(agent_id),
                        None,
                        health_dict  # Ora è un dict serializzabile
                    )
                    healthy_count += 1
                except Exception as e:
                    logger.warning(f"Health check failed for agent {agent_id}: {e}")

            logger.info(f"Initial health check completed: {healthy_count}/{len(self.agents)} agents healthy")
            self.last_health_check = datetime.now()
        except Exception as e:
            logger.warning(f"Initial health check failed: {e}")

    async def verify_all_agents(self) -> Dict[UUID, bool]:
        """
        Esegue verify_capabilities() su tutti gli agenti caricati.
        Versione migliorata con timeout e gestione errori.
        """
        results: Dict[UUID, bool] = {}
        
        if not self.agents:
            logger.warning(f"Nessun agente da verificare in manager per workspace {self.workspace_id}.")
            return results

        verification_tasks = []
        for agent_id, specialist in self.agents.items():
            verification_tasks.append(
                self._verify_single_agent(agent_id, specialist)
            )

        # Esegui verifiche in parallelo con timeout
        try:
            verification_results = await asyncio.wait_for(
                asyncio.gather(*verification_tasks, return_exceptions=True),
                timeout=30.0  # 30 secondi timeout totale
            )
            
            for i, (agent_id, _) in enumerate(self.agents.items()):
                result = verification_results[i]
                if isinstance(result, Exception):
                    logger.error(f"Verification failed for agent {agent_id}: {result}")
                    results[agent_id] = False
                else:
                    results[agent_id] = result

        except asyncio.TimeoutError:
            logger.warning("Agent verification timed out, marking all as failed")
            for agent_id in self.agents.keys():
                results[agent_id] = False

        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Agent verification completed: {success_count}/{len(results)} successful")
        return results

    async def _verify_single_agent(self, agent_id: UUID, specialist: SpecialistAgent) -> bool:
        """Verifica singolo agente con timeout"""
        try:
            return await asyncio.wait_for(
                specialist.verify_capabilities(),
                timeout=10.0  # 10 secondi per agente
            )
        except asyncio.TimeoutError:
            logger.warning(f"Verification timeout for agent {agent_id}")
            return False
        except Exception as e:
            logger.error(f"Verification error for agent {agent_id}: {e}")
            return False

    async def execute_task(self, task_id: UUID) -> Dict[str, Any]:
        """
        Recupera il Task dal DB e lo invia all'agente assegnato.
        Versione migliorata con anti-loop, timeout e retry logic.
        """
        task_id_str = str(task_id)
        
        # ANTI-LOOP: Controlla se task è già in esecuzione
        if task_id_str in self.task_execution_cache:
            last_execution = self.task_execution_cache[task_id_str]
            if datetime.now() - last_execution < timedelta(minutes=5):
                error_msg = f"Task {task_id} already executing or recently executed"
                logger.warning(error_msg)
                raise ValueError(error_msg)
        
        # Registra esecuzione
        self.task_execution_cache[task_id_str] = datetime.now()
        
        try:
            # 1. Recupera task con retry
            task = await self._safe_fetch_task(task_id)
            logger.info(f"_safe_fetch_task for task {task_id} returned: {task}")
            if not task:
                raise ValueError(f"Task {task_id} non trovato in workspace {self.workspace_id}")

            # 2. 🧠 MEMORY ENHANCEMENT: Retrieve relevant insights before execution
            relevant_insights = await self._get_task_insights(task)

            # 3. Verifica agent_id
            if not task.agent_id:
                await self._handle_task_failure(
                    task_id_str, 
                    "Task privo di agent_id", 
                    {"detail": "missing_agent_id"}
                )
                raise ValueError(f"Task {task_id} privo di agent_id")

            # 3. Verifica agente esiste e è inizializzato
            agent_uuid = UUID(str(task.agent_id))
            specialist = self.agents.get(agent_uuid)
            
            if not specialist:
                available_agent_list = list(str(aid) for aid in self.agents.keys())
                error_detail = {
                    "detail": "agent_not_found",
                    "available_agents": available_agent_list,
                    "requested_agent": str(agent_uuid),
                    "total_initialized_agents": len(self.agents),
                    "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None
                }
                
                logger.error(f"🚨 AGENT NOT FOUND - Task {task_id} requires agent {agent_uuid} but it's not initialized")
                logger.error(f"   Available agents ({len(self.agents)}): {available_agent_list}")
                logger.error(f"   Manager initialized at: {self.initialization_time}")
                logger.error(f"   Task details - Name: {task.name}, Status: {task.status}")
                
                await self._handle_task_failure(
                    task_id_str,
                    f"Agent {agent_uuid} non inizializzato nel manager",
                    error_detail
                )
                raise ValueError(f"Agent {agent_uuid} non inizializzato nel manager per task {task_id}")

            # 4. Controlla failures precedenti
            failure_count = self.failed_tasks_cache.get(task_id_str, 0)
            if failure_count >= self.max_retries:
                logger.warning(f"Task {task_id} exceeded max retries ({self.max_retries})")
                await self._handle_task_failure(
                    task_id_str,
                    f"Task exceeded max retries ({self.max_retries})",
                    {"detail": "max_retries_exceeded", "retry_count": failure_count}
                )
                raise ValueError(f"Task {task_id} exceeded maximum retries")

            # 5. Esecuzione con timeout
            logger.info(f"Dispatching task {task_id} -> agent {specialist.agent_data.name}")
            
            # 🔧 FIX #1: Create proper context with workspace_id to prevent SDK placeholders
            task_context = {
                "workspace_id": str(task.workspace_id),
                "task_id": str(task.id),
                "agent_id": str(specialist.agent_data.id)
            }
            
            # 🚀 NEW: Create execution record for full traceability
            from database import create_task_execution, update_task_execution
            
            execution_id = await create_task_execution(
                task_id_str,
                str(specialist.agent_data.id),
                str(task.workspace_id),
                openai_trace_id=getattr(task, 'openai_trace_id', None)
            )
            
            execution_start_time = asyncio.get_event_loop().time()
            
            try:
                logger.info(f"[{task_id}] AGENT EXECUTION START: Calling specialist.execute for agent '{specialist.agent_data.name}'")
                logger.info(f"[{task_id}] Task Name: {task.name}")
                logger.info(f"[{task_id}] Task Description: {task.description}")

                # 🧠 MEMORY: Enhance task with insights before execution
                enhanced_task = await self._enhance_task_with_insights(task, relevant_insights)
                
                # 🌉 SDK MEMORY BRIDGE: Create session for the workspace to enable native memory persistence
                session = create_workspace_session(
                    workspace_id=str(task.workspace_id),
                    agent_id=str(specialist.agent_data.id)
                )
                logger.info(f"🌉 Created SDK memory session for task {task_id} -> agent {specialist.agent_data.name}")
                
                result = await asyncio.wait_for(
                    specialist.execute(enhanced_task, session=session),
                    timeout=self.execution_timeout
                )
                
                logger.info(f"[{task_id}] AGENT EXECUTION END: specialist.execute returned successfully.")
                logger.info(f"specialist.execute_task for task {task_id} returned: {result}")
                
                execution_time = asyncio.get_event_loop().time() - execution_start_time
                
                # Update task status and result based on execution
                if result and result.status:
                    logger.info(f"Updating task {task_id} status to: {result.status.value}")
                    await update_task_status(task_id_str, result.status.value)
                    
                    # Update task result in database
                    from database import supabase
                    try:
                        update_data = {
                            "result": result.result,
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        await asyncio.to_thread(
                            supabase.table("tasks")
                            .update(update_data)
                            .eq("id", task_id_str)
                            .execute
                        )
                        logger.info(f"✅ Updated task {task_id} result in database")
                    except Exception as e:
                        logger.error(f"Failed to update task result: {e}")
                    
                    # 🚀 NEW: Update execution record with success
                    if execution_id:
                        await update_task_execution(
                            execution_id,
                            'completed',
                            result={'result': result.result, 'status': result.status.value} if result else None,
                            logs=f"Task executed successfully in {execution_time:.2f}s",
                            execution_time_seconds=execution_time
                        )
                    
                    # If task failed, handle appropriately
                    if result.status == TaskStatus.FAILED:
                        await self._handle_task_failure(
                            task_id_str,
                            result.error_message or "Task execution failed",
                            {"execution_result": "failed"}
                        )
                
                # 📦 ASSET EXTRACTION: Extract assets from completed task (moved from database.py to resolve circular dependency)
                if result.status == TaskStatus.COMPLETED:
                    await self._extract_task_assets(task, result)
                
                # 🧠 MEMORY: Store execution insights for future learning
                await self._store_execution_insights(task, result, relevant_insights)
                
                # Cleanup cache su successo
                self.failed_tasks_cache.pop(task_id_str, None)
                
                return result

            except asyncio.TimeoutError:
                error_msg = f"Task {task_id} execution timed out after {self.execution_timeout}s"
                logger.error(error_msg)
                
                # 🚀 NEW: Update execution record with timeout error
                if execution_id:
                    execution_time = asyncio.get_event_loop().time() - execution_start_time
                    await update_task_execution(
                        execution_id,
                        'failed_retriable',
                        error_message=error_msg,
                        error_type='TimeoutError',
                        execution_time_seconds=execution_time,
                        logs=f"Task timed out after {execution_time:.2f}s"
                    )
                
                await self._handle_task_failure(
                    task_id_str,
                    error_msg,
                    {"detail": "execution_timeout", "timeout_seconds": self.execution_timeout}
                )
                raise ValueError(error_msg)

        except ValueError:
            # Re-raise ValueError (già loggati)
            raise
        except Exception as e:
            # Increment failure count per retry logic
            self.failed_tasks_cache[task_id_str] = failure_count + 1
            
            error_msg = f"Unexpected error executing task {task_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 🚀 NEW: Update execution record with unexpected error
            if 'execution_id' in locals() and execution_id:
                execution_time = asyncio.get_event_loop().time() - execution_start_time
                await update_task_execution(
                    execution_id,
                    'failed_retriable',
                    error_message=error_msg,
                    error_type=type(e).__name__,
                    execution_time_seconds=execution_time,
                    logs=f"Unexpected error after {execution_time:.2f}s: {str(e)}"
                )
            
            await self._handle_task_failure(
                task_id_str,
                error_msg,
                {"detail": "unexpected_error", "error_type": type(e).__name__}
            )
            raise ValueError(error_msg)
        
        finally:
            # Cleanup execution cache dopo un po'
            asyncio.create_task(self._cleanup_execution_cache(task_id_str))

    async def _safe_fetch_task(self, task_id: UUID, max_retries: int = 3) -> Optional[Task]:
        """
        🔧 ROOT CAUSE FIX: Recupera task con AI-driven schema harmonization
        
        Fixes Pydantic validation errors for created_at/updated_at fields by using
        Universal Schema Harmonizer to convert raw database data to proper model format.
        """
        for attempt in range(max_retries):
            try:
                all_tasks = await db_list_tasks_from_db(str(self.workspace_id))
                task_record = next((t for t in all_tasks if UUID(t["id"]) == task_id), None)
                
                if task_record:
                    # Direct Task model creation with fallback processing
                    try:
                        return Task.model_validate(task_record)
                    except Exception as validation_error:
                        logger.warning(f"⚠️ Task validation failed for task {task_id}, using fallback: {validation_error}")
                        
                        # Emergency fallback: process fields manually
                        processed_record = self._emergency_task_field_processing(task_record)
                        return Task.model_validate(processed_record)
                else:
                    return None
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} to fetch task {task_id} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    logger.error(f"All attempts to fetch task {task_id} failed")
                    return None

    def _emergency_task_field_processing(self, task_record: Dict[str, Any]) -> Dict[str, Any]:
        """Emergency fallback for task field processing when harmonization fails"""
        from datetime import datetime, timezone
        from uuid import uuid4
        
        processed = task_record.copy()
        
        # Handle datetime fields that cause validation errors
        datetime_fields = ['created_at', 'updated_at', 'deadline']
        for field in datetime_fields:
            if field in processed:
                if processed[field] is None:
                    # Set default datetime for required fields
                    if field in ['created_at', 'updated_at']:
                        processed[field] = datetime.now(timezone.utc)
                elif isinstance(processed[field], str):
                    try:
                        # Try parsing ISO format from database
                        processed[field] = datetime.fromisoformat(processed[field].replace('Z', '+00:00'))
                    except:
                        # Fallback to current time if parsing fails
                        processed[field] = datetime.now(timezone.utc)
        
        # Ensure required fields exist
        if 'created_at' not in processed or processed['created_at'] is None:
            processed['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in processed or processed['updated_at'] is None:
            processed['updated_at'] = datetime.now(timezone.utc)
            
        return processed

    async def _handle_task_failure(self, task_id_str: str, error_msg: str, error_detail: Dict[str, Any]):
        """Gestisce il fallimento di un task con logging e update DB"""
        try:
            await update_task_status(
                task_id_str, 
                TaskStatus.FAILED.value,
                {"error": error_msg, **error_detail}
            )
        except Exception as e:
            logger.error(f"Failed to update task status for {task_id_str}: {e}")

    async def _cleanup_execution_cache(self, task_id_str: str):
        """Cleanup della cache di esecuzione dopo un delay"""
        await asyncio.sleep(300)  # 5 minuti delay
        self.task_execution_cache.pop(task_id_str, None)

    # 🧠 MEMORY ENHANCEMENT METHODS
    
    async def _get_task_insights(self, task: Task) -> List[Dict[str, Any]]:
        """Retrieve relevant insights from memory for task execution"""
        try:
            # Create task context for similarity search
            task_context = {
                'name': task.name,
                'description': task.description,
                'type': getattr(task, 'type', 'unknown'),
                'agent_role': getattr(task, 'agent_role', 'unknown'),
                'task_id': str(task.id)
            }
            
            # 1. Get task-specific insights via similarity search
            task_specific_insights = await memory_similarity_engine.get_relevant_insights(
                workspace_id=str(self.workspace_id),
                task_context=task_context,
                insight_types=['task_success_pattern', 'task_failure_lesson', 'agent_performance_insight']
            )
            
            # 2. 🎯 STRATEGIC LEARNING: Get strategic insights from LearningFeedbackEngine
            strategic_insights = await self._get_strategic_insights(task)
            
            # 3. Combine both types of insights
            all_insights = task_specific_insights + strategic_insights
            
            if task_specific_insights:
                logger.info(f"🧠 Found {len(task_specific_insights)} task-specific insights for task {task.name}")
                for insight in task_specific_insights:
                    logger.info(f"  - {insight.get('insight_type')}: {insight.get('similarity_score', 0):.2f} similarity")
            
            if strategic_insights:
                logger.info(f"🎯 Found {len(strategic_insights)} strategic insights for task {task.name}")
                for insight in strategic_insights:
                    logger.info(f"  - {insight.get('insight_type')}: strategic learning insight")
            
            if not all_insights:
                logger.info(f"🧠 No insights found for task {task.name}")
            
            return all_insights
            
        except Exception as e:
            logger.error(f"Error retrieving task insights: {e}")
            return []
    
    async def _get_strategic_insights(self, task: Task) -> List[Dict[str, Any]]:
        """Retrieve strategic insights generated by LearningFeedbackEngine"""
        try:
            from database import get_memory_insights
            
            # Get recent strategic insights generated by learning system
            strategic_insights = await get_memory_insights(
                workspace_id=str(self.workspace_id),
                insight_type=None,  # Get all types
                limit=10  # Get recent insights
            )
            
            # Filter for learning system insights only
            learning_system_insights = []
            for insight in strategic_insights:
                agent_role = insight.get('agent_role')
                insight_type = insight.get('insight_type')
                
                # Include insights from learning system that are strategic
                if (agent_role == 'learning_system' and 
                    insight_type in ['task_success_pattern', 'task_failure_lesson', 
                                   'agent_performance_insight', 'timing_optimization_insight']):
                    
                    # Add strategic flag to distinguish from similarity-based insights
                    insight_copy = insight.copy()
                    insight_copy['strategic'] = True
                    insight_copy['source'] = 'learning_feedback_engine'
                    learning_system_insights.append(insight_copy)
            
            return learning_system_insights
            
        except Exception as e:
            logger.error(f"Error retrieving strategic insights: {e}")
            return []
    
    async def _enhance_task_with_insights(self, task: Task, insights: List[Dict[str, Any]]) -> Task:
        """Enhance task description with relevant insights from memory"""
        try:
            if not insights:
                return task
            
            # Create enhanced description with insights
            enhanced_description = task.description or ""
            
            # Separate insights by type
            task_specific_insights = [i for i in insights if not i.get('strategic', False)]
            strategic_insights = [i for i in insights if i.get('strategic', False)]
            
            # Add insights section
            insights_section = "\n\n🧠 RELEVANT INSIGHTS FROM PAST EXPERIENCE:\n"
            
            insight_counter = 1
            
            # Add task-specific insights
            if task_specific_insights:
                insights_section += "\n📋 TASK-SPECIFIC INSIGHTS:\n"
                for insight in task_specific_insights[:2]:  # Limit to top 2
                    insight_type = insight.get('insight_type', 'unknown')
                    similarity_score = insight.get('similarity_score', 0)
                    content = insight.get('content', '')
                    
                    insights_section += f"\n{insight_counter}. {insight_type.upper()} (relevance: {similarity_score:.2f}):\n"
                    insights_section += self._format_insight_content(content)
                    insight_counter += 1
            
            # Add strategic insights
            if strategic_insights:
                insights_section += "\n🎯 STRATEGIC LEARNING FROM SYSTEM ANALYSIS:\n"
                for insight in strategic_insights[:2]:  # Limit to top 2
                    insight_type = insight.get('insight_type', 'unknown')
                    content = insight.get('content', '')
                    
                    insights_section += f"\n{insight_counter}. {insight_type.upper()} (from learning system):\n"
                    insights_section += self._format_insight_content(content)
                    insight_counter += 1
            
            insights_section += "\n⚡ IMPORTANT: Consider both task-specific patterns and strategic system insights when executing this task.\n"
            
            # Create enhanced task copy
            enhanced_task = task.model_copy()
            enhanced_task.description = enhanced_description + insights_section
            
            logger.info(f"🧠 Enhanced task {task.name} with {len(insights)} insights")
            return enhanced_task
            
        except Exception as e:
            logger.error(f"Error enhancing task with insights: {e}")
            return task
    
    def _format_insight_content(self, content: str) -> str:
        """Format insight content for display in task enhancement"""
        try:
            parsed_content = json.loads(content)
            if isinstance(parsed_content, dict):
                formatted = ""
                if 'success_factors' in parsed_content:
                    formatted += f"   ✅ Success factors: {', '.join(parsed_content['success_factors'])}\n"
                if 'recommendations' in parsed_content:
                    formatted += f"   💡 Recommendations: {', '.join(parsed_content['recommendations'])}\n"
                if 'prevention_strategies' in parsed_content:
                    formatted += f"   🛡️ Prevention strategies: {', '.join(parsed_content['prevention_strategies'])}\n"
                if 'performance_category' in parsed_content:
                    formatted += f"   📈 Performance: {parsed_content['performance_category']}\n"
                if 'pattern_name' in parsed_content:
                    formatted += f"   🎯 Pattern: {parsed_content['pattern_name']}\n"
                if 'failure_pattern' in parsed_content:
                    formatted += f"   ⚠️ Failure pattern: {parsed_content['failure_pattern']}\n"
                return formatted if formatted else f"   {content[:200]}...\n"
            else:
                return f"   {content[:200]}...\n"
        except:
            # If not structured, just use first 200 chars
            return f"   {content[:200]}...\n"
    
    async def _store_execution_insights(self, task: Task, result: Any, relevant_insights: List[Dict[str, Any]]):
        """Store insights from task execution for future learning"""
        try:
            # Create execution context
            execution_context = {
                'task_id': str(task.id),
                'name': task.name,
                'description': task.description,
                'type': getattr(task, 'type', 'unknown'),
                'agent_role': getattr(task, 'agent_role', 'unknown')
            }
            
            # Create execution result data
            execution_result = {
                'success': result.status == TaskStatus.COMPLETED if result else False,
                'result': result.result if result else None,
                'execution_time': getattr(result, 'execution_time', 0),
                'tools_used': getattr(result, 'tools_used', []),
                'insights_applied': len(relevant_insights)
            }
            
            # Store insight for future learning
            await memory_similarity_engine.store_task_execution_insight(
                workspace_id=str(self.workspace_id),
                task_context=execution_context,
                execution_result=execution_result,
                agent_id=str(task.agent_id) if task.agent_id else None
            )
            
            logger.info(f"🧠 Stored execution insights for task {task.name}")
            
        except Exception as e:
            logger.error(f"Error storing execution insights: {e}")

    # Metodi di utilità e monitoring
    async def _get_all_workspace_agents(self) -> List[AgentModelPydantic]:
        """Get all workspace agents for handoff support"""
        try:
            db_agents = await db_list_agents_from_db(workspace_id=self.workspace_id)
            agents = []
            for db_agent in db_agents:
                try:
                    agent_model = AgentModelPydantic(**db_agent)
                    agents.append(agent_model)
                except Exception as e:
                    logger.warning(f"Failed to create agent model for {db_agent.get('id')}: {e}")
            return agents
        except Exception as e:
            logger.error(f"Failed to get all workspace agents: {e}")
            return []
    
    async def get_agent(self, agent_id: str) -> Optional[SpecialistAgent]:
        """
        Ottieni un agente specifico per ID con auto-sync DB↔Manager
        
        Se l'agente non viene trovato nel manager cache, verifica se esiste nel DB
        e fa refresh automatico per sincronizzare la cache.
        """
        try:
            agent_uuid = UUID(agent_id)
            
            # Prima prova: cerca nella cache
            agent = self.agents.get(agent_uuid)
            if agent:
                return agent
            
            # 🔄 Auto-sync: Se non trovato nella cache, verifica nel DB
            logger.info(f"🔄 Agent {agent_id} not found in cache, checking DB and auto-refreshing...")
            
            # Verifica se l'agente esiste nel database
            from database import get_agent as db_get_agent
            db_agent = await db_get_agent(agent_id)
            
            if db_agent and str(db_agent.get('workspace_id')) == str(self.workspace_id):
                # L'agente esiste nel DB ma non nel manager - sync necessario
                logger.info(f"✅ Agent {agent_id} found in DB, adding to manager cache...")
                
                # Usa il metodo efficiente per aggiungere solo questo agente
                add_success = await self.add_agent_to_cache(agent_id)
                if add_success:
                    # Riprova dopo l'aggiunta
                    agent = self.agents.get(agent_uuid)
                    if agent:
                        logger.info(f"✅ Auto-sync successful: Agent {agent_id} now available in manager")
                        return agent
                    else:
                        logger.warning(f"⚠️ Auto-sync failed: Agent {agent_id} still not in cache after adding")
                else:
                    logger.error(f"❌ Failed to add agent {agent_id} to manager cache during auto-sync")
            else:
                logger.debug(f"Agent {agent_id} not found in DB or wrong workspace")
            
            return None
            
        except ValueError:
            logger.error(f"Invalid agent_id format: {agent_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return None

    async def add_agent_to_cache(self, agent_id: str) -> bool:
        """
        🚀 Aggiunge un singolo agente alla cache del manager senza re-initialize completo
        
        Più efficiente di initialize() quando serve aggiungere solo un agente specifico.
        """
        try:
            from database import get_agent as db_get_agent
            
            # Recupera l'agente dal DB
            db_agent = await db_get_agent(agent_id)
            if not db_agent:
                logger.warning(f"Agent {agent_id} not found in database")
                return False
            
            if str(db_agent.get('workspace_id')) != str(self.workspace_id):
                logger.warning(f"Agent {agent_id} belongs to different workspace")
                return False
            
            # Crea il SpecialistAgent
            from ai_agents.specialist_enhanced import SpecialistAgent
            from models import Agent as AgentModelPydantic
            
            try:
                agent_model = AgentModelPydantic(**db_agent)
                # Get all workspace agents for handoff support
                all_workspace_agents = await self._get_all_workspace_agents()
                specialist = SpecialistAgent(agent_model, all_workspace_agents)
                
                # Aggiunge alla cache
                agent_uuid = UUID(agent_id)
                self.agents[agent_uuid] = specialist
                
                logger.info(f"✅ Successfully added agent {agent_id} ({db_agent.get('name')}) to manager cache")
                return True
                
            except Exception as creation_error:
                logger.error(f"Failed to create SpecialistAgent for {agent_id}: {creation_error}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding agent {agent_id} to cache: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Ritorna lo stato di salute del manager"""
        return {
            "workspace_id": str(self.workspace_id),
            "agents_count": len(self.agents),
            "agents_ids": [str(aid) for aid in self.agents.keys()],
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "cached_executions": len(self.task_execution_cache),
            "failed_tasks_cache": len(self.failed_tasks_cache)
        }

    async def cleanup_caches(self):
        """Cleanup delle cache periodico"""
        try:
            # Cleanup execution cache
            current_time = datetime.now()
            expired_executions = [
                task_id for task_id, exec_time in self.task_execution_cache.items()
                if current_time - exec_time > timedelta(hours=1)
            ]
            
            for task_id in expired_executions:
                self.task_execution_cache.pop(task_id, None)
            
            # Cleanup failed tasks cache (mantieni solo ultimi)
            if len(self.failed_tasks_cache) > 100:
                # Mantieni solo gli ultimi 50
                sorted_items = sorted(self.failed_tasks_cache.items(), key=lambda x: x[1], reverse=True)
                self.failed_tasks_cache = dict(sorted_items[:50])
            
            logger.info(f"Cache cleanup completed for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)

    async def _extract_task_assets(self, task: Task, result: Any) -> None:
        """
        Extract assets from completed task result (moved from database.py to resolve circular dependency)
        """
        try:
            from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
            
            asset_extractor = ConcreteAssetExtractor()
            
            # Prepare result payload for asset extraction
            result_payload = {
                'result': result.result,
                'status': result.status.value,
                'summary': getattr(result, 'summary', None),
                'structured_content': getattr(result, 'structured_content', None),
                'execution_time': getattr(result, 'execution_time', 0)
            }
            
            workspace_id = str(task.workspace_id)
            # Extract assets using the correct method signature
            task_result_str = str(result_payload) if result_payload else ""
            context = {
                "task_id": str(task.id),
                "task_name": task.name,
                "workspace_id": workspace_id
            }
            
            extracted_assets = await asset_extractor.extract_assets(
                content=task_result_str,
                context=context
            )
            
            if extracted_assets:
                logger.info(f"📦 ASSET EXTRACTION: Extracted {len(extracted_assets)} assets from completed task {task.id}")
            else:
                logger.debug(f"📦 ASSET EXTRACTION: No assets extracted from completed task {task.id}")
                
        except ImportError as e:
            logger.warning(f"ConcreteAssetExtractor not available: {e}")
        except Exception as e:
            logger.warning(f"Asset extraction failed for completed task {task.id}: {e}")

    async def shutdown(self):
        """Shutdown graceful del manager"""
        try:
            logger.info(f"Shutting down AgentManager for workspace {self.workspace_id}")
            
            # Cleanup final delle cache
            await self.cleanup_caches()
            
            # Tentativo di health check finale per agenti
            for agent_id in self.agents.keys():
                try:
                    await update_agent_status(
                        str(agent_id),
                        None,
                        AgentHealth(
                            status=HealthStatus.UNKNOWN,
                            last_update=datetime.now(),
                            details={"manager_shutdown": True}
                        ).model_dump()
                    )
                except Exception as e:
                    logger.warning(f"Failed final health update for agent {agent_id}: {e}")
            
            # Clear references
            self.agents.clear()
            self.task_execution_cache.clear()
            self.failed_tasks_cache.clear()
            
            logger.info(f"AgentManager shutdown completed for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Error during manager shutdown: {e}", exc_info=True)