"""
Simple Tool Orchestrator
Provides basic tool orchestration functionality for real data collection
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None

@dataclass
class OrchestrationResult:
    tool_results: List[ToolResult]
    synthesized_data: Dict[str, Any]
    data_quality_score: float
    overall_success: bool
    completion_reasoning: str
    auto_improvements: List[str]

class SimpleToolOrchestrator:
    """Simple tool orchestrator that can execute web searches and other basic tools"""
    
    def __init__(self):
        self.available_tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available tools"""
        try:
            from tools.openai_sdk_tools import WebSearchTool
            self.available_tools["websearch"] = WebSearchTool()
            self.available_tools["web_search"] = WebSearchTool()
            logger.info("✅ Initialized WebSearchTool")
        except ImportError as e:
            logger.warning(f"⚠️ Could not initialize WebSearchTool: {e}")
    
    async def orchestrate_tools_for_task(
        self,
        task_objective: str,
        required_tools: List[str],
        business_context: Dict[str, Any]
    ) -> OrchestrationResult:
        """
        Execute tool orchestration for the given task
        
        Args:
            task_objective: The objective of the task
            required_tools: List of tools required for this task
            business_context: Business context including workspace info
            
        Returns:
            OrchestrationResult with tool execution results
        """
        start_time = asyncio.get_event_loop().time()
        tool_results = []
        synthesized_data = {}
        auto_improvements = []
        
        try:
            logger.info(f"🔧 Starting tool orchestration for: {task_objective}")
            logger.info(f"📋 Required tools: {required_tools}")
            
            # Execute each required tool
            for tool_name in required_tools:
                if tool_name.lower() in ["websearch", "web_search"]:
                    result = await self._execute_web_search(task_objective, business_context)
                    tool_results.append(result)
                    
                    if result.success:
                        synthesized_data[f"{tool_name}_data"] = result.data
                    else:
                        auto_improvements.append(f"Retry {tool_name} with different query")
                else:
                    # Placeholder for other tools
                    logger.info(f"⚠️ Tool {tool_name} not implemented, using placeholder")
                    tool_results.append(ToolResult(
                        tool_name=tool_name,
                        success=False,
                        data={"note": f"Tool {tool_name} not implemented yet"},
                        execution_time=0.1,
                        error_message=f"Tool {tool_name} not available"
                    ))
            
            # Calculate quality score
            successful_tools = [r for r in tool_results if r.success]
            data_quality_score = (len(successful_tools) / len(tool_results)) * 100 if tool_results else 0
            
            # Enhance quality score based on data richness
            if synthesized_data:
                total_data_size = sum(len(str(v)) for v in synthesized_data.values())
                if total_data_size > 1000:  # Rich data
                    data_quality_score = min(95, data_quality_score + 15)
                elif total_data_size > 500:  # Moderate data
                    data_quality_score = min(85, data_quality_score + 10)
            
            overall_success = len(successful_tools) > 0
            execution_time = asyncio.get_event_loop().time() - start_time
            
            completion_reasoning = f"Executed {len(tool_results)} tools, {len(successful_tools)} successful. " \
                                 f"Data quality: {data_quality_score:.1f}%. " \
                                 f"Total data collected: {len(synthesized_data)} sources."
            
            logger.info(f"✅ Tool orchestration complete: {completion_reasoning}")
            
            return OrchestrationResult(
                tool_results=tool_results,
                synthesized_data=synthesized_data,
                data_quality_score=data_quality_score,
                overall_success=overall_success,
                completion_reasoning=completion_reasoning,
                auto_improvements=auto_improvements
            )
            
        except Exception as e:
            logger.error(f"❌ Tool orchestration failed: {e}")
            return OrchestrationResult(
                tool_results=tool_results,
                synthesized_data={},
                data_quality_score=0,
                overall_success=False,
                completion_reasoning=f"Orchestration failed: {str(e)}",
                auto_improvements=[f"Fix orchestration error: {str(e)}"]
            )
    
    async def _execute_web_search(self, task_objective: str, business_context: Dict[str, Any]) -> ToolResult:
        """Execute web search for the given task"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            web_tool = self.available_tools.get("websearch")
            if not web_tool:
                return ToolResult(
                    tool_name="websearch",
                    success=False,
                    data={},
                    execution_time=0,
                    error_message="WebSearchTool not available"
                )
            
            # Create search query based on task objective and business context
            search_query = self._create_search_query(task_objective, business_context)
            logger.info(f"🔍 Executing web search with query: {search_query}")
            
            # Execute the search
            search_result = await web_tool.execute(search_query, business_context)
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Process and structure the result
            processed_data = {
                "query": search_query,
                "raw_result": search_result,
                "data_source": "web_search",
                "search_timestamp": asyncio.get_event_loop().time(),
                "result_quality": "high" if len(search_result) > 500 else "medium" if len(search_result) > 100 else "low"
            }
            
            logger.info(f"✅ Web search completed: {len(search_result)} characters of data")
            
            return ToolResult(
                tool_name="websearch",
                success=True,
                data=processed_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Web search failed: {e}")
            return ToolResult(
                tool_name="websearch",
                success=False,
                data={},
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _create_search_query(self, task_objective: str, business_context: Dict[str, Any]) -> str:
        """Create an effective search query based on task and context"""
        
        # Extract business domain if available
        workspace_goal = business_context.get("workspace_goal", "")
        workspace_name = business_context.get("workspace_name", "")
        
        # Build query components
        query_parts = []
        
        # Add main task objective
        if "contact" in task_objective.lower() or "lead" in task_objective.lower():
            query_parts.append("lead generation contact database")
        elif "email" in task_objective.lower():
            query_parts.append("email marketing campaigns templates")
        elif "content" in task_objective.lower():
            query_parts.append("content marketing strategy examples")
        else:
            # Use the task objective directly but clean it up
            clean_objective = task_objective.replace("🎯", "").replace("🤖", "").strip()
            query_parts.append(clean_objective)
        
        # Add business context
        if workspace_goal:
            # Extract business domain keywords
            domain_keywords = self._extract_domain_keywords(workspace_goal)
            if domain_keywords:
                query_parts.extend(domain_keywords[:2])  # Add top 2 keywords
        
        # Add current year for recent results
        query_parts.append("2024")
        
        return " ".join(query_parts)
    
    def _extract_domain_keywords(self, text: str) -> List[str]:
        """Extract relevant business domain keywords from text"""
        keywords = []
        text_lower = text.lower()
        
        # Business domains
        if "saas" in text_lower or "software" in text_lower:
            keywords.append("SaaS")
        if "ecommerce" in text_lower or "e-commerce" in text_lower:
            keywords.append("ecommerce")
        if "marketing" in text_lower:
            keywords.append("digital marketing")
        if "fintech" in text_lower or "finance" in text_lower:
            keywords.append("fintech")
        if "health" in text_lower or "medical" in text_lower:
            keywords.append("healthcare")
        if "education" in text_lower or "learning" in text_lower:
            keywords.append("edtech")
        
        return keywords

# Create singleton instance
simple_tool_orchestrator = SimpleToolOrchestrator()

# Export for easy import
__all__ = ["SimpleToolOrchestrator", "simple_tool_orchestrator", "ToolResult", "OrchestrationResult"]