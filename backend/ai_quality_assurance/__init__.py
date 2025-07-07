# backend/ai_quality_assurance/__init__.py
"""
AI Quality Assurance System - Unified v1.0
Consolidated from 13 files into unified_quality_engine.py
Maintains backward compatibility for all imports
"""

import logging

logger = logging.getLogger(__name__)

try:
    # Import unified engine
    from .unified_quality_engine import (
        unified_quality_engine,
        UnifiedQualityEngine,
        QualityAssessment,
        EnhancementPlan,
        # Backward compatibility aliases
        SmartDeliverableEvaluator,
        AssetEnhancementOrchestrator,
        AIQualityEvaluator,
        EnhancedAIQualityValidator
    )
    
    # Legacy compatibility - import from unified engine instead of removed modules
    from enum import Enum
    class QualityIssueType(Enum):
        FAKE_CONTENT = "fake_content"
        INCOMPLETE_DATA = "incomplete_data"
        LOW_ACTIONABILITY = "low_actionability"
        GENERIC_STRUCTURE = "generic_structure"
        PLACEHOLDER_DATA = "placeholder_data"
    
    # Legacy modules consolidated into unified engine
    logger.info("Legacy quality_integration module consolidated into unified engine")
    DynamicPromptEnhancer = None  # Integrated into unified engine
    quality_metrics_collector = None  # Integrated into unified engine
    
    # Primary exports (unified engine)
    AIQualityValidator = unified_quality_engine
    smart_evaluator = unified_quality_engine
    enhancement_orchestrator = unified_quality_engine
    ai_evaluator = unified_quality_engine
    
    __all__ = [
        # Unified engine
        'unified_quality_engine',
        'UnifiedQualityEngine',
        
        # Backward compatibility classes
        'AIQualityValidator',
        'QualityAssessment', 
        'QualityIssueType',
        'EnhancedAIQualityValidator',
        'AIQualityEvaluator',
        'AssetEnhancementOrchestrator',
        'EnhancementPlan',
        'SmartDeliverableEvaluator',
        
        # Singleton instances for compatibility
        'smart_evaluator',
        'enhancement_orchestrator', 
        'ai_evaluator',
        
        # Legacy compatibility (may be None)
        'DynamicPromptEnhancer',
        'quality_metrics_collector'
    ]
    
    QUALITY_SYSTEM_AVAILABLE = True
    
    logger.info("🔧 Unified Quality Assurance System loaded successfully")
    logger.info("   ├─ Consolidated 13 files into unified_quality_engine.py")
    logger.info("   ├─ Backward compatibility maintained for all imports")
    logger.info("   └─ Duplicate functions eliminated (unified __init__, reset_stats, _detect_fake_content)")
    
except ImportError as e:
    logger.warning(f"AI Quality Assurance system not fully available: {e}")
    QUALITY_SYSTEM_AVAILABLE = False
    __all__ = []
