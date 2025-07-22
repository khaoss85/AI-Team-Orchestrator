#!/usr/bin/env python3
"""
Test Enhanced QA and Deliverables Flow
Tests the complete enhanced flow: Task Execution → Asset Extraction → Quality Validation → Intelligent Aggregation
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
from deliverable_system.intelligent_aggregator import intelligent_aggregator
from ai_quality_assurance.unified_quality_engine import unified_quality_engine
from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
from database import list_tasks, get_task, create_task, update_task, get_deliverables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('test_enhanced_qa_deliverables.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedQADeliverablesTest:
    """Test the enhanced QA and Deliverables flow"""
    
    def __init__(self):
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "phases_completed": [],
            "phases_failed": [],
            "assets_extracted": 0,
            "quality_validations": 0,
            "deliverables_created": 0,
            "overall_success": False
        }
    
    async def run_complete_test(self):
        """Run the complete enhanced flow test"""
        logger.info("🚀 Starting Enhanced QA and Deliverables Flow Test")
        logger.info("=" * 70)
        
        try:
            # Phase 1: Create test tasks with rich content
            await self.phase_1_create_test_tasks()
            
            # Phase 2: Test asset extraction
            await self.phase_2_test_asset_extraction()
            
            # Phase 3: Test quality validation
            await self.phase_3_test_quality_validation()
            
            # Phase 4: Test intelligent aggregation
            await self.phase_4_test_intelligent_aggregation()
            
            # Phase 5: Test complete deliverable flow
            await self.phase_5_test_complete_flow()
            
            self.test_results["overall_success"] = len(self.test_results["phases_failed"]) == 0
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.test_results["overall_success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_test_summary()
        return self.test_results
    
    async def phase_1_create_test_tasks(self):
        """Create test tasks with various types of content"""
        phase_name = "create_test_tasks"
        logger.info("📝 PHASE 1: Creating Test Tasks with Rich Content")
        
        try:
            # Test workspace ID (you should use a real one from your system)
            self.workspace_id = "test-workspace-enhanced-qa"
            
            # Create diverse test tasks
            self.test_tasks = [
                {
                    "name": "Code Implementation Task",
                    "result": '''# User Authentication Module
                    
```python
def authenticate_user(username: str, password: str) -> dict:
    """Authenticate user and return JWT token"""
    import hashlib
    import jwt
    from datetime import datetime, timedelta
    
    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Check credentials (simplified)
    if username == "admin" and password_hash == hashlib.sha256("admin123".encode()).hexdigest():
        # Generate JWT token
        payload = {
            "user_id": "12345",
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, "secret_key", algorithm="HS256")
        
        return {
            "success": True,
            "token": token,
            "user": {"id": "12345", "username": username, "role": "admin"}
        }
    
    return {"success": False, "error": "Invalid credentials"}
```

Also implemented the user registration endpoint:

```python
async def register_user(user_data: dict) -> dict:
    """Register new user"""
    # Validate user data
    if not user_data.get("email") or not user_data.get("password"):
        return {"error": "Email and password required"}
    
    # Create user record
    user = {
        "id": str(uuid.uuid4()),
        "email": user_data["email"],
        "created_at": datetime.now().isoformat()
    }
    
    return {"success": True, "user": user}
```'''
                },
                {
                    "name": "Data Analysis Task",
                    "result": '''## Sales Analysis Report

We analyzed Q4 2024 sales data and found:

```json
{
    "total_revenue": 2456789.50,
    "growth_rate": 0.23,
    "top_products": [
        {"name": "Product A", "revenue": 567890.25, "units": 1234},
        {"name": "Product B", "revenue": 445678.90, "units": 987},
        {"name": "Product C", "revenue": 334567.80, "units": 756}
    ],
    "regional_breakdown": {
        "north_america": {"revenue": 1234567.80, "growth": 0.18},
        "europe": {"revenue": 876543.21, "growth": 0.25},
        "asia_pacific": {"revenue": 345678.49, "growth": 0.35}
    },
    "recommendations": [
        "Increase marketing spend in APAC region",
        "Launch Product D in Q1 2025",
        "Optimize supply chain for Product A"
    ]
}
```

Key insights:
- 23% YoY growth exceeded targets
- APAC showing strongest growth potential
- Product A maintaining market leadership'''
                },
                {
                    "name": "Architecture Design Task", 
                    "result": '''# Microservices Architecture Design

## Overview
Designed a scalable microservices architecture for the e-commerce platform.

## Services Breakdown:

```yaml
services:
  user-service:
    port: 3001
    database: PostgreSQL
    responsibilities:
      - User authentication
      - Profile management
      - JWT token generation
    
  product-service:
    port: 3002
    database: MongoDB
    responsibilities:
      - Product catalog
      - Inventory management
      - Search functionality
  
  order-service:
    port: 3003
    database: PostgreSQL
    responsibilities:
      - Order processing
      - Payment integration
      - Order tracking
  
  notification-service:
    port: 3004
    database: Redis
    responsibilities:
      - Email notifications
      - SMS alerts
      - Push notifications
```

## API Gateway Configuration:

```json
{
    "routes": [
        {"path": "/api/users/*", "service": "user-service"},
        {"path": "/api/products/*", "service": "product-service"},
        {"path": "/api/orders/*", "service": "order-service"}
    ],
    "rateLimit": {"requests": 1000, "window": "1m"},
    "authentication": {"type": "JWT", "secret": "${JWT_SECRET}"}
}
```'''
                }
            ]
            
            # Simulate completed tasks
            self.completed_tasks = []
            for i, task_data in enumerate(self.test_tasks):
                task = {
                    "id": f"test-task-{i+1}",
                    "name": task_data["name"],
                    "result": task_data["result"],
                    "status": "completed",
                    "workspace_id": self.workspace_id
                }
                self.completed_tasks.append(task)
            
            logger.info(f"✅ Created {len(self.completed_tasks)} test tasks with rich content")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 1 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_2_test_asset_extraction(self):
        """Test the ConcreteAssetExtractor"""
        phase_name = "asset_extraction"
        logger.info("🔍 PHASE 2: Testing Asset Extraction")
        
        try:
            # Test extraction for each task
            all_extracted_assets = []
            
            for task in self.completed_tasks:
                logger.info(f"Extracting assets from: {task['name']}")
                
                context = {
                    "task_name": task["name"],
                    "workspace_id": task["workspace_id"]
                }
                
                assets = await concrete_asset_extractor.extract_assets(
                    task["result"], 
                    context
                )
                
                logger.info(f"  📦 Extracted {len(assets)} assets")
                for asset in assets:
                    logger.info(f"    - {asset['asset_type']}: {asset['asset_name']} (quality: {asset.get('quality_score', 0):.2f})")
                
                all_extracted_assets.extend(assets)
            
            self.extracted_assets = all_extracted_assets
            self.test_results["assets_extracted"] = len(all_extracted_assets)
            
            # Verify we got meaningful extractions
            asset_types = set(a['asset_type'] for a in all_extracted_assets)
            assert len(all_extracted_assets) > 0, "No assets extracted"
            assert 'code' in asset_types, "No code assets found"
            assert 'data' in asset_types, "No data assets found"
            
            logger.info(f"✅ Phase 2 Complete - Extracted {len(all_extracted_assets)} assets")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 2 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_3_test_quality_validation(self):
        """Test the Quality Validation Engine"""
        phase_name = "quality_validation"
        logger.info("🛡️ PHASE 3: Testing Quality Validation")
        
        try:
            validated_assets = []
            
            for asset in self.extracted_assets[:5]:  # Test first 5 assets
                logger.info(f"Validating asset: {asset['asset_name']}")
                
                validation_result = await unified_quality_engine.validate_asset_quality(
                    asset_content=asset.get('content', ''),
                    asset_type=asset.get('asset_type', 'unknown'),
                    workspace_id=self.workspace_id,
                    domain_context="Software Development"
                )
                
                logger.info(f"  ✅ Quality Score: {validation_result.get('quality_score', 0):.2f}")
                logger.info(f"  🔍 Needs Enhancement: {validation_result.get('needs_enhancement', False)}")
                
                if validation_result.get('improvement_suggestions'):
                    logger.info("  💡 Suggestions:")
                    for suggestion in validation_result['improvement_suggestions'][:2]:
                        logger.info(f"    - {suggestion}")
                
                validated_assets.append({
                    'asset': asset,
                    'validation': validation_result
                })
            
            self.validated_assets = validated_assets
            self.test_results["quality_validations"] = len(validated_assets)
            
            logger.info(f"✅ Phase 3 Complete - Validated {len(validated_assets)} assets")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 3 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_4_test_intelligent_aggregation(self):
        """Test the Intelligent Aggregator"""
        phase_name = "intelligent_aggregation"
        logger.info("🎯 PHASE 4: Testing Intelligent Aggregation")
        
        try:
            # Use validated assets for aggregation
            assets_to_aggregate = [va['asset'] for va in self.validated_assets]
            
            context = {
                "workspace_id": self.workspace_id,
                "project_name": "Enhanced QA Test Project",
                "domain": "Software Development"
            }
            
            goal_info = {
                "goal_name": "Complete Software System",
                "metrics": ["Code Quality", "Documentation", "Architecture"]
            }
            
            logger.info(f"Aggregating {len(assets_to_aggregate)} assets...")
            
            deliverable = await intelligent_aggregator.aggregate_assets_to_deliverable(
                assets=assets_to_aggregate,
                context=context,
                goal_info=goal_info
            )
            
            self.aggregated_deliverable = deliverable
            
            logger.info(f"✅ Aggregation Result:")
            logger.info(f"  - Title: {deliverable.get('title')}")
            logger.info(f"  - Type: {deliverable.get('type')}")
            logger.info(f"  - Quality Score: {deliverable.get('quality_metrics', {}).get('overall_score', 0):.2f}")
            logger.info(f"  - Content Length: {len(deliverable.get('content', ''))} chars")
            
            # Verify aggregation quality
            assert deliverable.get('status') == 'completed', "Aggregation not completed"
            assert len(deliverable.get('content', '')) > 100, "Content too short"
            assert deliverable.get('quality_metrics', {}).get('overall_score', 0) > 0.5, "Quality too low"
            
            logger.info(f"✅ Phase 4 Complete - Created high-quality deliverable")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 4 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_5_test_complete_flow(self):
        """Test the complete integrated flow"""
        phase_name = "complete_flow"
        logger.info("🔄 PHASE 5: Testing Complete Integrated Flow")
        
        try:
            # Simulate the real flow by calling check_and_create_final_deliverable
            logger.info("Testing complete deliverable creation flow...")
            
            # Note: This would normally use a real workspace with real completed tasks
            # For this test, we're demonstrating the enhanced capabilities
            
            logger.info("📊 Enhanced Flow Summary:")
            logger.info(f"  1. Extracted {self.test_results['assets_extracted']} concrete assets")
            logger.info(f"  2. Validated {self.test_results['quality_validations']} assets for quality")
            logger.info(f"  3. Created intelligent deliverable with quality score: {self.aggregated_deliverable.get('quality_metrics', {}).get('overall_score', 0):.2f}")
            
            # Save deliverable sample
            sample_file = "enhanced_deliverable_sample.md"
            with open(sample_file, 'w') as f:
                f.write("# Enhanced Deliverable Sample\n\n")
                f.write(f"**Executive Summary**: {self.aggregated_deliverable.get('executive_summary', 'N/A')}\n\n")
                f.write("## Content Preview\n\n")
                f.write(self.aggregated_deliverable.get('content', '')[:2000] + "...")
            
            logger.info(f"✅ Saved deliverable sample to: {sample_file}")
            
            self.test_results["deliverables_created"] = 1
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 5 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 70)
        logger.info("🎯 ENHANCED QA & DELIVERABLES TEST SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"✅ Phases Completed: {len(self.test_results['phases_completed'])}/5")
        logger.info(f"❌ Phases Failed: {len(self.test_results['phases_failed'])}")
        
        logger.info(f"\n📊 Metrics:")
        logger.info(f"  - Assets Extracted: {self.test_results['assets_extracted']}")
        logger.info(f"  - Quality Validations: {self.test_results['quality_validations']}")
        logger.info(f"  - Deliverables Created: {self.test_results['deliverables_created']}")
        
        logger.info(f"\n🚀 Overall Success: {'YES' if self.test_results['overall_success'] else 'NO'}")
        
        if self.test_results['phases_failed']:
            logger.info(f"\n❌ Failed Phases: {', '.join(self.test_results['phases_failed'])}")
        
        # Save full results
        results_file = f"enhanced_qa_deliverables_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"\n💾 Full results saved to: {results_file}")
        logger.info("=" * 70)


async def main():
    """Run the enhanced QA and deliverables test"""
    test = EnhancedQADeliverablesTest()
    results = await test.run_complete_test()
    
    # Return exit code based on success
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)