import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Check if there's any data in the usage history table
result = supabase.table('openai_usage_history').select('*').order('created_at', desc=True).limit(10).execute()
print(f'Total recent records in openai_usage_history: {len(result.data)}')
if result.data:
    for record in result.data:
        print(f"  - {record.get('created_at')}: Cost=${record.get('total_cost', 0)}, Tokens={record.get('total_tokens', 0)}, Model={record.get('model', 'unknown')}")
else:
    print('No usage history records found')

# Check workspace-specific usage
workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
ws_result = supabase.table('openai_usage_history').select('*').eq('workspace_id', workspace_id).order('created_at', desc=True).limit(5).execute()
print(f'\nWorkspace {workspace_id} records: {len(ws_result.data)}')
if ws_result.data:
    for record in ws_result.data:
        print(f"  - {record.get('created_at')}: Cost=${record.get('total_cost', 0)}, Tokens={record.get('total_tokens', 0)}")