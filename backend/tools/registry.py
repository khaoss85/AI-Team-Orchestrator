import logging
import inspect
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable
from uuid import UUID
import importlib.util
import sys
import ast

from ai_agents.tools import function_tool 

logger = logging.getLogger(__name__)

class ToolValidationError(Exception):
    """Error raised when a tool fails validation"""
    pass

class ToolRegistry:
    """Registry for managing dynamic tools created by agents or users"""
    
    def __init__(self):
        self.tools_cache = {}
        self.initialized = False
    
    async def initialize(self, db_client=None):
        """Initialize the registry, loading tools from database"""
        if self.initialized:
            return
            
        self.db_client = db_client
        
        # Load tools from database if a client is provided
        if db_client:
            await self.load_tools_from_db()
        
        self.initialized = True
        logger.info("Tool registry initialized")
    
    async def load_tools_from_db(self):
        """Load all tools from the database"""
        try:
            # In a real implementation, this would query a database
            # For now, we'll just use a placeholder
            logger.info("Loading tools from database")
            
            # Placeholder: In reality we'd load from the database
            example_tools = [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "analyze_instagram_hashtags",
                    "description": "Analyze Instagram hashtags for popularity and relevance",
                    "workspace_id": "00000000-0000-0000-0000-000000000000",
                    "created_by": "user",  # or "agent"
                    "code": """
async def analyze_instagram_hashtags(hashtags: List[str]) -> Dict[str, Any]:
    \"\"\"
    Analyze Instagram hashtags for popularity and relevance.
    
    Args:
        hashtags: List of hashtags to analyze (without # symbol)
    
    Returns:
        Dictionary with analysis results
    \"\"\"
    # Placeholder implementation
    results = {}
    for hashtag in hashtags:
        results[hashtag] = {
            "popularity": 0.7,  # Placeholder score
            "posts_count": 10000,
            "related_tags": ["tag1", "tag2", "tag3"],
            "trending": True
        }
    return results
                    """
                }
            ]
            
            # Create function tools from the loaded data
            for tool_data in example_tools:
                await self.register_tool(
                    tool_data["name"],
                    tool_data["description"],
                    tool_data["code"],
                    tool_data["workspace_id"],
                    tool_data["created_by"]
                )
        except Exception as e:
            logger.error(f"Failed to load tools from database: {e}")
    
    async def register_tool(self, name: str, description: str, code: str, 
                           workspace_id: str, created_by: str) -> Dict[str, Any]:
        """
        Register a new tool with its implementation.
        
        Args:
            name: The name of the tool
            description: Tool description
            code: Python code implementing the tool
            workspace_id: The workspace this tool belongs to
            created_by: Who created the tool ("user" or "agent")
            
        Returns:
            Dictionary with tool information
        """
        try:
            # Validate the code
            if not self._validate_code(code):
                raise ToolValidationError("Code validation failed")
                
            # Create a module for the tool
            tool_func = self._compile_tool_code(name, code)
            
            if not tool_func:
                raise ToolValidationError("Failed to compile tool code")
                
            # Wrap the function with OpenAI's function_tool decorator
            wrapped_tool = function_tool(tool_func)
            
            # Store in cache
            tool_info = {
                "name": name,
                "description": description,
                "code": code,
                "workspace_id": workspace_id,
                "created_by": created_by,
                "function": wrapped_tool
            }
            
            self.tools_cache[name] = tool_info
            
            # In a real implementation, save to database
            logger.info(f"Registered tool: {name}")
            
            return {
                "name": name,
                "description": description,
                "workspace_id": workspace_id,
                "created_by": created_by
            }
        except Exception as e:
            logger.error(f"Failed to register tool '{name}': {e}")
            raise
    
    async def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            The tool function, or None if not found
        """
        if name in self.tools_cache:
            return self.tools_cache[name]["function"]
        return None
    
    async def get_tools_for_workspace(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all tools for a workspace.
        
        Args:
            workspace_id: The workspace ID
            
        Returns:
            List of tool information
        """
        result = []
        for name, tool_info in self.tools_cache.items():
            if tool_info["workspace_id"] == workspace_id:
                result.append({
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "created_by": tool_info["created_by"]
                })
        return result
    
    async def delete_tool(self, name: str) -> bool:
        """
        Delete a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            Boolean indicating success
        """
        if name in self.tools_cache:
            del self.tools_cache[name]
            # In a real implementation, delete from database
            logger.info(f"Deleted tool: {name}")
            return True
        return False
    
    def _validate_code(self, code: str) -> bool:
        """
        Validate tool code for security and correctness.
        
        Args:
            code: The Python code to validate
            
        Returns:
            Boolean indicating validity
        """
        try:
            # Parse the AST to check for forbidden operations
            tree = ast.parse(code)
            
            # Check for imports that could be dangerous
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    # Check if importing dangerous modules
                    for name in node.names:
                        if name.name in ['os', 'sys', 'subprocess', 'eval']:
                            logger.warning(f"Attempt to import dangerous module: {name.name}")
                            return False
                
                # Check for dangerous functions
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                            logger.warning(f"Attempt to call dangerous function: {node.func.id}")
                            return False
            
            # Compile to check for syntax errors
            compile(code, '<string>', 'exec')
            
            return True
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return False
    
    def _compile_tool_code(self, name: str, code: str) -> Optional[Callable]:
        """
        Compile tool code into a callable function.
        
        Args:
            name: The name of the tool
            code: The Python code implementing the tool
            
        Returns:
            Callable function object, or None if compilation failed
        """
        try:
            # Create a module for the tool
            spec = importlib.util.spec_from_loader(
                f"dynamic_tool_{name}",
                loader=None
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            
            # Execute the code in the module's namespace
            exec(code, module.__dict__)
            
            # Get the function from the module
            # We assume the function name matches the last part of the name
            func_name = name.split('.')[-1]
            if func_name in module.__dict__ and callable(module.__dict__[func_name]):
                return module.__dict__[func_name]
            else:
                for key, value in module.__dict__.items():
                    if callable(value) and not key.startswith('_'):
                        return value
                        
            logger.error(f"No callable function found in tool code: {name}")
            return None
        except Exception as e:
            logger.error(f"Failed to compile tool code: {e}")
            return None

# Create a singleton instance
tool_registry = ToolRegistry()