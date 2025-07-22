# project_agents/content_processor_agent.py
"""
Agent definition for the ContentProcessorAgent.
"""

def get_content_processor_agent_config(format: str, primary_model: str) -> dict:
    """
    Returns the configuration for the ContentProcessorAgent.
    The agent's instructions and model are dynamically tailored.
    """
    return {
        "name": "ContentProcessorAgent",
        "model": primary_model,
        "instructions": f"You are an expert UI/UX designer and content formatter. You specialize in transforming structured data into beautiful, professional {format.upper()} presentations that are engaging and business-focused.",
    }
