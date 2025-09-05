"""
🚨 SILENT FALLBACK DETECTOR - Emergency Service Health Monitoring
Detects when services are failing silently and falling back to degraded modes
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service health status levels"""
    HEALTHY = "healthy"           # Service working normally
    DEGRADED = "degraded"         # Service using fallbacks
    FAILING = "failing"           # Service experiencing errors
    CRITICAL = "critical"         # Service completely failed
    UNKNOWN = "unknown"           # Status cannot be determined

class ServiceHealthCheck:
    """Health check for a specific service"""
    
    def __init__(self, service_name: str, check_function: Callable, 
                 critical: bool = False, timeout: int = 5):
        self.service_name = service_name
        self.check_function = check_function
        self.critical = critical
        self.timeout = timeout
        self.last_check = None
        self.last_status = ServiceStatus.UNKNOWN
        self.failure_count = 0
        self.fallback_count = 0
        self.success_count = 0
        self.error_messages = []
    
    async def check(self) -> Dict[str, Any]:
        """Run health check for this service"""
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_function(),
                timeout=self.timeout
            )
            
            self.last_check = datetime.now()
            
            # Analyze result
            if result.get('status') == 'healthy':
                self.last_status = ServiceStatus.HEALTHY
                self.success_count += 1
                self.failure_count = 0  # Reset on success
            elif result.get('using_fallback'):
                self.last_status = ServiceStatus.DEGRADED
                self.fallback_count += 1
            elif result.get('error'):
                self.last_status = ServiceStatus.FAILING
                self.failure_count += 1
                self.error_messages.append(result.get('error'))
            
            return {
                'service': self.service_name,
                'status': self.last_status.value,
                'critical': self.critical,
                'details': result,
                'metrics': {
                    'success_count': self.success_count,
                    'failure_count': self.failure_count,
                    'fallback_count': self.fallback_count
                }
            }
            
        except asyncio.TimeoutError:
            self.failure_count += 1
            self.last_status = ServiceStatus.CRITICAL
            return {
                'service': self.service_name,
                'status': ServiceStatus.CRITICAL.value,
                'critical': self.critical,
                'error': f'Health check timed out after {self.timeout}s'
            }
        except Exception as e:
            self.failure_count += 1
            self.last_status = ServiceStatus.FAILING
            self.error_messages.append(str(e))
            return {
                'service': self.service_name,
                'status': ServiceStatus.FAILING.value,
                'critical': self.critical,
                'error': str(e)
            }

class SilentFallbackDetector:
    """
    Monitors services for silent failures and fallback usage
    """
    
    def __init__(self):
        """Initialize the fallback detector"""
        self.health_checks: Dict[str, ServiceHealthCheck] = {}
        self.monitoring_enabled = True
        self.alert_callbacks: List[Callable] = []
        self.fallback_thresholds = {
            'warning': 5,   # Warn after 5 fallbacks
            'critical': 10   # Critical after 10 fallbacks
        }
        
        logger.info("🔍 Silent Fallback Detector initialized")
    
    def register_health_check(self, service_name: str, check_function: Callable, 
                             critical: bool = False, timeout: int = 5):
        """
        Register a health check for a service
        
        Args:
            service_name: Name of the service
            check_function: Async function that returns health status
            critical: Whether this is a critical service
            timeout: Timeout for health check in seconds
        """
        self.health_checks[service_name] = ServiceHealthCheck(
            service_name, check_function, critical, timeout
        )
        logger.info(f"📋 Registered health check for {service_name}")
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Run health checks for all registered services"""
        results = {}
        critical_failures = []
        degraded_services = []
        
        for service_name, health_check in self.health_checks.items():
            result = await health_check.check()
            results[service_name] = result
            
            # Track critical issues
            if result['status'] == ServiceStatus.CRITICAL.value and result.get('critical'):
                critical_failures.append(service_name)
            elif result['status'] == ServiceStatus.DEGRADED.value:
                degraded_services.append(service_name)
        
        # Calculate overall health
        total_services = len(self.health_checks)
        healthy_count = sum(1 for r in results.values() 
                           if r['status'] == ServiceStatus.HEALTHY.value)
        
        overall_health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status(results),
            'total_services': total_services,
            'healthy_services': healthy_count,
            'degraded_services': len(degraded_services),
            'critical_failures': len(critical_failures),
            'health_percentage': (healthy_count / total_services * 100) if total_services > 0 else 0,
            'services': results,
            'alerts': []
        }
        
        # Generate alerts
        if critical_failures:
            alert = {
                'level': 'CRITICAL',
                'message': f"Critical services failing: {', '.join(critical_failures)}",
                'services': critical_failures,
                'timestamp': datetime.now().isoformat()
            }
            overall_health['alerts'].append(alert)
            await self._send_alert(alert)
        
        if degraded_services:
            alert = {
                'level': 'WARNING',
                'message': f"Services using fallbacks: {', '.join(degraded_services)}",
                'services': degraded_services,
                'timestamp': datetime.now().isoformat()
            }
            overall_health['alerts'].append(alert)
            
            # Check fallback thresholds
            for service in degraded_services:
                fallback_count = results[service]['metrics'].get('fallback_count', 0)
                if fallback_count >= self.fallback_thresholds['critical']:
                    critical_alert = {
                        'level': 'CRITICAL',
                        'message': f"{service} has been using fallbacks {fallback_count} times",
                        'service': service,
                        'fallback_count': fallback_count,
                        'timestamp': datetime.now().isoformat()
                    }
                    overall_health['alerts'].append(critical_alert)
                    await self._send_alert(critical_alert)
        
        return overall_health
    
    def _calculate_overall_status(self, results: Dict[str, Any]) -> str:
        """Calculate overall system status based on service health"""
        statuses = [r['status'] for r in results.values()]
        
        if any(s == ServiceStatus.CRITICAL.value for s in statuses):
            return ServiceStatus.CRITICAL.value
        elif any(s == ServiceStatus.FAILING.value for s in statuses):
            return ServiceStatus.FAILING.value
        elif any(s == ServiceStatus.DEGRADED.value for s in statuses):
            return ServiceStatus.DEGRADED.value
        elif all(s == ServiceStatus.HEALTHY.value for s in statuses):
            return ServiceStatus.HEALTHY.value
        else:
            return ServiceStatus.UNKNOWN.value
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via callback: {e}")
    
    async def monitor_continuously(self, interval: int = 60):
        """
        Continuously monitor services
        
        Args:
            interval: Check interval in seconds
        """
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        
        while self.monitoring_enabled:
            try:
                health_status = await self.check_all_services()
                
                # Log health status
                if health_status['overall_status'] == ServiceStatus.HEALTHY.value:
                    logger.info(f"✅ System healthy: {health_status['health_percentage']:.1f}% services operational")
                elif health_status['overall_status'] == ServiceStatus.DEGRADED.value:
                    logger.warning(f"⚠️ System degraded: {health_status['degraded_services']} services using fallbacks")
                else:
                    logger.error(f"🚨 System critical: {health_status['critical_failures']} critical failures")
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval)

# Global instance
fallback_detector = SilentFallbackDetector()

# Convenience function to create service health checks
async def check_ai_service_health() -> Dict[str, Any]:
    """Check if AI services are actually working or using fallbacks"""
    try:
        # Test AI call
        from utils.openai_client_factory import get_async_openai_client
        client = get_async_openai_client()
        
        # Simple test prompt
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with 'OK'"}],
            max_tokens=10,
            temperature=0
        )
        
        if response.choices[0].message.content:
            return {'status': 'healthy', 'using_fallback': False}
        else:
            return {'status': 'degraded', 'using_fallback': True, 
                   'reason': 'Empty response from AI'}
            
    except Exception as e:
        # Check if this is a fallback scenario
        error_msg = str(e).lower()
        if 'fallback' in error_msg or 'mock' in error_msg:
            return {'status': 'degraded', 'using_fallback': True, 
                   'error': 'AI service using fallback mode'}
        else:
            return {'status': 'failing', 'error': str(e)}

async def check_database_health() -> Dict[str, Any]:
    """Check if database is accessible"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Simple query to test connection
        response = supabase.table('workspaces').select('id').limit(1).execute()
        
        if response:
            return {'status': 'healthy', 'using_fallback': False}
        else:
            return {'status': 'degraded', 'using_fallback': True}
            
    except Exception as e:
        return {'status': 'failing', 'error': str(e)}

async def check_memory_service_health() -> Dict[str, Any]:
    """Check if memory service is working"""
    try:
        from services.unified_memory_engine import unified_memory_engine
        
        # Test memory operation
        test_id = await unified_memory_engine.store_context(
            workspace_id='test-health-check',
            context_type='health_check',
            content={'test': 'data'},
            importance_score=0.1
        )
        
        if test_id:
            return {'status': 'healthy', 'using_fallback': False}
        else:
            return {'status': 'degraded', 'using_fallback': True,
                   'reason': 'Memory storage returned empty ID'}
            
    except Exception as e:
        return {'status': 'failing', 'error': str(e)}

# Register default health checks
fallback_detector.register_health_check('ai_service', check_ai_service_health, critical=True)
fallback_detector.register_health_check('database', check_database_health, critical=True)
fallback_detector.register_health_check('memory_engine', check_memory_service_health, critical=False)