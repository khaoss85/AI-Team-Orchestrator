# backend/config/quality_system_config.py

import os
from typing import Dict, Any

class QualitySystemConfig:
    """
    Configurazione centralizzata per il sistema di AI Quality Assurance
    """
    
    # === CORE SETTINGS ===
    ENABLE_AI_QUALITY_EVALUATION: bool = os.getenv("ENABLE_AI_QUALITY_EVALUATION", "true").lower() == "true"
    INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM: bool = os.getenv("INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM", "true").lower() == "true"
    FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR: bool = os.getenv("FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR", "true").lower() == "true"
    
    # === QUALITY THRESHOLDS ===
    QUALITY_SCORE_THRESHOLD: float = float(os.getenv("QUALITY_SCORE_THRESHOLD", "0.8"))
    ACTIONABILITY_THRESHOLD: float = float(os.getenv("ACTIONABILITY_THRESHOLD", "0.7"))
    AUTHENTICITY_THRESHOLD: float = float(os.getenv("AUTHENTICITY_THRESHOLD", "0.8"))
    COMPLETENESS_THRESHOLD: float = float(os.getenv("COMPLETENESS_THRESHOLD", "0.7"))
    
    # === ENHANCEMENT SETTINGS ===
    AUTO_CREATE_ENHANCEMENT_TASKS: bool = os.getenv("AUTO_CREATE_ENHANCEMENT_TASKS", "true").lower() == "true"
    MAX_ENHANCEMENT_ATTEMPTS: int = int(os.getenv("MAX_ENHANCEMENT_ATTEMPTS", "5"))
    ENHANCEMENT_TASK_PRIORITY: str = os.getenv("ENHANCEMENT_TASK_PRIORITY", "high")
    
    # === MONITORING ===
    ENABLE_QUALITY_METRICS_COLLECTION: bool = os.getenv("ENABLE_QUALITY_METRICS_COLLECTION", "true").lower() == "true"
    ENABLE_DETAILED_LOGGING: bool = os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    
    # === AI MODEL SETTINGS ===
    QUALITY_EVALUATION_MODEL: str = os.getenv("QUALITY_EVALUATION_MODEL", "gpt-4o-mini")
    QUALITY_EVALUATION_TEMPERATURE: float = float(os.getenv("QUALITY_EVALUATION_TEMPERATURE", "0.1"))
    QUALITY_EVALUATION_MAX_TOKENS: int = int(os.getenv("QUALITY_EVALUATION_MAX_TOKENS", "1000"))
    QUALITY_EVALUATION_TIMEOUT: float = float(os.getenv("QUALITY_EVALUATION_TIMEOUT", "30.0"))
    
    # === COST MANAGEMENT ===
    MAX_QUALITY_ANALYSIS_COST_PER_ASSET: float = float(os.getenv("MAX_QUALITY_ANALYSIS_COST_PER_ASSET", "0.10"))
    ENABLE_COST_TRACKING: bool = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Ottieni tutte le impostazioni come dizionario"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
    
    @classmethod
    def is_quality_system_enabled(cls) -> bool:
        """Verifica se il sistema di qualità è completamente abilitato"""
        return (
            cls.ENABLE_AI_QUALITY_EVALUATION and
            cls.INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM
        )
    
    @classmethod
    def get_quality_thresholds(cls) -> Dict[str, float]:
        """Ottieni tutti i threshold di qualità"""
        return {
            "overall": cls.QUALITY_SCORE_THRESHOLD,
            "actionability": cls.ACTIONABILITY_THRESHOLD,
            "authenticity": cls.AUTHENTICITY_THRESHOLD,
            "completeness": cls.COMPLETENESS_THRESHOLD
        }