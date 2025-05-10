import logging
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from agents import Agent as OpenAIAgent
from agents import ModelSettings

from models import Agent as AgentModel, AgentSeniority
from ai_agents.specialist import SpecialistAgent
from tools import tool_registry
from tools.social_media import InstagramTools

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agent instances based on role and configuration"""
    
    @staticmethod
    async def create_agent(agent_data: AgentModel) -> SpecialistAgent:
        """
        Create a specialist agent instance based on agent data.
        
        Args:
            agent_data: Agent configuration from the database
            
        Returns:
            SpecialistAgent instance
        """
        return SpecialistAgent(agent_data)
    
    @staticmethod
    async def get_tools_for_role(role: str, workspace_id: str) -> List[Any]:
        """
        Get the appropriate tools for a given role, including custom tools from the registry.
        
        Args:
            role: The agent's role
            workspace_id: The workspace ID to get custom tools for
            
        Returns:
            List of tool functions
        """
        # Common tools for all agents
        tools = [
            # Core tools from CommonTools class would go here
        ]
        
        # Add role-specific tools
        role_lower = role.lower()
        
        # Add instagram-specific tools if role is related to social media
        if 'social' in role_lower or 'media' in role_lower or 'instagram' in role_lower:
            tools.extend([
                InstagramTools.analyze_hashtags,
                InstagramTools.analyze_account,
                InstagramTools.generate_content_ideas,
                InstagramTools.analyze_competitors
            ])
        
        # Add custom tools from registry
        custom_tools = await tool_registry.get_tools_for_workspace(workspace_id)
        for tool_info in custom_tools:
            tool_func = await tool_registry.get_tool(tool_info["name"])
            if tool_func:
                tools.append(tool_func)
        
        return tools
    
    @staticmethod
    def get_model_for_seniority(seniority: AgentSeniority) -> str:
        """
        Get the appropriate model for a given seniority level.
        
        Args:
            seniority: The agent's seniority
            
        Returns:
            Model name
        """
        seniority_model_map = {
            AgentSeniority.JUNIOR: "gpt-3.5-turbo",
            AgentSeniority.SENIOR: "gpt-4",
            AgentSeniority.EXPERT: "gpt-4-turbo"
        }
        
        return seniority_model_map.get(seniority, "gpt-4")
    
    @staticmethod
    def generate_system_prompt(agent_data: AgentModel) -> str:
        """
        Generate a system prompt for an agent based on its data.
        
        Args:
            agent_data: Agent configuration from the database
            
        Returns:
            System prompt string
        """
        # If a custom system prompt is provided, use it
        if agent_data.system_prompt:
            return agent_data.system_prompt
        
        # Otherwise, generate a prompt based on role and seniority
        role_description = agent_data.description or f"specialist in {agent_data.role}"
        
        prompt = f"""
        You are a {agent_data.seniority} AI agent specializing as a {role_description}.
        
        Your role: {agent_data.role}
        
        You work autonomously to complete tasks assigned to you, but can also collaborate with other agents.
        When working on tasks:
        1. Think step by step
        2. Use the tools available to you efficiently
        3. Always explain your reasoning
        4. If you need help from another specialist, use the handoff capability
        
        Regularly update your health status to indicate if you're functioning properly.
        """
        
        # Add Instagram-specific instructions if the role is related to social media
        role_lower = agent_data.role.lower()
        if 'social' in role_lower or 'media' in role_lower or 'instagram' in role_lower:
            prompt += f"""
            
            Since you are working with Instagram, keep in mind:
            - Always consider current Instagram trends and best practices
            - Focus on engaging visual content and compelling captions
            - Analyze hashtags carefully for maximum reach
            - Consider the client's brand identity in all recommendations
            - Track performance metrics to optimize content strategy
            """
        
        prompt += """
        
        This is a production environment, so complete your tasks efficiently and accurately.
        If you need to create a new tool to accomplish your task, you can propose its implementation.
        """
        
        return prompt