# project_agents/universal_pipeline_agent.py
"""
Agent definition for the UniversalPipelineAgent.
"""

def get_universal_pipeline_agent_config(model: str) -> dict:
    """
    Returns the configuration for the UniversalPipelineAgent.
    The agent's model is dynamically tailored.
    """
    return {
        "name": "UniversalPipelineAgent",
        "model": model,
        "instructions": "You are a universal AI assistant that follows instructions precisely.",
    }
