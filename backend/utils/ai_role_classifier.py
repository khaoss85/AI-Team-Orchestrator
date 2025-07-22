# utils/ai_role_classifier.py
"""
AI-Driven Role Classification System
Replaces hard-coded keyword matching with semantic understanding
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class RoleType(Enum):
    MANAGER = "manager"
    SPECIALIST = "specialist" 
    ANALYST = "analyst"
    COORDINATOR = "coordinator"
    CREATOR = "creator"
    OTHER = "other"

class SkillCategory(Enum):
    MANAGEMENT = "management"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    IMPLEMENTATION = "implementation"

async def classify_agent_role_ai(role_description: str, skills: List[str] = None) -> Dict[str, Any]:
    """
    Classify agent role using AI semantic understanding instead of keyword matching.
    
    Replaces hard-coded keyword lists with AI-driven classification.
    """
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        skills_text = ", ".join(skills) if skills else "No specific skills listed"
        
        prompt = f"""Analyze this agent role and classify it semantically:

Role Description: "{role_description}"
Skills: {skills_text}

Classify into these dimensions:

1. PRIMARY ROLE TYPE (choose one):
   - manager: Oversees, coordinates, plans, leads teams or processes
   - specialist: Deep expertise in specific technical or domain area
   - analyst: Analyzes data, information, trends, or situations  
   - coordinator: Facilitates, organizes, manages workflows/handoffs
   - creator: Produces content, designs, develops deliverables
   - other: Doesn't fit above categories clearly

2. SKILL CATEGORIES (can select multiple):
   - management: Leadership, planning, oversight, resource allocation
   - technical: Programming, tools, systems, technical implementation
   - creative: Design, content creation, ideation, artistic work
   - analytical: Data analysis, research, evaluation, insights
   - communication: Writing, presentation, stakeholder engagement
   - research: Information gathering, investigation, fact-finding
   - implementation: Execution, deployment, operational work

3. SENIORITY LEVEL (choose one):
   - junior: Entry level, requires guidance, handles routine tasks
   - senior: Experienced, independent, handles complex challenges
   - expert: Deep expertise, mentors others, strategic decisions

4. COMPLEXITY SCORE (0-10):
   Based on role complexity, required expertise, and decision-making level.

Return a JSON object:
{{
    "primary_role": "manager|specialist|analyst|coordinator|creator|other",
    "skill_categories": ["category1", "category2", ...],
    "seniority": "junior|senior|expert", 
    "complexity_score": 7,
    "confidence": 0.85,
    "reasoning": "Brief explanation of classification"
}}"""

        evaluator_agent = {
            "name": "RoleClassifierAgent",
            "model": "gpt-4o-mini",
            "instructions": "You are an expert HR analyst who classifies professional roles based on semantic understanding."
        }

        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=evaluator_agent,
            prompt=prompt,
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        if response and isinstance(response, dict):
            content = response.get('content', response)
            if isinstance(content, str):
                import json
                content = json.loads(content)
            
            # Validate and normalize response
            return {
                "primary_role": content.get("primary_role", "other"),
                "skill_categories": content.get("skill_categories", []),
                "seniority": content.get("seniority", "senior"),
                "complexity_score": min(10, max(0, content.get("complexity_score", 5))),
                "confidence": min(1.0, max(0.0, content.get("confidence", 0.8))),
                "reasoning": content.get("reasoning", "AI classification completed"),
                "classification_method": "ai_semantic"
            }
        
        return _fallback_role_classification(role_description, skills)
        
    except Exception as e:
        logger.error(f"❌ AI role classification failed: {e}")
        return _fallback_role_classification(role_description, skills)


def _fallback_role_classification(role_description: str, skills: List[str] = None) -> Dict[str, Any]:
    """Improved fallback classification (better than hard-coded keywords)."""
    role_lower = role_description.lower()
    
    # Use semantic patterns instead of exact keywords
    management_patterns = ["manag", "lead", "coordin", "oversee", "supervis", "direct"]
    technical_patterns = ["develop", "engineer", "code", "system", "technical", "architect"]
    analytical_patterns = ["analy", "research", "data", "insight", "evaluat", "assess"]
    creative_patterns = ["design", "creat", "content", "write", "visual", "brand"]
    
    # Count pattern matches for more nuanced classification
    mgmt_score = sum(1 for pattern in management_patterns if pattern in role_lower)
    tech_score = sum(1 for pattern in technical_patterns if pattern in role_lower) 
    analytical_score = sum(1 for pattern in analytical_patterns if pattern in role_lower)
    creative_score = sum(1 for pattern in creative_patterns if pattern in role_lower)
    
    # Determine primary role based on highest score
    scores = {
        "manager": mgmt_score,
        "specialist": tech_score,
        "analyst": analytical_score, 
        "creator": creative_score
    }
    
    primary_role = max(scores, key=scores.get) if max(scores.values()) > 0 else "other"
    
    # Estimate complexity based on role indicators
    complexity_indicators = ["senior", "expert", "lead", "principal", "architect", "head", "chief"]
    complexity_score = 5 + sum(2 for indicator in complexity_indicators if indicator in role_lower)
    complexity_score = min(10, complexity_score)
    
    # Determine seniority
    if any(term in role_lower for term in ["senior", "lead", "principal", "expert", "architect"]):
        seniority = "expert"
    elif any(term in role_lower for term in ["junior", "entry", "assistant", "trainee"]):
        seniority = "junior"  
    else:
        seniority = "senior"
    
    return {
        "primary_role": primary_role,
        "skill_categories": _infer_skill_categories(role_lower, scores),
        "seniority": seniority,
        "complexity_score": complexity_score,
        "confidence": 0.6,  # Lower confidence for fallback
        "reasoning": f"Fallback pattern matching - strongest pattern: {primary_role}",
        "classification_method": "pattern_fallback"
    }


def _infer_skill_categories(role_lower: str, scores: Dict[str, int]) -> List[str]:
    """Infer skill categories from role analysis."""
    categories = []
    
    if scores["manager"] > 0:
        categories.append("management")
    if scores["specialist"] > 0:
        categories.append("technical")
    if scores["analyst"] > 0:
        categories.append("analytical") 
    if scores["creator"] > 0:
        categories.append("creative")
    
    # Add communication if role involves stakeholder interaction
    if any(term in role_lower for term in ["communication", "stakeholder", "client", "customer"]):
        categories.append("communication")
        
    # Add research if role involves investigation
    if any(term in role_lower for term in ["research", "investigate", "discover", "explore"]):
        categories.append("research")
    
    return categories if categories else ["implementation"]  # Default fallback


async def check_role_similarity_ai(role1: str, role2: str) -> float:
    """
    Check semantic similarity between two roles using AI.
    Replaces simple keyword matching with semantic understanding.
    """
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        prompt = f"""Compare the semantic similarity of these two professional roles on a scale from 0.0 to 1.0:

Role 1: "{role1}"
Role 2: "{role2}"

Consider:
- Same core function/purpose (0.8-1.0)
- Same domain but different level (0.6-0.8) 
- Related skills/responsibilities (0.4-0.6)
- Different domains but transferable skills (0.2-0.4)
- Completely different roles (0.0-0.2)

Examples:
- "Senior Marketing Manager" vs "Marketing Manager" = 0.9
- "Content Writer" vs "Content Specialist" = 0.8  
- "Data Analyst" vs "Marketing Analyst" = 0.6
- "Software Engineer" vs "Web Developer" = 0.5
- "Accountant" vs "Graphic Designer" = 0.1

Return only the numeric similarity score (0.0 to 1.0):"""

        evaluator_agent = {
            "name": "RoleSimilarityAgent",
            "model": "gpt-4o-mini",
            "instructions": "Compare professional role similarity. Return only numeric score."
        }

        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=evaluator_agent,
            prompt=prompt,
            max_tokens=50,
            temperature=0.1
        )
        
        if response and isinstance(response, dict):
            content = response.get('content', '').strip()
            try:
                similarity = float(content)
                return max(0.0, min(1.0, similarity))
            except ValueError:
                pass
        
        return 0.3  # Default moderate similarity
        
    except Exception as e:
        logger.error(f"❌ AI role similarity failed: {e}")
        return 0.3


async def ai_skill_complexity_analysis(skills: List[str], domain_context: str = None) -> Dict[str, Any]:
    """
    Analyze skill complexity using AI instead of hard-coded patterns.
    """
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        skills_text = ", ".join(skills)
        context_text = f"Domain: {domain_context}" if domain_context else "No specific domain context"
        
        prompt = f"""Analyze the complexity and categorization of these professional skills:

Skills: {skills_text}
{context_text}

Provide analysis in these dimensions:

1. OVERALL COMPLEXITY SCORE (1-10):
   - 1-3: Basic/routine skills, minimal training required
   - 4-6: Intermediate skills, moderate experience needed  
   - 7-8: Advanced skills, significant expertise required
   - 9-10: Expert-level skills, deep specialization/years of experience

2. SKILL CATEGORIES (select applicable):
   - strategic: High-level planning, business strategy
   - technical: Programming, tools, systems, technical implementation
   - analytical: Data analysis, research, critical thinking
   - creative: Design, content creation, innovation
   - interpersonal: Communication, leadership, collaboration
   - operational: Process execution, workflow management

3. LEARNING CURVE (estimate months to proficiency):
   - Based on typical time to become proficient in these skills

4. MARKET RARITY (1-10):
   - How rare/specialized these skills are in the job market

Return JSON:
{{
    "complexity_score": 7,
    "skill_categories": ["technical", "analytical"],
    "learning_curve_months": 12,
    "market_rarity": 6,
    "reasoning": "Brief analysis explanation"
}}"""

        evaluator_agent = {
            "name": "SkillAnalyzer",
            "model": "gpt-4o-mini",
            "instructions": "Analyze professional skills complexity and categorization."
        }

        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=evaluator_agent,
            prompt=prompt,
            max_tokens=400,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        if response and isinstance(response, dict):
            content = response.get('content', response)
            if isinstance(content, str):
                import json
                content = json.loads(content)
            
            return {
                "complexity_score": min(10, max(1, content.get("complexity_score", 5))),
                "skill_categories": content.get("skill_categories", []),
                "learning_curve_months": max(1, content.get("learning_curve_months", 6)),
                "market_rarity": min(10, max(1, content.get("market_rarity", 5))),
                "reasoning": content.get("reasoning", "AI skill analysis completed"),
                "analysis_method": "ai_semantic"
            }
        
        return _fallback_skill_analysis(skills)
        
    except Exception as e:
        logger.error(f"❌ AI skill analysis failed: {e}")
        return _fallback_skill_analysis(skills)


def _fallback_skill_analysis(skills: List[str]) -> Dict[str, Any]:
    """Fallback skill analysis using improved heuristics."""
    if not skills:
        return {
            "complexity_score": 3,
            "skill_categories": ["operational"],
            "learning_curve_months": 3,
            "market_rarity": 3,
            "reasoning": "No skills provided - default values",
            "analysis_method": "fallback_default"
        }
    
    # Count complexity indicators
    high_complexity_terms = ["architect", "senior", "lead", "expert", "strategic", "machine learning", "ai", "blockchain"]
    mid_complexity_terms = ["analyst", "developer", "manager", "specialist", "advanced"]
    
    skills_text = " ".join(skills).lower()
    
    high_count = sum(1 for term in high_complexity_terms if term in skills_text)
    mid_count = sum(1 for term in mid_complexity_terms if term in skills_text)
    
    # Calculate complexity score
    base_complexity = 3
    complexity_score = base_complexity + (high_count * 2) + mid_count
    complexity_score = min(10, complexity_score)
    
    return {
        "complexity_score": complexity_score,
        "skill_categories": ["technical"] if any("technical" in skill.lower() for skill in skills) else ["operational"],
        "learning_curve_months": complexity_score * 2,
        "market_rarity": min(8, complexity_score),
        "reasoning": f"Pattern-based analysis - complexity indicators found: {high_count + mid_count}",
        "analysis_method": "pattern_fallback"
    }