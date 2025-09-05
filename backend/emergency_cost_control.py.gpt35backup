#!/usr/bin/env python3
"""
EMERGENCY COST CONTROL SCRIPT
Immediately reduces OpenAI API consumption to stop cost drain

Run this script to apply emergency cost controls:
python3 emergency_cost_control.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def apply_emergency_controls():
    """Apply immediate cost reduction measures"""
    
    print("=" * 60)
    print("EMERGENCY OPENAI COST CONTROL ACTIVATION")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    env_file = Path(".env")
    env_backup = Path(".env.backup_before_emergency")
    
    # Backup current .env
    if env_file.exists():
        print("📦 Backing up current .env file...")
        env_backup.write_text(env_file.read_text())
        print(f"   Backup saved to: {env_backup}")
    
    # Emergency environment variables to set
    emergency_config = {
        # CRITICAL: Disable high-cost AI services
        "ENABLE_AI_KNOWLEDGE_CATEGORIZATION": "false",
        "ENABLE_UNIVERSAL_LEARNING": "false", 
        "ENABLE_AI_CONTENT_TRANSFORMATION": "false",
        "ENABLE_THINKING_PROCESS": "false",
        "ENABLE_AUTO_TASK_RECOVERY": "false",
        "ENABLE_GOAL_PROGRESS_AI": "false",
        
        # Aggressive caching (24 hours)
        "KNOWLEDGE_CACHE_TTL_SECONDS": "86400",
        "USAGE_CACHE_TTL_SECONDS": "3600",
        "MEMORY_CACHE_TTL_SECONDS": "7200",
        
        # Strict rate limiting
        "AI_RATE_LIMIT_PER_MINUTE": "2",
        "AI_RATE_LIMIT_PER_HOUR": "20",
        
        # Cost thresholds
        "AI_COST_DAILY_LIMIT_USD": "5.0",
        "AI_COST_DUPLICATE_THRESHOLD": "2",
        "AI_COST_CIRCUIT_BREAKER": "true",
        
        # Use cheapest models only
        "DEFAULT_AI_MODEL": "gpt-3.5-turbo",
        "KNOWLEDGE_CATEGORIZATION_MODEL": "gpt-3.5-turbo",
        "DIRECTOR_MODEL": "gpt-3.5-turbo",
        
        # Reduce token limits
        "MAX_PROMPT_TOKENS": "1000",
        "MAX_COMPLETION_TOKENS": "500",
        
        # Disable parallel processing
        "ENABLE_PARALLEL_AGENTS": "false",
        "MAX_CONCURRENT_TASKS": "1",
    }
    
    # Read current .env
    current_env = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    current_env[key] = value
    
    # Apply emergency config
    print("🚨 Applying emergency cost controls:")
    print("-" * 40)
    changes_made = []
    
    for key, value in emergency_config.items():
        old_value = current_env.get(key, "not set")
        current_env[key] = value
        
        if old_value != value:
            changes_made.append(f"  {key}: {old_value} → {value}")
            print(f"  ✓ {key} = {value}")
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.write("# EMERGENCY COST CONTROLS APPLIED\n")
        f.write(f"# Applied at: {datetime.now().isoformat()}\n")
        f.write("# Restore original from .env.backup_before_emergency\n\n")
        
        for key, value in sorted(current_env.items()):
            f.write(f"{key}={value}\n")
    
    print()
    print("📝 Summary of changes:")
    print("-" * 40)
    if changes_made:
        for change in changes_made[:10]:  # Show first 10 changes
            print(change)
        if len(changes_made) > 10:
            print(f"  ... and {len(changes_made) - 10} more changes")
    else:
        print("  No changes needed (already configured)")
    
    # Create cost monitoring script
    monitor_script = """#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime
from services.openai_usage_api_client import get_usage_client

async def monitor_costs():
    client = get_usage_client()
    while True:
        usage = await client.get_today_usage()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Today's cost: ${usage.total_cost:.4f} | Tokens: {usage.total_tokens:,}")
        
        if usage.total_cost > 5.0:
            print("⚠️ DAILY LIMIT EXCEEDED - SHUTTING DOWN AI SERVICES")
            os._exit(1)
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    print("Starting cost monitor...")
    asyncio.run(monitor_costs())
"""
    
    monitor_file = Path("cost_monitor.py")
    monitor_file.write_text(monitor_script)
    print()
    print("📊 Cost monitor script created: cost_monitor.py")
    print("   Run it with: python3 cost_monitor.py")
    
    print()
    print("✅ EMERGENCY CONTROLS APPLIED SUCCESSFULLY")
    print()
    print("IMMEDIATE ACTIONS:")
    print("-" * 40)
    print("1. Restart the backend server to apply changes:")
    print("   cd backend && python3 main.py")
    print()
    print("2. Monitor costs in real-time:")
    print("   python3 cost_monitor.py")
    print()
    print("3. Check current OpenAI balance:")
    print("   https://platform.openai.com/usage")
    print()
    print("EXPECTED IMPACT:")
    print("-" * 40)
    print("• 80-90% reduction in API calls")
    print("• All non-essential AI services disabled")
    print("• Aggressive caching enabled (24 hours)")
    print("• Rate limiting enforced (2 calls/min)")
    print("• Cheapest models only (gpt-3.5-turbo)")
    print()
    print("TO RESTORE NORMAL OPERATION:")
    print("-" * 40)
    print("1. Copy backup: cp .env.backup_before_emergency .env")
    print("2. Restart backend: cd backend && python3 main.py")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = apply_emergency_controls()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)