#!/usr/bin/env python3
"""
Test del Sistema con Rate Limiting
==================================
Testa il TaskExecutor con rate limiting implementato per verificare
che risolva i problemi di timeout da overload API.
"""

import asyncio
import time
import logging
from datetime import datetime
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('rate_limited_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RateLimitedSystemTest:
    """Test del sistema con rate limiting"""
    
    def __init__(self):
        self.test_id = str(uuid4())
        self.start_time = datetime.now()
        self.results = {}
        
    async def run_test(self):
        """Esegue test del sistema rate-limited"""
        logger.info("=" * 80)
        logger.info("🚦 TESTING RATE LIMITED SYSTEM")
        logger.info("=" * 80)
        
        try:
            # Test 1: Rate limiter availability
            await self._test_rate_limiter_availability()
            
            # Test 2: Rate limiter functionality
            await self._test_rate_limiter_functionality()
            
            # Test 3: Concurrent task execution with rate limiting
            await self._test_concurrent_execution()
            
            # Test 4: Error handling for rate limits
            await self._test_error_handling()
            
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    async def _test_rate_limiter_availability(self):
        """Test che il rate limiter sia disponibile"""
        logger.info("\n🔍 TEST 1: Rate Limiter Availability")
        logger.info("-" * 50)
        
        try:
            from services.api_rate_limiter import api_rate_limiter
            
            # Check if rate limiter is initialized
            configs = api_rate_limiter.configs
            logger.info(f"✅ Rate limiter loaded with {len(configs)} provider configs")
            
            # Log provider configurations
            for provider, config in configs.items():
                logger.info(f"  {provider}: {config.requests_per_minute} req/min, "
                           f"burst: {config.max_burst}")
            
            self.results["rate_limiter_available"] = True
            
        except ImportError as e:
            logger.error(f"❌ Rate limiter not available: {e}")
            self.results["rate_limiter_available"] = False
            raise
    
    async def _test_rate_limiter_functionality(self):
        """Test funzionalità base del rate limiter"""
        logger.info("\n⚙️ TEST 2: Rate Limiter Functionality")
        logger.info("-" * 50)
        
        from services.api_rate_limiter import api_rate_limiter
        
        # Test basic acquire
        start_time = time.time()
        wait_time = await api_rate_limiter.acquire("openai_gpt4", "high")
        elapsed = time.time() - start_time
        
        logger.info(f"✅ Basic acquire: wait_time={wait_time:.2f}s, elapsed={elapsed:.2f}s")
        
        # Test stats
        stats = api_rate_limiter.get_stats()
        logger.info(f"✅ Stats retrieved: {len(stats)} providers")
        
        # Test multiple acquisitions
        acquisition_times = []
        for i in range(5):
            start = time.time()
            await api_rate_limiter.acquire("openai_gpt35", "normal")
            elapsed = time.time() - start
            acquisition_times.append(elapsed)
        
        avg_time = sum(acquisition_times) / len(acquisition_times)
        logger.info(f"✅ Average acquisition time for 5 calls: {avg_time:.2f}s")
        
        self.results["rate_limiter_functionality"] = {
            "basic_acquire_time": elapsed,
            "average_acquisition_time": avg_time,
            "stats_available": len(stats) > 0
        }
    
    async def _test_concurrent_execution(self):
        """Test esecuzione concorrente con rate limiting"""
        logger.info("\n🔄 TEST 3: Concurrent Execution with Rate Limiting")
        logger.info("-" * 50)
        
        from services.api_rate_limiter import api_rate_limiter, execute_with_rate_limit
        
        # Simula una funzione che fa chiamate API
        async def mock_api_call(call_id: int, delay: float = 0.1):
            logger.info(f"  Mock API call {call_id} starting")
            await asyncio.sleep(delay)  # Simula processing
            logger.info(f"  Mock API call {call_id} completed")
            return f"result_{call_id}"
        
        # Test esecuzione concorrente
        start_time = time.time()
        
        # Lancia 8 chiamate concorrenti (più del limite di burst)
        tasks = []
        for i in range(8):
            task = execute_with_rate_limit(
                mock_api_call,
                provider="openai_gpt4",
                priority="normal",
                call_id=i,
                delay=0.1
            )
            tasks.append(task)
        
        # Esegui tutte le task concorrenti
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        logger.info(f"✅ Completed {len(results)} concurrent API calls in {total_time:.2f}s")
        
        # Verifica che ci sia stato rate limiting (dovrebbe prendere più tempo)
        expected_minimum_time = 1.0  # Con rate limiting dovrebbe essere più lento
        rate_limited = total_time > expected_minimum_time
        
        if rate_limited:
            logger.info(f"✅ Rate limiting detected: {total_time:.2f}s > {expected_minimum_time}s")
        else:
            logger.warning(f"⚠️ Rate limiting may not be working: {total_time:.2f}s")
        
        self.results["concurrent_execution"] = {
            "total_time": total_time,
            "calls_completed": len(results),
            "rate_limited": rate_limited
        }
    
    async def _test_error_handling(self):
        """Test gestione errori di rate limiting"""
        logger.info("\n🚫 TEST 4: Error Handling for Rate Limits")
        logger.info("-" * 50)
        
        from services.api_rate_limiter import api_rate_limiter
        
        # Simula errore 429
        async def mock_429_error():
            raise Exception("429 Too Many Requests")
        
        # Test gestione errore
        try:
            backoff_time = await api_rate_limiter.handle_rate_limit_error(
                "openai_gpt4", Exception("429 Too Many Requests")
            )
            logger.info(f"✅ Error handling: backoff_time={backoff_time:.2f}s")
            
            # Verifica che il provider sia in cooldown
            stats = api_rate_limiter.get_stats("openai_gpt4")
            in_cooldown = stats.get("openai_gpt4", {}).get("in_cooldown", False)
            
            if in_cooldown:
                logger.info("✅ Provider correctly marked as in cooldown")
            else:
                logger.warning("⚠️ Provider not marked as in cooldown")
            
            self.results["error_handling"] = {
                "backoff_time": backoff_time,
                "in_cooldown": in_cooldown
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.results["error_handling"] = {"error": str(e)}
    
    def _generate_report(self):
        """Genera report dei test"""
        logger.info("\n📊 GENERATING TEST REPORT")
        logger.info("-" * 50)
        
        # Calcola metriche
        all_tests_passed = all(
            not isinstance(result, dict) or "error" not in result 
            for result in self.results.values()
        )
        
        report = {
            "test_id": self.test_id,
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "status": "PASSED" if all_tests_passed else "FAILED",
            "results": self.results,
            "summary": {
                "rate_limiter_available": self.results.get("rate_limiter_available", False),
                "functionality_works": "rate_limiter_functionality" in self.results,
                "concurrent_execution_works": "concurrent_execution" in self.results,
                "error_handling_works": "error_handling" in self.results
            }
        }
        
        # Log summary
        logger.info(f"📈 Test Summary:")
        logger.info(f"  Status: {report['status']}")
        logger.info(f"  Duration: {report['duration']:.2f}s")
        logger.info(f"  Tests Passed: {len([r for r in self.results.values() if not isinstance(r, dict) or 'error' not in r])}/{len(self.results)}")
        
        return report

async def main():
    """Esegue il test del sistema rate-limited"""
    test = RateLimitedSystemTest()
    result = await test.run_test()
    
    print("\n" + "=" * 80)
    print("🎯 RATE LIMITED SYSTEM TEST COMPLETE")
    print("=" * 80)
    print(f"Status: {result['status']}")
    
    if result['status'] == 'FAILED':
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())