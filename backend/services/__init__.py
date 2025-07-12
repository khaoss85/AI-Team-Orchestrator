# backend/services/__init__.py
"""
Services Module - Enhanced with Unified Memory Engine and Deliverable Aliases
Contains all service layer components including unified memory system and deliverable system aliases.
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
    
    # Import deliverable engine for aliasing
    import sys
    from pathlib import Path
    # Add project root to Python path for consistent imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine as deliverable_engine
    
    # Primary exports (unified engine)
    memory_system = unified_memory_engine
    universal_memory_architecture = unified_memory_engine
    memory_enhanced_ai_asset_generator = unified_memory_engine
    
    # --- DELIVERABLE SYSTEM ALIASES ---
    # This ensures that old imports like `from services.asset_artifact_processor import ...` still work
    AssetArtifactProcessor = deliverable_engine
    AssetRequirementsGenerator = deliverable_engine
    AssetFirstDeliverableSystem = deliverable_engine
    
    __all__ = [
        # Unified memory engine
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
        'memory_enhanced_ai_asset_generator',
        
        # Deliverable System Aliases
        'AssetArtifactProcessor',
        'AssetRequirementsGenerator',
        'AssetFirstDeliverableSystem'
    ]
    
    MEMORY_SYSTEM_AVAILABLE = True
    
    logger.info("🧠 Unified Memory System loaded successfully")
    logger.info("   ├─ Consolidated 3 files into unified_memory_engine.py")
    logger.info("   ├─ Backward compatibility maintained for all imports")
    logger.info("   └─ Memory patterns, context storage, and AI generation unified")
    
except ImportError as e:
    logger.warning(f"Memory or Deliverable System not fully available: {e}")
    MEMORY_SYSTEM_AVAILABLE = False
    __all__ = []