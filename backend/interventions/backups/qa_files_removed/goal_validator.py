# backend/ai_quality_assurance/goal_validator.py

import json
import logging
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    CRITICAL = "critical"  # Blocks project completion
    HIGH = "high"         # Should be addressed before delivery
    MEDIUM = "medium"     # Improvement recommended
    LOW = "low"          # Minor optimization

@dataclass
class GoalValidationResult:
    """Result of AI-driven goal validation"""
    is_valid: bool
    severity: ValidationSeverity
    confidence: float
    target_requirement: str
    actual_achievement: str
    gap_percentage: float
    validation_message: str
    recommendations: List[str]
    extracted_metrics: Dict[str, Any]
    
class AIGoalValidator:
    """
    AI-driven validator that checks if deliverables meet workspace goals
    Scalable across domains (finance, marketing, sports, etc.)
    """
    
    def __init__(self):
        # Add caching to avoid re-parsing the same workspace goals
        self._goal_requirements_cache = {}
        self._cache_max_size = 50
        # 🤖 AI-DRIVEN UNIVERSAL PATTERNS - Scalable across all domains
        self.numerical_patterns = [
            # 🎯 UNIVERSAL QUANTITY PATTERNS - Any number + noun
            r'(\d+)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+){0,3})',  # 1-4 words after number
            r'almeno\s+(\d+)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+){0,2})',  # "at least N items"
            r'(\d+)\s+([a-zA-ZÀ-ÿ]+)\s+di\s+([a-zA-ZÀ-ÿ]+)',  # "N items di categoria"
            r'(\d+)\s+([a-zA-ZÀ-ÿ]+)\s+per\s+([a-zA-ZÀ-ÿ]+)',  # "N items per category"
            r'fino\s+a\s+(\d+)\s+([a-zA-ZÀ-ÿ]+)',  # "up to N items"
            r'minimo\s+(\d+)\s+([a-zA-ZÀ-ÿ]+)',  # "minimum N items"
            r'massimo\s+(\d+)\s+([a-zA-ZÀ-ÿ]+)',  # "maximum N items"
            
            # 🎯 PERCENTAGE PATTERNS - Universal for any metric (IMPROVED to avoid false positives)
            r'(\d+(?:\.\d+)?)\s*%(?:\s+([a-zA-ZÀ-ÿ\-]+(?:\s+[a-zA-ZÀ-ÿ\-]+){0,2}))?',  # Percentage with optional context after
            r'≥\s*(\d+(?:\.\d+)?)\s*%',  # Greater-than-equal percentages
            r'>\s*(\d+(?:\.\d+)?)\s*%',   # Greater-than percentages  
            r'almeno\s+(\d+(?:\.\d+)?)\s*%',  # "at least X%"
            r'minimo\s+(\d+(?:\.\d+)?)\s*%',  # "minimum X%"
            r'target\s+(\d+(?:\.\d+)?)\s*%',  # "target X%"
            r'obiettivo\s+(\d+(?:\.\d+)?)\s*%',  # "obiettivo X%"
            
            # 🎯 FINANCIAL PATTERNS - Universal currency support
            r'(\d+(?:[\.,]\d{3})*(?:[\.,]\d{1,2})?)\s*(EUR|USD|GBP|CHF|JPY|\$|€|£|¥)',
            r'(\d+(?:\.\d+)?)\s*([KkMmBb])\s*(EUR|USD|GBP|CHF|\$|€|£)',  # 1K, 1M, 1B
            r'budget.*?(\d+(?:[\.,]\d{3})*)\s*(EUR|USD|\$|€)',  # Budget context
            r'costo.*?(\d+(?:[\.,]\d{3})*)\s*(EUR|USD|\$|€)',   # Cost context
            
            # 🎯 TIME PATTERNS - Universal temporal goals
            r'(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?|anni|years?|ore|hours?|minuti|minutes?)',
            r'entro\s+(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?)',
            r'in\s+(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?)',
            r'ogni\s+(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?)',  # "every N days"
            r'per\s+(\d+)\s*(settiman[ei]?|weeks?|giorni|days?|mesi|months?)',   # "for N days"
            
            # 🎯 RATIO & MEASUREMENT PATTERNS
            r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)',  # Ratios like 3:1
            r'(\d+(?:\.\d+)?)\s*(volte|times|x)',      # Multipliers  
            r'(\d+(?:\.\d+)?)\s*(punti|points|scores?|rating)',  # Scores/ratings
            r'(\d+(?:\.\d+)?)\s*(kg|lb|g|metri|meters?|km|miles?)',  # Physical measurements
        ]
        
        # 🤖 AI-DRIVEN GOAL ANALYSIS - No hard-coded domain assumptions
        # All concept analysis is now done dynamically via AI
        self.ai_available = self._check_ai_availability()
        
        # Only universal, cross-domain patterns (no business domain assumptions)
        self.universal_action_patterns = {
            'creation': ['create', 'creare', 'generate', 'build', 'develop', 'produce', 'make'],
            'collection': ['collect', 'raccogliere', 'gather', 'find', 'acquire', 'source', 'get'],
            'processing': ['process', 'analyze', 'evaluate', 'review', 'assess', 'study'],
            'completion': ['complete', 'finish', 'deliver', 'achieve', 'accomplish', 'realize'],
            'improvement': ['improve', 'enhance', 'optimize', 'increase', 'boost', 'grow']
        }
    
    def _check_ai_availability(self) -> bool:
        """Check if AI services are available for dynamic analysis"""
        try:
            import os
            return bool(os.getenv("OPENAI_API_KEY"))
        except:
            return False
    
    async def validate_workspace_goal_achievement(
        self, 
        workspace_goal: str, 
        completed_tasks: List[Dict],
        workspace_id: str
    ) -> List[GoalValidationResult]:
        """
        AI-driven validation of workspace goal achievement
        """
        try:
            # 1. Extract requirements from workspace goal using AI
            goal_requirements = await self._extract_goal_requirements(workspace_goal)
            
            # 2. Extract achievements from completed tasks
            actual_achievements = await self._extract_task_achievements(completed_tasks)
            
            # 3. Validate each requirement against achievements
            validation_results = []
            for requirement in goal_requirements:
                result = await self._validate_single_requirement(
                    requirement, actual_achievements, workspace_goal
                )
                validation_results.append(result)
            
            # 4. Log validation summary
            critical_failures = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
            if critical_failures:
                logger.warning(f"🚨 CRITICAL goal validation failures for workspace {workspace_id}: {len(critical_failures)} issues")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in goal validation: {e}", exc_info=True)
            return []
    
    async def validate_database_goals_achievement(
        self, 
        workspace_goals: List[Dict],
        completed_tasks: List[Dict],
        workspace_id: str
    ) -> List[GoalValidationResult]:
        """
        AI-driven validation of database workspace goals achievement
        This method includes goal_id in validation results for corrective task creation
        """
        try:
            logger.info(f"🎯 Validating {len(workspace_goals)} database goals for workspace {workspace_id}")
            
            # Extract achievements from completed tasks
            actual_achievements = await self._extract_task_achievements(completed_tasks)
            
            validation_results = []
            
            for goal in workspace_goals:
                goal_id = goal.get("id")
                metric_type = goal.get("metric_type", "unknown")
                target_value = goal.get("target_value", 0)
                current_value = goal.get("current_value", 0)
                unit = goal.get("unit", "")
                
                # Create requirement from database goal
                requirement = {
                    'type': metric_type,
                    'target_value': target_value,
                    'unit': unit,
                    'domain': 'database_goal',
                    'context': f"{target_value} {unit} {metric_type}",
                    'is_percentage': '%' in unit,
                    'is_minimum': False,  # Database goals are exact targets
                    'goal_id': goal_id  # Include goal_id for corrective tasks
                }
                
                # Validate this specific goal
                result = await self._validate_single_database_goal(
                    requirement, actual_achievements, goal, workspace_id
                )
                
                validation_results.append(result)
            
            # Log validation summary
            critical_failures = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
            if critical_failures:
                logger.warning(f"🚨 CRITICAL database goal validation failures for workspace {workspace_id}: {len(critical_failures)} issues")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in database goal validation: {e}", exc_info=True)
            return []
    
    async def _extract_goal_requirements(self, workspace_goal: str) -> List[Dict[str, Any]]:
        """
        AI-powered extraction of measurable requirements from workspace goal
        """
        # Check cache first
        cache_key = hash(workspace_goal)
        if cache_key in self._goal_requirements_cache:
            logger.debug("Using cached goal requirements")
            return self._goal_requirements_cache[cache_key]
        
        requirements = []
        goal_lower = workspace_goal.lower()
        
        # Extract numerical requirements using patterns with deduplication
        seen_requirements = set()  # Track unique requirements to avoid duplicates
        
        for pattern in self.numerical_patterns:
            matches = re.finditer(pattern, goal_lower, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract value and unit
                    value_str = match.group(1)
                    unit_context = match.group(2) if len(match.groups()) > 1 else ""
                    
                    # Parse numerical value
                    if ',' in value_str:
                        value = float(value_str.replace(',', ''))
                    else:
                        value = float(value_str)
                    
                    # Determine requirement type first for better deduplication
                    req_type = await self._classify_requirement_type(unit_context, goal_lower)
                    
                    # Create intelligent deduplication key
                    is_percentage = '%' in match.group(0)
                    context_key = match.group(0).lower().strip()
                    
                    # For percentages, use the exact context to avoid false duplicates
                    if is_percentage:
                        dedup_key = (value, req_type, context_key)
                    elif req_type == 'email_sequences':
                        # For email sequences, use value and type only to catch variants like "3 sequenze email" vs "almeno 3 sequenze email"
                        dedup_key = (value, req_type)
                    else:
                        # For other types, use semantic deduplication
                        unit_key_words = [word for word in unit_context.lower().split() if len(word) > 2]
                        dedup_key = (value, req_type, tuple(sorted(unit_key_words)))
                    
                    # Skip if we've already seen this requirement
                    if dedup_key in seen_requirements:
                        continue
                        
                    # Quality filter: skip low-quality extractions
                    if self._is_low_quality_extraction(unit_context, match.group(0), req_type):
                        continue
                        
                    seen_requirements.add(dedup_key)
                    
                    # Determine domain (req_type already determined above)
                    domain = await self._detect_domain(workspace_goal)
                    
                    requirement = {
                        'type': req_type,
                        'target_value': value,
                        'unit': unit_context,
                        'domain': domain,
                        'context': match.group(0),
                        'pattern_matched': pattern,
                        'is_percentage': '%' in match.group(0),
                        'is_minimum': any(word in goal_lower for word in ['almeno', 'at least', '≥', '>='])
                    }
                    requirements.append(requirement)
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse requirement from match: {match.group(0)}, error: {e}")
        
        # AI enhancement: detect implicit requirements
        implicit_requirements = await self._detect_implicit_requirements(workspace_goal)
        requirements.extend(implicit_requirements)
        
        # Cache the result
        self._goal_requirements_cache[cache_key] = requirements
        
        # Clean cache if it gets too large
        if len(self._goal_requirements_cache) > self._cache_max_size:
            # Remove oldest entry (simple cleanup)
            oldest_key = next(iter(self._goal_requirements_cache))
            del self._goal_requirements_cache[oldest_key]
        
        logger.info(f"🎯 Extracted {len(requirements)} goal requirements from workspace goal")
        return requirements
    
    async def _extract_task_achievements(self, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN universal achievement extraction from completed tasks
        """
        # Universal achievement tracking (no domain assumptions)
        achievements = {
            'items_created': 0,        # Universal: any countable items created
            'data_processed': 0,       # Universal: any data points processed  
            'deliverables_completed': 0, # Universal: any deliverables finished
            'metrics_achieved': [],    # Universal: any measurable results
            'currency_amounts': [],    # Universal: any financial values
            'percentages_achieved': [], # Universal: any percentage results
            'quality_scores': [],      # Universal: any quality metrics
            'temporal_values': [],     # Universal: any time-based results
            'raw_extractions': []      # Debug information
        }
        
        for task in completed_tasks:
            # Use the universal achievement extraction from database.py
            from database import extract_task_achievements as universal_extract
            
            task_result = task.get('result', {})
            task_name = task.get('name', '')
            
            # Get universal achievements
            task_achievements = await universal_extract(task_result, task_name)
            
            # Aggregate universal achievements
            achievements['items_created'] += task_achievements.get('items_created', 0)
            achievements['data_processed'] += task_achievements.get('data_processed', 0)
            achievements['deliverables_completed'] += task_achievements.get('deliverables_completed', 0)
            achievements['metrics_achieved'].append(task_achievements.get('metrics_achieved', 0))
            
            # Extract additional universal patterns from task result
            additional_achievements = await self._extract_universal_task_patterns(task_result)
            
            # Merge additional achievements
            if additional_achievements.get('currency_amounts'):
                achievements['currency_amounts'].extend(additional_achievements['currency_amounts'])
            if additional_achievements.get('percentages'):
                achievements['percentages_achieved'].extend(additional_achievements['percentages'])
            if additional_achievements.get('quality_scores'):
                achievements['quality_scores'].extend(additional_achievements['quality_scores'])
            if additional_achievements.get('temporal_values'):
                achievements['temporal_values'].extend(additional_achievements['temporal_values'])
            
            # Store raw extraction for debugging
            achievements['raw_extractions'].append({
                'task_id': task.get('id'),
                'task_name': task_name,
                'universal_achievements': task_achievements,
                'additional_patterns': additional_achievements
            })
        
        total_items = achievements['items_created']
        total_deliverables = achievements['deliverables_completed']
        logger.info(f"📊 Universal achievements: {total_items} items, {total_deliverables} deliverables")
        return achievements
    
    async def _extract_universal_task_patterns(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 Extract universal patterns from task result (currency, percentages, quality scores, etc.)
        """
        patterns = {
            'currency_amounts': [],
            'percentages': [],
            'quality_scores': [],
            'temporal_values': []
        }
        
        try:
            # Convert task result to string for pattern analysis
            result_text = json.dumps(task_result, default=str)
            
            # Extract currency amounts (universal)
            import re
            currency_patterns = [
                r'[\$€£¥]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|GBP|JPY|usd|eur|gbp|jpy)',
            ]
            for pattern in currency_patterns:
                matches = re.findall(pattern, result_text)
                for match in matches:
                    try:
                        amount = float(str(match).replace(',', ''))
                        patterns['currency_amounts'].append(amount)
                    except ValueError:
                        continue
            
            # Extract percentages (universal)
            percentage_patterns = [
                r'(\d+(?:\.\d+)?)\s*%',
                r'(\d+(?:\.\d+)?)\s*percent'
            ]
            for pattern in percentage_patterns:
                matches = re.findall(pattern, result_text)
                for match in matches:
                    try:
                        percentage = float(match)
                        patterns['percentages'].append(percentage)
                    except ValueError:
                        continue
            
            # Extract quality scores (universal)
            quality_patterns = [
                r'quality[:\s]*(\d+(?:\.\d+)?)',
                r'score[:\s]*(\d+(?:\.\d+)?)',
                r'rating[:\s]*(\d+(?:\.\d+)?)'
            ]
            for pattern in quality_patterns:
                matches = re.findall(pattern, result_text, re.IGNORECASE)
                for match in matches:
                    try:
                        score = float(match)
                        if 0 <= score <= 100:  # Reasonable quality score range
                            patterns['quality_scores'].append(score)
                    except ValueError:
                        continue
            
            # Extract temporal values (universal)
            temporal_patterns = [
                r'(\d+)\s*(?:days?|giorni?)',
                r'(\d+)\s*(?:weeks?|settimane?)',
                r'(\d+)\s*(?:months?|mesi?)',
                r'(\d+)\s*(?:hours?|ore?)'
            ]
            for pattern in temporal_patterns:
                matches = re.findall(pattern, result_text, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match)
                        patterns['temporal_values'].append(value)
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error extracting universal patterns: {e}")
        
        return patterns
    
    async def _map_requirement_to_achievement_universal(
        self, 
        req_type: str, 
        requirement: Dict[str, Any], 
        achievements: Dict[str, Any],
        workspace_goal: str
    ) -> float:
        """
        🤖 UNIVERSAL SEMANTIC MAPPING of requirements to achievements
        
        Uses AI-driven logic to map any requirement type to universal achievement categories
        """
        try:
            # Universal mapping based on semantic meaning, not domain-specific logic
            if req_type == 'items':
                # Any countable items created
                return achievements.get('items_created', 0)
            elif req_type == 'contacts':
                # Contact generation achievements - prioritize items_created for contact lists
                return achievements.get('items_created', achievements.get('data_processed', 0))
            elif req_type == 'email_sequences':
                # Email sequence achievements - prioritize deliverables_completed
                return achievements.get('deliverables_completed', achievements.get('metrics_achieved', 0))
            elif req_type == 'metric':
                # Any measurable results achieved
                metrics = achievements.get('metrics_achieved', [])
                return max(metrics) if metrics else 0
            elif req_type == 'percentage':
                # Any percentage-based achievements
                percentages = achievements.get('percentages_achieved', [])
                return max(percentages) if percentages else 0
            elif req_type == 'currency':
                # Any financial values
                currency_amounts = achievements.get('currency_amounts', [])
                return max(currency_amounts) if currency_amounts else 0
            elif req_type == 'temporal':
                # Any time-based achievements
                temporal_values = achievements.get('temporal_values', [])
                return max(temporal_values) if temporal_values else 0
            elif req_type == 'quality':
                # Any quality scores achieved
                quality_scores = achievements.get('quality_scores', [])
                return max(quality_scores) if quality_scores else 0
            elif req_type == 'general':
                # General deliverables completed
                return achievements.get('deliverables_completed', 0)
            else:
                # AI-driven fallback: try to match semantically
                if self.ai_available:
                    return await self._ai_semantic_match_requirement(
                        req_type, requirement, achievements, workspace_goal
                    )
                else:
                    # Ultimate fallback: use the most appropriate universal metric
                    if 'created' in req_type or 'item' in req_type:
                        return achievements.get('items_created', 0)
                    elif 'data' in req_type or 'process' in req_type:
                        return achievements.get('data_processed', 0)
                    else:
                        return achievements.get('deliverables_completed', 0)
        except Exception as e:
            logger.error(f"Error in universal requirement mapping: {e}")
            return 0
    
    async def _ai_semantic_match_requirement(
        self, 
        req_type: str, 
        requirement: Dict[str, Any], 
        achievements: Dict[str, Any],
        workspace_goal: str
    ) -> float:
        """
        🤖 AI-DRIVEN SEMANTIC MATCHING for unknown requirement types
        """
        try:
            from backend.ai_quality_assurance.quality_validator import AIQualityValidator
            ai_validator = AIQualityValidator()
            
            matching_prompt = f"""Analyze this requirement and match it to the most appropriate achievement category:

REQUIREMENT TYPE: "{req_type}"
REQUIREMENT CONTEXT: "{requirement.get('unit', '')} {requirement.get('context', '')}"
WORKSPACE GOAL: "{workspace_goal}"

AVAILABLE ACHIEVEMENT CATEGORIES:
- items_created: {achievements.get('items_created', 0)}
- data_processed: {achievements.get('data_processed', 0)}
- deliverables_completed: {achievements.get('deliverables_completed', 0)}
- metrics_achieved: {achievements.get('metrics_achieved', [])}
- currency_amounts: {achievements.get('currency_amounts', [])}
- percentages_achieved: {achievements.get('percentages_achieved', [])}
- quality_scores: {achievements.get('quality_scores', [])}
- temporal_values: {achievements.get('temporal_values', [])}

Return ONLY the numeric value from the most semantically appropriate category, nothing else."""

            ai_result = await ai_validator._call_openai_api(matching_prompt, "semantic_requirement_matching")
            if ai_result and "raw_response" in ai_result:
                try:
                    matched_value = float(str(ai_result["raw_response"]).strip())
                    logger.info(f"🤖 AI matched requirement '{req_type}' to value: {matched_value}")
                    return matched_value
                except ValueError:
                    logger.debug(f"AI returned non-numeric response: {ai_result['raw_response']}")
                    
        except Exception as e:
            logger.debug(f"AI semantic matching failed: {e}")
        
        # Fallback to universal default
        return achievements.get('deliverables_completed', 0)
    
    async def _validate_single_requirement(
        self, 
        requirement: Dict[str, Any], 
        achievements: Dict[str, Any],
        workspace_goal: str
    ) -> GoalValidationResult:
        """
        🤖 AI-DRIVEN UNIVERSAL REQUIREMENT VALIDATION
        
        Maps requirements to achievements using universal semantic matching
        """
        req_type = requirement['type']
        target_value = requirement['target_value']
        is_minimum = requirement.get('is_minimum', False)
        
        # 🤖 UNIVERSAL SEMANTIC MAPPING - No domain assumptions
        actual_value = await self._map_requirement_to_achievement_universal(
            req_type, requirement, achievements, workspace_goal
        )
        
        # Calculate gap
        if target_value > 0:
            gap_percentage = max(0, (target_value - actual_value) / target_value * 100)
        else:
            gap_percentage = 0
        
        # Determine validation result
        if is_minimum:
            is_valid = actual_value >= target_value
        else:
            # For exact targets, allow 10% tolerance
            is_valid = actual_value >= target_value * 0.9
        
        # Determine severity
        if gap_percentage >= 80:
            severity = ValidationSeverity.CRITICAL
        elif gap_percentage >= 50:
            severity = ValidationSeverity.HIGH
        elif gap_percentage >= 20:
            severity = ValidationSeverity.MEDIUM
        else:
            severity = ValidationSeverity.LOW
        
        # Generate AI-driven recommendations
        recommendations = await self._generate_recommendations(
            requirement, actual_value, target_value, gap_percentage
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(achievements, requirement)
        
        return GoalValidationResult(
            is_valid=is_valid,
            severity=severity,
            confidence=confidence,
            target_requirement=f"{target_value} {requirement['unit']}",
            actual_achievement=f"{actual_value} {requirement['unit']}",
            gap_percentage=gap_percentage,
            validation_message=self._generate_validation_message(
                requirement, actual_value, target_value, is_valid
            ),
            recommendations=recommendations,
            extracted_metrics={
                'target': target_value,
                'actual': actual_value,
                'type': req_type,
                'unit': requirement['unit'],
                'goal_id': requirement.get('goal_id')  # Include goal_id if available
            }
        )
    
    async def _validate_single_database_goal(
        self, 
        requirement: Dict[str, Any], 
        achievements: Dict[str, Any],
        goal: Dict[str, Any],
        workspace_id: str
    ) -> GoalValidationResult:
        """
        🤖 AI-DRIVEN DATABASE GOAL VALIDATION
        
        Validates a specific database goal and includes goal_id in extracted_metrics
        """
        req_type = requirement['type']
        target_value = requirement['target_value']
        goal_id = requirement.get('goal_id')
        current_value = goal.get('current_value', 0)
        
        # Use current_value from database as primary, but also check achievements
        actual_value = await self._map_requirement_to_achievement_universal(
            req_type, requirement, achievements, ""
        )
        
        # Combine database current_value with calculated achievements
        # Take the maximum to account for both database tracking and task analysis
        actual_value = max(current_value, actual_value)
        
        # Calculate gap
        if target_value > 0:
            gap_percentage = max(0, (target_value - actual_value) / target_value * 100)
        else:
            gap_percentage = 0
        
        # Determine validation result (database goals are exact targets)
        is_valid = actual_value >= target_value
        
        # Determine severity
        if gap_percentage >= 80:
            severity = ValidationSeverity.CRITICAL
        elif gap_percentage >= 50:
            severity = ValidationSeverity.HIGH
        elif gap_percentage >= 20:
            severity = ValidationSeverity.MEDIUM
        else:
            severity = ValidationSeverity.LOW
        
        # Generate AI-driven recommendations
        recommendations = await self._generate_recommendations(
            requirement, actual_value, target_value, gap_percentage
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(achievements, requirement)
        
        # Add database-specific context to recommendations
        if not is_valid:
            recommendations.insert(0, 
                f"🎯 DATABASE GOAL GAP: Current value {current_value}, target {target_value} {requirement['unit']}"
            )
        
        return GoalValidationResult(
            is_valid=is_valid,
            severity=severity,
            confidence=confidence,
            target_requirement=f"{target_value} {requirement['unit']}",
            actual_achievement=f"{actual_value} {requirement['unit']}",
            gap_percentage=gap_percentage,
            validation_message=self._generate_validation_message(
                requirement, actual_value, target_value, is_valid
            ),
            recommendations=recommendations,
            extracted_metrics={
                'target': target_value,
                'actual': actual_value,
                'current_value': current_value,
                'type': req_type,
                'unit': requirement['unit'],
                'goal_id': goal_id,  # This is the key fix - include goal_id
                'metric_type': req_type,
                'workspace_id': workspace_id
            }
        )
    
    async def _classify_requirement_type(self, unit_context: str, full_goal: str) -> str:
        """
        🤖 AI-DRIVEN UNIVERSAL CLASSIFICATION - No domain assumptions
        
        Uses AI to understand requirement type dynamically
        """
        # If AI is available, use it for classification
        if self.ai_available:
            try:
                from backend.ai_quality_assurance.quality_validator import AIQualityValidator
                ai_validator = AIQualityValidator()
                
                classification_prompt = f"""Analyze this requirement and classify its type universally:

REQUIREMENT CONTEXT: "{unit_context}"
FULL GOAL: "{full_goal}"

Classify into one of these UNIVERSAL types (no domain-specific assumptions):
- metric: Any measurable numeric target
- percentage: Percentage-based targets
- temporal: Time-based requirements
- currency: Financial/monetary values
- items: Countable objects/deliverables
- quality: Quality/performance metrics
- general: Other requirements

Return ONLY the classification type, nothing else."""

                ai_result = await ai_validator._call_openai_api(classification_prompt, "requirement_classification")
                if ai_result and "raw_response" in ai_result:
                    classification = str(ai_result["raw_response"]).strip().lower()
                    if classification in ['metric', 'percentage', 'temporal', 'currency', 'items', 'quality', 'general']:
                        logger.info(f"🤖 AI classified requirement as: {classification}")
                        return classification
            except Exception as e:
                logger.debug(f"AI classification failed, using fallback: {e}")
        
        # Fallback: Universal pattern-based classification (no domain assumptions)
        unit_lower = unit_context.lower()
        
        # Currency symbols (universal)
        if any(symbol in unit_lower for symbol in ['$', '€', '£', '¥', 'eur', 'usd', 'gbp']):
            return 'currency'
        # Percentage (universal)
        elif '%' in unit_context:
            return 'percentage'
        # Temporal patterns (universal)
        elif any(time_unit in unit_lower for time_unit in ['day', 'week', 'month', 'year', 'hour', 'giorno', 'settimana', 'mese', 'anno', 'ora']):
            return 'temporal'
        # Plural forms suggest countable items (universal)
        elif unit_lower.endswith(('s', 'i', 'e')) and len(unit_lower) > 2:
            return 'items'
        # Default to general metric
        else:
            return 'metric'
    
    async def _detect_domain(self, workspace_goal: str) -> str:
        """
        🤖 AI-DRIVEN DOMAIN DETECTION - Truly universal
        
        Uses AI to understand business domain without assumptions
        """
        # Always return 'universal' - domain doesn't matter for truly scalable system
        # The AI will understand context without needing domain categorization
        return 'universal'
    
    def _is_low_quality_extraction(self, unit_context: str, full_context: str, req_type: str) -> bool:
        """Filter out low-quality extractions with poor context"""
        unit_lower = unit_context.lower()
        full_lower = full_context.lower()
        
        # Skip extractions with very short or meaningless contexts
        if len(unit_context.strip()) < 3:
            return True
            
        # Skip percentage extractions that are just fragments
        if req_type == 'percentage' and len(full_context.strip()) < 5:
            return True
            
        # Skip temporal extractions that appear to be percentages in disguise
        if req_type == 'percentage' and 'settimane' in unit_lower:
            return True
            
        # Skip vague contexts like "in" or "da"
        if unit_lower in ['in', 'da', 'di', 'per', 'con', 'su', 'a', 'e', 'del', 'della', 'delle', 'dei']:
            return True
            
        return False
    
    async def _detect_implicit_requirements(self, workspace_goal: str) -> List[Dict[str, Any]]:
        """
        AI-powered detection of implicit requirements
        """
        implicit_requirements = []
        goal_lower = workspace_goal.lower()
        
        # Time-based implicit requirements
        if any(phrase in goal_lower for phrase in ['in 6 settimane', 'within 6 weeks', 'entro 6 settimane']):
            implicit_requirements.append({
                'type': 'timeline',
                'target_value': 6,
                'unit': 'weeks',
                'domain': 'general',
                'context': 'timeline constraint',
                'is_minimum': False,
                'is_percentage': False
            })
        
        # Quality-based implicit requirements
        if any(phrase in goal_lower for phrase in ['≥ 30%', '>=30%', 'almeno 30%']):
            implicit_requirements.append({
                'type': 'quality_threshold',
                'target_value': 30,
                'unit': 'percentage',
                'domain': 'quality',
                'context': 'minimum quality standard',
                'is_minimum': True,
                'is_percentage': True
            })
        
        return implicit_requirements
    
    async def _generate_recommendations(
        self, 
        requirement: Dict, 
        actual: float, 
        target: float, 
        gap_percentage: float
    ) -> List[str]:
        """
        🤖 AI-DRIVEN UNIVERSAL RECOMMENDATION GENERATION
        
        Generates actionable recommendations without domain-specific assumptions
        """
        recommendations = []
        req_type = requirement['type']
        unit = requirement.get('unit', 'units')
        gap_value = target - actual
        
        if gap_percentage > 50:  # Significant gap - TRIGGER CORRECTIVE TASKS
            # Universal critical gap recommendations
            recommendations.extend([
                f"🚨 CRITICAL GAP: Current achievement is {actual:.1f}/{target} {unit} ({gap_percentage:.1f}% gap)",
                f"📋 AUTO-GENERATING CORRECTIVE TASK: 'Close {gap_value:.1f} {unit} gap for {req_type}'",
                "🎯 Task will have numerical validation: cannot complete until target reached",
                "🔍 Will use memory insights from previous attempts to avoid similar failures",
                "📊 Implementing immediate quality gates and validation"
            ])
            
            # AI-driven specific recommendations if available
            if self.ai_available:
                try:
                    ai_recommendations = await self._generate_ai_specific_recommendations(
                        requirement, actual, target, gap_percentage, "critical"
                    )
                    recommendations.extend(ai_recommendations)
                except Exception as e:
                    logger.debug(f"AI recommendation generation failed: {e}")
                    
        elif gap_percentage > 20:  # Moderate gap - SUGGEST OPTIMIZATION
            recommendations.extend([
                f"📊 MODERATE GAP: {gap_percentage:.1f}% shortfall in {req_type}",
                f"📋 SUGGEST TASK: Optimize approach to close {gap_value:.1f} {unit} gap",
                "🔧 Fine-tune current processes with memory-guided improvements",
                "⏱️ Consider timeline adjustment or resource reallocation"
            ])
            
        else:  # Goal achieved or close
            recommendations.extend([
                f"✅ TARGET ACHIEVED: {actual:.1f}/{target} {unit} completed for {req_type}",
                "🎯 Consider setting stretch goals for additional value",
                "📝 SUCCESS PATTERN: Document approach for future similar goals",
                "🔄 Share insights with team for knowledge transfer"
            ])
        
        return recommendations
    
    async def _generate_ai_specific_recommendations(
        self, 
        requirement: Dict, 
        actual: float, 
        target: float, 
        gap_percentage: float,
        severity: str
    ) -> List[str]:
        """
        🤖 AI-DRIVEN SPECIFIC RECOMMENDATIONS based on requirement context
        """
        try:
            from backend.ai_quality_assurance.quality_validator import AIQualityValidator
            ai_validator = AIQualityValidator()
            
            recommendation_prompt = f"""Generate specific, actionable recommendations for this goal gap:

REQUIREMENT: {requirement['type']} - {requirement.get('unit', '')}
TARGET: {target}
ACTUAL: {actual}
GAP: {gap_percentage:.1f}%
SEVERITY: {severity}
CONTEXT: {requirement.get('context', '')}

Generate 2-3 specific, actionable recommendations that are:
1. Immediately implementable
2. Measurable in results  
3. Context-appropriate for the requirement type
4. Not domain-specific (universally applicable)

Return as numbered list, one recommendation per line."""

            ai_result = await ai_validator._call_openai_api(recommendation_prompt, "specific_recommendations")
            if ai_result and "raw_response" in ai_result:
                ai_recommendations = str(ai_result["raw_response"]).strip().split('\n')
                # Clean and format recommendations
                formatted_recs = []
                for rec in ai_recommendations:
                    cleaned = rec.strip()
                    if cleaned and len(cleaned) > 10:  # Filter out empty or too short
                        if not cleaned.startswith(('🤖', '📋', '⚡')):
                            cleaned = f"🤖 {cleaned}"
                        formatted_recs.append(cleaned)
                
                logger.info(f"🤖 Generated {len(formatted_recs)} AI-driven recommendations")
                return formatted_recs
                
        except Exception as e:
            logger.debug(f"AI-specific recommendation generation failed: {e}")
        
        return []
    
    def _calculate_confidence(self, achievements: Dict, requirement: Dict) -> float:
        """
        🤖 UNIVERSAL CONFIDENCE CALCULATION
        
        Calculate confidence score based on data quality without domain assumptions
        """
        base_confidence = 0.7  # Base confidence
        
        # Boost confidence if we have detailed extractions
        if achievements.get('raw_extractions'):
            detailed_extractions = sum(
                1 for ext in achievements['raw_extractions'] 
                if isinstance(ext, dict) and ext.get('universal_achievements')
            )
            if detailed_extractions > 0:
                base_confidence += 0.2
        
        # Boost confidence based on universal data richness
        req_type = requirement.get('type', '')
        
        # Universal confidence boosters based on achievement categories
        if req_type == 'items' and achievements.get('items_created', 0) > 0:
            base_confidence += 0.1
        elif req_type == 'metric' and achievements.get('metrics_achieved'):
            base_confidence += 0.15
        elif req_type == 'percentage' and achievements.get('percentages_achieved'):
            base_confidence += 0.1
        elif req_type == 'currency' and achievements.get('currency_amounts'):
            base_confidence += 0.1
        elif req_type == 'quality' and achievements.get('quality_scores'):
            base_confidence += 0.1
        elif achievements.get('deliverables_completed', 0) > 0:
            base_confidence += 0.05  # General deliverable completion
        
        # Additional boost for data richness (universal)
        total_data_points = (
            len(achievements.get('metrics_achieved', [])) +
            len(achievements.get('percentages_achieved', [])) +
            len(achievements.get('currency_amounts', [])) +
            len(achievements.get('quality_scores', [])) +
            len(achievements.get('temporal_values', []))
        )
        
        if total_data_points > 5:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _generate_validation_message(
        self, 
        requirement: Dict, 
        actual: float, 
        target: float, 
        is_valid: bool
    ) -> str:
        """
        Generate human-readable validation message
        """
        req_type = requirement['type']
        unit = requirement['unit']
        
        if is_valid:
            return f"✅ GOAL ACHIEVED: {actual}/{target} {unit} for {req_type}"
        else:
            gap = target - actual
            gap_pct = (gap / target * 100) if target > 0 else 0
            return f"⚠️ GOAL SHORTFALL: {actual}/{target} {unit} for {req_type} ({gap_pct:.1f}% gap, missing {gap})"
    
    async def trigger_corrective_actions(
        self, 
        validation_results: List[GoalValidationResult],
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """
        🎯 STEP 3: Memory-Driven Course Correction
        
        When critical gaps are detected, this method:
        1. Stores failure insights in workspace memory
        2. Calls Goal-Driven Task Planner to create corrective tasks
        3. Creates immediate action plan
        """
        corrective_tasks = []
        
        # Filter critical validation failures
        critical_failures = [
            v for v in validation_results 
            if v.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]
        ]
        
        if not critical_failures:
            logger.info(f"✅ No critical goal gaps found for workspace {workspace_id}")
            return []
        
        logger.warning(f"🚨 Found {len(critical_failures)} critical goal gaps in workspace {workspace_id}")
        
        for failure in critical_failures:
            try:
                # 1. 🧠 STORE FAILURE LESSON IN MEMORY
                await self._store_failure_insight(failure, workspace_id)
                
                # 2. 🎯 GENERATE CORRECTIVE TASK
                corrective_task = await self._generate_corrective_task(failure, workspace_id)
                
                if corrective_task and corrective_task.get("name"):
                    corrective_tasks.append(corrective_task)
                    
                    # 3. 📊 LOG COURSE CORRECTION
                    logger.warning(
                        f"🔄 COURSE CORRECTION triggered for {failure.target_requirement}: "
                        f"Gap {failure.gap_percentage:.1f}%, Created task: {corrective_task['name']}"
                    )
                elif corrective_task:
                    # Log when corrective task creation partially fails
                    logger.warning(
                        f"⚠️ Corrective task creation incomplete for {failure.target_requirement}: "
                        f"Gap {failure.gap_percentage:.1f}%, but no task name - likely agent assignment failed"
                    )
                
            except Exception as e:
                logger.error(f"Error creating corrective action for goal validation: {e}")
        
        return corrective_tasks
    
    async def _store_failure_insight(
        self, 
        failure: GoalValidationResult, 
        workspace_id: str
    ) -> None:
        """Store failure lesson in workspace memory for future course correction"""
        try:
            from workspace_memory import workspace_memory
            
            insight_content = (
                f"Goal gap detected: {failure.validation_message}. "
                f"Gap: {failure.gap_percentage:.1f}%. "
                f"Recommendations: {'; '.join(failure.recommendations[:2])}"
            )
            
            # Store failure insight
            await workspace_memory.store_insight(
                workspace_id=workspace_id,
                task_id=None,  # Not tied to specific task
                agent_role="goal_validator",
                insight_type="failure_lesson",
                content=insight_content,
                relevance_tags=[
                    f"metric_{failure.extracted_metrics.get('type', 'unknown')}",
                    f"gap_{int(failure.gap_percentage//10)*10}pct",  # 0-10%, 10-20%, etc.
                    "course_correction",
                    "critical_gap"
                ],
                confidence_score=failure.confidence
            )
            
            logger.info(f"💾 Stored failure insight for workspace {workspace_id}: {insight_content[:100]}...")
            
        except Exception as e:
            logger.error(f"Error storing failure insight: {e}")
    
    async def _generate_corrective_task(
        self, 
        failure: GoalValidationResult,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate corrective task using Goal-Driven Task Planner"""
        try:
            from goal_driven_task_planner import goal_driven_task_planner
            from uuid import UUID
            
            # Extract goal information from validation result
            goal_id = failure.extracted_metrics.get('goal_id')
            if not goal_id:
                logger.warning("No goal_id in validation result, cannot create corrective task")
                return None
            
            # Get memory context for corrective action
            failure_context = await self._get_failure_context(workspace_id, failure)
            
            # Create corrective task with memory-driven insights
            corrective_task = await goal_driven_task_planner.create_corrective_task(
                goal_id=UUID(goal_id),
                gap_percentage=failure.gap_percentage,
                failure_context=failure_context
            )
            
            # Add workspace context
            corrective_task.update({
                "workspace_id": workspace_id,
                "created_by": "goal_validator_course_correction",
                "urgency_reason": failure.validation_message,
                "memory_context": failure_context
            })
            
            # 🔧 BUGFIX: Extract agent_requirements from context_data to top level
            # This ensures automated_goal_monitor can access agent assignment info
            if "context_data" in corrective_task and "agent_requirements" in corrective_task["context_data"]:
                corrective_task["agent_requirements"] = corrective_task["context_data"]["agent_requirements"]
                logger.info(f"✅ Extracted agent_requirements: {corrective_task['agent_requirements'].get('role')} (agent_id: {corrective_task['agent_requirements'].get('agent_id')})")
            else:
                logger.warning(f"⚠️ No agent_requirements found in corrective task context_data")
            
            return corrective_task
            
        except Exception as e:
            logger.error(f"Error generating corrective task: {e}")
            return None
    
    async def _get_failure_context(
        self, 
        workspace_id: str, 
        failure: GoalValidationResult
    ) -> Dict[str, Any]:
        """Get relevant failure context from workspace memory"""
        try:
            from workspace_memory import workspace_memory
            
            # Get relevant insights for this metric type
            memory_context = await workspace_memory.get_relevant_context(
                workspace_id=workspace_id,
                context_filter={"insight_types": ["failure_lesson", "constraint"]}
            )
            
            return {
                "previous_failures": memory_context,
                "gap_severity": failure.severity.value,
                "target_missed": failure.target_requirement,
                "actual_achieved": failure.actual_achievement,
                "recommendations": failure.recommendations[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting failure context: {e}")
            return {}

# Singleton instance
goal_validator = AIGoalValidator()