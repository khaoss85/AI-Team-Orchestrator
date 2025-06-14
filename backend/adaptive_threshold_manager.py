#!/usr/bin/env python3
"""
🎯 ADAPTIVE THRESHOLD MANAGER
Gestisce soglie dinamiche basate su contesto e performance storica
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdaptiveThresholdManager:
    """
    Gestisce soglie adattive per feedback requests basate su:
    - Performance storica dell'agent
    - Tipo di task
    - Track record del workspace
    - Complexity del contenuto
    """
    
    def __init__(self):
        self.agent_performance: Dict[str, Dict] = defaultdict(lambda: {
            "approvals": 0,
            "rejections": 0,
            "total_requests": 0,
            "avg_quality": 0.0,
            "track_record": "new"
        })
        
        self.task_type_thresholds = {
            "research": 0.60,      # Research tasks more lenient
            "data_collection": 0.65,
            "content_creation": 0.75,
            "strategic_planning": 0.85,  # Strategic tasks stricter
            "financial_analysis": 0.90   # Financial tasks strictest
        }
        
        self.workspace_multipliers = {}
        
    def get_adaptive_threshold(
        self, 
        base_threshold: float,
        agent_id: str,
        task_type: str,
        workspace_id: str,
        content_complexity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calcola soglia adattiva basata su contesto multiple
        """
        
        # Base threshold adjustment
        adjusted_threshold = base_threshold
        adjustments = []
        
        # 1. Agent performance adjustment
        agent_perf = self.agent_performance.get(agent_id, {})
        if agent_perf.get("total_requests", 0) >= 10:  # Sufficient data
            approval_rate = agent_perf["approvals"] / agent_perf["total_requests"]
            
            if approval_rate >= 0.95:  # Excellent track record
                adjusted_threshold -= 0.15
                adjustments.append(f"Agent excellence bonus: -0.15 (approval rate: {approval_rate:.1%})")
            elif approval_rate >= 0.85:  # Good track record  
                adjusted_threshold -= 0.10
                adjustments.append(f"Agent performance bonus: -0.10 (approval rate: {approval_rate:.1%})")
            elif approval_rate <= 0.60:  # Poor track record
                adjusted_threshold += 0.10
                adjustments.append(f"Agent performance penalty: +0.10 (approval rate: {approval_rate:.1%})")
        
        # 2. Task type adjustment
        task_threshold = self.task_type_thresholds.get(task_type, 0.75)
        task_adjustment = (task_threshold - 0.75) * 0.5  # 50% of difference
        adjusted_threshold += task_adjustment
        if task_adjustment != 0:
            adjustments.append(f"Task type '{task_type}': {task_adjustment:+.2f}")
        
        # 3. Content complexity adjustment
        if content_complexity >= 0.8:  # High complexity
            adjusted_threshold -= 0.05
            adjustments.append("High complexity bonus: -0.05")
        elif content_complexity <= 0.3:  # Low complexity
            adjusted_threshold += 0.05
            adjustments.append("Low complexity penalty: +0.05")
        
        # 4. Workspace track record
        workspace_multiplier = self.workspace_multipliers.get(workspace_id, 1.0)
        if workspace_multiplier != 1.0:
            old_threshold = adjusted_threshold
            adjusted_threshold *= workspace_multiplier
            adjustments.append(f"Workspace multiplier: ×{workspace_multiplier:.2f} ({old_threshold:.2f}→{adjusted_threshold:.2f})")
        
        # Bounds checking
        adjusted_threshold = max(0.20, min(0.95, adjusted_threshold))
        
        logger.info(f"🎯 ADAPTIVE THRESHOLD: {base_threshold:.2f} → {adjusted_threshold:.2f}")
        for adjustment in adjustments:
            logger.debug(f"    {adjustment}")
        
        return {
            "base_threshold": base_threshold,
            "adjusted_threshold": adjusted_threshold,
            "adjustments": adjustments,
            "confidence": self._calculate_adjustment_confidence(agent_perf, task_type, workspace_id)
        }
    
    def update_agent_performance(
        self, 
        agent_id: str, 
        was_approved: bool, 
        quality_score: float
    ):
        """
        Aggiorna performance tracking per agent
        """
        
        perf = self.agent_performance[agent_id]
        
        if was_approved:
            perf["approvals"] += 1
        else:
            perf["rejections"] += 1
        
        perf["total_requests"] += 1
        
        # Update running average quality
        if perf["avg_quality"] == 0:
            perf["avg_quality"] = quality_score
        else:
            perf["avg_quality"] = (perf["avg_quality"] * (perf["total_requests"] - 1) + quality_score) / perf["total_requests"]
        
        # Update track record
        approval_rate = perf["approvals"] / perf["total_requests"]
        if approval_rate >= 0.90 and perf["total_requests"] >= 20:
            perf["track_record"] = "excellent"
        elif approval_rate >= 0.80 and perf["total_requests"] >= 10:
            perf["track_record"] = "good"
        elif approval_rate >= 0.60:
            perf["track_record"] = "average"
        else:
            perf["track_record"] = "needs_improvement"
        
        logger.debug(f"📊 AGENT UPDATE: {agent_id} - Approval: {approval_rate:.1%}, Quality: {perf['avg_quality']:.2f}, Track: {perf['track_record']}")
    
    def update_workspace_performance(self, workspace_id: str, overall_success_rate: float):
        """
        Aggiorna performance tracking per workspace
        """
        
        if overall_success_rate >= 0.95:
            self.workspace_multipliers[workspace_id] = 0.85  # Lower thresholds for excellent workspaces
        elif overall_success_rate >= 0.85:
            self.workspace_multipliers[workspace_id] = 0.90
        elif overall_success_rate <= 0.60:
            self.workspace_multipliers[workspace_id] = 1.15  # Higher thresholds for struggling workspaces
        else:
            self.workspace_multipliers[workspace_id] = 1.0
        
        logger.info(f"🏢 WORKSPACE UPDATE: {workspace_id} - Success: {overall_success_rate:.1%}, Multiplier: {self.workspace_multipliers[workspace_id]:.2f}")
    
    def _calculate_adjustment_confidence(
        self, 
        agent_perf: Dict, 
        task_type: str, 
        workspace_id: str
    ) -> float:
        """
        Calcola confidence nell'adjustment basato su quantità di dati
        """
        
        confidence = 0.5  # Base confidence
        
        # Agent data confidence
        total_requests = agent_perf.get("total_requests", 0)
        if total_requests >= 50:
            confidence += 0.3
        elif total_requests >= 20:
            confidence += 0.2
        elif total_requests >= 10:
            confidence += 0.1
        
        # Task type confidence (based on how common the task type is)
        common_task_types = ["research", "content_creation", "data_collection"]
        if task_type in common_task_types:
            confidence += 0.1
        
        # Workspace data confidence
        if workspace_id in self.workspace_multipliers:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Ottiene statistiche performance per monitoring
        """
        
        stats = {
            "total_agents_tracked": len(self.agent_performance),
            "total_workspaces_tracked": len(self.workspace_multipliers),
            "agent_performance_distribution": defaultdict(int),
            "avg_approval_rate": 0.0
        }
        
        total_approval_rate = 0
        tracked_agents = 0
        
        for agent_id, perf in self.agent_performance.items():
            if perf["total_requests"] >= 5:  # Only count agents with sufficient data
                track_record = perf["track_record"]
                stats["agent_performance_distribution"][track_record] += 1
                
                approval_rate = perf["approvals"] / perf["total_requests"]
                total_approval_rate += approval_rate
                tracked_agents += 1
        
        if tracked_agents > 0:
            stats["avg_approval_rate"] = total_approval_rate / tracked_agents
        
        return dict(stats)

# Global instance
adaptive_threshold_manager = AdaptiveThresholdManager()
