#!/usr/bin/env python3
"""
Debug the exact location of 'list' object has no attribute 'get' error
"""

import asyncio
import json
import traceback
from fix_deliverable_creation import extract_concrete_deliverables_ai_driven

async def debug_ai_parsing():
    """Debug where the list/get error occurs"""
    
    # Simulate the ACTUAL AI response that's causing issues (from the log)
    test_ai_response = '''```json
[
  {
    "key": "email_sequences",
    "type": "email sequence template",
    "description": "A sequence of emails designed for outreach, including subject and body content."
  },
  {
    "key": "contacts",
    "type": "contact list",
    "description": "A list of contacts with names and email addresses for outreach."
  }
]
```'''

    # Simulate a goal
    test_goal = {
        'id': 'test-goal',
        'description': 'Create Email Sequence Templates for Outreach',
        'target_value': 1.0,
        'unit': 'deliverable'
    }
    
    # Simulate detailed_results with email sequences
    test_detailed_results = json.dumps({
        'email_sequences': [
            {
                'emails': [
                    {'subject': 'Test Subject', 'body': 'Test body content'}
                ],
                'sequence_name': 'Test Sequence'
            }
        ],
        'contacts': [
            {'name': 'Test Contact', 'email': 'test@example.com'}
        ]
    })
    
    print("🧪 Testing AI parsing with debug...")
    
    try:
        result = await extract_concrete_deliverables_ai_driven(test_detailed_results, test_goal)
        print(f"✅ Success: {len(result)} deliverables extracted")
        
        for i, item in enumerate(result):
            print(f"  {i+1}. Type: {item.get('type', 'unknown')}")
            print(f"      Name: {item.get('name', 'N/A')}")
            print(f"      Source: {item.get('source_key', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error caught: {e}")
        print("Full traceback:")
        traceback.print_exc()
        
        # Try to identify the exact line causing issues
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        if exc_traceback:
            tb_lines = traceback.format_tb(exc_traceback)
            for line in tb_lines:
                if "'list' object has no attribute 'get'" in str(exc_value):
                    print(f"\n🎯 Error location identified:")
                    print(line)

if __name__ == "__main__":
    # Ensure environment is loaded
    from dotenv import load_dotenv
    load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')
    
    asyncio.run(debug_ai_parsing())