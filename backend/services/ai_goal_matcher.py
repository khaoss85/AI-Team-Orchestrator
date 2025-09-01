"""
AI Goal Matcher Service
Implements Pillar-compliant semantic matching between deliverables and goals
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class GoalMatchResult:
    """Result of AI goal matching"""
    def __init__(self, goal_id: str, confidence: float, reasoning: str):
        self.goal_id = goal_id
        self.confidence = confidence
        self.reasoning = reasoning

class AIGoalMatcher:
    """
    AI-driven semantic goal matching service
    Implements Pillar 1 (OpenAI SDK), Pillar 10 (Explainability), Pillar 6 (Memory)
    """
    
    def __init__(self):
        self.openai_available = self._check_openai_availability()
        
    def _check_openai_availability(self) -> bool:
        """Check if OpenAI is available"""
        try:
            import openai
            return bool(os.getenv("OPENAI_API_KEY"))
        except ImportError:
            logger.warning("OpenAI not available, will use fallback matching")
            return False
    
    async def analyze_and_match(
        self,
        deliverable_content: Dict[str, Any],
        available_goals: List[Dict[str, Any]],
        thinking_process_id: Optional[str] = None,
        pattern_insights: Optional[Dict[str, Any]] = None
    ) -> GoalMatchResult:
        """
        Semantically match deliverable to best goal using AI
        
        Args:
            deliverable_content: The deliverable data to match
            available_goals: List of workspace goals
            thinking_process_id: Optional thinking process for transparency
            pattern_insights: Optional learned patterns from memory
            
        Returns:
            GoalMatchResult with matched goal_id, confidence, and reasoning
        """
        
        # Extract key information
        deliverable_title = deliverable_content.get("title", "")
        deliverable_type = deliverable_content.get("type", "")
        content_str = json.dumps(deliverable_content.get("content", {}))[:500]  # First 500 chars
        
        # Check pattern insights first (Pillar 6: Memory)
        if pattern_insights:
            pattern_match = self._check_pattern_match(
                deliverable_type, 
                pattern_insights, 
                available_goals
            )
            if pattern_match:
                logger.info(f"📚 Using learned pattern for {deliverable_type}")
                return pattern_match
        
        # Use AI for semantic matching if available (Pillar 1: OpenAI SDK)
        if self.openai_available:
            return await self._ai_semantic_match(
                deliverable_title,
                deliverable_type,
                content_str,
                available_goals,
                thinking_process_id
            )
        else:
            # Fallback to rule-based matching
            return self._fallback_rule_match(
                deliverable_title,
                deliverable_type,
                available_goals
            )
    
    def _check_pattern_match(
        self,
        deliverable_type: str,
        pattern_insights: Dict[str, Any],
        available_goals: List[Dict[str, Any]]
    ) -> Optional[GoalMatchResult]:
        """Check if we have a learned pattern for this deliverable type"""
        
        common_mappings = pattern_insights.get("common_mappings", {})
        
        if deliverable_type in common_mappings:
            # Find most common goal mapping for this type
            type_mappings = common_mappings[deliverable_type]
            if type_mappings:
                # Sort by frequency
                most_common_goal = max(type_mappings.items(), key=lambda x: x[1])
                goal_id = most_common_goal[0]
                frequency = most_common_goal[1]
                
                # Check if goal still exists
                if any(g.get("id") == goal_id for g in available_goals):
                    confidence = min(95, 70 + (frequency * 5))  # Higher frequency = higher confidence
                    return GoalMatchResult(
                        goal_id=goal_id,
                        confidence=confidence,
                        reasoning=f"Pattern match: {deliverable_type} historically maps to this goal ({frequency} times)"
                    )
        
        return None
    
    async def _ai_semantic_match(
        self,
        title: str,
        deliverable_type: str,
        content_preview: str,
        available_goals: List[Dict[str, Any]],
        thinking_process_id: Optional[str] = None
    ) -> GoalMatchResult:
        """Use OpenAI to semantically match deliverable to goal"""
        
        try:
            import openai
            
            # Prepare goal descriptions
            goals_text = "\n".join([
                f"Goal {i+1} (ID: {g.get('id')}): {g.get('description', g.get('metric_type', 'Unknown'))}"
                for i, g in enumerate(available_goals)
            ])
            
            # Create prompt for AI matching
            prompt = f"""Analyze this deliverable and match it to the most appropriate goal.

Deliverable:
- Title: {title}
- Type: {deliverable_type}
- Content Preview: {content_preview[:200]}

Available Goals:
{goals_text}

Return the analysis in this exact JSON format:
{{
    "matched_goal_id": "the UUID of the best matching goal",
    "confidence": 85,
    "reasoning": "Brief explanation of why this goal matches best"
}}

Consider:
1. Semantic similarity between deliverable title/content and goal description
2. Logical relationship between deliverable type and goal type
3. Keywords and domain alignment"""

            # Call OpenAI
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Log thinking step if process provided
            if thinking_process_id:
                from services.thinking_process import add_thinking_step
                await add_thinking_step(
                    thinking_process_id,
                    "analyzing_deliverable",
                    f"Analyzing deliverable '{title}' for goal matching",
                    {"goals_count": len(available_goals)}
                )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at matching deliverables to their appropriate goals based on semantic content analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate result
            goal_id = result.get("matched_goal_id")
            if not any(g.get("id") == goal_id for g in available_goals):
                # AI returned invalid goal, use fallback
                logger.warning(f"AI returned invalid goal_id: {goal_id}")
                return self._fallback_rule_match(title, deliverable_type, available_goals)
            
            # Log final decision if process provided
            if thinking_process_id:
                await add_thinking_step(
                    thinking_process_id,
                    "goal_matched",
                    f"Matched to goal with {result.get('confidence', 0)}% confidence",
                    {"goal_id": goal_id, "reasoning": result.get("reasoning")}
                )
            
            return GoalMatchResult(
                goal_id=goal_id,
                confidence=result.get("confidence", 85),
                reasoning=result.get("reasoning", "AI semantic matching")
            )
            
        except Exception as e:
            logger.error(f"AI matching failed: {e}")
            # Fall back to rule-based matching
            return self._fallback_rule_match(title, deliverable_type, available_goals)
    
    def _fallback_rule_match(
        self,
        title: str,
        deliverable_type: str,
        available_goals: List[Dict[str, Any]]
    ) -> GoalMatchResult:
        """
        Rule-based fallback matching when AI is unavailable
        Uses keyword matching and heuristics
        """
        
        if not available_goals:
            raise ValueError("No goals available for matching")
        
        title_lower = title.lower()
        best_match = None
        best_score = 0
        
        for goal in available_goals:
            score = 0
            goal_desc = goal.get("description", "").lower()
            goal_type = goal.get("metric_type", "").lower()
            
            # Check for keyword matches
            goal_keywords = set(goal_desc.split())
            title_keywords = set(title_lower.split())
            
            # Calculate overlap
            overlap = goal_keywords.intersection(title_keywords)
            if overlap:
                score += len(overlap) * 10
            
            # Check for type alignment
            if "email" in title_lower and "email" in goal_desc:
                score += 30
            if "strategy" in title_lower and "strateg" in goal_desc:
                score += 30
            if "list" in title_lower and ("list" in goal_desc or "contact" in goal_desc):
                score += 25
            if "report" in title_lower and "report" in goal_type:
                score += 20
            
            # Boost active goals slightly
            if goal.get("status") == "active":
                score += 5
            
            if score > best_score:
                best_score = score
                best_match = goal
        
        # If no good match found, use first active goal as last resort
        if best_score < 10 and best_match is None:
            for goal in available_goals:
                if goal.get("status") == "active":
                    best_match = goal
                    break
        
        # If still no match, use first goal
        if best_match is None:
            best_match = available_goals[0]
        
        # Calculate confidence based on score
        confidence = min(90, 50 + best_score)
        
        return GoalMatchResult(
            goal_id=best_match.get("id"),
            confidence=confidence,
            reasoning=f"Rule-based matching: score={best_score}, keywords matched"
        )

# Singleton instance
ai_goal_matcher = AIGoalMatcher()