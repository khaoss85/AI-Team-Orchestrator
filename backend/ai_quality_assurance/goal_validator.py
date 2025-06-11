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
        # AI-powered patterns for extracting numerical requirements
        self.numerical_patterns = [
            # Quantity patterns
            r'(\d+)\s*(contatti?|contacts?|leads?)',
            r'(\d+)\s*(email|sequenc|campaigns?)',
            r'(\d+)\s*(customers?|clients?|users?)',
            r'(\d+)\s*(sales?|deals?|opportunities)',
            r'(\d+)\s*(workouts?|exercises?|sessions?)',
            r'(\d+)\s*(accounts?|portfolios?|investments?)',
            r'(\d+)\s*(products?|items?|assets?)',
            
            # Percentage patterns
            r'(\d+(?:\.\d+)?)\s*%\s*(open[- ]?rate|engagement|conversion|accuracy)',
            r'(\d+(?:\.\d+)?)\s*%\s*(click[- ]?rate|CTR|response)',
            r'(\d+(?:\.\d+)?)\s*%\s*(success|completion|achievement)',
            r'(\d+(?:\.\d+)?)\s*%\s*(growth|increase|improvement)',
            
            # Financial patterns
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(EUR|USD|GBP|\$|€|£)',
            r'(\d+(?:\.\d+)?)\s*([KkMm])\s*(EUR|USD|GBP|\$|€|£)',
            
            # Time patterns
            r'(\d+)\s*(settiman|weeks?|giorni|days?|mesi|months?)',
            r'entro\s+(\d+)\s*(settiman|weeks?|giorni|days?)',
            r'in\s+(\d+)\s*(settiman|weeks?|giorni|days?)',
        ]
        
        # Domain-specific keywords for context understanding
        self.domain_keywords = {
            'marketing': ['contatti', 'contacts', 'leads', 'email', 'campaign', 'open-rate', 'click-rate', 'engagement'],
            'finance': ['EUR', 'USD', 'revenue', 'profit', 'budget', 'cost', 'ROI', 'investment'],
            'sports': ['workout', 'exercise', 'training', 'session', 'performance', 'fitness'],
            'sales': ['deals', 'opportunities', 'pipeline', 'conversion', 'customers', 'clients'],
            'operations': ['efficiency', 'productivity', 'automation', 'process', 'optimization'],
            'content': ['posts', 'articles', 'content', 'publication', 'schedule', 'calendar']
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
        requirements = []
        goal_lower = workspace_goal.lower()
        
        # Extract numerical requirements using patterns
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
                    
                    # Determine requirement type and domain
                    req_type = self._classify_requirement_type(unit_context, goal_lower)
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
        AI-powered classification of requirement type
        """
        unit_lower = unit_context.lower()
        
        if any(word in unit_lower for word in ['contatti', 'contacts', 'leads']):
            return 'contacts'
        elif any(word in unit_lower for word in ['email', 'sequenc', 'campaign']):
            return 'email_sequences'
        elif any(word in unit_lower for word in ['content', 'posts', 'articles']):
            return 'content'
        elif any(word in unit_lower for word in ['open', 'click', 'conversion', 'engagement']):
            return 'percentage'
        elif any(word in unit_lower for word in ['eur', 'usd', 'gbp', '$', '€', '£']):
            return 'financial'
        elif any(word in unit_lower for word in ['workout', 'exercise', 'session']):
            return 'fitness'
        else:
            return 'general'
    
    def _detect_domain(self, workspace_goal: str) -> str:
        """
        AI-powered domain detection
        """
        goal_lower = workspace_goal.lower()
        
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in goal_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        else:
            return 'general'
    
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
        AI-driven generation of actionable recommendations
        """
        recommendations = []
        req_type = requirement['type']
        
        if gap_percentage > 50:  # Significant gap
            if req_type == 'contacts':
                recommendations.extend([
                    f"📈 IMMEDIATE ACTION: Current achievement is {actual}/{target} contacts ({gap_percentage:.1f}% gap)",
                    "🔄 Create additional contact research tasks with specific numerical targets",
                    "🎯 Implement iterative validation: task should not complete until target is reached",
                    "🔍 Consider expanding research sources and methodologies",
                    "📊 Add automated quality gates to prevent phase transitions with incomplete deliverables"
                ])
            elif req_type == 'email_sequences':
                recommendations.extend([
                    f"📧 EMAIL DEFICIT: Created {actual}/{target} sequences ({gap_percentage:.1f}% gap)",
                    "✨ Develop remaining email sequences before project completion",
                    "🎨 Consider templates and automation to scale sequence creation",
                    "📋 Implement sequence validation checklist"
                ])
            else:
                recommendations.extend([
                    f"⚠️ TARGET SHORTFALL: {gap_percentage:.1f}% gap in {req_type}",
                    "🔄 Review and iterate on current approach",
                    "📈 Scale up resources or extend timeline to meet targets"
                ])
        elif gap_percentage > 20:  # Moderate gap
            recommendations.extend([
                f"📊 MINOR GAP: {gap_percentage:.1f}% shortfall, consider optimization",
                "🔧 Fine-tune current processes to close remaining gap"
            ])
        else:  # Goal achieved or close
            recommendations.extend([
                f"✅ TARGET ACHIEVED: {actual}/{target} {requirement['unit']} completed",
                "🎯 Consider setting stretch goals for additional value"
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

# Singleton instance
goal_validator = AIGoalValidator()