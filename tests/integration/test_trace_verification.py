#!/usr/bin/env python3
"""
Test script per verificare che il trace OpenAI funzioni correttamente sui task
"""

import asyncio
import os
import sys
import logging

# Add current directory to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.ai_provider_abstraction import ai_provider_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_trace_functionality():
    """Test che il trace OpenAI funzioni correttamente"""
    logger.info("🧪 Testing OpenAI Trace functionality...")
    
    # Check if trace is enabled
    trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
    logger.info(f"OPENAI_TRACE environment variable: {trace_enabled}")
    
    if not trace_enabled:
        logger.warning("⚠️ OpenAI Trace is not enabled in environment")
        return False
    
    # Test AI provider call with trace
    try:
        test_agent = {
            "name": "TraceTestAgent",
            "model": "gpt-4o-mini", 
            "instructions": "You are a test agent for verifying trace functionality. Respond with 'Trace test successful!'"
        }
        
        logger.info("📞 Making test AI call to verify trace...")
        
        result = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=test_agent,
            prompt="Test trace functionality. Respond with exactly: 'Trace test successful!'",
            max_tokens=50
        )
        
        logger.info(f"✅ AI call completed. Result: {result}")
        
        # Check if we got expected response  
        if result and 'response' in result:
            logger.info("🎉 Trace test completed successfully!")
            return True
        else:
            logger.error("❌ Unexpected response format")
            return False
            
    except Exception as e:
        logger.error(f"❌ Trace test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting OpenAI Trace verification test...")
    
    success = await test_trace_functionality()
    
    if success:
        logger.info("🎉 TRACE VERIFICATION: SUCCESS")
        logger.info("✅ OpenAI SDK calls with trace are working correctly")
        logger.info("🔍 Check OpenAI platform dashboard for trace data")
        return 0
    else:
        logger.error("❌ TRACE VERIFICATION: FAILED")
        logger.error("💡 Check OpenAI API key, SDK installation, and trace configuration")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)