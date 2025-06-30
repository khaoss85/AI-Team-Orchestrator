"""
🤖 Simple AI Content Extractor
Simplified version that uses OpenAI directly for testing
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

@dataclass
class SimpleContentResult:
    """Simple content analysis result"""
    discovered_content: Dict[str, Any]
    reality_score: float
    usability_score: float
    confidence: float
    reasoning: str

class SimpleAIContentExtractor:
    """
    🤖 Simple AI-Driven Content Extractor for testing
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            self.ai_available = True
        else:
            logger.warning("OpenAI API key not available, AI analysis will be limited")
            self.client = None
            self.ai_available = False
        
    async def extract_real_content(
        self, 
        task_results: List[Dict[str, Any]], 
        goal_context: str,
        workspace_context: Dict[str, Any] = None
    ) -> SimpleContentResult:
        """
        🤖 Simple AI content extraction
        """
        try:
            logger.info("🤖 Starting simple AI content extraction...")
            
            if not self.ai_available:
                return self._fallback_analysis(task_results, goal_context)
            
            # Prepare task results
            results_text = self._prepare_results(task_results)
            
            # Simple AI prompt
            prompt = f"""
Analizza questi risultati di task per estrarre contenuto reale:

TASK RESULTS:
{results_text}

GOAL CONTEXT: {goal_context}

Identifica:
1. Che contenuto reale è stato prodotto?
2. È utilizzabile o template/generico?
3. Score 0-100 per realtà e usabilità

Rispondi in JSON:
{{
    "discovered_content": {{"description": "cosa è stato trovato"}},
    "reality_score": 0-100,
    "usability_score": 0-100,
    "confidence": 0-100,
    "reasoning": "spiegazione"
}}
"""
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse response
            try:
                result_data = json.loads(ai_response)
                return SimpleContentResult(
                    discovered_content=result_data.get("discovered_content", {}),
                    reality_score=result_data.get("reality_score", 0),
                    usability_score=result_data.get("usability_score", 0),
                    confidence=result_data.get("confidence", 0),
                    reasoning=result_data.get("reasoning", "")
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {ai_response}")
                return SimpleContentResult(
                    discovered_content={"error": "Parsing failed"},
                    reality_score=0,
                    usability_score=0,
                    confidence=0,
                    reasoning="AI response parsing failed"
                )
                
        except Exception as e:
            logger.error(f"Error in simple AI content extraction: {e}")
            return SimpleContentResult(
                discovered_content={"error": str(e)},
                reality_score=0,
                usability_score=0,
                confidence=0,
                reasoning=f"Extraction failed: {e}"
            )
    
    def _prepare_results(self, task_results: List[Dict[str, Any]]) -> str:
        """Prepare task results for AI analysis"""
        formatted_results = []
        
        for i, task_result in enumerate(task_results):
            task_name = task_result.get('name', f'Task {i+1}')
            task_status = task_result.get('status', 'unknown')
            
            # Extract actual results/content
            result_content = ""
            if 'result' in task_result:
                result = task_result['result']
                if isinstance(result, dict):
                    # Look for various result formats
                    if 'detailed_results_json' in result:
                        result_content = str(result['detailed_results_json'])
                    elif 'summary' in result:
                        result_content = str(result['summary'])
                    else:
                        result_content = str(result)
                else:
                    result_content = str(result)
            
            formatted_results.append(f"""
TASK: {task_name}
STATUS: {task_status}
CONTENT: {result_content[:500]}...
---""")
        
        return "\n".join(formatted_results)
    
    def _fallback_analysis(self, task_results: List[Dict[str, Any]], goal_context: str) -> SimpleContentResult:
        """Fallback analysis when AI is not available"""
        
        # Basic analysis without AI
        total_tasks = len(task_results)
        completed_tasks = len([t for t in task_results if t.get('status') == 'completed'])
        
        # Check for real content indicators
        content_found = False
        real_content = {}
        
        for task in task_results:
            if 'result' in task and task['result']:
                result = task['result']
                if isinstance(result, dict):
                    if 'detailed_results_json' in result or 'summary' in result:
                        content_found = True
                        real_content[task.get('name', 'unknown')] = "Content found in task results"
                    
        # Calculate basic scores
        reality_score = 60 if content_found else 20
        usability_score = 50 if completed_tasks > 0 else 10
        confidence = 30  # Low confidence without AI
        
        reasoning = f"Fallback analysis: Found {total_tasks} tasks, {completed_tasks} completed. Content indicators: {content_found}"
        
        return SimpleContentResult(
            discovered_content=real_content if real_content else {"note": "No detailed content analysis without AI"},
            reality_score=reality_score,
            usability_score=usability_score,
            confidence=confidence,
            reasoning=reasoning
        )

# Global instance
simple_ai_content_extractor = SimpleAIContentExtractor()

# Export
__all__ = ["SimpleAIContentExtractor", "simple_ai_content_extractor", "SimpleContentResult"]