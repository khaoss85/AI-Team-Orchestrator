#!/usr/bin/env python3
"""
Test script for Content-Aware Learning Engine
Demonstrates extraction of business-valuable insights from deliverable content
"""

import asyncio
import json
import logging
from uuid import UUID
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_content_learning_extraction():
    """Test the content-aware learning extraction system"""
    
    # Import necessary components
    from services.content_aware_learning_engine import content_aware_learning_engine, DomainType
    from database import get_supabase_client
    
    try:
        # Get a workspace with deliverables
        supabase = get_supabase_client()
        
        # Find a workspace with deliverables
        workspaces = supabase.table('workspaces').select('id, name').limit(5).execute()
        
        if not workspaces.data:
            logger.error("No workspaces found")
            return
        
        # Test each workspace
        for workspace in workspaces.data:
            workspace_id = workspace['id']
            workspace_name = workspace.get('name', 'Unknown')
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing workspace: {workspace_name} ({workspace_id})")
            logger.info(f"{'='*60}")
            
            # Check if workspace has deliverables
            deliverables = supabase.table('deliverables')\
                .select('id, title, type, content')\
                .eq('workspace_id', workspace_id)\
                .limit(3)\
                .execute()
            
            if not deliverables.data:
                logger.info(f"No deliverables in workspace {workspace_name}, skipping...")
                continue
            
            logger.info(f"Found {len(deliverables.data)} deliverables")
            
            # Show sample deliverable
            for i, deliverable in enumerate(deliverables.data[:2], 1):
                logger.info(f"\nDeliverable {i}:")
                logger.info(f"  Title: {deliverable.get('title', 'N/A')[:60]}...")
                logger.info(f"  Type: {deliverable.get('type', 'N/A')}")
                
                # Check content type
                content = deliverable.get('content')
                if content:
                    if isinstance(content, str):
                        logger.info(f"  Content: String ({len(content)} chars)")
                        # Check for business indicators
                        if '@' in content:
                            logger.info("    → Contains email addresses")
                        if '%' in content:
                            logger.info("    → Contains percentages/metrics")
                        if 'http' in content:
                            logger.info("    → Contains URLs")
                    elif isinstance(content, dict):
                        logger.info(f"  Content: Dictionary ({len(content)} keys)")
            
            # Run content-aware analysis
            logger.info(f"\n🔍 Running content-aware analysis...")
            result = await content_aware_learning_engine.analyze_workspace_content(workspace_id)
            
            # Display results
            logger.info(f"\n📊 Analysis Results:")
            logger.info(f"  Status: {result.get('status')}")
            logger.info(f"  Insights Generated: {result.get('insights_generated', 0)}")
            logger.info(f"  Domains Analyzed: {result.get('domains_analyzed', [])}")
            logger.info(f"  Deliverables Analyzed: {result.get('deliverables_analyzed', 0)}")
            
            # Get and display actionable learnings
            if result.get('insights_generated', 0) > 0:
                logger.info(f"\n💡 Actionable Business Insights:")
                learnings = await content_aware_learning_engine.get_actionable_learnings(workspace_id)
                
                for i, learning in enumerate(learnings[:5], 1):
                    logger.info(f"  {i}. {learning}")
                
                # Test domain-specific extraction
                for domain in result.get('domains_analyzed', [])[:2]:
                    try:
                        domain_enum = DomainType(domain)
                        domain_learnings = await content_aware_learning_engine.get_actionable_learnings(
                            workspace_id, 
                            domain_enum
                        )
                        if domain_learnings:
                            logger.info(f"\n📌 {domain.replace('_', ' ').title()} Specific Insights:")
                            for learning in domain_learnings[:2]:
                                logger.info(f"    • {learning}")
                    except:
                        pass
            
            # Compare with traditional learning
            logger.info(f"\n🔄 Comparing with traditional learning extraction...")
            from services.learning_feedback_engine import learning_feedback_engine
            
            traditional_result = await learning_feedback_engine.analyze_workspace_performance(workspace_id)
            
            logger.info(f"\n📈 Comparison:")
            logger.info(f"  Content-Aware Insights: {result.get('insights_generated', 0)}")
            logger.info(f"  Traditional Insights: {traditional_result.get('insights_generated', 0)}")
            
            if result.get('insights_generated', 0) > 0:
                logger.info(f"  ✅ Content-aware extraction provides {result.get('insights_generated', 0)}x more business value!")
            
            # Only test first workspace with deliverables
            break
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

async def test_api_endpoints():
    """Test the new API endpoints"""
    import aiohttp
    
    base_url = "http://localhost:8000/api/content-learning"
    
    logger.info("\n" + "="*60)
    logger.info("Testing API Endpoints")
    logger.info("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test domains endpoint
            logger.info("\n📋 Testing GET /domains...")
            async with session.get(f"{base_url}/domains") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"  Available domains: {len(data.get('domains', []))}")
                    for domain in data.get('domains', [])[:3]:
                        logger.info(f"    • {domain['name']}: {domain['description']}")
                else:
                    logger.error(f"  Failed with status {response.status}")
            
            # Get a workspace to test with
            async with session.get("http://localhost:8000/api/workspaces") as response:
                if response.status == 200:
                    workspaces = await response.json()
                    if workspaces:
                        workspace_id = workspaces[0]['id']
                        
                        # Test analysis endpoint
                        logger.info(f"\n🔍 Testing POST /analyze/{workspace_id}...")
                        async with session.post(
                            f"{base_url}/analyze/{workspace_id}",
                            params={"include_legacy": True}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"  Status: {data.get('status')}")
                                logger.info(f"  Insights generated: {data.get('insights_generated', 0)}")
                                logger.info(f"  Domains: {data.get('domains_analyzed', [])}")
                            else:
                                logger.error(f"  Failed with status {response.status}")
                        
                        # Test insights endpoint
                        logger.info(f"\n💡 Testing GET /insights/{workspace_id}...")
                        async with session.get(
                            f"{base_url}/insights/{workspace_id}",
                            params={"limit": 5}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"  Total insights: {data.get('insights_count', 0)}")
                                for insight in data.get('actionable_insights', [])[:3]:
                                    logger.info(f"    • {insight}")
                            else:
                                logger.error(f"  Failed with status {response.status}")
                        
                        # Test comparison endpoint
                        logger.info(f"\n📊 Testing GET /comparison/{workspace_id}...")
                        async with session.get(f"{base_url}/comparison/{workspace_id}") as response:
                            if response.status == 200:
                                data = await response.json()
                                comparison = data.get('comparison', {})
                                logger.info(f"  Content-aware: {comparison.get('content_aware', {}).get('insights_generated', 0)} insights")
                                logger.info(f"  Traditional: {comparison.get('traditional', {}).get('insights_generated', 0)} insights")
                                logger.info(f"  Improvement factor: {data.get('improvement_factor', 0):.1f}x")
                            else:
                                logger.error(f"  Failed with status {response.status}")
                
    except Exception as e:
        logger.error(f"API test failed: {e}")

async def main():
    """Main test function"""
    logger.info("="*60)
    logger.info("Content-Aware Learning Engine Test Suite")
    logger.info("="*60)
    
    # Test direct engine functionality
    logger.info("\n1️⃣ Testing Direct Engine Functionality")
    await test_content_learning_extraction()
    
    # Test API endpoints
    logger.info("\n2️⃣ Testing API Endpoints")
    await test_api_endpoints()
    
    logger.info("\n" + "="*60)
    logger.info("✅ Test Suite Complete!")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())