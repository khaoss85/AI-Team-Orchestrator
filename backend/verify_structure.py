#!/usr/bin/env python3
"""
Verify that all conversational AI files exist and have correct structure
"""

import os
from pathlib import Path

def verify_files():
    """Verify all conversational AI files exist"""
    
    print("🔍 Verifying Conversational AI File Structure...")
    
    backend_dir = Path(__file__).parent
    
    # Required files
    required_files = [
        "ai_agents/conversational.py",
        "ai_agents/conversational_tools.py", 
        "utils/context_manager.py",
        "utils/confirmation_manager.py",
        "utils/ambiguity_resolver.py",
        "utils/versioning_manager.py",
        "routes/conversation.py",
        "CONVERSATIONAL_AI_DATABASE_SCHEMA.sql",
        "VERSIONING_DATABASE_SCHEMA.sql"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} (MISSING)")
    
    print(f"\n📊 File Structure Summary:")
    print(f"   ✅ Existing: {len(existing_files)}")
    print(f"   ❌ Missing: {len(missing_files)}")
    
    return len(missing_files) == 0

def check_file_contents():
    """Check that files have expected content"""
    
    print("\n🔍 Checking File Contents...")
    
    backend_dir = Path(__file__).parent
    
    checks = [
        ("ai_agents/conversational.py", "class ConversationalAgent"),
        ("ai_agents/conversational_tools.py", "class ConversationalToolRegistry"),
        ("utils/context_manager.py", "class ConversationContextManager"),
        ("utils/confirmation_manager.py", "class ConfirmationManager"),
        ("utils/ambiguity_resolver.py", "class AmbiguityResolver"),
        ("utils/versioning_manager.py", "class VersioningManager"),
        ("routes/conversation.py", "@router.post"),
        ("CONVERSATIONAL_AI_DATABASE_SCHEMA.sql", "CREATE TABLE IF NOT EXISTS conversations"),
    ]
    
    all_good = True
    
    for file_path, expected_content in checks:
        full_path = backend_dir / file_path
        if full_path.exists():
            try:
                content = full_path.read_text()
                if expected_content in content:
                    print(f"   ✅ {file_path} - Contains expected content")
                else:
                    print(f"   ❌ {file_path} - Missing expected content: {expected_content}")
                    all_good = False
            except Exception as e:
                print(f"   ❌ {file_path} - Error reading: {e}")
                all_good = False
        else:
            print(f"   ❌ {file_path} - File not found")
            all_good = False
    
    return all_good

def check_main_integration():
    """Check if conversation router is integrated in main.py"""
    
    print("\n🔍 Checking main.py Integration...")
    
    backend_dir = Path(__file__).parent
    main_file = backend_dir / "main.py"
    
    if not main_file.exists():
        print("   ❌ main.py not found")
        return False
    
    try:
        content = main_file.read_text()
        
        checks = [
            ("from routes.conversation import router as conversation_router", "Import statement"),
            ("app.include_router(conversation_router)", "Router registration")
        ]
        
        all_integrated = True
        
        for check_text, description in checks:
            if check_text in content:
                print(f"   ✅ {description} found")
            else:
                print(f"   ❌ {description} missing")
                all_integrated = False
        
        return all_integrated
        
    except Exception as e:
        print(f"   ❌ Error reading main.py: {e}")
        return False

def check_database_tables():
    """Check if all required database tables are defined"""
    
    print("\n🔍 Checking Database Schema...")
    
    backend_dir = Path(__file__).parent
    
    schema_files = [
        ("CONVERSATIONAL_AI_DATABASE_SCHEMA.sql", [
            "conversations",
            "conversation_messages", 
            "pending_confirmations",
            "agent_knowledge",
            "workflow_automations"
        ]),
        ("VERSIONING_DATABASE_SCHEMA.sql", [
            "component_versions",
            "version_migrations",
            "conversation_backups",
            "version_compatibility"
        ])
    ]
    
    all_tables_defined = True
    
    for schema_file, expected_tables in schema_files:
        file_path = backend_dir / schema_file
        if file_path.exists():
            try:
                content = file_path.read_text()
                print(f"   📄 {schema_file}:")
                
                for table in expected_tables:
                    if f"CREATE TABLE IF NOT EXISTS {table}" in content:
                        print(f"      ✅ {table}")
                    else:
                        print(f"      ❌ {table} (MISSING)")
                        all_tables_defined = False
                        
            except Exception as e:
                print(f"   ❌ Error reading {schema_file}: {e}")
                all_tables_defined = False
        else:
            print(f"   ❌ {schema_file} not found")
            all_tables_defined = False
    
    return all_tables_defined

def main():
    """Run all verification checks"""
    
    print("🚀 Conversational AI Structure Verification\n")
    
    checks = [
        ("File Structure", verify_files),
        ("File Contents", check_file_contents),
        ("Main.py Integration", check_main_integration),
        ("Database Schema", check_database_tables)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {check_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All verification checks passed!")
        print("📋 Ready for database setup:")
        print("   1. Execute CONVERSATIONAL_AI_DATABASE_SCHEMA.sql in Supabase")
        print("   2. Execute VERSIONING_DATABASE_SCHEMA.sql in Supabase")
        print("   3. Start the backend server")
        print("   4. Test the conversational UI")
    else:
        print("\n⚠️ Some checks failed. Review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()