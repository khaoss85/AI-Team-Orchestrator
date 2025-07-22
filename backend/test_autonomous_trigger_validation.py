#!/usr/bin/env python3
"""
Test completo del trigger autonomo dei deliverable
Verifica che il trigger si attivi automaticamente dopo 2+ task completati
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

async def create_workspace_with_agents():
    """Create a workspace with agents for realistic testing"""
    
    # Create workspace
    workspace_data = {
        "name": "Autonomous Trigger Validation Test",
        "description": "E-commerce platform optimization project to test autonomous deliverable generation"
    }
    
    response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
    if response.status_code != 201:
        logger.error(f"Failed to create workspace: {response.status_code}")
        return None, []
    
    workspace = response.json()
    workspace_id = workspace["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Create agents
    agents = [
        {
            "name": "Sarah Chen",
            "role": "Senior UX Designer",
            "skills": ["user research", "interface design", "prototyping"],
            "seniority_level": "senior",
            "is_available": True
        },
        {
            "name": "Marco Rossi",
            "role": "Backend Developer",
            "skills": ["API development", "database optimization", "performance tuning"],
            "seniority_level": "expert",
            "is_available": True
        }
    ]
    
    created_agents = []
    for agent_data in agents:
        response = requests.post(f"{API_BASE}/agents", json=agent_data)
        if response.status_code == 201:
            agent = response.json()
            created_agents.append(agent)
            logger.info(f"✅ Agent created: {agent['name']} ({agent['role']})")
        else:
            logger.error(f"Failed to create agent {agent_data['name']}: {response.status_code} - {response.text}")
    
    return workspace_id, created_agents

async def create_and_assign_tasks(workspace_id, agents):
    """Create tasks and assign to agents"""
    
    tasks = [
        {
            "name": "User Journey Analysis",
            "description": "Analyze current user journey and identify pain points in the checkout process",
            "priority": 100,
            "estimated_effort_hours": 4,
            "agent_id": agents[0]["id"] if agents else None  # Sarah (UX)
        },
        {
            "name": "Database Performance Optimization",
            "description": "Optimize database queries for product catalog and order processing",
            "priority": 95,
            "estimated_effort_hours": 6,
            "agent_id": agents[1]["id"] if len(agents) > 1 else None  # Marco (Backend)
        },
        {
            "name": "Checkout Flow Redesign",
            "description": "Design new streamlined checkout flow based on user research findings",
            "priority": 90,
            "estimated_effort_hours": 8,
            "agent_id": agents[0]["id"] if agents else None  # Sarah (UX)
        }
    ]
    
    created_tasks = []
    for task_data in tasks:
        task_payload = {
            "workspace_id": workspace_id,
            "name": task_data["name"],
            "description": task_data["description"],
            "status": "pending",
            "priority": task_data["priority"],
            "estimated_effort_hours": task_data["estimated_effort_hours"]
        }
        
        # Create task
        response = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/tasks", json=task_payload)
        if response.status_code == 201:
            task = response.json()
            created_tasks.append(task)
            logger.info(f"✅ Task created: {task['name']}")
            
            # Assign to agent if specified
            if task_data.get("agent_id"):
                assign_response = requests.post(
                    f"{API_BASE}/tasks/{task['id']}/assign",
                    json={"agent_id": task_data["agent_id"]}
                )
                if assign_response.status_code == 200:
                    logger.info(f"   → Assigned to agent")
                else:
                    logger.warning(f"   Failed to assign task: {assign_response.status_code}")
        else:
            logger.error(f"Failed to create task {task_data['name']}: {response.status_code} - {response.text}")
    
    return created_tasks

async def execute_tasks_with_results(tasks):
    """Execute tasks with substantial results"""
    
    from database import update_task_status
    
    results = [
        {
            "task_index": 0,
            "result": """
## User Journey Analysis Report

### Executive Summary
Comprehensive analysis of the e-commerce checkout process revealed critical friction points affecting conversion rates.

### Key Findings

1. **Cart Abandonment Rate**: 68% (industry average: 70%)
   - Primary cause: Unexpected shipping costs (42%)
   - Secondary cause: Complex checkout process (31%)
   - Account creation requirement (18%)

2. **Pain Points Identified**:
   - 5-step checkout process (should be 3 max)
   - No guest checkout option
   - Shipping calculator appears too late
   - Limited payment options

3. **User Feedback Analysis** (n=500):
   - "Too many steps" - 67% of respondents
   - "Confusing navigation" - 45%
   - "Slow page loads" - 38%

### Recommendations

1. **Immediate Actions**:
   - Implement guest checkout
   - Show shipping costs upfront
   - Reduce checkout to 3 steps

2. **Short-term Improvements**:
   - Add progress indicator
   - Implement auto-save for forms
   - Add express checkout options

3. **Expected Impact**:
   - 15-20% reduction in cart abandonment
   - $2.5M additional revenue annually
   - Improved customer satisfaction scores

### Next Steps
Design team to create wireframes for new 3-step checkout flow incorporating all recommendations.
"""
        },
        {
            "task_index": 1,
            "result": """
## Database Performance Optimization Report

### Optimization Summary
Successfully optimized critical database queries affecting product catalog and order processing systems.

### Performance Improvements

1. **Product Search Queries**:
   - Before: 850ms average response time
   - After: 120ms average response time
   - Improvement: 86% faster

2. **Order Processing**:
   - Before: 2.3s for complex orders
   - After: 450ms for complex orders
   - Improvement: 80% faster

### Technical Implementation

1. **Index Optimization**:
   ```sql
   CREATE INDEX idx_products_category_price ON products(category_id, price);
   CREATE INDEX idx_orders_user_status ON orders(user_id, status);
   CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
   ```

2. **Query Refactoring**:
   - Eliminated N+1 queries in product listings
   - Implemented query result caching
   - Optimized JOIN operations

3. **Database Configuration**:
   - Increased connection pool size
   - Tuned PostgreSQL parameters
   - Implemented read replicas

### Performance Metrics

- Page load time reduced by 1.8 seconds
- Database CPU usage decreased 40%
- Concurrent user capacity increased 3x
- 99th percentile response time: 250ms

### Monitoring Setup

Implemented comprehensive monitoring:
- Real-time query performance tracking
- Automated slow query alerts
- Database health dashboard

### Business Impact
- Improved user experience with faster page loads
- Reduced infrastructure costs by 25%
- Enabled handling of Black Friday traffic levels
"""
        }
    ]
    
    completed = 0
    for result_data in results[:2]:  # Complete first 2 tasks
        if result_data["task_index"] < len(tasks):
            task = tasks[result_data["task_index"]]
            
            try:
                result_payload = {
                    "execution_time": 180.5,
                    "result": result_data["result"],
                    "quality_score": 0.94,
                    "status": "completed"
                }
                
                # Update task status - this should trigger the autonomous deliverable
                await update_task_status(task["id"], "completed", result_payload)
                completed += 1
                logger.info(f"✅ Task completed: {task['name']}")
                logger.info(f"   Content length: {len(result_data['result'])} chars")
                
                # Small delay to simulate realistic execution
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error completing task {task['id']}: {e}")
    
    return completed

async def monitor_deliverable_creation(workspace_id, timeout=180):
    """Monitor for autonomous deliverable creation"""
    
    logger.info("\n🔍 MONITORING FOR AUTONOMOUS DELIVERABLE TRIGGER")
    logger.info("=" * 60)
    
    start_time = time.time()
    check_interval = 10
    deliverable_found = False
    
    while time.time() - start_time < timeout:
        try:
            # Check for deliverables
            response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
            
            if response.status_code == 200:
                deliverables = response.json()
                
                if deliverables and len(deliverables) > 0:
                    logger.info("\n🎉 AUTONOMOUS DELIVERABLE TRIGGER SUCCESS!")
                    logger.info(f"✅ Found {len(deliverables)} deliverables created automatically")
                    
                    for i, d in enumerate(deliverables):
                        logger.info(f"\n📦 Deliverable {i+1}:")
                        logger.info(f"   Title: {d.get('title', 'Unknown')}")
                        logger.info(f"   Type: {d.get('type', 'Unknown')}")
                        logger.info(f"   Status: {d.get('status', 'Unknown')}")
                        if d.get('content'):
                            logger.info(f"   Content preview: {d['content'][:200]}...")
                    
                    deliverable_found = True
                    break
            
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            logger.info(f"⏱️  Checking... {elapsed}s elapsed, {remaining}s remaining")
            
        except Exception as e:
            logger.error(f"Error checking deliverables: {e}")
        
        await asyncio.sleep(check_interval)
    
    if not deliverable_found:
        logger.warning("\n⚠️  No autonomous deliverables detected within timeout")
        logger.info("Checking task completion status...")
        
        # Debug: Check task status
        response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
        if response.status_code == 200:
            all_tasks = response.json()
            completed_count = sum(1 for t in all_tasks if t.get('status') == 'completed')
            logger.info(f"📊 Task status: {completed_count}/{len(all_tasks)} completed")
            
            # Show completed task details
            for t in all_tasks:
                if t.get('status') == 'completed':
                    logger.info(f"   ✓ {t['name']} - has result: {bool(t.get('result'))}")
    
    return deliverable_found

async def test_autonomous_trigger():
    """Main test function"""
    
    logger.info("🚀 AUTONOMOUS DELIVERABLE TRIGGER VALIDATION TEST")
    logger.info("=" * 60)
    logger.info("This test will:")
    logger.info("1. Create a realistic workspace with agents")
    logger.info("2. Create and assign tasks")
    logger.info("3. Complete tasks with substantial results")
    logger.info("4. Monitor for autonomous deliverable creation")
    logger.info("=" * 60)
    
    # Step 1: Create workspace and agents
    workspace_id, agents = await create_workspace_with_agents()
    if not workspace_id:
        logger.error("Failed to create workspace")
        return
    
    # Step 2: Create and assign tasks
    tasks = await create_and_assign_tasks(workspace_id, agents)
    if len(tasks) < 2:
        logger.error("Not enough tasks created")
        return
    
    logger.info(f"\n📋 Created {len(tasks)} tasks")
    
    # Step 3: Execute tasks with results
    logger.info("\n🔧 Executing tasks with substantial results...")
    completed = await execute_tasks_with_results(tasks)
    logger.info(f"✅ Completed {completed} tasks")
    
    # Step 4: Monitor for autonomous trigger
    success = await monitor_deliverable_creation(workspace_id)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Workspace ID: {workspace_id}")
    logger.info(f"Agents created: {len(agents)}")
    logger.info(f"Tasks created: {len(tasks)}")
    logger.info(f"Tasks completed: {completed}")
    logger.info(f"Autonomous trigger: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        logger.info("\n🎯 The autonomous deliverable trigger is working correctly!")
        logger.info("   Deliverables were created automatically after task completion.")
    else:
        logger.info("\n⚠️  The autonomous trigger may need investigation.")
        logger.info("   Check server logs for detailed trigger evaluation.")

if __name__ == "__main__":
    asyncio.run(test_autonomous_trigger())