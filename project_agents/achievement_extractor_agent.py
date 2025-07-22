# project_agents/achievement_extractor_agent.py
"""
Agent definition for the AchievementExtractorAgent.
"""

ACHIEVEMENT_EXTRACTOR_AGENT_CONFIG = {
    "name": "AchievementExtractorAgent",
    "model": "gpt-4o-mini",
    "instructions": "You are an expert at extracting measurable achievements from task results. Respond only with valid JSON.",
}
