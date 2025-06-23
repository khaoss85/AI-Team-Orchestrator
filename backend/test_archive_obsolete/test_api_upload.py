#!/usr/bin/env python3
"""
Test API Upload directly
"""

import requests
import base64
import json

def test_api_upload():
    print("🌐 Testing API Upload Directly...\n")
    
    # Test document content
    test_content = "This is a direct API test document.\nIt should be uploaded via the documents API endpoint."
    file_data = base64.b64encode(test_content.encode()).decode('utf-8')
    
    # API endpoint
    workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    url = f"http://localhost:8000/documents/{workspace_id}/upload"
    
    payload = {
        "file_data": file_data,
        "filename": "api_test.txt",
        "sharing_scope": "team",
        "description": "Test document via direct API call",
        "tags": ["api", "test", "direct"]
    }
    
    try:
        print(f"📤 Uploading to: {url}")
        print(f"📄 Filename: {payload['filename']}")
        print(f"📊 Size: {len(test_content)} bytes")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📄 Document ID: {result['document']['id']}")
            print(f"📊 File size: {result['document']['file_size']} bytes")
            print(f"🔍 MIME type: {result['document']['mime_type']}")
            print(f"🗃️ Vector store: {result['document']['vector_store_id']}")
        else:
            print(f"❌ Upload failed: {response.text}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    test_api_upload()