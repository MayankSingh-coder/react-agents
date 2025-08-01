"""Click tool for automated mouse interactions."""

import time
from typing import Any, Dict, Tuple, Optional
import pyautogui
from ..base_tool import BaseTool, ToolResult
from .window_manager import window_manager


class ClickTool(BaseTool):
    """Tool for performing mouse clicks and interactions."""
    
    def __init__(self):
        super().__init__(
            name="click",
            description=self._get_detailed_description()
        )
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1  # Small pause between actions
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for click operations."""
        return """Perform precise mouse interactions including clicks, scrolls, and drag operations at specific screen coordinates.

🎯 WHEN TO USE THIS TOOL:
- Desktop applications (non-web)
- System UI elements (menus, dialogs, taskbar)
- Applications without web-based interfaces
- When you have exact pixel coordinates from visual analysis
- Cross-platform automation (works on any screen element)

❌ DON'T USE FOR:
- Web browsers (use ElementInteractionTool instead)
- When you have CSS selectors (use ElementInteractionTool instead)
- When you need to find elements by text/attributes (use ElementDiscoveryTool first)

OPERATIONS & SYNTAX:

• click <coordinates> - Left click at coordinates
  Usage: click at (100, 200)
  Usage: click at coordinates 150,300
  Usage: left click on coordinates 150,300

• right_click <coordinates> - Right click for context menu
  Usage: right click at (100, 200)
  Usage: context menu at 150,300
  Usage: right click at coordinates 200,400

• double_click <coordinates> - Double click at coordinates
  Usage: double click at (100, 200)
  Usage: double tap coordinates 150,300
  Usage: double click at (100, 150)

• middle_click <coordinates> - Middle click (scroll wheel click)
  Usage: middle click at (100, 200)
  Usage: scroll click at 150,300

• scroll <direction> <coordinates> - Scroll at coordinates
  Usage: scroll up at (500, 400)
  Usage: scroll down at (500, 400)
  Usage: scroll up 5 steps
  Usage: scroll down 3 steps
  ⚠️  IMPORTANT: Default scroll amount is 3 steps

• drag <from_coordinates> <to_coordinates> - Drag and drop
  Usage: drag from (100, 200) to (300, 400)
  Usage: drag slowly from (100, 200) to (300, 400)
  ⚠️  IMPORTANT: Default duration is 0.5 seconds

COORDINATE REQUIREMENTS:
- MUST provide exact x,y pixel coordinates
- Coordinates are absolute screen positions (not relative to window)
- Use visual_analysis tool first to identify element locations
- Screen coordinates start at (0,0) in top-left corner

LIMITATIONS:
- Requires exact pixel coordinates (cannot find elements by name/text)
- No automatic element detection or waiting
- Cannot verify if click was successful
- No retry logic for failed clicks
- Cannot handle moving or dynamic elements

WORKFLOW INTEGRATION:
Essential for automation workflows:
1. Use screenshot tool to capture current state
2. Use visual_analysis tool to identify clickable elements and their locations
3. Use click tool with extracted coordinates to interact with elements
4. Repeat cycle for multi-step interactions

PARAMETER OPTIONS:
- x, y: Exact coordinates (required)
- click_type: 'left', 'right', 'double', 'middle'
- clicks: Number of clicks (default: 1)
- interval: Time between multiple clicks
- scroll_direction: 'up', 'down', 'left', 'right'
- scroll_amount: Number of scroll steps
- duration: Duration for drag operations"""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Perform mouse interactions based on the query.
        
        Args:
            query: Description of the click action
            **kwargs: Additional parameters:
                - x, y: coordinates to click
                - click_type: 'left', 'right', 'double', 'middle'
                - button: alternative to click_type
                - clicks: number of clicks (default: 1)
                - interval: interval between clicks (default: 0.1)
                - duration: duration for drag operations
                - scroll_direction: 'up' or 'down' for scroll operations
                - scroll_amount: number of scroll steps
                - app_name: specific application to focus before clicking
                - browser_type: specific browser to focus before clicking
        """
        try:
            # Extract coordinates
            x = kwargs.get('x', None)
            y = kwargs.get('y', None)
            
            # If coordinates not provided, try to extract from query
            if x is None or y is None:
                coords = self._extract_coordinates(query)
                if coords:
                    x, y = coords
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="No coordinates provided. Please specify x and y coordinates."
                    )
            
            # CRITICAL: Ensure correct application focus before clicking
            app_name = kwargs.get('app_name', None)
            browser_type = kwargs.get('browser_type', None)
            
            # Try to detect application from query if not explicitly provided
            if not app_name and not browser_type:
                query_lower = query.lower()
                
                # Check for browser mentions
                if 'safari' in query_lower:
                    browser_type = 'safari'
                elif 'chrome' in query_lower and 'chromium' not in query_lower:
                    browser_type = 'chrome'
                elif 'chromium' in query_lower:
                    browser_type = 'chromium'
                elif 'firefox' in query_lower:
                    browser_type = 'firefox'
                elif 'edge' in query_lower:
                    browser_type = 'edge'
            
            # Focus the correct application before clicking
            if browser_type:
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {browser_type} browser before clicking. Please ensure browser is open."
                    )
            elif app_name:
                focus_success = window_manager.ensure_app_focus(app_name)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {app_name} before clicking. Please ensure application is open."
                    )
            
            # Determine action type
            action_type = self._determine_action_type(query, kwargs)
            
            # Perform the action
            result = await self._perform_action(action_type, x, y, kwargs)
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to perform click action: {str(e)}"
            )
    
    def _extract_coordinates(self, query: str) -> Optional[Tuple[int, int]]:
        """Extract coordinates from query string."""
        import re
        
        # Look for patterns like "click at 100, 200" or "coordinates 100,200"
        patterns = [
            r'(?:at|coordinates?)\s*(\d+)\s*,\s*(\d+)',
            r'(\d+)\s*,\s*(\d+)',
            r'x\s*=?\s*(\d+).*y\s*=?\s*(\d+)',
            r'position\s*(\d+)\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    x, y = int(match.group(1)), int(match.group(2))
                    return (x, y)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _determine_action_type(self, query: str, kwargs: Dict[str, Any]) -> str:
        """Determine the type of action to perform."""
        # Check kwargs first
        if 'click_type' in kwargs:
            return kwargs['click_type']
        if 'button' in kwargs:
            return kwargs['button']
        
        # Check query for action keywords
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['double', 'double-click', 'doubleclick']):
            return 'double'
        elif any(word in query_lower for word in ['right', 'right-click', 'context']):
            return 'right'
        elif any(word in query_lower for word in ['middle', 'middle-click', 'wheel']):
            return 'middle'
        elif any(word in query_lower for word in ['scroll', 'wheel']):
            if 'up' in query_lower:
                return 'scroll_up'
            elif 'down' in query_lower:
                return 'scroll_down'
            return 'scroll'
        elif any(word in query_lower for word in ['drag', 'move']):
            return 'drag'
        else:
            return 'left'  # Default to left click
    
    async def _perform_action(self, action_type: str, x: int, y: int, kwargs: Dict[str, Any]) -> ToolResult:
        """Perform the specified action."""
        try:
            # Get screen size for validation
            screen_width, screen_height = pyautogui.size()
            
            # Validate coordinates
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})"
                )
            
            # Move to position first
            pyautogui.moveTo(x, y)
            
            # Perform action based on type
            if action_type == 'left':
                clicks = kwargs.get('clicks', 1)
                interval = kwargs.get('interval', 0.1)
                pyautogui.click(x, y, clicks=clicks, interval=interval, button='left')
                action_performed = f"Left clicked at ({x}, {y}) {clicks} time(s)"
                
            elif action_type == 'right':
                pyautogui.click(x, y, button='right')
                action_performed = f"Right clicked at ({x}, {y})"
                
            elif action_type == 'double':
                pyautogui.doubleClick(x, y)
                action_performed = f"Double clicked at ({x}, {y})"
                
            elif action_type == 'middle':
                pyautogui.click(x, y, button='middle')
                action_performed = f"Middle clicked at ({x}, {y})"
                
            elif action_type in ['scroll', 'scroll_up', 'scroll_down']:
                scroll_amount = kwargs.get('scroll_amount', 3)
                if action_type == 'scroll_up':
                    pyautogui.scroll(scroll_amount, x=x, y=y)
                    action_performed = f"Scrolled up {scroll_amount} steps at ({x}, {y})"
                else:
                    pyautogui.scroll(-scroll_amount, x=x, y=y)
                    action_performed = f"Scrolled down {scroll_amount} steps at ({x}, {y})"
                    
            elif action_type == 'drag':
                # For drag operations, we need end coordinates
                end_x = kwargs.get('end_x', x + 100)  # Default drag 100 pixels right
                end_y = kwargs.get('end_y', y)
                duration = kwargs.get('duration', 0.5)
                
                pyautogui.dragTo(end_x, end_y, duration=duration)
                action_performed = f"Dragged from ({x}, {y}) to ({end_x}, {end_y})"
                
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action type: {action_type}"
                )
            
            # Small delay after action
            time.sleep(0.1)
            
            return ToolResult(
                success=True,
                data={
                    "action": action_performed,
                    "coordinates": (x, y),
                    "action_type": action_type,
                    "timestamp": time.time()
                },
                metadata=kwargs
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to perform {action_type} action: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of the click action (e.g., 'click at 100,200', 'right click at coordinates 150,300')"
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate to click"
                },
                "y": {
                    "type": "integer", 
                    "description": "Y coordinate to click"
                },
                "click_type": {
                    "type": "string",
                    "enum": ["left", "right", "double", "middle", "scroll_up", "scroll_down", "drag"],
                    "description": "Type of click to perform"
                },
                "clicks": {
                    "type": "integer",
                    "description": "Number of clicks (default: 1)"
                },
                "interval": {
                    "type": "number",
                    "description": "Interval between clicks in seconds (default: 0.1)"
                },
                "scroll_amount": {
                    "type": "integer",
                    "description": "Number of scroll steps (default: 3)"
                },
                "end_x": {
                    "type": "integer",
                    "description": "End X coordinate for drag operations"
                },
                "end_y": {
                    "type": "integer",
                    "description": "End Y coordinate for drag operations"
                },
                "duration": {
                    "type": "number",
                    "description": "Duration for drag operations in seconds (default: 0.5)"
                }
            },
            "required": ["query"]
        }
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return pyautogui.size()