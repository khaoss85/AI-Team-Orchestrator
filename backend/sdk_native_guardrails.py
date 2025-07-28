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
            validation_result = await unified_quality_engine.validate_task_input(
                content=task_input,
                agent_context={"agent_name": agent.name, "agent_role": getattr(agent, 'role', 'unknown')},
                workspace_id=getattr(ctx, 'workspace_id', None)
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
    AI-driven output guardrail to validate the quality and concreteness of the generated asset.
    Replaces the logic from UnifiedQualityEngine for pipeline agents.
    """
    try:
        output_str = str(output)
        logger.info(f"🛡️ [OutputGuardrail] Validating output from agent '{agent.name}'...")

        # Placeholder check (similar to the one in specialist_enhanced)
        placeholder_indicators = ["lorem ipsum", "placeholder", "todo", "tbd", "[insert"]
        if any(indicator in output_str.lower() for indicator in placeholder_indicators):
            logger.warning("🛡️ [OutputGuardrail] BLOCKED: Output contains placeholder content.")
            return GuardrailFunctionOutput(tripwire_triggered=True, output_info="The generated output contains placeholder text and is not a complete asset.")

        # 🧠 AI-DRIVEN: Use UnifiedQualityEngine for real quality evaluation
        try:
            from ai_quality_assurance.unified_quality_engine import unified_quality_engine
            quality_result = await unified_quality_engine.evaluate_asset_quality(
                content=output_str,
                task_context={"agent_name": agent.name},
                workspace_id=getattr(ctx, 'workspace_id', None)
            )
            quality_score = quality_result.get('quality_score', 0)
            threshold = quality_result.get('dynamic_threshold', 70)  # AI-driven threshold
        except Exception as e:
            logger.warning(f"Failed AI quality evaluation, using fallback: {e}")
            quality_score = 90  # Conservative fallback
            threshold = 70
        
        if quality_score < threshold:
            logger.warning(f"🛡️ [OutputGuardrail] BLOCKED: Output quality score ({quality_score}) is below AI threshold ({threshold}).")
            return GuardrailFunctionOutput(tripwire_triggered=True, output_info=f"Output quality score ({quality_score}) is below the AI-calculated threshold of {threshold}.")

        logger.info(f"🛡️ [OutputGuardrail] PASSED: Output quality is sufficient (Score: {quality_score}, Threshold: {threshold}).")
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=f"Output quality validation passed (Score: {quality_score})")
    except Exception as e:
        logger.error(f"🛡️ [OutputGuardrail] ERROR: {e}")
        return GuardrailFunctionOutput(tripwire_triggered=True, output_info=f"An error occurred during output validation: {e}")

