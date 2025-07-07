"""
Quality Automation Engine - Pillar 8: Quality Gates 100% Automation
Automated quality validation triggers, course correction, and approval workflows.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime

from services.ai_quality_gate_engine import AIQualityGateEngine
from database_asset_extensions import asset_db_manager
from models import AssetArtifact

logger = logging.getLogger(__name__)

class QualityAutomationEngine:
    """
    100% Automated Quality Gates (Pillar 8 Enhancement)
    
    Provides:
    - Auto-trigger quality validation on artifact creation
    - Automated approval for high-quality content (>0.9)
    - Course correction triggers for low quality
    - Human review only for edge cases (0.7-0.8 range)
    """
    
    def __init__(self):
        self.quality_engine = AIQualityGateEngine()
        self.auto_approve_threshold = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.9"))
        self.auto_reject_threshold = float(os.getenv("AUTO_REJECT_THRESHOLD", "0.5"))
        self.human_review_min = float(os.getenv("HUMAN_REVIEW_MIN", "0.7"))
        self.human_review_max = float(os.getenv("HUMAN_REVIEW_MAX", "0.8"))
        
        logger.info("🤖 Quality Automation Engine initialized - Pillar 8: 100% Automation")
    
    async def auto_process_new_artifact(self, artifact: AssetArtifact) -> Dict[str, Any]:
        """
        Auto-process new artifact through complete quality pipeline
        Returns processing result with automated decision
        """
        try:
            logger.info(f"🔄 Auto-processing artifact: {artifact.artifact_name}")
            
            # Step 1: AI Quality Validation
            validation_result = await self.quality_engine.validate_artifact_quality(artifact)
            quality_score = validation_result.get("quality_score", 0.0)
            
            # Step 2: Automated Decision Making
            decision = await self._make_automated_decision(quality_score, validation_result)
            
            # Step 3: Execute Decision
            execution_result = await self._execute_quality_decision(artifact, decision, validation_result)
            
            # Step 4: Course Correction if needed
            if decision["action"] == "course_correction":
                correction_result = await self._trigger_course_correction(artifact, validation_result)
                execution_result["course_correction"] = correction_result
            
            logger.info(f"✅ Auto-processed {artifact.artifact_name}: {decision['action']}")
            
            return {
                "artifact_id": str(artifact.id),
                "quality_score": quality_score,
                "automated_decision": decision,
                "execution_result": execution_result,
                "processing_time": datetime.utcnow().isoformat(),
                "pillar_8_compliance": "100%_automated"
            }
            
        except Exception as e:
            logger.error(f"❌ Auto-processing failed for {artifact.artifact_name}: {e}")
            return {
                "artifact_id": str(artifact.id),
                "error": str(e),
                "fallback_action": "human_review_required"
            }
    
    async def _make_automated_decision(self, quality_score: float, validation_result: Dict) -> Dict[str, Any]:
        """AI-driven automated decision making for quality gates"""
        
        # Auto-approve high quality
        if quality_score >= self.auto_approve_threshold:
            return {
                "action": "auto_approve",
                "confidence": 0.95,
                "reason": f"High quality score ({quality_score:.2f}) exceeds auto-approve threshold",
                "requires_human": False
            }
        
        # Auto-reject very low quality
        elif quality_score <= self.auto_reject_threshold:
            return {
                "action": "course_correction",
                "confidence": 0.9,
                "reason": f"Low quality score ({quality_score:.2f}) requires enhancement",
                "requires_human": False
            }
        
        # Human review for edge cases
        elif self.human_review_min <= quality_score <= self.human_review_max:
            return {
                "action": "human_review",
                "confidence": 0.7,
                "reason": f"Quality score ({quality_score:.2f}) in human review range",
                "requires_human": True
            }
        
        # Default to enhancement for mid-range quality
        else:
            return {
                "action": "ai_enhancement",
                "confidence": 0.8,
                "reason": f"Quality score ({quality_score:.2f}) can be improved with AI enhancement",
                "requires_human": False
            }
    
    async def _execute_quality_decision(self, artifact: AssetArtifact, decision: Dict, validation_result: Dict) -> Dict[str, Any]:
        """Execute the automated quality decision"""
        
        action = decision["action"]
        
        if action == "auto_approve":
            # Update artifact status to approved
            success = await asset_db_manager.update_artifact_status(
                artifact.id, 
                "approved", 
                validation_result.get("quality_score")
            )
            
            return {
                "status": "approved",
                "automated": True,
                "update_success": success
            }
        
        elif action == "human_review":
            # Flag for human review
            success = await asset_db_manager.update_artifact_status(
                artifact.id,
                "pending_review",
                validation_result.get("quality_score")
            )
            
            return {
                "status": "pending_human_review",
                "automated": False,
                "update_success": success,
                "review_priority": self._calculate_review_priority(validation_result)
            }
        
        elif action == "ai_enhancement":
            # Trigger AI enhancement
            enhanced_result = await self.quality_engine.auto_enhance_content(artifact)
            
            return {
                "status": "ai_enhanced",
                "automated": True,
                "enhancement_applied": enhanced_result.get("enhancement_applied", False),
                "new_quality_score": enhanced_result.get("new_quality_score", 0.0)
            }
        
        elif action == "course_correction":
            # Mark for course correction
            success = await asset_db_manager.update_artifact_status(
                artifact.id,
                "needs_correction",
                validation_result.get("quality_score")
            )
            
            return {
                "status": "course_correction_triggered",
                "automated": True,
                "update_success": success
            }
        
        else:
            return {
                "status": "unknown_action",
                "automated": False,
                "error": f"Unknown action: {action}"
            }
    
    async def _trigger_course_correction(self, artifact: AssetArtifact, validation_result: Dict) -> Dict[str, Any]:
        """
        Trigger automated course correction (Pillar 13: Course-Correction)
        """
        try:
            # Extract improvement suggestions from validation
            suggestions = validation_result.get("improvement_suggestions", [])
            
            # Create course correction task
            correction_task = {
                "artifact_id": str(artifact.id),
                "correction_type": "quality_improvement",
                "suggestions": suggestions,
                "priority": "high",
                "automated": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # In a real implementation, this would create a task for agents
            logger.info(f"🔄 Course correction triggered for {artifact.artifact_name}")
            
            return {
                "course_correction_triggered": True,
                "correction_task_id": f"cc-{artifact.id}",
                "suggestions_count": len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger course correction: {e}")
            return {
                "course_correction_triggered": False,
                "error": str(e)
            }
    
    def _calculate_review_priority(self, validation_result: Dict) -> str:
        """Calculate human review priority based on validation results"""
        quality_score = validation_result.get("quality_score", 0.0)
        business_impact = validation_result.get("business_impact", 0.0)
        
        if quality_score > 0.75 and business_impact > 0.8:
            return "high"
        elif quality_score > 0.7:
            return "medium"
        else:
            return "low"
    
    async def batch_process_pending_artifacts(self, workspace_id: UUID) -> Dict[str, Any]:
        """
        Batch process all pending artifacts for quality automation
        Useful for retroactive quality gate application
        """
        try:
            # Get all pending artifacts
            artifacts = await asset_db_manager.get_workspace_asset_artifacts(workspace_id)
            pending_artifacts = [a for a in artifacts if a.status in ["draft", "pending"]]
            
            logger.info(f"🔄 Batch processing {len(pending_artifacts)} pending artifacts")
            
            results = []
            for artifact in pending_artifacts:
                result = await self.auto_process_new_artifact(artifact)
                results.append(result)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            # Summary
            approved = len([r for r in results if r.get("automated_decision", {}).get("action") == "auto_approve"])
            enhanced = len([r for r in results if r.get("automated_decision", {}).get("action") == "ai_enhancement"])
            human_review = len([r for r in results if r.get("automated_decision", {}).get("action") == "human_review"])
            
            return {
                "total_processed": len(results),
                "auto_approved": approved,
                "ai_enhanced": enhanced,
                "human_review_required": human_review,
                "automation_rate": (approved + enhanced) / len(results) * 100 if results else 0
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {"error": str(e)}

# Global instance
quality_automation = QualityAutomationEngine()

# Convenience functions
async def auto_validate_artifact(artifact: AssetArtifact) -> Dict[str, Any]:
    """Auto-validate single artifact through quality pipeline"""
    return await quality_automation.auto_process_new_artifact(artifact)

async def batch_validate_workspace(workspace_id: UUID) -> Dict[str, Any]:
    """Batch validate all pending artifacts in workspace"""
    return await quality_automation.batch_process_pending_artifacts(workspace_id)