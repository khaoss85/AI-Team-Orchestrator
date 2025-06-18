# utils/rate_limiter.py
"""
🚦 Intelligent Rate Limiter for OpenAI API calls
Prevents 429 errors and optimizes API usage
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenAIRateLimiter:
    """Smart rate limiter for OpenAI API calls"""
    
    def __init__(self):
        # Track calls per function
        self.function_calls = defaultdict(deque)
        self.function_delays = defaultdict(float)
        
        # Rate limits per function type (calls per minute)
        self.rate_limits = {
            "goal_extraction": 10,  # Lower priority
            "quality_validation": 5,  # Medium priority  
            "semantic_matching": 8,  # Medium priority
            "recommendations": 3,   # Lower priority
            "task_analysis": 6,     # Medium priority
            "general": 15           # Default limit
        }
        
        # Exponential backoff settings
        self.max_delay = 60.0  # Max 1 minute delay
        self.base_delay = 1.0  # Start with 1 second
        
    async def acquire(self, function_name: str = "general") -> bool:
        """
        Acquire permission to make an API call
        Returns True if call is allowed, False if should skip
        """
        current_time = time.time()
        calls_queue = self.function_calls[function_name]
        rate_limit = self.rate_limits.get(function_name, self.rate_limits["general"])
        
        # Remove calls older than 1 minute
        while calls_queue and calls_queue[0] < current_time - 60:
            calls_queue.popleft()
        
        # Check if we're within rate limit
        if len(calls_queue) < rate_limit:
            calls_queue.append(current_time)
            return True
        
        # Calculate delay needed
        oldest_call = calls_queue[0]
        delay_needed = 60 - (current_time - oldest_call)
        
        if delay_needed > 0:
            logger.warning(f"🚦 Rate limit reached for {function_name}, waiting {delay_needed:.1f}s")
            await asyncio.sleep(delay_needed)
            
        calls_queue.append(time.time())
        return True
    
    def record_429_error(self, function_name: str):
        """Record a 429 error and increase delay"""
        current_delay = self.function_delays[function_name]
        new_delay = min(self.max_delay, max(self.base_delay, current_delay * 2))
        self.function_delays[function_name] = new_delay
        
        logger.warning(f"🚫 429 error for {function_name}, increasing delay to {new_delay}s")
    
    def record_success(self, function_name: str):
        """Record a successful call"""
        if self.function_delays[function_name] > 0:
            # Gradually reduce delay on success
            self.function_delays[function_name] *= 0.8
            if self.function_delays[function_name] < self.base_delay:
                self.function_delays[function_name] = 0
    
    async def get_delay_for_function(self, function_name: str) -> float:
        """Get current delay for a function"""
        return self.function_delays[function_name]

# Global rate limiter instance
openai_rate_limiter = OpenAIRateLimiter()

def rate_limited_openai_call(function_name: str = "general"):
    """Decorator for rate-limited OpenAI calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Acquire rate limit permission
            await openai_rate_limiter.acquire(function_name)
            
            # Apply any additional delay
            delay = await openai_rate_limiter.get_delay_for_function(function_name)
            if delay > 0:
                logger.info(f"⏳ Applying {delay:.1f}s delay for {function_name}")
                await asyncio.sleep(delay)
            
            try:
                result = await func(*args, **kwargs)
                openai_rate_limiter.record_success(function_name)
                return result
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    openai_rate_limiter.record_429_error(function_name)
                raise
        
        return wrapper
    return decorator

# Utility functions for common patterns
async def safe_openai_call(client, function_name: str, *args, **kwargs):
    """Make a safe OpenAI call with rate limiting"""
    await openai_rate_limiter.acquire(function_name)
    
    delay = await openai_rate_limiter.get_delay_for_function(function_name)
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        result = await client.chat.completions.create(*args, **kwargs)
        openai_rate_limiter.record_success(function_name)
        return result
    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            openai_rate_limiter.record_429_error(function_name)
        raise