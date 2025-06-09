"""
AI Content Processor Route
Processes structured content using AI to generate rich, formatted markup
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import openai
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ContentProcessingRequest(BaseModel):
    content: Dict[str, Any]
    title: str
    format: str = "html"  # html, markdown
    instructions: Optional[str] = None

class ContentProcessingResponse(BaseModel):
    processed_content: str
    original_content: Dict[str, Any]
    processing_metadata: Dict[str, Any]

@router.post("/ai/process-content", response_model=ContentProcessingResponse)
async def process_content_with_ai(request: ContentProcessingRequest):
    """
    Process structured content with AI to generate beautiful, user-friendly markup
    """
    try:
        # Default instructions if none provided
        default_instructions = f"""
Transform this structured data into a beautiful, professional {request.format.upper()} presentation.

Guidelines:
- Use appropriate headings (h1, h2, h3) for hierarchy
- Create visual elements like tables, cards, and lists
- Use semantic HTML tags for accessibility
- Include proper spacing and typography
- Highlight key insights and actionable items
- Make competitor analysis into cards with clear metrics
- Transform data into charts/tables where appropriate
- Add visual icons and emojis for engagement
- Focus on business value and actionability
- Use professional styling classes

CRITICAL: When you encounter arrays or lists (like calendar posts, competitors, etc.), you MUST iterate through ALL items and generate complete HTML for each one. Do NOT just show one example and add a comment about "repeating for each item". Generate the FULL HTML for ALL items in the array.

For example, if there are 18 calendar posts, generate HTML for all 18 posts, not just one with a note about repetition.

IMPORTANT: Do NOT reference external image files (like carousel-icon.png, reel-icon.png, etc.) since they don't exist. Use emoji icons or Unicode symbols instead (📷 🎬 📱 💪 ✨).

Do NOT add instructional comments about repeating content - just generate the complete content for all items.

Output clean, well-structured {request.format.upper()} that is ready to be rendered directly.
"""

        instructions = request.instructions or default_instructions
        
        # Create the AI prompt
        prompt = f"""
Title: {request.title}

Instructions: {instructions}

IMPORTANT STYLING REQUIREMENTS:
- Use only Tailwind CSS classes for styling (no inline styles or <style> tags)
- Generate clean HTML fragments, not full HTML documents
- Use semantic HTML structure (div, h1-h6, p, ul, ol, etc.)
- Focus on content presentation, not page layout

Structured Data to Transform:
{json.dumps(request.content, indent=2)}

Generate clean, professional {request.format.upper()} markup using Tailwind CSS classes that transforms this data into an engaging, easy-to-read presentation.
"""

        # Calculate appropriate max_tokens based on input length
        input_tokens = len(prompt) // 4  # Rough estimate: 1 token ≈ 4 characters
        max_available_tokens = 8000 - input_tokens  # Leave buffer for system message
        
        # Ensure we don't exceed reasonable limits
        max_tokens = min(max_available_tokens, 3000)  # Cap at 3000 for safety
        max_tokens = max(max_tokens, 500)  # Minimum 500 tokens for useful output
        
        logger.info(f"AI processing: input_tokens={input_tokens}, max_tokens={max_tokens}, content_length={len(json.dumps(request.content))}")
        
        # Call OpenAI API
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an expert UI/UX designer and content formatter. You specialize in transforming structured data into beautiful, professional {request.format.upper()} presentations that are engaging and business-focused."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        
        processed_content = response.choices[0].message.content.strip()
        
        # Clean up the response (remove any markdown code blocks if present)
        if request.format == "html":
            # Remove various markdown code block formats
            if processed_content.startswith("```html"):
                processed_content = processed_content[7:]
            elif processed_content.startswith("```HTML"):
                processed_content = processed_content[7:]
            elif processed_content.startswith("```"):
                processed_content = processed_content[3:]
            
            if processed_content.endswith("```"):
                processed_content = processed_content[:-3]
            
            # Remove any remaining HTML document wrapper if present
            if "<!DOCTYPE html>" in processed_content:
                # Extract only the body content
                import re
                body_match = re.search(r'<body[^>]*>(.*?)</body>', processed_content, re.DOTALL)
                if body_match:
                    processed_content = body_match.group(1)
            
            # Remove explanatory text after HTML (common AI behavior)
            # Look for patterns like "\n\nThis HTML..." or "\n\nThe HTML..."
            import re
            explanation_pattern = r'\n\n(This|The) HTML.*$'
            processed_content = re.sub(explanation_pattern, '', processed_content, flags=re.DOTALL)
            
            processed_content = processed_content.strip()
        
        return ContentProcessingResponse(
            processed_content=processed_content,
            original_content=request.content,
            processing_metadata={
                "model_used": "gpt-4",
                "format": request.format,
                "tokens_used": response.usage.total_tokens,
                "processing_time": "N/A"  # Could add timing if needed
            }
        )
        
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Content processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process content: {str(e)}")

@router.post("/ai/process-content/preview")
async def preview_content_processing(request: ContentProcessingRequest):
    """
    Preview what the AI processing would generate without actually calling the API
    Returns a mock/template response for testing
    """
    try:
        # Generate a preview based on content type
        if "competitor_analysis" in request.content:
            preview_html = generate_competitor_analysis_preview(request.content)
        elif "posts" in request.content or "calendar" in str(request.content).lower():
            preview_html = generate_content_calendar_preview(request.content)
        elif "workflow" in str(request.content).lower() or "steps" in request.content:
            preview_html = generate_workflow_preview(request.content)
        else:
            preview_html = generate_generic_preview(request.content, request.title)
        
        return ContentProcessingResponse(
            processed_content=preview_html,
            original_content=request.content,
            processing_metadata={
                "model_used": "preview-generator",
                "format": request.format,
                "tokens_used": 0,
                "processing_time": "0ms"
            }
        )
        
    except Exception as e:
        logger.error(f"Preview generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

def generate_competitor_analysis_preview(content: Dict[str, Any]) -> str:
    """Generate a preview for competitor analysis content"""
    html = f"""
    <div class="space-y-6">
        <div class="bg-blue-50 p-6 rounded-lg border border-blue-200">
            <h1 class="text-2xl font-bold text-blue-900 mb-3">🏆 Competitor Analysis Report</h1>
            <p class="text-blue-700">{content.get('executive_summary', 'Comprehensive analysis of key competitors in the market.')}</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    """
    
    competitors = content.get('competitor_analysis', [])
    for competitor in competitors[:4]:  # Show first 4
        html += f"""
            <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
                <div class="flex items-center mb-4">
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                        <span class="text-blue-600 font-bold text-lg">🏋️</span>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-900">{competitor.get('name', 'Competitor')}</h3>
                        <p class="text-blue-600 text-sm">{competitor.get('instagram_handle', '@handle')}</p>
                    </div>
                </div>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Followers:</span>
                        <span class="font-semibold text-gray-900">{competitor.get('followers', 'N/A')}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Engagement:</span>
                        <span class="font-semibold text-green-600">{competitor.get('engagement_rate', 'N/A')}</span>
                    </div>
                    <div class="mt-3">
                        <p class="text-sm text-gray-700">{competitor.get('content_focus', 'Focus area not specified')}</p>
                    </div>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div class="bg-green-50 p-6 rounded-lg border border-green-200">
            <h2 class="text-xl font-bold text-green-900 mb-4">📊 Key Insights & Recommendations</h2>
            <ul class="space-y-2">
    """
    
    insights = content.get('actionable_insights', [])
    for insight in insights[:3]:  # Show first 3
        html += f'<li class="flex items-start"><span class="text-green-600 mr-2">✓</span><span class="text-green-800">{insight}</span></li>'
    
    html += """
            </ul>
        </div>
    </div>
    """
    
    return html

def generate_content_calendar_preview(content: Dict[str, Any]) -> str:
    """Generate a preview for content calendar"""
    html = """
    <div class="space-y-6">
        <div class="bg-purple-50 p-6 rounded-lg border border-purple-200">
            <h1 class="text-2xl font-bold text-purple-900 mb-3">📅 Content Calendar Strategy</h1>
            <p class="text-purple-700">Strategic content planning and scheduling framework</p>
        </div>
    """
    
    # Check for calendar posts
    calendar_items = content.get('calendar', [])
    posts = content.get('posts', [])
    items_to_show = calendar_items or posts
    
    if items_to_show:
        html += '<div class="space-y-4">'
        html += f'<h2 class="text-xl font-bold text-gray-800">📱 {len(items_to_show)} Scheduled Posts</h2>'
        
        # Show ALL posts, not just a sample
        for idx, post in enumerate(items_to_show):
            post_type = post.get('type', 'Post')
            post_date = post.get('date', f'Day {idx + 1}')
            caption = post.get('caption', post.get('content', 'Content preview...'))
            hashtags = post.get('hashtags', [])
            
            html += f"""
            <div class="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="font-bold text-gray-900">Post #{idx + 1} - {post_type}</h3>
                    <span class="text-sm text-gray-500">{post_date}</span>
                </div>
                <p class="text-sm text-gray-700 mb-2">{caption[:150]}...</p>
            """
            
            if hashtags:
                hashtag_str = ' '.join(hashtags) if isinstance(hashtags, list) else str(hashtags)
                html += f'<div class="text-xs text-blue-600">{hashtag_str[:100]}</div>'
            
            html += '</div>'
        
        html += '</div>'
    else:
        # Fallback to generic calendar view
        html += """
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                <h3 class="font-bold text-gray-900 mb-2">📝 Week 1</h3>
                <p class="text-sm text-gray-600">Foundation content</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
                <h3 class="font-bold text-gray-900 mb-2">🎯 Week 2</h3>
                <p class="text-sm text-gray-600">Engagement focus</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
                <h3 class="font-bold text-gray-900 mb-2">🚀 Week 3</h3>
                <p class="text-sm text-gray-600">Growth content</p>
            </div>
        </div>
        """
    
    html += """
        <div class="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
            <h2 class="text-xl font-bold text-yellow-900 mb-4">💡 Implementation Guidelines</h2>
            <p class="text-yellow-800">Follow the structured approach for optimal engagement and growth.</p>
        </div>
    </div>
    """
    
    return html

def generate_workflow_preview(content: Dict[str, Any]) -> str:
    """Generate a preview for workflow content"""
    return f"""
    <div class="space-y-6">
        <div class="bg-indigo-50 p-6 rounded-lg border border-indigo-200">
            <h1 class="text-2xl font-bold text-indigo-900 mb-3">⚙️ Automation Workflow</h1>
            <p class="text-indigo-700">Streamlined process for campaign execution and optimization</p>
        </div>
        
        <div class="space-y-4">
            <div class="bg-white p-6 rounded-lg shadow border-l-4 border-indigo-500">
                <h3 class="text-lg font-bold text-gray-900 mb-3">🔄 Workflow Steps</h3>
                <ol class="space-y-2">
                    <li class="flex items-start"><span class="bg-indigo-100 text-indigo-800 font-bold text-sm px-2 py-1 rounded mr-3">1</span><span>Campaign Brief & Goal Setting</span></li>
                    <li class="flex items-start"><span class="bg-indigo-100 text-indigo-800 font-bold text-sm px-2 py-1 rounded mr-3">2</span><span>Content Creation & Approval</span></li>
                    <li class="flex items-start"><span class="bg-indigo-100 text-indigo-800 font-bold text-sm px-2 py-1 rounded mr-3">3</span><span>Automated Publishing</span></li>
                    <li class="flex items-start"><span class="bg-indigo-100 text-indigo-800 font-bold text-sm px-2 py-1 rounded mr-3">4</span><span>Performance Monitoring</span></li>
                </ol>
            </div>
        </div>
    </div>
    """

def generate_generic_preview(content: Dict[str, Any], title: str) -> str:
    """Generate a generic preview for any content"""
    return f"""
    <div class="space-y-6">
        <div class="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h1 class="text-2xl font-bold text-gray-900 mb-3">📋 {title}</h1>
            <p class="text-gray-700">Structured content analysis and insights</p>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
            <h2 class="text-xl font-bold text-gray-900 mb-4">📊 Content Overview</h2>
            <p class="text-gray-600">This content contains structured data that will be beautifully formatted by AI processing.</p>
        </div>
    </div>
    """