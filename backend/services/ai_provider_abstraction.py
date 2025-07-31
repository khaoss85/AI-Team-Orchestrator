# backend/services/ai_provider_abstraction.py
"""
AI Provider Abstraction Layer

This module provides a unified interface for making AI calls, abstracting the
underlying provider (e.g., OpenAI SDK, direct OpenAI client, fallbacks).
This is a key component of the Foundation Layer for the OpenAI SDK migration.
"""

import logging
import os
from typing import Any, Dict, Optional

# Placeholder for the real Agent SDK
# from agents import Agent, Runner, AgentOutputSchema
# from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BaseProvider:
    """Base class for all AI providers."""
    async def call_ai(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError

class OpenAISDKProvider(BaseProvider):
    """Provider for the OpenAI Agent SDK."""
    async def call_ai(self, **kwargs: Any) -> Dict[str, Any]:
        logger.info("Using REAL OpenAI SDK Provider")
        
        try:
            from agents import Runner
        except ImportError:
            logger.error("❌ OpenAI Agent SDK ('agents') not found. Cannot proceed with SDK call.")
            raise ImportError("agents SDK is not installed or available.")

        agent = kwargs.get('agent')
        prompt = kwargs.get('prompt')

        if not agent or not prompt:
            raise ValueError("Agent and prompt are required for the real SDK provider call.")

        try:
            # Handle both dict and object agents
            agent_name = agent.get('name', 'Unknown') if isinstance(agent, dict) else getattr(agent, 'name', 'Unknown')
            logger.info(f"Executing REAL SDK call for agent '{agent_name}'...")
            
            # Configure OpenAI Trace if enabled
            trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
            if trace_enabled:
                logger.info("🔍 OpenAI Trace enabled - calls will be tracked in OpenAI platform")
                # Set additional trace headers/config if needed
                os.environ['OPENAI_TRACE'] = 'true'
            
            # The actual, production-ready SDK call
            # Create proper agent object from dict if needed
            if isinstance(agent, dict):
                from agents import Agent as OpenAIAgent
                sdk_agent = OpenAIAgent(**agent)
            else:
                sdk_agent = agent
            
            # Use Runner.run as static method (not context manager)
            result = await Runner.run(sdk_agent, prompt)
            
            # Process the result - handle multiple possible formats
            logger.info(f"🔍 DEBUG: SDK result type: {type(result)}")
            logger.info(f"🔍 DEBUG: SDK result attributes: {dir(result) if hasattr(result, '__dict__') else 'No attributes'}")
            
            # Try different ways to extract the content
            if hasattr(result, 'data') and hasattr(result.data, 'model_dump'):
                # Pydantic model format
                output_data = result.data.model_dump()
                logger.info("✅ Real SDK call successful (Pydantic format).")
                return output_data
            elif hasattr(result, 'data') and isinstance(result.data, str):
                # String data format
                try:
                    import json
                    output_data = json.loads(result.data)
                    logger.info("✅ Real SDK call successful (JSON string format).")
                    return output_data
                except:
                    logger.info("✅ Real SDK call successful (raw string format).")
                    return {"content": result.data}
            elif hasattr(result, 'content'):
                # Direct content attribute
                try:
                    import json
                    output_data = json.loads(result.content)
                    logger.info("✅ Real SDK call successful (content JSON format).")
                    return output_data
                except:
                    logger.info("✅ Real SDK call successful (content string format).")
                    return {"content": result.content}
            elif isinstance(result, str):
                # Raw string response
                try:
                    import json
                    output_data = json.loads(result)
                    logger.info("✅ Real SDK call successful (raw JSON format).")
                    return output_data
                except:
                    logger.info("✅ Real SDK call successful (raw string format).")
                    return {"content": result}
            elif isinstance(result, dict):
                # Already a dict
                logger.info("✅ Real SDK call successful (dict format).")
                return result
            elif hasattr(result, 'final_output'):
                # RunResult format from OpenAI SDK
                final_output = result.final_output
                logger.info(f"✅ Real SDK call successful (RunResult format). Output type: {type(final_output)}")
                
                if isinstance(final_output, str):
                    # Extract JSON from markdown code blocks if present
                    import re
                    json_match = re.search(r'```json\s*\n(.*?)\n\s*```', final_output, re.DOTALL)
                    if json_match:
                        try:
                            import json
                            json_content = json_match.group(1)
                            output_data = json.loads(json_content)
                            logger.info("✅ Extracted JSON from RunResult markdown format.")
                            return output_data
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON from markdown: {e}")
                            # Try to fix common JSON issues
                            try:
                                # Fix common issues: trailing commas, single quotes, missing quotes
                                fixed_json = json_content
                                # Remove trailing commas
                                fixed_json = re.sub(r',\s*}', '}', fixed_json)
                                fixed_json = re.sub(r',\s*]', ']', fixed_json)
                                # Try again with fixed JSON
                                output_data = json.loads(fixed_json)
                                logger.info("✅ Fixed and parsed JSON from markdown format.")
                                return output_data
                            except:
                                pass
                    
                    # Try parsing the whole thing as JSON
                    try:
                        import json
                        output_data = json.loads(final_output)
                        logger.info("✅ Parsed RunResult final_output as JSON.")
                        return output_data
                    except Exception as parse_error:
                        logger.debug(f"JSON parsing failed: {parse_error}")
                        # Try to fix common JSON issues in the full output
                        try:
                            fixed_output = final_output
                            # Remove trailing commas
                            fixed_output = re.sub(r',\s*}', '}', fixed_output)
                            fixed_output = re.sub(r',\s*]', ']', fixed_output)
                            # Remove BOM and other invisible characters
                            fixed_output = fixed_output.strip().lstrip('\ufeff')
                            output_data = json.loads(fixed_output)
                            logger.info("✅ Fixed and parsed RunResult final_output as JSON.")
                            return output_data
                        except:
                            logger.info("✅ RunResult final_output as string (JSON parsing failed).")
                            return {"content": final_output}
                else:
                    return {"content": str(final_output)}
            else:
                logger.warning(f"SDK result format is unexpected: {type(result)}. Attempting string conversion.")
                return {"content": str(result)}

        except Exception as e:
            # Handle both dict and object agents for error logging
            agent_name = agent.get('name', 'Unknown') if isinstance(agent, dict) else getattr(agent, 'name', 'Unknown')
            logger.error(f"❌ Real OpenAI SDK call failed for agent '{agent_name}': {e}", exc_info=True)
            # Re-raise the exception to be handled by the caller
            raise e

class OpenAIDirectProvider(BaseProvider):
    """Provider for direct OpenAI client calls (legacy)."""
    async def call_ai(self, **kwargs: Any) -> Dict[str, Any]:
        logger.info("Using Direct OpenAI Client Provider (Legacy)")
        
        # Configure OpenAI Trace if enabled
        trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
        if trace_enabled:
            logger.info("🔍 OpenAI Trace enabled for direct client calls")
            # Note: Direct client calls may have limited trace support compared to SDK
        
        # Placeholder for the direct client call
        # client = kwargs.get('client')
        # response = await client.chat.completions.create(...)
        return {"provider": "openai_direct", "data": "direct_client_result"}

class FallbackProvider(BaseProvider):
    """Provider for fallback mechanisms."""
    async def call_ai(self, **kwargs: Any) -> Dict[str, Any]:
        logger.warning("Using Fallback Provider")
        return {"provider": "fallback", "error": "AI provider failed"}

class AIProviderManager:
    """
    Manages different AI providers and routes calls based on configuration.
    """
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            'openai_sdk': OpenAISDKProvider(),
            'openai_direct': OpenAIDirectProvider(),
            'fallback': FallbackProvider()
        }
        logger.info("AIProviderManager initialized.")

    async def call_ai(
        self,
        provider_type: str = 'openai_sdk',
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Calls the specified AI provider.

        Args:
            provider_type: 'openai_sdk', 'openai_direct', or 'fallback'.
            **kwargs: Arguments to pass to the provider's call_ai method.

        Returns:
            The result from the AI provider.
        """
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Invalid provider type: {provider_type}. Using fallback.")
            provider = self.providers['fallback']
        
        try:
            return await provider.call_ai(**kwargs)
        except Exception as e:
            logger.error(f"Error calling AI provider '{provider_type}': {e}", exc_info=True)
            logger.warning("Falling back to FallbackProvider.")
            fallback_provider = self.providers['fallback']
            return await fallback_provider.call_ai(**kwargs)

# Singleton instance
ai_provider_manager = AIProviderManager()
