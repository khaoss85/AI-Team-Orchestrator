# backend/ai_quality_assurance/quality_gates.py

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .goal_validator import goal_validator, ValidationSeverity, GoalValidationResult

logger = logging.getLogger(__name__)

class GateStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"

class PhaseTransition(Enum):
    ANALYSIS_TO_IMPLEMENTATION = "analysis_to_implementation"
    IMPLEMENTATION_TO_FINALIZATION = "implementation_to_finalization"
    FINALIZATION_TO_COMPLETION = "finalization_to_completion"

@dataclass
class QualityGateResult:
    """Result of quality gate evaluation"""
    gate_status: GateStatus
    can_proceed: bool
    blocking_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    validation_results: List[GoalValidationResult]
    gate_confidence: float
    next_actions: List[str]

class AIQualityGates:
    """
    AI-driven quality gates that prevent phase transitions when goals aren't met
    Scalable across all domains and project types
    """
    
    def __init__(self):
        # Define gate criteria for different phase transitions
        self.gate_criteria = {
            PhaseTransition.ANALYSIS_TO_IMPLEMENTATION: {
                'required_validations': ['contacts', 'research_completeness'],
                'critical_threshold': 0.8,  # 80% of goals must be met
                'warning_threshold': 0.6,   # 60% triggers warnings
                'allow_with_plan': True     # Can proceed with remediation plan
            },
            PhaseTransition.IMPLEMENTATION_TO_FINALIZATION: {
                'required_validations': ['deliverables', 'quality_scores', 'completeness'],
                'critical_threshold': 0.9,  # 90% for implementation phase
                'warning_threshold': 0.7,
                'allow_with_plan': True
            },
            PhaseTransition.FINALIZATION_TO_COMPLETION: {
                'required_validations': ['all_goals', 'quality_assurance', 'client_readiness'],
                'critical_threshold': 0.95, # 95% for final completion
                'warning_threshold': 0.8,
                'allow_with_plan': False    # Must be complete for final delivery
            }
        }
    
    async def evaluate_phase_transition_readiness(
        self,
        current_phase: str,
        target_phase: str,
        workspace_id: str,
        workspace_goal: str,
        completed_tasks: List[Dict],
        pending_tasks: List[Dict]
    ) -> QualityGateResult:
        """
        AI-driven evaluation of readiness for phase transition
        """
        try:
            # Determine transition type
            transition = self._determine_transition_type(current_phase, target_phase)
            if not transition:
                return self._create_error_result(f"Unknown phase transition: {current_phase} -> {target_phase}")
            
            # Get gate criteria
            criteria = self.gate_criteria[transition]
            
            # 1. Validate workspace goals achievement
            goal_validations = await goal_validator.validate_workspace_goal_achievement(
                workspace_goal, completed_tasks, workspace_id
            )
            
            # 2. Evaluate phase-specific criteria
            phase_evaluation = await self._evaluate_phase_specific_criteria(
                transition, completed_tasks, pending_tasks, workspace_goal
            )
            
            # 3. Calculate overall gate status
            gate_result = await self._calculate_gate_status(
                goal_validations, phase_evaluation, criteria, transition
            )
            
            # 4. Generate actionable recommendations
            gate_result.recommendations = await self._generate_gate_recommendations(
                gate_result, goal_validations, phase_evaluation, transition
            )
            
            # 5. Log gate evaluation
            self._log_gate_evaluation(workspace_id, transition, gate_result)
            
            return gate_result
            
        except Exception as e:
            logger.error(f"Error in quality gate evaluation: {e}", exc_info=True)
            return self._create_error_result(f"Quality gate evaluation failed: {str(e)}")
    
    async def validate_task_completion_against_goals(
        self,
        task: Dict,
        workspace_goal: str,
        all_completed_tasks: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a task completion contributes adequately to workspace goals
        """
        try:
            # Extract what this task should contribute
            task_requirements = await self._extract_task_expected_contribution(task, workspace_goal)
            
            # Validate actual contribution
            validations = await goal_validator.validate_workspace_goal_achievement(
                workspace_goal, [task], task.get('workspace_id', '')
            )
            
            # Check if task meets its expected contribution
            issues = []
            is_adequate = True
            
            for validation in validations:
                if validation.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                    if validation.gap_percentage > 50:  # More than 50% gap
                        is_adequate = False
                        issues.append(
                            f"Task '{task.get('name')}' achieved only {validation.actual_achievement} "
                            f"vs expected {validation.target_requirement} ({validation.gap_percentage:.1f}% gap)"
                        )
            
            return is_adequate, issues
            
        except Exception as e:
            logger.error(f"Error validating task completion: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    async def check_project_completion_readiness(
        self,
        workspace_id: str,
        workspace_goal: str,
        all_tasks: List[Dict]
    ) -> QualityGateResult:
        """
        Comprehensive check for project completion readiness
        """
        completed_tasks = [t for t in all_tasks if t.get('status') == 'completed']
        pending_tasks = [t for t in all_tasks if t.get('status') in ['pending', 'in_progress']]
        
        return await self.evaluate_phase_transition_readiness(
            'finalization', 'completion', workspace_id, workspace_goal, completed_tasks, pending_tasks
        )
    
    def _determine_transition_type(self, current_phase: str, target_phase: str) -> Optional[PhaseTransition]:
        """
        Determine the type of phase transition
        """
        transition_map = {
            ('analysis', 'implementation'): PhaseTransition.ANALYSIS_TO_IMPLEMENTATION,
            ('implementation', 'finalization'): PhaseTransition.IMPLEMENTATION_TO_FINALIZATION,
            ('finalization', 'completion'): PhaseTransition.FINALIZATION_TO_COMPLETION,
        }
        
        key = (current_phase.lower(), target_phase.lower())
        return transition_map.get(key)
    
    async def _evaluate_phase_specific_criteria(
        self,
        transition: PhaseTransition,
        completed_tasks: List[Dict],
        pending_tasks: List[Dict],
        workspace_goal: str
    ) -> Dict[str, Any]:
        """
        Evaluate criteria specific to the phase transition
        """
        evaluation = {
            'task_completion_rate': 0.0,
            'quality_scores': [],
            'deliverable_readiness': 0.0,
            'dependency_satisfaction': 1.0,
            'phase_specific_metrics': {}
        }
        
        total_tasks = len(completed_tasks) + len(pending_tasks)
        if total_tasks > 0:
            evaluation['task_completion_rate'] = len(completed_tasks) / total_tasks
        
        # Extract quality scores from completed tasks
        for task in completed_tasks:
            result = task.get('result', {})
            if result.get('detailed_results_json'):
                try:
                    import json
                    detailed = json.loads(result['detailed_results_json']) if isinstance(result['detailed_results_json'], str) else result['detailed_results_json']
                    if 'quality_score' in detailed:
                        evaluation['quality_scores'].append(detailed['quality_score'])
                except:
                    pass
        
        # Phase-specific evaluations
        if transition == PhaseTransition.ANALYSIS_TO_IMPLEMENTATION:
            evaluation['phase_specific_metrics'] = await self._evaluate_analysis_completeness(completed_tasks, workspace_goal)
        elif transition == PhaseTransition.IMPLEMENTATION_TO_FINALIZATION:
            evaluation['phase_specific_metrics'] = await self._evaluate_implementation_quality(completed_tasks, workspace_goal)
        elif transition == PhaseTransition.FINALIZATION_TO_COMPLETION:
            evaluation['phase_specific_metrics'] = await self._evaluate_completion_readiness(completed_tasks, workspace_goal)
        
        return evaluation
    
    async def _evaluate_analysis_completeness(self, completed_tasks: List[Dict], workspace_goal: str) -> Dict[str, Any]:
        """
        Evaluate if analysis phase is complete enough for implementation
        """
        metrics = {
            'research_tasks_completed': 0,
            'data_collection_adequacy': 0.0,
            'requirements_clarity': 0.0
        }
        
        # Count research/analysis tasks
        for task in completed_tasks:
            task_name = task.get('name', '').lower()
            if any(keyword in task_name for keyword in ['research', 'analysis', 'investigate', 'gather']):
                metrics['research_tasks_completed'] += 1
        
        # Check data collection adequacy using goal validation
        goal_validations = await goal_validator.validate_workspace_goal_achievement(
            workspace_goal, completed_tasks, ''
        )
        
        if goal_validations:
            adequacy_scores = [1.0 - (v.gap_percentage / 100) for v in goal_validations]
            metrics['data_collection_adequacy'] = sum(adequacy_scores) / len(adequacy_scores)
        
        return metrics
    
    async def _evaluate_implementation_quality(self, completed_tasks: List[Dict], workspace_goal: str) -> Dict[str, Any]:
        """
        Evaluate implementation phase quality
        """
        metrics = {
            'deliverables_created': 0,
            'average_quality_score': 0.0,
            'implementation_completeness': 0.0
        }
        
        quality_scores = []
        deliverable_count = 0
        
        for task in completed_tasks:
            task_name = task.get('name', '').lower()
            if any(keyword in task_name for keyword in ['create', 'develop', 'implement', 'build', 'design']):
                deliverable_count += 1
                
                # Extract quality scores
                result = task.get('result', {})
                if result.get('detailed_results_json'):
                    try:
                        import json
                        detailed = json.loads(result['detailed_results_json']) if isinstance(result['detailed_results_json'], str) else result['detailed_results_json']
                        if 'quality_score' in detailed:
                            quality_scores.append(detailed['quality_score'])
                    except:
                        pass
        
        metrics['deliverables_created'] = deliverable_count
        if quality_scores:
            metrics['average_quality_score'] = sum(quality_scores) / len(quality_scores)
        
        return metrics
    
    async def _evaluate_completion_readiness(self, completed_tasks: List[Dict], workspace_goal: str) -> Dict[str, Any]:
        """
        Evaluate readiness for project completion
        """
        metrics = {
            'all_goals_achieved': False,
            'client_ready_deliverables': 0,
            'quality_assurance_passed': False
        }
        
        # Check goal achievement
        goal_validations = await goal_validator.validate_workspace_goal_achievement(
            workspace_goal, completed_tasks, ''
        )
        
        critical_failures = [v for v in goal_validations if v.severity == ValidationSeverity.CRITICAL]
        metrics['all_goals_achieved'] = len(critical_failures) == 0
        
        # Count client-ready deliverables
        for task in completed_tasks:
            result = task.get('result', {})
            context = task.get('context_data', {})
            
            # Check if deliverable is marked as client-ready
            if (context.get('is_final_deliverable') or 
                'deliverable' in task.get('name', '').lower() or
                result.get('client_ready')):
                metrics['client_ready_deliverables'] += 1
        
        return metrics
    
    async def _calculate_gate_status(
        self,
        goal_validations: List[GoalValidationResult],
        phase_evaluation: Dict[str, Any],
        criteria: Dict[str, Any],
        transition: PhaseTransition
    ) -> QualityGateResult:
        """
        Calculate overall gate status based on validations and criteria
        """
        blocking_issues = []
        warnings = []
        
        # Check goal validation results
        critical_validations = [v for v in goal_validations if v.severity == ValidationSeverity.CRITICAL]
        high_validations = [v for v in goal_validations if v.severity == ValidationSeverity.HIGH]
        
        # Calculate achievement rate
        if goal_validations:
            achievement_scores = [1.0 - (v.gap_percentage / 100) for v in goal_validations]
            overall_achievement = sum(achievement_scores) / len(achievement_scores)
        else:
            overall_achievement = 1.0  # No specific goals to validate
        
        # Determine gate status
        can_proceed = True
        gate_status = GateStatus.PASSED
        
        # Check critical threshold
        if overall_achievement < criteria['critical_threshold']:
            if not criteria.get('allow_with_plan', False):
                can_proceed = False
                gate_status = GateStatus.BLOCKED
                blocking_issues.append(
                    f"Achievement rate {overall_achievement:.1%} below critical threshold {criteria['critical_threshold']:.1%}"
                )
            else:
                gate_status = GateStatus.FAILED
                warnings.append(
                    f"Achievement rate {overall_achievement:.1%} below threshold - remediation plan required"
                )
        elif overall_achievement < criteria['warning_threshold']:
            gate_status = GateStatus.WARNING
            warnings.append(
                f"Achievement rate {overall_achievement:.1%} below optimal threshold"
            )
        
        # Add specific critical issues
        for validation in critical_validations:
            blocking_issues.append(validation.validation_message)
        
        for validation in high_validations:
            warnings.append(validation.validation_message)
        
        # Calculate confidence
        confidence = min(1.0, sum(v.confidence for v in goal_validations) / len(goal_validations)) if goal_validations else 0.8
        
        return QualityGateResult(
            gate_status=gate_status,
            can_proceed=can_proceed,
            blocking_issues=blocking_issues,
            warnings=warnings,
            recommendations=[],  # Will be filled by _generate_gate_recommendations
            validation_results=goal_validations,
            gate_confidence=confidence,
            next_actions=[]
        )
    
    async def _generate_gate_recommendations(
        self,
        gate_result: QualityGateResult,
        goal_validations: List[GoalValidationResult],
        phase_evaluation: Dict[str, Any],
        transition: PhaseTransition
    ) -> List[str]:
        """
        Generate AI-driven recommendations for gate passage
        """
        recommendations = []
        
        if gate_result.gate_status == GateStatus.BLOCKED:
            recommendations.extend([
                "🚨 CRITICAL: Project cannot proceed to next phase",
                "📋 IMMEDIATE ACTIONS REQUIRED:"
            ])
            
            # Add specific recommendations from validations
            for validation in goal_validations:
                if validation.severity == ValidationSeverity.CRITICAL:
                    recommendations.extend(validation.recommendations)
        
        elif gate_result.gate_status == GateStatus.FAILED:
            recommendations.extend([
                "⚠️ PHASE TRANSITION AT RISK",
                "🔧 REMEDIATION PLAN REQUIRED:"
            ])
            
            for validation in goal_validations:
                if validation.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                    recommendations.extend(validation.recommendations)
        
        elif gate_result.gate_status == GateStatus.WARNING:
            recommendations.extend([
                "⚡ OPTIMIZATION RECOMMENDED",
                "💡 SUGGESTED IMPROVEMENTS:"
            ])
            
            for validation in goal_validations:
                if validation.severity == ValidationSeverity.HIGH:
                    recommendations.extend(validation.recommendations[:2])  # Limit to top 2
        
        else:  # PASSED
            recommendations.extend([
                "✅ PHASE TRANSITION APPROVED",
                "🎯 CONTINUE TO NEXT PHASE"
            ])
        
        # Add phase-specific recommendations
        if transition == PhaseTransition.ANALYSIS_TO_IMPLEMENTATION:
            if phase_evaluation.get('phase_specific_metrics', {}).get('data_collection_adequacy', 0) < 0.8:
                recommendations.append("📊 Consider additional data collection before implementation")
        
        return recommendations
    
    async def _extract_task_expected_contribution(self, task: Dict, workspace_goal: str) -> Dict[str, Any]:
        """
        Extract what a task was expected to contribute to workspace goals
        """
        task_name = task.get('name', '').lower()
        task_description = task.get('description', '').lower()
        
        expected_contribution = {
            'contacts_expected': 0,
            'sequences_expected': 0,
            'deliverables_expected': 0
        }
        
        # Use regex to extract expected contributions from task description
        import re
        
        # Look for numerical expectations in task description
        if 'contact' in task_description or 'contact' in task_name:
            # Try to extract expected number of contacts
            match = re.search(r'(\d+)\s*contatti?|contacts?', workspace_goal.lower())
            if match:
                expected_contribution['contacts_expected'] = int(match.group(1))
        
        if 'email' in task_description or 'sequence' in task_description:
            match = re.search(r'(\d+)\s*sequenc', workspace_goal.lower())
            if match:
                expected_contribution['sequences_expected'] = int(match.group(1))
        
        return expected_contribution
    
    def _create_error_result(self, error_message: str) -> QualityGateResult:
        """
        Create a quality gate result for error cases
        """
        return QualityGateResult(
            gate_status=GateStatus.BLOCKED,
            can_proceed=False,
            blocking_issues=[error_message],
            warnings=[],
            recommendations=["🔧 Fix system error before proceeding"],
            validation_results=[],
            gate_confidence=0.0,
            next_actions=["Contact system administrator"]
        )
    
    def _log_gate_evaluation(self, workspace_id: str, transition: PhaseTransition, result: QualityGateResult):
        """
        Log quality gate evaluation for monitoring
        """
        logger.info(
            f"🚦 Quality Gate [{transition.value}] for workspace {workspace_id}: "
            f"{result.gate_status.value.upper()} (can_proceed: {result.can_proceed})"
        )
        
        if result.blocking_issues:
            logger.warning(f"🚨 Blocking issues: {result.blocking_issues}")
        
        if result.warnings:
            logger.info(f"⚠️ Warnings: {result.warnings}")

# Singleton instance
quality_gates = AIQualityGates()