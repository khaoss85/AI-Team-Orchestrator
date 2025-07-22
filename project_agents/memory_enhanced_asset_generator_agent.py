# project_agents/memory_enhanced_asset_generator_agent.py
"""
Agent definition for the MemoryEnhancedAssetGeneratorAgent.
"""

def get_memory_enhanced_asset_generator_agent_config(content_type: str) -> dict:
    """
    Returns the configuration for the MemoryEnhancedAssetGeneratorAgent.
    The agent's instructions are dynamically tailored to the content type.
    """
    return {
        "name": "MemoryEnhancedAssetGeneratorAgent",
        "model": "gpt-4o-mini",
        "instructions": f"You are an expert {content_type} generator. Respond only with valid JSON.",
    }
