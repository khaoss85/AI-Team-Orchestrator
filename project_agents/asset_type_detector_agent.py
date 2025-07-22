# project_agents/asset_type_detector_agent.py
"""
Agent definition for the AssetTypeDetectorAgent.
"""

ASSET_TYPE_DETECTOR_AGENT_CONFIG = {
    "name": "AssetTypeDetectorAgent",
    "model": "gpt-4o-mini",
    "instructions": "You are an AI business analyst that intelligently classifies any content into business asset types. Respond only with valid JSON.",
}
