#!/usr/bin/env python3
"""
Fix deliverable creation for completed goals
Forces deliverable generation when goals are 100% complete but no deliverables exist
"""
import asyncio
import logging
import json
import os
from database import supabase
from uuid import UUID

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def find_semantically_related_tasks(goal: dict, all_tasks: list) -> list:
    """
    AI-DRIVEN semantic task-goal matching (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
    Uses AI to understand task-goal relationships instead of hard-coded keywords
    """
    # Check if AI task similarity is enabled
    enable_ai_task_similarity = os.getenv("ENABLE_AI_TASK_SIMILARITY", "true").lower() == "true"
    
    if not enable_ai_task_similarity:
        logger.info("🔄 AI task similarity disabled, using fallback direct matching")
        return await find_tasks_by_direct_matching(goal, all_tasks)
    
    try:
        # Import AI components for semantic analysis
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        goal_description = goal.get('description', '')
        goal_unit = goal.get('unit', '')
        goal_context = f"Goal: {goal_description} (Target: {goal['target_value']} {goal_unit})"
        
        # Analyze up to 20 tasks with results to avoid token limits
        tasks_with_results = [t for t in all_tasks if t.get('result') and isinstance(t.get('result'), dict)][:20]
        
        if not tasks_with_results:
            logger.warning("No tasks with results found for semantic matching")
            return await find_tasks_by_direct_matching(goal, all_tasks)
        
        # Create task summaries for AI analysis
        task_summaries = []
        for i, task in enumerate(tasks_with_results):
            task_info = f"Task {i}: {task.get('name', 'Unnamed')} - {task.get('result', {}).get('summary', 'No summary')}"
            task_summaries.append(task_info)
        
        # AI semantic analysis prompt
        prompt = f"""You are analyzing which tasks are semantically related to a specific goal.

GOAL CONTEXT:
{goal_context}

AVAILABLE TASKS:
{chr(10).join(task_summaries)}

INSTRUCTIONS:
1. Identify tasks that semantically contribute to achieving the goal
2. Consider indirect relationships (e.g., research tasks that enable deliverables)
3. Ignore meta-tasks that don't produce concrete outputs
4. Return ONLY the task numbers (0-{len(task_summaries)-1}) as a comma-separated list
5. If no tasks relate to the goal, return "NONE"

RELATED TASK NUMBERS:"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"🤖 AI semantic analysis result: {ai_response}")
        
        if ai_response == "NONE":
            logger.info("AI found no semantically related tasks")
            return []
        
        # Parse AI response to get task indices
        try:
            task_indices = [int(x.strip()) for x in ai_response.split(',') if x.strip().isdigit()]
            related_tasks = [tasks_with_results[i] for i in task_indices if 0 <= i < len(tasks_with_results)]
            
            logger.info(f"✅ AI found {len(related_tasks)} semantically related tasks")
            return related_tasks
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}, using fallback")
            return await find_tasks_by_direct_matching(goal, all_tasks)
            
    except Exception as e:
        logger.warning(f"AI semantic matching failed: {e}, using fallback")
        return await find_tasks_by_direct_matching(goal, all_tasks)

async def find_tasks_by_direct_matching(goal: dict, all_tasks: list) -> list:
    """
    Fallback method: Direct goal ID matching when AI is unavailable
    """
    goal_id = goal['id']
    related_tasks = []
    
    for task in all_tasks:
        # Check for direct goal ID references
        if goal_id in str(task.get('description', '')) or goal_id in str(task.get('metadata', {})):
            related_tasks.append(task)
    
    logger.info(f"🔄 Fallback matching found {len(related_tasks)} directly related tasks")
    return related_tasks

async def extract_concrete_deliverables_ai_driven(detailed_results: str, goal: dict) -> list:
    """
    AI-DRIVEN dynamic deliverable extraction (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
    Uses AI to identify and extract any concrete deliverable content from task results
    """
    if not detailed_results or detailed_results == '{}':
        return []
    
    # Check if AI fake detection is enabled
    enable_ai_fake_detection = os.getenv("ENABLE_AI_FAKE_DETECTION", "true").lower() == "true"
    
    if not enable_ai_fake_detection:
        logger.info("🔄 AI content extraction disabled, using fallback static parsing")
        return extract_deliverables_static_fallback(detailed_results)
    
    try:
        # Parse JSON data
        if isinstance(detailed_results, str):
            detailed_data = json.loads(detailed_results)
        else:
            detailed_data = detailed_results
        
        # Import AI components for content analysis
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        goal_description = goal.get('description', '')
        goal_context = f"Goal: {goal_description}"
        
        # Prepare data summary for AI analysis
        data_keys = list(detailed_data.keys()) if isinstance(detailed_data, dict) else []
        data_preview = json.dumps(detailed_data, indent=2)[:1000]  # First 1000 chars
        
        # AI content analysis prompt
        prompt = f"""You are analyzing task result data to extract concrete deliverables.

GOAL CONTEXT:
{goal_context}

AVAILABLE DATA KEYS:
{data_keys}

DATA PREVIEW:
{data_preview}

INSTRUCTIONS:
1. Identify which data keys contain concrete, actionable deliverables
2. Look for structured content like: email sequences, contact lists, templates, documents, code, etc.
3. Ignore meta-data, logs, or placeholder content
4. For each concrete deliverable found, return JSON format:
   {{"key": "data_key_name", "type": "deliverable_type", "description": "brief_description"}}
5. If no concrete deliverables found, return: {{"none": true}}

CONCRETE DELIVERABLES:"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"🤖 AI content analysis result: {ai_response}")
        
        # Parse AI response to extract deliverables (handle markdown code blocks)
        try:
            # Clean up markdown code blocks if present
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            ai_analysis = json.loads(clean_response)
            
            # Check for 'none' response only if it's a dict (not a list)
            if isinstance(ai_analysis, dict) and ai_analysis.get('none'):
                logger.info("AI found no concrete deliverables")
                return []
            
            concrete_deliverables = []
            
            # Process AI-identified deliverable keys
            if isinstance(ai_analysis, list):
                for item in ai_analysis:
                    if isinstance(item, dict):
                        key = item.get('key')
                        deliverable_type = item.get('type', 'unknown')
                        
                        if key and key in detailed_data:
                            deliverable_data = detailed_data[key]
                            
                            # Structure the deliverable based on type
                            if isinstance(deliverable_data, list) and deliverable_data:
                                concrete_deliverables.append({
                                    'type': deliverable_type,
                                    'name': item.get('description', f'{deliverable_type.title()} Content'),
                                    'data': deliverable_data,
                                    'source_key': key
                                })
                            elif isinstance(deliverable_data, dict) and deliverable_data:
                                concrete_deliverables.append({
                                    'type': deliverable_type,
                                    'name': item.get('description', f'{deliverable_type.title()} Content'),
                                    'data': deliverable_data,
                                    'source_key': key
                                })
            elif isinstance(ai_analysis, dict):
                # Handle single deliverable object
                key = ai_analysis.get('key')
                deliverable_type = ai_analysis.get('type', 'unknown')
                
                if key and key in detailed_data:
                    deliverable_data = detailed_data[key]
                    
                    if isinstance(deliverable_data, (list, dict)) and deliverable_data:
                        concrete_deliverables.append({
                            'type': deliverable_type,
                            'name': ai_analysis.get('description', f'{deliverable_type.title()} Content'),
                            'data': deliverable_data,
                            'source_key': key
                        })
            
            logger.info(f"✅ AI extracted {len(concrete_deliverables)} concrete deliverables")
            return concrete_deliverables
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI analysis JSON: {e}, using fallback")
            return extract_deliverables_static_fallback(detailed_results)
            
    except Exception as e:
        logger.warning(f"AI content extraction failed: {e}, using fallback")
        return extract_deliverables_static_fallback(detailed_results)

def extract_deliverables_static_fallback(detailed_results: str) -> list:
    """
    Fallback method: Static parsing when AI is unavailable
    Only checks for very common structures to maintain some domain agnosticism
    """
    try:
        if isinstance(detailed_results, str):
            detailed_data = json.loads(detailed_results)
        else:
            detailed_data = detailed_results
        
        concrete_deliverables = []
        
        # Very generic checks for common data structures
        for key, value in detailed_data.items():
            if isinstance(value, list) and value:
                # Generic list-based deliverable
                concrete_deliverables.append({
                    'type': 'structured_list',
                    'name': f'{key.title()} List',
                    'data': value,
                    'source_key': key
                })
            elif isinstance(value, dict) and value:
                # Generic dict-based deliverable
                concrete_deliverables.append({
                    'type': 'structured_data',
                    'name': f'{key.title()} Data',
                    'data': value,
                    'source_key': key
                })
        
        logger.info(f"🔄 Fallback extracted {len(concrete_deliverables)} generic deliverables")
        return concrete_deliverables
        
    except Exception as e:
        logger.warning(f"Static fallback extraction failed: {e}")
        return []

async def filter_deliverables_by_goal_relevance(deliverables: list, goal: dict) -> list:
    """
    AI-DRIVEN goal-specific deliverable filtering (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
    Uses AI to filter deliverables that are specifically relevant to the goal
    """
    if not deliverables:
        return []
    
    # Check if AI fake detection is enabled
    enable_ai_fake_detection = os.getenv("ENABLE_AI_FAKE_DETECTION", "true").lower() == "true"
    
    if not enable_ai_fake_detection:
        logger.info("🔄 AI filtering disabled, returning all deliverables")
        return deliverables
    
    try:
        # Import AI components for relevance analysis
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        goal_description = goal.get('description', '')
        goal_unit = goal.get('unit', '')
        goal_context = f"Goal: {goal_description} (Target: {goal['target_value']} {goal_unit})"
        
        # Create deliverable summaries for AI analysis
        deliverable_summaries = []
        for i, deliverable in enumerate(deliverables):
            deliverable_type = deliverable.get('type', 'unknown')
            deliverable_name = deliverable.get('name', 'Unnamed')
            source_key = deliverable.get('source_key', '')
            
            # Get data preview
            data = deliverable.get('data', {})
            if isinstance(data, list):
                data_info = f"List with {len(data)} items"
                if data and isinstance(data[0], dict):
                    data_info += f", first item keys: {list(data[0].keys())[:3]}"
            elif isinstance(data, dict):
                data_info = f"Object with keys: {list(data.keys())[:5]}"
            else:
                data_info = "Simple data"
            
            summary = f"Deliverable {i}: Type='{deliverable_type}', Name='{deliverable_name}', Source='{source_key}', Data={data_info}"
            deliverable_summaries.append(summary)
        
        # AI relevance analysis prompt
        prompt = f"""You are analyzing which deliverables are specifically relevant to a goal.

GOAL CONTEXT:
{goal_context}

AVAILABLE DELIVERABLES:
{chr(10).join(deliverable_summaries)}

INSTRUCTIONS:
1. Identify deliverables that DIRECTLY fulfill the specific goal
2. Consider the goal's primary objective (email sequences vs contacts vs documents etc.)
3. Exclude deliverables that are helpful but not the main focus
4. For an "email sequence" goal, prioritize email_sequence types over contact_list types
5. For a "contact collection" goal, prioritize contact_list types over email_sequence types
6. Return ONLY the deliverable numbers (0-{len(deliverables)-1}) as a comma-separated list
7. If no deliverables are specifically relevant, return "NONE"

GOAL-RELEVANT DELIVERABLE NUMBERS:"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"🤖 AI relevance filtering result: {ai_response}")
        
        if ai_response == "NONE":
            logger.info("AI found no goal-relevant deliverables")
            return []
        
        # Parse AI response to filter deliverables
        try:
            deliverable_indices = [int(x.strip()) for x in ai_response.split(',') if x.strip().isdigit()]
            filtered_deliverables = [deliverables[i] for i in deliverable_indices if 0 <= i < len(deliverables)]
            
            logger.info(f"✅ AI filtered {len(filtered_deliverables)}/{len(deliverables)} goal-relevant deliverables")
            return filtered_deliverables
            
        except Exception as e:
            logger.warning(f"Failed to parse AI filtering response: {e}, returning all deliverables")
            return deliverables
            
    except Exception as e:
        logger.warning(f"AI relevance filtering failed: {e}, returning all deliverables")
        return deliverables

async def check_and_fix_deliverable_creation():
    """Check workspaces with completed goals but no deliverables and create them"""
    logger.info("🔧 Starting deliverable creation fix...")
    
    try:
        # Get all workspaces with completed goals
        goals_response = supabase.table('workspace_goals').select('*').eq('status', 'completed').execute()
        
        if not goals_response.data:
            logger.info("No completed goals found")
            return
        
        # Process individual goals instead of grouping by workspace
        individual_completed_goals = goals_response.data
        
        logger.info(f"Found {len(individual_completed_goals)} completed goals to process")
        
        for goal in individual_completed_goals:
            goal_id = goal['id']
            workspace_id = goal['workspace_id']
            logger.info(f"Checking goal {goal_id} in workspace {workspace_id}")
            
            # Check if this goal already has a deliverable (search in metadata)
            deliverables_response = supabase.table('deliverables').select('id, metadata').eq('workspace_id', workspace_id).execute()
            goal_deliverables = [d for d in deliverables_response.data if d.get('metadata', {}).get('goal_id') == goal_id]
            
            if goal_deliverables:
                logger.info(f"  ✅ Goal {goal_id} already has {len(goal_deliverables)} deliverables")
                continue
            
            # Get goal-related tasks using AI-driven semantic matching (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
            all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute().data
            goal_related_tasks = []
            
            # AI-DRIVEN semantic task-goal matching instead of hard-coded keywords
            goal_related_tasks = await find_semantically_related_tasks(goal, all_tasks)
            
            # Check if goal is actually completed
            goal_completed = goal['current_value'] >= goal['target_value']
            
            if not goal_completed:
                logger.info(f"  ⚠️ Goal {goal_id} not fully completed ({goal['current_value']}/{goal['target_value']})")
                continue
            
            logger.info(f"  🎯 Goal {goal_id} qualifies for individual deliverable creation:")
            logger.info(f"     - Goal completed: {goal['current_value']}/{goal['target_value']} {goal.get('unit', '')}")
            logger.info(f"     - Related tasks: {len(goal_related_tasks)}")
            logger.info(f"     - No existing deliverable")
            
            # Force deliverable creation for this specific goal
            try:
                await force_create_goal_deliverable(workspace_id, goal, goal_related_tasks)
                logger.info(f"  ✅ Successfully created deliverable for goal {goal_id}")
            except Exception as e:
                logger.error(f"  ❌ Failed to create deliverable for goal {goal_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in deliverable creation fix: {e}")

async def force_create_goal_deliverable(workspace_id: str, goal: dict, tasks: list):
    """Force create a deliverable for a specific completed goal"""
    
    # Get workspace info
    workspace_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
    workspace = workspace_response.data[0] if workspace_response.data else {}
    
    workspace_goal = workspace.get('goal', 'Complete project objectives')
    goal_description = goal.get('description', 'Completed objective')
    goal_target = f"{goal['current_value']}/{goal['target_value']} {goal.get('unit', '')}"
    
    # Aggregate results from related tasks
    task_results = []
    concrete_deliverables = []  # Store actual concrete content
    
    for task in tasks:
        if task.get('result') and isinstance(task['result'], dict):
            summary = task['result'].get('summary', '')
            detailed_results = task['result'].get('detailed_results_json', '{}')
            
            # AI-DRIVEN goal-specific content extraction (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
            extracted_content = await extract_concrete_deliverables_ai_driven(detailed_results, goal)
            # Filter content to match goal specificity
            goal_relevant_content = await filter_deliverables_by_goal_relevance(extracted_content, goal)
            concrete_deliverables.extend(goal_relevant_content)
            
            if summary:
                task_results.append({
                    'task_name': task['name'],
                    'summary': summary,
                    'detailed_results': detailed_results,
                    'agent_role': task.get('assigned_to_role', 'AI Agent'),
                    'created_at': task['created_at']
                })
    
    # AI-DRIVEN deliverable content generation for specific goal
    from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
    
    # Create dynamic content using AI
    enhancer = AIContentEnhancer()
    
    # Check if we have concrete deliverables to use
    if concrete_deliverables:
        # Use the actual concrete content as the primary deliverable
        logger.info(f"Found {len(concrete_deliverables)} concrete deliverables for goal {goal['id']}")
        
        # Structure the content with actual deliverables
        deliverable_content = {
            'project_summary': f"Goal '{goal_description}' completed successfully with {len(concrete_deliverables)} concrete deliverables.",
            'key_achievements': [{
                'achievement': goal_description,
                'description': f"Successfully achieved {goal_target}",
                'metrics': {
                    'goal_status': goal_target,
                    'deliverables_created': len(concrete_deliverables)
                }
            }],
            'concrete_deliverables': concrete_deliverables,  # The actual email sequences, contacts, etc.
            'business_impact': {
                'measurable_value': f"Created {len(concrete_deliverables)} ready-to-use assets for immediate implementation",
                'next_steps': ["Import email sequences into HubSpot", "Begin outreach campaign", "Track engagement metrics"]
            },
            'implementation_roadmap': [
                {
                    'step': 'Import to HubSpot',
                    'action': 'Copy the email sequences below directly into your HubSpot email templates'
                },
                {
                    'step': 'Personalize',
                    'action': 'Replace placeholder names and company details with actual prospect information'
                },
                {
                    'step': 'Launch Campaign',
                    'action': 'Start sending the sequence to your prospect list'
                }
            ]
        }
    else:
        # Fallback to AI enhancement if no concrete deliverables found
        logger.warning(f"No concrete deliverables found for goal {goal['id']}, using AI enhancement")
        
        # Generate AI-driven deliverable structure for this goal
        raw_content = {
            'workspace_goal': workspace_goal,
            'specific_goal': goal,
            'goal_description': goal_description,
            'goal_achievement': goal_target,
            'task_results': task_results,
            'completion_context': f"Goal '{goal_description}' achieved {goal_target} with {len(task_results)} task outputs"
        }
        
        # Use AI to enhance and structure the deliverable content
        deliverable_content = await enhancer.enhance_deliverable_content(
            workspace_id=workspace_id,
            raw_content=raw_content,
            deliverable_type='goal_completion_report'
        )
    
    from database import create_deliverable

    payload = {
        'type': 'goal_completion',
        'title': f"Goal Achievement: {goal_description[:80]}",
        'content': deliverable_content,
        'status': 'completed',
        'readiness_score': 100,
        'completion_percentage': 100,
        'business_value_score': 90,
        'metadata': {
            'goal_id': goal['id'],  # Store goal_id in metadata
            'goal_description': goal_description,
            'achievement_ratio': f"{goal['current_value']}/{goal['target_value']}",
            'unit': goal.get('unit', ''),
            'related_tasks_count': len(task_results),
            'deliverable_type': 'goal_specific'
        }
    }
    created = await create_deliverable(workspace_id, payload)
    deliverable_id = created.get('id')
    if not deliverable_id:
        raise Exception(f"Failed to create goal deliverable via helper: {created}")
    logger.info(f"✅ Created goal-specific deliverable with ID: {deliverable_id}")
    return deliverable_id

async def force_create_deliverable(workspace_id: str, goals: list, tasks: list):
    """Force create a deliverable for a workspace with completed goals"""
    
    # Get workspace info
    workspace_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
    workspace = workspace_response.data[0] if workspace_response.data else {}
    
    workspace_goal = workspace.get('goal', 'Complete project objectives')
    
    # Aggregate results from completed tasks
    task_results = []
    for task in tasks:
        if task.get('result') and isinstance(task['result'], dict):
            summary = task['result'].get('summary', '')
            detailed_results = task['result'].get('detailed_results_json', '{}')
            
            if summary:
                task_results.append({
                    'task_name': task['name'],
                    'summary': summary,
                    'detailed_results': detailed_results,
                    'agent_role': task.get('assigned_to_role', 'AI Agent'),
                    'created_at': task['created_at']
                })
    
    # AI-DRIVEN deliverable content generation (instead of hardcoded templates)
    from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
    
    # Create dynamic content using AI
    enhancer = AIContentEnhancer()
    
    # Generate AI-driven deliverable structure
    raw_content = {
        'workspace_goal': workspace_goal,
        'goals_data': goals,
        'task_results': task_results,
        'completion_context': f"{len(goals)} project objectives completed with {len(task_results)} deliverable outputs"
    }
    
    # Use AI to enhance and structure the deliverable content
    enhanced_content = await enhancer.enhance_deliverable_content(
        workspace_id=workspace_id,
        raw_content=raw_content,
        deliverable_type='final_completion_report'
    )
    
    deliverable_content = enhanced_content
    
    from database import create_deliverable

    payload = {
        'type': 'final_report',
        'title': f"Project Completion Report - {workspace.get('name', workspace_goal)[:50]}",
        'content': deliverable_content,
        'status': 'completed',
        'readiness_score': 100,
        'completion_percentage': 100,
        'business_value_score': 85,
    }
    created = await create_deliverable(workspace_id, payload)
    deliverable_id = created.get('id')
    if not deliverable_id:
        raise Exception(f"Failed to create deliverable via helper: {created}")
    logger.info(f"✅ Created deliverable with ID: {deliverable_id}")
    return deliverable_id

if __name__ == "__main__":
    asyncio.run(check_and_fix_deliverable_creation())