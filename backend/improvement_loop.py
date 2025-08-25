import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from human_feedback_manager import human_feedback_manager, FeedbackRequestType
from database import (
    get_task,
    list_tasks,
    update_task_status,
    create_task,
    update_task_fields
)
from models import TaskStatus

try:
    from ai_quality_assurance.ai_adaptive_quality_engine import ai_adaptive_quality_engine
    HAS_AI_QA = True
except ImportError:
    HAS_AI_QA = False
    ai_adaptive_quality_engine = None

logger = logging.getLogger(__name__)

# 🤖 AI-First Configuration
AI_FIRST_MODE = os.getenv("AI_FIRST_IMPROVEMENT_LOOP", "true").lower() == "true"
AUTONOMOUS_QA_ENABLED = os.getenv("AUTONOMOUS_QA_ENABLED", "true").lower() == "true"
HUMAN_OVERRIDE_THRESHOLD = float(os.getenv("HUMAN_OVERRIDE_THRESHOLD", "0.3"))  # Only critical failures
DEFAULT_FEEDBACK_TIMEOUT = 60 * 60 * 2  # Reduced from 24h to 2h


async def checkpoint_output(task_id: str, output: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """🤖 AI-First output checkpoint with autonomous quality evaluation"""
    
    if not AI_FIRST_MODE:
        # Legacy mode - use human feedback
        return await _legacy_checkpoint_output(task_id, output, timeout)
    
    try:
        task = await get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for checkpoint")
            return False

        logger.info(f"🤖 Starting AI-First checkpoint for task: {task['name']}")
        
        # 🧠 AI-driven quality evaluation
        if HAS_AI_QA and AUTONOMOUS_QA_ENABLED:
            content = str(output.get("result", output))
            context = {
                "domain": task.get("domain", "business"),
                "content_type": "task_output",
                "complexity": task.get("complexity", "medium"),
                "user_expectations": "professional",
                "task_name": task["name"],
                "task_description": task.get("description", "")
            }
            
            quality_result = await ai_adaptive_quality_engine.evaluate_content_quality(content, context)
            
            overall_score = quality_result.get("overall_score", 0.0)
            decision = quality_result.get("autonomous_decision", {})
            decision_status = decision.get("status", "unknown")
            
            logger.info(f"🧠 AI quality evaluation: Score {overall_score:.2f}, Decision: {decision_status}")
            
            # AI-driven decision logic
            if decision_status in ["approved", "approved_with_notes"]:
                logger.info(f"✅ AI-approved task output (score: {overall_score:.2f})")
                return True
                
            elif decision_status in ["auto_enhance", "auto_enhance_required"]:
                logger.info(f"🔧 AI triggering autonomous enhancement (score: {overall_score:.2f})")
                
                # Create enhancement task automatically
                enhancement_suggestions = decision.get("improvements", [])
                await _create_autonomous_enhancement_task(
                    task_id, task["workspace_id"], enhancement_suggestions
                )
                
                # Mark original task as needing enhancement
                await update_task_status(task_id, TaskStatus.STALE.value)
                return False
                
            elif overall_score < HUMAN_OVERRIDE_THRESHOLD:
                # Only involve humans for critical failures
                logger.warning(f"⚠️ Critical quality failure (score: {overall_score:.2f}) - requiring human override")
                return await _critical_human_override(task_id, output, quality_result)
                
            else:
                # Autonomous rejection with enhancement opportunities
                logger.info(f"🔄 AI autonomous rejection with enhancement (score: {overall_score:.2f})")
                enhancement_suggestions = decision.get("improvements", [])
                await _create_autonomous_enhancement_task(
                    task_id, task["workspace_id"], enhancement_suggestions
                )
                await update_task_status(task_id, TaskStatus.STALE.value)
                return False
        
        else:
            # Fallback: Basic autonomous evaluation without advanced AI
            logger.info("🔄 Using basic autonomous evaluation (AI QA not available)")
            return await _basic_autonomous_checkpoint(task_id, output)
            
    except Exception as e:
        logger.error(f"❌ AI-First checkpoint failed for task {task_id}: {e}")
        # Emergency fallback to basic approval
        return True


async def feedback_to_task(comments: str, workspace_id: str, original_task_id: str) -> Optional[Dict[str, Any]]:
    """Convert human feedback comments into a follow up task."""
    try:
        new_task = await create_task(
            workspace_id=workspace_id,
            name=f"Address feedback for {original_task_id}",
            description=comments,
            status=TaskStatus.PENDING.value,
            parent_task_id=original_task_id,
            creation_type="feedback",
        )
        return new_task
    except Exception as e:
        logger.error(f"Failed creating feedback task: {e}")
        return None


async def controlled_iteration(task_id: str, workspace_id: str, max_iterations: Optional[int]) -> bool:
    """Increment iteration count and check against max."""
    task = await get_task(task_id)
    if not task:
        return False
    iteration = task.get("iteration_count", 0) + 1
    await update_task_fields(task_id, {"iteration_count": iteration})
    if max_iterations is not None and iteration > max_iterations:
        await update_task_status(task_id, TaskStatus.FAILED.value, {"detail": "max_iterations_exceeded"})
        return False
    return True


async def refresh_dependencies(task_id: str) -> None:
    """Mark tasks depending on the given task as stale."""
    task = await get_task(task_id)
    if not task:
        return
    workspace_id = task["workspace_id"]
    tasks = await list_tasks(workspace_id)
    for t in tasks:
        # Cerca le dipendenze nella nuova tabella di giunzione
        deps_result = await supabase_service.table('task_dependencies').select('depends_on_task_id').eq('task_id', t['id']).execute()
        deps = [dep['depends_on_task_id'] for dep in deps_result.data] if deps_result.data else []
        if task_id in deps:
            try:
                await update_task_status(t["id"], TaskStatus.STALE.value)
            except Exception as e:
                logger.error(f"Failed refreshing dependency {t['id']}: {e}")


async def qa_gate(task_id: str, output: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """🤖 AI-First QA gate with autonomous quality validation"""
    
    if not AI_FIRST_MODE:
        # Legacy mode - use human QA approval
        return await _legacy_qa_gate(task_id, output, timeout)
    
    try:
        task = await get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for QA gate")
            return False

        logger.info(f"🛡️ Starting AI-First QA gate for task: {task['name']}")
        
        # 🧠 Enhanced AI quality evaluation for final QA
        if HAS_AI_QA and AUTONOMOUS_QA_ENABLED:
            content = str(output.get("result", output))
            context = {
                "domain": task.get("domain", "business"),
                "content_type": "final_deliverable",
                "complexity": task.get("complexity", "medium"),
                "user_expectations": "high",  # Higher expectations for QA gate
                "project_phase": "finalization",
                "task_name": task["name"],
                "task_description": task.get("description", "")
            }
            
            quality_result = await ai_adaptive_quality_engine.evaluate_content_quality(content, context)
            
            overall_score = quality_result.get("overall_score", 0.0)
            decision = quality_result.get("autonomous_decision", {})
            decision_status = decision.get("status", "unknown")
            
            logger.info(f"🛡️ AI QA evaluation: Score {overall_score:.2f}, Decision: {decision_status}")
            
            # AI-driven QA decision with stricter thresholds
            qa_approval_threshold = 0.80  # Higher threshold for QA gate
            qa_critical_threshold = 0.50   # Lower threshold before escalation
            
            if overall_score >= qa_approval_threshold and decision_status in ["approved", "approved_with_notes"]:
                logger.info(f"✅ AI QA gate PASSED (score: {overall_score:.2f})")
                return True
                
            elif overall_score >= qa_critical_threshold:
                # Moderate quality - autonomous enhancement opportunity
                logger.info(f"🔧 AI QA gate: Quality enhancement triggered (score: {overall_score:.2f})")
                
                # Create high-priority enhancement task
                enhancement_suggestions = decision.get("improvements", [])
                await _create_qa_enhancement_task(
                    task_id, task["workspace_id"], enhancement_suggestions, overall_score
                )
                
                # Mark for rework
                await update_task_status(task_id, TaskStatus.STALE.value)
                return False
                
            else:
                # Low quality - escalate to critical human review
                logger.warning(f"⚠️ AI QA gate: Critical quality failure (score: {overall_score:.2f}) - escalating")
                return await _critical_qa_escalation(task_id, output, quality_result)
        
        else:
            # Basic QA evaluation without advanced AI
            logger.info("🔄 Using basic QA evaluation (AI QA not available)")
            return await _basic_qa_gate(task_id, output)
            
    except Exception as e:
        logger.error(f"❌ AI-First QA gate failed for task {task_id}: {e}")
        # For QA gate failures, be conservative
        return False


async def close_loop(task_id: str) -> None:
    """Mark improvement loop closed for the given task."""
    try:
        await update_task_fields(task_id, {"iteration_count": 0})
    except Exception as e:
        logger.error(f"Failed closing improvement loop for {task_id}: {e}")


# 🤖 AI-First Supporting Functions

async def _create_autonomous_enhancement_task(
    original_task_id: str, 
    workspace_id: str, 
    enhancement_suggestions: List[str]
) -> Optional[Dict[str, Any]]:
    """Create autonomous enhancement task based on AI suggestions"""
    
    try:
        original_task = await get_task(original_task_id)
        if not original_task:
            return None
        
        # Format enhancement suggestions into actionable task description
        suggestions_text = "\\n".join([f"• {suggestion}" for suggestion in enhancement_suggestions])
        
        enhancement_description = f"""
🤖 AUTONOMOUS ENHANCEMENT TASK

Original Task: {original_task['name']}
Quality Assessment: Requires improvement to meet professional standards

AI-DRIVEN ENHANCEMENT SUGGESTIONS:
{suggestions_text}

ENHANCEMENT OBJECTIVES:
1. Address all identified improvement areas
2. Ensure content meets quality thresholds
3. Maintain business value and actionability
4. Prepare for autonomous re-evaluation

This is an AI-generated enhancement task. Focus on implementing the specific suggestions provided.
        """.strip()
        
        enhancement_task = await create_task(
            workspace_id=workspace_id,
            name=f"🔧 AI Enhancement: {original_task['name'][:50]}",
            description=enhancement_description,
            status=TaskStatus.PENDING.value,
            parent_task_id=original_task_id,
            creation_type="ai_autonomous_enhancement",
        )
        
        if enhancement_task:
            logger.info(f"✅ Created autonomous enhancement task: {enhancement_task['id']}")
        
        return enhancement_task
        
    except Exception as e:
        logger.error(f"Failed creating autonomous enhancement task: {e}")
        return None


async def _critical_human_override(
    task_id: str, 
    output: Dict[str, Any], 
    quality_result: Dict[str, Any]
) -> bool:
    """Handle critical quality failures requiring human intervention"""
    
    try:
        task = await get_task(task_id)
        if not task:
            return False
        
        workspace_id = task["workspace_id"]
        overall_score = quality_result.get("overall_score", 0.0)
        decision = quality_result.get("autonomous_decision", {})
        
        result: Dict[str, Any] = {"approved": False, "comments": ""}
        event = asyncio.Event()

        async def _on_response(_, response: Dict[str, Any]):
            result.update({
                "approved": response.get("approved", False),
                "comments": response.get("comments", "")
            })
            event.set()

        # Critical failure - immediate human attention needed
        await human_feedback_manager.request_feedback(
            workspace_id=workspace_id,
            request_type=FeedbackRequestType.QUALITY_GATE_FAILURE,
            title=f"🚨 CRITICAL: Quality failure for {task['name']}",
            description=f"""
CRITICAL QUALITY FAILURE - HUMAN OVERRIDE REQUIRED

AI Quality Score: {overall_score:.2f} (Below critical threshold: {HUMAN_OVERRIDE_THRESHOLD})
AI Decision: {decision.get('status', 'unknown')}
AI Rationale: {decision.get('rationale', 'Critical quality issues detected')}

ENHANCEMENT SUGGESTIONS:
{chr(10).join(f"• {suggestion}" for suggestion in decision.get('improvements', []))}

This task output has been flagged as critically deficient by the AI quality system. 
Please review and decide on appropriate action.
            """.strip(),
            proposed_actions=[
                {"label": "approve_override", "value": "approve", "description": "Override AI and approve"},
                {"label": "reject_enhance", "value": "reject", "description": "Reject and enhance"},
                {"label": "escalate", "value": "escalate", "description": "Escalate to senior review"}
            ],
            context={
                "task_id": task_id, 
                "output": output,
                "quality_score": overall_score,
                "ai_decision": decision
            },
            response_callback=_on_response,
            timeout_hours=4  # Shorter timeout for critical issues
        )

        try:
            await asyncio.wait_for(event.wait(), timeout=60 * 60 * 4)  # 4 hours max
        except asyncio.TimeoutError:
            logger.error(f"CRITICAL: Human override request timed out for task {task_id}")
            # For critical failures, default to rejection
            await update_task_status(task_id, TaskStatus.FAILED.value)
            return False

        if result["approved"]:
            logger.warning(f"⚠️ Human override approved critical quality failure for task {task_id}")
            return True
        else:
            # Create enhancement task with human feedback
            await feedback_to_task(result["comments"], workspace_id, task_id)
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
            
    except Exception as e:
        logger.error(f"Critical human override failed for task {task_id}: {e}")
        return False


async def _basic_autonomous_checkpoint(task_id: str, output: Dict[str, Any]) -> bool:
    """Basic autonomous checkpoint without advanced AI quality assessment"""
    
    try:
        content = str(output.get("result", output))
        content_length = len(content)
        
        # Basic quality heuristics
        if content_length < 50:
            logger.warning(f"🔄 Basic checkpoint: Content too short ({content_length} chars)")
            # Create basic enhancement task
            await _create_basic_enhancement_task(task_id, "Content is too short and lacks sufficient detail")
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
            
        # Check for obvious placeholder content
        placeholder_indicators = ["lorem ipsum", "todo", "tbd", "[insert", "placeholder", "xxx"]
        has_placeholders = any(indicator in content.lower() for indicator in placeholder_indicators)
        
        if has_placeholders:
            logger.warning(f"🔄 Basic checkpoint: Placeholder content detected")
            await _create_basic_enhancement_task(task_id, "Content contains placeholder text that needs to be replaced with real information")
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
        
        # Basic approval for content that passes simple checks
        logger.info(f"✅ Basic autonomous approval (length: {content_length} chars, no obvious issues)")
        return True
        
    except Exception as e:
        logger.error(f"Basic autonomous checkpoint failed: {e}")
        return True  # Default to approval on errors


async def _create_basic_enhancement_task(task_id: str, issue_description: str) -> Optional[Dict[str, Any]]:
    """Create basic enhancement task without advanced AI analysis"""
    
    try:
        task = await get_task(task_id)
        if not task:
            return None
        
        enhancement_description = f"""
🔧 BASIC ENHANCEMENT TASK

Original Task: {task['name']}
Issue Identified: {issue_description}

ENHANCEMENT REQUIREMENTS:
• Address the specific issue identified above
• Ensure content is complete and professional
• Remove any placeholder or template content
• Provide specific, actionable information
• Review for clarity and business value

This enhancement task was created automatically based on quality checks.
        """.strip()
        
        enhancement_task = await create_task(
            workspace_id=task["workspace_id"],
            name=f"🔧 Basic Enhancement: {task['name'][:50]}",
            description=enhancement_description,
            status=TaskStatus.PENDING.value,
            parent_task_id=task_id,
            creation_type="basic_enhancement",
        )
        
        return enhancement_task
        
    except Exception as e:
        logger.error(f"Failed creating basic enhancement task: {e}")
        return None


async def _legacy_checkpoint_output(task_id: str, output: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """Legacy human feedback checkpoint (preserved for compatibility)"""
    
    task = await get_task(task_id)
    if not task:
        return False

    workspace_id = task["workspace_id"]
    result: Dict[str, Any] = {"approved": True, "comments": ""}
    event = asyncio.Event()

    async def _on_response(_, response: Dict[str, Any]):
        result.update({
            "approved": response.get("approved", True),
            "comments": response.get("comments", "")
        })
        event.set()

    await human_feedback_manager.request_feedback(
        workspace_id=workspace_id,
        request_type=FeedbackRequestType.TASK_APPROVAL,
        title=f"Review output for task {task['name']}",
        description="Please review the generated output and provide comments.",
        proposed_actions=[{"label": "approve", "value": "approve"}, {"label": "changes", "value": "changes"}],
        context={"task_id": task_id, "output": output},
        response_callback=_on_response
    )

    try:
        await asyncio.wait_for(event.wait(), timeout or DEFAULT_FEEDBACK_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(f"Legacy feedback request for task {task_id} timed out after {timeout or DEFAULT_FEEDBACK_TIMEOUT}s")
        await update_task_status(task_id, TaskStatus.TIMED_OUT.value)
        return False

    if not result["approved"]:
        await feedback_to_task(result["comments"], workspace_id, task_id)
        await update_task_status(task_id, TaskStatus.STALE.value)
        return False
    return True


async def _create_qa_enhancement_task(
    task_id: str, 
    workspace_id: str, 
    enhancement_suggestions: List[str], 
    quality_score: float
) -> Optional[Dict[str, Any]]:
    """Create QA-level enhancement task with high priority"""
    
    try:
        task = await get_task(task_id)
        if not task:
            return None
        
        suggestions_text = "\\n".join([f"• {suggestion}" for suggestion in enhancement_suggestions])
        
        qa_enhancement_description = f"""
🛡️ QA GATE ENHANCEMENT TASK - HIGH PRIORITY

Original Task: {task['name']}
QA Quality Score: {quality_score:.2f}/1.0
Status: FAILED QA Gate - Requires enhancement to meet final quality standards

AI-DRIVEN QA ENHANCEMENT REQUIREMENTS:
{suggestions_text}

QA GATE OBJECTIVES:
1. Address ALL quality issues identified by AI evaluation
2. Meet final deliverable standards (target score: 0.80+)
3. Ensure professional-grade output quality
4. Pass autonomous QA re-evaluation
5. Prepare for final approval and delivery

⚠️ HIGH PRIORITY: This task failed the QA gate and requires immediate attention.
Focus on implementing each enhancement suggestion precisely.
        """.strip()
        
        enhancement_task = await create_task(
            workspace_id=workspace_id,
            name=f"🛡️ QA Enhancement: {task['name'][:40]}",
            description=qa_enhancement_description,
            status=TaskStatus.PENDING.value,
            parent_task_id=task_id,
            creation_type="qa_gate_enhancement",
        )
        
        if enhancement_task:
            logger.info(f"✅ Created QA enhancement task: {enhancement_task['id']}")
        
        return enhancement_task
        
    except Exception as e:
        logger.error(f"Failed creating QA enhancement task: {e}")
        return None


async def _critical_qa_escalation(
    task_id: str, 
    output: Dict[str, Any], 
    quality_result: Dict[str, Any]
) -> bool:
    """Critical QA escalation for severely deficient deliverables"""
    
    try:
        task = await get_task(task_id)
        if not task:
            return False
        
        workspace_id = task["workspace_id"]
        overall_score = quality_result.get("overall_score", 0.0)
        decision = quality_result.get("autonomous_decision", {})
        
        result: Dict[str, Any] = {"approved": False, "comments": ""}
        event = asyncio.Event()

        async def _on_response(_, response: Dict[str, Any]):
            result.update({
                "approved": response.get("approved", False),
                "comments": response.get("comments", "")
            })
            event.set()

        # Critical QA failure - immediate escalation
        await human_feedback_manager.request_feedback(
            workspace_id=workspace_id,
            request_type=FeedbackRequestType.QUALITY_GATE_CHECKPOINT,
            title=f"🚨 CRITICAL QA FAILURE: {task['name']}",
            description=f"""
CRITICAL QA GATE FAILURE - IMMEDIATE ESCALATION REQUIRED

Task: {task['name']}
AI Quality Score: {overall_score:.2f} (Critical threshold: 0.50)
AI QA Decision: {decision.get('status', 'severe_quality_failure')}
AI Assessment: {decision.get('rationale', 'Severe quality deficiencies detected')}

CRITICAL ISSUES IDENTIFIED:
{chr(10).join(f"• {suggestion}" for suggestion in decision.get('improvements', []))}

This deliverable has FAILED the AI QA gate due to critical quality issues.
The AI system has determined this output is not suitable for delivery.

REQUIRED ACTIONS:
1. Review the AI assessment and quality score
2. Evaluate if the deliverable can be enhanced or needs complete rework  
3. Consider reassigning to a more experienced team member
4. Decide on project timeline impact and stakeholder communication

This requires immediate senior attention due to the severity of quality issues.
            """.strip(),
            proposed_actions=[
                {"label": "major_rework", "value": "rework", "description": "Require major rework"},
                {"label": "reassign_expert", "value": "reassign", "description": "Reassign to expert team member"},
                {"label": "escalate_senior", "value": "escalate", "description": "Escalate to senior management"},
                {"label": "override_critical", "value": "override", "description": "Override (requires justification)"}
            ],
            context={
                "task_id": task_id, 
                "output": output,
                "quality_score": overall_score,
                "ai_decision": decision,
                "escalation_level": "critical_qa_failure"
            },
            response_callback=_on_response,
            timeout_hours=2  # Very short timeout for critical issues
        )

        try:
            await asyncio.wait_for(event.wait(), timeout=60 * 60 * 2)  # 2 hours max
        except asyncio.TimeoutError:
            logger.error(f"🚨 CRITICAL: QA escalation timed out for task {task_id}")
            # For critical QA failures, mark as failed
            await update_task_status(task_id, TaskStatus.FAILED.value)
            return False

        action = result.get("action", "rework")
        
        if action == "override":
            logger.warning(f"⚠️ CRITICAL QA OVERRIDE approved for task {task_id}")
            return True
        elif action in ["rework", "reassign"]:
            # Create critical enhancement task with human feedback
            await feedback_to_task(result["comments"], workspace_id, task_id)
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
        else:  # escalate
            # Mark for senior escalation
            await update_task_status(task_id, TaskStatus.FAILED.value)
            return False
            
    except Exception as e:
        logger.error(f"Critical QA escalation failed for task {task_id}: {e}")
        return False


async def _basic_qa_gate(task_id: str, output: Dict[str, Any]) -> bool:
    """Basic QA gate without advanced AI assessment"""
    
    try:
        content = str(output.get("result", output))
        content_length = len(content)
        
        # Stricter basic QA checks
        if content_length < 100:
            logger.warning(f"🛡️ Basic QA: Content too short for final deliverable ({content_length} chars)")
            await _create_basic_qa_enhancement_task(task_id, "Final deliverable is too short and lacks sufficient detail for professional delivery")
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
            
        # Check for placeholder content (stricter for QA)
        placeholder_indicators = [
            "lorem ipsum", "todo", "tbd", "[insert", "placeholder", "xxx",
            "example.com", "sample@", "your-company", "company-name"
        ]
        has_placeholders = any(indicator in content.lower() for indicator in placeholder_indicators)
        
        if has_placeholders:
            logger.warning(f"🛡️ Basic QA: Placeholder content detected in final deliverable")
            await _create_basic_qa_enhancement_task(task_id, "Final deliverable contains placeholder content unsuitable for professional delivery")
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
        
        # Check for basic professional standards
        has_structure = bool(content.count("\\n") > 3 or content.count(".") > 5)
        if not has_structure:
            logger.warning(f"🛡️ Basic QA: Lacks professional structure")
            await _create_basic_qa_enhancement_task(task_id, "Final deliverable lacks professional structure and formatting")
            await update_task_status(task_id, TaskStatus.STALE.value)
            return False
        
        # Basic QA approval
        logger.info(f"✅ Basic QA gate PASSED (length: {content_length} chars, structure: good)")
        return True
        
    except Exception as e:
        logger.error(f"Basic QA gate failed: {e}")
        return False  # Conservative approach for QA failures


async def _create_basic_qa_enhancement_task(task_id: str, issue_description: str) -> Optional[Dict[str, Any]]:
    """Create basic QA enhancement task"""
    
    try:
        task = await get_task(task_id)
        if not task:
            return None
        
        qa_enhancement_description = f"""
🛡️ BASIC QA ENHANCEMENT TASK - HIGH PRIORITY

Original Task: {task['name']}
QA Gate Status: FAILED - Professional standards not met
Issue Identified: {issue_description}

BASIC QA REQUIREMENTS FOR FINAL DELIVERABLE:
• Address the specific QA issue identified above
• Ensure content meets professional delivery standards
• Remove ALL placeholder, template, or example content
• Provide complete, specific, and actionable information
• Structure content professionally with clear sections
• Review for grammar, clarity, and business appropriateness
• Ensure deliverable is ready for client/stakeholder review

⚠️ HIGH PRIORITY: This task failed the QA gate and must meet professional standards.
        """.strip()
        
        enhancement_task = await create_task(
            workspace_id=task["workspace_id"],
            name=f"🛡️ QA Fix: {task['name'][:45]}",
            description=qa_enhancement_description,
            status=TaskStatus.PENDING.value,
            parent_task_id=task_id,
            creation_type="qa_gate_basic_enhancement",
        )
        
        return enhancement_task
        
    except Exception as e:
        logger.error(f"Failed creating basic QA enhancement task: {e}")
        return None


async def _legacy_qa_gate(task_id: str, output: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """Legacy QA gate with human approval (preserved for compatibility)"""
    
    task = await get_task(task_id)
    if not task:
        return False
    workspace_id = task["workspace_id"]
    result: Dict[str, Any] = {"approved": True, "comments": ""}
    event = asyncio.Event()

    async def _on_response(_, response: Dict[str, Any]):
        result.update({
            "approved": response.get("approved", True),
            "comments": response.get("comments", "")
        })
        event.set()

    await human_feedback_manager.request_feedback(
        workspace_id=workspace_id,
        request_type=FeedbackRequestType.TASK_APPROVAL,
        title=f"QA approval for task {task['name']}",
        description="Approve final output or request changes.",
        proposed_actions=[{"label": "approve", "value": "approve"}, {"label": "changes", "value": "changes"}],
        context={"task_id": task_id, "output": output},
        response_callback=_on_response
    )

    try:
        await asyncio.wait_for(event.wait(), timeout or DEFAULT_FEEDBACK_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(f"Legacy QA gate for task {task_id} timed out after {timeout or DEFAULT_FEEDBACK_TIMEOUT}s")
        await update_task_status(task_id, TaskStatus.TIMED_OUT.value)
        return False

    if not result["approved"]:
        await feedback_to_task(result["comments"], workspace_id, task_id)
        await update_task_status(task_id, TaskStatus.STALE.value)
        return False
    return True
