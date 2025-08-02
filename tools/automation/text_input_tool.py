"""Text input tool for automated typing and keyboard interactions."""

import time
from typing import Any, Dict, List
import pyautogui
from ..base_tool import BaseTool, ToolResult
from .window_manager import window_manager


class TextInputTool(BaseTool):
    """Tool for typing text and performing keyboard interactions."""
    
    def __init__(self):
        super().__init__(
            name="text_input",
            description=self._get_detailed_description()
        )
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05  # Small pause between keystrokes
        
        # Common keyboard shortcuts
        self.shortcuts = {
            'copy': ['cmd', 'c'],
            'paste': ['cmd', 'v'],
            'cut': ['cmd', 'x'],
            'undo': ['cmd', 'z'],
            'redo': ['cmd', 'shift', 'z'],
            'select_all': ['cmd', 'a'],
            'save': ['cmd', 's'],
            'new': ['cmd', 'n'],
            'open': ['cmd', 'o'],
            'find': ['cmd', 'f'],
            'quit': ['cmd', 'q'],
            'close': ['cmd', 'w'],
            'tab': ['cmd', 't'],
            'refresh': ['cmd', 'r'],
            'zoom_in': ['cmd', '+'],
            'zoom_out': ['cmd', '-'],
            'fullscreen': ['cmd', 'ctrl', 'f']
        }
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for text input operations."""
        return """Perform keyboard interactions including typing text, sending keyboard shortcuts, and special key combinations.

🎯 WHEN TO USE THIS TOOL:
- Typing text at current cursor position
- Keyboard shortcuts (copy, paste, save, etc.)
- Special key presses (Enter, Tab, Escape)
- Form navigation using keyboard
- Any application that accepts keyboard input

❌ DON'T USE FOR:
- Web form filling (use ElementInteractionTool with selectors instead)
- Clicking to focus fields (use ClickTool or ElementInteractionTool first)
- Finding input fields (use ElementDiscoveryTool first)

OPERATIONS & SYNTAX:

• type_text - Type text at current cursor position
  Usage: {"action": "type_text", "text": "hello world"}
  Usage: {"action": "type_text", "text": "john@email.com"}
  Usage: {"action": "type_text", "text": "password123!@#"}
  Usage: {"action": "type_text", "text": "line1\\nline2\\nline3"}

• clear_and_type - Clear field and type new text
  Usage: {"action": "clear_and_type", "text": "new text"}
  Usage: {"action": "clear_and_type", "text": "replacement value"}
  ⚠️  IMPORTANT: Uses Cmd+A then Backspace to clear

• keyboard_shortcut - Execute predefined shortcuts
  Usage: {"action": "keyboard_shortcut", "shortcut": "copy"}
  Usage: {"action": "keyboard_shortcut", "shortcut": "paste"}
  Usage: {"action": "keyboard_shortcut", "shortcut": "save"}
  Usage: {"action": "keyboard_shortcut", "shortcut": "select_all"}
  ⚠️  IMPORTANT: Available shortcuts: copy, paste, cut, undo, redo, select_all, save, new, open, find, quit, close, tab, refresh

• press_key - Press special keys
  Usage: {"action": "press_key", "key": "enter"}
  Usage: {"action": "press_key", "key": "tab"}
  Usage: {"action": "press_key", "key": "escape"}
  Usage: {"action": "press_key", "key": "backspace"}
  Usage: {"action": "press_key", "key": "delete"}
  ⚠️  IMPORTANT: Supports enter, tab, escape, backspace, delete, space, up, down, left, right

• custom_keys - Press custom key combinations
  Usage: {"action": "custom_keys", "keys": ["cmd", "shift", "n"]}
  Usage: {"action": "custom_keys", "keys": ["ctrl", "alt", "t"]}
  Usage: {"action": "custom_keys", "keys": ["cmd", "c"]}

PREDEFINED SHORTCUTS (macOS):
- copy: Cmd+C
- paste: Cmd+V  
- cut: Cmd+X
- undo: Cmd+Z
- redo: Cmd+Shift+Z
- select_all: Cmd+A
- save: Cmd+S
- find: Cmd+F
- new: Cmd+N
- open: Cmd+O
- quit: Cmd+Q
- close: Cmd+W
- tab: Cmd+T
- refresh: Cmd+R

COMMON PARAMETERS:
- interval: Typing speed delay between keystrokes (default: 0.05)
- clear_first: Clear existing text before typing (default: false)

LIMITATIONS:
- Cannot target specific input fields (types at current cursor position)
- No automatic field detection or clicking
- Cannot verify text was entered correctly
- No retry logic for failed typing

WORKFLOW INTEGRATION:
Essential for form filling workflows:
1. Use ClickTool or ElementInteractionTool to focus on input field
2. Use TextInputTool to enter text
3. Use TextInputTool for navigation (tab, enter)
4. Repeat for multiple fields

⚠️  IMPORTANT: Requires active focus on target input field. Use click tools first to focus."""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Perform text input or keyboard actions based on the structured action.
        
        Args:
            query: JSON string or description of action to perform
            **kwargs: Additional parameters:
                - action: specific action to perform (type_text, keyboard_shortcut, press_key, etc.)
                - text: text to type
                - shortcut: predefined shortcut name
                - key: special key to press
                - keys: list of keys for custom combinations
                - interval: typing speed interval (default: 0.05)
                - clear_first: whether to clear existing text first
        """
        try:
            # Handle case where parameters are passed as JSON string in query (for LLM agents)
            if not kwargs and query.strip().startswith('{') and query.strip().endswith('}'):
                try:
                    import json
                    parsed_params = json.loads(query)
                    if isinstance(parsed_params, dict):
                        kwargs = parsed_params
                        query = kwargs.pop('query', '')  # Extract query if present
                        print(f"🔧 TextInputTool: Parsed JSON from query parameter")
                        print(f"  new query: '{query}'")
                        print(f"  new kwargs: {kwargs}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Failed to parse query as JSON: {e}")
            
            # Parse action from kwargs or query
            action = kwargs.get('action')
            if not action:
                # Fallback to legacy parsing for backward compatibility
                action = self._determine_action_type(query, kwargs)
            
            if action == 'type_text':
                result = await self._type_text(query, kwargs)
            elif action == 'clear_and_type':
                kwargs['clear_first'] = True
                result = await self._type_text(query, kwargs)
            elif action == 'keyboard_shortcut':
                result = await self._execute_shortcut(query, kwargs)
            elif action == 'press_key':
                result = await self._press_special_keys(query, kwargs)
            elif action == 'custom_keys':
                result = await self._execute_shortcut(query, kwargs)
            else:
                # Fallback to legacy method for backward compatibility
                action_type = self._determine_action_type(query, kwargs)
                if action_type == 'type_text':
                    result = await self._type_text(query, kwargs)
                elif action_type == 'shortcut':
                    result = await self._execute_shortcut(query, kwargs)
                elif action_type == 'special_keys':
                    result = await self._press_special_keys(query, kwargs)
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Unknown action: {action}. Supported actions: type_text, clear_and_type, keyboard_shortcut, press_key, custom_keys"
                    )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to perform text input action: {str(e)}"
            )
    
    def _determine_action_type(self, query: str, kwargs: Dict[str, Any]) -> str:
        """Determine the type of action to perform."""
        query_lower = query.lower()
        
        # Check kwargs first
        if 'shortcut' in kwargs or 'keys' in kwargs:
            return 'shortcut'
        
        # Check for shortcut keywords in query
        shortcut_keywords = ['shortcut', 'press', 'key', 'ctrl', 'cmd', 'alt', 'shift']
        if any(keyword in query_lower for keyword in shortcut_keywords):
            return 'shortcut'
        
        # Check for special key keywords
        special_keys = ['enter', 'return', 'tab', 'escape', 'backspace', 'delete', 'space']
        if any(key in query_lower for key in special_keys):
            return 'special_keys'
        
        # Default to typing text
        return 'type_text'
    
    async def _type_text(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Type text with realistic timing."""
        try:
            # CRITICAL: Ensure correct application focus before typing
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
                
                # Check for other common applications
                elif 'notes' in query_lower:
                    app_name = 'Notes'
                elif 'textedit' in query_lower or 'text edit' in query_lower:
                    app_name = 'TextEdit'
                elif 'finder' in query_lower:
                    app_name = 'Finder'
                elif 'terminal' in query_lower:
                    app_name = 'Terminal'
                elif 'calculator' in query_lower:
                    app_name = 'Calculator'
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
            
            # Focus the correct application before typing
            if browser_type:
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {browser_type} browser before typing. Please ensure browser is open."
                    )
            elif app_name:
                focus_success = window_manager.ensure_app_focus(app_name)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {app_name} before typing. Please ensure application is open."
                    )
            
            # Get text to type
            text = kwargs.get('text', None)
            if not text:
                # Extract text from query
                text = self._extract_text_from_query(query)
            
            if not text:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No text provided to type"
                )
            
            # Configuration
            interval = kwargs.get('interval', 0.05)
            clear_first = kwargs.get('clear_first', False)
            
            # Clear existing text if requested
            if clear_first:
                pyautogui.hotkey('cmd', 'a')  # Select all
                time.sleep(0.1)
                pyautogui.press('backspace')  # Delete
                time.sleep(0.1)
            
            # Type the text
            pyautogui.write(text, interval=interval)
            
            # Re-verify focus after typing to ensure it wasn't lost
            focus_maintained = True
            if browser_type or app_name:
                import time
                time.sleep(0.2)  # Brief pause to let typing complete
                
                # Check if focus was lost and try to regain it
                current_app = window_manager.get_frontmost_application()
                expected_app = browser_type if browser_type else app_name
                
                if browser_type:
                    expected_app_name = window_manager.browser_apps.get(browser_type, browser_type)
                else:
                    expected_app_name = app_name
                
                if current_app != expected_app_name:
                    # Focus was lost, try to regain it
                    if browser_type:
                        focus_maintained = window_manager.ensure_browser_focus(browser_type)
                    else:
                        focus_maintained = window_manager.ensure_app_focus(app_name)
            
            return ToolResult(
                success=True,
                data={
                    "text_typed": text,
                    "character_count": len(text),
                    "typing_speed": interval,
                    "cleared_first": clear_first,
                    "focus_maintained": focus_maintained,
                    "focused_app": browser_type or app_name
                },
                metadata={
                    "query": query,
                    "action": "type_text"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to type text: {str(e)}"
            )
    
    async def _execute_shortcut(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Execute keyboard shortcuts."""
        try:
            # CRITICAL: Ensure correct application focus before shortcuts
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
                
                # Check for other common applications
                elif 'notes' in query_lower:
                    app_name = 'Notes'
                elif 'textedit' in query_lower or 'text edit' in query_lower:
                    app_name = 'TextEdit'
                elif 'finder' in query_lower:
                    app_name = 'Finder'
                elif 'terminal' in query_lower:
                    app_name = 'Terminal'
                elif 'calculator' in query_lower:
                    app_name = 'Calculator'
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
            
            # Focus the correct application before shortcuts
            if browser_type:
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {browser_type} browser before shortcut. Please ensure browser is open."
                    )
            elif app_name:
                focus_success = window_manager.ensure_app_focus(app_name)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {app_name} before shortcut. Please ensure application is open."
                    )
            
            # Get shortcut to execute
            shortcut = kwargs.get('shortcut', None)
            keys = kwargs.get('keys', None)
            
            if not shortcut and not keys:
                # Try to extract from query
                shortcut = self._extract_shortcut_from_query(query)
            
            if shortcut and shortcut in self.shortcuts:
                keys = self.shortcuts[shortcut]
            elif not keys:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown shortcut or no keys provided: {query}"
                )
            
            # Execute the shortcut
            if isinstance(keys, list):
                pyautogui.hotkey(*keys)
                keys_pressed = ' + '.join(keys)
            else:
                pyautogui.press(keys)
                keys_pressed = keys
            
            return ToolResult(
                success=True,
                data={
                    "shortcut_executed": shortcut or "custom",
                    "keys_pressed": keys_pressed,
                    "action": "shortcut"
                },
                metadata={
                    "query": query,
                    "original_keys": keys
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to execute shortcut: {str(e)}"
            )
    
    async def _press_special_keys(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Press special keys like Enter, Tab, etc."""
        try:
            # Extract special key from query
            special_key = self._extract_special_key_from_query(query)
            
            if not special_key:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Could not identify special key from query: {query}"
                )
            
            # Press the key
            pyautogui.press(special_key)
            
            return ToolResult(
                success=True,
                data={
                    "key_pressed": special_key,
                    "action": "special_key"
                },
                metadata={
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to press special key: {str(e)}"
            )
    
    def _extract_text_from_query(self, query: str) -> str:
        """Extract text to type from query."""
        # Look for quoted text first
        import re
        
        # Match text in quotes
        quote_patterns = [
            r'"([^"]*)"',  # Double quotes
            r"'([^']*)'",  # Single quotes
            r'`([^`]*)`'   # Backticks
        ]
        
        for pattern in quote_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Look for "type" keyword
        if "type" in query.lower():
            parts = query.lower().split("type")
            if len(parts) > 1:
                text = parts[1].strip()
                # Remove common prefixes
                for prefix in ["the text", "text", ":"]:
                    if text.startswith(prefix):
                        text = text[len(prefix):].strip()
                return text
        
        # If no specific pattern found, return the whole query
        return query
    
    def _extract_shortcut_from_query(self, query: str) -> str:
        """Extract shortcut name from query."""
        query_lower = query.lower()
        
        for shortcut_name in self.shortcuts.keys():
            if shortcut_name.replace('_', ' ') in query_lower or shortcut_name in query_lower:
                return shortcut_name
        
        return None
    
    def _extract_special_key_from_query(self, query: str) -> str:
        """Extract special key from query."""
        query_lower = query.lower()
        
        key_mappings = {
            'enter': 'enter',
            'return': 'enter',
            'tab': 'tab',
            'escape': 'esc',
            'esc': 'esc',
            'backspace': 'backspace',
            'delete': 'delete',
            'space': 'space',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'home': 'home',
            'end': 'end',
            'pageup': 'pageup',
            'pagedown': 'pagedown'
        }
        
        for key_word, key_name in key_mappings.items():
            if key_word in query_lower:
                return key_name
        
        return None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of text to type or keyboard action (e.g., 'type hello world', 'press enter', 'copy shortcut')"
                },
                "text": {
                    "type": "string",
                    "description": "Optional: specific text to type"
                },
                "shortcut": {
                    "type": "string",
                    "description": "Optional: shortcut name (copy, paste, save, etc.)"
                },
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: list of keys to press together"
                },
                "interval": {
                    "type": "number",
                    "description": "Optional: typing speed interval in seconds (default: 0.05)"
                },
                "clear_first": {
                    "type": "boolean",
                    "description": "Optional: clear existing text before typing (default: false)"
                }
            },
            "required": ["query"]
        }
    
    def get_available_shortcuts(self) -> List[str]:
        """Get list of available shortcuts."""
        return list(self.shortcuts.keys())