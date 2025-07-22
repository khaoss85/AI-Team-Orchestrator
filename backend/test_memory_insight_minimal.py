#!/usr/bin/env python3
"""
Test minimo per verificare la memorizzazione degli insights
"""

import asyncio
import json
import uuid
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import add_memory_insight

async def test_memory_insight():
    """Test minimal memory insight storage"""
    print("🧠 Testing memory insight storage...")
    
    # Test data
    test_workspace_id = str(uuid.uuid4())
    
    # Try minimal valid content
    valid_content = {
        "type": "progress_update",
        "status": "completed",
        "message": "Test execution completed successfully"
    }
    
    try:
        result = await add_memory_insight(
            workspace_id=test_workspace_id,
            insight_type="discovery",
            content=json.dumps(valid_content, indent=2),
            agent_role="learning_system"
        )
        
        if result:
            print("✅ Memory insight stored successfully!")
            print(f"Result: {result}")
            return True
        else:
            print("❌ Memory insight storage returned None")
            return False
            
    except Exception as e:
        print(f"❌ Memory insight storage failed: {e}")
        return False

async def main():
    success = await test_memory_insight()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)