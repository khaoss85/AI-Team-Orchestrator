# backend/deliverable_system/__init__.py
"""
Deliverable System - Unified v1.0
Consolidated from 6 files into unified_deliverable_engine.py
Maintains backward compatibility for all imports
"""

import logging

logger = logging.getLogger(__name__)

try:
    # Import unified engine
    from .unified_deliverable_engine import (
        unified_deliverable_engine,
        UnifiedDeliverableEngine,
        # Standalone functions for backward compatibility
        check_and_create_final_deliverable,
        create_intelligent_deliverable,
        deliverable_aggregator
    )
    
    # Primary exports (unified engine)
    concrete_extractor = unified_deliverable_engine
    markup_processor = unified_deliverable_engine
    deliverable_pipeline = unified_deliverable_engine
    requirements_analyzer = unified_deliverable_engine
    schema_generator = unified_deliverable_engine
    ai_display_enhancer = unified_deliverable_engine
    multi_source_extractor = unified_deliverable_engine
    universal_ai_content_extractor = unified_deliverable_engine
    
    __all__ = [
        # Unified engine
        'unified_deliverable_engine',
        'UnifiedDeliverableEngine',
        
        # Standalone functions for backward compatibility
        'check_and_create_final_deliverable',
        'create_intelligent_deliverable',
        'deliverable_aggregator',
        
        # deliverable_aggregator.py compatibility aliases  
        'IntelligentDeliverableAggregator',
        'AIDeliverableAnalyzer',
        'DynamicAssetExtractor',
        'IntelligentDeliverablePackager',
        
        # Backward compatibility classes
        'AIDisplayEnhancer',
        'MultiSourceAssetExtractor',
        'UniversalAIContentExtractor',
        
        # Singleton instances for compatibility
        'concrete_extractor',
        'markup_processor',
        'deliverable_pipeline',
        'requirements_analyzer',
        'schema_generator',
        'ai_display_enhancer',
        'multi_source_extractor',
        'universal_ai_content_extractor'
    ]
    
    # Backward compatibility aliases
    deliverable_aggregator = unified_deliverable_engine
    IntelligentDeliverableAggregator = unified_deliverable_engine
    AIDeliverableAnalyzer = unified_deliverable_engine
    DynamicAssetExtractor = unified_deliverable_engine
    IntelligentDeliverablePackager = unified_deliverable_engine
    ConcreteAssetExtractor = unified_deliverable_engine
    AIDisplayEnhancer = unified_deliverable_engine
    MultiSourceAssetExtractor = unified_deliverable_engine
    UniversalAIContentExtractor = unified_deliverable_engine
    DeliverableMarkupProcessor = unified_deliverable_engine
    DeliverablePipeline = unified_deliverable_engine
    RequirementsAnalyzer = unified_deliverable_engine
    AssetSchemaGenerator = unified_deliverable_engine
    
    DELIVERABLE_SYSTEM_AVAILABLE = True
    
    logger.info("🔧 Unified Deliverable System loaded successfully")
    logger.info("   ├─ Consolidated 6 files into unified_deliverable_engine.py")
    logger.info("   ├─ Backward compatibility maintained for all imports")
    logger.info("   └─ Eliminated duplicate functionality across deliverable components")
    
except ImportError as e:
    logger.warning(f"Deliverable System not fully available: {e}")
    DELIVERABLE_SYSTEM_AVAILABLE = False
    __all__ = []