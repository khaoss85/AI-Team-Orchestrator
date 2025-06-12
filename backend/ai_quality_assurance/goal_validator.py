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
        
        # 🧠 AI-DRIVEN UNIVERSAL DOMAIN KEYWORDS - Completely scalable
        self.universal_concept_patterns = {
            # 🎯 CREATION/PRODUCTION CONCEPTS
            'creation': {
                'keywords': ['creare', 'generare', 'produrre', 'sviluppare', 'costruire', 'fare', 'realizzare', 
                           'create', 'generate', 'produce', 'develop', 'build', 'make', 'craft'],
                'metric_types': ['deliverables', 'content_pieces', 'products', 'items']
            },
            
            # 🎯 COLLECTION/GATHERING CONCEPTS  
            'collection': {
                'keywords': ['raccogliere', 'trovare', 'identificare', 'selezionare', 'acquisire',
                           'collect', 'gather', 'find', 'identify', 'acquire', 'source'],
                'metric_types': ['contacts', 'leads', 'data_points', 'resources']
            },
            
            # 🎯 PERFORMANCE/QUALITY CONCEPTS
            'performance': {
                'keywords': ['performance', 'qualità', 'efficienza', 'accuratezza', 'successo', 'rate',
                           'quality', 'efficiency', 'accuracy', 'success', 'score', 'rating'],
                'metric_types': ['conversion_rate', 'quality_score', 'performance_metrics']
            },
            
            # 🎯 COMMUNICATION/OUTREACH CONCEPTS
            'communication': {
                'keywords': ['email', 'messaggio', 'comunicazione', 'sequenza', 'campagna', 'outreach',
                           'message', 'communication', 'sequence', 'campaign', 'newsletter'],
                'metric_types': ['email_sequences', 'campaigns', 'communications']
            },
            
            # 🎯 FINANCIAL/BUSINESS CONCEPTS
            'financial': {
                'keywords': ['budget', 'costo', 'prezzo', 'revenue', 'profitto', 'investimento', 'ROI',
                           'cost', 'price', 'profit', 'investment', 'return', 'value'],
                'metric_types': ['revenue', 'costs', 'budget', 'roi']
            },
            
            # 🎯 TIME/TEMPORAL CONCEPTS
            'temporal': {
                'keywords': ['tempo', 'deadline', 'scadenza', 'durata', 'periodo', 'fase',
                           'time', 'duration', 'period', 'phase', 'timeline', 'schedule'],
                'metric_types': ['timeline_days', 'deadlines', 'milestones']
            },
            
            # 🎯 HEALTH/FITNESS CONCEPTS
            'health': {
                'keywords': ['esercizio', 'workout', 'allenamento', 'fitness', 'salute', 'peso',
                           'exercise', 'training', 'health', 'weight', 'nutrition', 'calories'],
                'metric_types': ['workouts', 'exercises', 'health_metrics']
            },
            
            # 🎯 TECHNOLOGY/DEVELOPMENT CONCEPTS
            'technology': {
                'keywords': ['app', 'software', 'API', 'feature', 'bug', 'deployment', 'codice',
                           'application', 'system', 'platform', 'integration', 'code', 'development'],
                'metric_types': ['features', 'deployments', 'integrations', 'apis']
            },
            
            # 🎯 EDUCATION/LEARNING CONCEPTS
            'education': {
                'keywords': ['corso', 'lezione', 'tutorial', 'training', 'apprendimento', 'skill',
                           'course', 'lesson', 'learning', 'knowledge', 'competency', 'certification'],
                'metric_types': ['courses', 'lessons', 'certifications', 'skills']
            }
        }
    
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
                    req_type = self._classify_requirement_type(unit_context, goal_lower)
                    
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
                    domain = self._detect_domain(workspace_goal)
                    
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
        AI-powered extraction of actual achievements from completed tasks
        """
        achievements = {
            'contacts_found': 0,
            'email_sequences': 0,
            'content_pieces': 0,
            'campaigns_created': 0,
            'financial_amounts': [],
            'percentages_achieved': [],
            'time_spent_days': 0,
            'quality_scores': [],
            'raw_extractions': []
        }
        
        for task in completed_tasks:
            task_achievements = await self._extract_single_task_achievements(task)
            
            # Aggregate achievements
            achievements['contacts_found'] += task_achievements.get('contacts_count', 0)
            achievements['email_sequences'] += task_achievements.get('email_sequences_count', 0)
            achievements['content_pieces'] += task_achievements.get('content_count', 0)
            achievements['campaigns_created'] += task_achievements.get('campaigns_count', 0)
            
            if task_achievements.get('financial_amounts'):
                achievements['financial_amounts'].extend(task_achievements['financial_amounts'])
            
            if task_achievements.get('percentages'):
                achievements['percentages_achieved'].extend(task_achievements['percentages'])
            
            if task_achievements.get('quality_scores'):
                achievements['quality_scores'].extend(task_achievements['quality_scores'])
            
            # Store raw extraction for debugging
            achievements['raw_extractions'].append({
                'task_id': task.get('id'),
                'task_name': task.get('name'),
                'extractions': task_achievements
            })
        
        logger.info(f"📊 Extracted achievements: {achievements['contacts_found']} contacts, {achievements['email_sequences']} sequences")
        return achievements
    
    async def _extract_single_task_achievements(self, task: Dict) -> Dict[str, Any]:
        """
        Extract measurable achievements from a single task
        """
        achievements = {
            'contacts_count': 0,
            'email_sequences_count': 0,
            'content_count': 0,
            'campaigns_count': 0,
            'financial_amounts': [],
            'percentages': [],
            'quality_scores': []
        }
        
        result = task.get('result', {})
        
        # 1. Extract from detailed_results_json
        if result.get('detailed_results_json'):
            try:
                detailed_data = json.loads(result['detailed_results_json']) if isinstance(result['detailed_results_json'], str) else result['detailed_results_json']
                
                # Contact extraction
                if 'contacts' in detailed_data:
                    contacts = detailed_data['contacts']
                    if isinstance(contacts, list):
                        achievements['contacts_count'] = len(contacts)
                    elif isinstance(contacts, dict) and 'length' in contacts:
                        achievements['contacts_count'] = contacts['length']
                
                # Email sequences extraction
                if 'email_sequences' in detailed_data:
                    sequences = detailed_data['email_sequences']
                    if isinstance(sequences, list):
                        achievements['email_sequences_count'] = len(sequences)
                    elif isinstance(sequences, dict) and 'total_sequences' in sequences:
                        achievements['email_sequences_count'] = sequences['total_sequences']
                
                # Content extraction
                content_fields = ['content_calendar', 'posts', 'articles', 'templates']
                for field in content_fields:
                    if field in detailed_data:
                        content = detailed_data[field]
                        if isinstance(content, list):
                            achievements['content_count'] += len(content)
                        elif isinstance(content, dict) and 'items' in content:
                            achievements['content_count'] += len(content['items'])
                
                # Quality scores
                if 'quality_score' in detailed_data:
                    achievements['quality_scores'].append(detailed_data['quality_score'])
                
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"Failed to parse detailed_results_json for task {task.get('id')}: {e}")
        
        # 2. Extract from summary using AI patterns
        summary_text = result.get('summary', '')
        if summary_text:
            # Use regex patterns to find numerical achievements
            for pattern in self.numerical_patterns:
                matches = re.finditer(pattern, summary_text.lower())
                for match in matches:
                    try:
                        value = float(match.group(1))
                        context = match.group(2) if len(match.groups()) > 1 else ""
                        
                        if 'contact' in context:
                            achievements['contacts_count'] = max(achievements['contacts_count'], int(value))
                        elif 'email' in context or 'sequenc' in context:
                            achievements['email_sequences_count'] = max(achievements['email_sequences_count'], int(value))
                        elif '%' in match.group(0):
                            achievements['percentages'].append(value)
                            
                    except (ValueError, IndexError):
                        continue
        
        return achievements
    
    async def _validate_single_requirement(
        self, 
        requirement: Dict[str, Any], 
        achievements: Dict[str, Any],
        workspace_goal: str
    ) -> GoalValidationResult:
        """
        Validate a single requirement against actual achievements
        """
        req_type = requirement['type']
        target_value = requirement['target_value']
        is_minimum = requirement.get('is_minimum', False)
        
        # Map requirement to achievement
        if req_type == 'contacts':
            actual_value = achievements['contacts_found']
        elif req_type == 'email_sequences':
            actual_value = achievements['email_sequences']
        elif req_type == 'content':
            actual_value = achievements['content_pieces']
        elif req_type == 'percentage':
            # For percentages, check if any achievement meets target
            relevant_percentages = achievements['percentages_achieved']
            actual_value = max(relevant_percentages) if relevant_percentages else 0
        else:
            actual_value = 0
        
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
                'unit': requirement['unit']
            }
        )
    
    def _classify_requirement_type(self, unit_context: str, full_goal: str) -> str:
        """
        🧠 AI-DRIVEN UNIVERSAL CLASSIFICATION - Scalable across all domains
        
        Uses concept-based pattern matching to classify any requirement type
        regardless of domain (marketing, fitness, tech, finance, etc.)
        """
        unit_lower = unit_context.lower()
        goal_lower = full_goal.lower()
        combined_text = f"{unit_lower} {goal_lower}"
        
        # 🎯 STEP 1: Direct detection - Most specific patterns first
        if any(curr in unit_lower for curr in ['eur', 'usd', 'gbp', '$', '€', '£', '¥']):
            return 'financial'
        elif any(contact_word in unit_lower for contact_word in ['contatti', 'contacts', 'contatto', 'contact']):
            return 'contacts'
        elif any(email_word in unit_lower for email_word in ['email', 'sequenze', 'sequence', 'messaggio', 'message']):
            return 'email_sequences'
        elif any(time_word in unit_lower for time_word in ['settimana', 'week', 'giorno', 'day', 'mese', 'month', 'anno', 'year', 'ora', 'hour']):
            return 'temporal'
        elif '%' in combined_text or any(word in combined_text for word in ['percentuale', 'percentage', 'rate', 'ratio']):
            return 'percentage'
        
        # 🎯 STEP 2: AI-driven concept-based classification
        concept_scores = {}
        
        for concept_name, concept_data in self.universal_concept_patterns.items():
            score = 0
            keywords = concept_data['keywords']
            
            # Score based on keyword matches in context and goal
            for keyword in keywords:
                if keyword in combined_text:
                    score += 2  # Higher weight for exact matches
                elif any(keyword in word for word in combined_text.split()):
                    score += 1  # Partial matches
            
            # Boost score if unit context contains concept-related words
            for keyword in keywords:
                if keyword in unit_lower:
                    score += 3  # Even higher weight for unit context matches
            
            if score > 0:
                concept_scores[concept_name] = score
        
        # 🎯 STEP 3: Select best matching concept
        if concept_scores:
            best_concept = max(concept_scores, key=concept_scores.get)
            
            # Map concept to specific type based on context
            concept_data = self.universal_concept_patterns[best_concept]
            metric_types = concept_data['metric_types']
            
            # Choose most appropriate metric type based on unit context
            for metric_type in metric_types:
                metric_keywords = metric_type.split('_')
                if any(keyword in unit_lower for keyword in metric_keywords):
                    return metric_type
            
            # Return first metric type if no specific match
            return metric_types[0] if metric_types else best_concept
        
        # 🎯 STEP 4: Fallback intelligent classification based on unit structure
        if len(unit_lower.split()) > 1:
            # Multi-word units likely represent complex deliverables
            return 'deliverables'
        elif unit_lower.endswith(('i', 'e', 's')):
            # Plural forms likely represent countable items
            return 'items'
        else:
            # Single word units default to general classification
            return 'general'
    
    def _detect_domain(self, workspace_goal: str) -> str:
        """
        🧠 AI-DRIVEN UNIVERSAL DOMAIN DETECTION - Completely scalable
        
        Uses concept-based analysis to detect domain regardless of specific keywords
        """
        goal_lower = workspace_goal.lower()
        
        concept_scores = {}
        for concept_name, concept_data in self.universal_concept_patterns.items():
            score = 0
            keywords = concept_data['keywords']
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword in goal_lower:
                    score += 2
                elif any(keyword in word for word in goal_lower.split()):
                    score += 1
            
            if score > 0:
                concept_scores[concept_name] = score
        
        # Return the concept with highest score, or 'general' if no matches
        if concept_scores:
            return max(concept_scores, key=concept_scores.get)
        else:
            return 'general'
    
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
        🎯 STEP 3: Enhanced AI-driven generation of actionable recommendations
        Now integrates with Goal-Driven Task Planner for immediate corrective action
        """
        recommendations = []
        req_type = requirement['type']
        
        if gap_percentage > 50:  # Significant gap - TRIGGER CORRECTIVE TASKS
            if req_type == 'contacts':
                recommendations.extend([
                    f"🚨 CRITICAL GAP: Current achievement is {actual}/{target} contacts ({gap_percentage:.1f}% gap)",
                    f"📋 AUTO-GENERATING CORRECTIVE TASK: 'Collect {target-actual} additional ICP contacts'",
                    "🎯 Task will have numerical validation: cannot complete until target reached",
                    "🔍 Will use memory insights from previous contact research failures",
                    "📊 Implementing immediate quality gates and validation"
                ])
            elif req_type == 'email_sequences':
                recommendations.extend([
                    f"📧 CRITICAL EMAIL DEFICIT: Created {actual}/{target} sequences ({gap_percentage:.1f}% gap)",
                    f"📋 AUTO-GENERATING CORRECTIVE TASK: 'Create {target-actual} email sequences immediately'",
                    "✨ Task will focus on complete, ready-to-deploy sequences",
                    "📋 Numerical validation: must create exact number required"
                ])
            else:
                recommendations.extend([
                    f"⚠️ CRITICAL TARGET SHORTFALL: {gap_percentage:.1f}% gap in {req_type}",
                    f"📋 AUTO-GENERATING CORRECTIVE TASK: Close {target-actual} {requirement.get('unit', 'units')} gap",
                    "🔄 Task will use failure insights to avoid previous mistakes",
                    "📈 Immediate action required - 24hr deadline"
                ])
        elif gap_percentage > 20:  # Moderate gap - SUGGEST OPTIMIZATION
            recommendations.extend([
                f"📊 MODERATE GAP: {gap_percentage:.1f}% shortfall, optimization needed",
                f"📋 SUGGEST TASK: Optimize approach to close {target-actual} {requirement.get('unit', 'units')} gap",
                "🔧 Fine-tune current processes with memory-guided improvements"
            ])
        else:  # Goal achieved or close
            recommendations.extend([
                f"✅ TARGET ACHIEVED: {actual}/{target} {requirement['unit']} completed",
                "🎯 Consider setting stretch goals for additional value",
                "📝 SUCCESS PATTERN: Document approach for future similar goals"
            ])
        
        return recommendations
    
    def _calculate_confidence(self, achievements: Dict, requirement: Dict) -> float:
        """
        Calculate confidence score based on data quality and extraction method
        """
        base_confidence = 0.7  # Base confidence
        
        # Boost confidence if we have detailed extractions
        if achievements.get('raw_extractions'):
            detailed_extractions = sum(1 for ext in achievements['raw_extractions'] if ext['extractions'])
            if detailed_extractions > 0:
                base_confidence += 0.2
        
        # Boost if we have structured data
        if requirement['type'] in ['contacts', 'email_sequences'] and achievements.get('contacts_found', 0) > 0:
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
                
                if corrective_task:
                    corrective_tasks.append(corrective_task)
                    
                    # 3. 📊 LOG COURSE CORRECTION
                    logger.warning(
                        f"🔄 COURSE CORRECTION triggered for {failure.target_requirement}: "
                        f"Gap {failure.gap_percentage:.1f}%, Created task: {corrective_task['name']}"
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
                current_task=None,
                context_filter={
                    "insight_types": ["failure_lesson", "constraint"],
                    "relevance_tags": [f"metric_{failure.extracted_metrics.get('type', 'unknown')}"],
                    "limit": 5
                }
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