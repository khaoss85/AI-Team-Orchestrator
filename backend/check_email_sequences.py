#!/usr/bin/env python3

from database import supabase
import json

# Get the email sequences task
workspace_id = 'bc41beb3-4380-434a-8280-92821006840e'
response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('name', 'Write 3 Email Sequences for Outreach').execute()

if response.data:
    task = response.data[0]
    print(f'Task: {task["name"]}')
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
    
    # Check email_sequences key
    if 'email_sequences' in detailed_data:
        sequences = detailed_data['email_sequences']
        print(f'\nFOUND EMAIL SEQUENCES: {len(sequences)} sequences')
        
        for i, seq in enumerate(sequences):
            print(f'\n--- Sequence {i+1}: {seq.get("name", "Unnamed")} ---')
            print(f'Audience: {seq.get("audience", "N/A")}')
            print(f'Purpose: {seq.get("purpose", "N/A")}')
            
            emails = seq.get('emails', [])
            print(f'Number of emails: {len(emails)}')
            
            # Show first email details
            if emails:
                first_email = emails[0]
                print(f'\nFirst Email:')
                print(f'  Subject: {first_email.get("subject", "N/A")}')
                print(f'  Preview: {first_email.get("body", "")[:100]}...')
else:
    print('Email sequences task not found')