#!/usr/bin/env python3
"""
🚦 PRE-EXECUTION QUALITY GATES SERVICE

Quality checks and validation before task execution begins.
Ensures tasks are well-formed, have necessary resources, and
meet quality criteria before consuming execution resources.

Part of the Goal-Driven Intelligent Integration:
Memory → Enhanced Task Generation → RAG-Enhanced Execution → Quality Gates → Learning Feedback
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
from enum import Enum

from models import Task, TaskStatus, Agent as AgentModel
from database import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()

class QualityGateStatus(Enum):
    """Status of quality gate check"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

class QualityGateResult:
    """Result of a quality gate check"""
    
    def __init__(
        self,
        gate_name: str,
        status: QualityGateStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None
    ):
        self.gate_name = gate_name
        self.status = status
        self.message = message
        self.details = details or {}
        self.recommendations = recommendations or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }

class PreExecutionQualityGates:
    """
    🚦 Pre-execution quality gate system
    
    Performs comprehensive quality checks before task execution:
    1. Task Completeness - Has all required fields and context
    2. Agent Readiness - Agent exists and is active
    3. Resource Availability - Required tools and documents available
    4. Dependency Resolution - Prerequisites completed
    5. Anti-Pattern Detection - Prevents known bad patterns
    6. Memory Integration - Leverages past successes/failures
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        self.strict_mode = os.getenv("QUALITY_GATES_STRICT_MODE", "false").lower() == "true"
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ Pre-execution Quality Gates initialized with AI")
            except ImportError:
                self.ai_available = False
                logger.warning("⚠️ OpenAI not available for AI quality checks")
        else:
            self.ai_available = False
            logger.info("ℹ️ Quality Gates operating in rule-based mode")
    
    async def run_all_gates(
        self,
        task: Task,
        agent: Optional[AgentModel] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[QualityGateResult], Dict[str, Any]]:
        """
        Run all quality gates on a task
        
        Returns:
            Tuple of (can_proceed, gate_results, enhanced_context)
        """
        
        logger.info(f"🚦 Running pre-execution quality gates for task: {task.name}")
        
        gate_results = []
        enhanced_context = {}
        
        # Gate 1: Task Completeness Check
        completeness_result = await self._check_task_completeness(task)
        gate_results.append(completeness_result)
        
        # Gate 2: Agent Readiness Check
        if agent:
            readiness_result = await self._check_agent_readiness(agent, task)
            gate_results.append(readiness_result)
        
        # Gate 3: Resource Availability Check
        resource_result = await self._check_resource_availability(task, workspace_context)
        gate_results.append(resource_result)
        
        # Gate 4: Dependency Resolution Check
        dependency_result = await self._check_dependencies(task, workspace_context)
        gate_results.append(dependency_result)
        
        # Gate 5: Anti-Pattern Detection
        if self.ai_available:
            antipattern_result = await self._detect_antipatterns(task)
            gate_results.append(antipattern_result)
        
        # Gate 6: Memory-Based Quality Check
        memory_result = await self._check_memory_insights(task, workspace_context)
        gate_results.append(memory_result)
        if memory_result.status == QualityGateStatus.PASSED and memory_result.details:
            enhanced_context.update(memory_result.details)
        
        # Determine if we can proceed
        failed_gates = [r for r in gate_results if r.status == QualityGateStatus.FAILED]
        warning_gates = [r for r in gate_results if r.status == QualityGateStatus.WARNING]
        
        can_proceed = len(failed_gates) == 0
        if self.strict_mode and len(warning_gates) > 0:
            can_proceed = False
        
        # Log summary
        logger.info(f"🚦 Quality Gates Summary: {len(gate_results)} checks, "
                   f"{len(failed_gates)} failed, {len(warning_gates)} warnings")
        
        for result in gate_results:
            if result.status == QualityGateStatus.FAILED:
                logger.error(f"❌ {result.gate_name}: {result.message}")
            elif result.status == QualityGateStatus.WARNING:
                logger.warning(f"⚠️ {result.gate_name}: {result.message}")
            else:
                logger.info(f"✅ {result.gate_name}: {result.message}")
        
        return can_proceed, gate_results, enhanced_context
    
    async def _check_task_completeness(self, task: Task) -> QualityGateResult:
        """Check if task has all required fields and is well-formed"""
        
        missing_fields = []
        warnings = []
        
        # Required fields
        if not task.name or task.name.strip() == "":
            missing_fields.append("name")
        
        if not task.description or len(task.description.strip()) < 10:
            missing_fields.append("meaningful description")
        
        if not task.agent_id:
            missing_fields.append("agent_id")
        
        if not task.workspace_id:
            missing_fields.append("workspace_id")
        
        # Warning-level checks
        if task.priority is None or task.priority == 0:
            warnings.append("No priority set")
        
        if not task.context or len(task.context) == 0:
            warnings.append("No execution context provided")
        
        # Determine status
        if missing_fields:
            return QualityGateResult(
                gate_name="Task Completeness",
                status=QualityGateStatus.FAILED,
                message=f"Missing required fields: {', '.join(missing_fields)}",
                recommendations=["Ensure task is properly created with all required fields"]
            )
        elif warnings:
            return QualityGateResult(
                gate_name="Task Completeness",
                status=QualityGateStatus.WARNING,
                message=f"Task complete but has warnings: {', '.join(warnings)}",
                recommendations=["Consider adding priority and context for better execution"]
            )
        else:
            return QualityGateResult(
                gate_name="Task Completeness",
                status=QualityGateStatus.PASSED,
                message="Task is complete and well-formed"
            )
    
    async def _check_agent_readiness(self, agent: AgentModel, task: Task) -> QualityGateResult:
        """Check if agent is ready to execute the task"""
        
        # Check agent status
        if agent.status != "active":
            return QualityGateResult(
                gate_name="Agent Readiness",
                status=QualityGateStatus.FAILED,
                message=f"Agent is not active (status: {agent.status})",
                recommendations=["Activate agent or reassign task to active agent"]
            )
        
        # Check agent-task compatibility
        if hasattr(agent, 'skills') and agent.skills:
            task_keywords = task.name.lower().split() + task.description.lower().split()[:10]
            skill_match = any(
                skill.lower() in " ".join(task_keywords) 
                for skill in agent.skills
            )
            
            if not skill_match:
                return QualityGateResult(
                    gate_name="Agent Readiness",
                    status=QualityGateStatus.WARNING,
                    message="Agent skills may not match task requirements",
                    details={"agent_skills": agent.skills, "task_keywords": task_keywords[:5]},
                    recommendations=["Consider reassigning to more suitable agent"]
                )
        
        return QualityGateResult(
            gate_name="Agent Readiness",
            status=QualityGateStatus.PASSED,
            message=f"Agent {agent.name} is ready to execute task"
        )
    
    async def _check_resource_availability(
        self, 
        task: Task, 
        workspace_context: Optional[Dict[str, Any]]
    ) -> QualityGateResult:
        """Check if required resources (tools, documents) are available"""
        
        unavailable_resources = []
        
        # Check for tool requirements in task description
        tool_keywords = ["web search", "file search", "document", "research", "analyze"]
        task_text = f"{task.name} {task.description}".lower()
        
        required_tools = [kw for kw in tool_keywords if kw in task_text]
        
        if required_tools:
            # Check workspace has document access configured
            if workspace_context:
                has_documents = workspace_context.get("has_documents", False)
                if "document" in required_tools and not has_documents:
                    unavailable_resources.append("Document access not configured")
        
        if unavailable_resources:
            return QualityGateResult(
                gate_name="Resource Availability",
                status=QualityGateStatus.WARNING,
                message=f"Some resources may be unavailable: {', '.join(unavailable_resources)}",
                recommendations=["Upload documents to workspace if needed", "Ensure tools are configured"]
            )
        
        return QualityGateResult(
            gate_name="Resource Availability",
            status=QualityGateStatus.PASSED,
            message="All required resources appear to be available"
        )
    
    async def _check_dependencies(
        self, 
        task: Task, 
        workspace_context: Optional[Dict[str, Any]]
    ) -> QualityGateResult:
        """Check if task dependencies are resolved"""
        
        if not task.depends_on:
            return QualityGateResult(
                gate_name="Dependency Resolution",
                status=QualityGateStatus.PASSED,
                message="No dependencies to check"
            )
        
        try:
            # Check dependency tasks status
            unresolved = []
            for dep_id in task.depends_on:
                dep_response = supabase.table("tasks").select("*").eq("id", str(dep_id)).execute()
                if dep_response.data and len(dep_response.data) > 0:
                    dep_task = dep_response.data[0]
                    if dep_task["status"] not in ["completed", "verified"]:
                        unresolved.append(f"{dep_task['name']} ({dep_task['status']})")
                else:
                    unresolved.append(f"Unknown task {dep_id}")
            
            if unresolved:
                return QualityGateResult(
                    gate_name="Dependency Resolution",
                    status=QualityGateStatus.FAILED,
                    message=f"Unresolved dependencies: {', '.join(unresolved)}",
                    recommendations=["Wait for dependencies to complete", "Review dependency chain"]
                )
            
            return QualityGateResult(
                gate_name="Dependency Resolution",
                status=QualityGateStatus.PASSED,
                message="All dependencies resolved"
            )
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return QualityGateResult(
                gate_name="Dependency Resolution",
                status=QualityGateStatus.WARNING,
                message="Could not verify all dependencies",
                details={"error": str(e)}
            )
    
    async def _detect_antipatterns(self, task: Task) -> QualityGateResult:
        """Use AI to detect known anti-patterns in task definition"""
        
        try:
            prompt = f"""
            Analyze this task for common anti-patterns and quality issues:
            
            Task: {task.name}
            Description: {task.description}
            Priority: {task.priority}
            Context: {task.context}
            
            Check for:
            1. Vague or ambiguous requirements
            2. Tasks that are too large (should be broken down)
            3. Missing success criteria
            4. Circular logic or impossible requirements
            5. Placeholder or fake content generation requests
            
            Respond with JSON:
            {{
                "has_antipatterns": true/false,
                "severity": "low/medium/high",
                "patterns_found": ["pattern1", "pattern2"],
                "recommendations": ["recommendation1", "recommendation2"]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a task quality analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = eval(response.choices[0].message.content)
            
            if result["has_antipatterns"]:
                status = QualityGateStatus.FAILED if result["severity"] == "high" else QualityGateStatus.WARNING
                return QualityGateResult(
                    gate_name="Anti-Pattern Detection",
                    status=status,
                    message=f"Anti-patterns detected: {', '.join(result['patterns_found'])}",
                    details=result,
                    recommendations=result["recommendations"]
                )
            
            return QualityGateResult(
                gate_name="Anti-Pattern Detection",
                status=QualityGateStatus.PASSED,
                message="No significant anti-patterns detected"
            )
            
        except Exception as e:
            logger.error(f"Error in anti-pattern detection: {e}")
            return QualityGateResult(
                gate_name="Anti-Pattern Detection",
                status=QualityGateStatus.SKIPPED,
                message="Could not perform anti-pattern detection",
                details={"error": str(e)}
            )
    
    async def _check_memory_insights(
        self, 
        task: Task, 
        workspace_context: Optional[Dict[str, Any]]
    ) -> QualityGateResult:
        """Check workspace memory for relevant insights about similar tasks"""
        
        try:
            from services.workspace_memory_system import workspace_memory_system
            
            # Get insights about similar tasks
            insights = await workspace_memory_system.get_relevant_insights(
                workspace_id=str(task.workspace_id),
                context_type="task_execution",
                query=f"{task.name} {task.description[:100]}"
            )
            
            if not insights:
                return QualityGateResult(
                    gate_name="Memory Insights",
                    status=QualityGateStatus.PASSED,
                    message="No relevant memory insights found"
                )
            
            # Analyze insights for warnings or enhancements
            failure_patterns = insights.get("failure_patterns", [])
            success_patterns = insights.get("success_patterns", [])
            recommendations = insights.get("recommendations", [])
            
            if failure_patterns:
                # Check if this task matches any failure patterns
                task_text = f"{task.name} {task.description}".lower()
                matching_failures = [
                    fp for fp in failure_patterns 
                    if any(keyword in task_text for keyword in fp.get("keywords", []))
                ]
                
                if matching_failures:
                    return QualityGateResult(
                        gate_name="Memory Insights",
                        status=QualityGateStatus.WARNING,
                        message=f"Task matches {len(matching_failures)} known failure patterns",
                        details={
                            "failure_patterns": matching_failures,
                            "success_patterns": success_patterns
                        },
                        recommendations=recommendations + ["Review and address known failure patterns"]
                    )
            
            # Enhance with success patterns
            return QualityGateResult(
                gate_name="Memory Insights",
                status=QualityGateStatus.PASSED,
                message=f"Found {len(success_patterns)} relevant success patterns",
                details={
                    "success_patterns": success_patterns,
                    "memory_recommendations": recommendations
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.warning(f"Could not check memory insights: {e}")
            return QualityGateResult(
                gate_name="Memory Insights",
                status=QualityGateStatus.SKIPPED,
                message="Memory insights not available",
                details={"error": str(e)}
            )

# Global instance
pre_execution_quality_gates = PreExecutionQualityGates()