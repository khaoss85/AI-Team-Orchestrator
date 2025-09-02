"""
AI Domain Classifier Service
Pillar 3 Compliance: Domain-agnostic project classification

This service replaces hard-coded domain detection with AI-driven semantic analysis,
enabling the system to work with ANY business domain, not just B2B/Content/Technical.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIDomainClassifier:
    """AI-driven domain classification for true domain agnosticism"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.enabled = os.getenv("DOMAIN_DETECTION_METHOD", "keywords") == "ai"
        logger.info(f"🤖 AI Domain Classifier initialized - Method: {os.getenv('DOMAIN_DETECTION_METHOD', 'keywords')}")
    
    async def classify_project_domain(self, goal: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Classify project domain using AI semantic understanding
        
        Args:
            goal: Project goal description
            context: Additional context (budget, requirements, etc.)
            
        Returns:
            {
                "primary_domain": "learning_education",  # domain identified
                "confidence": 0.95,                      # 0.0-1.0 confidence
                "required_specialists": ["Educator", "Curriculum Designer", "Assessment Specialist"],
                "reasoning": "Project focuses on educational content creation...",
                "domain_scores": {                       # All domain scores
                    "learning_education": 0.95,
                    "financial_research": 0.05,
                    "healthcare": 0.02,
                    # ... other domains
                }
            }
        """
        if not self.enabled:
            logger.debug("🔧 AI Domain Classification disabled, returning None")
            return None
            
        try:
            prompt = f"""
Analyze this project goal and classify its business domain using semantic understanding:

PROJECT GOAL: {goal}
CONTEXT: {json.dumps(context or {})}

You must provide comprehensive domain classification that works for ANY business sector.
Consider these domains (but don't limit yourself to only these):

EDUCATION & LEARNING:
- Online courses, curriculum development, educational platforms
- Training programs, skill development, certification systems
- Academic research, educational content creation

FINANCIAL & INVESTMENT:
- Market analysis, investment research, financial planning
- Risk assessment, portfolio management, ESG analysis
- Banking solutions, fintech development, regulatory compliance

HEALTHCARE & MEDICAL:
- Patient engagement, telemedicine, health platforms
- Medical research, clinical trials, health analytics
- Pharmaceutical, medical device development, compliance

LEGAL & COMPLIANCE:
- Regulatory frameworks, legal research, compliance audits
- Contract analysis, intellectual property, data privacy
- Legal technology, case management, documentation

E-COMMERCE & RETAIL:
- Online marketplaces, product catalogs, customer experience
- Supply chain, inventory management, loyalty programs
- Retail analytics, pricing strategies, merchandising

CREATIVE & DESIGN:
- Brand identity, visual design, creative campaigns
- Content production, artistic projects, media creation
- User experience design, creative direction

MANUFACTURING & OPERATIONS:
- Process optimization, quality control, supply chain
- Industrial automation, production planning, logistics
- Operational efficiency, cost reduction, lean processes

TECHNOLOGY & DEVELOPMENT:
- Software development, app creation, platform building
- System integration, technical architecture, APIs
- DevOps, cybersecurity, data infrastructure

B2B SALES & MARKETING:
- Lead generation, contact building, sales processes
- B2B marketing, account-based marketing, CRM systems
- Sales enablement, proposal development, client acquisition

CONTENT & SOCIAL MEDIA:
- Social media strategy, content marketing, influencer campaigns
- Brand storytelling, community management, digital presence
- Content creation, editorial calendars, engagement strategies

SUSTAINABILITY & ENVIRONMENT:
- Environmental impact, carbon tracking, sustainability reporting
- Green technology, renewable energy, circular economy
- ESG implementation, environmental compliance

Return JSON with this exact structure:
{{
    "primary_domain": "domain_name_here",
    "confidence": 0.0-1.0,
    "required_specialists": ["Specialist Role 1", "Specialist Role 2", "Specialist Role 3"],
    "reasoning": "Clear explanation of why this domain was selected based on project goals",
    "domain_scores": {{
        "learning_education": 0.0-1.0,
        "financial_research": 0.0-1.0,
        "healthcare": 0.0-1.0,
        "legal_compliance": 0.0-1.0,
        "ecommerce_retail": 0.0-1.0,
        "creative_design": 0.0-1.0,
        "manufacturing_operations": 0.0-1.0,
        "technology_development": 0.0-1.0,
        "b2b_sales": 0.0-1.0,
        "content_marketing": 0.0-1.0,
        "sustainability": 0.0-1.0
    }}
}}

IMPORTANT: Be domain-agnostic - support ANY industry or business type. 
If the project doesn't fit common categories, create appropriate domain names.
Focus on SEMANTIC understanding, not just keyword matching.
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a domain classification expert with deep understanding of business sectors. Provide accurate, semantic-based domain classification."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            required_keys = ["primary_domain", "confidence", "required_specialists", "reasoning", "domain_scores"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"AI response missing required keys: {required_keys}")
            
            logger.info(f"🎯 AI Domain Classification: {result['primary_domain']} (confidence: {result['confidence']:.2f})")
            logger.debug(f"📋 Reasoning: {result['reasoning']}")
            logger.debug(f"👥 Specialists: {result['required_specialists']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI domain classification failed: {e}")
            return None
    
    async def get_domain_specialists(self, domain: str, team_size: int, budget: float) -> List[Dict[str, Any]]:
        """
        Generate domain-specific specialist agent configurations
        
        Args:
            domain: Primary domain identified by classify_project_domain
            team_size: Number of specialists needed (excluding project manager)
            budget: Available budget for cost optimization
            
        Returns:
            List of agent specifications with roles, descriptions, prompts, tools
        """
        if not self.enabled:
            logger.debug("🔧 AI Specialist Generation disabled, returning empty list")
            return []
            
        try:
            prompt = f"""
Create {team_size} specialist agent configurations for the {domain} domain.
Budget available: €{budget:,.0f}

Generate agents with these specifications:
- role: Clear, specific role title
- seniority: "junior", "senior", or "expert" based on complexity
- description: 1-2 sentence role description
- system_prompt: Detailed AI assistant prompt (2-3 paragraphs)
- skills: List of key competencies
- tools_needed: List of tool types needed

Prioritize specialists that are ESSENTIAL for {domain} projects.
Make roles specific and actionable, not generic.

Example for learning_education domain:
{{
    "role": "Curriculum Designer",
    "seniority": "senior",
    "description": "Designs comprehensive learning curricula with clear objectives and assessment strategies.",
    "system_prompt": "You are a Curriculum Designer specializing in creating effective learning experiences...",
    "skills": ["instructional design", "learning objectives", "assessment strategies"],
    "tools_needed": ["content_creation", "research", "educational_frameworks"]
}}

Return JSON array of {team_size} specialist configurations.
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in organizational design and specialist role creation across all business domains."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            specialists = result.get("specialists", [])
            
            logger.info(f"🎯 Generated {len(specialists)} domain specialists for {domain}")
            logger.debug(f"👥 Specialist roles: {[s.get('role', 'Unknown') for s in specialists]}")
            
            return specialists
            
        except Exception as e:
            logger.error(f"❌ AI specialist generation failed: {e}")
            return []

# Singleton instance
ai_domain_classifier = AIDomainClassifier()

# Fallback domain detection using configurable keywords
def detect_domain_keywords(goal_text: str) -> Dict[str, bool]:
    """
    Configurable keyword-based domain detection as fallback
    Uses environment variables for keyword configuration
    """
    goal_lower = goal_text.lower()
    
    # Get keywords from environment (with sensible defaults)
    b2b_keywords = os.getenv("B2B_DETECTION_KEYWORDS", "b2b,sales,lead,crm,hubspot,outbound,prospect,icp,cmo,cto,saas,contatti,sequenze").split(",")
    content_keywords = os.getenv("CONTENT_DETECTION_KEYWORDS", "instagram,tiktok,social,media,posts,stories,reels,influencer,content,marketing").split(",")
    technical_keywords = os.getenv("TECHNICAL_DETECTION_KEYWORDS", "development,coding,app,website,api,software,backend,frontend,database").split(",")
    learning_keywords = os.getenv("LEARNING_DETECTION_KEYWORDS", "course,curriculum,education,learning,training,teaching,academic,skill").split(",")
    finance_keywords = os.getenv("FINANCE_DETECTION_KEYWORDS", "investment,financial,market,analysis,esg,portfolio,risk,banking,fintech").split(",")
    healthcare_keywords = os.getenv("HEALTHCARE_DETECTION_KEYWORDS", "patient,medical,healthcare,telemedicine,clinical,pharmaceutical,health,wellness").split(",")
    legal_keywords = os.getenv("LEGAL_DETECTION_KEYWORDS", "legal,compliance,regulatory,gdpr,audit,contract,intellectual,privacy,law").split(",")
    
    # Use configured keywords instead of hard-coded ones
    is_b2b = any(keyword.strip().lower() in goal_lower for keyword in b2b_keywords)
    is_content = any(keyword.strip().lower() in goal_lower for keyword in content_keywords) and not is_b2b
    is_technical = any(keyword.strip().lower() in goal_lower for keyword in technical_keywords)
    is_learning = any(keyword.strip().lower() in goal_lower for keyword in learning_keywords)
    is_finance = any(keyword.strip().lower() in goal_lower for keyword in finance_keywords)
    is_healthcare = any(keyword.strip().lower() in goal_lower for keyword in healthcare_keywords)
    is_legal = any(keyword.strip().lower() in goal_lower for keyword in legal_keywords)
    
    return {
        "is_b2b_lead_gen": is_b2b,
        "is_content_marketing": is_content,
        "is_technical": is_technical,
        "is_learning_education": is_learning,
        "is_financial_research": is_finance,
        "is_healthcare": is_healthcare,
        "is_legal_compliance": is_legal
    }

# Enhanced domain detection with AI fallback
async def detect_project_domain(goal_text: str, budget: float = 5000.0) -> Dict[str, Any]:
    """
    Enhanced domain detection with AI fallback
    
    Returns:
        {
            "detection_method": "ai" | "keywords",
            "primary_domain": "domain_name",
            "confidence": 0.0-1.0,
            "domain_flags": {boolean flags for backward compatibility},
            "ai_result": {...} if AI was used,
            "specialists_suggested": [...] if available
        }
    """
    
    # Try AI classification first if enabled
    if os.getenv("DOMAIN_DETECTION_METHOD", "keywords") == "ai":
        try:
            ai_result = await ai_domain_classifier.classify_project_domain(
                goal_text, 
                {"budget": budget}
            )
            
            if ai_result and ai_result.get("confidence", 0) > float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.7")):
                # Map AI domains to boolean flags for backward compatibility
                domain = ai_result["primary_domain"].lower()
                
                domain_flags = {
                    "is_b2b_lead_gen": "b2b" in domain or "sales" in domain,
                    "is_content_marketing": "content" in domain or "social" in domain,
                    "is_technical": "tech" in domain or "development" in domain,
                    "is_learning_education": "learning" in domain or "education" in domain,
                    "is_financial_research": "financial" in domain or "investment" in domain,
                    "is_healthcare": "healthcare" in domain or "medical" in domain,
                    "is_legal_compliance": "legal" in domain or "compliance" in domain
                }
                
                return {
                    "detection_method": "ai",
                    "primary_domain": ai_result["primary_domain"],
                    "confidence": ai_result["confidence"],
                    "domain_flags": domain_flags,
                    "ai_result": ai_result,
                    "specialists_suggested": ai_result.get("required_specialists", [])
                }
                
        except Exception as e:
            logger.warning(f"AI classification failed, falling back to keywords: {e}")
    
    # Fallback to keyword detection
    domain_flags = detect_domain_keywords(goal_text)
    
    # Determine primary domain from flags
    primary_domain = "general"
    if domain_flags["is_b2b_lead_gen"]:
        primary_domain = "b2b_sales"
    elif domain_flags["is_content_marketing"]:
        primary_domain = "content_marketing"
    elif domain_flags["is_technical"]:
        primary_domain = "technology_development"
    elif domain_flags["is_learning_education"]:
        primary_domain = "learning_education"
    elif domain_flags["is_financial_research"]:
        primary_domain = "financial_research"
    elif domain_flags["is_healthcare"]:
        primary_domain = "healthcare"
    elif domain_flags["is_legal_compliance"]:
        primary_domain = "legal_compliance"
    
    return {
        "detection_method": "keywords",
        "primary_domain": primary_domain,
        "confidence": 0.8,  # Assume high confidence for keyword matches
        "domain_flags": domain_flags,
        "ai_result": None,
        "specialists_suggested": []
    }