"""
API Rate Limiter - Gestisce rate limiting per chiamate API esterne
==================================================================
Implementa:
1. Token bucket algorithm per rate limiting
2. Exponential backoff per errori 429/529
3. Rate limiting per-provider (OpenAI, etc.)
4. Monitoraggio e logging delle chiamate
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Strategie di rate limiting disponibili"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"

@dataclass
class RateLimitConfig:
    """Configurazione per rate limiting"""
    provider: str
    requests_per_minute: int = 20
    requests_per_hour: int = 1000
    max_burst: int = 5
    retry_after_seconds: int = 60
    max_retries: int = 3
    exponential_base: float = 2.0
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET

class TokenBucket:
    """Implementazione del Token Bucket algorithm"""
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Token aggiunti per secondo
            capacity: Capacità massima del bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquisisce token dal bucket. Blocca se non ci sono token disponibili.
        
        Returns:
            float: Tempo di attesa in secondi (0 se token disponibili)
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Aggiungi nuovi token basati sul tempo trascorso
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0  # Nessuna attesa necessaria
            
            # Calcola quanto tempo aspettare per avere abbastanza token
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate
            
            # Aspetta il tempo necessario
            await asyncio.sleep(wait_time)
            
            # Aggiorna di nuovo dopo l'attesa
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            self.tokens -= tokens
            
            return wait_time

class APIRateLimiter:
    """
    Rate limiter principale per gestire chiamate API esterne
    """
    
    def __init__(self):
        self.configs: Dict[str, RateLimitConfig] = {}
        self.buckets: Dict[str, TokenBucket] = {}
        self.call_history: Dict[str, list] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_429_time: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
        # Configurazioni di default per provider comuni
        self._setup_default_configs()
        
        logger.info("🚦 API Rate Limiter initialized")
    
    def _setup_default_configs(self):
        """Configura rate limits di default per provider comuni"""
        # OpenAI GPT-4
        self.add_provider_config(RateLimitConfig(
            provider="openai_gpt4",
            requests_per_minute=40,  # Conservative per evitare 529
            requests_per_hour=2000,
            max_burst=10,
            retry_after_seconds=60,
            max_retries=3
        ))
        
        # OpenAI GPT-3.5
        self.add_provider_config(RateLimitConfig(
            provider="openai_gpt35",
            requests_per_minute=60,
            requests_per_hour=3500,
            max_burst=15,
            retry_after_seconds=30,
            max_retries=3
        ))
        
        # Generic fallback
        self.add_provider_config(RateLimitConfig(
            provider="default",
            requests_per_minute=30,
            requests_per_hour=1500,
            max_burst=5,
            retry_after_seconds=60,
            max_retries=3
        ))
    
    def add_provider_config(self, config: RateLimitConfig):
        """Aggiunge configurazione per un provider"""
        self.configs[config.provider] = config
        
        # Crea token bucket basato su requests per minuto
        tokens_per_second = config.requests_per_minute / 60.0
        self.buckets[config.provider] = TokenBucket(
            rate=tokens_per_second,
            capacity=config.max_burst
        )
        
        logger.info(f"Added rate limit config for {config.provider}: "
                   f"{config.requests_per_minute} req/min, "
                   f"burst: {config.max_burst}")
    
    async def acquire(self, provider: str = "default", priority: str = "normal") -> float:
        """
        Acquisisce il permesso di fare una chiamata API
        
        Args:
            provider: Nome del provider (es. "openai_gpt4")
            priority: Priorità della richiesta ("high", "normal", "low")
            
        Returns:
            float: Tempo di attesa in secondi
        """
        # Usa config di default se provider non configurato
        if provider not in self.configs:
            provider = "default"
        
        config = self.configs[provider]
        bucket = self.buckets[provider]
        
        # Verifica se siamo in cooldown per errore 429
        if provider in self.last_429_time:
            time_since_429 = time.time() - self.last_429_time[provider]
            if time_since_429 < config.retry_after_seconds:
                wait_time = config.retry_after_seconds - time_since_429
                logger.warning(f"⏳ Rate limit cooldown for {provider}: "
                              f"waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Acquisisce token dal bucket
        wait_time = await bucket.acquire()
        
        if wait_time > 0:
            logger.info(f"⏱️ Rate limit wait for {provider}: {wait_time:.1f}s")
        
        # Registra la chiamata
        async with self._lock:
            self.call_history[provider].append(time.time())
            # Mantieni solo le chiamate dell'ultima ora
            cutoff = time.time() - 3600
            self.call_history[provider] = [
                t for t in self.call_history[provider] if t > cutoff
            ]
        
        return wait_time
    
    async def handle_rate_limit_error(self, provider: str, error: Exception) -> float:
        """
        Gestisce errori di rate limiting (429/529)
        
        Returns:
            float: Tempo di attesa suggerito in secondi
        """
        config = self.configs.get(provider, self.configs["default"])
        
        async with self._lock:
            self.error_counts[provider] += 1
            self.last_429_time[provider] = time.time()
        
        # Calcola backoff esponenziale
        error_count = self.error_counts[provider]
        backoff_time = min(
            config.retry_after_seconds * (config.exponential_base ** (error_count - 1)),
            300  # Max 5 minuti
        )
        
        logger.error(f"🚫 Rate limit error for {provider} (attempt {error_count}): "
                    f"backing off {backoff_time:.1f}s")
        
        return backoff_time
    
    async def reset_error_count(self, provider: str):
        """Reset error count dopo successo"""
        async with self._lock:
            self.error_counts[provider] = 0
            if provider in self.last_429_time:
                del self.last_429_time[provider]
    
    def get_stats(self, provider: str = None) -> Dict[str, Any]:
        """Ottiene statistiche sulle chiamate"""
        if provider:
            providers = [provider] if provider in self.configs else []
        else:
            providers = list(self.configs.keys())
        
        stats = {}
        now = time.time()
        
        for p in providers:
            calls = self.call_history.get(p, [])
            calls_last_minute = len([t for t in calls if now - t < 60])
            calls_last_hour = len(calls)
            
            bucket = self.buckets.get(p)
            available_tokens = bucket.tokens if bucket else 0
            
            stats[p] = {
                "calls_last_minute": calls_last_minute,
                "calls_last_hour": calls_last_hour,
                "available_tokens": int(available_tokens),
                "error_count": self.error_counts.get(p, 0),
                "in_cooldown": p in self.last_429_time
            }
        
        return stats
    
    async def execute_with_rate_limit(
        self, 
        func: Callable, 
        provider: str = "default",
        priority: str = "normal",
        max_retries: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        Esegue una funzione con rate limiting e retry automatico
        
        Args:
            func: Funzione async da eseguire
            provider: Provider per rate limiting
            priority: Priorità della richiesta
            max_retries: Override del numero massimo di retry
            *args, **kwargs: Argomenti per la funzione
            
        Returns:
            Il risultato della funzione
        """
        config = self.configs.get(provider, self.configs["default"])
        retries = max_retries if max_retries is not None else config.max_retries
        
        for attempt in range(retries + 1):
            try:
                # Acquisisce permesso dal rate limiter
                await self.acquire(provider, priority)
                
                # Esegue la funzione
                result = await func(*args, **kwargs)
                
                # Reset error count su successo
                await self.reset_error_count(provider)
                
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Controlla se è un errore di rate limiting
                if any(code in error_str for code in ["429", "529", "rate_limit", "overloaded"]):
                    if attempt < retries:
                        wait_time = await self.handle_rate_limit_error(provider, e)
                        logger.warning(f"Rate limit hit for {provider}, "
                                     f"retry {attempt + 1}/{retries} "
                                     f"after {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {provider}")
                        raise
                else:
                    # Non è un errore di rate limiting, propaga
                    raise

# Singleton instance
api_rate_limiter = APIRateLimiter()

# Convenience functions
async def acquire_api_permit(provider: str = "default", priority: str = "normal") -> float:
    """Acquisisce permesso per chiamata API"""
    return await api_rate_limiter.acquire(provider, priority)

async def execute_with_rate_limit(func: Callable, provider: str = "default", *args, **kwargs):
    """Esegue funzione con rate limiting"""
    return await api_rate_limiter.execute_with_rate_limit(func, provider, *args, **kwargs)

def get_rate_limit_stats(provider: str = None) -> Dict[str, Any]:
    """Ottiene statistiche rate limiting"""
    return api_rate_limiter.get_stats(provider)