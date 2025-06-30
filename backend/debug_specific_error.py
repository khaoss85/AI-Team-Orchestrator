#!/usr/bin/env python3
"""
Debug the specific list/get error by simulating the exact AI response
"""

import asyncio
import json
import traceback
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def debug_specific_error():
    """Debug the exact case where list.get() fails"""
    
    # Simulate the exact AI response that causes the error
    ai_response = '''```json
[
    {
        "key": "email_sequences",
        "type": "email_sequence",
        "description": "A series of emails designed for outreach regarding automation solutions, including introductory, follow-up, and closing emails."
    }
]
```'''
    
    # Simulate detailed_data
    detailed_data = {
        "email_sequences": [
            {"subject": "Test", "body": "Test content"}
        ],
        "contacts": [
            {"name": "Test", "email": "test@example.com"}
        ]
    }
    
    # Simulate goal
    goal = {
        'id': 'test-goal',
        'description': 'Create Email Sequence Templates for Outreach',
        'target_value': 1.0,
        'unit': 'deliverable'
    }
    
    print("🧪 Testing specific error case...")
    print(f"AI Response: {ai_response}")
    
    try:
        # Parse AI response manually to trace the error
        clean_response = ai_response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        print(f"Cleaned response: {clean_response}")
        
        ai_analysis = json.loads(clean_response)
        print(f"Parsed AI analysis type: {type(ai_analysis)}")
        print(f"AI analysis content: {ai_analysis}")
        
        concrete_deliverables = []
        
        # This is where the error occurs - let's trace it step by step
        if isinstance(ai_analysis, list):
            print(f"✅ AI analysis is a list with {len(ai_analysis)} items")
            
            for i, item in enumerate(ai_analysis):
                print(f"Processing item {i}: {item} (type: {type(item)})")
                
                if isinstance(item, dict):
                    print(f"  ✅ Item {i} is a dict")
                    
                    # This is where the error should occur if there's a bug
                    key = item.get('key')
                    print(f"  Key extracted: {key}")
                    
                    deliverable_type = item.get('type', 'unknown')
                    print(f"  Type extracted: {deliverable_type}")
                    
                    if key and key in detailed_data:
                        print(f"  ✅ Key '{key}' found in detailed_data")
                        deliverable_data = detailed_data[key]
                        print(f"  Deliverable data type: {type(deliverable_data)}")
                        
                        # Structure the deliverable based on type
                        if isinstance(deliverable_data, list) and deliverable_data:
                            print(f"  ✅ Creating list deliverable")
                            concrete_deliverables.append({
                                'type': deliverable_type,
                                'name': item.get('description', f'{deliverable_type.title()} Content'),
                                'data': deliverable_data,
                                'source_key': key
                            })
                        elif isinstance(deliverable_data, dict) and deliverable_data:
                            print(f"  ✅ Creating dict deliverable")
                            concrete_deliverables.append({
                                'type': deliverable_type,
                                'name': item.get('description', f'{deliverable_type.title()} Content'),
                                'data': deliverable_data,
                                'source_key': key
                            })
                    else:
                        print(f"  ❌ Key '{key}' not found in detailed_data or key is None")
                else:
                    print(f"  ❌ Item {i} is not a dict: {type(item)}")
        else:
            print(f"❌ AI analysis is not a list: {type(ai_analysis)}")
        
        print(f"✅ Successfully created {len(concrete_deliverables)} deliverables")
        for i, deliverable in enumerate(concrete_deliverables):
            print(f"  {i+1}. {deliverable}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_specific_error())