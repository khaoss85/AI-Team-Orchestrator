#!/usr/bin/env python3
"""
Test Document Access Through Production Path
Verifies that specialist agents can access documents via the production execution flow
"""

import asyncio
import sys
import os
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from uuid import UUID
from models import Agent as AgentModel, Task, TaskStatus
from ai_agents.manager import AgentManager
from datetime import datetime, timezone

async def test_production_document_access():
    """Test document access through the actual production path"""
    
    print("=" * 80)
    print("🔧 TEST DOCUMENT ACCESS VIA PRODUCTION PATH")
    print("=" * 80)
    
    # Test workspace
    workspace_id = UUID("f35639dc-12ae-4720-882d-3e35a70a79b8")
    
    # Step 1: Create and initialize AgentManager (production path)
    print("\n📋 STEP 1: Initialize AgentManager (Production Path)")
    print("-" * 50)
    
    try:
        # This is how executor.py creates the manager
        manager = AgentManager(workspace_id)
        
        # Initialize the manager
        if await manager.initialize():
            print("✅ AgentManager initialized successfully")
            print(f"   Loaded {len(manager.agents)} specialist agents")
            
            # Show loaded agents
            for agent_id, specialist in manager.agents.items():
                print(f"   - {specialist.agent_data.name} ({specialist.agent_data.role})")
        else:
            print("❌ Failed to initialize AgentManager")
            return
            
    except Exception as e:
        print(f"❌ Error initializing AgentManager: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Check document access for each specialist
    print("\n🔍 STEP 2: Check Document Access Capability")
    print("-" * 50)
    
    specialists_with_access = []
    for agent_id, specialist in manager.agents.items():
        # Wait a bit for async document assistant initialization
        await asyncio.sleep(1)
        
        has_access = specialist.has_document_access()
        print(f"   {specialist.agent_data.name}: {'✅ Has document access' if has_access else '❌ No document access'}")
        
        if has_access:
            specialists_with_access.append(specialist)
    
    if not specialists_with_access:
        print("\n⚠️ No specialists have document access yet")
        print("   This is expected with memory fallback (database table not created)")
        print("   Document access will work once specialist_assistants table exists")
    
    # Step 3: Test document search with a specialist that has access
    if specialists_with_access:
        print("\n🔎 STEP 3: Test Document Search")
        print("-" * 50)
        
        test_specialist = specialists_with_access[0]
        print(f"Testing with: {test_specialist.agent_data.name}")
        
        try:
            # Search for documents
            search_results = await test_specialist.search_workspace_documents(
                "What are the main principles or pillars mentioned in the documents?",
                max_results=3
            )
            
            if search_results:
                print(f"✅ Found {len(search_results)} search results:")
                for i, result in enumerate(search_results, 1):
                    content_preview = str(result.get('content', ''))[:150]
                    print(f"   Result {i}: {content_preview}...")
            else:
                print("⚠️ No search results found (documents might not be uploaded)")
                
        except Exception as e:
            print(f"❌ Error during document search: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 4: Test task execution with document context
    if specialists_with_access:
        print("\n📝 STEP 4: Test Task Execution with Document Context")
        print("-" * 50)
        
        test_specialist = specialists_with_access[0]
        
        # Create a test task
        test_task = Task(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            workspace_id=workspace_id,
            agent_id=test_specialist.agent_data.id,
            name="Analyze workspace principles",
            description="Search the workspace documents and summarize the main principles or pillars mentioned",
            status=TaskStatus.PENDING,
            priority=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        print(f"Created test task: {test_task.name}")
        
        try:
            # Execute the task
            print("Executing task with document context...")
            result = await test_specialist.execute(test_task)
            
            if result:
                print("✅ Task executed successfully")
                print(f"   Status: {result.status}")
                if hasattr(result, 'summary'):
                    print(f"   Summary: {result.summary[:200]}...")
            else:
                print("❌ Task execution returned no result")
                
        except Exception as e:
            print(f"❌ Error executing task: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ PRODUCTION PATH DOCUMENT ACCESS TEST COMPLETED")
    print("=" * 80)
    
    # Summary
    print("\n📊 TEST SUMMARY:")
    print("-" * 50)
    print(f"✅ AgentManager initialization: SUCCESS")
    print(f"✅ Specialist agents loaded: {len(manager.agents)}")
    print(f"⚠️ Document access available: {len(specialists_with_access)}/{len(manager.agents)} agents")
    print(f"📝 Note: Full document access requires specialist_assistants table in database")
    print(f"         Currently using memory fallback which works for testing")

if __name__ == "__main__":
    asyncio.run(test_production_document_access())