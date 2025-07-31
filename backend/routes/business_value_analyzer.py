# backend/routes/business_value_analyzer.py

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel
from middleware.trace_middleware import get_trace_id, create_traced_logger

router = APIRouter(tags=["business_value"])
logger = logging.getLogger(__name__)

class BusinessValueAnalysisRequest(BaseModel):
    task: Dict[str, Any]
    goal_context: Optional[Dict[str, Any]] = None

class BusinessValueAnalysisResponse(BaseModel):
    success: bool
    business_value_score: float
    content_type: str
    reasoning: str
    confidence: float

@router.post("/analyze-task-business-value")
async def analyze_task_business_value(
    request: Request,
    analysis_request: BusinessValueAnalysisRequest
):
    """
    🤖 AI-DRIVEN: Analyze task business value using semantic understanding
    Replaces hard-coded business value scoring with intelligent analysis
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        task = analysis_request.task
        goal_context = analysis_request.goal_context or {}
        
        logger.info(f"🤖 Analyzing business value for task: {task.get('name', 'Unnamed')}")
        
        # 🧠 AI-DRIVEN: Use OpenAI for semantic business value analysis
        try:
            from openai import AsyncOpenAI
            import os
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Prepare context for AI analysis
            task_name = task.get('name', '')
            task_description = task.get('description', '')
            task_status = task.get('status', 'unknown')
            goal_description = goal_context.get('description', '')
            
            analysis_prompt = f"""Analyze the business value of this task:

Task: {task_name}
Description: {task_description}
Status: {task_status}
Goal Context: {goal_description}

Evaluate:
1. Business Impact: How directly does this contribute to business objectives?
2. Content Quality: Is this producing real, actionable business content?
3. Strategic Value: Does this align with business goals?

Provide:
- business_value_score: 0-100 (higher = more valuable)
- content_type: "strategic", "operational", "informational", "template"
- reasoning: Brief explanation of the score
- confidence: 0-1 confidence in the assessment

Respond in JSON format only."""

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a business value analyst. Respond only with valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            ai_result = json.loads(response.choices[0].message.content)
            
            # Extract and validate results
            business_value_score = float(ai_result.get('business_value_score', 50))
            content_type = ai_result.get('content_type', 'informational')
            reasoning = ai_result.get('reasoning', 'AI analysis completed')
            confidence = float(ai_result.get('confidence', 0.8))
            
            # Ensure score is within bounds
            business_value_score = max(0, min(100, business_value_score))
            confidence = max(0, min(1, confidence))
            
            logger.info(f"✅ AI Business Value Analysis completed: {business_value_score}/100 ({content_type})")
            
            return BusinessValueAnalysisResponse(
                success=True,
                business_value_score=business_value_score,
                content_type=content_type,
                reasoning=reasoning,
                confidence=confidence
            )
            
        except Exception as ai_error:
            logger.warning(f"⚠️ AI analysis failed, using fallback: {ai_error}")
            
            # 🛡️ FALLBACK: Basic heuristic scoring when AI unavailable
            fallback_score = 50.0
            content_type = "unknown"
            
            # Simple heuristic based on task status and name
            if task_status == "completed":
                fallback_score += 20
            if any(keyword in task_name.lower() for keyword in ['contact', 'email', 'revenue', 'customer']):
                fallback_score += 20
                content_type = "operational"
            elif any(keyword in task_name.lower() for keyword in ['strategy', 'plan', 'analysis']):
                fallback_score += 10
                content_type = "strategic"
            else:
                content_type = "informational"
            
            return BusinessValueAnalysisResponse(
                success=True,
                business_value_score=min(100, fallback_score),
                content_type=content_type,
                reasoning="Fallback heuristic analysis (AI unavailable)",
                confidence=0.6
            )
    
    except Exception as e:
        logger.error(f"❌ Business value analysis failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Business value analysis failed: {str(e)}"
        )