#!/usr/bin/env python3
"""
Execute Migration 013 using alternative methods
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

def try_execute_with_psql():
    """Try to execute migration using psql with Supabase connection"""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not supabase_url or "supabase.co" not in supabase_url:
        logger.error("❌ Invalid or missing SUPABASE_URL")
        return False
    
    # Extract project reference from URL
    # Format: https://xyz.supabase.co -> xyz
    project_ref = supabase_url.split("//")[1].split(".")[0]
    
    # Construct database connection details
    db_host = f"{project_ref}.db.supabase.co"
    db_port = "5432"
    db_name = "postgres"
    db_user = "postgres"
    
    print(f"🔗 Attempting connection to: {db_host}:{db_port}")
    print("⚠️  You will be prompted for the database password")
    print("   (This is the 'Password' from your Supabase Dashboard > Settings > Database)")
    
    # Path to SQL file
    sql_file = backend_dir / "temp_migration_013.sql"
    
    if not sql_file.exists():
        logger.error(f"❌ SQL file not found: {sql_file}")
        return False
    
    # Construct psql command
    psql_command = [
        "psql",
        f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}",
        "-f", str(sql_file),
        "-v", "ON_ERROR_STOP=1"  # Stop on first error
    ]
    
    logger.info("🔄 Executing migration with psql...")
    logger.info(f"Command: {' '.join(psql_command[:-2])} -f [migration_file]")
    
    try:
        result = subprocess.run(psql_command, 
                              capture_output=True, 
                              text=True, 
                              timeout=120)
        
        if result.returncode == 0:
            logger.info("✅ Migration executed successfully!")
            logger.info("Output:")
            print(result.stdout)
            return True
        else:
            logger.error("❌ Migration failed!")
            logger.error("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Migration timed out after 2 minutes")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ psql command failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def try_supabase_cli():
    """Try to execute migration using Supabase CLI"""
    
    sql_file = backend_dir / "temp_migration_013.sql"
    
    if not sql_file.exists():
        logger.error(f"❌ SQL file not found: {sql_file}")
        return False
    
    # Try different Supabase CLI commands
    cli_commands = [
        ["supabase", "db", "remote", "commit"],
        ["supabase", "db", "push"],
        ["supabase", "migration", "up"]
    ]
    
    logger.info("🔄 Trying Supabase CLI approaches...")
    
    for cmd in cli_commands:
        try:
            logger.info(f"Trying: {' '.join(cmd)}")
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=60,
                                  cwd=backend_dir)
            
            if result.returncode == 0:
                logger.info(f"✅ Command succeeded: {' '.join(cmd)}")
                return True
            else:
                logger.warning(f"⚠️ Command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Command timed out: {' '.join(cmd)}")
        except Exception as e:
            logger.warning(f"⚠️ Command error: {e}")
    
    return False

def manual_migration_instructions():
    """Provide detailed manual migration instructions"""
    
    print("\n" + "="*80)
    print("📋 MANUAL MIGRATION INSTRUCTIONS")
    print("="*80)
    
    print("\n🌐 OPTION 1: Supabase Dashboard (Recommended)")
    print("1. Go to your Supabase Dashboard")
    print("2. Navigate to the SQL Editor tab")
    print("3. Click 'New Query'")
    print("4. Copy the SQL from: temp_migration_013.sql")
    print("5. Paste it into the editor")
    print("6. Click 'Run' to execute the migration")
    
    print("\n🖥️  OPTION 2: Local psql with connection string")
    print("1. Get your database password from Supabase Dashboard > Settings > Database")
    print("2. Copy the connection string from the same page")
    print("3. Run: psql 'your-connection-string' -f temp_migration_013.sql")
    
    print("\n🔧 OPTION 3: Database GUI tool")
    print("1. Use pgAdmin, DBeaver, or similar tool")
    print("2. Connect using credentials from Supabase Dashboard")
    print("3. Execute the SQL from temp_migration_013.sql")
    
    print("\n✅ VALIDATION")
    print("After executing the migration, run:")
    print("   python3 apply_migration_013.py")
    print("to validate that all columns were added successfully.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    logger.info("🚀 Attempting to execute Migration 013...")
    
    success = False
    
    # Try psql approach first
    print("\n🔄 Method 1: Direct psql connection")
    try:
        success = try_execute_with_psql()
    except KeyboardInterrupt:
        print("\n⚠️ User cancelled psql connection")
    
    # If psql failed, try Supabase CLI
    if not success:
        print("\n🔄 Method 2: Supabase CLI")
        success = try_supabase_cli()
    
    # If both failed, provide manual instructions
    if not success:
        print("\n📋 Method 3: Manual execution required")
        manual_migration_instructions()
        
        # Check if migration was already applied manually
        print("\n🔍 Checking if migration was applied manually...")
        from apply_migration_013 import validate_migration
        if validate_migration():
            print("✅ Migration already applied successfully!")
            success = True
    
    if success:
        logger.info("🎉 Migration 013 completed successfully!")
    else:
        logger.info("📋 Please apply the migration manually using the instructions above.")
        
    sys.exit(0 if success else 1)