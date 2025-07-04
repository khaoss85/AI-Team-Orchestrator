
import logging
from typing import Dict, Any, List
from ai_agents.tools import PMOrchestrationTools, WorkspaceMemoryTools, CommonTools, ContentTools, DataTools, AgentTools

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> List[Any]:
        """Initializes all available tools with the workspace_id."""
        tool_instances = [
            PMOrchestrationTools(self.workspace_id).get_team_roles_and_status_tool(),
            PMOrchestrationTools(self.workspace_id).create_and_assign_sub_task_tool(),
            WorkspaceMemoryTools.query_project_memory,
            WorkspaceMemoryTools.store_key_insight,
            WorkspaceMemoryTools.get_workspace_discoveries,
            WorkspaceMemoryTools.get_relevant_project_context,
            CommonTools.store_data,
            CommonTools.retrieve_data,
            CommonTools.search_web,
            CommonTools.fetch_url,
            ContentTools.analyze_text,
            ContentTools.generate_headlines,
            DataTools.analyze_data,
            DataTools.find_correlation,
            DataTools.generate_chart_data,
            AgentTools.update_health,
            AgentTools.get_available_handoffs,
        ]
        logger.info(f"Initialized {len(tool_instances)} tools for workspace {self.workspace_id}")
        return tool_instances

    def get_tools(self) -> List[Any]:
        return self.tools
