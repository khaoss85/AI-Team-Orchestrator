#!/usr/bin/env python3
"""
🗑️ TEST CASCADE DELETION
Script per testare che la cancellazione di workspace elimini correttamente tutti i dati correlati
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def test_cascade_deletion():
    """Test completo della cascade deletion per workspace"""
    print("🗑️ TESTING WORKSPACE CASCADE DELETION")
    print("=" * 60)
    
    # Crea workspace di test
    test_workspace_id = str(uuid4())
    test_workspace = {
        "id": test_workspace_id,
        "name": "TEST DELETE WORKSPACE",
        "description": "Test workspace for cascade deletion",
        "user_id": "test-user",
        "goal": "Test workspace to verify cascade deletion works properly",
        "status": "active"
    }
    
    print(f"📁 Creating test workspace: {test_workspace_id}")
    
    try:
        # 1. Crea workspace
        workspace_result = supabase.table("workspaces").insert(test_workspace).execute()
        if not workspace_result.data:
            print("❌ Failed to create test workspace")
            return
        
        print("✅ Test workspace created")
        
        # 2. Crea dati correlati in varie tabelle
        test_data = []
        
        # Crea agente
        agent_id = str(uuid4())
        agent_data = {
            "id": agent_id,
            "workspace_id": test_workspace_id,
            "name": "Test Agent",
            "role": "test_role",
            "seniority": "junior",
            "status": "active"
        }
        agent_result = supabase.table("agents").insert(agent_data).execute()
        if agent_result.data:
            test_data.append(("agents", agent_id))
            print("✅ Test agent created")
        
        # Crea task
        task_id = str(uuid4())
        task_data = {
            "id": task_id,
            "workspace_id": test_workspace_id,
            "agent_id": agent_id,
            "name": "Test Task",
            "status": "pending",
            "priority": "medium"
        }
        task_result = supabase.table("tasks").insert(task_data).execute()
        if task_result.data:
            test_data.append(("tasks", task_id))
            print("✅ Test task created")
        
        # Crea workspace goal
        goal_id = str(uuid4())
        goal_data = {
            "id": goal_id,
            "workspace_id": test_workspace_id,
            "metric_type": "contacts",
            "target_value": 10,
            "current_value": 0,
            "unit": "contacts",
            "description": "Test goal for cascade deletion",
            "status": "active",
            "priority": 1
        }
        goal_result = supabase.table("workspace_goals").insert(goal_data).execute()
        if goal_result.data:
            test_data.append(("workspace_goals", goal_id))
            print("✅ Test workspace goal created")
        
        # Crea workspace insight
        insight_id = str(uuid4())
        insight_data = {
            "id": insight_id,
            "workspace_id": test_workspace_id,
            "task_id": task_id,
            "agent_role": "test_agent",
            "insight_type": "discovery",
            "content": "Test insight for cascade deletion",
            "relevance_tags": ["test"],
            "confidence_score": 0.8,
            "created_at": datetime.now().isoformat()
        }
        insight_result = supabase.table("workspace_insights").insert(insight_data).execute()
        if insight_result.data:
            test_data.append(("workspace_insights", insight_id))
            print("✅ Test workspace insight created")
        
        # Crea log entry
        log_id = str(uuid4())
        log_data = {
            "id": log_id,
            "workspace_id": test_workspace_id,
            "agent_id": agent_id,
            "type": "test_log",
            "message": "Test log entry for cascade deletion",
            "metadata": {"test": True}
        }
        log_result = supabase.table("logs").insert(log_data).execute()
        if log_result.data:
            test_data.append(("logs", log_id))
            print("✅ Test log entry created")
        
        # Crea execution log
        exec_log_id = str(uuid4())
        exec_log_data = {
            "id": exec_log_id,
            "workspace_id": test_workspace_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "type": "test_execution",
            "content": {"test": "execution log"}
        }
        exec_log_result = supabase.table("execution_logs").insert(exec_log_data).execute()
        if exec_log_result.data:
            test_data.append(("execution_logs", exec_log_id))
            print("✅ Test execution log created")
        
        # Crea human feedback request
        feedback_id = str(uuid4())
        feedback_data = {
            "id": feedback_id,
            "workspace_id": test_workspace_id,
            "request_type": "test_feedback",
            "title": "Test Feedback",
            "description": "Test feedback for cascade deletion",
            "proposed_actions": [{"action": "test"}],
            "context": {"test": True},
            "priority": "medium",
            "timeout_hours": 24
        }
        feedback_result = supabase.table("human_feedback_requests").insert(feedback_data).execute()
        if feedback_result.data:
            test_data.append(("human_feedback_requests", feedback_id))
            print("✅ Test human feedback request created")
        
        print(f"\n📊 CREATED {len(test_data)} related records across {len(set(item[0] for item in test_data))} tables")
        
        # 3. Verifica che tutti i dati esistano
        print("\n🔍 VERIFYING DATA EXISTS BEFORE DELETION:")
        data_counts_before = {}
        for table_name, record_id in test_data:
            result = supabase.table(table_name).select("id").eq("id", record_id).execute()
            count = len(result.data) if result.data else 0
            data_counts_before[table_name] = data_counts_before.get(table_name, 0) + count
            if count > 0:
                print(f"✅ {table_name}: {count} record found")
            else:
                print(f"❌ {table_name}: No record found!")
        
        # 4. CANCELLA WORKSPACE (cascade deletion test)
        print(f"\n🗑️ DELETING WORKSPACE: {test_workspace_id}")
        print("This should CASCADE DELETE all related records...")
        
        delete_result = supabase.table("workspaces").delete().eq("id", test_workspace_id).execute()
        if delete_result.data:
            print("✅ Workspace deleted successfully")
        else:
            print("❌ Failed to delete workspace")
            return
        
        # 5. Verifica che tutti i dati correlati siano stati eliminati
        print("\n🔍 VERIFYING CASCADE DELETION:")
        all_deleted = True
        data_counts_after = {}
        
        for table_name, record_id in test_data:
            result = supabase.table(table_name).select("id").eq("id", record_id).execute()
            count = len(result.data) if result.data else 0
            data_counts_after[table_name] = data_counts_after.get(table_name, 0) + count
            
            if count == 0:
                print(f"✅ {table_name}: Record properly deleted")
            else:
                print(f"❌ {table_name}: Record still exists! CASCADE DELETE failed!")
                all_deleted = False
        
        # 6. Verifica che workspace sia stato eliminato
        workspace_check = supabase.table("workspaces").select("id").eq("id", test_workspace_id).execute()
        workspace_exists = len(workspace_check.data) > 0 if workspace_check.data else False
        
        if not workspace_exists:
            print("✅ Workspace successfully deleted")
        else:
            print("❌ Workspace still exists!")
            all_deleted = False
        
        # 7. Riepilogo risultati
        print("\n" + "=" * 60)
        print("📊 CASCADE DELETION TEST RESULTS:")
        print("=" * 60)
        
        print(f"📁 Workspace: {'✅ DELETED' if not workspace_exists else '❌ STILL EXISTS'}")
        
        for table_name in set(item[0] for item in test_data):
            before_count = data_counts_before.get(table_name, 0)
            after_count = data_counts_after.get(table_name, 0)
            status = "✅ DELETED" if after_count == 0 else f"❌ {after_count} REMAIN"
            print(f"📋 {table_name}: {before_count} created → {status}")
        
        if all_deleted:
            print("\n🎉 SUCCESS: All cascade deletions worked correctly!")
            print("✅ No orphaned data remains in database")
        else:
            print("\n❌ FAILURE: Some data was not properly cascade deleted!")
            print("⚠️ Check foreign key constraints and CASCADE DELETE rules")
            
            # Show missing constraints
            print("\n🔧 RECOMMENDED FIXES:")
            for table_name in set(item[0] for item in test_data):
                if data_counts_after.get(table_name, 0) > 0:
                    print(f"   • Add CASCADE DELETE constraint to {table_name}.workspace_id")
        
        return all_deleted
        
    except Exception as e:
        print(f"❌ Error during cascade deletion test: {e}")
        
        # Cleanup in case of error
        try:
            print("🧹 Attempting cleanup of test data...")
            supabase.table("workspaces").delete().eq("id", test_workspace_id).execute()
            print("✅ Cleanup completed")
        except:
            print("⚠️ Manual cleanup may be required")
        
        return False

async def main():
    """Run cascade deletion test"""
    print("🚀 STARTING CASCADE DELETION TEST")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = await test_cascade_deletion()
        
        if success:
            print("\n✅ ALL TESTS PASSED!")
            print("Database cascade deletion is working correctly.")
        else:
            print("\n❌ TESTS FAILED!")
            print("Database cascade deletion needs fixes.")
            
    except Exception as e:
        print(f"\n💥 TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())