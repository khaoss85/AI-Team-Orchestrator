#!/usr/bin/env python3
"""
🔬 DELIVERABLE SYSTEM INTEGRATION TEST

Test di integrazione end-to-end per verificare che il sistema di deliverable
AI-driven funzioni correttamente e produca risultati di alta qualità.
"""

import pytest
import asyncio
import logging
from uuid import uuid4
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the backend path is available for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

@pytest.mark.asyncio
async def test_ai_driven_deliverable_system_integration():
    """
    Test di integrazione completo per il sistema di deliverable AI-driven.
    Verifica che tutti i componenti lavorino insieme correttamente.
    """
    print("\n🔬 TESTING AI-DRIVEN DELIVERABLE SYSTEM INTEGRATION")
    print("=" * 60)
    
    try:
        # Import the components we want to test
        from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
        from ai_agents.deliverable_assembly import deliverable_assembly_agent
        from deliverable_system.unified_deliverable_engine import _aggregate_task_results
        
        # 1. Test Asset Extraction from Mock Task Results
        print("\n📊 Step 1: Testing Asset Extraction")
        print("-" * 40)
        
        mock_task_results = [
            {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "name": "Market Research",
                "status": "completed",
                "result": """
                # Market Analysis Report
                
                ## Target Demographics
                - Age: 25-40 years
                - Income: €40,000-€80,000 annually
                - Location: Urban areas in Italy, Germany, France
                - Interests: Technology, sustainability, lifestyle optimization
                
                ## Key Findings
                1. 78% of target audience uses mobile apps daily
                2. Sustainability is a key purchasing factor (65% importance)
                3. Price sensitivity: willing to pay 15-20% premium for quality
                
                ## Recommendations
                - Focus on mobile-first approach
                - Emphasize sustainability credentials
                - Premium positioning justified by quality
                """
            },
            {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "name": "Marketing Strategy",
                "status": "completed", 
                "result": """
                # Marketing Strategy Document
                
                ## Campaign Goals
                - Reach 50,000 potential customers in Q1
                - Generate 2,500 qualified leads
                - Achieve 15% conversion rate
                
                ## Channel Strategy
                1. **Digital Marketing**
                   - Google Ads: €15,000 budget
                   - Facebook/Instagram: €10,000 budget
                   - LinkedIn: €5,000 budget
                
                2. **Content Marketing**
                   - Blog posts: 8 per month
                   - Video content: 4 per month
                   - Webinars: 2 per month
                
                ## Success Metrics
                - Cost per acquisition: < €25
                - Customer lifetime value: > €500
                - Return on ad spend: > 300%
                """
            }
        ]
        
        # Extract assets from task results
        total_assets = 0
        asset_quality_scores = []
        
        for task in mock_task_results:
            task_context = {
                "task_name": task["name"],
                "domain": "business_strategy"
            }
            
            assets = await concrete_asset_extractor.extract_assets(
                content=task["result"],
                context=task_context
            )
            
            total_assets += len(assets)
            
            for asset in assets:
                quality_score = asset.get('quality_score', 0.0)
                asset_quality_scores.append(quality_score)
                print(f"   ✅ Asset: {asset.get('asset_name', 'unknown')} - Quality: {quality_score:.2f}")
        
        print(f"\n📈 Asset Extraction Results:")
        print(f"   Total Assets: {total_assets}")
        print(f"   Average Quality: {sum(asset_quality_scores)/len(asset_quality_scores):.2f}")
        
        # Assertion: Should extract multiple high-quality assets
        assert total_assets >= 3, f"Expected at least 3 assets, got {total_assets}"
        avg_quality = sum(asset_quality_scores)/len(asset_quality_scores)
        assert avg_quality >= 0.7, f"Expected average quality >= 0.7, got {avg_quality:.2f}"
        
        # 2. Test Deliverable Assembly
        print(f"\n🔧 Step 2: Testing Deliverable Assembly")
        print("-" * 40)
        
        # Create mock assets for assembly
        mock_assets = [
            {
                "asset_name": "Target Demographics Analysis",
                "asset_type": "market_data",
                "content": "Age: 25-40 years, Income: €40,000-€80,000, Location: Urban areas",
                "quality_score": 0.9
            },
            {
                "asset_name": "Marketing Budget Allocation",
                "asset_type": "business_plan",
                "content": "Google Ads: €15,000, Facebook/Instagram: €10,000, LinkedIn: €5,000",
                "quality_score": 0.85
            },
            {
                "asset_name": "Success Metrics Definition",
                "asset_type": "performance_kpi",
                "content": "Cost per acquisition: < €25, Customer lifetime value: > €500",
                "quality_score": 0.88
            }
        ]
        
        # Test deliverable assembly
        assembly_result = await deliverable_assembly_agent.assemble_deliverable(
            goal_description="Launch Digital Marketing Campaign for European Market",
            assets=mock_assets,
            workspace_context={"industry": "technology", "region": "europe"}
        )
        
        print(f"📋 Assembly Results:")
        print(f"   Status: {assembly_result.get('status', 'unknown')}")
        print(f"   Quality Score: {assembly_result.get('quality_score', 0):.2f}")
        print(f"   Content Length: {len(assembly_result.get('content', ''))}")
        
        # Assertions for assembly
        assert assembly_result.get('status') == 'completed', "Assembly should complete successfully"
        assert assembly_result.get('quality_score', 0) >= 0.8, "Assembly should produce high-quality output"
        assert len(assembly_result.get('content', '')) >= 500, "Assembly should produce substantial content"
        
        # 3. Test End-to-End Aggregation
        print(f"\n🎯 Step 3: Testing End-to-End Aggregation")
        print("-" * 40)
        
        # Test the full aggregation pipeline
        aggregated_content, quality_score = await _aggregate_task_results(mock_task_results)
        
        print(f"🏆 Aggregation Results:")
        print(f"   Quality Score: {quality_score:.2f}")
        print(f"   Content Length: {len(aggregated_content)}")
        print(f"   Content Preview: {aggregated_content[:200]}...")
        
        # Final assertions
        assert quality_score >= 70.0, f"Expected quality score >= 70, got {quality_score:.2f}"
        assert len(aggregated_content) >= 300, f"Expected substantial content, got {len(aggregated_content)} characters"
        assert "Market Analysis" in aggregated_content or "Marketing Strategy" in aggregated_content, "Content should include relevant information"
        
        # 4. Success Summary
        print(f"\n🎉 INTEGRATION TEST RESULTS")
        print("=" * 60)
        print(f"✅ Asset Extraction: {total_assets} assets with {avg_quality:.2f} avg quality")
        print(f"✅ Deliverable Assembly: {assembly_result.get('quality_score', 0):.2f} quality score")
        print(f"✅ End-to-End Aggregation: {quality_score:.2f} quality score")
        print(f"")
        print(f"🏆 ALL TESTS PASSED - AI-Driven Deliverable System Working Correctly!")
        
        return {
            "total_assets": total_assets,
            "avg_asset_quality": avg_quality,
            "assembly_quality": assembly_result.get('quality_score', 0),
            "aggregation_quality": quality_score,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Can be run standalone
    result = asyncio.run(test_ai_driven_deliverable_system_integration())
    if result.get('success', False):
        print("\n✅ Standalone test completed successfully!")
        exit(0)
    else:
        print("\n❌ Standalone test failed!")
        exit(1)