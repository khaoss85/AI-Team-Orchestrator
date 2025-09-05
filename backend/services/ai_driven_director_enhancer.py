#!/usr/bin/env python3
"""
🧠 AI-DRIVEN DIRECTOR ENHANCER

Migliora il Director esistente con intelligenza AI per:
1. Analizzare l'intent dei task nel workspace goal
2. Influenzare AI-driven la creazione di agenti appropriati
3. Assegnare ruoli specifici basandosi su AI analysis

Principi:
- Usa Director esistente (no nuovi silos)
- Completamente AI-driven (no hard-coded rules)
- Integrazione olistica con sistema esistente
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class AIDirectorEnhancer:
    """
    🧠 Migliora il Director esistente con AI-driven intent analysis
    """
    
    def __init__(self):
        pass
    
    async def enhance_director_proposal_with_ai_intent(
        self, 
        workspace_goal: str,
        user_feedback: str,
        budget_constraint: Dict[str, Any],
        extracted_goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        🎯 Migliora la proposal del Director con AI intent analysis
        """
        
        logger.info("🧠 Enhancing Director proposal with AI intent analysis")
        
        # Analyze intent of workspace goals to understand what types of agents are needed
        from ai_driven_task_intent_analyzer import analyze_task_intent_ai_driven
        
        intent_analysis_results = []
        
        # Analyze main workspace goal
        main_intent = await analyze_task_intent_ai_driven(
            task_name="Workspace Main Goal",
            task_description=workspace_goal,
            workspace_context={"user_feedback": user_feedback, "budget": budget_constraint}
        )
        intent_analysis_results.append(main_intent)
        
        # Analyze extracted sub-goals
        for goal in extracted_goals:
            goal_intent = await analyze_task_intent_ai_driven(
                task_name=goal.get("type", "Sub-goal"),
                task_description=goal.get("description", ""),
                workspace_context={"metrics": goal.get("metrics", {})}
            )
            intent_analysis_results.append(goal_intent)
        
        # Generate AI-driven agent specialization recommendations
        specialization_prompt = self._build_agent_specialization_prompt(
            workspace_goal, intent_analysis_results, user_feedback
        )
        
        # Use AI to determine optimal agent roles based on intent analysis
        import openai
        client = openai.AsyncOpenAI()
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_agent_specialization_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": specialization_prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            specialization_result = json.loads(response.choices[0].message.content)
            
            logger.info(f"✅ AI generated agent specialization recommendations")
            return {
                "intent_analysis": [intent.model_dump() for intent in intent_analysis_results],
                "recommended_specializations": specialization_result,
                "ai_reasoning": specialization_result.get("ai_reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"❌ AI agent specialization failed: {e}")
            return {
                "intent_analysis": [intent.model_dump() for intent in intent_analysis_results],
                "recommended_specializations": {"agents": []},
                "ai_reasoning": f"Fallback due to error: {e}"
            }
    
    def _get_agent_specialization_system_prompt(self) -> str:
        """System prompt per AI-driven agent specialization"""
        return """You are an AI team composition specialist. Based on task intent analysis, recommend specific agent roles and specializations.

Your job is to analyze the intent analysis results and recommend agent roles that will ACTUALLY fulfill the user's true needs.

Key insights:
- If intent analysis shows "specific_data_extraction" needs, recommend agents specialized in data collection, web research, contact finding
- If intent analysis shows "methodology_research" needs, recommend strategy consultants, planners, analysts
- If mixed intents, recommend balanced teams

For specific_data_extraction intents, recommend roles like:
- "Data Research Specialist" (for finding actual contacts, emails, phone numbers)
- "Web Intelligence Analyst" (for scraping and data extraction)
- "Contact Database Manager" (for organizing and validating contact data)

For methodology_research intents, recommend roles like:
- "Strategy Consultant" (for developing approaches and methodologies)
- "Business Analyst" (for research and planning)
- "Process Designer" (for creating workflows and systems)

Respond in JSON format:
{
  "agents": [
    {
      "role": "specific role name",
      "specialization_focus": "what this agent specifically focuses on",
      "why_needed": "why this role is needed based on intent analysis",
      "seniority": "junior|senior|expert"
    }
  ],
  "team_composition_reasoning": "overall reasoning for this team composition",
  "ai_reasoning": "detailed reasoning for recommendations"
}"""

    def _build_agent_specialization_prompt(
        self,
        workspace_goal: str,
        intent_analysis_results: List[Any],
        user_feedback: str
    ) -> str:
        """Build prompt per AI agent specialization"""
        
        prompt = f"""Based on this intent analysis, recommend optimal agent roles and specializations:

WORKSPACE GOAL: {workspace_goal}
USER FEEDBACK: {user_feedback}

INTENT ANALYSIS RESULTS:"""
        
        for i, intent in enumerate(intent_analysis_results, 1):
            prompt += f"""

Intent {i}:
- Type: {intent.intent_type}
- Specificity: {intent.specificity_level}
- Expected Deliverable: {intent.expected_deliverable_nature}
- Confidence: {intent.confidence_score}
- AI Reasoning: {intent.ai_reasoning}"""
        
        prompt += """

Based on these intent analysis results, what specific agent roles and specializations would be most effective?

Consider:
- Are users expecting concrete data (contacts, emails, phone numbers) or abstract guidance?
- What specialist skills are needed to fulfill these specific intents?
- How should agents be specialized to deliver exactly what users expect?

Recommend agents that will ACTUALLY deliver what the intent analysis shows users want."""
        
        return prompt
    
    def modify_director_user_feedback_with_ai_insights(
        self, 
        original_user_feedback: str,
        ai_enhancement_results: Dict[str, Any]
    ) -> str:
        """
        🎯 Modifica il user_feedback per influenzare AI-driven il Director
        
        Invece di creare nuovi agenti, influenziamo l'AI del Director esistente
        aggiungendo insights AI-driven al user_feedback
        """
        
        intent_summaries = []
        for intent in ai_enhancement_results.get("intent_analysis", []):
            intent_summaries.append(f"- Intent: {intent['intent_type']} ({intent['specificity_level']})")
        
        recommended_agents = ai_enhancement_results.get("recommended_specializations", {}).get("agents", [])
        agent_recommendations = []
        for agent in recommended_agents:
            agent_recommendations.append(f"- {agent['role']}: {agent['specialization_focus']}")
        
        enhanced_feedback = f"""{original_user_feedback}

AI Intent Analysis Insights:
{chr(10).join(intent_summaries)}

Based on AI analysis, I need agents specialized in:
{chr(10).join(agent_recommendations)}

Please ensure the team has the right specialists to deliver concrete results matching these intents."""
        
        return enhanced_feedback

# Singleton instance
ai_director_enhancer = AIDirectorEnhancer()

async def enhance_director_with_ai_intent(
    workspace_goal: str,
    user_feedback: str, 
    budget_constraint: Dict[str, Any],
    extracted_goals: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    🎯 Entry point per migliorare Director con AI intent analysis
    
    Returns: Enhanced user feedback che influenza AI-driven il Director
    """
    
    # Get AI enhancement
    enhancement_results = await ai_director_enhancer.enhance_director_proposal_with_ai_intent(
        workspace_goal, user_feedback, budget_constraint, extracted_goals
    )
    
    # Modify user feedback to influence Director AI
    enhanced_user_feedback = ai_director_enhancer.modify_director_user_feedback_with_ai_insights(
        user_feedback, enhancement_results
    )
    
    return {
        "enhanced_user_feedback": enhanced_user_feedback,
        "ai_reasoning": enhancement_results.get("ai_reasoning", ""),
        "intent_summary": str(enhancement_results.get("intent_analysis", []))
    }