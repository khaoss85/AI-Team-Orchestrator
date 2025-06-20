# OpenAI SDK Migration Plan

## Current Status

✅ **Completed:**
- Added new tools to SimpleConversationalAgent (show_goal_progress, show_deliverables, create_goal)
- Created dynamic chats for each goal in workspace
- Integrated placeholder OpenAI SDK tools (WebSearch, CodeInterpreter, ImageGeneration, FileSearch)
- Modified SpecialistAgent to include WebSearchTool for all agents

✅ **Current Implementation:**
- Using `openai` library directly for SimpleConversationalAgent
- Using OpenAI Agents SDK (with fallback) for SpecialistAgent
- Tools available: team management, goal management, asset viewing, plus SDK tools

## Migration to Full OpenAI Agents SDK

### Phase 1: Install and Configure SDK ✅
```bash
pip install openai-agents-python
```

### Phase 2: Replace SimpleConversationalAgent
Currently using direct OpenAI API calls. Should migrate to:

```python
from agents import Agent, Runner, FunctionTool, WebSearchTool, CodeInterpreterTool, ImageGenerationTool, FileSearchTool

# Create agent with hosted tools
agent = Agent(
    name="Conversational Agent",
    instructions="You are a direct, execution-focused AI project manager...",
    tools=[
        WebSearchTool(),
        CodeInterpreterTool(),
        ImageGenerationTool(),
        FileSearchTool(vector_store_ids=["VECTOR_STORE_ID"]),
        # Custom function tools for our business logic
        add_team_member_tool,
        show_goal_progress_tool,
        show_deliverables_tool,
        create_goal_tool
    ]
)

# Run agent
result = await Runner.run(agent, user_message)
```

### Phase 3: Create Function Tools for Business Logic

```python
@function_tool
async def add_team_member(role: str, seniority: str = "senior", skills: List[str] = None) -> str:
    """Add a new team member to the workspace.
    
    Args:
        role: The role of the new member (e.g., 'developer', 'designer')
        seniority: Seniority level (junior, senior, expert)
        skills: List of skills for the member
    """
    # Implementation here
    return "Team member added successfully"

@function_tool
async def show_goal_progress(goal_id: str = None) -> str:
    """Show progress on workspace goals and objectives.
    
    Args:
        goal_id: Optional specific goal ID to view (shows all if not provided)
    """
    # Implementation here
    return "Goal progress information"
```

### Phase 4: Agent-as-Tools Architecture

Create specialized agents that can be used as tools:

```python
# Specialist agents
goal_manager_agent = Agent(
    name="Goal Manager",
    instructions="You manage goals and objectives...",
    tools=[...]
)

team_manager_agent = Agent(
    name="Team Manager", 
    instructions="You manage team members...",
    tools=[...]
)

# Main orchestrator agent
main_agent = Agent(
    name="AI Project Manager",
    instructions="You coordinate with specialist agents...",
    tools=[
        WebSearchTool(),
        CodeInterpreterTool(),
        goal_manager_agent.as_tool(
            tool_name="manage_goals",
            tool_description="Manage workspace goals and objectives"
        ),
        team_manager_agent.as_tool(
            tool_name="manage_team",
            tool_description="Manage team members and assignments"
        )
    ]
)
```

### Phase 5: Enhanced Tools Integration

Add all hosted tools from OpenAI SDK:

1. **WebSearchTool** - Current information search
2. **FileSearchTool** - Document/file search in vector stores
3. **CodeInterpreterTool** - Execute Python code
4. **ImageGenerationTool** - Generate images
5. **ComputerTool** - Computer automation (advanced)
6. **LocalShellTool** - Shell command execution (if needed)

### Benefits of Full SDK Migration

1. **Native Tool Support**: No need for manual tool execution parsing
2. **Better Error Handling**: SDK handles tool failures automatically
3. **Streaming**: Built-in streaming support for long-running operations
4. **Context Management**: Better conversation context handling
5. **Hosted Tools**: Direct access to OpenAI's hosted capabilities
6. **Agent Orchestration**: Native support for agent-to-agent communication

### Implementation Priority

1. **High Priority**: Migrate SimpleConversationalAgent to use SDK
2. **Medium Priority**: Add FileSearchTool with proper vector store setup
3. **Low Priority**: Implement ComputerTool for advanced automation

### Current Tool Capabilities

✅ **Working Tools:**
- add_team_member - Add new team members
- start_team / pause_team - Control team state
- show_team_status - Display team information
- show_goal_progress - View goal completion status
- show_deliverables - View assets and deliverables
- create_goal - Create new workspace goals
- web_search (placeholder) - Web search capability
- code_interpreter (placeholder) - Code execution
- generate_image (placeholder) - Image generation
- file_search (placeholder) - File search

### Next Steps

1. Replace SimpleConversationalAgent with full SDK implementation
2. Set up vector stores for FileSearchTool
3. Test all tools with real OpenAI hosted services
4. Implement agent-as-tools pattern for better specialization