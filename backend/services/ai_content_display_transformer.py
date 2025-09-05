#!/usr/bin/env python3
"""
🎨 AI Content Display Transformer
Transforms raw JSON deliverable content into user-friendly HTML/Markdown format

Pillar Compliance:
- 1-3: Uses OpenAI AsyncOpenAI SDK natively
- 4-6: No hard-coded patterns, AI-driven transformation
- 7-9: Domain agnostic, works with any business content
- 10-12: Real tool usage, semantic understanding
- 13-15: Performance optimized with async processing and rate limiting
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class ContentTransformationResult:
    """Result of content transformation"""
    transformed_content: str
    original_format: str
    display_format: str  # 'html' or 'markdown'
    transformation_confidence: float  # 0-100
    processing_time: float
    fallback_used: bool
    metadata: Dict[str, Any]

class AIContentDisplayTransformer:
    """
    🎨 AI-driven content transformer for user-friendly display
    Converts raw JSON execution format to beautiful HTML/Markdown
    """
    
    def __init__(self):
        self.rate_limiter = None
        self._initialize_rate_limiter()
        
    def _initialize_rate_limiter(self):
        """Initialize rate limiter for OpenAI calls"""
        try:
            from services.api_rate_limiter import api_rate_limiter
            self.rate_limiter = api_rate_limiter
        except ImportError:
            logger.warning("Rate limiter not available, proceeding without it")
    
    async def transform_to_display_format(
        self, 
        content: Union[Dict[str, Any], str],
        display_format: str = 'html',
        business_context: Optional[Dict[str, Any]] = None
    ) -> ContentTransformationResult:
        """
        🎨 Transform content to user-friendly display format
        
        Args:
            content: Raw JSON content or string from deliverable
            display_format: 'html' or 'markdown'
            business_context: Optional context for better transformation
            
        Returns:
            ContentTransformationResult with transformed content
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🎨 Starting AI content transformation to {display_format} format...")
            
            # Step 1: Analyze content structure
            content_analysis = await self._analyze_content_structure(content)
            
            # Step 2: AI-driven transformation
            transformed_content = await self._ai_transform_content(
                content, 
                display_format,
                content_analysis,
                business_context
            )
            
            # Step 3: Post-process and validate
            final_content = await self._post_process_content(
                transformed_content, 
                display_format
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ContentTransformationResult(
                transformed_content=final_content,
                original_format=content_analysis.get('detected_format', 'json'),
                display_format=display_format,
                transformation_confidence=content_analysis.get('confidence', 85.0),
                processing_time=processing_time,
                fallback_used=False,
                metadata={
                    'content_type': content_analysis.get('content_type', 'unknown'),
                    'structure_complexity': content_analysis.get('complexity', 'medium'),
                    'ai_transformation': True,
                    'processed_at': start_time.isoformat()
                }
            )
            
            logger.info(f"✅ Content transformation completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI transformation failed: {e}")
            return await self._fallback_transformation(
                content, display_format, start_time, str(e)
            )
    
    async def _analyze_content_structure(self, content: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        🔍 Analyze content structure for optimal transformation strategy
        """
        try:
            # Convert to dict if string
            if isinstance(content, str):
                try:
                    parsed_content = json.loads(content)
                    content_dict = parsed_content
                except json.JSONDecodeError:
                    content_dict = {"text_content": content}
            else:
                content_dict = content or {}
            
            # AI analysis of content structure
            analysis = await self._ai_analyze_structure(content_dict)
            
            return {
                'detected_format': 'json' if isinstance(content, dict) else 'text',
                'content_type': analysis.get('content_type', 'mixed'),
                'complexity': analysis.get('complexity', 'medium'),
                'key_elements': analysis.get('key_elements', []),
                'confidence': analysis.get('confidence', 75.0)
            }
            
        except Exception as e:
            logger.warning(f"Content structure analysis failed: {e}")
            return {
                'detected_format': 'unknown',
                'content_type': 'text',
                'complexity': 'low',
                'key_elements': [],
                'confidence': 30.0
            }
    
    async def _ai_analyze_structure(self, content_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        🧠 AI analysis of content structure
        """
        try:
            # FIX: Use quota-tracked client to ensure all API calls are monitored
            from utils.openai_client_factory import get_async_openai_client
            
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OpenAI API key not configured")
            
            client = get_async_openai_client()
            
            # Rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire("openai_gpt4", "normal")
            
            content_sample = json.dumps(content_dict, indent=2)[:1000]  # Limit for analysis
            
            analysis_prompt = f"""
Analyze this content structure to determine optimal display transformation strategy.

CONTENT TO ANALYZE:
{content_sample}

ANALYSIS REQUIREMENTS:
1. Identify the primary content type (email, contact_list, document, strategy, analysis, etc.)
2. Assess structural complexity (low/medium/high)
3. Identify key elements that need special formatting
4. Determine confidence level in analysis

Respond with JSON:
{{
    "content_type": "primary content type detected",
    "complexity": "low|medium|high", 
    "key_elements": ["list", "of", "important", "elements"],
    "confidence": 0-100,
    "transformation_hints": ["specific formatting suggestions"]
}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content structure analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.warning("AI analysis returned invalid JSON, using fallback")
                return self._fallback_analysis(content_dict)
                
        except Exception as e:
            logger.warning(f"AI structure analysis failed: {e}")
            return self._fallback_analysis(content_dict)
    
    async def _ai_transform_content(
        self, 
        content: Union[Dict[str, Any], str],
        display_format: str,
        content_analysis: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        🤖 AI-powered content transformation
        """
        try:
            # FIX: Use quota-tracked client to ensure all API calls are monitored
            from utils.openai_client_factory import get_async_openai_client
            
            client = get_async_openai_client()
            
            # Rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire("openai_gpt4", "normal")
            
            # Prepare content for transformation
            if isinstance(content, dict):
                content_str = json.dumps(content, indent=2)
            else:
                content_str = str(content)
            
            # Detect if content is already markdown
            is_already_markdown = False
            if isinstance(content, str) and (
                content.startswith('#') or 
                content.startswith('##') or
                content.startswith('###') or
                '**' in content or
                '- ' in content[:100]
            ):
                is_already_markdown = True
                logger.info("📝 Detected content is already in markdown format")
            
            # Context information
            context_info = ""
            if business_context:
                context_info = f"\nBUSINESS CONTEXT: {json.dumps(business_context, indent=2)}"
            
            content_type = content_analysis.get('content_type', 'mixed')
            transformation_hints = content_analysis.get('transformation_hints', [])
            
            # Adjust prompt based on whether content is already markdown
            if is_already_markdown:
                transform_prompt = f"""
Transform this markdown content into beautiful, professionally formatted {display_format.upper()}.

CONTENT TO TRANSFORM (already in markdown):
{content_str}

CONTENT TYPE: {content_type}
DISPLAY FORMAT: {display_format}
{context_info}

TRANSFORMATION REQUIREMENTS:
1. The content is ALREADY in markdown format - enhance it for professional display
2. If converting to HTML: Create rich, styled HTML with proper semantic tags
3. If keeping as markdown: Enhance formatting, add structure, improve readability
4. Make it visually appealing with proper hierarchy and spacing
5. Use tables for tabular data, lists for items, cards for sections
6. Add professional business styling appropriate for the content type
7. Preserve ALL actual business data and information

SPECIFIC ENHANCEMENTS:
- Convert markdown tables to beautiful HTML tables with styling
- Add semantic HTML5 tags (article, section, header, etc.) if HTML output
- Use proper heading hierarchy and formatting
- Add subtle visual enhancements (borders, backgrounds, spacing)
- Format code blocks, quotes, and lists beautifully
- Create a professional document that executives would appreciate

{"HTML" if display_format == "html" else "ENHANCED MARKDOWN"} OUTPUT ONLY - NO EXPLANATIONS:
"""
            else:
                transform_prompt = f"""
Transform this raw business content into beautiful, user-friendly {display_format.upper()} format.

CONTENT TO TRANSFORM:
{content_str}

CONTENT TYPE: {content_type}
DISPLAY FORMAT: {display_format}
{context_info}

TRANSFORMATION REQUIREMENTS:
1. Make it visually appealing and easy to read
2. Use appropriate {display_format} formatting (headings, lists, emphasis)
3. Preserve all important business information
4. Add structure and organization for clarity
5. Use professional business formatting style
6. Add icons/emojis sparingly for visual enhancement (only if appropriate)

SPECIFIC GUIDELINES:
- For emails: Show subject line prominently, format body nicely
- For contact lists: Create structured tables or lists
- For strategies: Use clear headings and bullet points  
- For reports: Add executive summary and structured sections
- Always preserve the actual business data/content

{"HTML" if display_format == "html" else "MARKDOWN"} OUTPUT ONLY - NO EXPLANATIONS:
"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert content formatter. Transform content to beautiful {display_format}. Return only the formatted content, no explanations."},
                    {"role": "user", "content": transform_prompt}
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            transformed = response.choices[0].message.content.strip()
            
            logger.info(f"✅ AI transformation completed: {len(transformed)} characters")
            return transformed
            
        except Exception as e:
            logger.error(f"AI transformation failed: {e}")
            raise e
    
    async def _post_process_content(self, content: str, display_format: str) -> str:
        """
        🔧 Post-process and validate transformed content
        """
        try:
            # Basic validation and cleanup
            if display_format == 'html':
                return self._validate_html_content(content)
            else:
                return self._validate_markdown_content(content)
                
        except Exception as e:
            logger.warning(f"Post-processing failed: {e}")
            return content  # Return as-is if post-processing fails
    
    def _validate_html_content(self, content: str) -> str:
        """Validate and clean HTML content"""
        # Ensure content is wrapped in proper HTML structure
        if not content.strip().startswith('<'):
            content = f"<div class='content'>{content}</div>"
        
        # Basic safety: remove any script tags for security
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        return content
    
    def _validate_markdown_content(self, content: str) -> str:
        """Validate and clean Markdown content"""
        # Ensure proper markdown structure
        if not content.startswith('#') and not content.startswith('**'):
            content = f"# Content\n\n{content}"
        
        return content
    
    async def _fallback_transformation(
        self, 
        content: Union[Dict[str, Any], str], 
        display_format: str,
        start_time: datetime,
        error_msg: str
    ) -> ContentTransformationResult:
        """
        🛡️ Fallback transformation when AI fails
        """
        try:
            logger.info("🛡️ Using fallback content transformation...")
            
            # Simple rule-based transformation
            if isinstance(content, dict):
                fallback_content = self._dict_to_display(content, display_format)
            else:
                fallback_content = self._text_to_display(str(content), display_format)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ContentTransformationResult(
                transformed_content=fallback_content,
                original_format='json' if isinstance(content, dict) else 'text',
                display_format=display_format,
                transformation_confidence=60.0,  # Lower confidence for fallback
                processing_time=processing_time,
                fallback_used=True,
                metadata={
                    'fallback_reason': error_msg,
                    'transformation_method': 'rule_based',
                    'processed_at': start_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Even fallback transformation failed: {e}")
            # Ultimate fallback - just return content as-is in basic format
            return ContentTransformationResult(
                transformed_content=str(content),
                original_format='unknown',
                display_format='text',
                transformation_confidence=10.0,
                processing_time=0.1,
                fallback_used=True,
                metadata={'error': str(e)}
            )
    
    def _dict_to_display(self, content_dict: Dict[str, Any], display_format: str) -> str:
        """Simple dict to display format conversion"""
        if display_format == 'html':
            return self._dict_to_html(content_dict)
        else:
            return self._dict_to_markdown(content_dict)
    
    def _dict_to_html(self, content_dict: Dict[str, Any]) -> str:
        """Convert dict to basic HTML"""
        # Special case: if dict has only one key and it's a string with markdown
        if len(content_dict) == 1:
            key = list(content_dict.keys())[0]
            value = content_dict[key]
            # Check for raw_content key or markdown content
            if (key == 'raw_content' or isinstance(value, str)) and isinstance(value, str) and (
                value.startswith('#') or value.startswith('##') or 
                '**' in value or '- ' in value[:100]
            ):
                # Convert markdown to HTML properly
                return self._markdown_to_html(value)
        
        html_parts = ['<div class="content">']
        
        for key, value in content_dict.items():
            # Skip the key header if it's "raw_content" - just process the content
            if key != 'raw_content':
                key_formatted = key.replace('_', ' ').title()
                html_parts.append(f'<h3>{key_formatted}</h3>')
            
            if isinstance(value, (list, tuple)):
                html_parts.append('<ul>')
                for item in value:
                    html_parts.append(f'<li>{str(item)}</li>')
                html_parts.append('</ul>')
            elif isinstance(value, dict):
                html_parts.append(self._dict_to_html(value))
            else:
                # Check if value is markdown string
                if isinstance(value, str) and (
                    value.startswith('#') or value.startswith('##') or
                    '**' in value or '- ' in value[:100]
                ):
                    html_parts.append(self._markdown_to_html(value))
                else:
                    html_parts.append(f'<p>{str(value)}</p>')
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to basic HTML"""
        html = markdown_text
        
        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Convert bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert lists
        lines = html.split('\n')
        in_list = False
        new_lines = []
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    new_lines.append('<ul>')
                    in_list = True
                new_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list and not line.strip().startswith('- '):
                    new_lines.append('</ul>')
                    in_list = False
                new_lines.append(line)
        if in_list:
            new_lines.append('</ul>')
        
        html = '\n'.join(new_lines)
        
        # Convert paragraphs
        html = re.sub(r'\n\n', '</p>\n<p>', html)
        if not html.startswith('<'):
            html = f'<p>{html}'
        if not html.endswith('>'):
            html = f'{html}</p>'
        
        return f'<div class="markdown-content">\n{html}\n</div>'
    
    def _dict_to_markdown(self, content_dict: Dict[str, Any]) -> str:
        """Convert dict to basic Markdown"""
        md_parts = []
        
        for key, value in content_dict.items():
            key_formatted = key.replace('_', ' ').title()
            md_parts.append(f'## {key_formatted}')
            md_parts.append('')
            
            if isinstance(value, (list, tuple)):
                for item in value:
                    md_parts.append(f'- {str(item)}')
            elif isinstance(value, dict):
                md_parts.append(self._dict_to_markdown(value))
            else:
                md_parts.append(str(value))
            
            md_parts.append('')
        
        return '\n'.join(md_parts)
    
    def _text_to_display(self, content_text: str, display_format: str) -> str:
        """Convert plain text to display format"""
        # Check if text is already markdown
        is_markdown = (
            content_text.startswith('#') or content_text.startswith('##') or
            '**' in content_text or '- ' in content_text[:100]
        )
        
        if display_format == 'html':
            if is_markdown:
                # Convert markdown to HTML
                return self._markdown_to_html(content_text)
            else:
                # Simple text to HTML conversion
                paragraphs = content_text.split('\n\n')
                html_paragraphs = [f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip()]
                return f'<div class="content">{"".join(html_paragraphs)}</div>'
        else:
            if is_markdown:
                # Already markdown, return as-is
                return content_text
            else:
                # Text is plain, add basic markdown formatting
                return f'# Content\n\n{content_text}'
    
    def _fallback_analysis(self, content_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback content analysis when AI fails"""
        # Simple rule-based analysis
        keys = list(content_dict.keys())
        
        content_type = 'document'
        if any(key in ['email', 'subject', 'body'] for key in keys):
            content_type = 'email'
        elif any(key in ['contacts', 'list', 'names'] for key in keys):
            content_type = 'contact_list'
        elif any(key in ['strategy', 'plan', 'phases'] for key in keys):
            content_type = 'strategy'
        
        complexity = 'low' if len(keys) <= 3 else 'medium' if len(keys) <= 8 else 'high'
        
        return {
            'content_type': content_type,
            'complexity': complexity,
            'key_elements': keys[:5],  # Top 5 keys
            'confidence': 40.0,  # Lower confidence for fallback
            'transformation_hints': [f'Focus on {content_type} formatting']
        }

# Global instance
ai_content_display_transformer = AIContentDisplayTransformer()

# Convenience functions for easy usage
async def transform_deliverable_to_html(
    content: Union[Dict[str, Any], str],
    business_context: Optional[Dict[str, Any]] = None
) -> ContentTransformationResult:
    """
    🎨 Transform deliverable content to HTML format
    """
    return await ai_content_display_transformer.transform_to_display_format(
        content, 'html', business_context
    )

async def transform_deliverable_to_markdown(
    content: Union[Dict[str, Any], str],
    business_context: Optional[Dict[str, Any]] = None
) -> ContentTransformationResult:
    """
    📝 Transform deliverable content to Markdown format
    """
    return await ai_content_display_transformer.transform_to_display_format(
        content, 'markdown', business_context
    )

# Export for easy import
__all__ = [
    "AIContentDisplayTransformer", 
    "ai_content_display_transformer", 
    "ContentTransformationResult",
    "transform_deliverable_to_html",
    "transform_deliverable_to_markdown"
]