# utils/rate_limiter.py
"""
🚦 Intelligent Rate Limiter for OpenAI API calls
Prevents 429 errors and optimizes API usage

🚨 ENHANCED WITH COST CONTROLS: Integrates emergency cost protection
"""

import asyncio
import time
import logging
import os
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
        
        # 🚨 EMERGENCY COST CONTROLS: Load from environment
        max_calls_per_minute = int(os.getenv("MAX_AI_CALLS_PER_MINUTE", "5"))  # Conservative default
        ai_cooldown = int(os.getenv("AI_CALL_COOLDOWN_SECONDS", "12"))
        
        # Rate limits per function type (calls per minute) - REDUCED for cost control
        self.rate_limits = {
            "goal_extraction": max(2, max_calls_per_minute // 3),   # Very limited
            "quality_validation": max(1, max_calls_per_minute // 5), # Ultra limited  
            "semantic_matching": max(2, max_calls_per_minute // 2),  # Limited
            "recommendations": max(1, max_calls_per_minute // 5),    # Ultra limited
            "task_analysis": max(2, max_calls_per_minute // 3),      # Limited
            "content_learning": 0,  # 🚨 DISABLED during cost emergency
            "general": max_calls_per_minute
        }
        
        # Additional cost controls
        self.ai_cooldown_seconds = ai_cooldown
        self.daily_call_count = 0
        self.daily_budget_usd = float(os.getenv("DAILY_OPENAI_BUDGET", "5.0"))
        self.estimated_cost_per_call = 0.03  # Conservative estimate
        
        # Exponential backoff settings
        self.max_delay = 60.0  # Max 1 minute delay
        self.base_delay = 1.0  # Start with 1 second
        
    async def acquire(self, function_name: str = "general") -> bool:
        """
        Acquire permission to make an API call
        Returns True if call is allowed, False if should skip
        
        🚨 ENHANCED WITH BUDGET PROTECTION
        """
        # 🚨 EMERGENCY BUDGET CHECK: Stop if over daily budget
        estimated_daily_cost = self.daily_call_count * self.estimated_cost_per_call
        if estimated_daily_cost >= self.daily_budget_usd:
            logger.error(f"🚨 DAILY BUDGET EXCEEDED: ${estimated_daily_cost:.2f} >= ${self.daily_budget_usd:.2f}")
            return False
        
        current_time = time.time()
        calls_queue = self.function_calls[function_name]
        rate_limit = self.rate_limits.get(function_name, self.rate_limits["general"])
        
        # 🚨 CONTENT LEARNING EMERGENCY BLOCK
        if function_name == "content_learning":
            logger.warning(f"🚨 COST CONTROL: {function_name} calls blocked during emergency")
            return False
        
        # Remove calls older than 1 minute
        while calls_queue and calls_queue[0] < current_time - 60:
            calls_queue.popleft()
        
        # Check if we're within rate limit
        if len(calls_queue) < rate_limit:
            calls_queue.append(current_time)
            self.daily_call_count += 1
            
            # Apply mandatory cooldown between calls
            if self.ai_cooldown_seconds > 0:
                logger.info(f"⏳ Cost control cooldown: {self.ai_cooldown_seconds}s for {function_name}")
                await asyncio.sleep(self.ai_cooldown_seconds)
            
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