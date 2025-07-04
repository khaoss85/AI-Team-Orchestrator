# backend/config/quality_system_config.py

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Utility functions for environment variable parsing
def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable with default"""
    return os.getenv(key, str(default)).lower() == "true"

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable with default"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable with default"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

class QualitySystemConfig:
    """
    Configurazione centralizzata per il sistema di AI Quality Assurance
    """
    
    # === CORE SETTINGS ===
    # ENHANCED: Quality assurance ora è OBBLIGATORIO per asset production tasks
    ENABLE_AI_QUALITY_EVALUATION: bool = os.getenv("ENABLE_AI_QUALITY_EVALUATION", "true").lower() == "true"
    INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM: bool = os.getenv("INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM", "true").lower() == "true"
    FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR: bool = os.getenv("FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR", "true").lower() == "true"
    
    # NUOVO: Enforce quality per asset production (non opzionale)
    MANDATORY_QUALITY_FOR_ASSETS: bool = os.getenv("MANDATORY_QUALITY_FOR_ASSETS", "true").lower() == "true"
    BLOCK_LOW_QUALITY_ASSETS: bool = os.getenv("BLOCK_LOW_QUALITY_ASSETS", "false").lower() == "true"
    
    # === AI-ADAPTIVE QUALITY THRESHOLDS ===
    # 🤖 AI-DRIVEN: Dynamic thresholds based on context and domain
    ENABLE_AI_ADAPTIVE_THRESHOLDS: bool = os.getenv("ENABLE_AI_ADAPTIVE_THRESHOLDS", "true").lower() == "true"
    
    # Fallback static thresholds (used when AI is unavailable) - Reduced for better success rate
    QUALITY_SCORE_THRESHOLD: float = float(os.getenv("QUALITY_SCORE_THRESHOLD", "0.6"))
    ACTIONABILITY_THRESHOLD: float = float(os.getenv("ACTIONABILITY_THRESHOLD", "0.5"))  
    AUTHENTICITY_THRESHOLD: float = float(os.getenv("AUTHENTICITY_THRESHOLD", "0.6"))
    COMPLETENESS_THRESHOLD: float = float(os.getenv("COMPLETENESS_THRESHOLD", "0.5"))
    CONCRETE_CONTENT_THRESHOLD: float = float(os.getenv("CONCRETE_CONTENT_THRESHOLD", "0.6"))
    PLACEHOLDER_DETECTION_THRESHOLD: float = float(os.getenv("PLACEHOLDER_DETECTION_THRESHOLD", "0.3"))
    
    # === AI-ADAPTIVE ENHANCEMENT SETTINGS ===
    AUTO_CREATE_ENHANCEMENT_TASKS: bool = os.getenv("AUTO_CREATE_ENHANCEMENT_TASKS", "true").lower() == "true"
    ENABLE_AI_ADAPTIVE_ENHANCEMENT: bool = os.getenv("ENABLE_AI_ADAPTIVE_ENHANCEMENT", "true").lower() == "true"
    
    # Fallback static values
    MAX_ENHANCEMENT_ATTEMPTS: int = int(os.getenv("MAX_ENHANCEMENT_ATTEMPTS", "3"))
    ENHANCEMENT_TASK_PRIORITY: str = os.getenv("ENHANCEMENT_TASK_PRIORITY", "high")
    
    # Settings specifici per migliorare contenuto concreto
    REQUIRE_SPECIFIC_EXAMPLES: bool = os.getenv("REQUIRE_SPECIFIC_EXAMPLES", "true").lower() == "true"
    DETECT_THEORETICAL_LANGUAGE: bool = os.getenv("DETECT_THEORETICAL_LANGUAGE", "true").lower() == "true"
    ENFORCE_ACTIONABLE_OUTPUTS: bool = os.getenv("ENFORCE_ACTIONABLE_OUTPUTS", "true").lower() == "true"
    
    # === MONITORING ===
    ENABLE_QUALITY_METRICS_COLLECTION: bool = os.getenv("ENABLE_QUALITY_METRICS_COLLECTION", "true").lower() == "true"
    ENABLE_DETAILED_LOGGING: bool = os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    
    # === AI MODEL SETTINGS ===
    QUALITY_EVALUATION_MODEL: str = os.getenv("QUALITY_EVALUATION_MODEL", "gpt-4.1-mini")
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
    async def get_adaptive_quality_thresholds(cls, context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """🤖 AI-DRIVEN: Get context-adaptive quality thresholds"""
        if not cls.ENABLE_AI_ADAPTIVE_THRESHOLDS or not context:
            return cls.get_static_quality_thresholds()
        
        try:
            return await cls._calculate_ai_adaptive_thresholds(context)
        except Exception as e:
            logger.warning(f"AI adaptive thresholds failed, using static: {e}")
            return cls.get_static_quality_thresholds()
    
    @classmethod
    def get_static_quality_thresholds(cls) -> Dict[str, float]:
        """Get static fallback quality thresholds"""
        return {
            "overall": cls.QUALITY_SCORE_THRESHOLD,
            "actionability": cls.ACTIONABILITY_THRESHOLD,
            "authenticity": cls.AUTHENTICITY_THRESHOLD,
            "completeness": cls.COMPLETENESS_THRESHOLD,
            "concrete_content": cls.CONCRETE_CONTENT_THRESHOLD,
            "placeholder_detection": cls.PLACEHOLDER_DETECTION_THRESHOLD
        }
    
    @classmethod
    async def _calculate_ai_adaptive_thresholds(cls, context: Dict[str, Any]) -> Dict[str, float]:
        """🤖 AI-DRIVEN: Calculate adaptive thresholds based on context"""
        try:
            # Initialize OpenAI client if available
            openai_client = None
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from openai import AsyncOpenAI
                    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                except ImportError:
                    pass
            
            if not openai_client:
                return cls.get_static_quality_thresholds()
            
            # Extract context information
            domain = context.get("domain", "general")
            complexity = context.get("complexity", "medium")
            deliverable_type = context.get("deliverable_type", "document")
            user_expectations = context.get("user_expectations", "standard")
            project_phase = context.get("project_phase", "implementation")
            
            ai_prompt = f"""
            Determine appropriate quality thresholds for this context:
            
            Domain: {domain}
            Complexity: {complexity}
            Deliverable Type: {deliverable_type}
            User Expectations: {user_expectations}
            Project Phase: {project_phase}
            
            Return JSON with quality thresholds (0.0-1.0) for:
            - overall: Overall quality score requirement
            - actionability: How actionable/practical the content should be
            - authenticity: How specific and realistic vs generic the content should be
            - completeness: How complete and thorough the content should be
            - concrete_content: How concrete vs theoretical the content should be
            - placeholder_detection: Sensitivity for detecting placeholder content
            
            Consider:
            - Technical domains need higher authenticity and completeness
            - Creative domains might accept lower concrete_content thresholds
            - Early project phases can have lower completeness requirements
            - High user expectations increase all thresholds
            
            Format: {{"overall": 0.85, "actionability": 0.8, ...}}
            """
            
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at quality assurance and adaptive standards. Provide only valid JSON output."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            ai_result = response.choices[0].message.content.strip()
            import json
            adaptive_thresholds = json.loads(ai_result)
            
            # Validate ranges and add missing keys
            static_thresholds = cls.get_static_quality_thresholds()
            for key, fallback_value in static_thresholds.items():
                if key not in adaptive_thresholds:
                    adaptive_thresholds[key] = fallback_value
                else:
                    # Ensure values are in reasonable range - more lenient minimums
                    adaptive_thresholds[key] = max(0.4, min(0.9, adaptive_thresholds[key]))
            
            logger.info(f"✅ AI-adaptive quality thresholds calculated for {domain}/{complexity}")
            return adaptive_thresholds
            
        except Exception as e:
            logger.warning(f"AI adaptive threshold calculation failed: {e}")
            return cls.get_static_quality_thresholds()
    
    @classmethod
    async def get_adaptive_enhancement_attempts(cls, task_context: Optional[Dict[str, Any]] = None) -> int:
        """🤖 AI-DRIVEN: Get adaptive enhancement attempts based on task context"""
        if not cls.ENABLE_AI_ADAPTIVE_ENHANCEMENT or not task_context:
            return cls.MAX_ENHANCEMENT_ATTEMPTS
        
        try:
            complexity = task_context.get("complexity", "medium")
            importance = task_context.get("importance", "medium")
            deadline_urgency = task_context.get("deadline_urgency", "medium")
            
            # Simple AI-driven logic (can be enhanced with OpenAI API if needed)
            base_attempts = cls.MAX_ENHANCEMENT_ATTEMPTS
            
            if complexity == "high":
                base_attempts += 1
            elif complexity == "low":
                base_attempts = max(1, base_attempts - 1)
            
            if importance == "high":
                base_attempts += 1
            elif importance == "low":
                base_attempts = max(1, base_attempts - 1)
            
            if deadline_urgency == "high":
                base_attempts = max(1, base_attempts - 1)  # Less attempts under time pressure
            
            return max(1, min(6, base_attempts))  # Keep within reasonable bounds
            
        except Exception as e:
            logger.warning(f"Adaptive enhancement attempts calculation failed: {e}")
            return cls.MAX_ENHANCEMENT_ATTEMPTS
    
    # Legacy method for backwards compatibility
    @classmethod
    def get_quality_thresholds(cls) -> Dict[str, float]:
        """Legacy method - use get_adaptive_quality_thresholds for AI-driven thresholds"""
        return cls.get_static_quality_thresholds()