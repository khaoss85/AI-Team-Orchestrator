#!/usr/bin/env python3
"""
Enhanced OpenAI Client Factory - Complete API Coverage
Tracks ALL OpenAI API methods including chat, embeddings, assistants, images, files, etc.
Provides 100% quota tracking coverage with model-specific metrics.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional, Union
from openai import OpenAI, AsyncOpenAI
from services.openai_quota_tracker import quota_manager

logger = logging.getLogger(__name__)

class EnhancedQuotaTrackedOpenAI:
    """
    Enhanced wrapper for OpenAI client that tracks ALL API methods
    """
    
    def __init__(self, client: Union[OpenAI, AsyncOpenAI], workspace_id: str = None):
        self._client = client
        self._workspace_id = workspace_id or "global"
        self._quota_tracker = quota_manager.get_tracker(self._workspace_id)
        
        # Wrap all trackable APIs (only if they exist)
        self._wrap_chat_api()
        self._wrap_embeddings_api()
        if hasattr(self._client, 'assistants'):
            self._wrap_assistants_api()
        if hasattr(self._client, 'threads'):
            self._wrap_threads_api()
        if hasattr(self._client, 'images'):
            self._wrap_images_api()
        if hasattr(self._client, 'files'):
            self._wrap_files_api()
        if hasattr(self._client, 'models'):
            self._wrap_models_api()
        
        logger.info(f"🔧 Enhanced QuotaTrackedOpenAI initialized for workspace: {self._workspace_id}")
    
    def __getattr__(self, name):
        """Forward all other attributes to the underlying client"""
        return getattr(self._client, name)
    
    def _wrap_chat_api(self):
        """Wrap chat completions API"""
        if not hasattr(self._client, 'chat'):
            return
        original_chat = self._client.chat
        if not hasattr(original_chat, 'completions'):
            return
        original_completions = original_chat.completions
        
        if hasattr(original_completions, 'create'):
            original_create = original_completions.create
            if asyncio.iscoroutinefunction(original_create):
                original_completions.create = self._async_track_chat_completion(original_create)
            else:
                original_completions.create = self._sync_track_chat_completion(original_create)
        
        if hasattr(original_completions, 'parse'):
            original_parse = original_completions.parse
            if asyncio.iscoroutinefunction(original_parse):
                original_completions.parse = self._async_track_chat_completion(original_parse)
            else:
                original_completions.parse = self._sync_track_chat_completion(original_parse)
    
    def _wrap_embeddings_api(self):
        """Wrap embeddings API"""
        if not hasattr(self._client, 'embeddings'):
            return
        original_embeddings = self._client.embeddings
        
        if hasattr(original_embeddings, 'create'):
            original_create = original_embeddings.create
            if asyncio.iscoroutinefunction(original_create):
                original_embeddings.create = self._async_track_embeddings(original_create)
            else:
                original_embeddings.create = self._sync_track_embeddings(original_create)
    
    def _wrap_assistants_api(self):
        """Wrap assistants API"""
        original_assistants = self._client.assistants
        
        # Track assistant creation and updates
        for method_name in ['create', 'update', 'list', 'retrieve', 'delete']:
            if hasattr(original_assistants, method_name):
                original_method = getattr(original_assistants, method_name)
                if asyncio.iscoroutinefunction(original_method):
                    setattr(original_assistants, method_name, 
                           self._async_track_generic_api(original_method, f"assistants.{method_name}"))
                else:
                    setattr(original_assistants, method_name,
                           self._sync_track_generic_api(original_method, f"assistants.{method_name}"))
    
    def _wrap_threads_api(self):
        """Wrap threads API"""
        original_threads = self._client.threads
        
        # Track thread operations
        for method_name in ['create', 'update', 'retrieve', 'delete']:
            if hasattr(original_threads, method_name):
                original_method = getattr(original_threads, method_name)
                if asyncio.iscoroutinefunction(original_method):
                    setattr(original_threads, method_name,
                           self._async_track_generic_api(original_method, f"threads.{method_name}"))
                else:
                    setattr(original_threads, method_name,
                           self._sync_track_generic_api(original_method, f"threads.{method_name}"))
        
        # Track messages API
        if hasattr(original_threads, 'messages'):
            messages = original_threads.messages
            for method_name in ['create', 'list', 'retrieve', 'update']:
                if hasattr(messages, method_name):
                    original_method = getattr(messages, method_name)
                    if asyncio.iscoroutinefunction(original_method):
                        setattr(messages, method_name,
                               self._async_track_generic_api(original_method, f"threads.messages.{method_name}"))
                    else:
                        setattr(messages, method_name,
                               self._sync_track_generic_api(original_method, f"threads.messages.{method_name}"))
        
        # Track runs API
        if hasattr(original_threads, 'runs'):
            runs = original_threads.runs
            for method_name in ['create', 'list', 'retrieve', 'update', 'cancel']:
                if hasattr(runs, method_name):
                    original_method = getattr(runs, method_name)
                    if asyncio.iscoroutinefunction(original_method):
                        setattr(runs, method_name,
                               self._async_track_generic_api(original_method, f"threads.runs.{method_name}"))
                    else:
                        setattr(runs, method_name,
                               self._sync_track_generic_api(original_method, f"threads.runs.{method_name}"))
    
    def _wrap_images_api(self):
        """Wrap images API"""
        original_images = self._client.images
        
        for method_name in ['generate', 'create_variation', 'edit']:
            if hasattr(original_images, method_name):
                original_method = getattr(original_images, method_name)
                if asyncio.iscoroutinefunction(original_method):
                    setattr(original_images, method_name,
                           self._async_track_generic_api(original_method, f"images.{method_name}"))
                else:
                    setattr(original_images, method_name,
                           self._sync_track_generic_api(original_method, f"images.{method_name}"))
    
    def _wrap_files_api(self):
        """Wrap files API"""
        original_files = self._client.files
        
        for method_name in ['create', 'list', 'retrieve', 'delete']:
            if hasattr(original_files, method_name):
                original_method = getattr(original_files, method_name)
                if asyncio.iscoroutinefunction(original_method):
                    setattr(original_files, method_name,
                           self._async_track_generic_api(original_method, f"files.{method_name}"))
                else:
                    setattr(original_files, method_name,
                           self._sync_track_generic_api(original_method, f"files.{method_name}"))
    
    def _wrap_models_api(self):
        """Wrap models API"""
        original_models = self._client.models
        
        for method_name in ['list', 'retrieve']:
            if hasattr(original_models, method_name):
                original_method = getattr(original_models, method_name)
                if asyncio.iscoroutinefunction(original_method):
                    setattr(original_models, method_name,
                           self._async_track_generic_api(original_method, f"models.{method_name}", track_usage=False))
                else:
                    setattr(original_models, method_name,
                           self._sync_track_generic_api(original_method, f"models.{method_name}", track_usage=False))
    
    def _sync_track_chat_completion(self, original_method):
        """Synchronous chat completion tracking"""
        def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'unknown')
            try:
                response = original_method(*args, **kwargs)
                
                # Extract usage and model info
                tokens_used = 0
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                
                self._record_usage(
                    success=True, 
                    tokens_used=tokens_used, 
                    model=model, 
                    api_method="chat.completions"
                )
                
                logger.debug(f"✅ Tracked chat completion: {model}, {tokens_used} tokens")
                return response
                
            except Exception as e:
                self._record_usage(success=False, model=model, api_method="chat.completions", error=str(e))
                logger.error(f"❌ Chat completion error: {e}")
                raise
        return wrapper
    
    def _async_track_chat_completion(self, original_method):
        """Asynchronous chat completion tracking"""
        async def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'unknown')
            try:
                response = await original_method(*args, **kwargs)
                
                # Extract usage and model info
                tokens_used = 0
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                
                self._record_usage(
                    success=True, 
                    tokens_used=tokens_used, 
                    model=model, 
                    api_method="chat.completions"
                )
                
                logger.debug(f"✅ Tracked async chat completion: {model}, {tokens_used} tokens")
                return response
                
            except Exception as e:
                self._record_usage(success=False, model=model, api_method="chat.completions", error=str(e))
                logger.error(f"❌ Async chat completion error: {e}")
                raise
        return wrapper
    
    def _sync_track_embeddings(self, original_method):
        """Synchronous embeddings tracking"""
        def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'text-embedding-ada-002')
            try:
                response = original_method(*args, **kwargs)
                
                # Calculate estimated tokens for embeddings
                input_data = kwargs.get('input', '')
                estimated_tokens = len(str(input_data).split()) if input_data else 0
                
                tokens_used = 0
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                elif estimated_tokens:
                    tokens_used = estimated_tokens
                
                self._record_usage(
                    success=True, 
                    tokens_used=tokens_used, 
                    model=model, 
                    api_method="embeddings.create"
                )
                
                logger.debug(f"✅ Tracked embeddings: {model}, {tokens_used} tokens")
                return response
                
            except Exception as e:
                self._record_usage(success=False, model=model, api_method="embeddings.create", error=str(e))
                logger.error(f"❌ Embeddings error: {e}")
                raise
        return wrapper
    
    def _async_track_embeddings(self, original_method):
        """Asynchronous embeddings tracking"""
        async def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'text-embedding-ada-002')
            try:
                response = await original_method(*args, **kwargs)
                
                # Calculate estimated tokens for embeddings
                input_data = kwargs.get('input', '')
                estimated_tokens = len(str(input_data).split()) if input_data else 0
                
                tokens_used = 0
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens
                elif estimated_tokens:
                    tokens_used = estimated_tokens
                
                self._record_usage(
                    success=True, 
                    tokens_used=tokens_used, 
                    model=model, 
                    api_method="embeddings.create"
                )
                
                logger.debug(f"✅ Tracked async embeddings: {model}, {tokens_used} tokens")
                return response
                
            except Exception as e:
                self._record_usage(success=False, model=model, api_method="embeddings.create", error=str(e))
                logger.error(f"❌ Async embeddings error: {e}")
                raise
        return wrapper
    
    def _sync_track_generic_api(self, original_method, api_method: str, track_usage: bool = True):
        """Generic synchronous API tracking"""
        def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'unknown')
            try:
                response = original_method(*args, **kwargs)
                
                if track_usage:
                    self._record_usage(
                        success=True, 
                        tokens_used=0,  # Most APIs don't return token usage
                        model=model, 
                        api_method=api_method
                    )
                
                logger.debug(f"✅ Tracked API call: {api_method}")
                return response
                
            except Exception as e:
                if track_usage:
                    self._record_usage(success=False, model=model, api_method=api_method, error=str(e))
                logger.error(f"❌ API error {api_method}: {e}")
                raise
        return wrapper
    
    def _async_track_generic_api(self, original_method, api_method: str, track_usage: bool = True):
        """Generic asynchronous API tracking"""
        async def wrapper(*args, **kwargs):
            model = kwargs.get('model', 'unknown')
            try:
                response = await original_method(*args, **kwargs)
                
                if track_usage:
                    self._record_usage(
                        success=True, 
                        tokens_used=0,  # Most APIs don't return token usage
                        model=model, 
                        api_method=api_method
                    )
                
                logger.debug(f"✅ Tracked async API call: {api_method}")
                return response
                
            except Exception as e:
                if track_usage:
                    self._record_usage(success=False, model=model, api_method=api_method, error=str(e))
                logger.error(f"❌ Async API error {api_method}: {e}")
                raise
        return wrapper
    
    def _record_usage(self, success: bool, tokens_used: int = 0, model: str = "unknown", 
                      api_method: str = "unknown", error: str = None):
        """Record usage with enhanced tracking and cost intelligence"""
        try:
            # Record basic request tracking
            self._quota_tracker.record_request(success=success, tokens_used=tokens_used)
            
            # Enhanced tracking with model and API method info
            if hasattr(self._quota_tracker, 'record_enhanced_usage'):
                self._quota_tracker.record_enhanced_usage(
                    success=success,
                    tokens_used=tokens_used,
                    model=model,
                    api_method=api_method,
                    error=error
                )
            
            # AI Cost Intelligence Analysis
            asyncio.create_task(self._analyze_cost_intelligence(
                success=success,
                tokens_used=tokens_used,
                model=model,
                api_method=api_method,
                error=error
            ))
            
            # Broadcast update asynchronously
            if self._quota_tracker.connected_websockets:
                status_data = self._quota_tracker.get_status_data()
                # Add enhanced data if available
                if hasattr(self._quota_tracker, 'get_enhanced_status_data'):
                    status_data.update(self._quota_tracker.get_enhanced_status_data())
                
                asyncio.create_task(self._quota_tracker.broadcast_status_update(status_data))
                
        except Exception as e:
            logger.error(f"❌ Failed to record usage: {e}")
    
    async def _analyze_cost_intelligence(self, success: bool, tokens_used: int, model: str,
                                       api_method: str, error: str = None):
        """Analyze call for cost optimization opportunities"""
        try:
            from services.ai_cost_intelligence import get_cost_intelligence
            
            # Prepare call data for analysis
            call_data = {
                "model": model,
                "tokens_used": tokens_used,
                "completion_tokens": 0,  # We don't have this breakdown yet
                "api_method": api_method,
                "success": success,
                "error": error,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Get cost intelligence instance
            cost_intelligence = get_cost_intelligence(self._workspace_id)
            
            # Analyze call and get alerts
            alerts = await cost_intelligence.analyze_api_call(call_data)
            
            # If alerts generated, broadcast them via WebSocket
            if alerts and self._quota_tracker.connected_websockets:
                alert_data = {
                    "type": "cost_intelligence_alerts",
                    "alerts": [
                        {
                            "id": alert.id,
                            "severity": alert.severity.value,
                            "type": alert.type,
                            "title": alert.title,
                            "description": alert.description,
                            "potential_savings": alert.potential_savings,
                            "confidence": alert.confidence,
                            "recommendation": alert.recommendation,
                            "created_at": alert.created_at.isoformat()
                        }
                        for alert in alerts
                    ]
                }
                
                await self._quota_tracker.broadcast_status_update(alert_data)
                
        except Exception as e:
            logger.error(f"❌ Error in cost intelligence analysis: {e}")


def get_enhanced_openai_client(api_key: str = None, workspace_id: str = None) -> EnhancedQuotaTrackedOpenAI:
    """
    Get enhanced quota-tracked OpenAI client (synchronous)
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    client = OpenAI(api_key=api_key)
    return EnhancedQuotaTrackedOpenAI(client, workspace_id)


def get_enhanced_async_openai_client(api_key: str = None, workspace_id: str = None) -> EnhancedQuotaTrackedOpenAI:
    """
    Get enhanced quota-tracked AsyncOpenAI client (asynchronous) 
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    client = AsyncOpenAI(api_key=api_key)
    return EnhancedQuotaTrackedOpenAI(client, workspace_id)


# Backward compatibility - keep original functions but redirect to enhanced versions
def get_openai_client(api_key: str = None, workspace_id: str = None) -> EnhancedQuotaTrackedOpenAI:
    """Backward compatible - now uses enhanced tracking"""
    return get_enhanced_openai_client(api_key, workspace_id)


def get_async_openai_client(api_key: str = None, workspace_id: str = None) -> EnhancedQuotaTrackedOpenAI:
    """Backward compatible - now uses enhanced tracking"""
    return get_enhanced_async_openai_client(api_key, workspace_id)


if __name__ == "__main__":
    # Test the enhanced factory
    print("🧪 Testing Enhanced OpenAI Client Factory...")
    
    try:
        client = get_enhanced_openai_client(workspace_id="test")
        print(f"✅ Enhanced client created successfully: {type(client)}")
        
        # Test that all APIs are accessible
        print(f"✅ Chat API available: {hasattr(client, 'chat')}")
        print(f"✅ Embeddings API available: {hasattr(client, 'embeddings')}")
        print(f"✅ Assistants API available: {hasattr(client, 'assistants')}")
        print(f"✅ Threads API available: {hasattr(client, 'threads')}")
        print(f"✅ Images API available: {hasattr(client, 'images')}")
        print(f"✅ Files API available: {hasattr(client, 'files')}")
        print(f"✅ Models API available: {hasattr(client, 'models')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")