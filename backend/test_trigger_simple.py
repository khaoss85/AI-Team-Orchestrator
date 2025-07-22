#!/usr/bin/env python3
"""
Test semplice del trigger autonomo - crea workspace, task e li completa
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_simple_trigger():
    """Test semplice del trigger autonomo"""
    
    logger.info("🚀 SIMPLE AUTONOMOUS TRIGGER TEST")
    logger.info("=" * 50)
    
    # Step 1: Create workspace
    workspace_data = {
        "name": "Simple Trigger Test",
        "description": "Testing autonomous trigger with minimal setup"
    }
    
    response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
    if response.status_code != 201:
        logger.error(f"Failed to create workspace: {response.status_code} - {response.text}")
        return
    
    workspace = response.json()
    workspace_id = workspace["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Step 2: Create a simple agent for task assignment
    agent_data = {
        "workspace_id": workspace_id,
        "name": "Test Agent",
        "role": "Developer",
        "seniority": "senior"
    }
    
    response = requests.post(f"{BASE_URL}/agents/{workspace_id}", json=agent_data)
    if response.status_code != 201:
        logger.error(f"Failed to create agent: {response.status_code} - {response.text}")
        return
    
    agent = response.json()
    agent_id = agent["id"]
    logger.info(f"✅ Agent created: {agent['name']}")
    
    # Step 3: Create tasks
    tasks = []
    for i in range(3):
        task_data = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "name": f"Analysis Task {i+1}",
            "description": f"Complete analysis and documentation for component {i+1}",
            "status": "pending",
            "priority": str(100 - i*10),
            "estimated_effort_hours": 4
        }
        
        response = requests.post(f"{BASE_URL}/agents/{workspace_id}/tasks", json=task_data)
        if response.status_code == 201:
            task = response.json()
            tasks.append(task)
            logger.info(f"✅ Task created: {task['name']}")
        else:
            logger.error(f"Failed to create task: {response.status_code} - {response.text}")
    
    if len(tasks) < 2:
        logger.error("Not enough tasks created for trigger test")
        return
    
    # Step 4: Complete tasks using database function directly
    logger.info("\n🔧 Completing tasks with substantial results...")
    
    from database import update_task_status
    
    results = [
        """
## Component Analysis Report 1

### Executive Summary
Comprehensive analysis of the e-commerce checkout system component completed with significant findings.

### Key Findings
1. **Performance Bottlenecks**: Database queries taking 800ms average
2. **User Experience Issues**: 5-step checkout process causing 68% abandonment
3. **Security Assessment**: All critical vulnerabilities patched

### Detailed Analysis
The checkout component shows several optimization opportunities:
- Implement query caching for 60% performance improvement
- Reduce checkout steps from 5 to 3 for better conversion
- Add progress indicators for user clarity

### Technical Recommendations
1. **Database Optimization**: Add composite indexes for product searches
2. **Frontend Improvements**: Implement progressive loading
3. **API Enhancements**: Add response compression

### Metrics Achieved
- Analysis coverage: 100% of critical paths
- Performance testing: 1000+ scenarios
- Security scan: 0 high-risk vulnerabilities
- Documentation: 45 pages of technical specifications

This analysis provides the foundation for the optimization phase.
""",
        """
## Component Analysis Report 2

### Executive Summary
Completed in-depth analysis of the payment processing component with actionable optimization recommendations.

### Performance Analysis
Current payment processing shows:
- Average transaction time: 2.3 seconds
- Success rate: 97.8%
- Error handling: Comprehensive but slow

### Optimization Opportunities
1. **Response Time**: Reduce from 2.3s to <1s through caching
2. **Error Recovery**: Implement intelligent retry logic
3. **Integration**: Streamline third-party payment gateway calls

### Security Enhancements
- PCI DSS compliance verification completed
- Encryption standards updated to latest protocols
- Audit trail implementation for all transactions

### Business Impact
- Potential revenue increase: $180K annually
- Customer satisfaction improvement: +22%
- Operational cost reduction: 15%

### Implementation Roadmap
1. **Phase 1**: Caching layer implementation (2 weeks)
2. **Phase 2**: API optimization (3 weeks)
3. **Phase 3**: Enhanced monitoring (1 week)

This comprehensive analysis delivers concrete steps for implementation.
"""
    ]
    
    completed = 0
    for i, task in enumerate(tasks[:2]):  # Complete first 2 tasks
        try:
            result_payload = {
                "execution_time": 150.0,
                "result": results[i],
                "quality_score": 0.93,
                "status": "completed"
            }
            
            # Use the database function to update task
            await update_task_status(task["id"], "completed", result_payload)
            completed += 1
            logger.info(f"✅ Task {i+1} completed: {task['name']}")
            logger.info(f"   Content length: {len(results[i])} chars")
            
            # Small delay
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error completing task {task['id']}: {e}")
    
    logger.info(f"\n📊 Completed {completed} tasks")
    
    # Step 5: Monitor for deliverables
    logger.info("\n🔍 Monitoring for autonomous deliverable creation...")
    logger.info("The trigger should activate after detecting 2+ completed tasks with substantial content")
    
    start_time = time.time()
    timeout = 120  # 2 minutes
    check_interval = 10
    
    while time.time() - start_time < timeout:
        try:
            # Check for deliverables
            response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
            
            if response.status_code == 200:
                deliverables = response.json()
                
                if deliverables and len(deliverables) > 0:
                    logger.info(f"\n🎉 AUTONOMOUS TRIGGER SUCCESS!")
                    logger.info(f"✅ Found {len(deliverables)} deliverables")
                    
                    for i, d in enumerate(deliverables):
                        logger.info(f"\n📦 Deliverable {i+1}:")
                        logger.info(f"   Title: {d.get('title', 'Unknown')}")
                        logger.info(f"   Type: {d.get('type', 'Unknown')}")
                        logger.info(f"   Status: {d.get('status', 'Unknown')}")
                    
                    return True
            
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            logger.info(f"⏱️  {elapsed}s elapsed, {remaining}s remaining...")
            
        except Exception as e:
            logger.error(f"Error checking deliverables: {e}")
        
        await asyncio.sleep(check_interval)
    
    logger.warning("\n⚠️ No autonomous deliverables detected within timeout")
    
    # Debug information
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code == 200:
        all_tasks = response.json()
        completed_count = sum(1 for t in all_tasks if t.get('status') == 'completed')
        logger.info(f"📊 Final status: {completed_count}/{len(all_tasks)} tasks completed")
        
        for t in all_tasks:
            if t.get('status') == 'completed':
                has_result = bool(t.get('result'))
                result_size = len(str(t.get('result', '')))
                logger.info(f"   ✓ {t['name']} - result: {has_result} ({result_size} chars)")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_trigger())
    
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    if success:
        print("✅ AUTONOMOUS TRIGGER WORKING CORRECTLY")
        print("Deliverables were created automatically after task completion")
    else:
        print("❌ AUTONOMOUS TRIGGER NEEDS INVESTIGATION")
        print("No deliverables detected - check server logs for trigger evaluation")