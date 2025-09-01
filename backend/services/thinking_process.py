"""
Real-Time Thinking Process - Pillar 10: Real-Time Thinking
Captures and visualizes AI reasoning process similar to Claude/o3 style thinking.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, AsyncGenerator
from uuid import UUID, uuid4
from dataclasses import dataclass

from database import get_supabase_client

logger = logging.getLogger(__name__)

@dataclass
class ThinkingStep:
    """Individual thinking step in reasoning chain"""
    step_id: str
    step_type: str  # analysis, reasoning, evaluation, conclusion
    content: str
    confidence: float
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ThinkingProcess:
    """Complete thinking process for a task/goal"""
    process_id: str
    workspace_id: str
    context: str
    steps: List[ThinkingStep]
    final_conclusion: Optional[str]
    overall_confidence: float
    started_at: str
    completed_at: Optional[str]

class RealTimeThinkingEngine:
    """
    Real-Time Thinking Engine (Pillar 10: Real-Time Thinking)
    
    Captures, stores, and broadcasts AI reasoning processes in real-time
    similar to Claude/o3 thinking visualization.
    """
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.active_processes: Dict[str, ThinkingProcess] = {}
        self.websocket_handlers: List[Any] = []
        
        logger.info("💭 Real-Time Thinking Engine initialized")
    
    async def start_thinking_process(self, workspace_id: UUID, context: str, 
                                   process_type: str = "general") -> str:
        """Start a new thinking process"""
        process_id = str(uuid4())
        
        thinking_process = ThinkingProcess(
            process_id=process_id,
            workspace_id=str(workspace_id),
            context=context,
            steps=[],
            final_conclusion=None,
            overall_confidence=0.0,
            started_at=datetime.utcnow().isoformat(),
            completed_at=None
        )
        
        self.active_processes[process_id] = thinking_process
        
        # Store in database
        await self._store_thinking_process(thinking_process)
        
        # Broadcast start event
        await self._broadcast_thinking_event("process_started", {
            "process_id": process_id,
            "workspace_id": str(workspace_id),
            "context": context,
            "process_type": process_type
        })
        
        logger.info(f"💭 Started thinking process: {process_id}")
        return process_id
    
    async def add_thinking_step(self, process_id: str, step_type: str, content: str, 
                              confidence: float = 0.5, metadata: Optional[Dict] = None) -> str:
        """Add a thinking step to active process"""
        if process_id not in self.active_processes:
            raise ValueError(f"No active thinking process: {process_id}")
        
        step_id = str(uuid4())
        step = ThinkingStep(
            step_id=step_id,
            step_type=step_type,
            content=content,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        # Add to active process
        self.active_processes[process_id].steps.append(step)
        
        # Update database
        await self._store_thinking_step(process_id, step)
        
        # Broadcast step in real-time
        await self._broadcast_thinking_event("step_added", {
            "process_id": process_id,
            "step": {
                "step_id": step_id,
                "step_type": step_type,
                "content": content,
                "confidence": confidence,
                "timestamp": step.timestamp,
                "metadata": metadata  # Include metadata in broadcast
            }
        })
        
        logger.debug(f"💭 Added thinking step: {step_type} - {content[:50]}")
        return step_id
    
    async def complete_thinking_process(self, process_id: str, conclusion: str, 
                                      overall_confidence: float) -> ThinkingProcess:
        """Complete a thinking process with final conclusion"""
        if process_id not in self.active_processes:
            raise ValueError(f"No active thinking process: {process_id}")
        
        thinking_process = self.active_processes[process_id]
        thinking_process.final_conclusion = conclusion
        thinking_process.overall_confidence = overall_confidence
        thinking_process.completed_at = datetime.utcnow().isoformat()
        
        # Update database
        await self._update_thinking_process_completion(thinking_process)
        
        # Broadcast completion
        await self._broadcast_thinking_event("process_completed", {
            "process_id": process_id,
            "conclusion": conclusion,
            "confidence": overall_confidence,
            "total_steps": len(thinking_process.steps)
        })
        
        # Remove from active processes
        completed_process = self.active_processes.pop(process_id)
        
        logger.info(f"💭 Completed thinking process: {process_id} with {len(completed_process.steps)} steps")
        return completed_process
    
    async def get_thinking_process(self, process_id: str) -> Optional[ThinkingProcess]:
        """Get thinking process by ID"""
        # Check active processes first
        if process_id in self.active_processes:
            return self.active_processes[process_id]
        
        # Retrieve from database
        try:
            response = self.supabase.table("thinking_processes") \
                .select("*") \
                .eq("process_id", process_id) \
                .execute()
            
            if not response.data:
                return None
            
            process_data = response.data[0]
            
            # Get steps
            steps_response = self.supabase.table("thinking_steps") \
                .select("*") \
                .eq("process_id", process_id) \
                .order("created_at", desc=False) \
                .execute()
            
            steps = []
            for step_data in steps_response.data:
                steps.append(ThinkingStep(
                    step_id=step_data["step_id"],
                    step_type=step_data["step_type"],
                    content=step_data["content"],
                    confidence=step_data["confidence"],
                    timestamp=step_data["created_at"],
                    metadata=step_data.get("metadata", {})
                ))
            
            return ThinkingProcess(
                process_id=process_data["process_id"],
                workspace_id=process_data["workspace_id"],
                context=process_data["context"],
                steps=steps,
                final_conclusion=process_data.get("final_conclusion"),
                overall_confidence=process_data.get("overall_confidence", 0.0),
                started_at=process_data["started_at"],
                completed_at=process_data.get("completed_at")
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve thinking process {process_id}: {e}")
            return None
    
    async def get_workspace_thinking(self, workspace_id: UUID, limit: int = 10) -> List[ThinkingProcess]:
        """Get recent thinking processes for workspace"""
        try:
            response = self.supabase.table("thinking_processes") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .order("started_at", desc=True) \
                .limit(limit) \
                .execute()
            
            processes = []
            for process_data in response.data:
                # Get steps for each process (limit to avoid performance issues)
                steps_response = self.supabase.table("thinking_steps") \
                    .select("*") \
                    .eq("process_id", process_data["process_id"]) \
                    .order("created_at", desc=False) \
                    .limit(20) \
                    .execute()
                
                steps = []
                for step_data in steps_response.data:
                    steps.append(ThinkingStep(
                        step_id=step_data["step_id"],
                        step_type=step_data["step_type"],
                        content=step_data["content"],
                        confidence=step_data["confidence"],
                        timestamp=step_data["created_at"],
                        metadata=step_data.get("metadata", {})
                    ))
                
                processes.append(ThinkingProcess(
                    process_id=process_data["process_id"],
                    workspace_id=process_data["workspace_id"],
                    context=process_data["context"],
                    steps=steps,
                    final_conclusion=process_data.get("final_conclusion"),
                    overall_confidence=process_data.get("overall_confidence", 0.0),
                    started_at=process_data["started_at"],
                    completed_at=process_data.get("completed_at")
                ))
            
            return processes
            
        except Exception as e:
            logger.error(f"Failed to get workspace thinking: {e}")
            return []
    
    async def generate_o3_style_thinking(self, workspace_id: UUID, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate O3/Claude-style thinking process for a query
        
        Yields thinking steps in real-time as they're generated
        """
        process_id = await self.start_thinking_process(workspace_id, query, "o3_style")
        
        try:
            # Step 1: Context Loading
            yield await self._yield_thinking_step(process_id, "context_loading", 
                "Loading workspace context and relevant information...", 0.9)
            
            await asyncio.sleep(0.5)  # Simulate thinking time
            
            # Step 2: Problem Analysis
            yield await self._yield_thinking_step(process_id, "analysis", 
                f"Analyzing the query: '{query}'. Breaking down components and identifying key requirements.", 0.8)
            
            await asyncio.sleep(0.8)
            
            # Step 3: Multiple Perspectives
            yield await self._yield_thinking_step(process_id, "perspective", 
                "Considering multiple approaches: 1) Direct implementation 2) Iterative development 3) Risk-first approach", 0.7)
            
            await asyncio.sleep(0.6)
            
            # Step 4: Deep Evaluation
            yield await self._yield_thinking_step(process_id, "evaluation", 
                "Evaluating trade-offs between speed, quality, and maintainability. Considering long-term implications.", 0.8)
            
            await asyncio.sleep(0.7)
            
            # Step 5: Critical Review
            yield await self._yield_thinking_step(process_id, "critical_review", 
                "Critical review: Am I missing any edge cases? Are there simpler solutions? What could go wrong?", 0.7)
            
            await asyncio.sleep(0.5)
            
            # Step 6: Synthesis
            conclusion = f"Based on analysis, the optimal approach is to implement a phased solution focusing on immediate business value while maintaining flexibility for future enhancements."
            
            yield await self._yield_thinking_step(process_id, "synthesis", conclusion, 0.9)
            
            # Complete process
            await self.complete_thinking_process(process_id, conclusion, 0.85)
            
        except Exception as e:
            logger.error(f"O3-style thinking generation failed: {e}")
            await self.complete_thinking_process(process_id, f"Error in thinking process: {e}", 0.1)
    
    async def _yield_thinking_step(self, process_id: str, step_type: str, content: str, confidence: float) -> Dict[str, Any]:
        """Helper to add step and return formatted response"""
        step_id = await self.add_thinking_step(process_id, step_type, content, confidence)
        
        return {
            "process_id": process_id,
            "step_id": step_id,
            "step_type": step_type,
            "content": content,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _store_thinking_process(self, thinking_process: ThinkingProcess):
        """Store thinking process in database"""
        try:
            process_data = {
                "process_id": thinking_process.process_id,
                "workspace_id": thinking_process.workspace_id,
                "context": thinking_process.context,
                "started_at": thinking_process.started_at,
                "overall_confidence": thinking_process.overall_confidence
            }
            
            self.supabase.table("thinking_processes").insert(process_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store thinking process: {e}")
    
    async def _store_thinking_step(self, process_id: str, step: ThinkingStep):
        """Store thinking step in database"""
        try:
            step_data = {
                "step_id": step.step_id,
                "process_id": process_id,
                "step_type": step.step_type,
                "content": step.content,
                "confidence": step.confidence,
                "metadata": step.metadata,
                "created_at": step.timestamp
            }
            
            self.supabase.table("thinking_steps").insert(step_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store thinking step: {e}")
    
    async def _update_thinking_process_completion(self, thinking_process: ThinkingProcess):
        """Update thinking process completion in database"""
        try:
            update_data = {
                "final_conclusion": thinking_process.final_conclusion,
                "overall_confidence": thinking_process.overall_confidence,
                "completed_at": thinking_process.completed_at
            }
            
            self.supabase.table("thinking_processes") \
                .update(update_data) \
                .eq("process_id", thinking_process.process_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update thinking process completion: {e}")
    
    async def _broadcast_thinking_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast thinking event to WebSocket clients"""
        try:
            # Format the thinking step for WebSocket broadcast
            if event_type == "step_added" and "step" in data:
                # Extract workspace_id from process
                workspace_id = None
                if data.get("process_id") and data["process_id"] in self.active_processes:
                    workspace_id = self.active_processes[data["process_id"]].workspace_id
                
                if workspace_id:
                    # Broadcast thinking step via WebSocket
                    try:
                        from routes.websocket import broadcast_thinking_step
                        await broadcast_thinking_step(workspace_id, data["step"])
                        logger.debug(f"💭 Broadcasted thinking step to workspace {workspace_id}")
                    except Exception as ws_error:
                        logger.warning(f"WebSocket broadcast failed: {ws_error}")
            
            # Also handle goal decomposition events
            elif event_type == "process_started" and data.get("workspace_id"):
                try:
                    from routes.websocket import broadcast_goal_decomposition_start
                    goal_data = {
                        "id": data.get("process_id"),
                        "description": data.get("context", "Processing goal...")
                    }
                    await broadcast_goal_decomposition_start(data["workspace_id"], goal_data)
                    logger.debug(f"💭 Broadcasted goal decomposition start to workspace {data['workspace_id']}")
                except Exception as ws_error:
                    logger.warning(f"Goal decomposition start broadcast failed: {ws_error}")
            
            elif event_type == "process_completed" and data.get("process_id"):
                # Find workspace_id for completed process
                workspace_id = None
                if data["process_id"] in self.active_processes:
                    workspace_id = self.active_processes[data["process_id"]].workspace_id
                
                if workspace_id:
                    try:
                        from routes.websocket import broadcast_goal_decomposition_complete
                        await broadcast_goal_decomposition_complete(workspace_id, data)
                        logger.debug(f"💭 Broadcasted goal decomposition complete to workspace {workspace_id}")
                    except Exception as ws_error:
                        logger.warning(f"Goal decomposition complete broadcast failed: {ws_error}")
            
            # Log all thinking events
            logger.debug(f"💭 Broadcasting thinking event: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast thinking event: {e}")
    
    def register_websocket_handler(self, handler):
        """Register WebSocket handler for real-time broadcasting"""
        self.websocket_handlers.append(handler)
        logger.info("📡 WebSocket handler registered for thinking broadcasts")
    
    def get_current_time(self) -> str:
        """Get current time in ISO format"""
        return datetime.utcnow().isoformat()
    
    # ============= ENHANCED AGENT AND TOOL METADATA METHODS =============
    
    async def add_agent_thinking_step(self, process_id: str, agent_info: Dict[str, Any], 
                                     action_description: str, confidence: float = 0.7) -> str:
        """
        Add a thinking step with agent metadata capture.
        
        Args:
            process_id: ID of the active thinking process
            agent_info: Dict containing agent metadata (name, role, seniority, id, etc.)
            action_description: Description of what the agent is doing
            confidence: Confidence level for this action (0.0-1.0)
        
        Returns:
            step_id: ID of the created thinking step
        """
        # Structure agent metadata
        agent_metadata = {
            "agent": {
                "id": agent_info.get("id"),
                "name": agent_info.get("name"),
                "role": agent_info.get("role"),
                "seniority": agent_info.get("seniority"),
                "skills": agent_info.get("skills", []),
                "status": agent_info.get("status")
            },
            "execution_context": {
                "workspace_id": agent_info.get("workspace_id"),
                "task_id": agent_info.get("task_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Create content with agent context
        content = f"🤖 Agent '{agent_info.get('role', 'Unknown')}' ({agent_info.get('seniority', 'unknown')} level): {action_description}"
        
        # Add the thinking step with agent metadata
        # Use 'reasoning' as the step_type since it's an allowed value
        step_id = await self.add_thinking_step(
            process_id=process_id,
            step_type="reasoning",  # Use allowed step_type
            content=content,
            confidence=confidence,
            metadata=agent_metadata
        )
        
        logger.info(f"💭 Added agent thinking step: {agent_info.get('role')} - {action_description[:50]}")
        return step_id
    
    async def add_tool_execution_step(self, process_id: str, tool_results: Dict[str, Any],
                                     step_description: str, confidence: float = 0.8) -> str:
        """
        Add a thinking step with tool execution metadata.
        
        Args:
            process_id: ID of the active thinking process
            tool_results: Dict containing tool execution results and metadata
            step_description: Description of the tool execution
            confidence: Confidence level for the results (0.0-1.0)
        
        Returns:
            step_id: ID of the created thinking step
        """
        # Structure tool execution metadata
        tool_metadata = {
            "tool": {
                "name": tool_results.get("tool_name"),
                "type": tool_results.get("tool_type"),
                "parameters": tool_results.get("parameters", {}),
                "execution_time_ms": tool_results.get("execution_time_ms"),
                "success": tool_results.get("success", False),
                "error": tool_results.get("error")
            },
            "results": {
                "output_type": tool_results.get("output_type"),
                "output_size": tool_results.get("output_size"),
                "summary": tool_results.get("summary"),
                "artifacts_created": tool_results.get("artifacts_created", [])
            },
            "context": {
                "agent_id": tool_results.get("agent_id"),
                "task_id": tool_results.get("task_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Create content with tool execution details
        success_indicator = "✅" if tool_results.get("success", False) else "❌"
        content = f"🔧 Tool '{tool_results.get('tool_name', 'Unknown')}' execution {success_indicator}: {step_description}"
        
        # Add error details if present
        if tool_results.get("error"):
            content += f" | Error: {tool_results.get('error')[:100]}"
        
        # Add the thinking step with tool metadata
        # Use 'evaluation' as the step_type since it's an allowed value
        step_id = await self.add_thinking_step(
            process_id=process_id,
            step_type="evaluation",  # Use allowed step_type
            content=content,
            confidence=confidence,
            metadata=tool_metadata
        )
        
        logger.info(f"💭 Added tool execution step: {tool_results.get('tool_name')} - {success_indicator}")
        return step_id
    
    async def update_step_with_agent_info(self, step_id: str, agent_info: Dict[str, Any]) -> bool:
        """
        Update an existing thinking step with agent information.
        
        Args:
            step_id: ID of the thinking step to update
            agent_info: Agent metadata to add/update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the step in active processes
            step_found = False
            for process_id, process in self.active_processes.items():
                for step in process.steps:
                    if step.step_id == step_id:
                        # Update metadata
                        if not step.metadata:
                            step.metadata = {}
                        
                        step.metadata["agent"] = {
                            "id": agent_info.get("id"),
                            "name": agent_info.get("name"),
                            "role": agent_info.get("role"),
                            "seniority": agent_info.get("seniority"),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        step_found = True
                        break
                if step_found:
                    break
            
            if not step_found:
                # Try updating in database directly
                response = self.supabase.table("thinking_steps") \
                    .select("metadata") \
                    .eq("step_id", step_id) \
                    .execute()
                
                if response.data:
                    existing_metadata = response.data[0].get("metadata", {})
                    existing_metadata["agent"] = {
                        "id": agent_info.get("id"),
                        "name": agent_info.get("name"),
                        "role": agent_info.get("role"),
                        "seniority": agent_info.get("seniority"),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    self.supabase.table("thinking_steps") \
                        .update({"metadata": existing_metadata}) \
                        .eq("step_id", step_id) \
                        .execute()
                    
                    logger.debug(f"💭 Updated step {step_id} with agent info in database")
                    return True
            else:
                # Update in database
                self.supabase.table("thinking_steps") \
                    .update({"metadata": step.metadata}) \
                    .eq("step_id", step_id) \
                    .execute()
                
                logger.debug(f"💭 Updated step {step_id} with agent info")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update step {step_id} with agent info: {e}")
            return False
    
    async def update_step_with_tool_info(self, step_id: str, tool_results: Dict[str, Any]) -> bool:
        """
        Update an existing thinking step with tool execution results.
        
        Args:
            step_id: ID of the thinking step to update
            tool_results: Tool execution results and metadata
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the step in active processes
            step_found = False
            for process_id, process in self.active_processes.items():
                for step in process.steps:
                    if step.step_id == step_id:
                        # Update metadata
                        if not step.metadata:
                            step.metadata = {}
                        
                        step.metadata["tool"] = {
                            "name": tool_results.get("tool_name"),
                            "type": tool_results.get("tool_type"),
                            "success": tool_results.get("success", False),
                            "execution_time_ms": tool_results.get("execution_time_ms"),
                            "error": tool_results.get("error"),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        step_found = True
                        break
                if step_found:
                    break
            
            if not step_found:
                # Try updating in database directly
                response = self.supabase.table("thinking_steps") \
                    .select("metadata") \
                    .eq("step_id", step_id) \
                    .execute()
                
                if response.data:
                    existing_metadata = response.data[0].get("metadata", {})
                    existing_metadata["tool"] = {
                        "name": tool_results.get("tool_name"),
                        "type": tool_results.get("tool_type"),
                        "success": tool_results.get("success", False),
                        "execution_time_ms": tool_results.get("execution_time_ms"),
                        "error": tool_results.get("error"),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    self.supabase.table("thinking_steps") \
                        .update({"metadata": existing_metadata}) \
                        .eq("step_id", step_id) \
                        .execute()
                    
                    logger.debug(f"💭 Updated step {step_id} with tool info in database")
                    return True
            else:
                # Update in database
                self.supabase.table("thinking_steps") \
                    .update({"metadata": step.metadata}) \
                    .eq("step_id", step_id) \
                    .execute()
                
                logger.debug(f"💭 Updated step {step_id} with tool info")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update step {step_id} with tool info: {e}")
            return False
    
    async def add_multi_agent_collaboration_step(self, process_id: str, agents: List[Dict[str, Any]],
                                                collaboration_type: str, description: str) -> str:
        """
        Add a thinking step for multi-agent collaboration scenarios.
        
        Args:
            process_id: ID of the active thinking process
            agents: List of agent info dicts participating in collaboration
            collaboration_type: Type of collaboration (handoff, parallel, sequential, etc.)
            description: Description of the collaboration
        
        Returns:
            step_id: ID of the created thinking step
        """
        # Structure collaboration metadata
        collaboration_metadata = {
            "collaboration": {
                "type": collaboration_type,
                "agents": [
                    {
                        "id": agent.get("id"),
                        "role": agent.get("role"),
                        "seniority": agent.get("seniority"),
                        "responsibility": agent.get("responsibility")
                    }
                    for agent in agents
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Create content with collaboration details
        agent_roles = ", ".join([agent.get("role", "Unknown") for agent in agents])
        content = f"🤝 Multi-agent collaboration ({collaboration_type}): {agent_roles} - {description}"
        
        # Add the thinking step
        # Use 'analysis' as the step_type since it's an allowed value
        step_id = await self.add_thinking_step(
            process_id=process_id,
            step_type="analysis",  # Use allowed step_type
            content=content,
            confidence=0.75,
            metadata=collaboration_metadata
        )
        
        logger.info(f"💭 Added collaboration step: {collaboration_type} with {len(agents)} agents")
        return step_id
    
    async def get_agent_performance_metrics(self, workspace_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze thinking processes to extract agent performance metrics.
        
        Args:
            workspace_id: Workspace ID to analyze
            agent_id: Optional specific agent ID to filter by
        
        Returns:
            Dict containing performance metrics per agent
        """
        try:
            # Get recent thinking processes
            # Filter by step_type 'reasoning' which contains agent actions
            query = self.supabase.table("thinking_steps") \
                .select("step_id, step_type, confidence, metadata, created_at") \
                .eq("step_type", "reasoning")
            
            if agent_id:
                # Note: JSON filtering would need to be done client-side
                # as Supabase doesn't support direct JSON field queries with ilike
                pass  # Will filter in post-processing
            
            response = query.execute()
            
            if not response.data:
                return {}
            
            # Analyze agent performance
            agent_metrics = {}
            for step in response.data:
                metadata = step.get("metadata", {})
                agent_info = metadata.get("agent", {})
                step_agent_id = agent_info.get("id")
                
                # Filter by agent_id if specified
                if agent_id and step_agent_id != agent_id:
                    continue
                
                if not step_agent_id:
                    continue
                
                if step_agent_id not in agent_metrics:
                    agent_metrics[step_agent_id] = {
                        "agent_id": step_agent_id,
                        "role": agent_info.get("role"),
                        "seniority": agent_info.get("seniority"),
                        "total_actions": 0,
                        "average_confidence": 0,
                        "confidence_scores": [],
                        "action_types": {},
                        "first_action": step.get("created_at"),
                        "last_action": step.get("created_at")
                    }
                
                metrics = agent_metrics[step_agent_id]
                metrics["total_actions"] += 1
                metrics["confidence_scores"].append(step.get("confidence", 0.5))
                
                # Track action types
                action_type = metadata.get("execution_context", {}).get("action_type", "unknown")
                metrics["action_types"][action_type] = metrics["action_types"].get(action_type, 0) + 1
                
                # Update time range
                if step.get("created_at") < metrics["first_action"]:
                    metrics["first_action"] = step.get("created_at")
                if step.get("created_at") > metrics["last_action"]:
                    metrics["last_action"] = step.get("created_at")
            
            # Calculate averages
            for agent_id, metrics in agent_metrics.items():
                if metrics["confidence_scores"]:
                    metrics["average_confidence"] = sum(metrics["confidence_scores"]) / len(metrics["confidence_scores"])
                del metrics["confidence_scores"]  # Remove raw scores from output
            
            return agent_metrics
            
        except Exception as e:
            logger.error(f"Failed to get agent performance metrics: {e}")
            return {}
    
    async def get_tool_usage_statistics(self, workspace_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze thinking processes to extract tool usage statistics.
        
        Args:
            workspace_id: Workspace ID to analyze
            time_window_hours: Hours to look back for statistics
        
        Returns:
            Dict containing tool usage statistics
        """
        try:
            # Calculate time window
            cutoff_time = (datetime.utcnow() - timedelta(hours=time_window_hours)).isoformat()
            
            # Get tool execution steps
            # Use 'evaluation' step_type which contains tool executions
            response = self.supabase.table("thinking_steps") \
                .select("step_id, metadata, confidence, created_at") \
                .eq("step_type", "evaluation") \
                .gte("created_at", cutoff_time) \
                .execute()
            
            if not response.data:
                return {"message": "No tool executions found in time window"}
            
            # Analyze tool usage
            tool_stats = {}
            total_executions = 0
            total_successes = 0
            total_failures = 0
            
            for step in response.data:
                metadata = step.get("metadata", {})
                tool_info = metadata.get("tool", {})
                tool_name = tool_info.get("name", "unknown")
                
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        "name": tool_name,
                        "type": tool_info.get("type"),
                        "executions": 0,
                        "successes": 0,
                        "failures": 0,
                        "average_execution_time_ms": 0,
                        "execution_times": [],
                        "error_types": {}
                    }
                
                stats = tool_stats[tool_name]
                stats["executions"] += 1
                total_executions += 1
                
                if tool_info.get("success", False):
                    stats["successes"] += 1
                    total_successes += 1
                else:
                    stats["failures"] += 1
                    total_failures += 1
                    
                    # Track error types
                    error = tool_info.get("error", "unknown_error")
                    error_type = error.split(":")[0] if ":" in error else error[:50]
                    stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
                
                # Track execution times
                exec_time = tool_info.get("execution_time_ms")
                if exec_time:
                    stats["execution_times"].append(exec_time)
            
            # Calculate averages and success rates
            for tool_name, stats in tool_stats.items():
                if stats["execution_times"]:
                    stats["average_execution_time_ms"] = sum(stats["execution_times"]) / len(stats["execution_times"])
                del stats["execution_times"]  # Remove raw data
                
                stats["success_rate"] = (stats["successes"] / stats["executions"] * 100) if stats["executions"] > 0 else 0
            
            return {
                "time_window_hours": time_window_hours,
                "total_executions": total_executions,
                "total_successes": total_successes,
                "total_failures": total_failures,
                "overall_success_rate": (total_successes / total_executions * 100) if total_executions > 0 else 0,
                "tools": tool_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get tool usage statistics: {e}")
            return {"error": str(e)}

# Global thinking engine instance
thinking_engine = RealTimeThinkingEngine()

# Convenience functions
async def start_thinking(workspace_id: UUID, context: str, process_type: str = "general") -> str:
    return await thinking_engine.start_thinking_process(workspace_id, context, process_type)

async def add_thinking_step(process_id: str, step_type: str, content: str, confidence: float = 0.5, metadata: Optional[Dict] = None) -> str:
    return await thinking_engine.add_thinking_step(process_id, step_type, content, confidence, metadata)

async def complete_thinking(process_id: str, conclusion: str, confidence: float) -> ThinkingProcess:
    return await thinking_engine.complete_thinking_process(process_id, conclusion, confidence)

async def get_workspace_thinking(workspace_id: UUID, limit: int = 10) -> List[ThinkingProcess]:
    return await thinking_engine.get_workspace_thinking(workspace_id, limit)

# Enhanced convenience functions for agent and tool metadata
async def add_agent_thinking_step(process_id: str, agent_info: Dict[str, Any], action_description: str, confidence: float = 0.7) -> str:
    """Convenience function for adding agent thinking steps"""
    return await thinking_engine.add_agent_thinking_step(process_id, agent_info, action_description, confidence)

async def add_tool_execution_step(process_id: str, tool_results: Dict[str, Any], step_description: str, confidence: float = 0.8) -> str:
    """Convenience function for adding tool execution steps"""
    return await thinking_engine.add_tool_execution_step(process_id, tool_results, step_description, confidence)

async def update_step_with_agent_info(step_id: str, agent_info: Dict[str, Any]) -> bool:
    """Convenience function for updating step with agent info"""
    return await thinking_engine.update_step_with_agent_info(step_id, agent_info)

async def update_step_with_tool_info(step_id: str, tool_results: Dict[str, Any]) -> bool:
    """Convenience function for updating step with tool info"""
    return await thinking_engine.update_step_with_tool_info(step_id, tool_results)

async def add_multi_agent_collaboration_step(process_id: str, agents: List[Dict[str, Any]], collaboration_type: str, description: str) -> str:
    """Convenience function for adding multi-agent collaboration steps"""
    return await thinking_engine.add_multi_agent_collaboration_step(process_id, agents, collaboration_type, description)

async def get_agent_performance_metrics(workspace_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for getting agent performance metrics"""
    return await thinking_engine.get_agent_performance_metrics(workspace_id, agent_id)

async def get_tool_usage_statistics(workspace_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
    """Convenience function for getting tool usage statistics"""
    return await thinking_engine.get_tool_usage_statistics(workspace_id, time_window_hours)