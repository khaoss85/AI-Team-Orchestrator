#!/usr/bin/env python3
"""
Knowledge Insights Configuration Module

Centralized configuration management for knowledge insights system.
All values are externalized to environment variables with sensible defaults.

This module ensures:
- No hardcoded configuration values
- Easy runtime configuration changes
- Clear documentation of all settings
- Validation of configuration values
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeInsightsConfig:
    """
    Configuration class for Knowledge Insights system.
    All values are loaded from environment variables with defaults.
    """
    
    # AI Configuration
    ai_enabled: bool = field(default=True)
    model: str = field(default="gpt-4")
    confidence_threshold: float = field(default=0.7)
    cache_ttl_seconds: int = field(default=3600)
    max_tags: int = field(default=10)
    default_language: str = field(default="auto")
    
    # Fallback Configuration
    fallback_categories: List[str] = field(default_factory=list)
    fallback_tags: List[str] = field(default_factory=list)
    
    # Performance Configuration
    max_content_length: int = field(default=2000)
    batch_size: int = field(default=10)
    timeout_seconds: int = field(default=30)
    
    # Feature Flags
    enable_caching: bool = field(default=True)
    enable_language_detection: bool = field(default=True)
    enable_confidence_scoring: bool = field(default=True)
    enable_semantic_tags: bool = field(default=True)
    
    def __post_init__(self):
        """Load configuration from environment variables after initialization."""
        self._load_from_env()
        self._validate_config()
        self._log_configuration()
    
    def _load_from_env(self):
        """Load all configuration values from environment variables."""
        # AI Configuration
        self.ai_enabled = os.getenv("ENABLE_AI_KNOWLEDGE_CATEGORIZATION", "true").lower() == "true"
        self.model = os.getenv("KNOWLEDGE_CATEGORIZATION_MODEL", "gpt-4")
        self.confidence_threshold = float(os.getenv("KNOWLEDGE_CONFIDENCE_THRESHOLD", "0.7"))
        self.cache_ttl_seconds = int(os.getenv("KNOWLEDGE_CACHE_TTL_SECONDS", "3600"))
        self.max_tags = int(os.getenv("MAX_KNOWLEDGE_TAGS", "10"))
        self.default_language = os.getenv("DEFAULT_KNOWLEDGE_LANGUAGE", "auto")
        
        # Fallback Configuration
        fallback_categories_str = os.getenv(
            "FALLBACK_KNOWLEDGE_CATEGORIES", 
            "discovery,optimization,success_pattern,constraint,learning"
        )
        self.fallback_categories = [c.strip() for c in fallback_categories_str.split(",")]
        
        fallback_tags_str = os.getenv(
            "FALLBACK_DEFAULT_TAGS",
            "general,insight,knowledge"
        )
        self.fallback_tags = [t.strip() for t in fallback_tags_str.split(",")]
        
        # Performance Configuration
        self.max_content_length = int(os.getenv("KNOWLEDGE_MAX_CONTENT_LENGTH", "2000"))
        self.batch_size = int(os.getenv("KNOWLEDGE_BATCH_SIZE", "10"))
        self.timeout_seconds = int(os.getenv("KNOWLEDGE_TIMEOUT_SECONDS", "30"))
        
        # Feature Flags
        self.enable_caching = os.getenv("KNOWLEDGE_ENABLE_CACHING", "true").lower() == "true"
        self.enable_language_detection = os.getenv("KNOWLEDGE_ENABLE_LANGUAGE_DETECTION", "true").lower() == "true"
        self.enable_confidence_scoring = os.getenv("KNOWLEDGE_ENABLE_CONFIDENCE_SCORING", "true").lower() == "true"
        self.enable_semantic_tags = os.getenv("KNOWLEDGE_ENABLE_SEMANTIC_TAGS", "true").lower() == "true"
    
    def _validate_config(self):
        """Validate configuration values and apply constraints."""
        # Validate confidence threshold
        if not 0.0 <= self.confidence_threshold <= 1.0:
            logger.warning(f"Invalid confidence threshold: {self.confidence_threshold}, using 0.7")
            self.confidence_threshold = 0.7
        
        # Validate max tags
        if self.max_tags < 1:
            logger.warning(f"Invalid max_tags: {self.max_tags}, using 10")
            self.max_tags = 10
        elif self.max_tags > 50:
            logger.warning(f"max_tags too high: {self.max_tags}, limiting to 50")
            self.max_tags = 50
        
        # Validate cache TTL
        if self.cache_ttl_seconds < 0:
            logger.warning(f"Invalid cache TTL: {self.cache_ttl_seconds}, disabling cache")
            self.enable_caching = False
            self.cache_ttl_seconds = 0
        
        # Validate batch size
        if self.batch_size < 1:
            logger.warning(f"Invalid batch size: {self.batch_size}, using 10")
            self.batch_size = 10
        
        # Ensure at least one fallback category
        if not self.fallback_categories:
            self.fallback_categories = ["general"]
            logger.warning("No fallback categories configured, using ['general']")
        
        # Ensure at least one fallback tag
        if not self.fallback_tags:
            self.fallback_tags = ["knowledge"]
            logger.warning("No fallback tags configured, using ['knowledge']")
    
    def _log_configuration(self):
        """Log the current configuration for debugging."""
        logger.info("Knowledge Insights Configuration loaded:")
        logger.info(f"  AI Enabled: {self.ai_enabled}")
        if self.ai_enabled:
            logger.info(f"  Model: {self.model}")
            logger.info(f"  Confidence Threshold: {self.confidence_threshold}")
        logger.info(f"  Caching: {self.enable_caching} (TTL: {self.cache_ttl_seconds}s)")
        logger.info(f"  Max Tags: {self.max_tags}")
        logger.info(f"  Language Detection: {self.enable_language_detection}")
        logger.info(f"  Fallback Categories: {', '.join(self.fallback_categories)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "ai_enabled": self.ai_enabled,
            "model": self.model,
            "confidence_threshold": self.confidence_threshold,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_tags": self.max_tags,
            "default_language": self.default_language,
            "fallback_categories": self.fallback_categories,
            "fallback_tags": self.fallback_tags,
            "max_content_length": self.max_content_length,
            "batch_size": self.batch_size,
            "timeout_seconds": self.timeout_seconds,
            "enable_caching": self.enable_caching,
            "enable_language_detection": self.enable_language_detection,
            "enable_confidence_scoring": self.enable_confidence_scoring,
            "enable_semantic_tags": self.enable_semantic_tags
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration for AI provider."""
        return {
            "model": self.model,
            "temperature": 0.7,  # Can be externalized if needed
            "max_tokens": 500,   # Can be externalized if needed
            "timeout": self.timeout_seconds
        }
    
    def should_use_ai(self) -> bool:
        """Determine if AI should be used based on configuration."""
        return self.ai_enabled and self.model
    
    def get_fallback_category(self) -> str:
        """Get the default fallback category."""
        return self.fallback_categories[0] if self.fallback_categories else "general"
    
    def get_fallback_tags(self, limit: Optional[int] = None) -> List[str]:
        """Get fallback tags up to specified limit."""
        limit = limit or self.max_tags
        return self.fallback_tags[:limit]


# Module-level configuration instance
_config_instance: Optional[KnowledgeInsightsConfig] = None


def get_config() -> KnowledgeInsightsConfig:
    """
    Get singleton instance of configuration.
    
    Returns:
        KnowledgeInsightsConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = KnowledgeInsightsConfig()
    return _config_instance


def reload_config() -> KnowledgeInsightsConfig:
    """
    Force reload configuration from environment.
    Useful for testing or runtime configuration changes.
    
    Returns:
        New KnowledgeInsightsConfig instance
    """
    global _config_instance
    _config_instance = KnowledgeInsightsConfig()
    logger.info("Configuration reloaded from environment")
    return _config_instance


def validate_environment() -> Dict[str, Any]:
    """
    Validate that all required environment variables are properly set.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "configuration": {}
    }
    
    config = get_config()
    
    # Check AI configuration
    if config.ai_enabled and not os.getenv("OPENAI_API_KEY"):
        results["warnings"].append("AI enabled but OPENAI_API_KEY not set")
        results["valid"] = False
    
    # Check for common misconfigurations
    if config.confidence_threshold == 1.0:
        results["warnings"].append("Confidence threshold set to 1.0 - may reject valid categorizations")
    
    if config.cache_ttl_seconds > 86400:  # More than 24 hours
        results["warnings"].append(f"Cache TTL very high: {config.cache_ttl_seconds}s (>24 hours)")
    
    if not config.fallback_categories:
        results["errors"].append("No fallback categories configured")
        results["valid"] = False
    
    # Add configuration summary
    results["configuration"] = config.to_dict()
    
    return results


# Export configuration for easy access
__all__ = [
    "KnowledgeInsightsConfig",
    "get_config",
    "reload_config",
    "validate_environment"
]