# backend/ai_quality_assurance/__init__.py
"""
AI Quality Assurance System
"""

import logging

logger = logging.getLogger(__name__)

try:
    from .quality_validator import AIQualityValidator, QualityAssessment, QualityIssueType
    from .ai_evaluator import EnhancedAIQualityValidator, AIQualityEvaluator
    from .enhancement_orchestrator import AssetEnhancementOrchestrator, EnhancementPlan
    from .quality_integration import DynamicPromptEnhancer, quality_metrics_collector
    
    __all__ = [
        'AIQualityValidator',
        'QualityAssessment', 
        'QualityIssueType',
        'EnhancedAIQualityValidator',
        'AIQualityEvaluator',
        'AssetEnhancementOrchestrator',
        'EnhancementPlan',
        'DynamicPromptEnhancer',
        'quality_metrics_collector'
    ]
    
    QUALITY_SYSTEM_AVAILABLE = True
    
except ImportError as e:
    logger.warning(f"AI Quality Assurance system not fully available: {e}")
    QUALITY_SYSTEM_AVAILABLE = False
    __all__ = []
