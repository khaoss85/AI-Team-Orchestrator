#!/usr/bin/env python3
"""
Test the AI Content Display Transformation system
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_transformation_service():
    """Test the AI Content Display Transformer service directly"""
    try:
        logger.info("\n" + "="*60)
        logger.info("🧪 TESTING AI CONTENT DISPLAY TRANSFORMER SERVICE")
        logger.info("="*60)
        
        from services.ai_content_display_transformer import transform_deliverable_to_html
        
        # Test content samples
        test_cases = [
            {
                "name": "Email Template",
                "content": {
                    "subject": "Welcome to Our Platform",
                    "body": "Dear [Customer Name],\n\nWe're excited to have you join our community!",
                    "sender": "team@company.com"
                }
            },
            {
                "name": "Contact List",
                "content": {
                    "contacts": [
                        {"name": "John Doe", "email": "john@example.com", "role": "CEO"},
                        {"name": "Jane Smith", "email": "jane@example.com", "role": "CTO"}
                    ]
                }
            },
            {
                "name": "Strategy Document",
                "content": {
                    "title": "Q1 Marketing Strategy",
                    "goals": ["Increase brand awareness", "Generate 100 leads"],
                    "tactics": ["Social media campaign", "Email marketing", "Content creation"]
                }
            }
        ]
        
        business_context = {
            "company_name": "Test Company",
            "industry": "Technology",
            "workspace_name": "Marketing Workspace"
        }
        
        for test_case in test_cases:
            logger.info(f"\n📝 Testing: {test_case['name']}")
            logger.info(f"Input content: {json.dumps(test_case['content'], indent=2)[:200]}...")
            
            try:
                result = await transform_deliverable_to_html(
                    test_case['content'],
                    business_context
                )
                
                if result:
                    logger.info(f"✅ Transformation successful!")
                    logger.info(f"   - Format: {result.display_format}")
                    logger.info(f"   - Confidence: {result.transformation_confidence}%")
                    logger.info(f"   - Processing time: {result.processing_time:.2f}s")
                    logger.info(f"   - Fallback used: {result.fallback_used}")
                    logger.info(f"   - Output preview: {result.transformed_content[:200]}...")
                else:
                    logger.error(f"❌ Transformation returned None")
                    
            except Exception as e:
                logger.error(f"❌ Transformation failed: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ TRANSFORMATION SERVICE TEST COMPLETE")
        logger.info("="*60)
        
    except ImportError as e:
        logger.error(f"❌ Failed to import AI Content Display Transformer: {e}")
        logger.error("Make sure the service file exists at: backend/services/ai_content_display_transformer.py")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

async def test_api_endpoints():
    """Test the deliverables API endpoints with transformation"""
    try:
        logger.info("\n" + "="*60)
        logger.info("🌐 TESTING DELIVERABLES API ENDPOINTS")
        logger.info("="*60)
        
        import httpx
        
        # Get a workspace ID for testing
        from database import supabase
        workspaces_result = supabase.table('workspaces').select('id').limit(1).execute()
        
        if not workspaces_result.data:
            logger.warning("No workspaces found for testing")
            return
        
        workspace_id = workspaces_result.data[0]['id']
        logger.info(f"Using workspace ID: {workspace_id}")
        
        # Test the API endpoint
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:8000/api/deliverables/workspace/{workspace_id}"
            logger.info(f"Testing endpoint: {url}")
            
            try:
                response = await client.get(url, timeout=30.0)
                
                if response.status_code == 200:
                    deliverables = response.json()
                    logger.info(f"✅ API returned {len(deliverables)} deliverables")
                    
                    # Check for display_content in deliverables
                    with_display = 0
                    without_display = 0
                    
                    for deliverable in deliverables:
                        if deliverable.get('display_content'):
                            with_display += 1
                            logger.info(f"✅ Deliverable {deliverable.get('id')}: HAS display_content")
                            logger.info(f"   - Format: {deliverable.get('display_format')}")
                            logger.info(f"   - Quality: {deliverable.get('display_quality_score', 0) * 100:.1f}%")
                        else:
                            without_display += 1
                            logger.warning(f"⚠️ Deliverable {deliverable.get('id')}: NO display_content")
                    
                    logger.info(f"\n📊 Summary:")
                    logger.info(f"   - With display content: {with_display}")
                    logger.info(f"   - Without display content: {without_display}")
                    
                    if with_display > 0:
                        logger.info(f"✅ SUCCESS: {with_display} deliverables have enhanced display content!")
                    else:
                        logger.warning("⚠️ No deliverables have display content yet")
                        
                else:
                    logger.error(f"❌ API returned status {response.status_code}: {response.text}")
                    
            except httpx.TimeoutException:
                logger.error("❌ API request timed out (30s)")
            except httpx.ConnectError:
                logger.error("❌ Could not connect to API. Make sure the backend is running on port 8000")
            except Exception as e:
                logger.error(f"❌ API test failed: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ API ENDPOINT TEST COMPLETE")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ API test failed: {e}")
        raise

async def main():
    """Run all tests"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--api':
        # Test API endpoints only
        await test_api_endpoints()
    elif len(sys.argv) > 1 and sys.argv[1] == '--service':
        # Test transformation service only
        await test_transformation_service()
    else:
        # Run all tests
        logger.info("🚀 Starting AI Content Display Transformation Tests")
        
        # Test the transformation service
        await test_transformation_service()
        
        # Test the API endpoints
        await test_api_endpoints()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 ALL TESTS COMPLETE")
        logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())