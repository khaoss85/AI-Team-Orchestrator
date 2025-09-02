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
            search_query = await self._create_search_query(task_objective, business_context)
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
    
    async def _create_search_query(self, task_objective: str, business_context: Dict[str, Any]) -> str:
        """Create an effective search query based on task and context"""
        
        # Extract business domain if available
        workspace_goal = business_context.get("workspace_goal", "")
        workspace_name = business_context.get("workspace_name", "")
        
        # Build query components
        query_parts = []
        
        # 🤖 AI-DRIVEN: Generate semantic search query based on task understanding
        try:
            semantic_query = await self._generate_semantic_query_ai(task_objective, business_context)
            if semantic_query:
                query_parts.append(semantic_query)
            else:
                # Fallback: Clean task objective without keyword-based logic
                clean_objective = task_objective.replace("🎯", "").replace("🤖", "").strip()
                query_parts.append(clean_objective)
        except Exception as e:
            logger.warning(f"AI semantic query generation failed: {e}")
            # Fallback: Clean task objective without keyword-based logic  
            clean_objective = task_objective.replace("🎯", "").replace("🤖", "").strip()
            query_parts.append(clean_objective)
        
        # 🤖 AI-DRIVEN: Add semantic business context  
        if workspace_goal:
            try:
                domain_context = await self._extract_domain_context_ai(workspace_goal)
                if domain_context:
                    query_parts.extend(domain_context[:2])  # Add top 2 semantic terms
            except Exception as e:
                logger.warning(f"AI domain context extraction failed: {e}")
                # Fallback: Use goal directly without keyword matching
                clean_goal = workspace_goal.replace("🎯", "").replace("🤖", "").strip()[:50]
                query_parts.append(clean_goal)
        
        # Add current year for recent results
        query_parts.append("2024")
        
        return " ".join(query_parts)
    
    async def _generate_semantic_query_ai(self, task_objective: str, business_context: Dict[str, Any]) -> str:
        """🤖 AI-DRIVEN: Generate semantic search query based on task understanding"""
        from services.ai_provider_abstraction import ai_provider_manager
        
        # 🤖 SELF-CONTAINED: Create query generator config internally
        QUERY_GENERATOR_CONFIG = {
            "name": "SemanticQueryGenerator", 
            "instructions": """
                You are a semantic search query specialist.
                Generate optimized search terms for finding relevant business information.
                Focus on intent rather than keywords. Return only the search terms.
            """,
            "model": "gpt-4o-mini"
        }
        
        prompt = f"""Generate semantic search terms for this business task:

TASK: {task_objective}
CONTEXT: {business_context.get('workspace_goal', '')}

Return 3-5 search terms that capture the intent and domain, not just keywords.
Example: Instead of 'contact lead' return 'customer acquisition strategies'

Search terms:"""
        
        try:
            result = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=QUERY_GENERATOR_CONFIG,
                prompt=prompt
            )
            
            return result.get('content', '').strip() if result else None
        except Exception as e:
            logger.warning(f"AI semantic query generation error: {e}")
            return None
    
    async def _extract_domain_context_ai(self, workspace_goal: str) -> List[str]:
        """🤖 AI-DRIVEN: Extract domain-specific context terms using semantic understanding"""
        from services.ai_provider_abstraction import ai_provider_manager
        
        # 🤖 SELF-CONTAINED: Create domain extractor config internally
        DOMAIN_EXTRACTOR_CONFIG = {
            "name": "DomainContextExtractor",
            "instructions": """
                You are a business domain specialist.
                Extract 2-3 domain-specific search terms that enhance search relevance.
                Focus on industry context and business domain, not generic keywords.
            """,
            "model": "gpt-4o-mini"
        }
        
        prompt = f"""Extract domain context terms for this business goal:

GOAL: {workspace_goal}

Return 2-3 industry/domain terms that provide search context.
Example: For 'Build learning platform' return ['educational technology', 'e-learning solutions']

Domain terms:"""
        
        try:
            result = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=DOMAIN_EXTRACTOR_CONFIG,
                prompt=prompt
            )
            
            content = result.get('content', '') if result else ''
            # Simple parsing - split on common delimiters
            terms = []
            for line in content.split('\n'):
                if line.strip() and not line.startswith(('Example:', 'Domain:', 'Terms:')):
                    # Clean and extract terms
                    clean_line = line.strip().strip('•-').strip('[]"\'')
                    if clean_line and len(clean_line) > 3:
                        terms.append(clean_line)
            
            return terms[:3]  # Max 3 terms
        except Exception as e:
            logger.warning(f"AI domain context extraction error: {e}")
            return []

# Create singleton instance
simple_tool_orchestrator = SimpleToolOrchestrator()

# Export for easy import
__all__ = ["SimpleToolOrchestrator", "simple_tool_orchestrator", "ToolResult", "OrchestrationResult"]