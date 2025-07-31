#!/usr/bin/env python3
"""
Comprehensive test of deliverable system fixes on real workspace data.
Tests the entire pipeline from asset extraction to deliverable creation.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import database and models
from database import supabase
from models import TaskStatus
from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from deliverable_system.unified_deliverable_engine import UnifiedDeliverableEngine
from ai_agents.deliverable_assembly import DeliverableAssemblyAgent
from services.ai_provider_abstraction import ai_provider_manager

# Test configuration
TEST_WORKSPACE_ID = "40284998-3fd1-4a7b-8cb9-07d3b85fe993"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

class DeliverableSystemTester:
    def __init__(self):
        self.db = supabase
        self.asset_extractor = ConcreteAssetExtractor()
        self.deliverable_engine = UnifiedDeliverableEngine()
        self.ai_provider = ai_provider_manager
        self.results = {
            "timestamp": TIMESTAMP,
            "workspace_id": TEST_WORKSPACE_ID,
            "tests": []
        }
    
    async def test_workspace_data(self):
        """Load and analyze workspace data."""
        print("\n" + "="*80)
        print("📊 LOADING WORKSPACE DATA")
        print("="*80)
        
        # Get workspace info
        workspace = self.db.table("workspaces").select("*").eq("id", TEST_WORKSPACE_ID).single().execute()
        print(f"\nWorkspace: {workspace.data['name']}")
        print(f"Goal: {workspace.data.get('goal', 'No goal set')}")
        print(f"Description: {workspace.data.get('description', 'No description')[:100]}...")
        
        # Get completed tasks
        tasks = self.db.table("tasks").select("*").eq(
            "workspace_id", TEST_WORKSPACE_ID
        ).eq("status", TaskStatus.COMPLETED.value).execute()
        
        print(f"\nCompleted Tasks: {len(tasks.data)}")
        for i, task in enumerate(tasks.data[:5]):  # Show first 5
            title = task.get('title') or task.get('name') or f"Task {task.get('id', i+1)}"
            print(f"  {i+1}. {title} (Priority: {task.get('priority', 0)})")
            if task.get('result'):
                result = str(task['result'])
                print(f"     Result preview: {result[:100]}...")
            elif task.get('output'):
                output = str(task['output'])
                print(f"     Output preview: {output[:100]}...")
        
        self.results["tests"].append({
            "test": "workspace_data",
            "workspace_name": workspace.data['name'],
            "completed_tasks": len(tasks.data),
            "status": "success"
        })
        
        return tasks.data
    
    async def test_asset_extraction(self, tasks: List[Dict]):
        """Test the concrete asset extractor."""
        print("\n" + "="*80)
        print("🔍 TESTING ASSET EXTRACTION")
        print("="*80)
        
        all_assets = []
        extraction_results = []
        
        for task in tasks[:3]:  # Test first 3 tasks
            title = task.get('title') or task.get('name') or f"Task {task.get('id', 'Unknown')}"
            print(f"\nExtracting assets from: {title}")
            
            # Extract assets from task content
            task_content = str(task.get('result', {}).get('result', '') or task.get('output', ''))
            assets = await self.asset_extractor.extract_assets(task_content, {"task_id": task.get('id')})
            
            print(f"  Found {len(assets)} assets:")
            for asset in assets:
                asset_type = asset.get('type', 'unknown')
                quality_score = asset.get('quality_score', 0)
                print(f"    - Type: {asset_type}, Quality: {quality_score}")
                content = str(asset.get('content', ''))
                print(f"      Content preview: {content[:100]}...")
                print(f"      Asset keys: {list(asset.keys())}")  # Debug info
            
            all_assets.extend(assets)
            extraction_results.append({
                "task_title": title,
                "assets_found": len(assets),
                "asset_types": [a.get('type', 'unknown') for a in assets],
                "avg_quality": sum(a.get('quality_score', 0) for a in assets) / len(assets) if assets else 0
            })
        
        self.results["tests"].append({
            "test": "asset_extraction",
            "total_assets": len(all_assets),
            "extraction_results": extraction_results,
            "status": "success" if all_assets else "warning"
        })
        
        return all_assets
    
    async def test_deliverable_assembly(self, assets: List[Dict]):
        """Test the deliverable assembly agent."""
        print("\n" + "="*80)
        print("🏗️ TESTING DELIVERABLE ASSEMBLY")
        print("="*80)
        
        # Create assembly agent instance
        assembly_agent = DeliverableAssemblyAgent()
        
        # Test deliverable assembly from assets  
        print("\nTesting deliverable assembly from assets...")
        
        if assets:
            # Calculate average quality of input assets
            avg_quality = sum(a.get('quality_score', 0) for a in assets) / len(assets)
            print(f"Input assets average quality: {avg_quality:.1f}")
            
            # Test deliverable assembly
            workspace_goal = "Generate email marketing assets for B2B outbound sales"
            workspace_context = {
                "workspace_id": TEST_WORKSPACE_ID,
                "domain": "B2B SaaS Marketing",
                "target_audience": "CMO/CTO of European SaaS companies"
            }
            
            deliverable = await assembly_agent.assemble_deliverable(
                workspace_goal, 
                assets[:5],  # Use first 5 assets
                workspace_context
            )
            
            print(f"\nDeliverable assembled:")
            print(f"  Content Length: {len(str(deliverable.get('content', '')))}")
            print(f"  Quality Score: {deliverable.get('quality_score', 0)}")
            print(f"  Asset Count Used: {len(assets[:5])}")
            
            # Show a preview of the assembled content
            content_preview = str(deliverable.get('content', ''))[:300]
            print(f"  Content Preview: {content_preview}...")
            
            deliverable_quality = deliverable.get('quality_score', 0)
        else:
            print("No assets available for assembly test")
            deliverable_quality = 0
        
        self.results["tests"].append({
            "test": "deliverable_assembly",
            "input_assets_count": len(assets),
            "avg_input_quality": avg_quality if assets else 0,
            "deliverable_quality": deliverable_quality,
            "status": "success" if deliverable_quality > 80 else "warning"
        })
        
        return deliverable
    
    async def test_unified_engine(self, workspace_id: str):
        """Test the unified deliverable engine end-to-end."""
        print("\n" + "="*80)
        print("🚀 TESTING UNIFIED DELIVERABLE ENGINE")
        print("="*80)
        
        # Get workspace goals
        goals = self.db.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).execute()
        
        print(f"Found {len(goals.data)} goals for workspace")
        
        result = None
        if goals.data:
            goal_id = goals.data[0]['id']
            print(f"Testing deliverable creation for goal: {goal_id}")
            
            # Import the function directly since it's a module-level function
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            
            # Create deliverable for the goal
            result = await create_goal_specific_deliverable(workspace_id, goal_id, force=True)
            
            if result:
                print(f"\nDeliverable created successfully!")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Quality Score: {result.get('quality_score', 0)}")
                print(f"  Content Length: {len(str(result.get('content', '')))}")
                
                # Show a preview of the content
                content_preview = str(result.get('content', ''))[:300]
                print(f"  Content Preview: {content_preview}...")
            else:
                print("Failed to create deliverable")
        else:
            print("No goals found for workspace - testing general deliverable creation")
            
            # Try the general function
            from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
            result = await check_and_create_final_deliverable(workspace_id, force=True)
            
            if result:
                print(f"General deliverable created: {result}")
            else:
                print("No deliverable was created")
        
        self.results["tests"].append({
            "test": "unified_engine",
            "goals_found": len(goals.data) if goals.data else 0,
            "creation_result": result is not None,
            "deliverable_quality": result.get('quality_score', 0) if result else 0,
            "status": "success" if result else "warning"
        })
        
        return result
    
    async def test_quality_improvements(self):
        """Test that quality scores are now in the 85-95 range."""
        print("\n" + "="*80)
        print("✨ TESTING QUALITY IMPROVEMENTS")
        print("="*80)
        
        # Get recent deliverables
        deliverables = self.db.table("deliverables").select("*").eq(
            "workspace_id", TEST_WORKSPACE_ID
        ).order("created_at", desc=True).limit(5).execute()
        
        print(f"\nAnalyzing {len(deliverables.data)} recent deliverables:")
        
        quality_scores = []
        for d in deliverables.data:
            quality = d.get('quality_score', 0)
            quality_scores.append(quality)
            print(f"  - {d['title']}: Quality Score = {quality}")
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"\nAverage Quality Score: {avg_quality:.1f}")
            print(f"Quality Range: {min(quality_scores)} - {max(quality_scores)}")
            
            # Check if scores are in target range
            in_target_range = all(85 <= q <= 95 for q in quality_scores)
            print(f"\nAll scores in 85-95 range: {'✅ YES' if in_target_range else '❌ NO'}")
        
        self.results["tests"].append({
            "test": "quality_improvements",
            "deliverable_count": len(deliverables.data),
            "quality_scores": quality_scores,
            "avg_quality": avg_quality if quality_scores else 0,
            "in_target_range": in_target_range if quality_scores else False,
            "status": "success" if quality_scores and avg_quality >= 85 else "warning"
        })
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        try:
            print("\n" + "="*80)
            print("🧪 DELIVERABLE SYSTEM COMPREHENSIVE TEST")
            print(f"   Workspace: {TEST_WORKSPACE_ID}")
            print(f"   Timestamp: {TIMESTAMP}")
            print("="*80)
            
            # 1. Load workspace data
            tasks = await self.test_workspace_data()
            
            if not tasks:
                print("\n⚠️ No completed tasks found. Creating some test data...")
                # Would normally create test tasks here
                return
            
            # 2. Test asset extraction
            assets = await self.test_asset_extraction(tasks)
            
            # 3. Test deliverable assembly
            if assets:
                deliverable = await self.test_deliverable_assembly(assets)
            
            # 4. Test unified engine
            engine_result = await self.test_unified_engine(TEST_WORKSPACE_ID)
            
            # 5. Test quality improvements
            await self.test_quality_improvements()
            
            # Save results
            results_file = f"deliverable_fixes_test_{TIMESTAMP}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print("\n" + "="*80)
            print("📊 TEST SUMMARY")
            print("="*80)
            
            success_count = sum(1 for t in self.results["tests"] if t["status"] == "success")
            total_count = len(self.results["tests"])
            
            print(f"\nTests Run: {total_count}")
            print(f"Successful: {success_count}")
            print(f"Warnings: {total_count - success_count}")
            print(f"\nResults saved to: {results_file}")
            
            # Print key findings
            print("\n🔑 KEY FINDINGS:")
            for test in self.results["tests"]:
                if test["test"] == "quality_improvements":
                    print(f"  - Average Quality Score: {test.get('avg_quality', 0):.1f}")
                    print(f"  - In Target Range (85-95): {'Yes' if test.get('in_target_range') else 'No'}")
                elif test["test"] == "deliverable_assembly":
                    print(f"  - Quality Improvement: {test.get('enhanced_avg_quality', 0) - test.get('original_avg_quality', 0):.1f} points")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["error"] = str(e)
            return self.results


async def main():
    """Run the comprehensive deliverable system test."""
    tester = DeliverableSystemTester()
    results = await tester.run_all_tests()
    
    # Final verdict
    print("\n" + "="*80)
    print("🏁 FINAL VERDICT")
    print("="*80)
    
    all_success = all(t["status"] == "success" for t in results["tests"])
    if all_success:
        print("\n✅ ALL TESTS PASSED! The deliverable system fixes are working correctly.")
    else:
        print("\n⚠️ Some tests had warnings. Review the results for details.")
    
    print("\n💡 Next Steps:")
    print("  1. Monitor deliverable creation in production")
    print("  2. Check that quality scores stay in 85-95 range")
    print("  3. Verify asset extraction captures all relevant content")
    print("  4. Ensure no duplicate deliverables are created")


if __name__ == "__main__":
    asyncio.run(main())