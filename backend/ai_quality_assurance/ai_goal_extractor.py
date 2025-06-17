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

# Import strategic decomposer for complex goals
try:
    from .strategic_goal_decomposer import strategic_decomposer, StrategicGoalPlan, StrategicDeliverable
    STRATEGIC_DECOMPOSER_AVAILABLE = True
    logger.info("✅ Strategic Goal Decomposer available")
except ImportError as e:
    logger.warning(f"Strategic decomposer not available: {e}")
    STRATEGIC_DECOMPOSER_AVAILABLE = False

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
    
    async def extract_goals_from_text(self, goal_text: str, workspace_context: Optional[Dict] = None) -> List[ExtractedGoal]:
        """
        🤖 Estrae goal usando AI per comprensione semantica con decomposizione strategica
        """
        logger.info(f"🎯 AI Goal Extraction from: {goal_text[:100]}...")
        
        if self.ai_available:
            try:
                # Step 1: Determina se serve decomposizione strategica
                needs_strategic_decomposition = await self._needs_strategic_analysis(goal_text)
                
                if needs_strategic_decomposition and STRATEGIC_DECOMPOSER_AVAILABLE:
                    logger.info("🧠 Goal requires strategic decomposition - using comprehensive analysis")
                    goals = await self._extract_goals_with_strategic_decomposition(goal_text, workspace_context)
                else:
                    logger.info("📊 Goal is simple metrics - using direct extraction")
                    goals = await self._ai_extract_goals(goal_text)
                
                logger.info(f"✅ AI extracted {len(goals)} unique goals")
                return goals
            except Exception as e:
                logger.error(f"AI extraction failed: {e}, falling back to pattern matching")
        
        # Fallback to pattern matching
        return self._pattern_extract_goals(goal_text)
    
    async def _needs_strategic_analysis(self, goal_text: str) -> bool:
        """
        🧠 Determina se l'obiettivo richiede decomposizione strategica completa
        """
        if not self.ai_available:
            return False
        
        prompt = f"""Analyze this business goal and determine if it requires strategic decomposition into multiple deliverables and assets:

Goal: "{goal_text}"

A goal needs strategic decomposition if it:
1. Involves creating multiple types of content/assets (strategies, calendars, templates, etc.)
2. Has complex processes that require multiple steps/deliverables
3. Mentions creating, developing, building, or establishing systems
4. Requires coordination of multiple activities to achieve the outcome
5. Is more than just a simple metric target

Examples that NEED strategic decomposition:
- "Create a marketing strategy and content calendar to grow followers"
- "Develop a lead generation system with email sequences"
- "Build a comprehensive social media presence"
- "Establish a content creation workflow"

Examples that DON'T need strategic decomposition (simple metrics):
- "Increase followers by 500"
- "Achieve 20% open rate"
- "Generate 100 leads per month"

Return JSON: {{"needs_strategic_decomposition": true/false, "reason": "explanation"}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business goal analyzer. Determine if goals need strategic breakdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            needs_decomposition = result.get("needs_strategic_decomposition", False)
            reason = result.get("reason", "No reason provided")
            
            logger.info(f"Strategic analysis decision: {needs_decomposition} - {reason}")
            return needs_decomposition
            
        except Exception as e:
            logger.error(f"Strategic analysis failed: {e}")
            return False
    
    async def _extract_goals_with_strategic_decomposition(self, goal_text: str, workspace_context: Optional[Dict] = None) -> List[ExtractedGoal]:
        """
        🧠 Estrae goal usando decomposizione strategica completa
        """
        logger.info("🧠 Performing strategic goal decomposition...")
        
        try:
            # Step 1: Ottieni piano strategico completo
            strategic_plan = await strategic_decomposer.decompose_strategic_goal(goal_text, workspace_context)
            
            goals = []
            
            # Step 2: Crea goal per le metriche finali
            for metric in strategic_plan.final_metrics:
                # Map AI-generated metric types to valid database enum values
                raw_metric_type = metric.get("metric_type", "quality_score")
                metric_type = self._map_metric_type_to_enum(raw_metric_type, metric.get("metric_name", ""))
                
                goal = ExtractedGoal(
                    goal_type=GoalType.METRIC,
                    metric_type=metric_type,
                    target_value=float(metric.get("target_value", 0)),
                    unit=metric.get("unit", ""),
                    description=metric.get("description", ""),
                    is_percentage=metric.get("unit", "").endswith("%") or "percentage" in metric.get("unit", ""),
                    is_minimum=metric.get("is_increase", True),
                    semantic_context={
                        "metric_name": metric.get("metric_name", ""),
                        "period": metric.get("period", ""),
                        "is_final_metric": True
                    },
                    confidence=0.95,
                    source_text=goal_text
                )
                goals.append(goal)
                logger.info(f"  🎯 Final metric goal: {goal.description}")
            
            # Step 3: Crea goal per ogni deliverable strategico
            for deliverable in strategic_plan.required_deliverables:
                # Converti deliverable in goal appropriato
                goal_type = GoalType.DELIVERABLE
                metric_type = "deliverables"
                
                # Usa mapping più specifico basato sul tipo di deliverable
                if deliverable.deliverable_type.value in ["content_calendar", "social_media_plan"]:
                    metric_type = "content_pieces"
                elif deliverable.deliverable_type.value in ["contact_database", "email_sequence"]:
                    metric_type = "contacts" if "contact" in deliverable.deliverable_type.value else "email_sequences"
                elif deliverable.deliverable_type.value in ["monitoring_system", "measurement_framework"]:
                    metric_type = "quality_score"
                
                goal = ExtractedGoal(
                    goal_type=goal_type,
                    metric_type=metric_type,
                    target_value=1.0,  # Deliverable è binario: esiste o non esiste
                    unit="deliverable",
                    description=f"Create {deliverable.name}",
                    is_percentage=False,
                    is_minimum=True,
                    semantic_context={
                        "deliverable_type": deliverable.deliverable_type.value,
                        "priority": deliverable.priority,
                        "estimated_effort": deliverable.estimated_effort,
                        "depends_on": deliverable.depends_on,
                        "contributes_to_metrics": deliverable.contributes_to_metrics,
                        "acceptance_criteria": deliverable.acceptance_criteria,
                        "business_value": deliverable.business_value,
                        "required_tools": deliverable.required_tools,
                        "full_description": deliverable.description,
                        "is_strategic_deliverable": True,
                        "execution_phase": self._determine_execution_phase(deliverable, strategic_plan.execution_phases),
                        # AI Autonomy information
                        "autonomy_level": deliverable.autonomy_level,
                        "autonomy_reason": deliverable.autonomy_reason,
                        "available_tools": deliverable.available_tools or [],
                        "human_input_required": deliverable.human_input_required or []
                    },
                    confidence=0.90,
                    source_text=goal_text
                )
                goals.append(goal)
                logger.info(f"  📋 Deliverable goal: {deliverable.name} (priority: {deliverable.priority})")
            
            logger.info(f"🧠 Strategic decomposition created {len(goals)} goals: {len(strategic_plan.final_metrics)} metrics + {len(strategic_plan.required_deliverables)} deliverables")
            return goals
            
        except Exception as e:
            logger.error(f"Strategic decomposition failed: {e}, falling back to simple extraction")
            # Fallback alla estrazione semplice
            return await self._ai_extract_goals(goal_text)
    
    def _determine_execution_phase(self, deliverable: StrategicDeliverable, execution_phases: List[Dict]) -> Optional[str]:
        """Determina in quale fase di esecuzione rientra questo deliverable"""
        try:
            for phase in execution_phases:
                if deliverable.name in phase.get("deliverables", []) or \
                   any(dep in phase.get("deliverables", []) for dep in deliverable.depends_on):
                    return phase.get("phase_name", "")
            return execution_phases[0].get("phase_name", "") if execution_phases else None
        except:
            return None
    
    def _map_metric_type_to_enum(self, raw_metric_type: str, metric_name: str = "") -> str:
        """
        🎯 Maps AI-generated metric types to valid database enum values
        Ensures universal compatibility across all business domains
        """
        # Convert to lowercase for matching
        raw_lower = raw_metric_type.lower()
        name_lower = metric_name.lower()
        
        # Direct mappings for common AI outputs
        if raw_lower in ["contacts", "contact"]:
            return "contacts"
        elif raw_lower in ["followers", "follower", "following"]:
            return "contacts"  # Treat followers as a type of contact/audience
        elif raw_lower in ["email_sequences", "email_sequence", "sequences"]:
            return "email_sequences"
        elif raw_lower in ["content_pieces", "content", "posts"]:
            return "content_pieces"
        elif raw_lower in ["campaigns", "campaign"]:
            return "campaigns"
        elif raw_lower in ["revenue", "sales", "income"]:
            return "revenue"
        elif raw_lower in ["timeline_days", "timeline", "days"]:
            return "timeline_days"
        elif raw_lower in ["deliverables", "deliverable", "items"]:
            return "deliverables"
        elif raw_lower in ["tasks_completed", "tasks"]:
            return "tasks_completed"
        
        # Rate/percentage mappings based on metric name context
        elif raw_lower == "rate" or "rate" in raw_lower or "percentage" in raw_lower:
            if "open" in name_lower and "email" in name_lower:
                return "conversion_rate"  # Email open rate
            elif "click" in name_lower or "ctr" in name_lower:
                return "engagement_rate"  # Click-through rate (different from open rate)
            elif "engagement" in name_lower or "interaction" in name_lower:
                return "engagement_rate"  # Social engagement
            elif "conversion" in name_lower:
                return "conversion_rate"  # General conversion
            elif "email" in name_lower and ("performance" in name_lower or "rate" in raw_lower):
                # Differentiate email metrics to avoid constraint violations
                if "open" in name_lower:
                    return "conversion_rate"  # Email open rate
                elif "click" in name_lower:
                    return "engagement_rate"  # Email click rate  
                else:
                    return "conversion_rate"  # General email performance
            else:
                return "quality_score"    # Generic percentage metric
        
        # Quality/score mappings
        elif "quality" in raw_lower or "score" in raw_lower:
            return "quality_score"
        
        # Default fallback - AI-driven semantic analysis
        else:
            # Intelligent semantic fallback to avoid constraint violations
            if "frequency" in name_lower or "times" in name_lower or "count" in name_lower:
                return "tasks_completed"  # Frequency/count metrics
            elif "decision" in name_lower or "choice" in name_lower:
                return "engagement_rate"  # Decision-making effectiveness
            elif "portfolio" in name_lower or "diversification" in name_lower:
                return "quality_score"   # Portfolio quality metrics
            elif "monitoring" in name_lower or "tracking" in name_lower:
                return "tasks_completed"  # Monitoring task frequency
            else:
                logger.info(f"🤖 AI metric type mapping: '{raw_metric_type}' -> 'quality_score' (universal fallback)")
                return "quality_score"
    
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
        # Extract goals using AI with workspace context (get context from workspace_id)
        workspace_context = await _get_workspace_context_for_extraction(workspace_id)
        extracted_goals = await ai_goal_extractor.extract_goals_from_text(goal_text, workspace_context)
        
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

async def _get_workspace_context_for_extraction(workspace_id: str) -> Dict[str, Any]:
    """
    🏢 Recupera contesto del workspace per la decomposizione strategica in goal extraction
    """
    try:
        from database import supabase
        
        # Get workspace basic info
        workspace_response = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        
        workspace_context = {}
        
        if workspace_response.data:
            workspace = workspace_response.data[0]
            workspace_context.update({
                "workspace_name": workspace.get("name", ""),
                "workspace_description": workspace.get("description", ""),
                "original_goal": workspace.get("goal", ""),
                "workspace_status": workspace.get("status", "")
            })
        
        logger.info(f"🏢 Workspace context for goal extraction: {workspace_id}")
        return workspace_context
        
    except Exception as e:
        logger.error(f"Failed to get workspace context for extraction: {e}")
        return {}