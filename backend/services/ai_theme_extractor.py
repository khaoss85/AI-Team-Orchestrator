#!/usr/bin/env python3
"""
🎯 AI Theme Extractor Service
Groups related goals into business-friendly themes using pure AI semantic analysis

Pillar Compliance:
- ✅ Pillar 1: Uses OpenAI AsyncOpenAI SDK
- ✅ Pillar 2: No hard-coded theme names - pure AI generation
- ✅ Pillar 3: Domain agnostic semantic clustering
- ✅ Pillar 6: Integrates with workspace memory for pattern learning
- ✅ Pillar 7: Preserves goal-deliverable relationships
- ✅ Pillar 10: Provides explainability for groupings
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from uuid import uuid4

logger = logging.getLogger(__name__)

@dataclass
class ExtractedTheme:
    """AI-extracted theme with grouped goals"""
    theme_id: str
    name: str  # AI-generated, never hard-coded
    description: str  # AI-generated business context
    goal_ids: List[str]  # Preserved goal relationships
    deliverable_counts: Dict[str, int]  # Goal ID -> deliverable count
    confidence_score: float  # 0-100 confidence in grouping
    reasoning: str  # AI explanation for grouping
    business_value: str  # AI-identified business value
    suggested_icon: str  # AI-suggested emoji/icon
    extracted_at: str

@dataclass
class ThemeExtractionResult:
    """Result of theme extraction process"""
    themes: List[ExtractedTheme]
    ungrouped_goals: List[str]  # Goals that didn't fit themes
    extraction_confidence: float  # Overall confidence
    extraction_time: float
    fallback_used: bool
    user_locale: str
    extraction_reasoning: str  # Overall AI reasoning

class AIThemeExtractor:
    """
    🎯 Pure AI-driven theme extraction service
    NO hard-coded categories, templates, or industry-specific logic
    """
    
    def __init__(self):
        self.cache: Dict[str, Tuple[ThemeExtractionResult, datetime]] = {}
        self.cache_ttl = timedelta(minutes=5)  # 5-minute cache as per compliance
        self.rate_limiter = None
        self._initialize_rate_limiter()
        
    def _initialize_rate_limiter(self):
        """Initialize rate limiter for OpenAI calls"""
        try:
            from services.api_rate_limiter import api_rate_limiter
            self.rate_limiter = api_rate_limiter
            logger.info("✅ Rate limiter initialized for AIThemeExtractor")
        except ImportError:
            logger.warning("⚠️ Rate limiter not available, proceeding without it")
    
    async def extract_themes(
        self,
        goals: List[Dict[str, Any]],
        workspace_context: Optional[Dict[str, Any]] = None,
        user_locale: str = "en",
        min_confidence: float = 70.0
    ) -> ThemeExtractionResult:
        """
        🎯 Extract themes from goals using pure AI semantic analysis
        
        Args:
            goals: List of goal objects with descriptions
            workspace_context: Optional business context
            user_locale: User's language for theme naming
            min_confidence: Minimum confidence for theme creation
            
        Returns:
            ThemeExtractionResult with AI-generated themes
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = self._generate_cache_key(goals, workspace_context, user_locale)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info("✅ Using cached theme extraction")
            return cached_result
        
        try:
            logger.info(f"🎯 Starting AI theme extraction for {len(goals)} goals...")
            
            # Step 1: Prepare goal data for AI analysis
            goal_data = self._prepare_goal_data(goals)
            
            # Step 2: AI semantic analysis and clustering
            extraction_result = await self._ai_extract_themes(
                goal_data,
                workspace_context,
                user_locale,
                min_confidence
            )
            
            # Step 3: Post-process and validate
            final_result = await self._post_process_themes(
                extraction_result,
                goals,
                user_locale,
                start_time
            )
            
            # Cache the result
            self._cache_result(cache_key, final_result)
            
            # Store patterns in workspace memory if available
            await self._store_theme_patterns(final_result, workspace_context)
            
            logger.info(f"✅ Theme extraction completed: {len(final_result.themes)} themes")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Theme extraction failed: {e}")
            return await self._fallback_extraction(goals, user_locale, start_time, str(e))
    
    async def _ai_extract_themes(
        self,
        goal_data: List[Dict[str, Any]],
        workspace_context: Optional[Dict[str, Any]],
        user_locale: str,
        min_confidence: float
    ) -> Dict[str, Any]:
        """
        🤖 Core AI theme extraction using OpenAI
        
        CRITICAL: No hard-coded themes or templates!
        Everything must be AI-generated based on actual content.
        """
        try:
            # Import OpenAI client
            from openai import AsyncOpenAI
            import os
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Build dynamic prompt - NO TEMPLATES!
            prompt = self._build_extraction_prompt(goal_data, workspace_context, user_locale)
            
            # Apply rate limiting if available
            if self.rate_limiter:
                await self.rate_limiter.acquire()
            
            # Call OpenAI for semantic analysis
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a business analyst expert at identifying natural groupings.
                        You MUST create theme names that are:
                        1. Specific to the actual content (not generic categories)
                        2. Business-friendly and value-focused
                        3. In the user's language
                        4. Unique to this specific set of goals
                        
                        NEVER use generic categories like 'Marketing', 'Sales', 'Operations'.
                        Instead, create specific themes like 'Customer Acquisition Campaign Q1' or 'Product Launch Preparation'.
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistency
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate AI didn't use generic templates
            if self._contains_generic_themes(result):
                logger.warning("⚠️ AI returned generic themes, requesting more specific grouping")
                # Request more specific grouping
                result = await self._request_specific_themes(result, client, goal_data)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            raise
    
    def _build_extraction_prompt(
        self,
        goal_data: List[Dict[str, Any]],
        workspace_context: Optional[Dict[str, Any]],
        user_locale: str
    ) -> str:
        """Build prompt for AI theme extraction"""
        
        context_str = ""
        if workspace_context:
            context_str = f"\nBusiness Context: {json.dumps(workspace_context, indent=2)}"
        
        goals_str = json.dumps(goal_data, indent=2, ensure_ascii=False)
        
        return f"""Analyze these goals and group them into natural business themes.
        
Goals to analyze:
{goals_str}
{context_str}

User Language: {user_locale}

Create specific, value-focused themes that reflect the ACTUAL content.
Each theme should have:
1. A specific, descriptive name (not generic)
2. Clear business value statement
3. List of goal IDs that belong to it
4. Reasoning for the grouping
5. Suggested emoji that represents the theme

Return JSON with this structure:
{{
    "themes": [
        {{
            "name": "Specific theme name in {user_locale}",
            "description": "What this theme achieves",
            "goal_ids": ["goal1_id", "goal2_id"],
            "reasoning": "Why these goals belong together",
            "business_value": "The business value of this theme",
            "suggested_icon": "📊",
            "confidence": 85.0
        }}
    ],
    "ungrouped_goal_ids": ["goal3_id"],
    "overall_reasoning": "How you decided on these groupings"
}}

IMPORTANT: Create themes based on the ACTUAL content, not generic categories.
"""
    
    def _contains_generic_themes(self, result: Dict[str, Any]) -> bool:
        """Check if AI returned generic template-like themes"""
        generic_keywords = [
            "marketing", "sales", "operations", "finance", "hr",
            "development", "support", "general", "other", "misc"
        ]
        
        for theme in result.get("themes", []):
            theme_name_lower = theme.get("name", "").lower()
            if any(keyword in theme_name_lower for keyword in generic_keywords):
                if len(theme_name_lower.split()) <= 2:  # Single word or two-word generic
                    return True
        
        return False
    
    async def _request_specific_themes(
        self,
        generic_result: Dict[str, Any],
        client: Any,
        goal_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Request more specific themes if generic ones were returned"""
        
        refinement_prompt = f"""The themes you provided are too generic:
{json.dumps(generic_result['themes'], indent=2)}

Please create MORE SPECIFIC themes based on the actual goal content.
For example, instead of "Marketing", use "Q1 Social Media Engagement Campaign".
Instead of "Sales", use "Enterprise Client Acquisition Initiative".

Goals to reconsider:
{json.dumps(goal_data, indent=2)}

Provide specific, descriptive theme names that reflect the actual work being done.
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": refinement_prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _post_process_themes(
        self,
        extraction_result: Dict[str, Any],
        original_goals: List[Dict[str, Any]],
        user_locale: str,
        start_time: datetime
    ) -> ThemeExtractionResult:
        """Post-process and validate extracted themes"""
        
        themes = []
        goal_id_map = {g.get("id"): g for g in original_goals}
        
        for theme_data in extraction_result.get("themes", []):
            # Calculate deliverable counts for each goal in theme
            deliverable_counts = {}
            for goal_id in theme_data.get("goal_ids", []):
                if goal_id in goal_id_map:
                    goal = goal_id_map[goal_id]
                    deliverable_counts[goal_id] = goal.get("deliverable_count", 0)
            
            theme = ExtractedTheme(
                theme_id=str(uuid4()),
                name=theme_data.get("name", "Unnamed Theme"),
                description=theme_data.get("description", ""),
                goal_ids=theme_data.get("goal_ids", []),
                deliverable_counts=deliverable_counts,
                confidence_score=theme_data.get("confidence", 75.0),
                reasoning=theme_data.get("reasoning", ""),
                business_value=theme_data.get("business_value", ""),
                suggested_icon=theme_data.get("suggested_icon", "📁"),
                extracted_at=datetime.now().isoformat()
            )
            
            themes.append(theme)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ThemeExtractionResult(
            themes=themes,
            ungrouped_goals=extraction_result.get("ungrouped_goal_ids", []),
            extraction_confidence=sum(t.confidence_score for t in themes) / len(themes) if themes else 0,
            extraction_time=processing_time,
            fallback_used=False,
            user_locale=user_locale,
            extraction_reasoning=extraction_result.get("overall_reasoning", "")
        )
    
    async def _fallback_extraction(
        self,
        goals: List[Dict[str, Any]],
        user_locale: str,
        start_time: datetime,
        error_message: str
    ) -> ThemeExtractionResult:
        """
        Fallback extraction when AI fails
        Returns ungrouped goals rather than forcing bad groupings
        """
        logger.warning(f"⚠️ Using fallback extraction due to: {error_message}")
        
        # Don't create artificial groupings - just return ungrouped
        ungrouped_ids = [g.get("id") for g in goals if g.get("id")]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ThemeExtractionResult(
            themes=[],  # No themes in fallback
            ungrouped_goals=ungrouped_ids,
            extraction_confidence=0.0,
            extraction_time=processing_time,
            fallback_used=True,
            user_locale=user_locale,
            extraction_reasoning=f"Fallback mode: {error_message}. Displaying goals ungrouped."
        )
    
    async def _store_theme_patterns(
        self,
        result: ThemeExtractionResult,
        workspace_context: Optional[Dict[str, Any]]
    ):
        """Store successful theme patterns in workspace memory for learning"""
        if not workspace_context or result.fallback_used:
            return
        
        try:
            # Import workspace memory if available
            from services.workspace_memory import WorkspaceMemory
            
            workspace_id = workspace_context.get("workspace_id")
            if not workspace_id:
                return
            
            memory = WorkspaceMemory()
            
            # Store successful theme patterns
            for theme in result.themes:
                if theme.confidence_score >= 80:  # Only store high-confidence themes
                    await memory.store_pattern(
                        workspace_id,
                        "theme_extraction",
                        {
                            "theme_name": theme.name,
                            "goal_count": len(theme.goal_ids),
                            "confidence": theme.confidence_score,
                            "reasoning": theme.reasoning,
                            "timestamp": theme.extracted_at
                        }
                    )
            
            logger.info(f"✅ Stored {len(result.themes)} theme patterns in workspace memory")
            
        except ImportError:
            logger.debug("Workspace memory not available")
        except Exception as e:
            logger.warning(f"Failed to store theme patterns: {e}")
    
    def _prepare_goal_data(self, goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare goal data for AI analysis"""
        prepared_goals = []
        
        for goal in goals:
            prepared_goals.append({
                "id": goal.get("id"),
                "description": goal.get("description", ""),
                "status": goal.get("status"),
                "progress": goal.get("progress", 0),
                "deliverable_count": len(goal.get("deliverables", [])),
                "metric_type": goal.get("metric_type"),
                "created_at": goal.get("created_at")
            })
        
        return prepared_goals
    
    def _generate_cache_key(
        self,
        goals: List[Dict[str, Any]],
        workspace_context: Optional[Dict[str, Any]],
        user_locale: str
    ) -> str:
        """Generate cache key for theme extraction"""
        goal_ids = sorted([g.get("id", "") for g in goals])
        workspace_id = workspace_context.get("workspace_id", "") if workspace_context else ""
        return f"themes_{workspace_id}_{user_locale}_{'_'.join(goal_ids)}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[ThemeExtractionResult]:
        """Get cached result if still valid"""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return result
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: ThemeExtractionResult):
        """Cache extraction result"""
        self.cache[cache_key] = (result, datetime.now())
        
        # Clean old cache entries
        self._clean_cache()
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

# Singleton instance
ai_theme_extractor = AIThemeExtractor()