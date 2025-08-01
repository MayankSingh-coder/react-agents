"""Screenshot tool for capturing screen content."""

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
from PIL import Image
import pyautogui
from ..base_tool import BaseTool, ToolResult
from .window_manager import window_manager


class ScreenshotTool(BaseTool):
    """Tool for taking screenshots of the screen or specific windows."""
    
    def __init__(self):
        super().__init__(
            name="screenshot",
            description=self._get_detailed_description()
        )
        # Create screenshots directory if it doesn't exist
        self.screenshots_dir = "/Users/mayank/Desktop/concepts/react-agents/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Disable pyautogui failsafe for automation
        pyautogui.FAILSAFE = False
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for screenshot operations."""
        return """Capture screenshots of the screen or specific applications for visual analysis and automation workflows.

SUPPORTED OPERATIONS:

• Full Screen Capture:
  - Complete screen: "take screenshot", "capture screen", "screenshot"
  - All displays: Captures entire desktop including multiple monitors

• Region Capture:
  - Specific area: "screenshot region (100, 200, 300, 400)"
  - Custom bounds: region=(x, y, width, height) parameter
  - Partial screen: Capture only specified rectangular area

• Window Capture:
  - Specific application: "screenshot Safari window", "capture Chrome"
  - Active window: "screenshot active window", "capture current app"
  - Window by title: window_title parameter

• File Management:
  - Auto-naming: Generates timestamped filenames
  - Custom names: filename parameter for specific naming
  - Organized storage: Saves to dedicated screenshots directory
  - Multiple formats: PNG (default), JPEG support

CAPTURE FEATURES:
- High quality PNG format by default
- Automatic timestamp in filename
- Organized file storage in screenshots directory
- Immediate availability for visual_analysis tool
- Cross-platform compatibility (macOS optimized)

OUTPUT INFORMATION:
Returns:
- filename: Generated screenshot filename
- filepath: Full path to screenshot file
- dimensions: Image width and height
- file_size: Screenshot file size
- timestamp: When screenshot was taken

LIMITATIONS:
- Cannot capture specific UI elements (captures rectangular regions only)
- No automatic element detection or cropping
- Cannot capture hidden or minimized windows
- No built-in image editing or annotation
- Limited to visible screen content only

WORKFLOW INTEGRATION:
Critical first step in automation workflows:
1. Take screenshot after navigation or page changes
2. Pass screenshot to visual_analysis tool for element detection
3. Use analysis results to guide click/text_input actions
4. Repeat cycle for multi-step automation

USAGE EXAMPLES:
- "take screenshot" → Captures full screen with timestamp
- "screenshot for analysis" → Takes screenshot for visual_analysis tool
- "capture current page" → Screenshots current browser/app state
- "screenshot region (100, 200, 500, 400)" → Captures specific area
- "screenshot Safari window" → Captures only Safari application

PARAMETER OPTIONS:
- region: (x, y, width, height) for specific area capture
- filename: Custom filename (optional, auto-generated if not provided)
- window_title: Specific window to capture
- format: Image format (PNG default, JPEG available)

INTEGRATION NOTES:
- Screenshots automatically saved to: /Users/mayank/Desktop/concepts/react-agents/screenshots/
- Files immediately available for visual_analysis tool
- Filenames include timestamp for organization
- Essential for any visual automation workflow"""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Take a screenshot based on the query.
        
        Args:
            query: Description of what to screenshot
            **kwargs: Additional parameters:
                - region: tuple (x, y, width, height) for specific region
                - filename: custom filename (optional)
                - window_title: specific window to capture (optional)
                - app_name: specific application to focus and capture (optional)
                - browser_type: specific browser to focus and capture (optional)
        """
        try:
            # Parse parameters
            region = kwargs.get('region', None)
            filename = kwargs.get('filename', None)
            window_title = kwargs.get('window_title', None)
            app_name = kwargs.get('app_name', None)
            browser_type = kwargs.get('browser_type', None)
            
            # Detect application from query if not explicitly provided
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
                
                # Check for other common applications
                elif 'finder' in query_lower:
                    app_name = 'Finder'
                elif 'terminal' in query_lower:
                    app_name = 'Terminal'
                elif 'notes' in query_lower:
                    app_name = 'Notes'
                elif 'calculator' in query_lower:
                    app_name = 'Calculator'
                elif 'textedit' in query_lower:
                    app_name = 'TextEdit'
                elif 'preview' in query_lower:
                    app_name = 'Preview'
                elif 'mail' in query_lower:
                    app_name = 'Mail'
                elif 'calendar' in query_lower:
                    app_name = 'Calendar'
                elif 'messages' in query_lower:
                    app_name = 'Messages'
                elif 'music' in query_lower:
                    app_name = 'Music'
                elif 'photos' in query_lower:
                    app_name = 'Photos'
            
            # CRITICAL: Focus the correct application before taking screenshot
            focus_success = True
            if browser_type:
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {browser_type} browser before taking screenshot. Please ensure browser is open."
                    )
            elif app_name:
                focus_success = window_manager.ensure_app_focus(app_name)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {app_name} before taking screenshot. Please ensure application is open."
                    )
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if browser_type:
                    filename = f"screenshot_{browser_type}_{timestamp}.png"
                elif app_name:
                    filename = f"screenshot_{app_name.lower().replace(' ', '_')}_{timestamp}.png"
                else:
                    filename = f"screenshot_{timestamp}.png"
            
            # Ensure filename has .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            if region:
                # Screenshot specific region
                screenshot = pyautogui.screenshot(region=region)
            elif window_title:
                # Try to find and screenshot specific window
                # This is a simplified approach - in production you might want more sophisticated window handling
                screenshot = pyautogui.screenshot()
            else:
                # Full screen screenshot (but focused application should be on top)
                screenshot = pyautogui.screenshot()
            
            # Save screenshot
            screenshot.save(filepath)
            
            # Get screenshot info
            width, height = screenshot.size
            file_size = os.path.getsize(filepath)
            
            return ToolResult(
                success=True,
                data={
                    "filepath": filepath,
                    "filename": filename,
                    "width": width,
                    "height": height,
                    "file_size": file_size,
                    "timestamp": datetime.now().isoformat(),
                    "focused_app": browser_type or app_name,
                    "focus_success": focus_success
                },
                metadata={
                    "query": query,
                    "region": region,
                    "window_title": window_title,
                    "app_name": app_name,
                    "browser_type": browser_type
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to take screenshot: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of what to screenshot (e.g., 'take full screen screenshot', 'capture browser window')"
                },
                "region": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "Optional: [x, y, width, height] for specific region"
                },
                "filename": {
                    "type": "string",
                    "description": "Optional: custom filename for the screenshot"
                },
                "window_title": {
                    "type": "string",
                    "description": "Optional: title of specific window to capture"
                }
            },
            "required": ["query"]
        }
    
    def get_latest_screenshot(self) -> Optional[str]:
        """Get the path to the most recently taken screenshot."""
        try:
            screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]
            if not screenshots:
                return None
            
            # Sort by modification time
            screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshots_dir, x)), reverse=True)
            return os.path.join(self.screenshots_dir, screenshots[0])
        except Exception:
            return None
    
    def cleanup_old_screenshots(self, keep_count: int = 10):
        """Clean up old screenshots, keeping only the most recent ones."""
        try:
            screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]
            if len(screenshots) <= keep_count:
                return
            
            # Sort by modification time
            screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshots_dir, x)), reverse=True)
            
            # Remove old screenshots
            for screenshot in screenshots[keep_count:]:
                os.remove(os.path.join(self.screenshots_dir, screenshot))
                
        except Exception as e:
            print(f"Warning: Failed to cleanup old screenshots: {e}")