#!/usr/bin/env python3
"""
🧪 TEST QUALITY VALIDATOR

Test diretto del quality validator per vedere se il problema è nei dati o nel validator stesso.
"""

import asyncio
import logging
import sys
import os

# Setup path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(CURRENT_DIR, ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quality_validator():
    """Test quality validator con dati mock"""
    try:
        from ai_quality_assurance.quality_validator import AIQualityValidator
        quality_validator = AIQualityValidator()
        
        # Test 1: Asset ricco di contenuto (dovrebbe avere score alto)
        rich_asset_data = {
            "contact_list": [
                {
                    "name": "John Smith", 
                    "email": "john.smith@saas-company.com",
                    "company": "TechFlow SaaS",
                    "title": "CTO",
                    "linkedin": "https://linkedin.com/in/johnsmith",
                    "country": "Germany"
                },
                {
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@eurotech.com", 
                    "company": "EuroTech Solutions",
                    "title": "CMO",
                    "linkedin": "https://linkedin.com/in/sarahjohnson",
                    "country": "France"
                }
            ],
            "total_contacts": 2,
            "verification_date": "2025-06-26",
            "source": "LinkedIn research",
            "quality_notes": "All contacts verified for accuracy"
        }
        
        # Test 2: Asset povero di contenuto (dovrebbe avere score basso)
        poor_asset_data = {
            "message": "Unable to complete task",
            "reason": "No access to databases"
        }
        
        # Test 3: Asset vuoto (dovrebbe avere score 0)
        empty_asset_data = {}
        
        context = {
            "workspace_id": "test-workspace",
            "task_name": "Contact Research Test",
            "goal_type": "contact_gathering"
        }
        
        logger.info("🧪 Testing Quality Validator...")
        
        # Test 1: Rich content
        logger.info("📊 Test 1: Rich content asset")
        result1 = await quality_validator.validate_asset_quality(
            rich_asset_data, "contact_database", context
        )
        logger.info(f"✅ Rich content score: {result1.overall_score:.2f}")
        
        # Test 2: Poor content  
        logger.info("📊 Test 2: Poor content asset")
        result2 = await quality_validator.validate_asset_quality(
            poor_asset_data, "contact_database", context
        )
        logger.info(f"⚠️ Poor content score: {result2.overall_score:.2f}")
        
        # Test 3: Empty content
        logger.info("📊 Test 3: Empty content asset")
        result3 = await quality_validator.validate_asset_quality(
            empty_asset_data, "contact_database", context
        )
        logger.info(f"❌ Empty content score: {result3.overall_score:.2f}")
        
        # Summary
        logger.info("🎯 QUALITY VALIDATOR TEST SUMMARY")
        logger.info(f"Rich content: {result1.overall_score:.2f} (expected: >0.7)")
        logger.info(f"Poor content: {result2.overall_score:.2f} (expected: 0.3-0.6)")  
        logger.info(f"Empty content: {result3.overall_score:.2f} (expected: 0.0-0.2)")
        
        # Determine if validator is working correctly
        if result1.overall_score > result2.overall_score > result3.overall_score:
            logger.info("✅ Quality validator is working correctly!")
            return True
        else:
            logger.error("❌ Quality validator is not working correctly!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_quality_validator())
    sys.exit(0 if result else 1)