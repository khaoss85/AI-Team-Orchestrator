#!/usr/bin/env python3
"""
🧠 Enhanced Thinking Process with Agent & Tool Metadata
Extends the base thinking process to capture agent and tool usage details

Pillar Compliance:
- ✅ Pillar 10: Real-time thinking visualization
- ✅ Pillar 14: Modular service extension
- ✅ Pillar 15: Enhanced context for conversations
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from services.thinking_process import (
    ThinkingStep,
    ThinkingProcess,
    RealTimeThinkingEngine
)

logger = logging.getLogger(__name__)

@dataclass
class AgentInfo:
    """Agent information for thinking steps"""
    agent_id: str
    name: str
    role: str
    seniority: str  # junior, senior, expert
    specialization: str
    confidence_level: float = 0.0
    
@dataclass
class ToolUsage:
    """Tool usage information"""
    tool_id: str
    tool_name: str
    tool_type: str  # search, file, api, etc.
    input_summary: str
    output_summary: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class EnhancedThinkingStep(ThinkingStep):
    """Extended thinking step with agent and tool metadata"""
    agent_info: Optional[AgentInfo] = None
    tool_usage: List[ToolUsage] = field(default_factory=list)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    sub_steps: List[Dict[str, Any]] = field(default_factory=list)

class EnhancedThinkingEngine(RealTimeThinkingEngine):
    """
    🧠 Enhanced thinking engine with agent and tool tracking
    """
    
    def __init__(self):
        super().__init__()
        self.agent_registry: Dict[str, AgentInfo] = {}
        self.tool_metrics: Dict[str, Dict[str, Any]] = {}
        logger.info("🧠 Enhanced Thinking Engine initialized with agent/tool tracking")
    
    async def add_thinking_step_with_agent(
        self,
        process_id: str,
        step_type: str,
        content: str,
        agent_info: Optional[Dict[str, Any]] = None,
        tool_usage: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.5,
        execution_metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an enhanced thinking step with agent and tool information
        
        Args:
            process_id: Active thinking process ID
            step_type: Type of thinking step
            content: Step description
            agent_info: Information about the executing agent
            tool_usage: List of tools used in this step
            confidence: Confidence level
            execution_metrics: Performance metrics
            
        Returns:
            Step ID
        """
        
        # Prepare enhanced metadata
        enhanced_metadata = {
            "enhanced": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add agent information if provided
        if agent_info:
            agent = self._create_agent_info(agent_info)
            enhanced_metadata["agent"] = {
                "id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "seniority": agent.seniority,
                "specialization": agent.specialization,
                "confidence": agent.confidence_level
            }
            
            # Track agent performance
            await self._track_agent_performance(agent.agent_id, confidence)
        
        # Add tool usage if provided
        if tool_usage:
            tools = [self._create_tool_usage(tool) for tool in tool_usage]
            enhanced_metadata["tools"] = [
                {
                    "id": tool.tool_id,
                    "name": tool.tool_name,
                    "type": tool.tool_type,
                    "success": tool.success,
                    "execution_time": tool.execution_time,
                    "input_summary": tool.input_summary,
                    "output_summary": tool.output_summary,
                    "error": tool.error_message
                }
                for tool in tools
            ]
            
            # Track tool effectiveness
            for tool in tools:
                await self._track_tool_effectiveness(tool)
        
        # Add execution metrics
        if execution_metrics:
            enhanced_metadata["metrics"] = execution_metrics
        
        # Add the enhanced step using parent method
        step_id = await self.add_thinking_step(
            process_id=process_id,
            step_type=step_type,
            content=content,
            confidence=confidence,
            metadata=enhanced_metadata
        )
        
        # Broadcast enhanced information
        await self._broadcast_enhanced_step(
            process_id, step_id, enhanced_metadata
        )
        
        return step_id
    
    def _create_agent_info(self, agent_data: Dict[str, Any]) -> AgentInfo:
        """Create AgentInfo from dictionary"""
        return AgentInfo(
            agent_id=agent_data.get("id", "unknown"),
            name=agent_data.get("name", "Unknown Agent"),
            role=agent_data.get("role", "specialist"),
            seniority=agent_data.get("seniority", "senior"),
            specialization=agent_data.get("specialization", "general"),
            confidence_level=agent_data.get("confidence", 0.75)
        )
    
    def _create_tool_usage(self, tool_data: Dict[str, Any]) -> ToolUsage:
        """Create ToolUsage from dictionary"""
        return ToolUsage(
            tool_id=tool_data.get("id", "unknown"),
            tool_name=tool_data.get("name", "Unknown Tool"),
            tool_type=tool_data.get("type", "general"),
            input_summary=tool_data.get("input_summary", ""),
            output_summary=tool_data.get("output_summary", ""),
            execution_time=tool_data.get("execution_time", 0.0),
            success=tool_data.get("success", True),
            error_message=tool_data.get("error_message")
        )
    
    async def _track_agent_performance(self, agent_id: str, confidence: float):
        """Track agent performance metrics"""
        if agent_id not in self.agent_registry:
            self.agent_registry[agent_id] = {
                "total_steps": 0,
                "total_confidence": 0.0,
                "average_confidence": 0.0
            }
        
        metrics = self.agent_registry[agent_id]
        metrics["total_steps"] += 1
        metrics["total_confidence"] += confidence
        metrics["average_confidence"] = (
            metrics["total_confidence"] / metrics["total_steps"]
        )
        
        logger.debug(f"Agent {agent_id} performance: {metrics['average_confidence']:.2f} avg confidence")
    
    async def _track_tool_effectiveness(self, tool: ToolUsage):
        """Track tool effectiveness metrics"""
        if tool.tool_id not in self.tool_metrics:
            self.tool_metrics[tool.tool_id] = {
                "total_uses": 0,
                "successful_uses": 0,
                "total_execution_time": 0.0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0
            }
        
        metrics = self.tool_metrics[tool.tool_id]
        metrics["total_uses"] += 1
        if tool.success:
            metrics["successful_uses"] += 1
        metrics["total_execution_time"] += tool.execution_time
        metrics["success_rate"] = (
            metrics["successful_uses"] / metrics["total_uses"] * 100
        )
        metrics["avg_execution_time"] = (
            metrics["total_execution_time"] / metrics["total_uses"]
        )
        
        logger.debug(
            f"Tool {tool.tool_name} effectiveness: "
            f"{metrics['success_rate']:.1f}% success rate, "
            f"{metrics['avg_execution_time']:.2f}s avg time"
        )
    
    async def _broadcast_enhanced_step(
        self,
        process_id: str,
        step_id: str,
        enhanced_metadata: Dict[str, Any]
    ):
        """Broadcast enhanced step information through WebSocket"""
        await self._broadcast_thinking_event("enhanced_step_added", {
            "process_id": process_id,
            "step_id": step_id,
            "agent": enhanced_metadata.get("agent"),
            "tools": enhanced_metadata.get("tools", []),
            "metrics": enhanced_metadata.get("metrics", {})
        })
    
    async def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all agents"""
        summary = {}
        for agent_id, metrics in self.agent_registry.items():
            summary[agent_id] = {
                "total_steps": metrics["total_steps"],
                "average_confidence": round(metrics["average_confidence"], 2)
            }
        return summary
    
    async def get_tool_effectiveness_summary(self) -> Dict[str, Any]:
        """Get effectiveness summary for all tools"""
        summary = {}
        for tool_id, metrics in self.tool_metrics.items():
            summary[tool_id] = {
                "total_uses": metrics["total_uses"],
                "success_rate": round(metrics["success_rate"], 1),
                "avg_execution_time": round(metrics["avg_execution_time"], 2)
            }
        return summary
    
    async def add_decomposition_step(
        self,
        process_id: str,
        goal_description: str,
        sub_tasks: List[Dict[str, Any]],
        agent_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a goal decomposition thinking step
        
        Args:
            process_id: Active thinking process ID
            goal_description: Goal being decomposed
            sub_tasks: List of sub-tasks created
            agent_info: Agent performing decomposition
            
        Returns:
            Step ID
        """
        
        content = f"Decomposing goal: {goal_description[:100]}..."
        
        # Format sub-tasks for display
        sub_task_summary = [
            {
                "title": task.get("title", ""),
                "priority": task.get("priority", "normal"),
                "estimated_time": task.get("estimated_time", "unknown")
            }
            for task in sub_tasks[:5]  # Show first 5
        ]
        
        return await self.add_thinking_step_with_agent(
            process_id=process_id,
            step_type="decomposition",
            content=content,
            agent_info=agent_info,
            confidence=0.8,
            execution_metrics={
                "sub_tasks_created": len(sub_tasks),
                "sub_task_preview": sub_task_summary
            }
        )
    
    async def add_tool_execution_step(
        self,
        process_id: str,
        tool_name: str,
        tool_input: str,
        tool_output: str,
        execution_time: float,
        success: bool,
        agent_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a tool execution thinking step
        
        Args:
            process_id: Active thinking process ID
            tool_name: Name of tool executed
            tool_input: Tool input summary
            tool_output: Tool output summary
            execution_time: Execution time in seconds
            success: Whether execution succeeded
            agent_info: Agent executing the tool
            
        Returns:
            Step ID
        """
        
        status_emoji = "✅" if success else "❌"
        content = f"{status_emoji} Executed {tool_name}: {tool_input[:100]}..."
        
        tool_usage = [{
            "id": f"tool_{tool_name}",
            "name": tool_name,
            "type": "execution",
            "input_summary": tool_input[:200],
            "output_summary": tool_output[:200],
            "execution_time": execution_time,
            "success": success
        }]
        
        return await self.add_thinking_step_with_agent(
            process_id=process_id,
            step_type="tool_execution",
            content=content,
            agent_info=agent_info,
            tool_usage=tool_usage,
            confidence=0.9 if success else 0.3
        )

# Singleton instance
enhanced_thinking_engine = EnhancedThinkingEngine()