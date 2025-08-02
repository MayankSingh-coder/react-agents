"""Tool manager for the React Agent."""

from typing import Any, Dict, List, Optional
from tools import DatabaseTool, WikipediaTool, WebSearchTool, CalculatorTool, CppExecutorTool, CommandLineTool, FileManagerTool
from tools.file_explorer_tool import FileExplorerTool
from tools.base_tool import BaseTool, ToolResult

# Import automation tools
from tools.automation.screenshot_tool import ScreenshotTool
from tools.automation.app_launcher_tool import AppLauncherTool
from tools.automation.text_input_tool import TextInputTool
from tools.automation.click_tool import ClickTool
from tools.automation.unified_browser_tool import UnifiedBrowserTool
from tools.automation.visual_analysis_tool import VisualAnalysisTool


class ToolManager:
    """Manages all available tools for the React Agent."""
    
    def __init__(self, include_automation: bool = True):
        self.tools: Dict[str, BaseTool] = {}
        self.include_automation = include_automation
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools."""
        tools = [
            DatabaseTool(),
            WikipediaTool(),
            WebSearchTool(),
            CalculatorTool(),
            CppExecutorTool(),
            CommandLineTool(),
            FileManagerTool(),
            FileExplorerTool(working_directory='*', safe_mode=True)  # Allow access to all paths with safety checks
        ]
        
        # Add automation tools if requested
        if self.include_automation:
            automation_tools = [
                ScreenshotTool(),
                AppLauncherTool(),
                TextInputTool(),
                # ClickTool(),
                UnifiedBrowserTool(),  # Replaces BrowserAutomationTool
                VisualAnalysisTool()
            ]
            tools.extend(automation_tools)
        
        for tool in tools:
            self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all available tools."""
        return self.tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get names of all available tools."""
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools."""
        return {name: tool.description for name, tool in self.tools.items()}
    
    async def execute_tool(self, tool_name: str, query: str, **kwargs) -> ToolResult:
        """Execute a tool with the given query."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found. Available tools: {', '.join(self.get_tool_names())}"
            )
        
        # Handle case where parameters are passed as JSON string in query (for LLM agents)
        if not kwargs and query.strip().startswith('{') and query.strip().endswith('}'):
            try:
                import json
                parsed_params = json.loads(query)
                if isinstance(parsed_params, dict):
                    kwargs = parsed_params
                    query = kwargs.pop('query', '')  # Extract query if present
                    print(f"🔧 ToolManager: Parsed JSON from query for {tool_name}")
                    print(f"  new query: '{query}'")
                    print(f"  new kwargs: {kwargs}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse query as JSON for {tool_name}: {e}")
        
        try:
            return await tool.execute(query, **kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def add_tool(self, name: str, tool: BaseTool):
        """Add a new tool to the manager."""
        self.tools[name] = tool
    
    def add_tool_object(self, tool: BaseTool):
        """Add a new tool to the manager using the tool's name."""
        self.tools[tool.name] = tool
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the manager."""
        if name in self.tools:
            del self.tools[name]
            return True
        return False
    
    def get_tools_schema(self) -> Dict[str, Any]:
        """Get schema for all tools."""
        schema = {
            "tools": {},
            "tool_descriptions": self.get_tool_descriptions()
        }
        
        for name, tool in self.tools.items():
            schema["tools"][name] = tool.get_schema()
        
        return schema
    
    def format_tools_for_prompt(self) -> str:
        """Format tools information for inclusion in prompts."""
        tool_descriptions = []
        
        for name, tool in self.tools.items():
            tool_descriptions.append(f"{name}: {tool.description}")
        
        return "\n".join(tool_descriptions)