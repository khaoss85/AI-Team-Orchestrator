import asyncio
import aiohttp
import json

async def quick_test():
    base_url = 'http://localhost:8000'
    
    # Create workspace
    async with aiohttp.ClientSession() as session:
        workspace_data = {
            'name': 'Quick Test Workspace',
            'description': 'Testing task completion'
        }
        
        async with session.post(f'{base_url}/api/workspaces/', json=workspace_data) as resp:
            if resp.status != 201:
                print(f'Failed to create workspace: {resp.status}')
                return
            workspace = await resp.json()
            workspace_id = workspace['id']
            print(f'✅ Created workspace: {workspace_id}')

        # Create goal
        goal_data = {
            'workspace_id': workspace_id,
            'metric_type': 'completion_percentage',
            'target_value': 90.0,
            'priority': 1,
            'description': 'Quick test goal'
        }
        
        async with session.post(f'{base_url}/api/workspaces/{workspace_id}/goals', json=goal_data) as resp:
            if resp.status != 200:
                print(f'Failed to create goal: {resp.status}')
                return
            print('✅ Created goal')

        # Trigger team proposal
        proposal_data = {'workspace_id': workspace_id}
        async with session.post(f'{base_url}/api/director/proposal', json=proposal_data) as resp:
            if resp.status != 200:
                print(f'Failed to create proposal: {resp.status}')
                return
            proposal = await resp.json()
            proposal_id = proposal['proposal_id']
            print(f'✅ Created proposal: {proposal_id}')

        # Approve proposal
        await asyncio.sleep(1)
        async with session.post(f'{base_url}/api/director/approve/{workspace_id}?proposal_id={proposal_id}') as resp:
            if resp.status != 200:
                print(f'Failed to approve proposal: {resp.status}')
                return
            print('✅ Approved proposal')

        # Wait and check tasks multiple times
        for i in range(3):
            await asyncio.sleep(20)
            async with session.get(f'{base_url}/api/workspaces/{workspace_id}/tasks') as resp:
                if resp.status == 200:
                    tasks = await resp.json()
                    print(f'📋 Check {i+1} - Tasks: {len(tasks)} total')
                    for status in ['pending', 'in_progress', 'completed', 'failed']:
                        count = len([t for t in tasks if t['status'] == status])
                        print(f'  {status}: {count}')
                    
                    completed = len([t for t in tasks if t['status'] == 'completed'])
                    if completed > 0:
                        print(f'🎉 SUCCESS! {completed} tasks completed!')
                        break
                else:
                    print(f'Failed to get tasks: {resp.status}')

if __name__ == "__main__":
    asyncio.run(quick_test())