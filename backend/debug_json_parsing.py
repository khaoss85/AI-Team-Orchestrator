#!/usr/bin/env python3
"""
Debug the JSON parsing issue in AI content extraction
"""

import json

# Test the exact AI response that's causing issues
test_response = '''```json
[
  {
    "key": "email_sequences",
    "type": "email_sequence_template",
    "description": "A series of email templates for outreach focused on automation solutions, including introductory, follow-up, and closing emails."
  }
]
```'''

print("Original response:")
print(repr(test_response))

# Clean up markdown code blocks if present
clean_response = test_response.strip()
if clean_response.startswith('```json'):
    clean_response = clean_response[7:]
if clean_response.endswith('```'):
    clean_response = clean_response[:-3]
clean_response = clean_response.strip()

print("\nCleaned response:")
print(repr(clean_response))

try:
    ai_analysis = json.loads(clean_response)
    print(f"\nParsed successfully: {type(ai_analysis)}")
    print(f"Content: {ai_analysis}")
    
    if isinstance(ai_analysis, list):
        print("Processing as list...")
        for item in ai_analysis:
            print(f"Item type: {type(item)}")
            if isinstance(item, dict):
                print(f"Item keys: {item.keys()}")
                print(f"Key: {item.get('key')}")
                print(f"Type: {item.get('type')}")
            else:
                print(f"⚠️ Item is not a dict: {item}")
    elif isinstance(ai_analysis, dict):
        print("Processing as dict...")
        print(f"Keys: {ai_analysis.keys()}")
    
except json.JSONDecodeError as e:
    print(f"JSON parsing failed: {e}")
except Exception as e:
    print(f"Other error: {e}")
    import traceback
    traceback.print_exc()