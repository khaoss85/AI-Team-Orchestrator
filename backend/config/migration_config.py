# backend/config/migration_config.py
"""
Configuration for the migration from direct OpenAI client calls to the Agent SDK.

This file contains feature flags to enable or disable the new SDK-based implementations
for different parts of the system, allowing for a gradual and safe rollout.
"""

MIGRATION_FLAGS = {
    # Core Business Logic - Phase 1
    'task_generation_sdk': False,
    'director_sdk': False,
    'executor_sdk': False,

    # Orchestration Layer - Phase 2
    'universal_pipeline_sdk': False,
    'memory_sdk': False,
    'conversational_sdk': False,
    'real_task_executor_sdk': False,
    'task_analyzer_sdk': False,

    # Support Layer - Phase 3
    'ai_utils_sdk': False,
    'similarity_engine_sdk': False,
    'tool_validator_sdk': False,
    'agent_provisioner_sdk': False,
}

def is_sdk_migrated(component_name: str) -> bool:
    """
    Check if a component is configured to use the new Agent SDK implementation.
    
    Args:
        component_name: The name of the component (e.g., 'task_generation_sdk').
    
    Returns:
        True if the component's feature flag is set to True, False otherwise.
    """
    return MIGRATION_FLAGS.get(component_name, False)
