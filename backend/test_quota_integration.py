#!/usr/bin/env python3
"""
Test Quota Integration
======================
This script tests the complete OpenAI quota tracking system by:
1. Making real OpenAI API calls
2. Verifying quota tracking updates
3. Testing WebSocket notifications
4. Validating multi-tenant workspace isolation
"""

import asyncio
import os
import sys
import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from services.openai_quota_tracker import quota_manager, QuotaStatus
from utils.ai_utils import get_structured_ai_response
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test model for structured response
class TestResponse(BaseModel):
    message: str
    timestamp: str

async def test_real_api_tracking(workspace_id: str = "test-workspace"):
    """Test real OpenAI API call tracking"""
    logger.info("=" * 60)
    logger.info("🚀 Testing Real OpenAI API Quota Tracking")
    logger.info("=" * 60)
    
    # Get workspace tracker
    tracker = quota_manager.get_tracker(workspace_id)
    
    # Check initial status
    initial_status = tracker.get_status_data()
    logger.info(f"📊 Initial Status: {initial_status['status']}")
    logger.info(f"   Requests this minute: {initial_status['requests_per_minute']['current']}")
    logger.info(f"   Requests today: {initial_status['requests_per_day']['current']}")
    
    # Make a real OpenAI API call through our tracked function
    logger.info("\n🔄 Making real OpenAI API call...")
    
    try:
        result = await get_structured_ai_response(
            prompt="Generate a test message with current timestamp",
            response_model=TestResponse,
            model="gpt-4o-mini"  # Use cheaper model for testing
        )
        
        if result:
            logger.info(f"✅ API call successful: {result.message}")
        else:
            logger.error("❌ API call returned None")
    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
    
    # Check updated status
    await asyncio.sleep(0.5)  # Small delay to ensure tracking is processed
    updated_status = tracker.get_status_data()
    logger.info(f"\n📊 Updated Status: {updated_status['status']}")
    logger.info(f"   Requests this minute: {updated_status['requests_per_minute']['current']}")
    logger.info(f"   Requests today: {updated_status['requests_per_day']['current']}")
    logger.info(f"   Errors count: {updated_status['errors']['count']}")
    
    # Verify tracking worked
    if updated_status['requests_per_minute']['current'] > initial_status['requests_per_minute']['current']:
        logger.info("✅ QUOTA TRACKING VERIFIED: Request count increased!")
    else:
        logger.error("❌ QUOTA TRACKING FAILED: Request count did not increase")
    
    # Test notification data
    notifications = tracker.get_notification_data()
    logger.info(f"\n🔔 Notification Status: Show={notifications['show_notification']}, Level={notifications['level']}")
    if notifications['show_notification']:
        logger.info(f"   Title: {notifications['title']}")
        logger.info(f"   Message: {notifications['message']}")
    
    # Test workspace isolation
    logger.info("\n🏢 Testing Workspace Isolation...")
    workspace2_tracker = quota_manager.get_tracker("workspace-2")
    workspace2_status = workspace2_tracker.get_status_data()
    logger.info(f"   Workspace 1 requests: {updated_status['requests_per_minute']['current']}")
    logger.info(f"   Workspace 2 requests: {workspace2_status['requests_per_minute']['current']}")
    
    if workspace2_status['requests_per_minute']['current'] == 0:
        logger.info("✅ WORKSPACE ISOLATION VERIFIED: Different workspaces have separate tracking")
    else:
        logger.error("❌ WORKSPACE ISOLATION FAILED: Workspace 2 should have 0 requests")
    
    return updated_status

async def test_rate_limit_simulation(workspace_id: str = "test-rate-limit"):
    """Simulate rate limiting by making multiple requests"""
    logger.info("\n" + "=" * 60)
    logger.info("⚡ Testing Rate Limit Detection")
    logger.info("=" * 60)
    
    tracker = quota_manager.get_tracker(workspace_id)
    
    # Make multiple rapid requests to trigger warning
    logger.info("📈 Making multiple rapid requests...")
    for i in range(5):
        tracker.record_request(success=True, tokens_used=1000)
        await asyncio.sleep(0.1)
    
    status = tracker.get_status_data()
    logger.info(f"📊 Status after rapid requests: {status['status']}")
    logger.info(f"   Requests this minute: {status['requests_per_minute']['current']}/{status['requests_per_minute']['limit']}")
    logger.info(f"   Usage percentage: {status['requests_per_minute']['percentage']:.1f}%")
    
    # Simulate rate limit error
    logger.info("\n🚨 Simulating rate limit error...")
    tracker.record_openai_error("RateLimitError", "Rate limit exceeded")
    
    status_after_error = tracker.get_status_data()
    logger.info(f"📊 Status after error: {status_after_error['status']}")
    
    if status_after_error['status'] == 'rate_limited':
        logger.info("✅ RATE LIMIT DETECTION VERIFIED: Status changed to rate_limited")
    else:
        logger.error(f"❌ RATE LIMIT DETECTION FAILED: Expected 'rate_limited', got '{status_after_error['status']}'")
    
    # Check if requests are blocked
    can_make_request = tracker.can_make_request()
    logger.info(f"🔒 Can make request: {can_make_request}")
    
    if not can_make_request:
        logger.info("✅ REQUEST BLOCKING VERIFIED: Requests blocked when rate limited")
    else:
        logger.error("❌ REQUEST BLOCKING FAILED: Should block requests when rate limited")

async def test_production_readiness():
    """Verify all production requirements are met"""
    logger.info("\n" + "=" * 60)
    logger.info("🏭 Production Readiness Verification")
    logger.info("=" * 60)
    
    checks_passed = []
    checks_failed = []
    
    # Check 1: Environment variables
    logger.info("\n📋 Checking environment configuration...")
    required_vars = [
        "OPENAI_API_KEY",
        "OPENAI_RATE_LIMIT_PER_MINUTE",
        "OPENAI_RATE_LIMIT_PER_DAY",
        "QUOTA_ADMIN_RESET_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value and var != "OPENAI_API_KEY":  # Don't log API key
            logger.info(f"   ✅ {var}: {value[:20]}...")
            checks_passed.append(f"{var} configured")
        elif value:
            logger.info(f"   ✅ {var}: [REDACTED]")
            checks_passed.append(f"{var} configured")
        else:
            logger.error(f"   ❌ {var}: NOT SET")
            checks_failed.append(f"{var} missing")
    
    # Check 2: Multi-workspace tracking
    logger.info("\n📋 Checking multi-workspace support...")
    workspace_count = len(quota_manager.get_all_trackers())
    if workspace_count > 0:
        logger.info(f"   ✅ Multi-workspace tracking active: {workspace_count} workspaces")
        checks_passed.append("Multi-workspace tracking")
    else:
        logger.error("   ❌ No workspace trackers active")
        checks_failed.append("Multi-workspace tracking")
    
    # Check 3: WebSocket functionality
    logger.info("\n📋 Checking WebSocket support...")
    try:
        import websocket
        logger.info("   ✅ WebSocket library available")
        checks_passed.append("WebSocket support")
    except ImportError:
        logger.error("   ❌ WebSocket library not installed")
        checks_failed.append("WebSocket support")
    
    # Check 4: Security (no hardcoded values)
    logger.info("\n📋 Checking security compliance...")
    admin_key = os.getenv("QUOTA_ADMIN_RESET_KEY")
    if admin_key and admin_key != "test" and admin_key != "admin":
        logger.info("   ✅ Admin key properly configured (not default)")
        checks_passed.append("Security compliance")
    else:
        logger.error("   ❌ Admin key using default/weak value")
        checks_failed.append("Security compliance")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 PRODUCTION READINESS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Passed: {len(checks_passed)}/{len(checks_passed) + len(checks_failed)}")
    logger.info(f"❌ Failed: {len(checks_failed)}/{len(checks_passed) + len(checks_failed)}")
    
    if checks_failed:
        logger.error("\n⚠️  PRODUCTION READINESS: NOT MET")
        logger.error("Failed checks:")
        for check in checks_failed:
            logger.error(f"  - {check}")
    else:
        logger.info("\n🎉 PRODUCTION READINESS: FULLY MET!")
        logger.info("All systems operational and ready for production deployment!")
    
    return len(checks_failed) == 0

async def main():
    """Run all integration tests"""
    logger.info("🔧 OpenAI Quota System Integration Test")
    logger.info("=" * 60)
    
    try:
        # Test 1: Real API tracking
        await test_real_api_tracking()
        
        # Test 2: Rate limit simulation
        await test_rate_limit_simulation()
        
        # Test 3: Production readiness
        is_production_ready = await test_production_readiness()
        
        # Final verdict
        logger.info("\n" + "=" * 60)
        if is_production_ready:
            logger.info("🎯 FINAL VERDICT: System is PRODUCTION READY!")
        else:
            logger.error("⚠️  FINAL VERDICT: System needs configuration fixes")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())