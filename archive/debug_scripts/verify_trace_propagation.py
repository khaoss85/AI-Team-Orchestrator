#!/usr/bin/env python3
"""
Trace ID Propagation Verification Script
Tests end-to-end trace ID flow through the system
"""

import requests
import uuid
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TRACE_ID = str(uuid.uuid4())

def test_trace_propagation():
    """Test trace ID propagation through various endpoints"""
    
    headers = {
        "X-Trace-ID": TRACE_ID,
        "Content-Type": "application/json"
    }
    
    results = {
        "trace_id": TRACE_ID,
        "timestamp": datetime.now().isoformat(),
        "endpoints_tested": [],
        "propagation_success": [],
        "propagation_failures": []
    }
    
    # Test endpoints that should propagate trace ID
    test_endpoints = [
        ("POST", "/workspaces", {"name": "Test Workspace", "description": "Trace test"}),
        ("GET", "/workspaces", None),
        ("POST", "/api/director/analyze", {"workspace_id": "test-id"}),
        ("GET", "/api/agents", None),
        ("GET", "/api/tasks", None)
    ]
    
    for method, endpoint, data in test_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
            
            results["endpoints_tested"].append({
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code
            })
            
            # Check if trace ID is in response headers
            if "X-Trace-ID" in response.headers:
                if response.headers["X-Trace-ID"] == TRACE_ID:
                    results["propagation_success"].append(endpoint)
                else:
                    results["propagation_failures"].append({
                        "endpoint": endpoint,
                        "reason": "Different trace ID returned",
                        "returned_id": response.headers.get("X-Trace-ID")
                    })
            else:
                results["propagation_failures"].append({
                    "endpoint": endpoint,
                    "reason": "No trace ID in response"
                })
                
        except Exception as e:
            results["propagation_failures"].append({
                "endpoint": endpoint,
                "reason": f"Error: {str(e)}"
            })
    
    # Save results
    with open(f"trace_verification_{TRACE_ID[:8]}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"Trace ID Propagation Test Results")
    print(f"=================================")
    print(f"Trace ID: {TRACE_ID}")
    print(f"Endpoints tested: {len(results['endpoints_tested'])}")
    print(f"Successful propagations: {len(results['propagation_success'])}")
    print(f"Failed propagations: {len(results['propagation_failures'])}")
    
    if results['propagation_failures']:
        print("\nFailures:")
        for failure in results['propagation_failures']:
            print(f"  - {failure['endpoint']}: {failure['reason']}")
    
    return results

if __name__ == "__main__":
    test_trace_propagation()
