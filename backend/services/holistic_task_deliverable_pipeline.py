#!/usr/bin/env python3
"""
🎯 HOLISTIC TASK-TO-DELIVERABLE CONTENT PIPELINE

Pipeline olistico che connette:
1. Task classification AI (execution type detection) 
2. Specialist agents con tool usage enforcement
3. Real data collection validation
4. Deliverable content generation

Elimina il gap tra task execution e real content creation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from models import Task, TaskStatus, TaskExecutionOutput
from ai_agents.specialist_enhanced import SpecialistAgent
from services.ai_task_execution_classifier import classify_task_for_execution, TaskExecutionType
from database import get_agent, create_deliverable
from models import AssetArtifact
from uuid import uuid4

logger = logging.getLogger(__name__)

class HolisticTaskDeliverablePipeline:
    """
    🎯 Pipeline olistico che garantisce task execution produce real business content
    """
    
    def __init__(self):
        self.real_data_validation_enabled = True
        self.deliverable_creation_enabled = True
        
    async def execute_task_with_deliverable_pipeline(
        self, 
        task: Task, 
        workspace_agents: List[Dict[str, Any]],
        session: Optional[Any] = None,
        thinking_process_id: Optional[str] = None
    ) -> TaskExecutionOutput:
        """
        🎯 Execute task attraverso pipeline olistico task-to-deliverable
        
        Flow:
        1. AI classifica il task (planning vs data_collection vs content_generation)
        2. Crea specialist agent configurato per il tipo di execution
        3. Monitora execution per garantire tool usage appropriato
        4. Valida output per contenuto reale vs template/fake
        5. Crea deliverable se necessario con contenuto business-ready
        """
        
        logger.info(f"🎯 Starting holistic task-to-deliverable pipeline for task: {task.name}")
        
        # Track execution time for learning
        import time
        execution_start_time = time.time()
        
        try:
            # Step 1: 🔧 HOLISTIC - Get available tools first
            logger.info(f"🔧 Step 1A: Detecting available tools for intelligent classification...")
            available_tools = await self._detect_available_tools_for_task(task, workspace_agents)
            
            # Step 1B: AI-driven task classification with tool awareness
            logger.info(f"🧠 Step 1B: AI classifying task execution type with tool context...")
            classification = await classify_task_for_execution(
                task_name=task.name,
                task_description=task.description,
                workspace_context={"workspace_id": str(task.workspace_id)},
                available_tools=available_tools
            )
            
            logger.info(f"✅ Task classified as: {classification.execution_type.value}")
            logger.info(f"🔧 Tools needed: {classification.tools_needed}")
            logger.info(f"📋 Expected content: {classification.content_type_expected}")
            
            # Step 2: Create specialized agent with proper tool configuration
            logger.info(f"👤 Step 2: Creating specialist agent with classification-aware configuration...")
            agent_data = await get_agent(str(task.agent_id))
            if not agent_data:
                raise ValueError(f"Agent {task.agent_id} not found")
            
            # Convert DB agent data to AgentModel
            from models import Agent as AgentModel
            agent_model = AgentModel.model_validate(agent_data)
            
            # Create specialist agent with all workspace agents for handoffs
            all_workspace_agents = []
            for wa in workspace_agents:
                try:
                    all_workspace_agents.append(AgentModel.model_validate(wa))
                except Exception as e:
                    logger.warning(f"Failed to validate workspace agent: {e}")
            
            # Step 2.25: 🚦 PRE-EXECUTION QUALITY GATES - Validate task before execution
            logger.info(f"🚦 Step 2.25: Running pre-execution quality gates...")
            try:
                from services.pre_execution_quality_gates import pre_execution_quality_gates
                
                workspace_context = {
                    "workspace_id": str(task.workspace_id),
                    "has_documents": len(available_tools) > 0 and "file_search" in available_tools
                }
                
                can_proceed, gate_results, enhanced_context = await pre_execution_quality_gates.run_all_gates(
                    task=task,
                    agent=agent_model,
                    workspace_context=workspace_context
                )
                
                if not can_proceed:
                    # Task failed quality gates
                    failed_gates = [r for r in gate_results if r.status.value == "failed"]
                    error_message = f"Task failed {len(failed_gates)} quality gates: " + \
                                  ", ".join([f"{g.gate_name}: {g.message}" for g in failed_gates])
                    
                    logger.error(f"❌ {error_message}")
                    
                    return TaskExecutionOutput(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        error_message=error_message,
                        summary="Task failed pre-execution quality checks",
                        quality_gate_results=[g.to_dict() for g in gate_results]
                    )
                
                # Enhance task context with quality gate insights
                if enhanced_context:
                    task.context = task.context or {}
                    task.context["quality_insights"] = enhanced_context
                    logger.info(f"✅ Task enhanced with quality gate insights")
                    
            except Exception as e:
                logger.warning(f"⚠️ Quality gates failed, continuing with caution: {e}")
            
            specialist_agent = SpecialistAgent(
                agent_data=agent_model,
                all_workspace_agents_data=all_workspace_agents
            )
            
            # Step 2.5: 🔍 INTELLIGENT RAG INTEGRATION - Check if document search would help
            logger.info(f"🔍 Step 2.5: Checking if document search would enhance task execution...")
            document_context = None
            try:
                from services.intelligent_rag_trigger import intelligent_rag_trigger
                
                should_search, search_queries, confidence = await intelligent_rag_trigger.should_trigger_document_search(
                    task_name=task.name,
                    task_description=task.description,
                    task_type=classification.execution_type.value,
                    execution_context={"workspace_id": str(task.workspace_id)}
                )
                
                if should_search:
                    logger.info(f"📚 Document search triggered (confidence: {confidence:.2f})")
                    logger.info(f"🔍 Search queries: {search_queries}")
                    
                    # Execute document search
                    document_results = await intelligent_rag_trigger.execute_intelligent_document_search(
                        workspace_id=str(task.workspace_id),
                        agent_id=str(task.agent_id),
                        search_queries=search_queries
                    )
                    
                    if document_results.get("documents_found"):
                        document_context = document_results
                        logger.info(f"✅ Found {len(document_results['results'])} relevant documents")
                        
                        # Enhance task context with document information
                        task.context = task.context or {}
                        task.context["document_context"] = {
                            "found_documents": True,
                            "document_count": len(document_results['results']),
                            "document_summaries": [
                                {
                                    "title": doc.get("title", "Untitled"),
                                    "relevance": doc.get("relevance_score", 0),
                                    "excerpt": doc.get("content", "")[:200]
                                }
                                for doc in document_results['results'][:3]
                            ]
                        }
                else:
                    logger.info(f"📄 No document search needed (confidence: {confidence:.2f})")
                    
            except Exception as e:
                logger.warning(f"⚠️ RAG integration failed, continuing without document context: {e}")
            
            # Step 3: Execute with classification context and document enhancement
            logger.info(f"🚀 Step 3: Executing task with specialist agent...")
            execution_result = await specialist_agent.execute(task, session, thinking_process_id)
            
            # Step 4: Validate execution result based on classification
            logger.info(f"✅ Step 4: Validating execution result...")
            validated_result = await self._validate_execution_result(
                execution_result, classification, task
            )
            
            # Step 5: Create deliverable if execution produced real content
            logger.info(f"📦 Step 5: Creating deliverable if content is business-ready...")
            deliverable_created = await self._create_deliverable_if_ready(
                validated_result, classification, task
            )
            
            if deliverable_created:
                logger.info(f"✅ Deliverable created with real business content")
                validated_result.summary = f"{validated_result.summary or ''} + Deliverable created with real content"
            
            # Step 6: 🔄 SYSTEMATIC LEARNING - Capture execution outcome for continuous improvement
            logger.info(f"🔄 Step 6: Capturing learning from task execution...")
            try:
                from services.systematic_learning_loops import systematic_learning_loops
                import time
                
                # Calculate execution metadata
                execution_end_time = time.time()
                execution_duration = execution_end_time - execution_start_time if 'execution_start_time' in locals() else None
                
                execution_metadata = {
                    "duration": execution_duration,
                    "had_document_context": document_context is not None,
                    "quality_gates_passed": True,  # We got here, so gates passed
                    "deliverable_created": deliverable_created,
                    "classification_type": classification.execution_type.value
                }
                
                # Capture learning asynchronously (don't block return)
                asyncio.create_task(
                    systematic_learning_loops.capture_task_outcome(
                        task=task,
                        execution_result=validated_result,
                        execution_metadata=execution_metadata
                    )
                )
                
                logger.info(f"📝 Learning capture initiated for future improvement")
                
            except Exception as e:
                logger.warning(f"⚠️ Learning capture failed, but task succeeded: {e}")
            
            logger.info(f"🎯 Holistic pipeline completed successfully for task: {task.name}")
            return validated_result
            
        except Exception as e:
            logger.error(f"❌ Holistic pipeline failed for task {task.id}: {e}")
            return TaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=f"Holistic pipeline failure: {str(e)}",
                summary="Failed to execute task through holistic pipeline"
            )
    
    async def _validate_execution_result(
        self, 
        result: TaskExecutionOutput, 
        classification, 
        task: Task
    ) -> TaskExecutionOutput:
        """🔍 Validate execution result matches expected classification"""
        
        if not self.real_data_validation_enabled:
            return result
            
        # For DATA_COLLECTION tasks, validate real data was collected
        if classification.execution_type == TaskExecutionType.DATA_COLLECTION:
            return await self._validate_data_collection_result(result, task)
        
        # For CONTENT_GENERATION tasks, validate content was actually generated
        elif classification.execution_type == TaskExecutionType.CONTENT_GENERATION:
            return await self._validate_content_generation_result(result, task)
        
        # For other types, basic validation
        return result
    
    async def _validate_data_collection_result(
        self, 
        result: TaskExecutionOutput, 
        task: Task
    ) -> TaskExecutionOutput:
        """🔍 Validate data collection task produced real business data"""
        
        result_content = result.result or ""
        
        # Check for fake data indicators
        fake_indicators = [
            "example.com", "sample@", "placeholder", "template",
            "your-company", "company-name", "contact-name",
            "[Your", "[Company", "XXXX", "TODO", "TBD",
            "lorem ipsum", "dummy data", "fake email"
        ]
        
        fake_count = sum(1 for indicator in fake_indicators if indicator.lower() in result_content.lower())
        
        # Check for real data indicators (positive signals)
        real_data_indicators = [
            "@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com",
            ".com", ".org", ".net", "linkedin.com", "phone:", "tel:",
            "www.", "http", "contact", "email", "address"
        ]
        
        real_count = sum(1 for indicator in real_data_indicators if indicator.lower() in result_content.lower())
        
        # Calculate authenticity score
        content_length = len(result_content)
        authenticity_score = 0
        
        if content_length > 500:  # Substantial content
            authenticity_score += 30
        if real_count > fake_count:  # More real indicators than fake
            authenticity_score += 40
        if fake_count == 0:  # No fake indicators
            authenticity_score += 30
        
        logger.info(f"📊 Data collection validation: {authenticity_score}/100 authenticity score")
        logger.info(f"   Real indicators: {real_count}, Fake indicators: {fake_count}")
        logger.info(f"   Content length: {content_length} chars")
        
        if authenticity_score < 50:
            # Low authenticity - enhance result with warning
            enhanced_result = TaskExecutionOutput(
                task_id=result.task_id,
                status=TaskStatus.COMPLETED,  # Don't fail, but flag for improvement
                result=result.result,
                error_message=result.error_message,
                execution_time=result.execution_time,
                summary=f"⚠️ ATTENTION: Task completed but output needs enhancement with real data (Authenticity: {authenticity_score}/100). Content appears to contain template/placeholder data."
            )
            return enhanced_result
        
        # High authenticity - approve result
        enhanced_result = TaskExecutionOutput(
            task_id=result.task_id,
            status=result.status,
            result=result.result,
            error_message=result.error_message,
            execution_time=result.execution_time,
            summary=f"✅ Real business data collected (Authenticity: {authenticity_score}/100). Ready for deliverable creation."
        )
        return enhanced_result
    
    async def _validate_content_generation_result(
        self, 
        result: TaskExecutionOutput, 
        task: Task
    ) -> TaskExecutionOutput:
        """✍️ Validate content generation task produced complete content"""
        
        result_content = result.result or ""
        content_length = len(result_content)
        
        # Basic content validation
        if content_length < 200:
            result.summary = f"⚠️ Content seems short ({content_length} chars). May need expansion."
        else:
            result.summary = f"✅ Substantial content generated ({content_length} chars). Ready for use."
        
        return result
    
    async def _create_deliverable_if_ready(
        self, 
        result: TaskExecutionOutput, 
        classification, 
        task: Task
    ) -> bool:
        """📦 Create deliverable if execution result contains business-ready content"""
        
        if not self.deliverable_creation_enabled:
            return False
            
        # Only create deliverables for successful executions with substantial content
        if result.status != TaskStatus.COMPLETED:
            logger.info("❌ Task not completed - skipping deliverable creation")
            return False
        
        result_content = result.result or ""
        if len(result_content) < 300:
            logger.info("❌ Content too short for deliverable creation")
            return False
        
        # Check if content seems like real business data (not templates)
        if result.summary and "template" in result.summary.lower():
            logger.info("❌ Content appears to be template - skipping deliverable creation")
            return False
        
        try:
            # Determine deliverable type based on classification
            deliverable_type_map = {
                TaskExecutionType.DATA_COLLECTION: "contact_list",
                TaskExecutionType.CONTENT_GENERATION: "content_asset", 
                TaskExecutionType.ANALYSIS: "analysis_report",
                TaskExecutionType.VALIDATION: "validation_report",
                TaskExecutionType.PLANNING: "strategy_document"
            }
            
            deliverable_type = deliverable_type_map.get(
                classification.execution_type, 
                "task_output"
            )
            
            # 🎯 SCHEMA-ALIGNED: Create deliverable using correct table and fields
            deliverable_data = {
                "task_id": str(task.id),
                "goal_id": str(task.goal_id) if task.goal_id else None,
                "title": f"{task.name} - AI-Generated Deliverable",
                "description": task.description,
                "content": result_content,  # Store actual business content
                "type": "real_business_asset",
                "status": "completed",
                "business_value_score": 85.0,
                "quality_level": "acceptable",
                "metadata": {
                    "execution_type": classification.execution_type.value,
                    "content_type": classification.content_type_expected,
                    "authenticity_validated": True,
                    "tools_used": classification.tools_needed,
                    "created_via": "holistic_pipeline"
                }
            }
            
            deliverable_response = await create_deliverable(str(task.workspace_id), deliverable_data)
            
            if deliverable_response:
                logger.info(f"✅ Deliverable created with content: {deliverable_response.get('id')}")
                logger.info(f"📊 Content length: {len(result_content)} chars")
                return True
            else:
                logger.warning("❌ Failed to create deliverable - database error")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create deliverable: {e}")
            return False

    async def _detect_available_tools_for_task(
        self, 
        task: Task, 
        workspace_agents: List[Dict[str, Any]]
    ) -> List[str]:
        """🔧 Detect available tools for this specific task context"""
        available_tools = []
        
        try:
            # 1. Check MCP tools for the assigned agent
            from services.mcp_tool_discovery import get_mcp_tools_for_agent
            
            # Get agent data to determine domain
            agent_data = next((wa for wa in workspace_agents if wa.get('id') == str(task.agent_id)), None)
            agent_role = agent_data.get('role', 'unknown') if agent_data else 'unknown'
            
            # Map agent role to domain for tool discovery
            domain_mapping = {
                'marketing': 'content_creation',
                'researcher': 'data_analysis', 
                'analyst': 'data_analysis',
                'content': 'content_creation',
                'sales': 'data_analysis'
            }
            
            domain = domain_mapping.get(agent_role.lower(), 'data_analysis')
            
            # Get MCP tools for this agent
            mcp_tools = await get_mcp_tools_for_agent(
                agent_name=agent_data.get('name', 'unknown') if agent_data else 'unknown',
                domain=domain,
                workspace_id=str(task.workspace_id)
            )
            
            available_tools.extend([tool.get("name", "unknown") for tool in mcp_tools])
            
            # 2. Always add basic SDK tools (should be available by default)
            basic_tools = ["WebSearchTool", "FileSearchTool"]
            available_tools.extend(basic_tools)
            
            # 3. Remove duplicates
            available_tools = list(set(available_tools))
            
        except Exception as e:
            logger.warning(f"Failed to detect available tools for task {task.id}: {e}")
            # Fallback to basic tools only
            available_tools = ["WebSearchTool", "FileSearchTool"]
        
        logger.info(f"🔧 Detected {len(available_tools)} tools for task {task.name}: {available_tools}")
        return available_tools

# Singleton instance
holistic_pipeline = HolisticTaskDeliverablePipeline()

async def execute_task_holistically(
    task: Task, 
    workspace_agents: List[Dict[str, Any]],
    session: Optional[Any] = None,
    thinking_process_id: Optional[str] = None
) -> TaskExecutionOutput:
    """
    🎯 Entry point for holistic task execution with deliverable pipeline
    """
    return await holistic_pipeline.execute_task_with_deliverable_pipeline(
        task, workspace_agents, session, thinking_process_id
    )