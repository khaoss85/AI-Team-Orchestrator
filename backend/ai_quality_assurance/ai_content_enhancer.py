# backend/ai_quality_assurance/ai_content_enhancer.py

import logging
import json
import re
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AIContentEnhancer:
    """
    🤖 AI-DRIVEN UNIVERSAL CONTENT ENHANCER
    
    Transforms placeholder/generic content into business-ready, actionable content
    using workspace context and AI intelligence. Works across all business domains.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for content enhancement")
        else:
            self.ai_available = False
    
    async def enhance_content_for_business_use(
        self, 
        content: Dict[str, Any], 
        task_context: Dict[str, Any], 
        workspace_context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool]:
        """
        🤖 AI-DRIVEN CONTENT ENHANCEMENT
        
        Transforms generic/placeholder content into business-ready content
        using workspace context and task specifics.
        
        Returns:
            (enhanced_content, was_enhanced)
        """
        try:
            # 1. Check if content needs enhancement
            needs_enhancement = self._needs_enhancement(content)
            if not needs_enhancement:
                logger.debug("Content is already business-ready")
                return content, False
            
            # 2. Extract business context for enhancement
            business_context = await self._extract_business_context(
                task_context, workspace_context
            )
            
            # 3. Use AI to enhance content
            if self.ai_available:
                enhanced_content = await self._ai_enhance_content(
                    content, business_context
                )
                if enhanced_content:
                    logger.info("🤖 AI ENHANCED: Content transformed to business-ready")
                    return enhanced_content, True
            
            # 4. Fallback: Pattern-based enhancement
            enhanced_content = self._pattern_based_enhancement(
                content, business_context
            )
            
            if enhanced_content != content:
                logger.info("🔄 PATTERN ENHANCED: Content improved with business context")
                return enhanced_content, True
            
            return content, False
            
        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return content, False
    
    def _needs_enhancement(self, content: Dict[str, Any]) -> bool:
        """Check if content contains placeholders or generic elements"""
        
        content_str = json.dumps(content, default=str).lower()
        
        # 🚫 PLACEHOLDER PATTERNS
        placeholder_patterns = [
            r'\[.*?\]',  # [placeholder], [Product], [Company]
            r'\{.*?\}',  # {placeholder}, {firstName}, {company}
            r'<.*?>',    # <placeholder>
            r'your\s+(?:company|name|email|website|product)',
            r'insert\s+(?:here|your|data)',
            r'add\s+(?:your|data|information)',
            r'customize\s+(?:this|here)',
            r'fill\s+(?:in|out|this)',
            r'replace\s+(?:with|this)',
            r'example\s+(?:company|inc|ltd)',
            r'sample\s+(?:data|content)',
            r'lorem\s+ipsum',
        ]
        
        # Check for placeholder patterns
        for pattern in placeholder_patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                return True
        
        # Check for generic/fake content indicators
        generic_indicators = [
            'john doe', 'jane smith', 'example.com', 'acme corp',
            'lorem ipsum', 'placeholder', 'sample data',
            'test company', 'demo data', 'fake data'
        ]
        
        for indicator in generic_indicators:
            if indicator in content_str:
                return True
        
        return False
    
    async def _extract_business_context(
        self, 
        task_context: Dict[str, Any], 
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract real business context for content enhancement"""
        
        # Get workspace goal for context
        workspace_goal = workspace_context.get('goal', '')
        workspace_id = workspace_context.get('id', '')
        
        # Extract business details from goal text
        business_context = {
            'workspace_goal': workspace_goal,
            'workspace_id': workspace_id,
            'industry': self._extract_industry_from_goal(workspace_goal),
            'target_audience': self._extract_target_audience_from_goal(workspace_goal),
            'business_type': self._extract_business_type_from_goal(workspace_goal),
            'key_metrics': self._extract_key_metrics_from_goal(workspace_goal),
            'timeline': self._extract_timeline_from_goal(workspace_goal),
            'task_type': task_context.get('project_phase', 'IMPLEMENTATION')
        }
        
        # Add any additional context from task
        if task_context:
            business_context.update({
                'task_creation_type': task_context.get('creation_type', ''),
                'task_priority': task_context.get('priority', 'medium'),
                'delegation_context': task_context.get('delegation_chain', [])
            })
        
        return business_context
    
    def _extract_industry_from_goal(self, goal_text: str) -> str:
        """🌍 Universal industry extraction from goal text"""
        goal_lower = goal_text.lower()
        
        # Industry patterns
        if any(word in goal_lower for word in ['saas', 'software', 'tech', 'technology']):
            return 'Technology/SaaS'
        elif any(word in goal_lower for word in ['finance', 'financial', 'bank', 'investment']):
            return 'Financial Services'
        elif any(word in goal_lower for word in ['health', 'medical', 'healthcare', 'wellness']):
            return 'Healthcare'
        elif any(word in goal_lower for word in ['education', 'learning', 'training', 'course']):
            return 'Education'
        elif any(word in goal_lower for word in ['retail', 'ecommerce', 'shop', 'store']):
            return 'Retail/E-commerce'
        elif any(word in goal_lower for word in ['marketing', 'advertising', 'brand', 'campaign']):
            return 'Marketing/Advertising'
        else:
            return 'Business Services'
    
    def _extract_target_audience_from_goal(self, goal_text: str) -> str:
        """🎯 Extract target audience from goal text"""
        goal_lower = goal_text.lower()
        
        # Look for specific roles/titles
        roles = []
        if 'cmo' in goal_lower or 'chief marketing officer' in goal_lower:
            roles.append('CMO')
        if 'cto' in goal_lower or 'chief technology officer' in goal_lower:
            roles.append('CTO')
        if 'ceo' in goal_lower or 'chief executive officer' in goal_lower:
            roles.append('CEO')
        if 'cfo' in goal_lower or 'chief financial officer' in goal_lower:
            roles.append('CFO')
        
        if roles:
            return f"{'/'.join(roles)} executives"
        
        # Look for general audience indicators
        if any(word in goal_lower for word in ['decision maker', 'executive', 'manager']):
            return 'Business decision makers'
        elif any(word in goal_lower for word in ['professional', 'expert', 'specialist']):
            return 'Industry professionals'
        elif any(word in goal_lower for word in ['customer', 'client', 'user']):
            return 'End customers'
        else:
            return 'Business professionals'
    
    def _extract_business_type_from_goal(self, goal_text: str) -> str:
        """🏢 Extract business type from goal text"""
        goal_lower = goal_text.lower()
        
        if any(word in goal_lower for word in ['european', 'europe', 'eu']):
            return 'European companies'
        elif any(word in goal_lower for word in ['startup', 'scale-up']):
            return 'Startups/Scale-ups'
        elif any(word in goal_lower for word in ['enterprise', 'large', 'corporate']):
            return 'Enterprise companies'
        elif any(word in goal_lower for word in ['small', 'sme', 'medium']):
            return 'SME companies'
        else:
            return 'Mid-market companies'
    
    def _extract_key_metrics_from_goal(self, goal_text: str) -> List[str]:
        """📊 Extract key metrics from goal text"""
        metrics = []
        goal_lower = goal_text.lower()
        
        # Look for percentage metrics
        percent_matches = re.findall(r'(\d+)\s*%', goal_text)
        for match in percent_matches:
            if int(match) >= 20:  # Filter out small percentages
                metrics.append(f"{match}% target")
        
        # Look for count metrics
        count_matches = re.findall(r'(\d+)\s+(?:contatti|contacts|leads|email|sequence)', goal_lower)
        for match in count_matches:
            if int(match) >= 10:  # Filter out small counts
                metrics.append(f"{match} units target")
        
        # Look for specific metric types
        if 'open rate' in goal_lower or 'open-rate' in goal_lower:
            metrics.append('Email open rate optimization')
        if 'click rate' in goal_lower or 'ctr' in goal_lower:
            metrics.append('Click-through rate optimization')
        if 'conversion' in goal_lower:
            metrics.append('Conversion rate optimization')
        
        return metrics or ['Performance optimization']
    
    def _extract_timeline_from_goal(self, goal_text: str) -> str:
        """⏰ Extract timeline from goal text"""
        goal_lower = goal_text.lower()
        
        # Look for specific time periods
        week_matches = re.findall(r'(\d+)\s*(?:week|settiman)', goal_lower)
        if week_matches:
            weeks = max(int(w) for w in week_matches)
            return f"{weeks} weeks"
        
        month_matches = re.findall(r'(\d+)\s*(?:month|mes)', goal_lower)
        if month_matches:
            months = max(int(m) for m in month_matches)
            return f"{months} months"
        
        day_matches = re.findall(r'(\d+)\s*(?:day|giorn)', goal_lower)
        if day_matches:
            days = max(int(d) for d in day_matches)
            return f"{days} days"
        
        return "6-8 weeks"  # Default timeline
    
    async def _ai_enhance_content(
        self, 
        content: Dict[str, Any], 
        business_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """🤖 AI-powered content enhancement using business context"""
        
        if not self.ai_available:
            return None
        
        try:
            content_str = json.dumps(content, indent=2, default=str)
            
            enhancement_prompt = f"""Transform this generic/placeholder content into business-ready, actionable content using the provided business context.

BUSINESS CONTEXT:
- Industry: {business_context.get('industry', 'Business Services')}
- Target Audience: {business_context.get('target_audience', 'Business professionals')}
- Business Type: {business_context.get('business_type', 'Mid-market companies')}
- Key Metrics: {', '.join(business_context.get('key_metrics', ['Performance optimization']))}
- Timeline: {business_context.get('timeline', '6-8 weeks')}
- Project Goal: {business_context.get('workspace_goal', '')[:200]}

CONTENT TO ENHANCE:
{content_str}

ENHANCEMENT INSTRUCTIONS:
1. Replace ALL placeholders like [Product], [Company], {firstName} with realistic business examples
2. Replace generic company names (Acme Corp, Example Inc) with realistic industry-specific names
3. Replace generic email addresses with realistic business email patterns
4. Replace generic phone numbers with realistic business phone formats
5. Add specific, industry-relevant details that make the content immediately usable
6. Ensure all data is realistic but not referencing real companies (use realistic fictional names)
7. Make the content ready for immediate business use without further modification

Return ONLY the enhanced content as valid JSON in the same structure, with all placeholders replaced with realistic business data.

IMPORTANT: Keep the exact same JSON structure, only replace placeholder/generic content with realistic business-specific content."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business content specialist. Transform generic content into business-ready content using provided context. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": enhancement_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            enhanced_content_str = response.choices[0].message.content.strip()
            enhanced_content = json.loads(enhanced_content_str)
            
            # Validate enhancement
            if self._validate_enhancement(content, enhanced_content):
                return enhanced_content
            else:
                logger.warning("AI enhancement validation failed")
                return None
                
        except Exception as e:
            logger.error(f"AI enhancement error: {e}")
            return None
    
    def _validate_enhancement(
        self, 
        original: Dict[str, Any], 
        enhanced: Dict[str, Any]
    ) -> bool:
        """Validate that enhancement improved content without breaking structure"""
        
        try:
            # Check structure preservation
            def get_structure(obj, path=""):
                if isinstance(obj, dict):
                    return {k: get_structure(v, f"{path}.{k}") for k in obj.keys()}
                elif isinstance(obj, list):
                    return [get_structure(obj[0] if obj else {}, f"{path}[0]")]
                else:
                    return type(obj).__name__
            
            original_structure = get_structure(original)
            enhanced_structure = get_structure(enhanced)
            
            if original_structure != enhanced_structure:
                logger.warning("Enhancement changed content structure")
                return False
            
            # Check that placeholders were actually replaced
            original_str = json.dumps(original, default=str).lower()
            enhanced_str = json.dumps(enhanced, default=str).lower()
            
            placeholder_patterns = [r'\[.*?\]', r'\{.*?\}', 'placeholder', 'example', 'sample']
            
            original_placeholder_count = sum(
                len(re.findall(pattern, original_str)) for pattern in placeholder_patterns
            )
            enhanced_placeholder_count = sum(
                len(re.findall(pattern, enhanced_str)) for pattern in placeholder_patterns
            )
            
            if enhanced_placeholder_count >= original_placeholder_count:
                logger.warning("Enhancement didn't reduce placeholders")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Enhancement validation error: {e}")
            return False
    
    def _pattern_based_enhancement(
        self, 
        content: Dict[str, Any], 
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """🔄 Pattern-based content enhancement (fallback)"""
        
        try:
            enhanced = json.loads(json.dumps(content, default=str))  # Deep copy
            content_str = json.dumps(enhanced, default=str)
            
            # Get realistic business data based on context
            industry = business_context.get('industry', 'Business Services')
            target_audience = business_context.get('target_audience', 'Business professionals')
            
            # Industry-specific replacements
            if 'Technology/SaaS' in industry:
                replacements = {
                    r'\[Product\]': 'TechFlow CRM',
                    r'\[Company\]': 'TechFlow Solutions',
                    r'\{company\}': 'TechFlow Solutions',
                    r'\{product\}': 'TechFlow CRM',
                    r'example\.com': 'techflow.io',
                    r'your company': 'TechFlow Solutions',
                    r'your product': 'TechFlow CRM'
                }
            elif 'Financial' in industry:
                replacements = {
                    r'\[Product\]': 'FinanceMax Pro',
                    r'\[Company\]': 'FinanceMax Analytics',
                    r'\{company\}': 'FinanceMax Analytics',
                    r'\{product\}': 'FinanceMax Pro',
                    r'example\.com': 'financemax.com',
                    r'your company': 'FinanceMax Analytics',
                    r'your product': 'FinanceMax Pro'
                }
            else:
                replacements = {
                    r'\[Product\]': 'BusinessEdge Platform',
                    r'\[Company\]': 'BusinessEdge Solutions',
                    r'\{company\}': 'BusinessEdge Solutions',
                    r'\{product\}': 'BusinessEdge Platform',
                    r'example\.com': 'businessedge.com',
                    r'your company': 'BusinessEdge Solutions',
                    r'your product': 'BusinessEdge Platform'
                }
            
            # Apply replacements
            for pattern, replacement in replacements.items():
                content_str = re.sub(pattern, replacement, content_str, flags=re.IGNORECASE)
            
            # Convert back to dict
            try:
                enhanced = json.loads(content_str)
                return enhanced
            except json.JSONDecodeError:
                logger.warning("Pattern enhancement broke JSON structure")
                return content
                
        except Exception as e:
            logger.error(f"Pattern enhancement error: {e}")
            return content