"""Tool manager for the React Agent."""

from typing import Any, Dict, List, Optional
from tools import DatabaseTool, WikipediaTool, WebSearchTool, CalculatorTool, CppExecutorTool, CommandLineTool, FileManagerTool
from tools.base_tool import BaseTool, ToolResult


class ToolManager:
    """Manages all available tools for the React Agent."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
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
            FileManagerTool()
        ]
        
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
        
        try:
            return await tool.execute(query, **kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def add_tool(self, tool: BaseTool):
        """Add a new tool to the manager."""
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