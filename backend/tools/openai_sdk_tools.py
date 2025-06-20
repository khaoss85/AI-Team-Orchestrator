"""
OpenAI SDK Tools Integration - PRODUCTION VERSION
Provides actual OpenAI tools integration to all agents in the system
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class WebSearchTool:
    """PRODUCTION: Real web search using DuckDuckGo API (free alternative)"""
    name: str = "web_search"
    description: str = "Search the web for information"
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute real web search using DuckDuckGo Instant Answer API"""
        try:
            # DuckDuckGo Instant Answer API (free, no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract useful information
            result_parts = []
            
            if data.get("Abstract"):
                result_parts.append(f"Summary: {data['Abstract']}")
            
            if data.get("Definition"):
                result_parts.append(f"Definition: {data['Definition']}")
            
            # Add related topics
            if data.get("RelatedTopics"):
                topics = [topic.get("Text", "") for topic in data["RelatedTopics"][:3] if topic.get("Text")]
                if topics:
                    result_parts.append(f"Related: {'; '.join(topics)}")
            
            if result_parts:
                return "\n".join(result_parts)
            else:
                return f"No immediate results found for '{query}'. You may want to search more specifically."
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search temporarily unavailable. Error: {str(e)}"

@dataclass  
class CodeInterpreterTool:
    """PRODUCTION: Safe Python code execution with restricted environment"""
    name: str = "code_interpreter"
    description: str = "Execute Python code in a sandboxed environment"
    
    async def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute Python code safely with restricted built-ins"""
        try:
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            # Security: Restricted builtins
            safe_builtins = {
                'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
                'chr': chr, 'dict': dict, 'enumerate': enumerate, 'filter': filter,
                'float': float, 'format': format, 'hex': hex, 'int': int,
                'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
                'ord': ord, 'pow': pow, 'range': range, 'reversed': reversed,
                'round': round, 'set': set, 'sorted': sorted, 'str': str,
                'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip,
                'print': print
            }
            
            # Allowed modules
            safe_globals = {
                '__builtins__': safe_builtins,
                'math': __import__('math'),
                'datetime': __import__('datetime'),
                'json': __import__('json')
            }
            
            # Capture output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute code with restricted environment
                exec(code, safe_globals)
            
            stdout_result = stdout_capture.getvalue()
            stderr_result = stderr_capture.getvalue()
            
            result_parts = []
            if stdout_result:
                result_parts.append(f"Output:\n{stdout_result}")
            if stderr_result:
                result_parts.append(f"Errors:\n{stderr_result}")
            
            return "\n".join(result_parts) if result_parts else "Code executed successfully (no output)"
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return f"Code execution error: {str(e)}"

@dataclass
class ImageGenerationTool:
    """PRODUCTION: Real image generation using OpenAI DALL-E"""
    name: str = "generate_image"
    description: str = "Generate images from text descriptions"
    
    def __init__(self):
        try:
            self.openai_client = OpenAI()
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
            self.openai_client = None
    
    async def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate image using OpenAI DALL-E"""
        if not self.openai_client:
            return "Image generation unavailable: OpenAI API key not configured"
        
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return f"✅ Image generated successfully!\n\nURL: {image_url}\n\nRevised prompt: {revised_prompt}"
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return f"Image generation error: {str(e)}. Please ensure OpenAI API key is configured."

@dataclass
class FileSearchTool:
    """PRODUCTION: File search through workspace documents using OpenAI vector search"""
    name: str = "file_search"
    description: str = "Search through uploaded files and documents using AI-powered vector search"
    vector_store_ids: List[str] = None
    max_num_results: Optional[int] = None
    include_search_results: bool = False
    
    def __init__(self, vector_store_ids: Optional[List[str]] = None, max_num_results: Optional[int] = None, include_search_results: bool = False):
        self.vector_store_ids = vector_store_ids or []
        self.max_num_results = max_num_results
        self.include_search_results = include_search_results
        
        # Initialize OpenAI client with Beta headers for Vector Stores
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(
                default_headers={"OpenAI-Beta": "assistants=v2"}
            )
        except Exception as e:
            logger.warning(f"OpenAI client not available for file search: {e}")
            self.openai_client = None
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Search through workspace documents using OpenAI vector search"""
        try:
            workspace_id = context.get("workspace_id") if context else None
            if not workspace_id:
                return "Error: workspace_id required for file search"
            
            # If no vector store IDs provided, get them from document manager
            if not self.vector_store_ids:
                try:
                    from services.document_manager import document_manager
                    agent_id = context.get("agent_id") if context else None
                    self.vector_store_ids = await document_manager.get_vector_store_ids_for_agent(
                        workspace_id, agent_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to get vector store IDs: {e}")
                    return await self._fallback_search(query, workspace_id)
            
            # Use OpenAI vector search API directly
            if self.openai_client and self.vector_store_ids:
                try:
                    search_results = []
                    
                    # Search each vector store
                    for vector_store_id in self.vector_store_ids[:5]:  # Limit to 5 stores
                        try:
                            # Use the vector store search endpoint directly
                            response = self.openai_client.beta.vector_stores.search(
                                vector_store_id=vector_store_id,
                                query=query,
                                max_num_results=self.max_num_results or 10
                            )
                            
                            if response.data:
                                for result in response.data[:3]:  # Top 3 results per store
                                    search_results.append({
                                        "file_id": result.file_id,
                                        "filename": result.filename,
                                        "score": result.score,
                                        "content": result.content[0].text if result.content else ""
                                    })
                                    
                        except Exception as e:
                            logger.error(f"Failed to search vector store {vector_store_id}: {e}")
                            continue
                    
                    if search_results:
                        # Format results
                        formatted_results = []
                        formatted_results.append(f"🔍 **Vector Search Results for**: \"{query}\"\n")
                        
                        for i, result in enumerate(search_results[:self.max_num_results or 10], 1):
                            formatted_results.append(f"{i}. **{result['filename']}** (Score: {result['score']:.2f})")
                            if result['content']:
                                preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                                formatted_results.append(f"   📄 {preview}")
                            formatted_results.append("")
                        
                        return "\n".join(formatted_results)
                    
                except Exception as e:
                    logger.error(f"OpenAI vector search failed: {e}")
                    return await self._fallback_search(query, workspace_id)
            
            # Fallback to database search
            return await self._fallback_search(query, workspace_id)
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return f"File search error: {str(e)}"
    
    async def _fallback_search(self, query: str, workspace_id: str) -> str:
        """Fallback search using database queries"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Search in uploaded documents
            documents = supabase.table("workspace_documents")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .or_(f"filename.ilike.%{query}%,description.ilike.%{query}%")\
                .execute()
            
            # Search in deliverables
            deliverables = supabase.table("project_deliverables")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .ilike("content", f"%{query}%")\
                .execute()
            
            # Search in assets
            assets = supabase.table("project_assets")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .or_(f"name.ilike.%{query}%,description.ilike.%{query}%")\
                .execute()
            
            # Format results
            results = []
            
            if documents.data:
                results.append(f"📄 Documents ({len(documents.data)} found):")
                for doc in documents.data[:5]:  # Limit to 5 results
                    results.append(f"  • {doc['filename']} - {doc.get('description', 'No description')}")
            
            if deliverables.data:
                results.append(f"📋 Deliverables ({len(deliverables.data)} found):")
                for d in deliverables.data[:3]:  # Limit to top 3
                    content_preview = d.get("content", "")[:100] + "..." if d.get("content") else ""
                    results.append(f"  • {d.get('title', 'Untitled')}: {content_preview}")
            
            if assets.data:
                results.append(f"\n📦 Assets ({len(assets.data)} found):")
                for a in assets.data[:3]:  # Limit to top 3
                    results.append(f"  • {a.get('name', 'Unnamed')} ({a.get('asset_type', 'unknown type')})")
            
            if context_data.data:
                results.append(f"\n🔍 Context Data ({len(context_data.data)} found):")
                for c in context_data.data[:2]:  # Limit to top 2
                    results.append(f"  • {c.get('context_key', 'Unknown key')}")
            
            if results:
                return "\n".join(results)
            else:
                return f"No files or documents found matching '{query}' in this workspace."
                
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return f"File search error: {str(e)}"


class OpenAISDKToolsManager:
    """
    PRODUCTION Manager for OpenAI SDK tools that can be shared across all agents
    """
    
    def __init__(self):
        self.web_search = WebSearchTool()
        self.code_interpreter = CodeInterpreterTool()
        self.image_generation = ImageGenerationTool()
        self.file_search = FileSearchTool()
        
    def get_all_tools(self) -> List[Any]:
        """Get all available OpenAI SDK tools"""
        return [
            self.web_search,
            self.code_interpreter,
            self.image_generation,
            self.file_search
        ]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools for AI context"""
        return {
            "web_search": "Search the web for current information",
            "code_interpreter": "Execute Python code for calculations and data processing",
            "generate_image": "Create images from text descriptions",
            "file_search": "Search through workspace documents and files"
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific tool with parameters and context"""
        try:
            if tool_name == "web_search":
                query = parameters.get("query", "")
                result = await self.web_search.execute(query, context)
                return {"success": True, "result": result}
                
            elif tool_name == "code_interpreter":
                code = parameters.get("code", "")
                result = await self.code_interpreter.execute(code, context)
                return {"success": True, "result": result}
                
            elif tool_name == "generate_image":
                prompt = parameters.get("prompt", "")
                result = await self.image_generation.execute(prompt, context)
                return {"success": True, "result": result}
                
            elif tool_name == "file_search":
                query = parameters.get("query", "")
                result = await self.file_search.execute(query, context)
                return {"success": True, "result": result}
                
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}


# Global instance
openai_tools_manager = OpenAISDKToolsManager()