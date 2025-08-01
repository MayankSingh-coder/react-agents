"""Enhanced Tool Manager with MySQL Database Support."""

from typing import Any, Dict, List, Optional
from tools import DatabaseTool, WikipediaTool, WebSearchTool, CalculatorTool, CppExecutorTool, CommandLineTool, FileManagerTool
from tools.base_tool import BaseTool, ToolResult
from tools.conversation_history_tool import ConversationHistoryTool
from tools.file_explorer_tool import FileExplorerTool
from mysql_config import MySQLConfig
import logging

# Import automation tools
from tools.automation.screenshot_tool import ScreenshotTool
from tools.automation.app_launcher_tool import AppLauncherTool
from tools.automation.text_input_tool import TextInputTool
from tools.automation.click_tool import ClickTool
from tools.automation.unified_browser_tool import UnifiedBrowserTool
from tools.automation.visual_analysis_tool import VisualAnalysisTool
from tools.automation.element_discovery_tool import ElementDiscoveryTool
from tools.automation.element_interaction_tool import ElementInteractionTool

try:
    from tools.mysql_database_tool import MySQLDatabaseTool
    MYSQL_TOOL_AVAILABLE = True
except ImportError:
    MySQLDatabaseTool = None
    MYSQL_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedToolManager:
    """Enhanced tool manager with support for both in-memory and MySQL databases."""
    
    def __init__(self, use_mysql: bool = False, mysql_config: Optional[Dict[str, Any]] = None, 
                 chatbot_instance=None, include_automation: bool = True):
        self.tools: Dict[str, BaseTool] = {}
        self.use_mysql = use_mysql
        self.mysql_config = mysql_config or MySQLConfig.get_config()
        self.chatbot_instance = chatbot_instance
        self.include_automation = include_automation
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools."""
        tools = []
        
        # Database tool selection
        if self.use_mysql and MYSQL_TOOL_AVAILABLE:
            try:
                # Validate MySQL config before creating tool
                if MySQLConfig.validate_config(self.mysql_config):
                    mysql_tool = MySQLDatabaseTool(
                        host=self.mysql_config["host"],
                        database=self.mysql_config["database"],
                        user=self.mysql_config["user"],
                        password=self.mysql_config["password"],
                        port=self.mysql_config["port"]
                    )
                    tools.append(mysql_tool)
                    logger.info("✅ MySQL Database Tool initialized")
                else:
                    logger.warning("❌ Invalid MySQL config, falling back to in-memory database")
                    tools.append(DatabaseTool())
            except Exception as e:
                logger.error(f"❌ Failed to initialize MySQL tool: {e}")
                logger.info("🔄 Falling back to in-memory database")
                tools.append(DatabaseTool())
        elif self.use_mysql and not MYSQL_TOOL_AVAILABLE:
            logger.warning("❌ MySQL requested but not available, falling back to in-memory database")
            tools.append(DatabaseTool())
        else:
            # Use in-memory database tool
            tools.append(DatabaseTool())
            logger.info("✅ In-memory Database Tool initialized")
        
        # Add conversation history tool
        conversation_tool = ConversationHistoryTool(self.chatbot_instance)
        tools.append(conversation_tool)
        
        # Add other tools
        tools.extend([
            WikipediaTool(),
            WebSearchTool(),
            CalculatorTool(),
            CppExecutorTool(),
            CommandLineTool(),
            FileManagerTool(),
            FileExplorerTool(working_directory='*', safe_mode=True)  # Allow access to all paths with safety checks
        ])
        
        # Add automation tools if requested
        if self.include_automation:
            automation_tools = [
                ScreenshotTool(),
                AppLauncherTool(),
                TextInputTool(),
                ClickTool(),
                UnifiedBrowserTool(),  # Unified browser tool with navigation and basic automation
                ElementDiscoveryTool(),  # Advanced element discovery for web automation
                ElementInteractionTool(),  # Precise element interaction for web automation
                VisualAnalysisTool()
            ]
            tools.extend(automation_tools)
            logger.info(f"✅ Added {len(automation_tools)} automation tools")
        
        # Register all tools
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
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def add_tool(self, name: str, tool: BaseTool):
        """Add a new tool to the manager."""
        self.tools[name] = tool
        logger.info(f"Added tool: {name}")
    
    def add_tool_object(self, tool: BaseTool):
        """Add a new tool to the manager using the tool's name."""
        self.tools[tool.name] = tool
        logger.info(f"Added tool: {tool.name}")
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the manager."""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Removed tool: {name}")
            return True
        return False
    
    def get_tools_schema(self) -> Dict[str, Any]:
        """Get schema for all tools."""
        schema = {
            "tools": {},
            "tool_descriptions": self.get_tool_descriptions(),
            "database_type": "mysql" if self.use_mysql else "in_memory"
        }
        
        for name, tool in self.tools.items():
            schema["tools"][name] = tool.get_schema()
        
        return schema
    
    def format_tools_for_prompt(self) -> str:
        """Format tools information for inclusion in prompts."""
        tool_descriptions = []
        
        # Add database type info
        db_type = "MySQL" if self.use_mysql else "In-Memory"
        
        for name, tool in self.tools.items():
            if "database" in name:
                tool_descriptions.append(f"{name} ({db_type}): {tool.description}")
            else:
                tool_descriptions.append(f"{name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    def get_database_tool_name(self) -> str:
        """Get the name of the active database tool."""
        if self.use_mysql:
            return "mysql_database"
        else:
            return "database"
    
    def switch_database_type(self, use_mysql: bool, mysql_config: Optional[Dict[str, Any]] = None):
        """Switch between MySQL and in-memory database."""
        if use_mysql == self.use_mysql:
            logger.info(f"Already using {'MySQL' if use_mysql else 'in-memory'} database")
            return
        
        # Remove current database tool
        current_db_tool = self.get_database_tool_name()
        if current_db_tool in self.tools:
            self.remove_tool(current_db_tool)
        
        # Update configuration
        self.use_mysql = use_mysql
        if mysql_config:
            self.mysql_config = mysql_config
        
        # Add new database tool
        if use_mysql:
            try:
                if MySQLConfig.validate_config(self.mysql_config):
                    mysql_tool = MySQLDatabaseTool(
                        host=self.mysql_config["host"],
                        database=self.mysql_config["database"],
                        user=self.mysql_config["user"],
                        password=self.mysql_config["password"],
                        port=self.mysql_config["port"]
                    )
                    self.add_tool_object(mysql_tool)
                    logger.info("✅ Switched to MySQL database")
                else:
                    logger.error("❌ Invalid MySQL config, keeping current database")
            except Exception as e:
                logger.error(f"❌ Failed to switch to MySQL: {e}")
        else:
            self.add_tool_object(DatabaseTool())
            logger.info("✅ Switched to in-memory database")
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get status of the database connection."""
        db_tool_name = self.get_database_tool_name()
        db_tool = self.get_tool(db_tool_name)
        
        status = {
            "type": "mysql" if self.use_mysql else "in_memory",
            "tool_name": db_tool_name,
            "available": db_tool is not None
        }
        
        if self.use_mysql and hasattr(db_tool, 'mysql'):
            status["connected"] = db_tool.mysql.is_connected()
            status["host"] = db_tool.mysql.host
            status["database"] = db_tool.mysql.database
        
        return status
    
    def set_chatbot_instance(self, chatbot_instance):
        """Set the chatbot instance for the conversation history tool."""
        self.chatbot_instance = chatbot_instance
        
        # Update the conversation history tool if it exists
        conversation_tool = self.get_tool("conversation_history")
        if conversation_tool:
            conversation_tool.set_chatbot_instance(chatbot_instance)
    
    def __str__(self) -> str:
        """String representation of the tool manager."""
        db_type = "MySQL" if self.use_mysql else "In-Memory"
        return f"EnhancedToolManager({len(self.tools)} tools, {db_type} database)"