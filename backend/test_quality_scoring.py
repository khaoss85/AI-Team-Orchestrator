#!/usr/bin/env python3
"""
Test Quality Scoring Fixes

Tests the improved quality scoring system to ensure deliverables
get reasonable quality scores instead of defaulting to 0%.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
from deliverable_system.intelligent_aggregator import intelligent_aggregator

async def main():
    """Test quality scoring improvements"""
    
    print("🧪 TESTING QUALITY SCORING FIXES")
    print("=" * 60)
    
    # Test 1: Asset quality scoring
    print(f"\n📋 TEST 1: Asset Quality Scoring")
    
    # Create test task results to extract assets from
    test_tasks = [
        {
            'id': 'test-task-1',
            'name': 'Create project documentation',
            'status': 'completed',
            'result': '''
# Project Documentation

## Overview
This project implements an AI-driven task orchestration system with the following features:

## Features
- **Multi-agent coordination**: Intelligent agent assignment based on skills and expertise
- **Quality assurance**: Automated QA gates with AI validation
- **Real-time monitoring**: Comprehensive system health monitoring
- **Asset management**: Intelligent asset extraction and aggregation

## Technical Architecture
The system consists of several key components:

1. **Director Agent**: Analyzes projects and proposes specialized teams
2. **Specialist Agents**: Execute specific tasks based on their expertise
3. **Quality Engine**: Validates outputs and ensures high standards
4. **Asset System**: Extracts and manages project deliverables

## Implementation Details
```python
class AIOrchestrator:
    def __init__(self):
        self.agents = []
        self.quality_engine = QualityEngine()
    
    async def process_task(self, task):
        agent = await self.select_best_agent(task)
        result = await agent.execute(task)
        return await self.quality_engine.validate(result)
```

This documentation provides a comprehensive overview of the system architecture and implementation.
            ''',
            'workspace_id': 'test-workspace',
            'type': 'documentation'
        },
        {
            'id': 'test-task-2',
            'name': 'Analyze system performance',
            'status': 'completed',
            'result': {
                'analysis_type': 'performance_metrics',
                'findings': [
                    'System processes 95% of tasks within 30 seconds',
                    'Memory usage stays below 2GB under normal load',
                    'Quality gate validation accuracy is 92%'
                ],
                'recommendations': [
                    'Implement task batching for improved throughput',
                    'Add memory cleanup routines for long-running processes',
                    'Enhance quality validation with domain-specific rules'
                ],
                'metrics': {
                    'avg_response_time': 12.5,
                    'success_rate': 0.95,
                    'quality_score': 0.92
                }
            },
            'workspace_id': 'test-workspace',
            'type': 'analysis'
        }
    ]
    
    # Extract assets from tasks
    assets_by_task = await concrete_asset_extractor.extract_assets_from_task_batch(test_tasks)
    
    total_assets = 0
    total_quality = 0.0
    
    print(f"   📊 Asset extraction results:")
    for task_id, assets in assets_by_task.items():
        print(f"      Task {task_id}: {len(assets)} assets extracted")
        
        for asset in assets:
            quality = asset.get('quality_score', 0.0)
            asset_name = asset.get('asset_name', 'unknown')
            asset_type = asset.get('asset_type', 'unknown')
            
            print(f"         - {asset_name} ({asset_type}): Quality {quality:.2f}")
            
            total_assets += 1
            total_quality += quality
    
    avg_asset_quality = total_quality / max(1, total_assets)
    print(f"   🎯 Average asset quality: {avg_asset_quality:.2f}")
    
    if avg_asset_quality >= 0.6:
        print(f"   ✅ Asset quality scoring IMPROVED (was defaulting to ~0.5)")
    else:
        print(f"   ⚠️  Asset quality still low: {avg_asset_quality:.2f}")
    
    # Test 2: Deliverable aggregation quality
    print(f"\n📦 TEST 2: Deliverable Quality Calculation")
    
    # Flatten all assets for aggregation
    all_assets = []
    for assets in assets_by_task.values():
        all_assets.extend(assets)
    
    if not all_assets:
        print(f"   ❌ No assets to aggregate - asset extraction failed")
        return
    
    # Create test context
    context = {
        'workspace_id': 'test-workspace',
        'project_name': 'Quality Scoring Test',
        'domain': 'Software Development'
    }
    
    # Aggregate into deliverable
    deliverable_result = await intelligent_aggregator.aggregate_assets_to_deliverable(
        assets=all_assets,
        context=context,
        goal_info=None
    )
    
    # Check deliverable quality
    deliverable_quality = deliverable_result.get('quality_metrics', {})
    overall_score = deliverable_quality.get('overall_score', 0.0)
    asset_quality = deliverable_quality.get('asset_quality', 0.0)
    completeness = deliverable_quality.get('completeness', 0.0)
    diversity = deliverable_quality.get('diversity', 0.0)
    
    print(f"   📊 Deliverable quality breakdown:")
    print(f"      Overall Score: {overall_score:.2f}")
    print(f"      Asset Quality: {asset_quality:.2f}")
    print(f"      Completeness: {completeness:.2f}")
    print(f"      Diversity: {diversity:.2f}")
    print(f"      Assets Count: {deliverable_quality.get('asset_count', 0)}")
    
    # Test 3: End-to-end quality validation
    print(f"\n🔍 TEST 3: End-to-End Quality Validation")
    
    content_length = len(deliverable_result.get('content', ''))
    print(f"   Content length: {content_length} characters")
    
    if overall_score >= 0.6:
        print(f"   ✅ DELIVERABLE QUALITY FIXED: {overall_score:.2f} (was ~0.0)")
        quality_status = "EXCELLENT" if overall_score >= 0.8 else "GOOD"
        print(f"   🎉 Quality Status: {quality_status}")
    else:
        print(f"   ⚠️  Deliverable quality still low: {overall_score:.2f}")
    
    # Test 4: Quality thresholds validation  
    print(f"\n⚙️ TEST 4: Quality Thresholds Validation")
    
    passed_asset_threshold = len([a for a in all_assets if a.get('quality_score', 0) >= 0.5])
    total_assets_count = len(all_assets)
    pass_rate = passed_asset_threshold / max(1, total_assets_count)
    
    print(f"   Assets passing quality threshold (≥0.5): {passed_asset_threshold}/{total_assets_count} ({pass_rate:.1%})")
    
    if pass_rate >= 0.8:
        print(f"   ✅ Asset filtering threshold WORKING")
    else:
        print(f"   ⚠️  Low asset quality pass rate")
    
    # Summary
    print(f"\n📈 QUALITY SCORING FIX SUMMARY")
    print(f"   Asset Quality Fixed: {'✅ YES' if avg_asset_quality >= 0.6 else '❌ NO'}")
    print(f"   Deliverable Quality Fixed: {'✅ YES' if overall_score >= 0.6 else '❌ NO'}")
    print(f"   Quality Thresholds Working: {'✅ YES' if pass_rate >= 0.8 else '❌ NO'}")
    
    if overall_score >= 0.6 and avg_asset_quality >= 0.6:
        print(f"\n🎉 PHASE 2 SUCCESS: Quality scoring system fixed!")
        print(f"   - Assets now get realistic quality scores (avg: {avg_asset_quality:.2f})")
        print(f"   - Deliverables get proper quality metrics (score: {overall_score:.2f})")
        print(f"   - Quality thresholds prevent 0% scores")
    else:
        print(f"\n⚠️  PHASE 2 PARTIAL: Some quality issues remain")

if __name__ == "__main__":
    asyncio.run(main())