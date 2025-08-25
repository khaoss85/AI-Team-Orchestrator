"""
🛡️ SDK Native Guardrails - Phase 3.2 Implementation
Aligns the quality assurance system with OpenAI Agents SDK native primitives.

This module defines reusable, AI-driven guardrail functions that can be attached
directly to agents within the SDK Pipeline, replacing the custom QualityGateStage.
"""
import logging
from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput, RunContextWrapper
from typing import Any, Dict

logger = logging.getLogger(__name__)

# --- NATIVE SDK GUARDRAILS ---

@input_guardrail
async def validate_task_input_ai(ctx: RunContextWrapper, agent: Any, input_content: Any) -> GuardrailFunctionOutput:
    """
    AI-driven input guardrail to validate task completeness and clarity.
    """
    try:
        task_input = str(input_content)
        logger.info(f"🛡️ [InputGuardrail] Validating input for agent '{agent.name}'...")

        # 🧠 AI-DRIVEN: Use AI to validate task input quality and clarity
        try:
            from ai_quality_assurance.unified_quality_engine import unified_quality_engine
            # 🔧 Get workspace_id from context using the same access pattern
            workspace_id = getattr(ctx, 'workspace_id', None)
            if not workspace_id and hasattr(ctx, '__dict__'):
                workspace_id = ctx.__dict__.get('workspace_id', None)
            
            validation_result = await unified_quality_engine.validate_task_input(
                content=task_input,
                agent_context={"agent_name": agent.name, "agent_role": getattr(agent, 'role', 'unknown')},
                workspace_id=workspace_id
            )
            
            if not validation_result.get('is_valid', True):
                reason = validation_result.get('validation_reason', 'Input validation failed')
                logger.warning(f"🛡️ [InputGuardrail] BLOCKED: {reason}")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info=reason)
                
        except Exception as e:
            logger.warning(f"Failed AI input validation, using fallback rules: {e}")
            # Fallback to simple rules
            if len(task_input) < 20:
                logger.warning("🛡️ [InputGuardrail] BLOCKED: Input is too short.")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info="Task input is too short. Please provide more details.")
            
            if "unclear" in task_input.lower() or "figure out" in task_input.lower():
                logger.warning("🛡️ [InputGuardrail] BLOCKED: Input appears to be ambiguous.")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info="Task input is ambiguous. Please clarify the requirements.")

        logger.info("🛡️ [InputGuardrail] PASSED: Input validated successfully.")
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info="Input validation passed")
    except Exception as e:
        logger.error(f"🛡️ [InputGuardrail] ERROR: {e}")
        return GuardrailFunctionOutput(tripwire_triggered=True, output_info=f"An error occurred during input validation: {e}")


@output_guardrail
async def validate_asset_output_ai(ctx: RunContextWrapper, agent: Any, output: Any) -> GuardrailFunctionOutput:
    """
    🧠 AI-driven output guardrail with TASK CLASSIFICATION CONTEXT awareness.
    Adapts validation based on whether task was classified as DATA_COLLECTION vs CONTENT_GENERATION.
    """
    try:
        output_str = str(output)
        logger.info(f"🛡️ [OutputGuardrail] Validating output from agent '{agent.name}'...")

        # 🔧 HOLISTIC: Get task classification context from SDK RunContextWrapper
        # The SDK may wrap our context data, so we try multiple access patterns
        task_classification = None
        execution_type = 'unknown'
        available_tools = []
        
        # Try direct attribute access first
        task_classification = getattr(ctx, 'task_classification', None)
        if task_classification:
            execution_type = task_classification.execution_type.value if hasattr(task_classification, 'execution_type') else 'unknown'
            available_tools = getattr(ctx, 'available_tools', [])
        else:
            # Try accessing from wrapped context data
            execution_type = getattr(ctx, 'execution_type', 'unknown')
            available_tools = getattr(ctx, 'available_tools', [])
            
            # If still no data, try accessing from nested context
            if hasattr(ctx, '__dict__'):
                ctx_dict = ctx.__dict__
                execution_type = ctx_dict.get('execution_type', execution_type)
                available_tools = ctx_dict.get('available_tools', available_tools)
                task_classification = ctx_dict.get('task_classification', task_classification)
        
        logger.info(f"🔧 [OutputGuardrail] Task classification context: {execution_type}, tools: {available_tools}")
        logger.debug(f"🔍 [OutputGuardrail] Context debug - task_classification object: {task_classification is not None}, ctx type: {type(ctx)}")

        # 🧠 CONTEXT-AWARE VALIDATION: Different rules for different task types
        if execution_type == 'data_collection':
            # Strict validation for data collection tasks
            placeholder_indicators = ["lorem ipsum", "placeholder", "todo", "tbd", "[insert", "example.com", "sample@"]
            if any(indicator in output_str.lower() for indicator in placeholder_indicators):
                logger.warning("🛡️ [OutputGuardrail] BLOCKED: DATA_COLLECTION task contains placeholder content.")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info="Data collection tasks must provide real data, not placeholders.")
        
        elif execution_type == 'content_generation':
            # More lenient validation for content generation tasks
            placeholder_indicators = ["lorem ipsum", "todo", "tbd", "[insert"]  # Allow examples and templates
            if any(indicator in output_str.lower() for indicator in placeholder_indicators):
                logger.warning("🛡️ [OutputGuardrail] BLOCKED: CONTENT_GENERATION contains incomplete placeholder content.")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info="Content generation should be complete, not contain TODO placeholders.")
        
        else:
            # Default validation for unknown task types
            placeholder_indicators = ["lorem ipsum", "placeholder", "todo", "tbd", "[insert"]
            if any(indicator in output_str.lower() for indicator in placeholder_indicators):
                logger.warning("🛡️ [OutputGuardrail] BLOCKED: Output contains placeholder content.")
                return GuardrailFunctionOutput(tripwire_triggered=True, output_info="The generated output contains placeholder text and is not a complete asset.")

        # 🧠 AI-DRIVEN: Use UnifiedQualityEngine with TASK CLASSIFICATION CONTEXT
        try:
            from ai_quality_assurance.unified_quality_engine import unified_quality_engine
            
            # 🔧 Enhanced context for AI quality evaluation
            enhanced_task_context = {
                "agent_name": agent.name,
                "execution_type": execution_type,
                "available_tools": available_tools,
                "content_length": len(output_str)
            }
            
            # 🔧 Get workspace_id using the same access pattern
            workspace_id = getattr(ctx, 'workspace_id', None)
            if not workspace_id and hasattr(ctx, '__dict__'):
                workspace_id = ctx.__dict__.get('workspace_id', None)
            
            quality_result = await unified_quality_engine.evaluate_asset_quality(
                content=output_str,
                task_context=enhanced_task_context,
                workspace_id=workspace_id
            )
            quality_score = quality_result.get('quality_score', 0)
            
            # 🎯 CONTEXT-AWARE THRESHOLDS: Different thresholds based on task type
            if execution_type == 'data_collection':
                base_threshold = quality_result.get('dynamic_threshold', 80)  # Higher threshold for data
            elif execution_type == 'content_generation':
                base_threshold = quality_result.get('dynamic_threshold', 60)  # Lower threshold for creative content
            else:
                base_threshold = quality_result.get('dynamic_threshold', 70)  # Default threshold
                
        except Exception as e:
            logger.warning(f"Failed AI quality evaluation, using context-aware fallback: {e}")
            # Context-aware fallback thresholds
            if execution_type == 'content_generation':
                quality_score = 75  # More lenient for content generation
                base_threshold = 60
            else:
                quality_score = 90  # Conservative for other types
                base_threshold = 70
        
        # Final threshold decision
        threshold = base_threshold
        
        if quality_score < threshold:
            logger.warning(f"🛡️ [OutputGuardrail] BLOCKED: Output quality score ({quality_score}) is below context-aware threshold ({threshold}) for {execution_type}.")
            return GuardrailFunctionOutput(tripwire_triggered=True, output_info=f"Output quality score ({quality_score}) is below the context-aware threshold of {threshold} for {execution_type} tasks.")

        logger.info(f"🛡️ [OutputGuardrail] PASSED: Output quality is sufficient (Score: {quality_score}, Threshold: {threshold}, Type: {execution_type}).")
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=f"Output quality validation passed (Score: {quality_score}, Type: {execution_type})")
    except Exception as e:
        logger.error(f"🛡️ [OutputGuardrail] ERROR: {e}")
        return GuardrailFunctionOutput(tripwire_triggered=True, output_info=f"An error occurred during output validation: {e}")

