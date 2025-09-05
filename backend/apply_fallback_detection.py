#!/usr/bin/env python3
"""
Apply silent fallback detection to monitor service health
"""

import logging
import asyncio
import json
from typing import Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_fallback_detection():
    """Apply fallback detection to prevent silent failures"""
    
    print("""
    🔍 APPLYING SILENT FALLBACK DETECTION
    =====================================
    
    This script enables monitoring for:
    1. Services failing silently
    2. Fallback mode usage
    3. Degraded functionality
    4. Critical service failures
    """)
    
    try:
        # Import fallback detector
        from services.silent_fallback_detector import fallback_detector, ServiceStatus
        
        print("✅ Silent Fallback Detector loaded")
        
        # Register alert callback for user notification
        async def user_alert_callback(alert: Dict[str, Any]):
            """Print alerts to user"""
            level = alert.get('level', 'INFO')
            message = alert.get('message', 'Unknown alert')
            
            if level == 'CRITICAL':
                print(f"\n🚨 CRITICAL ALERT: {message}")
            elif level == 'WARNING':
                print(f"\n⚠️ WARNING: {message}")
            else:
                print(f"\nℹ️ INFO: {message}")
        
        fallback_detector.register_alert_callback(user_alert_callback)
        
        print("\n🔍 Running system health check...")
        
        # Run health check
        health_status = await fallback_detector.check_all_services()
        
        # Display results
        print(f"\n📊 SYSTEM HEALTH STATUS")
        print(f"{'='*50}")
        print(f"Overall Status: {health_status['overall_status'].upper()}")
        print(f"Health Score: {health_status['health_percentage']:.1f}%")
        print(f"Total Services: {health_status['total_services']}")
        print(f"Healthy: {health_status['healthy_services']}")
        print(f"Degraded: {health_status['degraded_services']}")
        print(f"Critical: {health_status['critical_failures']}")
        
        print(f"\n📋 SERVICE DETAILS:")
        for service_name, details in health_status['services'].items():
            status = details['status']
            critical = "CRITICAL" if details.get('critical') else "Normal"
            
            # Use emoji based on status
            if status == 'healthy':
                emoji = "✅"
            elif status == 'degraded':
                emoji = "⚠️"
            elif status == 'failing':
                emoji = "❌"
            else:
                emoji = "🚨"
            
            print(f"\n  {emoji} {service_name}:")
            print(f"     Status: {status}")
            print(f"     Priority: {critical}")
            
            if 'error' in details:
                print(f"     Error: {details['error'][:100]}...")
            
            if 'metrics' in details:
                metrics = details['metrics']
                print(f"     Success: {metrics.get('success_count', 0)}")
                print(f"     Failures: {metrics.get('failure_count', 0)}")
                print(f"     Fallbacks: {metrics.get('fallback_count', 0)}")
        
        # Check for alerts
        if health_status['alerts']:
            print(f"\n⚠️ ACTIVE ALERTS:")
            for alert in health_status['alerts']:
                print(f"  - [{alert['level']}] {alert['message']}")
        
        # Provide recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if health_status['overall_status'] == ServiceStatus.CRITICAL.value:
            print("""
  🚨 CRITICAL ISSUES DETECTED:
  1. Check OpenAI API key and quota
  2. Verify database connection
  3. Review error logs for details
  4. Consider restarting services
            """)
        elif health_status['overall_status'] == ServiceStatus.DEGRADED.value:
            print("""
  ⚠️ SYSTEM RUNNING IN DEGRADED MODE:
  1. Some services using fallbacks
  2. Functionality may be limited
  3. Monitor for escalation to critical
  4. Apply pending fixes
            """)
        elif health_status['overall_status'] == ServiceStatus.HEALTHY.value:
            print("""
  ✅ SYSTEM HEALTHY:
  All services operational
  No fallback usage detected
  Continue normal operations
            """)
        
        # Test specific service calls to verify detection
        print(f"\n🧪 Testing service execution detection...")
        
        # Test 1: Check if AI Goal Matcher works
        try:
            from services.ai_goal_matcher import AIGoalMatcher
            
            # Mock test
            result = await AIGoalMatcher.match_deliverable_to_goal(
                deliverable_content={'test': 'content'},
                deliverable_title='Test Deliverable',
                goals=[{'id': 'test-goal', 'description': 'Test Goal'}]
            )
            
            if result and result.success:
                print("  ✅ AI Goal Matcher: WORKING")
            else:
                print("  ⚠️ AI Goal Matcher: USING FALLBACK")
                
        except Exception as e:
            print(f"  ❌ AI Goal Matcher: FAILED - {str(e)[:50]}...")
        
        # Test 2: Check if Display Transformer works
        try:
            from services.ai_content_display_transformer import transform_deliverable_to_html
            
            result = await transform_deliverable_to_html(
                content={'test': 'data'},
                business_context={'company': 'Test Corp'}
            )
            
            if result and not result.fallback_used:
                print("  ✅ Display Transformer: WORKING")
            else:
                print("  ⚠️ Display Transformer: USING FALLBACK")
                
        except Exception as e:
            print(f"  ❌ Display Transformer: FAILED - {str(e)[:50]}...")
        
        print(f"""
        
        ✅ FALLBACK DETECTION CONFIGURED
        =================================
        
        Monitoring is now active for:
        - Silent service failures
        - Fallback mode usage
        - Performance degradation
        - Critical errors
        
        The system will:
        - Alert on critical failures
        - Track fallback usage
        - Monitor service health
        - Provide diagnostic information
        
        Next Steps:
        1. Review service status above
        2. Address any critical issues
        3. Monitor fallback usage patterns
        4. Apply fixes for failing services
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fallback detection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(apply_fallback_detection())
    exit(0 if success else 1)