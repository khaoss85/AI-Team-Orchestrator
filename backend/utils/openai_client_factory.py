"""
Centralized OpenAI Client Factory
Ensures all OpenAI clients throughout the system use quota tracking

CRITICAL: This factory MUST be used for ALL OpenAI client instantiations to ensure
proper quota tracking. Direct OpenAI() or AsyncOpenAI() instantiation bypasses
quota tracking and is the root cause of the 0/10000 tracking issue.
"""

import os
import logging
from typing import Optional
from openai import OpenAI, AsyncOpenAI
from functools import wraps

# Import quota tracker for real API monitoring
from services.openai_quota_tracker import quota_tracker

logger = logging.getLogger(__name__)

# Singleton instances to avoid creating multiple clients
_sync_client: Optional[OpenAI] = None
_async_client: Optional[AsyncOpenAI] = None


class QuotaTrackedOpenAI(OpenAI):
    """
    Wrapper for OpenAI client that automatically tracks quota usage.
    Intercepts all API calls to record quota metrics.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_chat_completions_create = self.chat.completions.create
        self._original_beta_chat_completions_parse = self.beta.chat.completions.parse
        self._wrap_methods()
        logger.info("📊 QuotaTrackedOpenAI initialized - ALL calls will be tracked")
    
    def _wrap_methods(self):
        """Wrap OpenAI methods with quota tracking"""
        # Wrap standard chat completions
        def tracked_chat_create(*args, **kwargs):
            try:
                result = self._original_chat_completions_create(*args, **kwargs)
                # Record successful request with token usage
                tokens_used = 0
                if hasattr(result, 'usage') and result.usage:
                    tokens_used = result.usage.total_tokens
                quota_tracker.record_request(success=True, tokens_used=tokens_used)
                logger.debug(f"✅ QUOTA TRACKED: Sync chat completion - {tokens_used} tokens")
                return result
            except Exception as e:
                # Record failed request
                quota_tracker.record_openai_error(str(type(e).__name__), str(e))
                logger.error(f"❌ QUOTA TRACKED: Sync chat completion error: {e}")
                raise
        
        # Wrap beta parse (structured outputs)
        def tracked_beta_parse(*args, **kwargs):
            try:
                result = self._original_beta_chat_completions_parse(*args, **kwargs)
                # Record successful request with token usage
                tokens_used = 0
                if hasattr(result, 'usage') and result.usage:
                    tokens_used = result.usage.total_tokens
                quota_tracker.record_request(success=True, tokens_used=tokens_used)
                logger.debug(f"✅ QUOTA TRACKED: Sync beta parse - {tokens_used} tokens")
                return result
            except Exception as e:
                # Record failed request
                quota_tracker.record_openai_error(str(type(e).__name__), str(e))
                logger.error(f"❌ QUOTA TRACKED: Sync beta parse error: {e}")
                raise
        
        self.chat.completions.create = tracked_chat_create
        self.beta.chat.completions.parse = tracked_beta_parse


class QuotaTrackedAsyncOpenAI(AsyncOpenAI):
    """
    Wrapper for AsyncOpenAI client that automatically tracks quota usage.
    Intercepts all async API calls to record quota metrics.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_chat_completions_create = self.chat.completions.create
        self._original_beta_chat_completions_parse = self.beta.chat.completions.parse
        self._wrap_methods()
        logger.info("📊 QuotaTrackedAsyncOpenAI initialized - ALL async calls will be tracked")
    
    def _wrap_methods(self):
        """Wrap AsyncOpenAI methods with quota tracking"""
        # Wrap async chat completions
        @wraps(self._original_chat_completions_create)
        async def tracked_async_chat_create(*args, **kwargs):
            try:
                result = await self._original_chat_completions_create(*args, **kwargs)
                # Record successful request with token usage
                tokens_used = 0
                if hasattr(result, 'usage') and result.usage:
                    tokens_used = result.usage.total_tokens
                quota_tracker.record_request(success=True, tokens_used=tokens_used)
                logger.debug(f"✅ QUOTA TRACKED: Async chat completion - {tokens_used} tokens")
                return result
            except Exception as e:
                # Record failed request
                quota_tracker.record_openai_error(str(type(e).__name__), str(e))
                logger.error(f"❌ QUOTA TRACKED: Async chat completion error: {e}")
                raise
        
        # Wrap async beta parse (structured outputs)
        @wraps(self._original_beta_chat_completions_parse)
        async def tracked_async_beta_parse(*args, **kwargs):
            try:
                result = await self._original_beta_chat_completions_parse(*args, **kwargs)
                # Record successful request with token usage
                tokens_used = 0
                if hasattr(result, 'usage') and result.usage:
                    tokens_used = result.usage.total_tokens
                quota_tracker.record_request(success=True, tokens_used=tokens_used)
                logger.debug(f"✅ QUOTA TRACKED: Async beta parse - {tokens_used} tokens")
                return result
            except Exception as e:
                # Record failed request
                quota_tracker.record_openai_error(str(type(e).__name__), str(e))
                logger.error(f"❌ QUOTA TRACKED: Async beta parse error: {e}")
                raise
        
        self.chat.completions.create = tracked_async_chat_create
        self.beta.chat.completions.parse = tracked_async_beta_parse


def get_openai_client() -> OpenAI:
    """
    Get singleton synchronous OpenAI client with quota tracking.
    
    Returns:
        QuotaTrackedOpenAI: Quota-tracked synchronous OpenAI client
    """
    global _sync_client
    if _sync_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _sync_client = QuotaTrackedOpenAI(api_key=api_key)
        logger.info("📊 Created singleton QuotaTrackedOpenAI client")
    return _sync_client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Get singleton asynchronous OpenAI client with quota tracking.
    
    Returns:
        QuotaTrackedAsyncOpenAI: Quota-tracked asynchronous OpenAI client
    """
    global _async_client
    if _async_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _async_client = QuotaTrackedAsyncOpenAI(api_key=api_key)
        logger.info("📊 Created singleton QuotaTrackedAsyncOpenAI client")
    return _async_client


# Export convenience functions for backward compatibility
def create_openai_client() -> OpenAI:
    """
    Create a new OpenAI client with quota tracking.
    Prefer get_openai_client() for singleton pattern.
    
    Returns:
        QuotaTrackedOpenAI: New quota-tracked synchronous OpenAI client
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return QuotaTrackedOpenAI(api_key=api_key)


def create_async_openai_client() -> AsyncOpenAI:
    """
    Create a new AsyncOpenAI client with quota tracking.
    Prefer get_async_openai_client() for singleton pattern.
    
    Returns:
        QuotaTrackedAsyncOpenAI: New quota-tracked asynchronous OpenAI client
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return QuotaTrackedAsyncOpenAI(api_key=api_key)


# Log warning if this module is imported
logger.warning("""
🚨 CRITICAL: OpenAI Client Factory Loaded
=========================================
ALL OpenAI clients MUST use this factory to ensure quota tracking.
Direct instantiation of OpenAI() or AsyncOpenAI() bypasses quota tracking!

Replace:
    from openai import OpenAI
    client = OpenAI()

With:
    from utils.openai_client_factory import get_openai_client
    client = get_openai_client()

This is REQUIRED for proper quota monitoring and cost management.
=========================================
""")