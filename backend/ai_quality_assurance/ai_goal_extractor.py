#!/usr/bin/env python3
"""
🤖 AI-DRIVEN GOAL EXTRACTOR
Sistema intelligente per estrarre e strutturare obiettivi da linguaggio naturale
evitando duplicazioni e generando goal specifici e misurabili
"""

import logging
import json
import re
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GoalType(Enum):
    """Tipi di goal supportati dal sistema"""
    DELIVERABLE = "deliverable"      # Qualcosa da produrre/consegnare
    METRIC = "metric"                # Una metrica da raggiungere  
    QUALITY = "quality"              # Un livello di qualità da ottenere
    TIMELINE = "timeline"            # Un vincolo temporale
    QUANTITY = "quantity"            # Una quantità specifica

@dataclass
class ExtractedGoal:
    """Rappresenta un goal estratto e strutturato"""
    goal_type: GoalType
    metric_type: str                 # quality_score, deliverables, timeline_days
    target_value: float
    unit: str
    description: str
    is_percentage: bool = False
    is_minimum: bool = True
    semantic_context: Dict[str, Any] = None
    confidence: float = 1.0
    source_text: str = ""

class AIGoalExtractor:
    """
    🤖 Estrattore AI-driven di obiettivi che:
    - Comprende semanticamente gli obiettivi
    - Evita duplicazioni
    - Genera goal specifici e pragmatici
    - È universale e scalabile
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ AI Goal Extractor initialized with OpenAI")
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for goal extraction")
        else:
            self.ai_available = False
            
        # Fallback patterns solo per numeri evidenti
        self.basic_number_patterns = [
            r'(\d+)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+){0,3})',
            r'(\d+(?:\.\d+)?)\s*%',
            r'(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?)'
        ]
        
        # Mapping intelligente metric_type
        self.metric_type_mappings = {
            "quality": "quality_score",
            "deliverable": "deliverables", 
            "timeline": "timeline_days",
            "performance": "quality_score",
            "output": "deliverables"
        }
    
    async def extract_goals_from_text(self, goal_text: str) -> List[ExtractedGoal]:
        """
        🤖 Estrae goal usando AI per comprensione semantica
        """
        logger.info(f"🎯 AI Goal Extraction from: {goal_text[:100]}...")
        
        if self.ai_available:
            try:
                goals = await self._ai_extract_goals(goal_text)
                logger.info(f"✅ AI extracted {len(goals)} unique goals")
                return goals
            except Exception as e:
                logger.error(f"AI extraction failed: {e}, falling back to pattern matching")
        
        # Fallback to pattern matching
        return self._pattern_extract_goals(goal_text)
    
    def prepare_goal_data_for_db(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Prepare AI goal data for database insertion with full schema support
        All AI columns are now supported in the updated schema
        """
        return goal_data  # Schema is now complete, no filtering needed

    async def _ai_extract_goals(self, goal_text: str) -> List[ExtractedGoal]:
        """
        🤖 Usa AI per estrarre goal con comprensione semantica
        """
        
        prompt = f"""Analyze this business goal and extract SPECIFIC, MEASURABLE objectives.
Think creatively about how to make abstract goals concrete and actionable.
Consider the specific industry context and avoid defaulting to generic metrics.
Avoid duplicates - each metric should be extracted only once.

GOAL TEXT: "{goal_text}"

IMPORTANT: If the goal is abstract (like "innovate", "be agile", "grow"), translate it into 
industry-appropriate metrics. For example:
- "Innovate" → new products launched, R&D investment %, patents filed
- "Be agile" → sprint velocity, time to market, deployment frequency  
- "Improve quality" → defect rate, customer satisfaction score, uptime %
- "Grow" → revenue growth %, new customers, market share %

Extract goals in this exact JSON format:
{{
    "goals": [
        {{
            "goal_type": "deliverable|metric|quality|timeline|quantity",
            "metric_type": "quality_score|deliverables|timeline_days|contacts|email_sequences",
            "target_value": numeric_value,
            "unit": "specific unit of measurement",
            "description": "clear description of what needs to be achieved",
            "is_percentage": true/false,
            "is_minimum": true/false,
            "semantic_context": {{
                "what": "what is being measured",
                "why": "business purpose",
                "who": "target audience if specified"
            }}
        }}
    ]
}}

RULES:
1. Extract each unique goal only ONCE
2. For "50 contatti ICP" -> deliverable type, value=50, unit="ICP contacts", metric_type="contacts"
3. For "3 sequenze email" -> deliverable type, value=3, unit="email sequences", metric_type="email_sequences"
4. For "open-rate ≥ 30%" -> quality type, value=30, unit="open rate %", metric_type="quality_score"
5. For "Click-to-rate 10%" -> quality type, value=10, unit="click rate %", metric_type="quality_score"
6. For "6 settimane" -> timeline type, value=6, unit="weeks", metric_type="timeline_days"
7. Use metric_type mapping:
   - Contact/lead generation = "contacts"
   - Email sequences/campaigns = "email_sequences"
   - Performance metrics (%, rates) = "quality_score"
   - Time constraints = "timeline_days"
   - Generic deliverables = "deliverables"

Be specific and avoid generic descriptions. Each goal must be actionable and measurable."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business goal analysis expert. Extract specific, measurable goals without duplicates."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            goals = []
            
            # Track unique goals to avoid duplicates
            seen_goals = set()
            
            for goal_data in result.get("goals", []):
                # Create unique key to detect duplicates
                goal_key = f"{goal_data['metric_type']}_{goal_data['target_value']}_{goal_data['unit']}"
                
                if goal_key not in seen_goals:
                    seen_goals.add(goal_key)
                    
                    goal = ExtractedGoal(
                        goal_type=GoalType(goal_data["goal_type"]),
                        metric_type=goal_data["metric_type"],
                        target_value=float(goal_data["target_value"]),
                        unit=goal_data["unit"],
                        description=goal_data["description"],
                        is_percentage=goal_data.get("is_percentage", False),
                        is_minimum=goal_data.get("is_minimum", True),
                        semantic_context=goal_data.get("semantic_context", {}),
                        confidence=0.95,  # High confidence for AI extraction
                        source_text=goal_text
                    )
                    goals.append(goal)
                    
                    logger.info(f"  ✅ Extracted: {goal.description} ({goal.metric_type}={goal.target_value} {goal.unit})")
                else:
                    logger.debug(f"  ⚠️  Skipped duplicate: {goal_key}")
            
            return goals
            
        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            raise
    
    def _pattern_extract_goals(self, goal_text: str) -> List[ExtractedGoal]:
        """
        Fallback pattern-based extraction (meno intelligente ma funzionale)
        """
        logger.info("📊 Using pattern-based goal extraction (fallback)")
        
        goals = []
        seen_patterns = set()
        
        # Extract numbers with context
        for pattern in self.basic_number_patterns:
            for match in re.finditer(pattern, goal_text, re.IGNORECASE):
                groups = match.groups()
                if len(groups) >= 2:
                    value = float(groups[0])
                    unit = groups[1]
                    
                    # Create unique key
                    pattern_key = f"{value}_{unit}"
                    if pattern_key in seen_patterns:
                        continue
                    seen_patterns.add(pattern_key)
                    
                    # Determine goal type and metric_type
                    if '%' in match.group():
                        goal_type = GoalType.QUALITY
                        metric_type = "quality_score"
                        unit = unit.strip() + " %" if unit else "percentage"
                    elif any(time in unit.lower() for time in ['settiman', 'week', 'giorn', 'day', 'mes', 'month']):
                        goal_type = GoalType.TIMELINE
                        metric_type = "timeline_days"
                        # Convert to days
                        if 'settiman' in unit.lower() or 'week' in unit.lower():
                            value = value * 7
                            unit = "days"
                    else:
                        goal_type = GoalType.DELIVERABLE
                        metric_type = "deliverables"
                    
                    goal = ExtractedGoal(
                        goal_type=goal_type,
                        metric_type=metric_type,
                        target_value=value,
                        unit=unit,
                        description=f"Achieve {value} {unit}",
                        is_percentage='%' in match.group(),
                        confidence=0.7,  # Lower confidence for pattern matching
                        source_text=match.group()
                    )
                    goals.append(goal)
                    logger.info(f"  📊 Pattern extracted: {goal.description}")
        
        return goals
    
    def consolidate_goals(self, goals: List[ExtractedGoal]) -> List[ExtractedGoal]:
        """
        🧠 Consolida goal duplicati o simili in goal unici
        """
        consolidated = {}
        
        for goal in goals:
            # Create consolidation key based on metric_type + unit for better granularity
            # This ensures "50 contatti ICP" and "3 sequenze email" remain separate
            key = f"{goal.metric_type}_{goal.unit}_{goal.target_value}"
            
            if key not in consolidated:
                consolidated[key] = goal
            else:
                # Merge similar goals - take the higher value
                existing = consolidated[key]
                if goal.target_value > existing.target_value:
                    consolidated[key] = goal
                elif goal.confidence > existing.confidence:
                    # Keep higher confidence goal
                    consolidated[key] = goal
                else:
                    # Merge descriptions
                    existing.description = f"{existing.description} + {goal.description}"
        
        final_goals = list(consolidated.values())
        logger.info(f"🎯 Consolidated {len(goals)} goals into {len(final_goals)} unique goals")
        
        return final_goals
    
    def validate_goals(self, goals: List[ExtractedGoal]) -> List[ExtractedGoal]:
        """
        🔍 Valida che i goal siano specifici e pragmatici
        """
        validated = []
        
        for goal in goals:
            # Check specificity
            if goal.target_value <= 0:
                logger.warning(f"⚠️  Skipping goal with invalid value: {goal}")
                continue
            
            if not goal.unit or goal.unit.lower() in ['items', 'things', 'stuff']:
                logger.warning(f"⚠️  Goal too generic: {goal}")
                goal.confidence *= 0.8  # Reduce confidence for generic goals
            
            # Ensure pragmatic descriptions
            if len(goal.description) < 10:
                goal.description = f"Achieve {goal.target_value} {goal.unit} for {goal.metric_type}"
            
            validated.append(goal)
        
        return validated

# Singleton instance
ai_goal_extractor = AIGoalExtractor()

async def extract_and_create_workspace_goals(workspace_id: str, goal_text: str) -> List[Dict[str, Any]]:
    """
    🤖 Funzione helper per estrarre e creare goal workspace
    """
    try:
        # Extract goals using AI
        extracted_goals = await ai_goal_extractor.extract_goals_from_text(goal_text)
        
        # Consolidate duplicates
        consolidated_goals = ai_goal_extractor.consolidate_goals(extracted_goals)
        
        # Validate specificity
        validated_goals = ai_goal_extractor.validate_goals(consolidated_goals)
        
        # Convert to workspace goal format
        workspace_goals = []
        for goal in validated_goals:
            workspace_goal = {
                "workspace_id": workspace_id,
                "metric_type": goal.metric_type,
                "target_value": goal.target_value,
                "current_value": 0.0,
                "unit": goal.unit,
                "description": goal.description,
                "source_goal_text": goal_text,
                # AI-specific fields (may be excluded if columns don't exist)
                "goal_type": goal.goal_type.value,
                "is_percentage": goal.is_percentage,
                "is_minimum": goal.is_minimum,
                "semantic_context": goal.semantic_context or {},
                "confidence": goal.confidence
            }
            
            # 🎯 AI goal data ready for full schema
            workspace_goals.append(workspace_goal)
        
        return workspace_goals
        
    except Exception as e:
        logger.error(f"Goal extraction failed: {e}")
        # Return minimal fallback goals (schema-safe)
        fallback_goals = [
            {
                "workspace_id": workspace_id,
                "metric_type": "quality_score",
                "target_value": 50.0,
                "current_value": 0.0,
                "unit": "points",
                "description": "Achieve quality target",
                "source_goal_text": goal_text
            },
            {
                "workspace_id": workspace_id,
                "metric_type": "deliverables",
                "target_value": 3.0,
                "current_value": 0.0,
                "unit": "items", 
                "description": "Complete deliverables",
                "source_goal_text": goal_text
            },
            {
                "workspace_id": workspace_id,
                "metric_type": "timeline_days",
                "target_value": 42.0,
                "current_value": 0.0,
                "unit": "days",
                "description": "Complete within timeline",
                "source_goal_text": goal_text
            }
        ]
        
        return fallback_goals