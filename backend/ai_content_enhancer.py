# backend/ai_content_enhancer.py
"""
🤖 AI Content Enhancer
Improves agent prompts and content generation to avoid placeholder data
"""

import logging
import json
import openai
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIContentEnhancer:
    """
    🌍 AI-DRIVEN CONTENT ENHANCEMENT
    Improves content generation quality to reduce placeholder data
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def enhance_agent_prompt(
        self,
        original_prompt: str,
        workspace_goal: str,
        task_context: Dict[str, Any]
    ) -> str:
        """
        🤖 AI-DRIVEN PROMPT ENHANCEMENT
        Improve agent prompts to generate more concrete, actionable content
        """
        try:
            enhancement_prompt = f"""
Enhance this agent prompt to generate higher quality, more concrete business deliverables.

WORKSPACE GOAL: {workspace_goal}
TASK CONTEXT: {json.dumps(task_context, indent=2)}
ORIGINAL PROMPT: {original_prompt}

Transform the prompt to:
1. Request SPECIFIC, REAL data instead of placeholders
2. Demand business-ready output that can be used immediately
3. Include quality criteria and validation requirements  
4. Emphasize concrete metrics, numbers, and actionable items
5. Prevent generic examples and placeholder content

Enhanced prompt should result in deliverables that:
- Contain real business data (not [Company], [Name], example@email.com)
- Are immediately actionable by business users
- Include specific metrics, timelines, and concrete details
- Meet professional business standards

Return only the enhanced prompt text, ready to use.
"""

            try:
                from utils.rate_limiter import safe_openai_call
                response = await safe_openai_call(
                    self.client, "prompt_enhancement",
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI prompt engineer specializing in business content quality. Transform prompts to generate concrete, professional deliverables without placeholder content."},
                        {"role": "user", "content": enhancement_prompt}
                    ],
                    temperature=0.2
                )
            except ImportError:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI prompt engineer specializing in business content quality. Transform prompts to generate concrete, professional deliverables without placeholder content."},
                        {"role": "user", "content": enhancement_prompt}
                    ],
                    temperature=0.2
                )
            
            enhanced_prompt = response.choices[0].message.content
            
            # Add quality enforcement footer
            quality_footer = """

QUALITY REQUIREMENTS:
- Generate REAL data only (no placeholders like [Name], [Company], example@email.com)
- Provide specific numbers, dates, and concrete details
- Create immediately usable business content
- Include actionable steps with clear metrics
- Ensure professional presentation standards
- Validate all data for business appropriateness

OUTPUT MUST BE BUSINESS-READY WITHOUT FURTHER EDITING."""

            return enhanced_prompt + quality_footer
            
        except Exception as e:
            logger.error(f"🤖 Prompt enhancement failed: {e}")
            return original_prompt
    
    async def post_process_content(
        self,
        generated_content: str,
        workspace_goal: str,
        task_type: str
    ) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN POST-PROCESSING
        Clean up generated content to replace any remaining placeholders
        """
        try:
            cleanup_prompt = f"""
Review and enhance this generated business content to eliminate placeholders and improve quality.

WORKSPACE GOAL: {workspace_goal}
TASK TYPE: {task_type}
GENERATED CONTENT: {generated_content}

Transform this content to:
1. Replace ALL placeholder patterns with realistic business data
2. Ensure professional presentation quality
3. Add specific metrics and concrete details
4. Make content immediately actionable for business use
5. Verify all contact info, numbers, and details are realistic

Common placeholder patterns to fix:
- [Name], [Company], [Email] → Real examples
- example@email.com → Professional email addresses  
- Your company, Insert here → Specific content
- Generic metrics → Realistic business numbers
- Template text → Customized content

Return enhanced content in this format:
{{
    "enhanced_content": "cleaned and enhanced content",
    "quality_score": 0-100,
    "improvements_made": ["improvement 1", "improvement 2"],
    "remaining_issues": ["issue 1", "issue 2"],
    "business_readiness": "ready|needs_review|requires_enhancement"
}}
"""

            try:
                from utils.rate_limiter import safe_openai_call
                response = await safe_openai_call(
                    self.client, "content_cleanup",
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI content editor specializing in transforming placeholder-heavy content into professional, business-ready deliverables."},
                        {"role": "user", "content": cleanup_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            except ImportError:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI content editor specializing in transforming placeholder-heavy content into professional, business-ready deliverables."},
                        {"role": "user", "content": cleanup_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            
            result = json.loads(response.choices[0].message.content)
            result["processed_at"] = datetime.now().isoformat()
            result["processing_method"] = "ai_driven_cleanup"
            
            return result
            
        except Exception as e:
            logger.error(f"🤖 Content post-processing failed: {e}")
            return {
                "enhanced_content": generated_content,
                "quality_score": 50,
                "improvements_made": [],
                "remaining_issues": ["Post-processing failed"],
                "business_readiness": "needs_review",
                "processed_at": datetime.now().isoformat(),
                "processing_method": "fallback"
            }
    
    async def generate_realistic_sample_data(
        self,
        data_type: str,
        business_context: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN REALISTIC DATA GENERATION
        Generate realistic sample data for any business context
        """
        try:
            data_prompt = f"""
Generate {count} realistic sample {data_type} entries for this business context.

BUSINESS CONTEXT: {business_context}
DATA TYPE: {data_type}

Requirements:
1. Use realistic names, companies, and contact information
2. Ensure data fits the business context authentically
3. Avoid obvious patterns or fake-sounding data
4. Include appropriate business details and metrics
5. Make data diverse but contextually appropriate

Generate realistic, varied data that a business would actually encounter.

Return as JSON array of objects with appropriate fields for the data type.
"""

            try:
                from utils.rate_limiter import safe_openai_call
                response = await safe_openai_call(
                    self.client, "sample_data_generation",
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI data generator that creates realistic business sample data. Generate diverse, authentic-looking data appropriate for professional business use."},
                        {"role": "user", "content": data_prompt}
                    ],
                    temperature=0.7,  # Higher temperature for diversity
                    response_format={"type": "json_object"}
                )
            except ImportError:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI data generator that creates realistic business sample data. Generate diverse, authentic-looking data appropriate for professional business use."},
                        {"role": "user", "content": data_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            
            data_result = json.loads(response.choices[0].message.content)
            return data_result.get("data", [])
            
        except Exception as e:
            logger.error(f"🤖 Sample data generation failed: {e}")
            return []

# Global instance
ai_content_enhancer = AIContentEnhancer()