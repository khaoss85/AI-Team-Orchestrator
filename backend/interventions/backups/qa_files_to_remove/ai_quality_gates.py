"""
AI Quality Gates System

Implements semantic validation gates that ensure task outputs meet quality standards
before allowing goal progress updates and deliverable creation.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class QualityGateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"

class QualityGate:
    """Base class for quality gates"""
    
    def __init__(self, name: str, threshold: float = 0.7):
        self.name = name
        self.threshold = threshold
    
    async def validate(self, task_data: Dict[str, Any], output: str) -> Tuple[QualityGateResult, Dict[str, Any]]:
        """Validate task output. Returns (result, metadata)"""
        raise NotImplementedError

class SemanticRelevanceGate(QualityGate):
    """Validates that task output is semantically relevant to the task description"""
    
    def __init__(self):
        super().__init__("semantic_relevance", threshold=0.6)
    
    async def validate(self, task_data: Dict[str, Any], output: str) -> Tuple[QualityGateResult, Dict[str, Any]]:
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return QualityGateResult.WARNING, {"error": "No OpenAI API key available"}
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            
            task_name = task_data.get("name", "")
            task_description = task_data.get("description", "")
            
            prompt = f"""Evaluate if the task output is semantically relevant and useful for the given task.

TASK CONTEXT:
- Name: {task_name}
- Description: {task_description}

TASK OUTPUT:
{output[:2000]}  # Limit to first 2000 chars

EVALUATION CRITERIA:
1. Does the output directly address the task requirements?
2. Is the output substantive and meaningful (not placeholder or generic)?
3. Does it provide real value for the intended purpose?
4. Is the quality acceptable for professional use?

Provide a JSON response:
{{
    "relevance_score": 0.0-1.0,
    "is_relevant": true/false,
    "is_substantive": true/false,
    "quality_issues": ["list", "of", "issues"],
    "reasoning": "Brief explanation"
}}

Score 0.8-1.0 for excellent outputs, 0.6-0.8 for good outputs, 0.4-0.6 for acceptable, below 0.4 for poor."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a quality assurance expert who evaluates task outputs for relevance and usefulness."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            relevance_score = result.get("relevance_score", 0.0)
            is_relevant = result.get("is_relevant", False)
            is_substantive = result.get("is_substantive", False)
            quality_issues = result.get("quality_issues", [])
            reasoning = result.get("reasoning", "")
            
            metadata = {
                "relevance_score": relevance_score,
                "is_relevant": is_relevant,
                "is_substantive": is_substantive,
                "quality_issues": quality_issues,
                "reasoning": reasoning,
                "threshold": self.threshold
            }
            
            if relevance_score >= self.threshold and is_relevant and is_substantive:
                return QualityGateResult.PASS, metadata
            elif relevance_score >= 0.4:
                return QualityGateResult.WARNING, metadata
            else:
                return QualityGateResult.FAIL, metadata
                
        except Exception as e:
            logger.error(f"Error in semantic relevance validation: {e}")
            return QualityGateResult.WARNING, {"error": str(e)}

class ContentCompletenessGate(QualityGate):
    """Validates that task output is complete and not a placeholder"""
    
    def __init__(self):
        super().__init__("content_completeness", threshold=0.7)
    
    async def validate(self, task_data: Dict[str, Any], output: str) -> Tuple[QualityGateResult, Dict[str, Any]]:
        try:
            # Basic heuristic checks
            output_length = len(output.strip())
            word_count = len(output.split())
            
            # Check for placeholder patterns
            placeholder_patterns = [
                "todo", "tbd", "coming soon", "placeholder", "lorem ipsum",
                "sample text", "example", "template", "insert here",
                "add content", "fill in", "to be completed"
            ]
            
            placeholder_count = sum(1 for pattern in placeholder_patterns 
                                  if pattern.lower() in output.lower())
            
            # Quality scoring
            length_score = min(output_length / 500, 1.0)  # Expect at least 500 chars
            word_score = min(word_count / 50, 1.0)        # Expect at least 50 words
            placeholder_penalty = placeholder_count * 0.3  # Penalty for placeholders
            
            completeness_score = max(0.0, (length_score + word_score) / 2 - placeholder_penalty)
            
            metadata = {
                "completeness_score": completeness_score,
                "output_length": output_length,
                "word_count": word_count,
                "placeholder_count": placeholder_count,
                "threshold": self.threshold
            }
            
            if completeness_score >= self.threshold:
                return QualityGateResult.PASS, metadata
            elif completeness_score >= 0.4:
                return QualityGateResult.WARNING, metadata
            else:
                return QualityGateResult.FAIL, metadata
                
        except Exception as e:
            logger.error(f"Error in content completeness validation: {e}")
            return QualityGateResult.WARNING, {"error": str(e)}

class BusinessValueGate(QualityGate):
    """Validates that task output provides actual business value"""
    
    def __init__(self):
        super().__init__("business_value", threshold=0.6)
    
    async def validate(self, task_data: Dict[str, Any], output: str) -> Tuple[QualityGateResult, Dict[str, Any]]:
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return QualityGateResult.WARNING, {"error": "No OpenAI API key available"}
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            
            task_name = task_data.get("name", "")
            workspace_id = task_data.get("workspace_id", "")
            
            # Get workspace context for business relevance
            from database import get_workspace
            workspace = await get_workspace(workspace_id)
            workspace_context = workspace.get("description", "") if workspace else ""
            
            prompt = f"""Evaluate the business value and practical utility of this task output.

BUSINESS CONTEXT:
- Workspace: {workspace_context}
- Task: {task_name}

TASK OUTPUT:
{output[:2000]}

BUSINESS VALUE CRITERIA:
1. Does this output solve a real business problem?
2. Can this be used immediately for business purposes?
3. Does it provide actionable insights or deliverables?
4. Is it professionally formatted and presentation-ready?

Provide a JSON response:
{{
    "business_value_score": 0.0-1.0,
    "is_actionable": true/false,
    "is_professional": true/false,
    "practical_utility": "high/medium/low",
    "business_impact": "Brief description of business impact",
    "recommendations": ["list", "of", "improvements"]
}}"""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business consultant who evaluates deliverables for practical business value."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            business_value_score = result.get("business_value_score", 0.0)
            is_actionable = result.get("is_actionable", False)
            is_professional = result.get("is_professional", False)
            
            metadata = {
                "business_value_score": business_value_score,
                "is_actionable": is_actionable,
                "is_professional": is_professional,
                "practical_utility": result.get("practical_utility", "low"),
                "business_impact": result.get("business_impact", ""),
                "recommendations": result.get("recommendations", []),
                "threshold": self.threshold
            }
            
            if business_value_score >= self.threshold and is_actionable:
                return QualityGateResult.PASS, metadata
            elif business_value_score >= 0.4:
                return QualityGateResult.WARNING, metadata
            else:
                return QualityGateResult.FAIL, metadata
                
        except Exception as e:
            logger.error(f"Error in business value validation: {e}")
            return QualityGateResult.WARNING, {"error": str(e)}

class AIQualityGateEngine:
    """
    🎯 PRIORITY 3: AI Quality Gate Engine
    
    Orchestrates multiple quality gates to ensure task outputs meet standards
    before allowing goal progress updates.
    """
    
    def __init__(self):
        self.gates = [
            SemanticRelevanceGate(),
            ContentCompletenessGate(),
            BusinessValueGate()
        ]
        self.validation_history = {}
        
    async def validate_task_output(
        self, 
        task_data: Dict[str, Any], 
        output: str,
        strict_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Run all quality gates on task output
        
        Args:
            task_data: Task information
            output: Task output to validate
            strict_mode: If True, all gates must pass. If False, majority must pass.
        
        Returns:
            Validation result with gate results and overall decision
        """
        validation_start = datetime.now()
        task_id = task_data.get("id", "unknown")
        
        validation_result = {
            "task_id": task_id,
            "timestamp": validation_start.isoformat(),
            "strict_mode": strict_mode,
            "gate_results": {},
            "overall_result": QualityGateResult.PENDING.value,
            "passed_gates": 0,
            "total_gates": len(self.gates),
            "recommendations": [],
            "allow_progress_update": False
        }
        
        try:
            # Run all quality gates
            for gate in self.gates:
                gate_result, metadata = await gate.validate(task_data, output)
                
                validation_result["gate_results"][gate.name] = {
                    "result": gate_result.value,
                    "metadata": metadata
                }
                
                if gate_result == QualityGateResult.PASS:
                    validation_result["passed_gates"] += 1
                elif gate_result == QualityGateResult.WARNING:
                    validation_result["passed_gates"] += 0.5  # Partial credit
                
                # Collect recommendations
                if "recommendations" in metadata:
                    validation_result["recommendations"].extend(metadata["recommendations"])
            
            # Determine overall result
            pass_rate = validation_result["passed_gates"] / validation_result["total_gates"]
            
            if strict_mode:
                # All gates must pass in strict mode
                if validation_result["passed_gates"] == validation_result["total_gates"]:
                    validation_result["overall_result"] = QualityGateResult.PASS.value
                    validation_result["allow_progress_update"] = True
                else:
                    validation_result["overall_result"] = QualityGateResult.FAIL.value
            else:
                # Majority must pass in non-strict mode
                if pass_rate >= 0.7:
                    validation_result["overall_result"] = QualityGateResult.PASS.value
                    validation_result["allow_progress_update"] = True
                elif pass_rate >= 0.5:
                    validation_result["overall_result"] = QualityGateResult.WARNING.value
                    validation_result["allow_progress_update"] = True  # Allow with warning
                else:
                    validation_result["overall_result"] = QualityGateResult.FAIL.value
            
            # Store validation history
            self.validation_history[task_id] = validation_result
            
            # Log results
            if validation_result["allow_progress_update"]:
                logger.info(f"✅ Quality gates PASSED for task {task_id}: {validation_result['passed_gates']}/{validation_result['total_gates']} gates")
            else:
                logger.warning(f"❌ Quality gates FAILED for task {task_id}: {validation_result['passed_gates']}/{validation_result['total_gates']} gates")
                logger.debug(f"Failed gates: {[name for name, result in validation_result['gate_results'].items() if result['result'] == 'fail']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in quality gate validation for task {task_id}: {e}")
            validation_result["overall_result"] = QualityGateResult.WARNING.value
            validation_result["allow_progress_update"] = True  # Allow on error to prevent blocking
            validation_result["error"] = str(e)
            return validation_result
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of quality gate performance"""
        if not self.validation_history:
            return {"total_validations": 0, "pass_rate": 0.0}
        
        total = len(self.validation_history)
        passed = sum(1 for result in self.validation_history.values() 
                    if result["allow_progress_update"])
        
        return {
            "total_validations": total,
            "passed_validations": passed,
            "pass_rate": (passed / total) * 100,
            "recent_validations": list(self.validation_history.values())[-10:]
        }

# Singleton instance
ai_quality_gate_engine = AIQualityGateEngine()