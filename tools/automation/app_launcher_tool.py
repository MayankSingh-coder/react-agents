"""Application launcher tool for opening macOS applications."""

import subprocess
import time
from typing import Any, Dict, List
from ..base_tool import BaseTool, ToolResult
from .window_manager import window_manager


class AppLauncherTool(BaseTool):
    """Tool for launching and managing macOS applications."""
    
    def __init__(self):
        super().__init__(
            name="app_launcher",
            description="Launch and manage macOS applications like Notes, TextEdit, Safari, etc."
        )
        
        # Common macOS applications mapping
        self.app_mappings = {
            "notes": "Notes",
            "textedit": "TextEdit",
            "text edit": "TextEdit",
            "safari": "Safari",
            "chrome": "Google Chrome",
            "chromium": "Chromium",
            "firefox": "Firefox",
            "finder": "Finder",
            "terminal": "Terminal",
            "calculator": "Calculator",
            "calendar": "Calendar",
            "mail": "Mail",
            "music": "Music",
            "photos": "Photos",
            "preview": "Preview",
            "system preferences": "System Preferences",
            "activity monitor": "Activity Monitor",
            "keychain access": "Keychain Access"
        }
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Launch an application based on the query.
        
        Args:
            query: Description of what application to launch
            **kwargs: Additional parameters:
                - app_name: specific application name
                - wait_time: time to wait after launching (default: 2 seconds)
                - bring_to_front: whether to bring app to front (default: True)
        """
        try:
            app_name = kwargs.get('app_name', None)
            wait_time = kwargs.get('wait_time', 2)
            bring_to_front = kwargs.get('bring_to_front', True)
            
            # Extract app name from query if not provided
            if not app_name:
                app_name = self._extract_app_name(query.lower())
            
            if not app_name:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Could not identify application to launch from query: {query}"
                )
            
            # Launch the application
            result = self._launch_app(app_name, bring_to_front)
            
            if result["success"]:
                # Wait for app to launch
                time.sleep(wait_time)
                
                # CRITICAL: Ensure the launched app is focused
                if bring_to_front:
                    focus_success = window_manager.ensure_app_focus(app_name)
                    if not focus_success:
                        # Still return success but note the focus issue
                        return ToolResult(
                            success=True,
                            data={
                                "app_name": app_name,
                                "launched": True,
                                "wait_time": wait_time,
                                "focus_success": False,
                                "warning": f"App launched but failed to bring {app_name} to front",
                                "process_info": result.get("process_info", {})
                            },
                            metadata={
                                "query": query,
                                "bring_to_front": bring_to_front
                            }
                        )
                
                return ToolResult(
                    success=True,
                    data={
                        "app_name": app_name,
                        "launched": True,
                        "wait_time": wait_time,
                        "focus_success": True if bring_to_front else None,
                        "process_info": result.get("process_info", {})
                    },
                    metadata={
                        "query": query,
                        "bring_to_front": bring_to_front
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=result["error"]
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to launch application: {str(e)}"
            )
    
    def _extract_app_name(self, query: str) -> str:
        """Extract application name from query."""
        # Check direct mappings first
        for key, app in self.app_mappings.items():
            if key in query:
                return app
        
        # Check for common phrases
        if "open" in query:
            words = query.split()
            try:
                open_index = words.index("open")
                if open_index + 1 < len(words):
                    potential_app = words[open_index + 1]
                    if potential_app in self.app_mappings:
                        return self.app_mappings[potential_app]
                    # Try capitalizing the word
                    return potential_app.capitalize()
            except ValueError:
                pass
        
        # Look for app names in the query
        for word in query.split():
            if word in self.app_mappings:
                return self.app_mappings[word]
            # Try capitalizing
            capitalized = word.capitalize()
            if capitalized in self.app_mappings.values():
                return capitalized
        
        return None
    
    def _launch_app(self, app_name: str, bring_to_front: bool = True) -> Dict[str, Any]:
        """Launch a macOS application."""
        try:
            # Use 'open' command to launch the application
            cmd = ["open", "-a", app_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                process_info = {
                    "command": " ".join(cmd),
                    "returncode": result.returncode
                }
                
                # If we need to bring to front, use AppleScript
                if bring_to_front:
                    try:
                        applescript = f'''
                        tell application "{app_name}"
                            activate
                        end tell
                        '''
                        subprocess.run(["osascript", "-e", applescript], timeout=5)
                    except Exception as e:
                        print(f"Warning: Could not bring {app_name} to front: {e}")
                
                return {
                    "success": True,
                    "process_info": process_info
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to launch {app_name}: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout while launching {app_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error launching {app_name}: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of what application to launch (e.g., 'open notes', 'launch safari', 'start calculator')"
                },
                "app_name": {
                    "type": "string",
                    "description": "Optional: specific application name to launch"
                },
                "wait_time": {
                    "type": "number",
                    "description": "Optional: time to wait after launching (default: 2 seconds)"
                },
                "bring_to_front": {
                    "type": "boolean",
                    "description": "Optional: whether to bring app to front (default: true)"
                }
            },
            "required": ["query"]
        }
    
    def get_available_apps(self) -> List[str]:
        """Get list of available applications."""
        return list(self.app_mappings.values())
    
    def is_app_running(self, app_name: str) -> bool:
        """Check if an application is currently running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", app_name], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False