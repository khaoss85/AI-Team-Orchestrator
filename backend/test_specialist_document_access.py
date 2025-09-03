#!/usr/bin/env python3
"""
Test Specialist Agent Document Access
Verifies that specialist agents can access and search workspace documents
"""

import asyncio
import os
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from database import get_supabase_client
from services.shared_document_manager import shared_document_manager

async def test_specialist_document_integration():
    """Test the complete specialist document integration"""
    
    print("=" * 80)
    print("🔧 TEST SPECIALIST AGENTS DOCUMENT ACCESS")
    print("=" * 80)
    
    # Test workspace
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    # Step 1: Check shared document manager
    print("\n📋 STEP 1: Check Shared Document Manager")
    print("-" * 50)
    try:
        # Get workspace vector stores
        vector_stores = await shared_document_manager._get_workspace_vector_stores(workspace_id)
        print(f"✅ Workspace vector stores: {len(vector_stores)}")
        for vs_id in vector_stores:
            print(f"   - Vector store: {vs_id}")
            
    except Exception as e:
        print(f"❌ Error checking vector stores: {e}")
        return
    
    # Step 2: Get existing agents in workspace
    print("\n👥 STEP 2: Get Workspace Agents")
    print("-" * 50)
    try:
        supabase = get_supabase_client()
        result = supabase.table("agents")\
            .select("id, name, role, seniority")\
            .eq("workspace_id", workspace_id)\
            .eq("status", "available")\
            .limit(3)\
            .execute()
        
        if not result.data:
            print("❌ No agents found in workspace")
            return
            
        print(f"✅ Found {len(result.data)} agents in workspace:")
        agents = result.data
        for agent in agents:
            print(f"   - {agent['name']} ({agent['role']}, {agent.get('seniority', 'N/A')})")
            
    except Exception as e:
        print(f"❌ Error getting agents: {e}")
        return
    
    # Step 3: Test specialist assistant creation
    print("\n🤖 STEP 3: Create Specialist Assistants")
    print("-" * 50)
    test_agent = agents[0]  # Use first agent for testing
    agent_id = test_agent['id']
    
    try:
        # Build agent config
        agent_config = {
            'role': test_agent['role'],
            'name': test_agent['name'],
            'skills': ['analysis', 'research', 'documentation'],
            'seniority': test_agent.get('seniority', 'senior'),
            'preferred_model': 'gpt-4-turbo-preview',
            'temperature': 0.3
        }
        
        # Create specialist assistant
        assistant_id = await shared_document_manager.create_specialist_assistant(
            workspace_id, agent_id, agent_config
        )
        
        if assistant_id:
            print(f"✅ Created specialist assistant: {assistant_id}")
            print(f"   For agent: {test_agent['name']} ({test_agent['role']})")
        else:
            print("❌ Failed to create specialist assistant")
            return
            
    except Exception as e:
        print(f"❌ Error creating specialist assistant: {e}")
        return
    
    # Step 4: Test document synchronization
    print("\n🔄 STEP 4: Test Document Synchronization")  
    print("-" * 50)
    try:
        # Sync documents to all specialists
        sync_result = await shared_document_manager.sync_documents_to_all_specialists(workspace_id)
        
        if sync_result:
            print("✅ Document synchronization successful")
        else:
            print("⚠️ Document synchronization had some issues")
            
    except Exception as e:
        print(f"❌ Error syncing documents: {e}")
    
    # Step 5: Test specialist assistant mapping retrieval
    print("\n🔍 STEP 5: Test Assistant Mapping Retrieval")
    print("-" * 50)
    try:
        # Get specialist assistant ID
        retrieved_assistant_id = await shared_document_manager.get_specialist_assistant_id(
            workspace_id, agent_id
        )
        
        if retrieved_assistant_id:
            print(f"✅ Retrieved assistant ID: {retrieved_assistant_id}")
            if retrieved_assistant_id == assistant_id:
                print("✅ Assistant ID matches created assistant")
            else:
                print("⚠️ Assistant ID mismatch")
        else:
            print("❌ Could not retrieve assistant ID")
            
    except Exception as e:
        print(f"❌ Error retrieving assistant mapping: {e}")
    
    # Step 6: Test document search capability
    print("\n🔍 STEP 6: Test Document Search via Specialist")
    print("-" * 50)
    try:
        # Import specialist agent for testing
        from ai_agents.specialist import SpecialistAgent
        from models import Agent as AgentModel
        from datetime import datetime, timezone
        
        # Create agent model instance
        agent_model = AgentModel(
            id=agent_id,
            workspace_id=workspace_id,
            name=test_agent['name'],
            role=test_agent['role'],
            seniority=test_agent.get('seniority', 'senior'),
            skills=['analysis', 'research', 'documentation'],
            status='available',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create specialist agent instance
        specialist = SpecialistAgent(agent_model)
        
        # Initialize document assistant
        await specialist._initialize_document_assistant()
        
        # Check if document access is available
        has_access = specialist.has_document_access()
        print(f"Document access available: {'✅ Yes' if has_access else '❌ No'}")
        
        if has_access:
            # Test document search
            print("\n🔎 Testing document search...")
            search_results = await specialist.search_workspace_documents(
                "What are the main principles mentioned in the documents?"
            )
            
            if search_results:
                print(f"✅ Document search successful - {len(search_results)} results")
                for i, result in enumerate(search_results, 1):
                    content_preview = result.get('content', '')[:200]
                    print(f"   Result {i}: {content_preview}...")
            else:
                print("⚠️ No search results found")
        
    except Exception as e:
        print(f"❌ Error testing document search: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ SPECIALIST DOCUMENT ACCESS TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_specialist_document_integration())