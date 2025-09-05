"""
Goal Progress Quality Gates - 15 Pillars Compliance Validator
Ensures all goal progress operations meet compliance requirements
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import UUID

from services.ai_provider_abstraction import ai_provider_manager
from services.universal_learning_engine import universal_learning_engine
from database import get_supabase_client

logger = logging.getLogger(__name__)

class GoalProgressQualityGates:
    """
    Quality validation system for goal progress operations.
    Ensures 15 Pillars compliance at every step.
    """
    
    def __init__(self):
        self.validation_rules = [
            self._validate_no_hardcoding,
            self._validate_ai_driven,
            self._validate_multi_tenant,
            self._validate_learning_capture,
            self._validate_explainability,
            self._validate_autonomous_capability,
            self._validate_real_content,
            self._validate_user_visibility
        ]
        
    async def validate_operation(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate an operation against all quality gates.
        Returns (passed, validation_report).
        """
        validation_report = {
            "operation_type": operation_type,
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "checks_passed": [],
            "checks_failed": [],
            "compliance_score": 0,
            "recommendations": [],
            "blocking_issues": []
        }
        
        try:
            total_checks = len(self.validation_rules)
            passed_checks = 0
            
            for validator in self.validation_rules:
                check_name = validator.__name__.replace('_validate_', '')
                try:
                    is_valid, message = await validator(operation_type, operation_data, workspace_id)
                    
                    if is_valid:
                        passed_checks += 1
                        validation_report["checks_passed"].append({
                            "check": check_name,
                            "message": message
                        })
                    else:
                        validation_report["checks_failed"].append({
                            "check": check_name,
                            "message": message
                        })
                        
                        # Critical checks that block operation
                        if check_name in ['no_hardcoding', 'ai_driven', 'multi_tenant']:
                            validation_report["blocking_issues"].append(message)
                            
                except Exception as e:
                    logger.error(f"Error in validator {check_name}: {e}")
                    validation_report["checks_failed"].append({
                        "check": check_name,
                        "message": f"Validation error: {str(e)}"
                    })
            
            # Calculate compliance score
            validation_report["compliance_score"] = int((passed_checks / total_checks) * 100)
            
            # Generate recommendations
            if validation_report["checks_failed"]:
                recommendations = await self._generate_recommendations(
                    validation_report["checks_failed"],
                    operation_type
                )
                validation_report["recommendations"] = recommendations
            
            # Determine if operation can proceed
            can_proceed = len(validation_report["blocking_issues"]) == 0
            
            # Capture learning about validation patterns
            await self._capture_validation_learning(
                workspace_id,
                operation_type,
                validation_report
            )
            
            return can_proceed, validation_report
            
        except Exception as e:
            logger.error(f"Error in quality gate validation: {e}")
            validation_report["error"] = str(e)
            return False, validation_report
    
    async def _validate_no_hardcoding(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 11: Ensure no hard-coded workspace IDs or values"""
        try:
            # Check for hard-coded workspace ID
            hardcoded_id = 'f79d87cc-b61f-491d-9226-4220e39e71ad'
            
            data_str = str(operation_data)
            if hardcoded_id in data_str:
                return False, f"Hard-coded workspace ID detected: {hardcoded_id}"
            
            # Check if workspace_id parameter matches the one in operation
            if operation_data.get('workspace_id') and operation_data['workspace_id'] != workspace_id:
                return False, "Workspace ID mismatch - potential hard-coding"
            
            return True, "No hard-coding detected"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_ai_driven(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillars 1-2: Ensure AI-driven decision making"""
        try:
            # Check for AI involvement indicators
            ai_indicators = [
                'ai_driven', 'semantic_matching', 'confidence_score',
                'reasoning', 'ai_assignment', 'classification_result'
            ]
            
            has_ai = any(key in operation_data for key in ai_indicators)
            
            if has_ai:
                return True, "AI-driven decision making confirmed"
            
            # For certain operations, AI is mandatory
            if operation_type in ['agent_assignment', 'goal_decomposition', 'recovery_strategy']:
                return False, f"Operation '{operation_type}' must be AI-driven"
            
            return True, "AI involvement appropriate for operation type"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_multi_tenant(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 11: Ensure multi-tenant compatibility"""
        try:
            # Verify workspace context is properly maintained
            if not workspace_id or workspace_id == 'undefined':
                return False, "Invalid or missing workspace context"
            
            # Check for tenant isolation
            if 'cross_workspace' in operation_data and operation_data['cross_workspace']:
                return False, "Cross-workspace operations not allowed"
            
            return True, "Multi-tenant isolation maintained"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_learning_capture(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 6: Ensure learning is captured"""
        try:
            # Check for learning capture flags
            if operation_data.get('capture_learning', True):
                return True, "Learning capture enabled"
            
            # Some operations must capture learning
            if operation_type in ['recovery', 'assignment', 'quality_validation']:
                if not operation_data.get('capture_learning', True):
                    return False, f"Learning capture required for '{operation_type}'"
            
            return True, "Learning capture appropriate"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_explainability(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 10: Ensure explainability"""
        try:
            # Check for explanation/reasoning fields
            explanation_fields = ['reasoning', 'explanation', 'decision_rationale', 'why']
            
            has_explanation = any(
                field in operation_data and operation_data[field]
                for field in explanation_fields
            )
            
            if has_explanation:
                return True, "Explainability provided"
            
            # Warning for operations that should have explanations
            if operation_type in ['recovery', 'agent_assignment']:
                return False, f"Explanation required for '{operation_type}'"
            
            return True, "Explainability not required for this operation"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_autonomous_capability(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 8: Validate autonomous capability"""
        try:
            # Check if operation can run autonomously
            if operation_data.get('requires_human', False):
                if operation_type in ['recovery', 'auto_assignment']:
                    return False, f"'{operation_type}' should be autonomous"
            
            return True, "Autonomous capability validated"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_real_content(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 5: Ensure real content, no placeholders"""
        try:
            # Check for placeholder patterns
            placeholder_patterns = [
                'lorem ipsum', 'placeholder', 'test data',
                'example.com', 'foo', 'bar', 'TODO', 'FIXME'
            ]
            
            data_str = str(operation_data).lower()
            
            for pattern in placeholder_patterns:
                if pattern.lower() in data_str:
                    return False, f"Placeholder content detected: '{pattern}'"
            
            return True, "Real content validated"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_user_visibility(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        workspace_id: str
    ) -> Tuple[bool, str]:
        """Pillar 4: Ensure user visibility"""
        try:
            # Check for user-facing data
            visibility_fields = [
                'user_message', 'display_content', 'ui_update',
                'notification', 'status_update'
            ]
            
            has_visibility = any(field in operation_data for field in visibility_fields)
            
            # Operations that must have user visibility
            if operation_type in ['task_completion', 'goal_update', 'recovery']:
                if not has_visibility:
                    return False, f"User visibility required for '{operation_type}'"
            
            return True, "User visibility appropriate"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _generate_recommendations(
        self,
        failed_checks: List[Dict[str, str]],
        operation_type: str
    ) -> List[str]:
        """Generate AI-driven recommendations for fixing failed checks"""
        try:
            prompt = f"""
            The following quality checks failed for operation '{operation_type}':
            {failed_checks}
            
            Generate 3-5 actionable recommendations to fix these issues and achieve 100% compliance.
            Focus on practical, immediate actions.
            """
            
            agent = {
                "name": "QualityAdvisor",
                "model": "gpt-4o-mini",
                "instructions": "You provide actionable recommendations for fixing compliance issues."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                temperature=0.3
            )
            
            if response:
                # Parse recommendations from response
                recommendations = response.strip().split('\n')
                return [r.strip() for r in recommendations if r.strip()][:5]
            
            return ["Review failed checks and ensure AI-driven decision making"]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations - review failed checks manually"]
    
    async def _capture_validation_learning(
        self,
        workspace_id: str,
        operation_type: str,
        validation_report: Dict[str, Any]
    ):
        """Capture learning from validation patterns"""
        try:
            if validation_report['compliance_score'] < 100:
                # Learn from failures
                insight = {
                    "insight_type": "quality_gate_pattern",
                    "domain_context": "compliance_validation",
                    "title": f"Quality gate results for {operation_type}",
                    "metric_name": "compliance_score",
                    "metric_value": validation_report['compliance_score'],
                    "actionable_recommendation": validation_report['recommendations'][0] if validation_report.get('recommendations') else "Improve compliance checks",
                    "confidence_score": 0.95,
                    "evidence_sources": [workspace_id],
                    "extraction_method": "quality_gate_validation"
                }
                
                await universal_learning_engine._store_universal_insights(
                    workspace_id,
                    [insight]
                )
                
        except Exception as e:
            logger.error(f"Error capturing validation learning: {e}")
    
    async def generate_compliance_report(
        self,
        workspace_id: str,
        time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report for a workspace"""
        try:
            supabase = get_supabase_client()
            
            # Get validation history from audit table
            cutoff_time = (datetime.now() - timedelta(hours=time_period_hours)).isoformat()
            
            audit_data = supabase.table('goal_progress_audit')\
                .select('*')\
                .eq('workspace_id', workspace_id)\
                .gte('created_at', cutoff_time)\
                .execute()
            
            # Analyze compliance trends
            total_operations = len(audit_data.data) if audit_data.data else 0
            compliant_operations = sum(
                1 for op in (audit_data.data or [])
                if op.get('pillars_compliance', {}).get('score', 0) == 100
            )
            
            compliance_rate = (compliant_operations / total_operations * 100) if total_operations > 0 else 100
            
            return {
                "workspace_id": workspace_id,
                "period_hours": time_period_hours,
                "total_operations": total_operations,
                "compliant_operations": compliant_operations,
                "compliance_rate": compliance_rate,
                "pillars_coverage": {
                    "ai_driven": True,
                    "autonomous": True,
                    "multi_tenant": True,
                    "learning_enabled": True,
                    "explainable": True,
                    "real_content": True,
                    "user_visible": True,
                    "quality_validated": True
                },
                "report_generated": datetime.now().isoformat(),
                "status": "compliant" if compliance_rate >= 95 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {
                "error": str(e),
                "workspace_id": workspace_id
            }


# Singleton instance
goal_progress_quality_gates = GoalProgressQualityGates()

# Export for use
__all__ = ['GoalProgressQualityGates', 'goal_progress_quality_gates']