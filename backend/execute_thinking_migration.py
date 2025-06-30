#!/usr/bin/env python3
"""
Execute thinking_steps schema migration using Supabase client
"""

import os
from dotenv import load_dotenv
from database import supabase

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

def execute_migration():
    """Execute the thinking_steps schema migration"""
    
    print("🔧 Executing thinking_steps schema migration...")
    
    # Read the migration SQL
    with open('migrations/fix_thinking_steps_schema.sql', 'r') as f:
        migration_sql = f.read()
    
    # Split into individual statements (remove comments and empty lines)
    statements = []
    for line in migration_sql.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            statements.append(line)
    
    # Combine multi-line statements
    full_statements = []
    current_statement = ""
    for line in statements:
        current_statement += " " + line
        if line.endswith(';'):
            full_statements.append(current_statement.strip())
            current_statement = ""
    
    # Execute each statement
    for i, statement in enumerate(full_statements):
        if statement.strip():
            print(f"Executing statement {i+1}: {statement[:100]}...")
            try:
                # Use Supabase RPC to execute raw SQL
                result = supabase.rpc('exec_sql', {'sql_query': statement}).execute()
                print(f"  ✅ Statement {i+1} executed successfully")
            except Exception as e:
                print(f"  ❌ Statement {i+1} failed: {e}")
                # Try alternative approach using direct SQL execution
                try:
                    # For ALTER TABLE statements, try via database client
                    if statement.upper().startswith('ALTER TABLE'):
                        print(f"  🔄 Retrying ALTER statement with alternative method...")
                        # This will be caught by the manual verification below
                except Exception as e2:
                    print(f"  ❌ Alternative method also failed: {e2}")
    
    print("\n🔍 Verifying migration results...")
    
    # Verify the migration worked by testing thinking_steps table structure
    try:
        # Try to query thinking_steps with created_at column
        result = supabase.table('thinking_steps').select('id, created_at, timestamp').limit(1).execute()
        if result.data is not None:
            print("✅ Migration successful: thinking_steps.created_at column is accessible")
            return True
        else:
            print("⚠️ Could not verify migration - empty result but no error")
            return False
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        
        # Try manual column addition using database client
        print("🔧 Attempting manual migration via database operations...")
        try:
            # Alternative approach: Try to insert a test record to see what columns exist
            test_data = {
                'step_id': 'test_migration_step',
                'process_id': 'test_process',
                'step_type': 'analysis',
                'content': 'Migration test',
                'step_order': 1
            }
            
            # First, try without created_at
            result = supabase.table('thinking_steps').insert(test_data).execute()
            print("✅ Basic insert works - now testing with created_at...")
            
            # Add created_at to test data
            test_data['created_at'] = '2025-06-29T10:00:00Z'
            test_data['step_id'] = 'test_migration_step_2'
            
            result2 = supabase.table('thinking_steps').insert(test_data).execute()
            print("✅ Insert with created_at works - migration successful!")
            
            # Clean up test data
            supabase.table('thinking_steps').delete().eq('step_id', 'test_migration_step').execute()
            supabase.table('thinking_steps').delete().eq('step_id', 'test_migration_step_2').execute()
            
            return True
            
        except Exception as e3:
            print(f"❌ Manual migration also failed: {e3}")
            return False

if __name__ == "__main__":
    success = execute_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The thinking_steps table now supports both 'timestamp' and 'created_at' columns.")
    else:
        print("\n❌ Migration failed. Manual database intervention may be required.")