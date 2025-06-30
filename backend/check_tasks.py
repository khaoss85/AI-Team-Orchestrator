#!/usr/bin/env python3

from database import supabase
import json

# Get tasks for this workspace that might contain email sequences
workspace_id = 'bc41beb3-4380-434a-8280-92821006840e'
response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()

print(f'Found {len(response.data)} total tasks in workspace')

# Look for tasks with detailed results
tasks_with_results = []
for task in response.data:
    result = task.get('result', {})
    if result and isinstance(result, dict):
        detailed_results = result.get('detailed_results_json', {})
        if detailed_results and detailed_results != '{}':
            tasks_with_results.append(task)
            
print(f'Tasks with detailed results: {len(tasks_with_results)}')

# Check for email sequences in the detailed results
for task in tasks_with_results[:3]:  # Show first 3
    print(f'\n=== TASK: {task["name"]} ===')
    print(f'Status: {task["status"]}')
    
    result = task.get('result', {})
    detailed_results = result.get('detailed_results_json', {})
    
    if isinstance(detailed_results, str):
        try:
            detailed_data = json.loads(detailed_results)
        except:
            detailed_data = {}
    else:
        detailed_data = detailed_results
    
    # Check for email sequences
    if 'sequences' in detailed_data:
        sequences = detailed_data['sequences']
        print(f'FOUND EMAIL SEQUENCES: {len(sequences)} sequences')
        for i, seq in enumerate(sequences[:2]):  # Show first 2
            print(f'  Sequence {i+1}: {seq.get("name", "Unnamed")} (Audience: {seq.get("audience", "N/A")})')
            emails = seq.get('emails', [])
            print(f'    Emails: {len(emails)} in sequence')
            if emails:
                print(f'    First email subject: {emails[0].get("subject", "N/A")}')
    else:
        print('No email sequences found in detailed results')
        # Show what keys are available
        if detailed_data:
            print(f'Available keys: {list(detailed_data.keys())}')