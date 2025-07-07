# backend/services/__init__.py
"""
Services Module - Enhanced with Unified Memory Engine
Contains all service layer components including unified memory system
"""

import logging

logger = logging.getLogger(__name__)

try:
    # Import unified memory engine
    from .unified_memory_engine import (
        unified_memory_engine,
        UnifiedMemoryEngine,
        get_universal_memory_architecture,
        # Data classes
        ContextEntry,
        MemoryPattern,
        AssetGenerationResult,
        ContentQuality,
        # Backward compatibility aliases
        MemorySystem,
        UniversalMemoryArchitecture,
        MemoryEnhancedAIAssetGenerator
    )
    
    # Primary exports (unified engine)
    memory_system = unified_memory_engine
    universal_memory_architecture = unified_memory_engine
    memory_enhanced_ai_asset_generator = unified_memory_engine
    
    __all__ = [
        # Unified engine
        'unified_memory_engine',
        'UnifiedMemoryEngine',
        'get_universal_memory_architecture',
        
        # Data classes
        'ContextEntry',
        'MemoryPattern', 
        'AssetGenerationResult',
        'ContentQuality',
        
        # Backward compatibility classes
        'MemorySystem',
        'UniversalMemoryArchitecture',
        'MemoryEnhancedAIAssetGenerator',
        
        # Singleton instances for compatibility
        'memory_system',
        'universal_memory_architecture',
        'memory_enhanced_ai_asset_generator'
    ]
    
    MEMORY_SYSTEM_AVAILABLE = True
    
    logger.info("🧠 Unified Memory System loaded successfully")
    logger.info("   ├─ Consolidated 3 files into unified_memory_engine.py")
    logger.info("   ├─ Backward compatibility maintained for all imports")
    logger.info("   └─ Memory patterns, context storage, and AI generation unified")
    
except ImportError as e:
    logger.warning(f"Memory System not fully available: {e}")
    MEMORY_SYSTEM_AVAILABLE = False
    __all__ = []