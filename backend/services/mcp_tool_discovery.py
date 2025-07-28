"""
🔧 MCP Tool Discovery Engine - Phase 3.2 Implementation

Model Context Protocol (MCP) integration for dynamic tool discovery and registration.
Aligns with OpenAI Agents SDK for seamless tool integration.

This module provides:
- Dynamic tool discovery from MCP servers
- Automatic tool registration with SDK agents
- Cross-domain tool compatibility
- Real-time tool availability monitoring
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Represents a tool discovered via MCP"""
    name: str
    description: str
    schema: Dict[str, Any]
    endpoint: str
    capabilities: List[str]
    domain: str
    priority: int = 5
    last_health_check: Optional[datetime] = None
    is_available: bool = True
    usage_stats: Dict[str, int] = field(default_factory=dict)

@dataclass
class MCPServer:
    """Represents an MCP server providing tools"""
    server_id: str
    endpoint: str
    capabilities: List[str]
    tools: List[MCPTool] = field(default_factory=list)
    is_online: bool = True
    last_ping: Optional[datetime] = None

class MCPToolDiscoveryEngine:
    """
    🧠 AI-Driven MCP Tool Discovery Engine
    
    Dynamically discovers and registers tools from MCP servers,
    providing seamless integration with SDK agents.
    """
    
    def __init__(self):
        self.discovered_tools: Dict[str, MCPTool] = {}
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.tool_registry_callbacks: List[Callable] = []
        self.discovery_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self.is_running = False
        
        # AI-driven tool categorization
        self.domain_categories = {
            'web_search': ['search', 'web', 'information', 'research'],
            'file_management': ['file', 'document', 'storage', 'filesystem'],
            'data_analysis': ['data', 'analysis', 'visualization', 'statistics'],
            'communication': ['email', 'messaging', 'notification', 'communication'],
            'development': ['code', 'git', 'deployment', 'testing'],
            'business': ['crm', 'finance', 'accounting', 'business']
        }
        
        logger.info("🔧 MCP Tool Discovery Engine initialized")
    
    async def start_discovery(self):
        """Start the MCP tool discovery process"""
        if self.is_running:
            logger.warning("MCP discovery already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting MCP tool discovery...")
        
        # Start discovery and health check tasks
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._health_check_loop())
        
        # Initial discovery
        await self._discover_available_servers()
        await self._discover_tools_from_servers()
        
        logger.info(f"✅ MCP discovery started with {len(self.discovered_tools)} tools")
    
    async def stop_discovery(self):
        """Stop the MCP tool discovery process"""
        self.is_running = False
        logger.info("🛑 MCP tool discovery stopped")
    
    async def register_mcp_server(self, server_id: str, endpoint: str, capabilities: List[str] = None):
        """Register a new MCP server for tool discovery"""
        try:
            server = MCPServer(
                server_id=server_id,
                endpoint=endpoint,
                capabilities=capabilities or [],
                is_online=False
            )
            
            # Test server connectivity
            is_online = await self._ping_server(server)
            server.is_online = is_online
            server.last_ping = datetime.now()
            
            self.mcp_servers[server_id] = server
            
            if is_online:
                # Discover tools from this server
                await self._discover_tools_from_server(server)
                logger.info(f"✅ MCP server '{server_id}' registered and {len(server.tools)} tools discovered")
            else:
                logger.warning(f"⚠️ MCP server '{server_id}' registered but is offline")
                
        except Exception as e:
            logger.error(f"Failed to register MCP server '{server_id}': {e}")
    
    async def get_tools_for_domain(self, domain: str, agent_context: Dict[str, Any] = None) -> List[MCPTool]:
        """
        🧠 AI-driven tool discovery for specific domain and agent context
        """
        try:
            relevant_tools = []
            
            # Find tools by domain category
            domain_keywords = self.domain_categories.get(domain, [domain])
            
            for tool in self.discovered_tools.values():
                if not tool.is_available:
                    continue
                    
                # Check domain compatibility
                tool_domain_match = any(
                    keyword in tool.description.lower() or 
                    keyword in tool.domain.lower() or
                    keyword in tool.name.lower()
                    for keyword in domain_keywords
                )
                
                if tool_domain_match:
                    relevant_tools.append(tool)
            
            # AI-driven tool prioritization based on agent context
            if agent_context:
                relevant_tools = await self._prioritize_tools_for_agent(relevant_tools, agent_context)
            
            # Sort by priority and usage stats
            relevant_tools.sort(key=lambda t: (t.priority, t.usage_stats.get('success_rate', 0)), reverse=True)
            
            logger.info(f"🔧 Found {len(relevant_tools)} tools for domain '{domain}'")
            return relevant_tools
            
        except Exception as e:
            logger.error(f"Failed to get tools for domain '{domain}': {e}")
            return []
    
    async def get_sdk_compatible_tools(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Convert MCP tools to SDK-compatible tool definitions"""
        try:
            sdk_tools = []
            
            for tool in tools:
                sdk_tool = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.schema.get('parameters', {}),
                    "mcp_endpoint": tool.endpoint,
                    "capabilities": tool.capabilities,
                    "domain": tool.domain,
                    "priority": tool.priority
                }
                
                # Add MCP-specific metadata for tool execution
                sdk_tool["mcp_metadata"] = {
                    "server_endpoint": tool.endpoint,
                    "tool_schema": tool.schema,
                    "last_health_check": tool.last_health_check.isoformat() if tool.last_health_check else None
                }
                
                sdk_tools.append(sdk_tool)
            
            logger.info(f"🔧 Converted {len(sdk_tools)} tools to SDK format")
            return sdk_tools
            
        except Exception as e:
            logger.error(f"Failed to convert tools to SDK format: {e}")
            return []
    
    async def register_tool_callback(self, callback: Callable):
        """Register a callback for when new tools are discovered"""
        self.tool_registry_callbacks.append(callback)
        logger.info("📋 Tool registry callback registered")
    
    async def _discover_available_servers(self):
        """Discover available MCP servers in the environment"""
        try:
            # In a real implementation, this would:
            # 1. Check environment variables for MCP server endpoints
            # 2. Scan known MCP registry services
            # 3. Query service discovery mechanisms
            
            # For now, register some common tool servers
            common_servers = [
                {
                    "server_id": "web_search_mcp",
                    "endpoint": "http://localhost:8001/mcp",
                    "capabilities": ["web_search", "information_retrieval"]
                },
                {
                    "server_id": "file_tools_mcp", 
                    "endpoint": "http://localhost:8002/mcp",
                    "capabilities": ["file_management", "document_processing"]
                }
            ]
            
            for server_config in common_servers:
                await self.register_mcp_server(**server_config)
                
        except Exception as e:
            logger.error(f"Failed to discover MCP servers: {e}")
    
    async def _discover_tools_from_servers(self):
        """Discover tools from all registered MCP servers"""
        for server in self.mcp_servers.values():
            if server.is_online:
                await self._discover_tools_from_server(server)
    
    async def _discover_tools_from_server(self, server: MCPServer):
        """Discover tools from a specific MCP server"""
        try:
            # In a real implementation, this would make HTTP requests to the MCP server
            # For now, simulate tool discovery
            
            mock_tools = [
                MCPTool(
                    name=f"advanced_web_search_{server.server_id}",
                    description="Advanced web search with domain filtering and AI summarization",
                    schema={
                        "parameters": {
                            "query": {"type": "string", "description": "Search query"},
                            "domain_filter": {"type": "string", "description": "Optional domain filter"}
                        }
                    },
                    endpoint=server.endpoint,
                    capabilities=["search", "summarization"],
                    domain="web_search",
                    priority=8
                ),
                MCPTool(
                    name=f"intelligent_file_processor_{server.server_id}",
                    description="AI-powered file processing and analysis",
                    schema={
                        "parameters": {
                            "file_path": {"type": "string", "description": "Path to file"},
                            "analysis_type": {"type": "string", "description": "Type of analysis to perform"}
                        }
                    },
                    endpoint=server.endpoint,
                    capabilities=["file_analysis", "content_extraction"],
                    domain="file_management",
                    priority=7
                )
            ]
            
            for tool in mock_tools:
                tool.last_health_check = datetime.now()
                server.tools.append(tool)
                self.discovered_tools[tool.name] = tool
            
            logger.info(f"🔧 Discovered {len(mock_tools)} tools from server '{server.server_id}'")
            
            # Notify callbacks about new tools
            for callback in self.tool_registry_callbacks:
                try:
                    await callback(mock_tools)
                except Exception as e:
                    logger.error(f"Tool registry callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to discover tools from server '{server.server_id}': {e}")
    
    async def _ping_server(self, server: MCPServer) -> bool:
        """Check if an MCP server is online"""
        try:
            # In a real implementation, this would make an HTTP ping to the server
            # For now, simulate server availability
            return True
        except Exception as e:
            logger.error(f"Failed to ping server '{server.server_id}': {e}")
            return False
    
    async def _prioritize_tools_for_agent(self, tools: List[MCPTool], agent_context: Dict[str, Any]) -> List[MCPTool]:
        """AI-driven tool prioritization based on agent context"""
        try:
            agent_role = agent_context.get('role', 'general')
            agent_skills = agent_context.get('skills', [])
            
            # AI-driven priority boost based on agent compatibility
            for tool in tools:
                # Boost priority for tools matching agent skills
                skill_match = any(
                    skill.lower() in tool.description.lower() or
                    skill.lower() in tool.name.lower()
                    for skill in agent_skills
                )
                
                if skill_match:
                    tool.priority += 2
                
                # Role-specific boosts
                if agent_role.lower() in ['developer', 'lead developer'] and 'development' in tool.domain:
                    tool.priority += 3
                elif agent_role.lower() in ['data analyst', 'analyst'] and 'analysis' in tool.domain:
                    tool.priority += 3
                elif agent_role.lower() in ['project manager', 'manager'] and 'business' in tool.domain:
                    tool.priority += 2
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to prioritize tools for agent: {e}")
            return tools
    
    async def _discovery_loop(self):
        """Continuous tool discovery loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.discovery_interval)
                await self._discover_tools_from_servers()
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
    
    async def _health_check_loop(self):
        """Continuous health check loop for servers and tools"""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all servers and tools"""
        for server in self.mcp_servers.values():
            is_online = await self._ping_server(server)
            server.is_online = is_online
            server.last_ping = datetime.now()
            
            # Update tool availability based on server status
            for tool in server.tools:
                tool.is_available = is_online
                if is_online:
                    tool.last_health_check = datetime.now()

# Global instance
mcp_tool_discovery = MCPToolDiscoveryEngine()

# Integration with specialist agents
async def get_mcp_tools_for_agent(agent_data, domain: str = None) -> List[Dict[str, Any]]:
    """
    Helper function to get MCP tools for a specific agent
    Integrates with specialist_enhanced.py
    """
    try:
        # Determine domain from agent role if not specified
        if not domain:
            role = agent_data.role.lower()
            if 'developer' in role or 'engineer' in role:
                domain = 'development'
            elif 'analyst' in role or 'data' in role:
                domain = 'data_analysis'
            elif 'designer' in role or 'ui' in role:
                domain = 'design'
            elif 'manager' in role or 'project' in role:
                domain = 'business'
            else:
                domain = 'web_search'  # Default
        
        # Get agent context
        agent_context = {
            'role': agent_data.role,
            'seniority': agent_data.seniority,
            'skills': getattr(agent_data, 'hard_skills', [])
        }
        
        # Discover relevant tools
        mcp_tools = await mcp_tool_discovery.get_tools_for_domain(domain, agent_context)
        
        # Convert to SDK format
        sdk_tools = await mcp_tool_discovery.get_sdk_compatible_tools(mcp_tools)
        
        logger.info(f"🔧 Retrieved {len(sdk_tools)} MCP tools for agent '{agent_data.name}' in domain '{domain}'")
        return sdk_tools
        
    except Exception as e:
        logger.error(f"Failed to get MCP tools for agent: {e}")
        return []