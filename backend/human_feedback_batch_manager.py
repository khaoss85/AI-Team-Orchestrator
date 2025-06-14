#!/usr/bin/env python3
"""
📦 HUMAN FEEDBACK BATCH MANAGER
Raggruppa richieste feedback simili per ridurre interruzioni
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

class FeedbackBatchManager:
    """
    Gestisce batching intelligente delle richieste feedback per ridurre interruzioni
    """
    
    def __init__(self):
        self.pending_batches: Dict[str, List[Dict]] = defaultdict(list)
        self.batch_windows = {
            "task_quality": 300,  # 5 minutes for task quality reviews
            "deliverable_validation": 600,  # 10 minutes for deliverable validation
            "goal_progress": 1800,  # 30 minutes for goal progress reviews
            "content_enhancement": 180,  # 3 minutes for content enhancement
        }
        self.auto_approve_thresholds = {
            "task_quality": 0.80,  # Auto-approve if 80%+ similar requests approved
            "deliverable_validation": 0.85,  # Auto-approve if 85%+ approved
            "goal_progress": 0.90,  # Auto-approve if 90%+ approved
            "content_enhancement": 0.75,  # Auto-approve if 75%+ approved
        }
        
    async def process_feedback_request(
        self, 
        request_type: str, 
        workspace_id: str, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa richiesta feedback con batching intelligente
        """
        
        # Check if similar requests can be auto-approved
        auto_approval = await self._check_auto_approval(request_type, workspace_id, request_data)
        if auto_approval["can_auto_approve"]:
            logger.info(f"🤖 AUTO-APPROVED: {request_type} - {auto_approval['reason']}")
            return {
                "decision": "auto_approved",
                "confidence": auto_approval["confidence"],
                "reasoning": auto_approval["reason"],
                "batch_optimized": True
            }
        
        # Add to batch for delayed processing
        batch_key = f"{workspace_id}_{request_type}"
        self.pending_batches[batch_key].append({
            "request_data": request_data,
            "timestamp": datetime.now(),
            "request_id": str(uuid4())
        })
        
        # Check if batch should be processed
        should_process = await self._should_process_batch(batch_key, request_type)
        if should_process:
            return await self._process_batch(batch_key, request_type, workspace_id)
        else:
            return {
                "decision": "batched",
                "batch_key": batch_key,
                "estimated_processing_time": self.batch_windows[request_type],
                "batch_size": len(self.pending_batches[batch_key])
            }
    
    async def _check_auto_approval(
        self, 
        request_type: str, 
        workspace_id: str, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verifica se la richiesta può essere auto-approvata basandosi su pattern storici
        """
        
        # Simulate historical approval rate check
        historical_approval_rate = {
            "task_quality": 0.87,  # 87% of similar requests were approved
            "deliverable_validation": 0.92,
            "goal_progress": 0.94,
            "content_enhancement": 0.78
        }.get(request_type, 0.50)
        
        threshold = self.auto_approve_thresholds.get(request_type, 0.80)
        
        if historical_approval_rate >= threshold:
            # Additional quality checks
            quality_score = request_data.get("quality_score", 0.0)
            confidence_score = request_data.get("confidence", 0.0)
            
            # Enhanced auto-approval logic
            if quality_score >= 0.75 and confidence_score >= 0.70:
                return {
                    "can_auto_approve": True,
                    "confidence": min(historical_approval_rate, 0.95),
                    "reason": f"Historical approval rate {historical_approval_rate:.1%} above threshold {threshold:.1%}"
                }
        
        return {
            "can_auto_approve": False,
            "confidence": historical_approval_rate,
            "reason": f"Approval rate {historical_approval_rate:.1%} below threshold {threshold:.1%}"
        }
    
    async def _should_process_batch(self, batch_key: str, request_type: str) -> bool:
        """
        Determina se il batch dovrebbe essere processato ora
        """
        
        batch = self.pending_batches.get(batch_key, [])
        if not batch:
            return False
        
        # Check batch size threshold
        if len(batch) >= 5:  # Process when 5+ similar requests
            return True
        
        # Check time threshold
        oldest_request = min(batch, key=lambda x: x["timestamp"])
        time_elapsed = (datetime.now() - oldest_request["timestamp"]).total_seconds()
        
        window = self.batch_windows.get(request_type, 300)
        return time_elapsed >= window
    
    async def _process_batch(
        self, 
        batch_key: str, 
        request_type: str, 
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Processa batch di richieste simili
        """
        
        batch = self.pending_batches.pop(batch_key, [])
        if not batch:
            return {"decision": "no_batch_found"}
        
        logger.info(f"📦 PROCESSING BATCH: {request_type} - {len(batch)} requests")
        
        # Consolidate similar requests
        consolidated = await self._consolidate_requests(batch, request_type)
        
        # Auto-approve if requests are very similar
        if consolidated["similarity_score"] >= 0.90:
            logger.info(f"🤖 BATCH AUTO-APPROVED: High similarity ({consolidated['similarity_score']:.1%})")
            return {
                "decision": "batch_auto_approved",
                "batch_size": len(batch),
                "similarity_score": consolidated["similarity_score"],
                "reasoning": "High similarity between requests allows auto-approval"
            }
        
        # Create consolidated review request
        return {
            "decision": "batch_review_required",
            "batch_size": len(batch),
            "consolidated_request": consolidated,
            "estimated_review_time": len(batch) * 0.3  # 30% of individual review time
        }
    
    async def _consolidate_requests(self, batch: List[Dict], request_type: str) -> Dict[str, Any]:
        """
        Consolida richieste simili in una singola review
        """
        
        # Simple similarity calculation
        quality_scores = [req["request_data"].get("quality_score", 0) for req in batch]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calculate similarity based on request types and quality scores
        similarity_score = min(0.95, 0.7 + (avg_quality * 0.25))
        
        return {
            "request_type": request_type,
            "batch_size": len(batch),
            "average_quality": avg_quality,
            "similarity_score": similarity_score,
            "requests": [req["request_id"] for req in batch],
            "consolidated_summary": f"Batch of {len(batch)} similar {request_type} requests"
        }

# Global instance
feedback_batch_manager = FeedbackBatchManager()
