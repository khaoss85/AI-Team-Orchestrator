#!/usr/bin/env python3
"""
🔍 Diagnose System State
Quick diagnostic to understand what's actually running
"""

import asyncio
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def diagnose():
    print("🔍 SYSTEM DIAGNOSTIC")
    print("="*50)
    
    # Test 1: Server connectivity
    print("\n1️⃣ Testing Server Connectivity...")
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoints = ["/", "/api/health", "/health", "/api", "/docs"]
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{base_url}{endpoint}")
                    print(f"   {endpoint}: {response.status_code} {'✅' if response.status_code < 400 else '❌'}")
                except Exception as e:
                    print(f"   {endpoint}: Failed - {type(e).__name__}")
    except Exception as e:
        print(f"   ❌ Cannot create HTTP client: {e}")
        return
    
    # Test 2: Database connectivity
    print("\n2️⃣ Testing Database Connectivity...")
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Try a simple query
        result = supabase.table("workspaces").select("id").limit(1).execute()
        print(f"   ✅ Database connected - can query workspaces")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test 3: Check recent workspaces
    print("\n3️⃣ Checking Recent Workspaces...")
    try:
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        result = supabase.table("workspaces").select("id, name, status, created_at").gte("created_at", yesterday).execute()
        
        if result.data:
            print(f"   Found {len(result.data)} workspaces created in last 24h:")
            for ws in result.data[:5]:
                print(f"   - {ws['id']}: {ws['name']} ({ws['status']})")
        else:
            print("   No workspaces created in last 24h")
    except Exception as e:
        print(f"   ❌ Error checking workspaces: {e}")
    
    # Test 4: Check orchestration components
    print("\n4️⃣ Checking Orchestration Components...")
    components = [
        ("UnifiedOrchestrator", "services.unified_orchestrator"),
        ("Executor", "executor"),
        ("Director", "ai_agents.director"),
        ("RealToolIntegrationPipeline", "services.real_tool_integration_pipeline"),
    ]
    
    for name, module_path in components:
        try:
            module = __import__(module_path, fromlist=[name])
            print(f"   ✅ {name} - available")
        except Exception as e:
            print(f"   ❌ {name} - {type(e).__name__}")
    
    # Test 5: Check if we can create a workspace via Python
    print("\n5️⃣ Testing Workspace Creation (Direct)...")
    try:
        workspace_data = {
            "id": str(uuid.uuid4()),
            "name": "Diagnostic Test Workspace",
            "description": "Testing system state",
            "goal": "Verify system functionality",
            "budget": 1000.0,
            "status": "active",
            "user_id": str(uuid.uuid4())
        }
        
        result = supabase.table("workspaces").insert(workspace_data).execute()
        
        if result.data:
            ws_id = result.data[0]['id']
            print(f"   ✅ Created workspace: {ws_id}")
            
            # Clean up
            supabase.table("workspaces").delete().eq("id", ws_id).execute()
            print(f"   🧹 Cleaned up test workspace")
        else:
            print("   ❌ Failed to create workspace")
    except Exception as e:
        print(f"   ❌ Workspace creation error: {e}")
    
    print("\n" + "="*50)
    print("Diagnostic complete!")

if __name__ == "__main__":
    import uuid
    asyncio.run(diagnose())