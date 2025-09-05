#!/usr/bin/env python3
"""
🧠 AI-DRIVEN TASK INTENT ANALYZER

Sistema completamente AI-driven per comprendere l'intent del task
senza hard-coding o keyword matching. Utilizza solo AI per determinare
se un task richiede dati specifici o metodologie.

Principi:
- Completamente AI-driven (no keywords hard-coded)
- Usa componenti esistenti del sistema  
- No nuovi silos
- Integrazione olistica con Director e Agent assignment esistente
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskIntent(BaseModel):
    """Risultato dell'analisi AI dell'intent del task"""
    intent_type: str  # "specific_data_extraction" | "methodology_research" | "content_creation" | "analysis"
    specificity_level: str  # "concrete" | "abstract" | "mixed"
    expected_deliverable_nature: str  # Descrizione AI di cosa si aspetta l'utente
    confidence_score: float
    ai_reasoning: str

class AITaskIntentAnalyzer:
    """
    🧠 Analizzatore AI-driven per comprendere l'intent reale del task
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI()
    
    async def analyze_task_intent(
        self, 
        task_name: str, 
        task_description: str,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> TaskIntent:
        """
        🎯 Analizza l'intent del task in modo completamente AI-driven
        """
        
        logger.info(f"🧠 AI analyzing task intent: {task_name}")
        
        # Build AI-driven analysis prompt
        analysis_prompt = self._build_intent_analysis_prompt(
            task_name, task_description, workspace_context
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_intent_analysis_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            intent = TaskIntent(
                intent_type=result["intent_type"],
                specificity_level=result["specificity_level"], 
                expected_deliverable_nature=result["expected_deliverable_nature"],
                confidence_score=result["confidence_score"],
                ai_reasoning=result["ai_reasoning"]
            )
            
            logger.info(f"✅ Task intent analyzed: {intent.intent_type} ({intent.specificity_level})")
            return intent
            
        except Exception as e:
            logger.error(f"❌ AI intent analysis failed: {e}")
            # Fallback - but still AI-driven through simple heuristics
            return self._create_fallback_intent(task_name, task_description)
    
    def _get_intent_analysis_system_prompt(self) -> str:
        """Sistema prompt completamente AI-driven per analisi intent"""
        return """You are an AI task intent analyzer. Your job is to understand what the user ACTUALLY wants from a task, not just classify it mechanically.

Analyze the task to understand:

1. INTENT TYPE - What is the user's true goal?:
   - "specific_data_extraction": User wants actual, concrete data (names, emails, phone numbers, specific facts)
   - "methodology_research": User wants to understand HOW to do something (strategies, approaches, tools)
   - "content_creation": User wants new content to be created (articles, designs, code)
   - "analysis": User wants insights from existing data

2. SPECIFICITY LEVEL - How concrete vs abstract is the request?:
   - "concrete": User expects specific, actionable, real-world data
   - "abstract": User expects concepts, ideas, strategies
   - "mixed": User expects both concrete data and abstract guidance

3. EXPECTED DELIVERABLE NATURE:
   - Describe in your own words what the user is expecting to receive

Key Insight: The same words can mean different things based on context:
- "Lista contatti" could mean "give me actual contacts" OR "tell me how to find contacts"
- Look for context clues like format specifications ("CSV", "JSON") which indicate concrete data needs
- Look for action words vs research words

Respond in JSON format:
{
  "intent_type": "specific_data_extraction|methodology_research|content_creation|analysis",
  "specificity_level": "concrete|abstract|mixed", 
  "expected_deliverable_nature": "detailed description of what user expects",
  "confidence_score": 0.0-1.0,
  "ai_reasoning": "your reasoning for this classification"
}"""

    def _build_intent_analysis_prompt(
        self, 
        task_name: str, 
        task_description: str,
        workspace_context: Optional[Dict[str, Any]]
    ) -> str:
        """Costruisce prompt per analisi intent specifica"""
        
        prompt = f"""Analyze this task to understand the user's true intent:

TASK NAME: {task_name}
TASK DESCRIPTION: {task_description}"""
        
        if workspace_context:
            import json
            prompt += f"\nWORKSPACE CONTEXT: {json.dumps(workspace_context, indent=2)}"
        
        prompt += """

Consider these scenarios:
- If user mentions specific formats (CSV, JSON, list format), they likely want concrete data
- If user mentions quantities ("10 contacts", "50 leads"), they want specific data
- If user asks for "strategy", "approach", "methodology", they want abstract guidance
- If user asks for "how to", they want methodology
- If user provides detailed field requirements (name, email, phone), they want concrete data

What is the user's TRUE intent? What do they expect to receive?"""
        
        return prompt
    
    def _create_fallback_intent(self, task_name: str, task_description: str) -> TaskIntent:
        """AI-DRIVEN fallback intent analysis - conservative approach without hard-coded keywords"""
        
        logger.warning(f"🔄 Using fallback intent analysis for: {task_name}")
        
        # Conservative AI-driven fallback: assume methodology unless clear data extraction patterns
        # This preserves the AI-driven principle while providing graceful degradation
        
        text_length = len(f"{task_name} {task_description}")
        
        # Conservative approach: if task is very short or unclear, assume methodology
        # This prevents incorrect data extraction attempts when AI is unavailable
        if text_length < 50:
            intent_type = "methodology_research"
            specificity_level = "abstract"
            expected_nature = "General guidance and strategic approaches"
            reasoning = "Conservative fallback: short task description suggests high-level guidance needed"
        else:
            # For longer descriptions, assume mixed intent to allow both approaches
            intent_type = "content_creation"  # Neutral category
            specificity_level = "mixed"
            expected_nature = "Content creation with potential for both data and methodology"
            reasoning = "Conservative fallback: mixed approach to handle uncertain intent"
        
        return TaskIntent(
            intent_type=intent_type,
            specificity_level=specificity_level,
            expected_deliverable_nature=expected_nature,
            confidence_score=0.5,  # Lower confidence for fallback
            ai_reasoning=f"FALLBACK MODE: {reasoning}. Main AI analysis unavailable - using conservative approach to avoid incorrect assumptions."
        )

# Singleton instance
ai_intent_analyzer = AITaskIntentAnalyzer()

async def analyze_task_intent_ai_driven(
    task_name: str,
    task_description: str, 
    workspace_context: Optional[Dict[str, Any]] = None
) -> TaskIntent:
    """
    🎯 Entry point per analisi AI-driven dell'intent del task
    """
    return await ai_intent_analyzer.analyze_task_intent(
        task_name, task_description, workspace_context
    )