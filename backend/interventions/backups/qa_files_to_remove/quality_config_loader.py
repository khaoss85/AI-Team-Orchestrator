# backend/utils/quality_config_loader.py
"""
Utility centralizzato per caricare QualitySystemConfig con fallback robusti
"""

import logging
import os
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Cache globale per evitare multiple import
_quality_config_cache = None
_quality_available_cache = None

def load_quality_system_config() -> tuple[Optional[Any], bool]:
    """
    Carica QualitySystemConfig con tutti i possibili path di fallback
    
    Returns:
        tuple[QualitySystemConfig_class_or_None, is_available]
    """
    global _quality_config_cache, _quality_available_cache
    
    # Return cached result se già caricato
    if _quality_available_cache is not None:
        return _quality_config_cache, _quality_available_cache
    
    # Lista di path da provare in ordine
    import_paths = [
        "backend.config.quality_system_config",
        "config.quality_system_config", 
        "quality_system_config",
        "backend.ai_quality_assurance.config.quality_system_config",
        "ai_quality_assurance.config.quality_system_config"
    ]
    
    QualitySystemConfig = None
    
    for import_path in import_paths:
        try:
            logger.debug(f"Attempting to import QualitySystemConfig from {import_path}")
            
            if import_path == "backend.config.quality_system_config":
                from backend.config.quality_system_config import QualitySystemConfig
            elif import_path == "config.quality_system_config":
                from config.quality_system_config import QualitySystemConfig
            elif import_path == "quality_system_config":
                import quality_system_config
                QualitySystemConfig = quality_system_config.QualitySystemConfig
            elif import_path == "backend.ai_quality_assurance.config.quality_system_config":
                from backend.ai_quality_assurance.config.quality_system_config import QualitySystemConfig
            elif import_path == "ai_quality_assurance.config.quality_system_config":
                from backend.ai_quality_assurance.unified_quality_engine import QualitySystemConfig
            
            if QualitySystemConfig:
                logger.info(f"✅ QualitySystemConfig loaded successfully from {import_path}")
                _quality_config_cache = QualitySystemConfig
                _quality_available_cache = True
                return QualitySystemConfig, True
                
        except ImportError as e:
            logger.debug(f"Import from {import_path} failed: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error importing from {import_path}: {e}")
            continue
    
    # Se tutti gli import falliscono, crea una classe fallback
    logger.warning("⚠️ QualitySystemConfig not available from any path, creating fallback")
    
    class QualitySystemConfigFallback:
        """Fallback class con valori di default"""
        QUALITY_SCORE_THRESHOLD = 0.8
        ACTIONABILITY_THRESHOLD = 0.7
        AUTHENTICITY_THRESHOLD = 0.8
        COMPLETENESS_THRESHOLD = 0.7
        ENABLE_AI_QUALITY_EVALUATION = True
        INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM = True
        FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR = True
        AUTO_CREATE_ENHANCEMENT_TASKS = True
        MAX_ENHANCEMENT_ATTEMPTS = 5
        ENHANCEMENT_TASK_PRIORITY = "high"
        ENABLE_QUALITY_METRICS_COLLECTION = True
        ENABLE_DETAILED_LOGGING = True
        QUALITY_EVALUATION_MODEL = "gpt-4.1-mini"
        QUALITY_EVALUATION_TEMPERATURE = 0.1
        QUALITY_EVALUATION_MAX_TOKENS = 1000
        QUALITY_EVALUATION_TIMEOUT = 30.0
        MAX_QUALITY_ANALYSIS_COST_PER_ASSET = 0.10
        ENABLE_COST_TRACKING = True
        
        @classmethod
        def get_all_settings(cls):
            return {
                attr: getattr(cls, attr)
                for attr in dir(cls)
                if not attr.startswith('_') and not callable(getattr(cls, attr))
            }
        
        @classmethod
        def is_quality_system_enabled(cls):
            return True
        
        @classmethod
        def get_quality_thresholds(cls):
            return {
                "overall": cls.QUALITY_SCORE_THRESHOLD,
                "actionability": cls.ACTIONABILITY_THRESHOLD,
                "authenticity": cls.AUTHENTICITY_THRESHOLD,
                "completeness": cls.COMPLETENESS_THRESHOLD
            }
    
    _quality_config_cache = QualitySystemConfigFallback
    _quality_available_cache = False  # False perché è fallback
    
    return QualitySystemConfigFallback, False

def get_quality_config():
    """Helper per ottenere solo la classe config"""
    config, _ = load_quality_system_config()
    return config

def is_quality_system_available():
    """Helper per verificare se il sistema di qualità è disponibile"""
    _, available = load_quality_system_config()
    return available

# Per compatibilità, esponi le funzioni come erano prima
def load_quality_system():
    return load_quality_system_config()

# Test della configurazione al momento dell'import
if __name__ == "__main__":
    config, available = load_quality_system_config()
    logger.info(f"Quality system test: Available={available}, Config={config.__name__ if config else None}")
    if config:
        logger.info(f"Quality threshold: {config.QUALITY_SCORE_THRESHOLD}")